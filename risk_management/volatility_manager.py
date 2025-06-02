"""
Volatility Manager - Kezeli a piaci volatilitást a kereskedési rendszerben.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('volatility_manager')

class VolatilityManager:
    """
    Kezeli a piaci volatilitást a kereskedési rendszerben, beleértve a
    volatilitás alapú pozíció méretezést, volatilitás szűrést és
    volatilitás alapú stop loss beállítást.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a VolatilityManager-t a megadott konfigurációval.
        
        Args:
            config: A VolatilityManager konfigurációja
        """
        self.config = config
        
        # Konfigurációs beállítások
        self.volatility_window = config.get('volatility_window', 20)  # Volatilitás számítási ablak
        self.volatility_multiplier = config.get('volatility_multiplier', 2.0)  # Volatilitás szorzó a stop loss-hoz
        self.max_volatility_threshold = config.get('max_volatility_threshold', 0.05)  # 5% maximális volatilitás
        self.min_volatility_threshold = config.get('min_volatility_threshold', 0.005)  # 0.5% minimális volatilitás
        self.volatility_adjustment_factor = config.get('volatility_adjustment_factor', 0.5)  # Volatilitás módosító faktor
        
        # Volatilitás adatok tárolása
        self.volatility_data = {}
        self.last_update_time = None
        
        # RPI4 optimalizáció
        self.max_lookback = config.get('max_lookback', 100)  # Korlátozott visszatekintés
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        
        logger.info("VolatilityManager initialized")
    
    def update_volatility(self, symbol: str, ohlcv_data: List[List]) -> Dict:
        """
        Frissíti a volatilitás adatokat az OHLCV adatok alapján.
        
        Args:
            symbol: A kereskedési szimbólum
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            Dict: A volatilitás adatok
        """
        try:
            if not ohlcv_data:
                logger.warning(f"Empty OHLCV data for {symbol}")
                return {'volatility': 0.0, 'error': 'Empty OHLCV data'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(ohlcv_data), self.max_lookback)
            ohlcv_data = ohlcv_data[-lookback:]
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Egyszerű volatilitás számítás: záróárak szórása
                closes = [candle[4] for candle in ohlcv_data[-self.volatility_window:]]
                returns = [np.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
                volatility = np.std(returns)
                
                # Napi volatilitás -> éves volatilitás
                annualized_volatility = volatility * np.sqrt(252)
                
                # Volatilitás trend
                if len(ohlcv_data) >= self.volatility_window * 2:
                    prev_closes = [candle[4] for candle in ohlcv_data[-self.volatility_window*2:-self.volatility_window]]
                    prev_returns = [np.log(prev_closes[i] / prev_closes[i-1]) for i in range(1, len(prev_closes))]
                    prev_volatility = np.std(prev_returns)
                    volatility_trend = (volatility - prev_volatility) / prev_volatility if prev_volatility > 0 else 0.0
                else:
                    volatility_trend = 0.0
            
            else:
                # Fejlettebb volatilitás számítás: GARCH vagy más módszerek
                # Itt most csak egy egyszerű példa implementáció
                
                # Záróárak
                closes = [candle[4] for candle in ohlcv_data]
                
                # Napi hozamok
                returns = [np.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
                
                # Exponenciálisan súlyozott mozgóátlag (EWMA) volatilitás
                alpha = 0.94  # Decay faktor
                ewma_volatility = 0.0
                
                for i, ret in enumerate(returns[-self.volatility_window:]):
                    if i == 0:
                        ewma_volatility = ret ** 2
                    else:
                        ewma_volatility = alpha * ewma_volatility + (1 - alpha) * (ret ** 2)
                
                volatility = np.sqrt(ewma_volatility)
                
                # Napi volatilitás -> éves volatilitás
                annualized_volatility = volatility * np.sqrt(252)
                
                # Volatilitás trend
                if len(returns) >= self.volatility_window * 2:
                    prev_ewma_volatility = 0.0
                    for i, ret in enumerate(returns[-self.volatility_window*2:-self.volatility_window]):
                        if i == 0:
                            prev_ewma_volatility = ret ** 2
                        else:
                            prev_ewma_volatility = alpha * prev_ewma_volatility + (1 - alpha) * (ret ** 2)
                    
                    prev_volatility = np.sqrt(prev_ewma_volatility)
                    volatility_trend = (volatility - prev_volatility) / prev_volatility if prev_volatility > 0 else 0.0
                else:
                    volatility_trend = 0.0
            
            # Volatilitás adatok frissítése
            self.volatility_data[symbol] = {
                'volatility': volatility,
                'annualized_volatility': annualized_volatility,
                'volatility_trend': volatility_trend,
                'timestamp': datetime.now()
            }
            
            self.last_update_time = datetime.now()
            
            return self.volatility_data[symbol]
        
        except Exception as e:
            logger.error(f"Error updating volatility for {symbol}: {str(e)}")
            return {'volatility': 0.0, 'error': str(e)}
    
    def get_volatility(self, symbol: str) -> Optional[Dict]:
        """
        Visszaadja a volatilitás adatokat egy adott szimbólumra.
        
        Args:
            symbol: A kereskedési szimbólum
            
        Returns:
            Optional[Dict]: A volatilitás adatok, vagy None ha a szimbólum nem található
        """
        try:
            if symbol in self.volatility_data:
                return self.volatility_data[symbol]
            
            logger.warning(f"No volatility data for {symbol}")
            return None
        
        except Exception as e:
            logger.error(f"Error getting volatility for {symbol}: {str(e)}")
            return None
    
    def get_all_volatilities(self) -> Dict:
        """
        Visszaadja az összes volatilitás adatot.
        
        Returns:
            Dict: Az összes volatilitás adat
        """
        return self.volatility_data
    
    def calculate_volatility_adjusted_position_size(self, symbol: str, base_position_size: float) -> float:
        """
        Kiszámítja a volatilitás alapján módosított pozíció méretet.
        
        Args:
            symbol: A kereskedési szimbólum
            base_position_size: Az alap pozíció méret
            
        Returns:
            float: A módosított pozíció méret
        """
        try:
            # Ha a pozíció méret 0 vagy negatív, akkor nem módosít
            if base_position_size <= 0:
                return 0.0
            
            # Volatilitás adatok
            volatility_data = self.get_volatility(symbol)
            
            if not volatility_data or 'volatility' not in volatility_data:
                logger.warning(f"No volatility data for {symbol}, using base position size")
                return base_position_size
            
            # Volatilitás
            volatility = volatility_data['volatility']
            
            # Volatilitás alapú módosítás
            # Magasabb volatilitás = kisebb pozíció
            if volatility <= self.min_volatility_threshold:
                # Alacsony volatilitás: nagyobb pozíció
                adjustment_factor = 1.0 + self.volatility_adjustment_factor
            elif volatility >= self.max_volatility_threshold:
                # Magas volatilitás: kisebb pozíció
                adjustment_factor = 1.0 - self.volatility_adjustment_factor
            else:
                # Közepes volatilitás: lineáris interpoláció
                normalized_volatility = (volatility - self.min_volatility_threshold) / (self.max_volatility_threshold - self.min_volatility_threshold)
                adjustment_factor = 1.0 + self.volatility_adjustment_factor * (0.5 - normalized_volatility)
            
            # Módosított pozíció méret
            adjusted_position_size = base_position_size * adjustment_factor
            
            logger.debug(f"Position size adjusted for volatility: {base_position_size} -> {adjusted_position_size} (factor: {adjustment_factor})")
            
            return adjusted_position_size
        
        except Exception as e:
            logger.error(f"Error calculating volatility adjusted position size for {symbol}: {str(e)}")
            return base_position_size
    
    def calculate_volatility_based_stop_loss(self, symbol: str, entry_price: float, direction: str) -> Optional[float]:
        """
        Kiszámítja a volatilitás alapú stop loss árat.
        
        Args:
            symbol: A kereskedési szimbólum
            entry_price: A belépési ár
            direction: A kereskedés iránya ('buy' vagy 'sell')
            
        Returns:
            Optional[float]: A stop loss ár, vagy None hiba esetén
        """
        try:
            if entry_price <= 0:
                logger.warning(f"Invalid entry price: {entry_price}")
                return None
            
            if direction not in ['buy', 'sell']:
                logger.warning(f"Invalid direction: {direction}")
                return None
            
            # Volatilitás adatok
            volatility_data = self.get_volatility(symbol)
            
            if not volatility_data or 'volatility' not in volatility_data:
                logger.warning(f"No volatility data for {symbol}, cannot calculate stop loss")
                return None
            
            # Volatilitás
            volatility = volatility_data['volatility']
            
            # Stop loss távolság (volatilitás * szorzó)
            stop_distance = volatility * self.volatility_multiplier
            
            # Stop loss ár
            if direction == 'buy':
                stop_loss = entry_price * (1 - stop_distance)
            else:  # sell
                stop_loss = entry_price * (1 + stop_distance)
            
            logger.debug(f"Volatility based stop loss for {symbol}: {stop_loss} (distance: {stop_distance:.2%})")
            
            return stop_loss
        
        except Exception as e:
            logger.error(f"Error calculating volatility based stop loss for {symbol}: {str(e)}")
            return None
    
    def is_volatility_suitable_for_trading(self, symbol: str) -> Tuple[bool, str]:
        """
        Ellenőrzi, hogy a volatilitás megfelelő-e a kereskedéshez.
        
        Args:
            symbol: A kereskedési szimbólum
            
        Returns:
            Tuple[bool, str]: (Megfelelő-e, Indoklás)
        """
        try:
            # Volatilitás adatok
            volatility_data = self.get_volatility(symbol)
            
            if not volatility_data or 'volatility' not in volatility_data:
                return (False, "No volatility data available")
            
            # Volatilitás
            volatility = volatility_data['volatility']
            volatility_trend = volatility_data.get('volatility_trend', 0.0)
            
            # Túl alacsony volatilitás
            if volatility < self.min_volatility_threshold:
                return (False, f"Volatility too low: {volatility:.2%} < {self.min_volatility_threshold:.2%}")
            
            # Túl magas volatilitás
            if volatility > self.max_volatility_threshold:
                return (False, f"Volatility too high: {volatility:.2%} > {self.max_volatility_threshold:.2%}")
            
            # Volatilitás trend
            if volatility_trend > 0.5:
                return (False, f"Volatility increasing too rapidly: {volatility_trend:.2%}")
            
            return (True, f"Volatility suitable for trading: {volatility:.2%}")
        
        except Exception as e:
            logger.error(f"Error checking volatility suitability for {symbol}: {str(e)}")
            return (False, f"Error: {str(e)}")
    
    def calculate_volatility_breakout_levels(self, symbol: str, base_price: float) -> Dict:
        """
        Kiszámítja a volatilitás alapú kitörési szinteket.
        
        Args:
            symbol: A kereskedési szimbólum
            base_price: Az alap ár
            
        Returns:
            Dict: A kitörési szintek
        """
        try:
            if base_price <= 0:
                logger.warning(f"Invalid base price: {base_price}")
                return {'error': 'Invalid base price'}
            
            # Volatilitás adatok
            volatility_data = self.get_volatility(symbol)
            
            if not volatility_data or 'volatility' not in volatility_data:
                logger.warning(f"No volatility data for {symbol}, cannot calculate breakout levels")
                return {'error': 'No volatility data'}
            
            # Volatilitás
            volatility = volatility_data['volatility']
            
            # Kitörési szintek
            breakout_levels = {
                'upper_1': base_price * (1 + volatility),
                'upper_2': base_price * (1 + volatility * 2),
                'upper_3': base_price * (1 + volatility * 3),
                'lower_1': base_price * (1 - volatility),
                'lower_2': base_price * (1 - volatility * 2),
                'lower_3': base_price * (1 - volatility * 3),
                'volatility': volatility,
                'base_price': base_price,
                'timestamp': datetime.now()
            }
            
            return breakout_levels
        
        except Exception as e:
            logger.error(f"Error calculating volatility breakout levels for {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def calculate_volatility_bands(self, symbol: str, ohlcv_data: List[List]) -> Dict:
        """
        Kiszámítja a volatilitás sávokat (hasonló a Bollinger sávokhoz).
        
        Args:
            symbol: A kereskedési szimbólum
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            Dict: A volatilitás sávok
        """
        try:
            if not ohlcv_data:
                logger.warning(f"Empty OHLCV data for {symbol}")
                return {'error': 'Empty OHLCV data'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(ohlcv_data), self.max_lookback)
            ohlcv_data = ohlcv_data[-lookback:]
            
            # Záróárak
            closes = [candle[4] for candle in ohlcv_data[-self.volatility_window:]]
            
            # Középső sáv (egyszerű mozgóátlag)
            middle_band = np.mean(closes)
            
            # Volatilitás (szórás)
            std = np.std(closes)
            
            # Felső és alsó sávok
            upper_band_1 = middle_band + std
            upper_band_2 = middle_band + std * 2
            lower_band_1 = middle_band - std
            lower_band_2 = middle_band - std * 2
            
            # Relatív volatilitás (szórás / átlag)
            relative_volatility = std / middle_band if middle_band > 0 else 0.0
            
            # Sáv szélesség
            band_width = (upper_band_2 - lower_band_2) / middle_band if middle_band > 0 else 0.0
            
            # Aktuális ár pozíciója a sávokban
            current_price = closes[-1]
            price_position = (current_price - lower_band_2) / (upper_band_2 - lower_band_2) if (upper_band_2 - lower_band_2) > 0 else 0.5
            
            return {
                'middle_band': middle_band,
                'upper_band_1': upper_band_1,
                'upper_band_2': upper_band_2,
                'lower_band_1': lower_band_1,
                'lower_band_2': lower_band_2,
                'relative_volatility': relative_volatility,
                'band_width': band_width,
                'price_position': price_position,
                'current_price': current_price,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating volatility bands for {symbol}: {str(e)}")
            return {'error': str(e)}
