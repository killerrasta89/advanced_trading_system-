"""
Momentum Strategy - Momentum alapú kereskedési stratégia
"""
import logging
import numpy as np
from strategies.base_strategy import BaseStrategy

class MomentumStrategy(BaseStrategy):
    """
    Momentum stratégia implementációja
    
    A stratégia az árfolyam lendületét (momentum) követi, és a trendek irányába
    kereskedik. Amikor az árfolyam erős pozitív momentumot mutat, vásárol,
    amikor pedig negatív momentumot, elad.
    """
    
    def __init__(self, name, symbol, timeframe, exchange, risk_manager=None):
        """
        Inicializálja a Momentum stratégiát
        
        Args:
            name: Stratégia neve
            symbol: Kereskedési szimbólum (pl. "BTC/USDT")
            timeframe: Időkeret (pl. "1h", "15m", "1d")
            exchange: Tőzsde objektum
            risk_manager: Kockázatkezelő objektum (opcionális)
        """
        super().__init__(name, symbol, timeframe, exchange, risk_manager)
        
        # Momentum stratégia specifikus beállítások
        self.config.update({
            'momentum_period': 14,     # Momentum számítási periódus
            'rsi_period': 14,          # RSI periódus
            'rsi_overbought': 70,      # RSI túlvett szint
            'rsi_oversold': 30,        # RSI túladott szint
            'macd_fast_period': 12,    # MACD gyors periódus
            'macd_slow_period': 26,    # MACD lassú periódus
            'macd_signal_period': 9,   # MACD jelzés periódus
            'volume_factor': 1.5,      # Volumen szorzó (átlag feletti volumen)
            'take_profit_pct': 3.0,    # Take profit százalék
            'stop_loss_pct': 2.0,      # Stop loss százalék
            'trailing_stop_pct': 1.0,  # Trailing stop százalék
            'position_size_pct': 10.0, # Pozíció méret a portfólió százalékában
        })
        
        # Momentum stratégia állapot
        self.current_position = None
        self.entry_price = 0
        self.highest_price = 0
        self.lowest_price = 0
        
    def initialize(self):
        """
        Momentum stratégia inicializálása
        """
        super().initialize()
        self.logger.info("Momentum stratégia inicializálása")
    
    def calculate_momentum_indicators(self, data):
        """
        Momentum indikátorok számítása
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            DataFrame: Indikátorokkal kiegészített adatok
        """
        # Alap indikátorok számítása
        data = self.calculate_indicators(data)
        
        if len(data) > self.config['momentum_period']:
            # Momentum indikátor
            data['momentum'] = data['close'].diff(self.config['momentum_period'])
            
            # Rate of Change (ROC)
            data['roc'] = data['close'].pct_change(self.config['momentum_period']) * 100
            
            # Volumen alapú indikátorok
            data['volume_sma'] = data['volume'].rolling(window=20).mean()
            data['volume_ratio'] = data['volume'] / data['volume_sma']
            
            # Átlagos Directional Index (ADX)
            high_diff = data['high'].diff()
            low_diff = -data['low'].diff()
            
            plus_dm = ((high_diff > 0) & (high_diff > low_diff)) * high_diff
            minus_dm = ((low_diff > 0) & (low_diff > high_diff)) * low_diff
            
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            
            tr = data['high'] - data['low']
            tr = tr.combine(abs(data['high'] - data['close'].shift()), max)
            tr = tr.combine(abs(data['low'] - data['close'].shift()), max)
            
            atr = tr.rolling(window=14).mean()
            
            plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            data['adx'] = dx.rolling(window=14).mean()
            
            # Chaikin Money Flow (CMF)
            mfv = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
            mfv = mfv * data['volume']
            data['cmf'] = mfv.rolling(window=20).sum() / data['volume'].rolling(window=20).sum()
        
        return data
    
    def generate_signal(self, data):
        """
        Kereskedési jel generálása az adatok alapján
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            dict: Kereskedési jel vagy None
        """
        if len(data) < max(self.config['momentum_period'], self.config['macd_slow_period']) + 10:
            return None
        
        # Momentum indikátorok számítása
        data = self.calculate_momentum_indicators(data)
        
        # Aktuális ár és indikátor értékek
        current_price = data['close'].iloc[-1]
        current_rsi = data['rsi'].iloc[-1]
        prev_rsi = data['rsi'].iloc[-2]
        
        current_macd = data['macd'].iloc[-1]
        current_macd_signal = data['macd_signal'].iloc[-1]
        prev_macd = data['macd'].iloc[-2]
        prev_macd_signal = data['macd_signal'].iloc[-2]
        
        current_momentum = data['momentum'].iloc[-1]
        prev_momentum = data['momentum'].iloc[-2]
        
        current_volume_ratio = data['volume_ratio'].iloc[-1]
        
        current_adx = data['adx'].iloc[-1]
        current_cmf = data['cmf'].iloc[-1]
        
        # Vételi feltételek
        buy_signal = (
            # RSI túladott zónából felfelé
            (prev_rsi < self.config['rsi_oversold'] and current_rsi > self.config['rsi_oversold']) or
            # MACD kereszteződés felfelé
            (prev_macd < prev_macd_signal and current_macd > current_macd_signal) or
            # Pozitív momentum növekedés
            (prev_momentum < 0 and current_momentum > 0)
        )
        
        # További megerősítő feltételek
        buy_confirmation = (
            # Átlag feletti volumen
            current_volume_ratio > self.config['volume_factor'] and
            # Erős trend (ADX > 25)
            current_adx > 25 and
            # Pozitív pénzáramlás
            current_cmf > 0
        )
        
        # Eladási feltételek
        sell_signal = (
            # RSI túlvett zónából lefelé
            (prev_rsi > self.config['rsi_overbought'] and current_rsi < self.config['rsi_overbought']) or
            # MACD kereszteződés lefelé
            (prev_macd > prev_macd_signal and current_macd < current_macd_signal) or
            # Negatív momentum csökkenés
            (prev_momentum > 0 and current_momentum < 0)
        )
        
        # További megerősítő feltételek
        sell_confirmation = (
            # Átlag feletti volumen
            current_volume_ratio > self.config['volume_factor'] and
            # Erős trend (ADX > 25)
            current_adx > 25 and
            # Negatív pénzáramlás
            current_cmf < 0
        )
        
        # Pozíció kezelés
        if self.current_position is None:
            # Nincs nyitott pozíció, új pozíció nyitása
            if buy_signal and buy_confirmation:
                # Pozíció méret kiszámítása
                position_size = self.calculate_position_size(current_price)
                
                # Vételi jel
                signal = {
                    'action': 'buy',
                    'price': current_price,
                    'volume': position_size,
                    'type': 'market',
                    'params': {
                        'stop_loss': current_price * (1 - self.config['stop_loss_pct'] / 100),
                        'take_profit': current_price * (1 + self.config['take_profit_pct'] / 100),
                        'trailing_stop': self.config['trailing_stop_pct']
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = 'long'
                self.entry_price = current_price
                self.highest_price = current_price
                
                return signal
                
            elif sell_signal and sell_confirmation:
                # Pozíció méret kiszámítása
                position_size = self.calculate_position_size(current_price)
                
                # Eladási jel (short pozíció)
                signal = {
                    'action': 'sell',
                    'price': current_price,
                    'volume': position_size,
                    'type': 'market',
                    'params': {
                        'stop_loss': current_price * (1 + self.config['stop_loss_pct'] / 100),
                        'take_profit': current_price * (1 - self.config['take_profit_pct'] / 100),
                        'trailing_stop': self.config['trailing_stop_pct']
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = 'short'
                self.entry_price = current_price
                self.lowest_price = current_price
                
                return signal
        
        elif self.current_position == 'long':
            # Long pozíció kezelése
            
            # Trailing stop frissítése
            if current_price > self.highest_price:
                self.highest_price = current_price
            
            # Stop loss ellenőrzése
            trailing_stop_price = self.highest_price * (1 - self.config['trailing_stop_pct'] / 100)
            
            if current_price < trailing_stop_price:
                # Pozíció zárása trailing stop miatt
                signal = {
                    'action': 'sell',
                    'price': current_price,
                    'volume': 'all',
                    'type': 'market',
                    'params': {
                        'reason': 'trailing_stop',
                        'profit_pct': (current_price / self.entry_price - 1) * 100
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = None
                
                return signal
            
            # Take profit ellenőrzése
            take_profit_price = self.entry_price * (1 + self.config['take_profit_pct'] / 100)
            
            if current_price >= take_profit_price:
                # Pozíció zárása take profit miatt
                signal = {
                    'action': 'sell',
                    'price': current_price,
                    'volume': 'all',
                    'type': 'market',
                    'params': {
                        'reason': 'take_profit',
                        'profit_pct': (current_price / self.entry_price - 1) * 100
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = None
                
                return signal
            
            # Eladási jel ellenőrzése
            if sell_signal and sell_confirmation:
                # Pozíció zárása eladási jel miatt
                signal = {
                    'action': 'sell',
                    'price': current_price,
                    'volume': 'all',
                    'type': 'market',
                    'params': {
                        'reason': 'signal',
                        'profit_pct': (current_price / self.entry_price - 1) * 100
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = None
                
                return signal
        
        elif self.current_position == 'short':
            # Short pozíció kezelése
            
            # Trailing stop frissítése
            if current_price < self.lowest_price:
                self.lowest_price = current_price
            
            # Stop loss ellenőrzése
            trailing_stop_price = self.lowest_price * (1 + self.config['trailing_stop_pct'] / 100)
            
            if current_price > trailing_stop_price:
                # Pozíció zárása trailing stop miatt
                signal = {
                    'action': 'buy',
                    'price': current_price,
                    'volume': 'all',
                    'type': 'market',
                    'params': {
                        'reason': 'trailing_stop',
                        'profit_pct': (self.entry_price / current_price - 1) * 100
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = None
                
                return signal
            
            # Take profit ellenőrzése
            take_profit_price = self.entry_price * (1 - self.config['take_profit_pct'] / 100)
            
            if current_price <= take_profit_price:
                # Pozíció zárása take profit miatt
                signal = {
                    'action': 'buy',
                    'price': current_price,
                    'volume': 'all',
                    'type': 'market',
                    'params': {
                        'reason': 'take_profit',
                        'profit_pct': (self.entry_price / current_price - 1) * 100
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = None
                
                return signal
            
            # Vételi jel ellenőrzése
            if buy_signal and buy_confirmation:
                # Pozíció zárása vételi jel miatt
                signal = {
                    'action': 'buy',
                    'price': current_price,
                    'volume': 'all',
                    'type': 'market',
                    'params': {
                        'reason': 'signal',
                        'profit_pct': (self.entry_price / current_price - 1) * 100
                    }
                }
                
                # Pozíció állapot frissítése
                self.current_position = None
                
                return signal
        
        return None
    
    def calculate_position_size(self, price):
        """
        Pozíció méret kiszámítása
        
        Args:
            price: Aktuális ár
            
        Returns:
            float: Pozíció méret
        """
        # Portfólió érték lekérdezése
        try:
            portfolio_value = self.exchange.get_balance()['total']['USDT']
        except:
            # Ha nem sikerül lekérdezni, használjunk egy alapértelmezett értéket
            portfolio_value = 10000
        
        # Pozíció méret a portfólió százalékában
        position_value = portfolio_value * (self.config['position_size_pct'] / 100)
        
        # Mennyiség kiszámítása
        quantity = position_value / price
        
        return quantity
    
    def reset_position(self):
        """
        Pozíció állapot visszaállítása
        """
        self.current_position = None
        self.entry_price = 0
        self.highest_price = 0
        self.lowest_price = 0
