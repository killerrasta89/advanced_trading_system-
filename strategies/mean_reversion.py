"""
Mean Reversion Strategy - Átlaghoz visszatérő stratégia
"""
import logging
import numpy as np
from strategies.base_strategy import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion (Átlaghoz visszatérő) stratégia implementációja
    
    A stratégia abból a feltételezésből indul ki, hogy az árak idővel visszatérnek
    az átlagukhoz. Amikor az ár jelentősen eltér az átlagtól, a stratégia
    az átlaghoz való visszatérésre fogad.
    """
    
    def __init__(self, name, symbol, timeframe, exchange, risk_manager=None):
        """
        Inicializálja a Mean Reversion stratégiát
        
        Args:
            name: Stratégia neve
            symbol: Kereskedési szimbólum (pl. "BTC/USDT")
            timeframe: Időkeret (pl. "1h", "15m", "1d")
            exchange: Tőzsde objektum
            risk_manager: Kockázatkezelő objektum (opcionális)
        """
        super().__init__(name, symbol, timeframe, exchange, risk_manager)
        
        # Mean Reversion stratégia specifikus beállítások
        self.config.update({
            'ma_period': 20,          # Mozgóátlag periódus
            'std_dev_period': 20,     # Szórás számítási periódus
            'entry_std_dev': 2.0,     # Belépési szórás szorzó
            'exit_std_dev': 0.5,      # Kilépési szórás szorzó
            'rsi_period': 14,         # RSI periódus
            'rsi_overbought': 70,     # RSI túlvett szint
            'rsi_oversold': 30,       # RSI túladott szint
            'take_profit_pct': 2.0,   # Take profit százalék
            'stop_loss_pct': 3.0,     # Stop loss százalék
            'max_positions': 3,       # Maximális nyitott pozíciók száma
            'position_size_pct': 10.0, # Pozíció méret a portfólió százalékában
        })
        
        # Mean Reversion stratégia állapot
        self.open_positions = {}  # Nyitott pozíciók: {id: {entry_price, volume, side}}
        
    def initialize(self):
        """
        Mean Reversion stratégia inicializálása
        """
        super().initialize()
        self.logger.info("Mean Reversion stratégia inicializálása")
    
    def calculate_mean_reversion_indicators(self, data):
        """
        Mean Reversion indikátorok számítása
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            DataFrame: Indikátorokkal kiegészített adatok
        """
        # Alap indikátorok számítása
        data = self.calculate_indicators(data)
        
        if len(data) > max(self.config['ma_period'], self.config['std_dev_period']):
            # Bollinger sávok
            data['bb_middle'] = data['close'].rolling(window=self.config['ma_period']).mean()
            data['bb_std'] = data['close'].rolling(window=self.config['std_dev_period']).std()
            data['bb_upper'] = data['bb_middle'] + self.config['entry_std_dev'] * data['bb_std']
            data['bb_lower'] = data['bb_middle'] - self.config['entry_std_dev'] * data['bb_std']
            
            # Z-score (hány szórásnyira van az ár az átlagtól)
            data['z_score'] = (data['close'] - data['bb_middle']) / data['bb_std']
            
            # Átlaghoz való távolság százalékban
            data['pct_from_mean'] = (data['close'] / data['bb_middle'] - 1) * 100
            
            # Stochastic Oscillator
            data['stoch_k'] = ((data['close'] - data['low'].rolling(window=14).min()) / 
                              (data['high'].rolling(window=14).max() - data['low'].rolling(window=14).min())) * 100
            data['stoch_d'] = data['stoch_k'].rolling(window=3).mean()
            
            # Commodity Channel Index (CCI)
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            mean_tp = typical_price.rolling(window=20).mean()
            mean_deviation = abs(typical_price - mean_tp).rolling(window=20).mean()
            data['cci'] = (typical_price - mean_tp) / (0.015 * mean_deviation)
            
            # Williams %R
            data['williams_r'] = ((data['high'].rolling(window=14).max() - data['close']) / 
                                 (data['high'].rolling(window=14).max() - data['low'].rolling(window=14).min())) * -100
        
        return data
    
    def generate_signal(self, data):
        """
        Kereskedési jel generálása az adatok alapján
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            dict: Kereskedési jel vagy None
        """
        if len(data) < max(self.config['ma_period'], self.config['std_dev_period']) + 10:
            return None
        
        # Mean Reversion indikátorok számítása
        data = self.calculate_mean_reversion_indicators(data)
        
        # Aktuális ár és indikátor értékek
        current_price = data['close'].iloc[-1]
        current_z_score = data['z_score'].iloc[-1]
        current_rsi = data['rsi'].iloc[-1]
        current_cci = data['cci'].iloc[-1]
        current_williams_r = data['williams_r'].iloc[-1]
        
        # Előző értékek
        prev_z_score = data['z_score'].iloc[-2]
        prev_rsi = data['rsi'].iloc[-2]
        
        # Vételi feltételek (túladott állapot)
        buy_signal = (
            # Z-score túl alacsony (ár jelentősen az átlag alatt)
            current_z_score < -self.config['entry_std_dev'] and
            # RSI túladott zónában
            current_rsi < self.config['rsi_oversold'] and
            # CCI túladott zónában
            current_cci < -100 and
            # Williams %R túladott zónában
            current_williams_r < -80
        )
        
        # Eladási feltételek (túlvett állapot)
        sell_signal = (
            # Z-score túl magas (ár jelentősen az átlag felett)
            current_z_score > self.config['entry_std_dev'] and
            # RSI túlvett zónában
            current_rsi > self.config['rsi_overbought'] and
            # CCI túlvett zónában
            current_cci > 100 and
            # Williams %R túlvett zónában
            current_williams_r > -20
        )
        
        # Kilépési feltételek (átlaghoz való visszatérés)
        exit_long_signal = (
            # Z-score visszatért az átlaghoz
            abs(current_z_score) < self.config['exit_std_dev'] or
            # RSI kilépett a túladott zónából
            (prev_rsi < self.config['rsi_oversold'] and current_rsi > self.config['rsi_oversold'])
        )
        
        exit_short_signal = (
            # Z-score visszatért az átlaghoz
            abs(current_z_score) < self.config['exit_std_dev'] or
            # RSI kilépett a túlvett zónából
            (prev_rsi > self.config['rsi_overbought'] and current_rsi < self.config['rsi_overbought'])
        )
        
        # Nyitott pozíciók kezelése
        for position_id, position in list(self.open_positions.items()):
            # Long pozíció kilépési feltételek
            if position['side'] == 'long' and exit_long_signal:
                # Pozíció zárása
                signal = {
                    'action': 'sell',
                    'price': current_price,
                    'volume': position['volume'],
                    'type': 'market',
                    'params': {
                        'position_id': position_id,
                        'reason': 'mean_reversion_exit',
                        'profit_pct': (current_price / position['entry_price'] - 1) * 100
                    }
                }
                
                # Pozíció törlése
                del self.open_positions[position_id]
                
                return signal
            
            # Short pozíció kilépési feltételek
            elif position['side'] == 'short' and exit_short_signal:
                # Pozíció zárása
                signal = {
                    'action': 'buy',
                    'price': current_price,
                    'volume': position['volume'],
                    'type': 'market',
                    'params': {
                        'position_id': position_id,
                        'reason': 'mean_reversion_exit',
                        'profit_pct': (position['entry_price'] / current_price - 1) * 100
                    }
                }
                
                # Pozíció törlése
                del self.open_positions[position_id]
                
                return signal
            
            # Stop loss ellenőrzése
            if position['side'] == 'long':
                stop_loss_price = position['entry_price'] * (1 - self.config['stop_loss_pct'] / 100)
                if current_price <= stop_loss_price:
                    # Pozíció zárása stop loss miatt
                    signal = {
                        'action': 'sell',
                        'price': current_price,
                        'volume': position['volume'],
                        'type': 'market',
                        'params': {
                            'position_id': position_id,
                            'reason': 'stop_loss',
                            'profit_pct': (current_price / position['entry_price'] - 1) * 100
                        }
                    }
                    
                    # Pozíció törlése
                    del self.open_positions[position_id]
                    
                    return signal
            
            elif position['side'] == 'short':
                stop_loss_price = position['entry_price'] * (1 + self.config['stop_loss_pct'] / 100)
                if current_price >= stop_loss_price:
                    # Pozíció zárása stop loss miatt
                    signal = {
                        'action': 'buy',
                        'price': current_price,
                        'volume': position['volume'],
                        'type': 'market',
                        'params': {
                            'position_id': position_id,
                            'reason': 'stop_loss',
                            'profit_pct': (position['entry_price'] / current_price - 1) * 100
                        }
                    }
                    
                    # Pozíció törlése
                    del self.open_positions[position_id]
                    
                    return signal
            
            # Take profit ellenőrzése
            if position['side'] == 'long':
                take_profit_price = position['entry_price'] * (1 + self.config['take_profit_pct'] / 100)
                if current_price >= take_profit_price:
                    # Pozíció zárása take profit miatt
                    signal = {
                        'action': 'sell',
                        'price': current_price,
                        'volume': position['volume'],
                        'type': 'market',
                        'params': {
                            'position_id': position_id,
                            'reason': 'take_profit',
                            'profit_pct': (current_price / position['entry_price'] - 1) * 100
                        }
                    }
                    
                    # Pozíció törlése
                    del self.open_positions[position_id]
                    
                    return signal
            
            elif position['side'] == 'short':
                take_profit_price = position['entry_price'] * (1 - self.config['take_profit_pct'] / 100)
                if current_price <= take_profit_price:
                    # Pozíció zárása take profit miatt
                    signal = {
                        'action': 'buy',
                        'price': current_price,
                        'volume': position['volume'],
                        'type': 'market',
                        'params': {
                            'position_id': position_id,
                            'reason': 'take_profit',
                            'profit_pct': (position['entry_price'] / current_price - 1) * 100
                        }
                    }
                    
                    # Pozíció törlése
                    del self.open_positions[position_id]
                    
                    return signal
        
        # Új pozíció nyitása, ha nincs elég nyitott pozíció
        if len(self.open_positions) < self.config['max_positions']:
            # Vételi jel
            if buy_signal:
                # Pozíció méret kiszámítása
                position_size = self.calculate_position_size(current_price)
                position_id = f"{self.name}_{self.symbol}_{len(self.open_positions) + 1}"
                
                # Vételi jel
                signal = {
                    'action': 'buy',
                    'price': current_price,
                    'volume': position_size,
                    'type': 'market',
                    'params': {
                        'position_id': position_id,
                        'reason': 'mean_reversion_entry',
                        'z_score': current_z_score,
                        'rsi': current_rsi
                    }
                }
                
                # Pozíció hozzáadása
                self.open_positions[position_id] = {
                    'entry_price': current_price,
                    'volume': position_size,
                    'side': 'long'
                }
                
                return signal
            
            # Eladási jel
            elif sell_signal:
                # Pozíció méret kiszámítása
                position_size = self.calculate_position_size(current_price)
                position_id = f"{self.name}_{self.symbol}_{len(self.open_positions) + 1}"
                
                # Eladási jel
                signal = {
                    'action': 'sell',
                    'price': current_price,
                    'volume': position_size,
                    'type': 'market',
                    'params': {
                        'position_id': position_id,
                        'reason': 'mean_reversion_entry',
                        'z_score': current_z_score,
                        'rsi': current_rsi
                    }
                }
                
                # Pozíció hozzáadása
                self.open_positions[position_id] = {
                    'entry_price': current_price,
                    'volume': position_size,
                    'side': 'short'
                }
                
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
    
    def get_open_positions(self):
        """
        Nyitott pozíciók lekérdezése
        
        Returns:
            dict: Nyitott pozíciók
        """
        return self.open_positions
    
    def reset_positions(self):
        """
        Pozíciók visszaállítása
        """
        self.open_positions = {}
