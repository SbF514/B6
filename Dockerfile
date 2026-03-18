FROM python:3.11-slim

WORKDIR /app

# Create data directories
RUN mkdir -p /app/data /app/logs

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "binance_trade_bot"]
