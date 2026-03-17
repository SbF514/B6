# RSI Trading Bot

Automated cryptocurrency trading bot using RSI(21,25,95) strategy on SOL/USDT.

Based on binance-trade-bot - only modified the strategy file.

## Strategy
- **Buy Signal**: RSI(21) drops below 25 (oversold)
- **Sell Signal**: RSI(21) rises above 95 (overbought)
- **Trading Pair**: SOL/USDT

## Backtest Results (0.1% fee included)
- Average Weekly Return: +4.42%
- Profitable Weeks: 4/4 (100%)
- Last 2 Weeks: +16.12%

## Installation

### Requirements
```bash
pip install -r requirements.txt
```

### Configuration
Create `user.cfg`:
```ini
[binance_user_config]
api_key = YOUR_API_KEY
api_secret_key = YOUR_API_SECRET
bridge = USDT
strategy = rsi
```

Or set environment variables:
```bash
export API_KEY=your_key
export API_SECRET_KEY=your_secret
export STRATEGY=rsi
```

## Running

### Option 1 - Direct
```bash
python -m binance_trade_bot
```

### Option 2 - Docker
```bash
docker-compose up -d
```

### Option 3 - Heroku
```bash
heroku config:set API_KEY=your_key
heroku config:set API_SECRET_KEY=your_secret
heroku config:set STRATEGY=rsi
git push heroku main
```

## Project Structure

```
B6/
├── binance_trade_bot/
│   ├── __main__.py          # Entry point (original)
│   ├── config.py             # Configuration (original)
│   ├── database.py           # SQLite database (original)
│   ├── logger.py            # Logging (original)
│   ├── scheduler.py         # Task scheduler (original)
│   ├── binance_api_manager.py # Binance API (original)
│   ├── binance_stream_manager.py # WebSocket (original)
│   ├── crypto_trading.py    # Main loop (original)
│   ├── auto_trader.py      # Base trading class (original)
│   ├── models/              # Data models (original)
│   └── strategies/
│       ├── __init__.py
│       ├── default_strategy.py # Original strategy (not used)
│       └── rsi_strategy.py  # ← OUR MODIFICATION
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## What Was Modified

Only ONE file was modified from the original binance-trade-bot:

**`binance_trade_bot/strategies/rsi_strategy.py`**
- Implements RSI(21,25,95) strategy
- Uses original API methods: `manager.get_ticker_price()`, `manager.buy_alt()`, `manager.sell_alt()`
- Uses original database: `db.set_current_coin()`
- Extends original `AutoTrader` class

Everything else is unchanged from the original repo.

## How It Works

1. Every `SCOUT_SLEEP_TIME` seconds (default 60), the `scout()` method runs
2. It fetches SOL/USDT price using original `get_ticker_price()` method
3. Calculates RSI(21) locally on price history
4. When RSI < 25, calls `manager.buy_alt()` to buy SOL
5. When RSI > 95, calls `manager.sell_alt()` to sell SOL

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | - | Binance API Key |
| `API_SECRET_KEY` | - | Binance API Secret |
| `STRATEGY` | default | Set to `rsi` |
| `BRIDGE_SYMBOL` | USDT | Bridge currency |
| `SUPPORTED_COIN_LIST` | - | Coins to trade (set to SOL) |
| `SCOUT_SLEEP_TIME` | 60 | Seconds between checks |

## Requirements

- Python 3.8+
- Binance account with API key
- SQLite3

## License

GPL-3.0 (same as original)
