FROM python:3.11-slim

WORKDIR /app

# Install dependencies without conflicting with system packages
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

CMD ["python", "-m", "binance_trade_bot"]
