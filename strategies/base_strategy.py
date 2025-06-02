"""
Base Strategy - Alap stratégia osztály
"""
from abc import ABC, abstractmethod
import logging
import pandas as pd
import numpy as np
from datetime import datetime

class BaseStrategy(ABC):
    """
    Alap stratégia osztály, amelyből minden konkrét stratégia származik
    """
    
    def __init__(self, name, symbol, timeframe, exchange, risk_manager=None):
        """
        Inicializálja az alap stratégiát
        
        Args:
            name: Stratégia neve
            symbol: Kereskedési szimbólum (pl. "BTC/USDT")
            timeframe: Időkeret (pl. "1h", "15m", "1d")
            exchange: Tőzsde objektum
            risk_manager: Kockázatkezelő objektum (opcionális)
        """
        self.name = name
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange = exchange
        self.risk_manager = risk_manager
        self.logger = logging.getLogger(f"strategy.{name}")
        
        # Stratégia állapot
        self.is_active = False
        self.last_update_time = None
        self.last_signal = None
        
        # Teljesítmény metrikák
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        }
        
        # Konfiguráció
        self.config = {}
        
        # Inicializálás
        self.initialize()
        
    def initialize(self):
        """
        Stratégia inicializálása, felülírható a leszármazott osztályokban
        """
        self.logger.info(f"Stratégia inicializálása: {self.name} - {self.symbol} - {self.timeframe}")
    
    @abstractmethod
    def generate_signal(self, data):
        """
        Kereskedési jel generálása az adatok alapján
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            dict: Kereskedési jel (pl. {'action': 'buy', 'price': 50000, 'volume': 0.1})
        """
        pass
    
    def update(self, data):
        """
        Stratégia frissítése új adatokkal
        
        Args:
            data: Új piaci adatok
            
        Returns:
            dict: Kereskedési jel vagy None
        """
        self.last_update_time = datetime.now()
        
        if not self.is_active:
            self.logger.debug(f"Stratégia nem aktív: {self.name}")
            return None
        
        # Jel generálása
        signal = self.generate_signal(data)
        
        # Kockázatkezelés alkalmazása, ha van
        if signal and self.risk_manager:
            signal = self.risk_manager.validate_signal(signal, self, data)
        
        # Jel naplózása
        if signal:
            self.logger.info(f"Kereskedési jel: {signal}")
            self.last_signal = signal
        
        return signal
    
    def activate(self):
        """
        Stratégia aktiválása
        """
        self.is_active = True
        self.logger.info(f"Stratégia aktiválva: {self.name}")
    
    def deactivate(self):
        """
        Stratégia deaktiválása
        """
        self.is_active = False
        self.logger.info(f"Stratégia deaktiválva: {self.name}")
    
    def set_config(self, config):
        """
        Stratégia konfigurálása
        
        Args:
            config: Konfigurációs beállítások
        """
        self.config.update(config)
        self.logger.info(f"Stratégia konfigurálva: {self.name}")
    
    def update_performance(self, trade_result):
        """
        Teljesítmény metrikák frissítése egy kereskedés eredménye alapján
        
        Args:
            trade_result: Kereskedés eredménye (dict)
        """
        self.performance['total_trades'] += 1
        
        if trade_result['profit'] > 0:
            self.performance['winning_trades'] += 1
            self.performance['total_profit'] += trade_result['profit']
        else:
            self.performance['losing_trades'] += 1
            self.performance['total_loss'] += abs(trade_result['profit'])
        
        # Win rate számítása
        if self.performance['total_trades'] > 0:
            self.performance['win_rate'] = self.performance['winning_trades'] / self.performance['total_trades'] * 100
        
        # Profit factor számítása
        if self.performance['total_loss'] > 0:
            self.performance['profit_factor'] = self.performance['total_profit'] / self.performance['total_loss']
        
        # Max drawdown frissítése
        if 'drawdown' in trade_result and trade_result['drawdown'] > self.performance['max_drawdown']:
            self.performance['max_drawdown'] = trade_result['drawdown']
    
    def get_performance(self):
        """
        Teljesítmény metrikák lekérdezése
        
        Returns:
            dict: Teljesítmény metrikák
        """
        return self.performance
    
    def calculate_indicators(self, data):
        """
        Technikai indikátorok számítása
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            DataFrame: Indikátorokkal kiegészített adatok
        """
        # Alap indikátorok számítása
        if len(data) > 0:
            # Mozgóátlagok
            data['sma_20'] = data['close'].rolling(window=20).mean()
            data['sma_50'] = data['close'].rolling(window=50).mean()
            data['sma_200'] = data['close'].rolling(window=200).mean()
            
            # Exponenciális mozgóátlagok
            data['ema_12'] = data['close'].ewm(span=12, adjust=False).mean()
            data['ema_26'] = data['close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
            data['macd_hist'] = data['macd'] - data['macd_signal']
            
            # RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            data['bb_middle'] = data['close'].rolling(window=20).mean()
            data['bb_std'] = data['close'].rolling(window=20).std()
            data['bb_upper'] = data['bb_middle'] + 2 * data['bb_std']
            data['bb_lower'] = data['bb_middle'] - 2 * data['bb_std']
            
            # ATR (Average True Range)
            high_low = data['high'] - data['low']
            high_close = (data['high'] - data['close'].shift()).abs()
            low_close = (data['low'] - data['close'].shift()).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            data['atr'] = true_range.rolling(14).mean()
        
        return data
    
    def __str__(self):
        """
        Stratégia string reprezentációja
        
        Returns:
            str: Stratégia leírása
        """
        return f"{self.name} ({self.symbol}, {self.timeframe})"
