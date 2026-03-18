# RSI Strategy - Implements RSI(21,25,95) on SOL/USDT
# Extends AutoTrader from original binance-trade-bot

from .binance_api_manager import BinanceAPIManager
from .config import Config
from .crypto_trading import main
from .database import Database
from .logger import Logger
from .models import Coin
from .auto_trader import AutoTrader


class RSIStrategy(AutoTrader):
    def __init__(self, manager: BinanceAPIManager, db: Database, logger: Logger, config: Config):
        super().__init__(manager, db, logger, config)
        
        # RSI Parameters
        self.rsi_period = 21
        self.rsi_oversold = 25
        self.rsi_overbought = 95
        
        # Trading pair - use config bridge and SOL
        self.trade_coin_symbol = "SOL"
        
        # Track position
        self.position = None
        
        # Store historical prices for RSI
        self.price_history = []
        
        self.logger.info(f"RSI Strategy initialized: RSI({self.rsi_period},{self.rsi_oversold},{self.rsi_overbought})")

    def initialize(self):
        """Initialize the strategy - check current position"""
        super().initialize()
        
        # Check if we already hold SOL
        current_coin = self.db.get_current_coin()
        if current_coin and current_coin.symbol == self.trade_coin_symbol:
            self.position = "BUY"
            self.logger.info(f"Already holding {self.trade_coin_symbol}")
        else:
            self.position = None
            self.logger.info(f"Not holding {self.trade_coin_symbol}")

    def scout(self):
        """Main trading logic - check for RSI signals"""
        try:
            self.logger.info(f"=== SCOUT START ===")
            
            # Get current SOL/USDT price using original API method
            self.logger.info(f"Fetching price for {self.trade_coin_symbol}{self.config.BRIDGE.symbol}...")
            current_price = self.manager.get_ticker_price(self.trade_coin_symbol + self.config.BRIDGE.symbol)
            self.logger.info(f"Price fetched: {current_price}")
            
            if current_price is None:
                self.logger.warning(f"Could not get price for {self.trade_coin_symbol}")
                return
            
            # Add to price history
            self.price_history.append(current_price)
            self.logger.info(f"Price history length: {len(self.price_history)}")
            
            # Keep last 50 prices
            if len(self.price_history) > 50:
                self.price_history = self.price_history[-50:]
            
            # Need enough data for RSI
            if len(self.price_history) < self.rsi_period + 1:
                self.logger.info(f"Not enough data for RSI. Have {len(self.price_history)}, need {self.rsi_period + 1}")
                return
            
            # Calculate RSI locally
            rsi_value = self._calculate_rsi(self.price_history, self.rsi_period)
            
            self.logger.info(f">>> Price: ${current_price}, RSI({self.rsi_period}): {rsi_value:.2f} <<<")
            self.logger.info(f"Position: {self.position}, Oversold threshold: {self.rsi_oversold}, Overbought threshold: {self.rsi_overbought}")
            
            # Check signals
            if self.position is None and rsi_value < self.rsi_oversold:
                # BUY - RSI oversold
                self.logger.info(f">>> RSI oversold ({rsi_value:.2f} < {self.rsi_oversold}) - BUY SIGNAL <<<")
                self._buy_sol()
                
            elif self.position == "BUY" and rsi_value > self.rsi_overbought:
                # SELL - RSI overbought
                self.logger.info(f">>> RSI overbought ({rsi_value:.2f} > {self.rsi_overbought}) - SELL SIGNAL <<<")
                self._sell_sol()
            else:
                self.logger.info("No trading signal")
                
            self.logger.info(f"=== SCOUT END ===")
                
        except Exception as e:
            self.logger.error(f"Error in scout: {e}")

    def _calculate_rsi(self, prices, period):
        """Calculate RSI locally"""
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

    def _buy_sol(self):
        """Buy SOL using original bot method"""
        try:
            # Use Coin model like original
            sol_coin = Coin(self.trade_coin_symbol, False)
            
            # Check USDT balance using original method
            usdt_balance = self.manager.get_currency_balance(self.config.BRIDGE.symbol)
            
            if usdt_balance < 10:
                self.logger.warning(f"Insufficient {self.config.BRIDGE.symbol} balance: {usdt_balance}")
                return
            
            # Use original buy_alt method
            order = self.manager.buy_alt(sol_coin, self.config.BRIDGE)
            
            if order:
                self.position = "BUY"
                self.db.set_current_coin(sol_coin)
                self.logger.info(f"BUY order executed: {order}")
            else:
                self.logger.warning("BUY order failed")
                
        except Exception as e:
            self.logger.error(f"Error executing BUY: {e}")

    def _sell_sol(self):
        """Sell SOL using original bot method"""
        try:
            sol_coin = Coin(self.trade_coin_symbol, False)
            
            # Check SOL balance using original method
            sol_balance = self.manager.get_currency_balance(sol_coin.symbol)
            
            if sol_balance <= 0:
                self.logger.warning(f"No {sol_coin.symbol} to sell")
                return
            
            # Use original sell_alt method
            order = self.manager.sell_alt(sol_coin, self.config.BRIDGE)
            
            if order:
                self.position = None
                self.db.set_current_coin(self.config.BRIDGE)
                self.logger.info(f"SELL order executed: {order}")
            else:
                self.logger.warning("SELL order failed")
                
        except Exception as e:
            self.logger.error(f"Error executing SELL: {e}")


def get_strategy(name: str):
    """Get strategy by name"""
    if name == "rsi":
        return RSIStrategy
    return None
