# RSI Trading Bot

Automated cryptocurrency trading bot using RSI(21,25,95) strategy on SOL/USDT.

## Strategy
- **Buy Signal**: RSI(21) drops below 25 (oversold)
- **Sell Signal**: RSI(21) rises above 95 (overbought)
- **Trading Pair**: SOL/USDT

## Backtest Results (0.1% fee included)
- Average Weekly Return: +4.42%
- Profitable Weeks: 4/4 (100%)

## Binance Account Setup

### 1. Create API Key
1. Log into Binance
2. Go to Account → API Management
3. Create New API Key
4. **Permissions:** Read & Trade (NOT Withdrawal)
5. Save your API Key and Secret

### 2. Fund Account
- Deposit USDT (recommended $100+)
- Or deposit SOL

## Installation

### Option A - Direct Run
```bash
pip install -r requirements.txt
export API_KEY="your_binance_api_key"
export API_SECRET_KEY="your_binance_api_secret"
python -m binance_trade_bot
```

### Option B - Docker
```bash
echo "API_KEY=your_key" > .env
echo "API_SECRET_KEY=your_secret" >> .env
docker-compose up -d
```

### Option C - Heroku
```bash
heroku create your-bot-name
heroku config:set API_KEY=your_key
heroku config:set API_SECRET_KEY=your_secret
git push heroku main
```

## Configuration

### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | - | Binance API Key |
| `API_SECRET_KEY` | Yes | - | Binance API Secret |
| `STRATEGY` | No | rsi | Strategy name |
| `BRIDGE_SYMBOL` | No | USDT | Bridge currency |
| `SUPPORTED_COIN_LIST` | No | SOL | Coins to trade |
| `SCOUT_SLEEP_TIME` | No | 60 | Seconds between checks |

### Or use user.cfg
```ini
[binance_user_config]
api_key = YOUR_API_KEY
api_secret_key = YOUR_API_SECRET
bridge = USDT
strategy = rsi
```

## How It Works

1. Every 60 seconds, bot fetches SOL/USDT price via REST API
2. Calculates RSI(21) on local price history
3. **BUY** when RSI < 25 (oversold)
4. **SELL** when RSI > 95 (overbought)
5. Repeats

## Files

```
B6/
├── binance_trade_bot/
│   ├── __main__.py          # Entry point
│   ├── config.py             # Configuration
│   ├── binance_api_manager.py # Binance REST API
│   └── strategies/
│       └── rsi_strategy.py  # RSI strategy
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## Requirements

- Python 3.8+
- Binance account with API key
- SQLite3

## License

GPL-3.0
