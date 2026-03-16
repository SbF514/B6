# RSI Strategy - Implements RSI(21,25,95) on SOL/USDT
# Uses REST API only - NO WEBSOCKET for price data

import logging
import time

from .binance_api_manager import BinanceAPIManager
from .config import Config
from .crypto_trading import CryptoTrading
from .database import Database
from .logger import Logger
from .models import Coin


class RSIStrategy(CryptoTrading):
    def __init__(self, manager: BinanceAPIManager, db: Database, logger: Logger, config: Config):
        super().__init__(manager, db, logger, config)
        
        # RSI Parameters - Hardcoded (no need to change)
        self.rsi_period = 21
        self.rsi_oversold = 25
        self.rsi_overbought = 95
        
        # Trading pair
        self.bridge = Coin("USDT", False)
        self.trade_coin = Coin("SOL", False)
        
        # Track position
        self.position = None
        
        # Store historical prices for RSI
        self.price_history = []
        
        # RSI calculation uses LOCAL data only - NO WEBSOCKET
        self.logger.info(f"RSI Strategy initialized: RSI({self.rsi_period},{self.rsi_oversold},{self.rsi_overbought})")
        self.logger.info("Using REST API only - no WebSocket for price data")

    def initialize(self):
        """Initialize the strategy"""
        self.logger.info("Initializing RSI strategy")
        
        # Check current position via REST API
        current_balance = self.manager.get_currency_balance(self.trade_coin.symbol)
        if current_balance > 0:
            self.position = "BUY"
            self.logger.info(f"Already holding {current_balance} {self.trade_coin.symbol}")
        else:
            self.position = None
            self.logger.info("Not holding any position")

    def scout(self):
        """Main trading logic - uses REST API only"""
        try:
            # Get current price via REST API (no WebSocket)
            ticker = str(self.trade_coin + self.bridge)
            current_price = self.manager.binance_client.get_symbol_ticker(symbol=ticker)
            current_price = float(current_price['price'])
            
            if current_price is None:
                self.logger.warning("Could not get price")
                return
            
            # Add to price history
            self.price_history.append(current_price)
            
            # Keep last 50 prices
            if len(self.price_history) > 50:
                self.price_history = self.price_history[-50:]
            
            # Need enough data for RSI
            if len(self.price_history) < self.rsi_period + 1:
                return
            
            # Calculate RSI locally
            rsi_value = self.calculate_rsi(self.price_history, self.rsi_period)
            
            self.logger.info(f"Current RSI({self.rsi_period}): {rsi_value:.2f}, Price: ${current_price}")
            
            # Check signals
            if self.position is None and rsi_value < self.rsi_oversold:
                self.logger.info(f"RSI oversold ({rsi_value:.2f} < {self.rsi_oversold}) - BUY")
                self.execute_buy()
                
            elif self.position == "BUY" and rsi_value > self.rsi_overbought:
                self.logger.info(f"RSI overbought ({rsi_value:.2f} > {self.rsi_overbought}) - SELL")
                self.execute_sell()
                
        except Exception as e:
            self.logger.error(f"Error in scout: {e}")

    def calculate_rsi(self, prices, period):
        """Calculate RSI locally - no external data"""
        if len(prices) < period + 1:
            return 50
        
        deltas = []
        for i in range(1, len(prices)):
            deltas.append(prices[i] - prices[i-1])
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def execute_buy(self):
        """Execute buy order via REST API"""
        try:
            # Check balance via REST
            usdt_balance = self.manager.get_currency_balance(self.bridge.symbol)
            
            if usdt_balance < 10:
                self.logger.warning(f"Insufficient {self.bridge.symbol} balance: {usdt_balance}")
                return
            
            self.logger.info(f"Buying {self.trade_coin.symbol} with {usdt_balance} {self.bridge.symbol}")
            
            # Use REST API for order
            order = self.manager.buy_alt(self.trade_coin, self.bridge)
            
            if order:
                self.position = "BUY"
                self.logger.info(f"BUY executed: {order}")
            else:
                self.logger.warning("BUY order failed")
                
        except Exception as e:
            self.logger.error(f"Error executing BUY: {e}")

    def execute_sell(self):
        """Execute sell order via REST API"""
        try:
            coin_balance = self.manager.get_currency_balance(self.trade_coin.symbol)
            
            if coin_balance <= 0:
                self.logger.warning(f"No {self.trade_coin.symbol} to sell")
                return
            
            self.logger.info(f"Selling {coin_balance} {self.trade_coin.symbol}")
            
            # Use REST API for order
            order = self.manager.sell_alt(self.trade_coin, self.bridge)
            
            if order:
                self.position = None
                self.logger.info(f"SELL executed: {order}")
            else:
                self.logger.warning("SELL order failed")
                
        except Exception as e:
            self.logger.error(f"Error executing SELL: {e}")


def get_strategy(name: str):
    """Get strategy by name"""
    if name == "rsi":
        return RSIStrategy
    return None
