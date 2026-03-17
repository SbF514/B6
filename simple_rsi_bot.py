#!/usr/bin/env python3
"""
RSI Trading Bot - RSI(21,25,95) on SOL/USDT
Uses Binance TESTNET for paper trading
"""

import os
import time
import logging
from binance.client import Client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.environ.get('API_KEY', '')
API_SECRET = os.environ.get('API_SECRET', '')
TESTNET = os.environ.get('TESTNET', 'false').lower() in ('true', '1', 'yes')
SYMBOL = 'SOLUSDT'
RSI_PERIOD = 21
OVERSOLD = 25
OVERBOUGHT = 95
CHECK_INTERVAL = 60  # seconds

class RSIBot:
    def __init__(self):
        # Use testnet if TESTNET=true
        self.client = Client(API_KEY, API_SECRET, testnet=TESTNET)
        self.position = None
        self.price_history = []
        logger.info(f"RSI Bot initialized: RSI({RSI_PERIOD},{OVERSOLD},{OVERBOUGHT}) on {SYMBOL}")
        if TESTNET:
            logger.info("*** TESTNET MODE - Using Binance Testnet ***")
    
    def get_price(self):
        try:
            ticker = self.client.get_symbol_ticker(symbol=SYMBOL)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None
    
    def calculate_rsi(self, prices, period):
        if len(prices) < period + 1:
            return 50
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def get_balance(self, asset):
        try:
            acc = self.client.get_account()
            for bal in acc['balances']:
                if bal['asset'] == asset:
                    return float(bal['free'])
            return 0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0
    
    def buy(self):
        try:
            usdt = self.get_balance('USDT')
            if usdt < 10:
                logger.warning(f"Insufficient USDT: {usdt}")
                return False
            
            price = self.get_price()
            quantity = (usdt * 0.99) / price
            
            order = self.client.order_market_buy(symbol=SYMBOL, quantity=quantity)
            logger.info(f"BUY order executed: {order}")
            self.position = 'BUY'
            return True
        except Exception as e:
            logger.error(f"Error buying: {e}")
            return False
    
    def sell(self):
        try:
            sol = self.get_balance('SOL')
            if sol <= 0:
                logger.warning("No SOL to sell")
                return False
            
            order = self.client.order_market_sell(symbol=SYMBOL, quantity=sol)
            logger.info(f"SELL order executed: {order}")
            self.position = None
            return True
        except Exception as e:
            logger.error(f"Error selling: {e}")
            return False
    
    def check_position(self):
        sol = self.get_balance('SOL')
        self.position = 'BUY' if sol > 0 else None
        logger.info(f"Current position: {self.position}")
    
    def run(self):
        logger.info("Starting RSI Bot...")
        
        if TESTNET:
            logger.info("="*50)
            logger.info("*** TESTNET MODE - No real money ***")
            logger.info("="*50)
        
        self.check_position()
        
        while True:
            try:
                price = self.get_price()
                if price is None:
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                self.price_history.append(price)
                if len(self.price_history) > 50:
                    self.price_history = self.price_history[-50:]
                
                if len(self.price_history) < RSI_PERIOD + 1:
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                rsi = self.calculate_rsi(self.price_history, RSI_PERIOD)
                logger.info(f"Price: ${price}, RSI({RSI_PERIOD}): {rsi:.2f}")
                
                # Check signals
                if self.position is None and rsi < OVERSOLD:
                    mode = "[TESTNET] " if TESTNET else ""
                    logger.info(f"{mode}RSI oversold ({rsi:.2f} < {OVERSOLD}) - BUYING")
                    self.buy()
                elif self.position == 'BUY' and rsi > OVERBOUGHT:
                    mode = "[TESTNET] " if TESTNET else ""
                    logger.info(f"{mode}RSI overbought ({rsi:.2f} > {OVERBOUGHT}) - SELLING")
                    self.sell()
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    if not API_KEY or not API_SECRET:
        print("Please set API_KEY and API_SECRET environment variables:")
        print("  export API_KEY='your_api_key'")
        print("  export API_SECRET='your_api_secret'")
        print("\nFor paper trading (testnet):")
        print("  export TESTNET=true")
        exit(1)
    
    if TESTNET:
        print("="*50)
        print("TESTNET MODE - Using Binance Testnet")
        print("="*50)
    
    bot = RSIBot()
    bot.run()
