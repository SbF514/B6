FROM python:3.11-slim

WORKDIR /app

# Install dependencies with newer pip resolver
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install with relaxed dependencies
RUN pip install --no-cache-dir python-binance sqlalchemy schedule apprise flask gunicorn flask-cors flask-socketio eventlet python-socketio cachetools sqlitedict unicorn-binance-websocket-api unicorn-fy

COPY . .

CMD ["python", "-m", "binance_trade_bot"]
