import os
import sys
import threading
import time
import traceback

print("[DEBUG] Starting...")

# Import the trading bot components
try:
    from binance_trade_bot.binance_api_manager import BinanceAPIManager
    from binance_trade_bot.config import Config
    from binance_trade_bot.database import Database
    from binance_trade_bot.logger import Logger
    from binance_trade_bot.scheduler import SafeScheduler
    from binance_trade_bot.strategies import get_strategy
    print("[DEBUG] Imports OK")
except Exception as e:
    print(f"[ERROR] Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Import Flask app
try:
    from binance_trade_bot.api_server import app, socketio
    print("[DEBUG] Flask imports OK")
except Exception as e:
    print(f"[ERROR] Flask import failed: {e}")
    traceback.print_exc()
    sys.exit(1)


def run_trader():
    """Run the trading bot"""
    try:
        logger = Logger()
        print("[DEBUG] Trader Logger created")
        
        config = Config()
        print(f"[DEBUG] Config loaded - TESTNET={config.TESTNET}, API_KEY={'set' if config.BINANCE_API_KEY else 'NOT SET'}")
        
        db = Database(logger, config)
        manager = BinanceAPIManager(config, db, logger, config.TESTNET)
        
        strategy = get_strategy(config.STRATEGY)
        if strategy is None:
            logger.error("Invalid strategy name")
            return
        
        trader = strategy(manager, db, logger, config)
        
        db.create_database()
        db.set_coins(config.SUPPORTED_COIN_LIST)
        db.migrate_old_state()
        trader.initialize()
        
        schedule = SafeScheduler(logger)
        schedule.every(config.SCOUT_SLEEP_TIME).seconds.do(trader.scout).tag("scouting")
        schedule.every(1).minutes.do(trader.update_values).tag("updating value history")
        schedule.every(1).minutes.do(db.prune_scout_history).tag("pruning scout history")
        schedule.every(1).hours.do(db.prune_value_history).tag("pruning value history")
        
        print("[DEBUG] Starting trading loop...")
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        print(f"[ERROR] Trader error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Start trader in background thread
    trader_thread = threading.Thread(target=run_trader, daemon=True)
    trader_thread.start()
    print("[DEBUG] Trader thread started")
    
    # Run Flask server in main thread
    port = int(os.environ.get("PORT", 5123))
    print(f"[DEBUG] Starting Flask on port {port}...")
    socketio.run(app, debug=False, port=port, host="0.0.0.0")
