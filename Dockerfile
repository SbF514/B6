FROM python:3.11-slim

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy rest of files
COPY . .

CMD ["python", "-m", "binance_trade_bot"]
