"""
Market Regime Detector - Azonosítja a különböző piaci rezsimeket és környezeteket.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.utils.logger import setup_logger

logger = setup_logger('market_regime_detector')

class MarketRegimeDetector:
    """
    Azonosítja a különböző piaci rezsimeket és környezeteket, mint például
    trend, oldalazás, magas volatilitás, alacsony volatilitás, stb.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a MarketRegimeDetector-t a megadott konfigurációval.
        
        Args:
            config: A MarketRegimeDetector konfigurációja
        """
        self.config = config
        self.scaler = StandardScaler()
        self.model = None
        self.is_trained = False
        self.last_training_time = None
        
        # Konfigurációs beállítások
        self.lookback_window = config.get('lookback_window', 30)  # Visszatekintési időablak
        self.min_training_samples = config.get('min_training_samples', 100)  # Minimum minták száma a tanításhoz
        self.retraining_interval = config.get('retraining_interval', 24 * 60 * 60)  # Újratanítási intervallum másodpercben
        self.num_regimes = config.get('num_regimes', 4)  # Rezsimek száma
        
        # Rezsim típusok
        self.regime_types = {
            0: 'trending_up',
            1: 'trending_down',
            2: 'ranging_low_volatility',
            3: 'ranging_high_volatility'
        }
        
        # RPI4 optimalizáció
        self.max_lookback = config.get('max_lookback', 200)  # Korlátozott visszatekintés
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        
        logger.info("MarketRegimeDetector initialized")
    
    def _prepare_features(self, ohlcv_data: List[List]) -> np.ndarray:
        """
        Előkészíti a feature-öket a rezsim detektáláshoz.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            np.ndarray: Feature-ök
        """
        try:
            # Korlátozza a visszatekintést
            lookback = min(len(ohlcv_data), self.max_lookback)
            
            if lookback < self.lookback_window:
                logger.warning(f"Not enough data for feature preparation: {lookback} < {self.lookback_window}")
                return np.array([])
            
            # Konvertálja az OHLCV adatokat DataFrame-mé
            df = pd.DataFrame(ohlcv_data[-lookback:], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Egyszerű feature-ök
                features = []
                
                # Utolsó N gyertya
                window_data = df.tail(self.lookback_window)
                
                # 1. Trend indikátor: záróárak lineáris regressziójának meredeksége
                closes = window_data['close'].values
                x = np.arange(len(closes))
                slope, _ = np.polyfit(x, closes, 1)
                normalized_slope = slope * len(closes) / closes[0]
                
                # 2. Volatilitás: záróárak relatív szórása
                volatility = np.std(closes) / np.mean(closes)
                
                # 3. Volumen trend: volumenek lineáris regressziójának meredeksége
                volumes = window_data['volume'].values
                volume_slope, _ = np.polyfit(x, volumes, 1)
                normalized_volume_slope = volume_slope * len(volumes) / (np.mean(volumes) if np.mean(volumes) > 0 else 1)
                
                # 4. Ártartomány: (max-min)/átlag
                price_range = (np.max(closes) - np.min(closes)) / np.mean(closes)
                
                # 5. Momentum: utolsó ár / első ár - 1
                momentum = closes[-1] / closes[0] - 1
                
                features = [normalized_slope, volatility, normalized_volume_slope, price_range, momentum]
                
                return np.array([features])
            
            else:
                # Fejlettebb feature-ök
                features = []
                
                for i in range(lookback - self.lookback_window):
                    window_data = df.iloc[i:i+self.lookback_window]
                    
                    # 1. Trend indikátorok
                    closes = window_data['close'].values
                    x = np.arange(len(closes))
                    slope, _ = np.polyfit(x, closes, 1)
                    normalized_slope = slope * len(closes) / closes[0]
                    
                    # 2. Volatilitás indikátorok
                    returns = np.diff(np.log(closes))
                    volatility = np.std(returns)
                    
                    # 3. Volumen indikátorok
                    volumes = window_data['volume'].values
                    volume_mean = np.mean(volumes)
                    volume_std = np.std(volumes) / volume_mean if volume_mean > 0 else 0
                    
                    # 4. Ártartomány indikátorok
                    highs = window_data['high'].values
                    lows = window_data['low'].values
                    price_range = np.mean((highs - lows) / lows)
                    
                    # 5. Momentum indikátorok
                    momentum_1d = closes[-1] / closes[-2] - 1 if len(closes) >= 2 else 0
                    momentum_5d = closes[-1] / closes[-6] - 1 if len(closes) >= 6 else 0
                    
                    # 6. Trend erősség indikátorok
                    adx = self._calculate_adx(window_data)
                    
                    feature_vector = [
                        normalized_slope,
                        volatility,
                        volume_std,
                        price_range,
                        momentum_1d,
                        momentum_5d,
                        adx
                    ]
                    
                    features.append(feature_vector)
                
                return np.array(features)
        
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            return np.array([])
    
    def _calculate_adx(self, df: pd.DataFrame) -> float:
        """
        Kiszámítja az Average Directional Index (ADX) értékét.
        
        Args:
            df: OHLCV adatok DataFrame-ben
            
        Returns:
            float: Az ADX érték
        """
        try:
            # Egyszerűsített ADX számítás
            if len(df) < 14:
                return 0.0
            
            # +DI és -DI számítása
            highs = df['high'].values
            lows = df['low'].values
            closes = df['close'].values
            
            # True Range
            tr = np.zeros(len(df))
            for i in range(1, len(df)):
                hl = highs[i] - lows[i]
                hc = abs(highs[i] - closes[i-1])
                lc = abs(lows[i] - closes[i-1])
                tr[i] = max(hl, hc, lc)
            
            # Átlagos True Range (ATR)
            atr = np.mean(tr[1:14])
            
            # +DM és -DM
            plus_dm = np.zeros(len(df))
            minus_dm = np.zeros(len(df))
            
            for i in range(1, len(df)):
                up_move = highs[i] - highs[i-1]
                down_move = lows[i-1] - lows[i]
                
                if up_move > down_move and up_move > 0:
                    plus_dm[i] = up_move
                elif down_move > up_move and down_move > 0:
                    minus_dm[i] = down_move
            
            # +DI és -DI
            plus_di = 100 * np.mean(plus_dm[1:14]) / atr if atr > 0 else 0
            minus_di = 100 * np.mean(minus_dm[1:14]) / atr if atr > 0 else 0
            
            # DX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0
            
            # ADX (egyszerűsített, csak az utolsó DX értéket használjuk)
            adx = dx
            
            return adx
        
        except Exception as e:
            logger.error(f"Error calculating ADX: {str(e)}")
            return 0.0
    
    def train(self, ohlcv_data: List[List]) -> bool:
        """
        Betanítja a modellt az OHLCV adatokon.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            bool: Sikeres tanítás esetén True, egyébként False
        """
        try:
            if len(ohlcv_data) < self.min_training_samples:
                logger.warning(f"Not enough training samples: {len(ohlcv_data)} < {self.min_training_samples}")
                return False
            
            logger.info(f"Training market regime detector on {len(ohlcv_data)} samples")
            
            # Előkészíti a feature-öket
            X = self._prepare_features(ohlcv_data)
            
            if len(X) == 0:
                logger.warning("No features generated")
                return False
            
            # Normalizálja a feature-öket
            X_scaled = self.scaler.fit_transform(X)
            
            # Létrehozza és betanítja a modellt
            self.model = KMeans(
                n_clusters=self.num_regimes,
                random_state=42,
                n_init=10
            )
            
            self.model.fit(X_scaled)
            
            # Címkézi a rezsimeket
            self._label_regimes()
            
            self.is_trained = True
            self.last_training_time = datetime.now()
            
            logger.info("Market regime detector trained successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def _label_regimes(self) -> None:
        """
        Címkézi a rezsimeket a klaszter centroidok alapján.
        """
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model is not trained yet")
                return
            
            # Klaszter centroidok
            centroids = self.model.cluster_centers_
            
            # Egyszerűsített címkézés
            if self.simplify_calculations:
                # Feltételezzük, hogy 4 rezsim van
                if self.num_regimes == 4:
                    # Trend indikátor (első feature) alapján címkézés
                    trend_values = centroids[:, 0]
                    volatility_values = centroids[:, 1]
                    
                    # Rendezi a klasztereket trend szerint
                    sorted_indices = np.argsort(trend_values)
                    
                    # Címkézi a rezsimeket
                    regime_map = {}
                    
                    # Legalacsonyabb trend érték: lefelé trend
                    regime_map[sorted_indices[0]] = 'trending_down'
                    
                    # Legmagasabb trend érték: felfelé trend
                    regime_map[sorted_indices[-1]] = 'trending_up'
                    
                    # Középső értékek: oldalazás (alacsony/magas volatilitás)
                    middle_indices = sorted_indices[1:-1]
                    if len(middle_indices) >= 2:
                        # Volatilitás alapján rendezi
                        middle_volatilities = volatility_values[middle_indices]
                        sorted_middle = np.argsort(middle_volatilities)
                        
                        regime_map[middle_indices[sorted_middle[0]]] = 'ranging_low_volatility'
                        regime_map[middle_indices[sorted_middle[-1]]] = 'ranging_high_volatility'
                    
                    # Frissíti a rezsim típusokat
                    self.regime_types = {i: regime_map.get(i, f'regime_{i}') for i in range(self.num_regimes)}
                else:
                    # Alapértelmezett címkézés
                    self.regime_types = {i: f'regime_{i}' for i in range(self.num_regimes)}
            
            else:
                # Fejlettebb címkézés
                # TODO: Implementálni a fejlettebb címkézést
                pass
        
        except Exception as e:
            logger.error(f"Error labeling regimes: {str(e)}")
    
    def detect(self, ohlcv_data: List[List]) -> Optional[Dict]:
        """
        Detektálja a piaci rezsimet az OHLCV adatok alapján.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            Optional[Dict]: A detektált rezsim, vagy None hiba esetén
        """
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model is not trained yet")
                return None
            
            # Ellenőrzi, hogy van-e elég adat
            if len(ohlcv_data) < self.lookback_window:
                logger.warning(f"Not enough data for regime detection: {len(ohlcv_data)} < {self.lookback_window}")
                return None
            
            # Előkészíti a feature-öket
            X = self._prepare_features(ohlcv_data)
            
            if len(X) == 0:
                logger.warning("No features generated")
                return None
            
            # Csak az utolsó ablakot használja
            X_last = X[-1].reshape(1, -1)
            
            # Normalizálja a feature-öket
            X_scaled = self.scaler.transform(X_last)
            
            # Előrejelzi a rezsimet
            regime_id = self.model.predict(X_scaled)[0]
            regime_type = self.regime_types.get(regime_id, f'regime_{regime_id}')
            
            # Kiszámítja a távolságot a centroidtól (bizonytalanság mérték)
            distance = np.linalg.norm(X_scaled - self.model.cluster_centers_[regime_id])
            confidence = 1.0 / (1.0 + distance)  # Távolság inverze, normalizálva
            
            logger.debug(f"Detected regime: {regime_type} (ID: {regime_id}, confidence: {confidence:.2f})")
            
            return {
                'regime_id': int(regime_id),
                'regime_type': regime_type,
                'confidence': float(confidence),
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error detecting regime: {str(e)}")
            return None
    
    def needs_retraining(self) -> bool:
        """
        Ellenőrzi, hogy a modellnek szüksége van-e újratanításra.
        
        Returns:
            bool: True, ha a modellnek újratanításra van szüksége, egyébként False
        """
        if not self.is_trained or self.last_training_time is None:
            return True
        
        elapsed_seconds = (datetime.now() - self.last_training_time).total_seconds()
        return elapsed_seconds >= self.retraining_interval
    
    def get_regime_characteristics(self, regime_id: int) -> Optional[Dict]:
        """
        Visszaadja egy adott rezsim jellemzőit.
        
        Args:
            regime_id: A rezsim azonosítója
            
        Returns:
            Optional[Dict]: A rezsim jellemzői, vagy None ha a rezsim nem található
        """
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model is not trained yet")
                return None
            
            if regime_id < 0 or regime_id >= self.num_regimes:
                logger.warning(f"Invalid regime ID: {regime_id}")
                return None
            
            # Rezsim centroid
            centroid = self.model.cluster_centers_[regime_id]
            
            # Rezsim jellemzők
            characteristics = {
                'regime_id': regime_id,
                'regime_type': self.regime_types.get(regime_id, f'regime_{regime_id}'),
                'trend': float(centroid[0]),
                'volatility': float(centroid[1]),
                'volume_trend': float(centroid[2]) if len(centroid) > 2 else 0.0,
                'price_range': float(centroid[3]) if len(centroid) > 3 else 0.0,
                'momentum': float(centroid[4]) if len(centroid) > 4 else 0.0
            }
            
            return characteristics
        
        except Exception as e:
            logger.error(f"Error getting regime characteristics: {str(e)}")
            return None
    
    def get_all_regimes(self) -> List[Dict]:
        """
        Visszaadja az összes rezsim jellemzőit.
        
        Returns:
            List[Dict]: Az összes rezsim jellemzői
        """
        regimes = []
        
        for i in range(self.num_regimes):
            regime = self.get_regime_characteristics(i)
            if regime:
                regimes.append(regime)
        
        return regimes
    
    def get_optimal_strategies(self, regime_id: int) -> List[str]:
        """
        Visszaadja az optimális stratégiákat egy adott rezsimhez.
        
        Args:
            regime_id: A rezsim azonosítója
            
        Returns:
            List[str]: Az optimális stratégiák listája
        """
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model is not trained yet")
                return []
            
            if regime_id < 0 or regime_id >= self.num_regimes:
                logger.warning(f"Invalid regime ID: {regime_id}")
                return []
            
            regime_type = self.regime_types.get(regime_id, f'regime_{regime_id}')
            
            # Optimális stratégiák rezsimenként
            strategy_map = {
                'trending_up': ['momentum', 'trend_following', 'breakout'],
                'trending_down': ['momentum', 'trend_following', 'breakout'],
                'ranging_low_volatility': ['mean_reversion', 'grid_trading', 'statistical_arbitrage'],
                'ranging_high_volatility': ['volatility_breakout', 'options_strategies', 'pairs_trading']
            }
            
            return strategy_map.get(regime_type, [])
        
        except Exception as e:
            logger.error(f"Error getting optimal strategies: {str(e)}")
            return []
