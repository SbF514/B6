# RSI Strategy - Implements RSI(21,25,95) on SOL/USDT
# Extends AutoTrader from original binance-trade-bot

from binance_trade_bot.binance_api_manager import BinanceAPIManager
from binance_trade_bot.config import Config
from binance_trade_bot.crypto_trading import main
from binance_trade_bot.database import Database
from binance_trade_bot.logger import Logger
from binance_trade_bot.models import Coin
from binance_trade_bot.auto_trader import AutoTrader


class Strategy(AutoTrader):
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
            
            # Fetch historical klines for proper RSI calculation
            symbol = self.trade_coin_symbol + self.config.BRIDGE.symbol
            self.logger.info(f"Fetching klines for {symbol}...")
            
            # Get 1-hour klines, last 100 candles
            klines = self.manager.get_klines(symbol, interval="1h", limit=100)
            
            if not klines or len(klines) < self.rsi_period + 1:
                self.logger.warning(f"Not enough kline data: {len(klines) if klines else 0}")
                return
            
            # Use the closing prices from klines
            self.price_history = klines
            current_price = klines[-1]
            
            # Debug
            price_min = min(klines[-30:])
            price_max = max(klines[-30:])
            self.logger.info(f"Klines: {len(klines)} points, range: {price_min:.2f} - {price_max:.2f}")
            
            # Calculate RSI from historical data
            rsi_value = self._calculate_rsi(self.price_history, self.rsi_period)
            
            self.logger.info(f">>> Price: ${current_price}, RSI({self.rsi_period}): {rsi_value:.2f} <<<")
            self.logger.info(f"Position: {self.position}, Oversold: {self.rsi_oversold}, Overbought: {self.rsi_overbought}")
            
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
        """Calculate RSI properly"""
        if len(prices) < period + 1:
            return 50
        
        # Get recent changes
        changes = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            changes.append(change)
        
        if len(changes) < period:
            return 50
        
        # Use only the last period changes for calculation
        recent = changes[-period:]
        
        gains = [c for c in recent if c > 0]
        losses = [-c for c in recent if c < 0]
        
        if not gains:
            return 100  # All negative or zero
        if not losses:
            return 0  # All positive
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Clamp to valid range
        return max(0, min(100, rsi))

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
        return Strategy
    return None
