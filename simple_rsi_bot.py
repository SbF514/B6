#!/usr/bin/env python3
"""
RSI Trading Bot - RSI(21,25,95) on SOL/USDT
Minimal version - REST API only
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
TEST_MODE = os.environ.get('TEST_MODE', 'false').lower() in ('true', '1', 'yes')
SYMBOL = 'SOLUSDT'
RSI_PERIOD = 21
OVERSOLD = 25
OVERBOUGHT = 95
CHECK_INTERVAL = 60  # seconds

class RSIBot:
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        self.position = None
        self.price_history = []
        
        # Paper trading state
        self.paper_balance_usdt = 10000  # Start with $10,000 fake USDT
        self.paper_balance_sol = 0
        
        if TEST_MODE:
            logger.info(f"TEST MODE ENABLED - Paper Trading")
            logger.info(f"Starting paper balance: ${self.paper_balance_usdt:.2f}")
        logger.info(f"RSI Bot initialized: RSI({RSI_PERIOD},{OVERSOLD},{OVERBOUGHT}) on {SYMBOL}")
    
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
        if TEST_MODE:
            if asset == 'USDT':
                return self.paper_balance_usdt
            elif asset == 'SOL':
                return self.paper_balance_sol
            return 0
        
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
        if TEST_MODE:
            # Paper trade - just log
            price = self.get_price()
            if price and self.paper_balance_usdt >= 10:
                quantity = (self.paper_balance_usdt * 0.99) / price
                cost = quantity * price
                self.paper_balance_sol = quantity
                self.paper_balance_usdt -= cost
                logger.info(f"[PAPER] BUY {quantity:.4f} SOL at ${price:.2f} = ${cost:.2f}")
                logger.info(f"[PAPER] New balance: ${self.paper_balance_usdt:.2f} USDT, {self.paper_balance_sol:.4f} SOL")
                self.position = 'BUY'
            return True
        
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
        if TEST_MODE:
            # Paper trade - just log
            price = self.get_price()
            if price and self.paper_balance_sol > 0:
                proceeds = self.paper_balance_sol * price
                self.paper_balance_usdt += proceeds * 0.999  # Simulate 0.1% fee
                logger.info(f"[PAPER] SELL {self.paper_balance_sol:.4f} SOL at ${price:.2f} = ${proceeds:.2f}")
                logger.info(f"[PAPER] New balance: ${self.paper_balance_usdt:.2f} USDT, 0 SOL")
                self.paper_balance_sol = 0
                self.position = None
            return True
        
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
        if TEST_MODE:
            self.position = 'BUY' if self.paper_balance_sol > 0 else None
            logger.info(f"[PAPER] Current position: {self.position}, Balance: ${self.paper_balance_usdt:.2f}")
            return
        
        sol = self.get_balance('SOL')
        self.position = 'BUY' if sol > 0 else None
        logger.info(f"Current position: {self.position}")
    
    def run(self):
        logger.info("Starting RSI Bot...")
        
        if TEST_MODE:
            logger.info("="*50)
            logger.info("PAPER TRADING MODE - NO REAL MONEY")
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
                    mode = "[PAPER] " if TEST_MODE else ""
                    logger.info(f"{mode}RSI oversold ({rsi:.2f} < {OVERSOLD}) - BUYING")
                    self.buy()
                elif self.position == 'BUY' and rsi > OVERBOUGHT:
                    mode = "[PAPER] " if TEST_MODE else ""
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
        print("\nOptional - Paper Trading:")
        print("  export TEST_MODE=true")
        print("  (Set TEST_MODE=true to simulate trades without real money)")
        exit(1)
    
    if TEST_MODE:
        print("="*50)
        print("PAPER TRADING MODE ENABLED")
        print("="*50)
    
    bot = RSIBot()
    bot.run()
