import re
from datetime import datetime, timedelta
from itertools import groupby
from typing import List, Tuple

from flask import Flask, jsonify, request, send_from_directory
import os
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import Config
from .database import Database
from .logger import Logger
from .models import Coin, CoinValue, CurrentCoin, Pair, ScoutHistory, Trade

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*")


logger = Logger("api_server")
config = Config()
db = Database(logger, config)


def filter_period(query, model):  # pylint: disable=inconsistent-return-statements
    period = request.args.get("period", "all")

    if period == "all":
        return query

    num = float(re.search(r"(\d*)[shdwm]", "1d").group(1))

    if "s" in period:
        return query.filter(model.datetime >= datetime.now() - timedelta(seconds=num))
    if "h" in period:
        return query.filter(model.datetime >= datetime.now() - timedelta(hours=num))
    if "d" in period:
        return query.filter(model.datetime >= datetime.now() - timedelta(days=num))
    if "w" in period:
        return query.filter(model.datetime >= datetime.now() - timedelta(weeks=num))
    if "m" in period:
        return query.filter(model.datetime >= datetime.now() - timedelta(days=28 * num))


@app.route("/api/value_history/<coin>")
@app.route("/api/value_history")
def value_history(coin: str = None):
    session: Session
    with db.db_session() as session:
        query = session.query(CoinValue).order_by(CoinValue.coin_id.asc(), CoinValue.datetime.asc())

        query = filter_period(query, CoinValue)

        if coin:
            values: List[CoinValue] = query.filter(CoinValue.coin_id == coin).all()
            return jsonify([entry.info() for entry in values])

        coin_values = groupby(query.all(), key=lambda cv: cv.coin)
        return jsonify({coin.symbol: [entry.info() for entry in history] for coin, history in coin_values})


@app.route("/api/total_value_history")
def total_value_history():
    session: Session
    with db.db_session() as session:
        query = session.query(
            CoinValue.datetime,
            func.sum(CoinValue.btc_value),
            func.sum(CoinValue.usd_value),
        ).group_by(CoinValue.datetime)

        query = filter_period(query, CoinValue)

        total_values: List[Tuple[datetime, float, float]] = query.all()
        return jsonify([{"datetime": tv[0], "btc": tv[1], "usd": tv[2]} for tv in total_values])


@app.route("/api/trade_history")
def trade_history():
    session: Session
    with db.db_session() as session:
        query = session.query(Trade).order_by(Trade.datetime.asc())

        query = filter_period(query, Trade)

        trades: List[Trade] = query.all()
        return jsonify([trade.info() for trade in trades])


@app.route("/api/scouting_history")
def scouting_history():
    _current_coin = db.get_current_coin()
    coin = _current_coin.symbol if _current_coin is not None else None
    session: Session
    with db.db_session() as session:
        query = (
            session.query(ScoutHistory)
            .join(ScoutHistory.pair)
            .filter(Pair.from_coin_id == coin)
            .order_by(ScoutHistory.datetime.asc())
        )

        query = filter_period(query, ScoutHistory)

        scouts: List[ScoutHistory] = query.all()
        return jsonify([scout.info() for scout in scouts])


@app.route("/api/current_coin")
def current_coin():
    coin = db.get_current_coin()
    return coin.info() if coin else None


@app.route("/api/current_coin_history")
def current_coin_history():
    session: Session
    with db.db_session() as session:
        query = session.query(CurrentCoin)

        query = filter_period(query, CurrentCoin)

        current_coins: List[CurrentCoin] = query.all()
        return jsonify([cc.info() for cc in current_coins])


@app.route("/api/coins")
def coins():
    session: Session
    with db.db_session() as session:
        _current_coin = session.merge(db.get_current_coin())
        _coins: List[Coin] = session.query(Coin).all()
        return jsonify([{**coin.info(), "is_current": coin == _current_coin} for coin in _coins])


@app.route("/api/pairs")
def pairs():
    session: Session
    with db.db_session() as session:
        all_pairs: List[Pair] = session.query(Pair).all()
        return jsonify([pair.info() for pair in all_pairs])


# Global state for RSI strategy (set by the trading bot)
_rsi_status = {
    "price": None,
    "rsi": None,
    "position": None,
    "last_update": None,
    "klines_range": None,
}

# Store last commands and outputs for terminal
_terminal_output = []


def set_rsi_status(price=None, rsi=None, position=None, klines_range=None):
    """Update RSI status from the trading bot"""
    global _rsi_status
    _rsi_status["price"] = price
    _rsi_status["rsi"] = rsi
    _rsi_status["position"] = position
    _rsi_status["last_update"] = datetime.now().isoformat()
    _rsi_status["klines_range"] = klines_range


@app.route("/api/status")
def status():
    """Get current bot status"""
    return jsonify({
        "rsi": _rsi_status,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/terminal", methods=["POST"])
def terminal():
    """Execute a command on the server"""
    global _terminal_output
    data = request.get_json()
    command = data.get("command", "")
    
    if not command:
        return jsonify({"error": "No command provided"}), 400
    
    # Security: only allow certain commands
    allowed_commands = ["status", "ls", "ps", "date", "uptime", "df", "free"]
    cmd_parts = command.strip().split()
    if not cmd_parts or cmd_parts[0] not in allowed_commands:
        _terminal_output.append(f"$ {command}")
        _terminal_output.append(f"Error: Command not allowed. Allowed: {allowed_commands}")
        return jsonify({"error": f"Command not allowed. Allowed: {allowed_commands}"}), 403
    
    try:
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        _terminal_output.append(f"$ {command}")
        _terminal_output.append(output if output else "(no output)")
        # Keep only last 100 lines
        _terminal_output = _terminal_output[-100:]
        return jsonify({"output": output, "returncode": result.returncode})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/terminal/output")
def terminal_output():
    """Get terminal output history"""
    return jsonify({"output": _terminal_output[-50:]})


@app.route("/")
def index():
    import os
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "dashboard.html")
    return send_from_directory(os.path.dirname(template_path), "dashboard.html")


@app.route("/api/account")
def account():
    """Get account balances"""
    try:
        import os
        from binance_trade_bot.binance_api_manager import BinanceAPIManager
        
        # Debug: show env vars
        api_key = os.environ.get("API_KEY") or os.environ.get("API_SECRET")
        print(f"[account API] API_KEY from env: {api_key[:10] if api_key else 'None'}...")
        
        config = Config()
        print(f"[account API] Config loaded API_KEY: {config.BINANCE_API_KEY[:10] if config.BINANCE_API_KEY else 'None'}...")
        
        logger = Logger("account_api")
        db = Database(logger, config)
        manager = BinanceAPIManager(config, db, logger, config.TESTNET)
        
        try:
            account = manager.binance_client.get_account()
            balances = []
            for b in account.get("balances", []):
                free = float(b.get("free", 0))
                locked = float(b.get("locked", 0))
                if free + locked > 0:
                    balances.append({
                        "asset": b["asset"],
                        "free": free,
                        "locked": locked,
                        "total": free + locked
                    })
            return jsonify({"balances": balances})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    socketio.run(app, debug=True, port=5123)
