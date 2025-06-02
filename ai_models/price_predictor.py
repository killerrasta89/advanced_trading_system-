"""
Price Predictor - Gépi tanulási modell az árfolyam előrejelzésére.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from src.utils.logger import setup_logger

logger = setup_logger('price_predictor')

class PricePredictor:
    """
    Gépi tanulási modell az árfolyam előrejelzésére.
    Random Forest algoritmust használ a jövőbeli árak becslésére.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a PricePredictor-t a megadott konfigurációval.
        
        Args:
            config: A PricePredictor konfigurációja
        """
        self.config = config
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.last_training_time = None
        
        # Konfigurációs beállítások
        self.prediction_horizon = config.get('prediction_horizon', 12)  # Hány időegységre előre jósoljon
        self.feature_window = config.get('feature_window', 24)  # Hány időegységet használjon a feature-ökhöz
        self.min_training_samples = config.get('min_training_samples', 1000)  # Minimum minták száma a tanításhoz
        self.retraining_interval = config.get('retraining_interval', 24 * 60 * 60)  # Újratanítási intervallum másodpercben
        
        # RPI4 optimalizáció
        self.n_estimators = config.get('n_estimators', 50)  # Kevesebb fa a Random Forest-ben
        self.max_depth = config.get('max_depth', 10)  # Korlátozott fa mélység
        self.n_jobs = config.get('n_jobs', 2)  # Párhuzamos feldolgozás korlátozása
        
        logger.info("PricePredictor initialized")
    
    def _prepare_features(self, ohlcv_data: List[List]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Előkészíti a feature-öket és a célváltozókat a tanításhoz.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Feature-ök és célváltozók
        """
        try:
            # Konvertálja az OHLCV adatokat DataFrame-mé
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Technikai indikátorok számítása
            # 1. Mozgóátlagok
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_10'] = df['close'].rolling(window=10).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            
            # 2. Relatív erősség index (RSI)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 3. MACD
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # 4. Bollinger sávok
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
            df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
            
            # 5. Árváltozás százalékban
            df['price_change'] = df['close'].pct_change()
            
            # 6. Volatilitás
            df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
            
            # Eltávolítja a NaN értékeket
            df = df.dropna()
            
            # Létrehozza a feature-öket és a célváltozókat
            features = []
            targets = []
            
            for i in range(len(df) - self.feature_window - self.prediction_horizon):
                # Feature ablak
                feature_window_data = df.iloc[i:i+self.feature_window]
                
                # Feature-ök létrehozása
                feature_vector = []
                
                # Záróárak az ablakban
                feature_vector.extend(feature_window_data['close'].values)
                
                # Technikai indikátorok
                feature_vector.extend(feature_window_data['sma_5'].values[-5:])
                feature_vector.extend(feature_window_data['sma_10'].values[-5:])
                feature_vector.extend(feature_window_data['sma_20'].values[-5:])
                feature_vector.extend(feature_window_data['rsi'].values[-5:])
                feature_vector.extend(feature_window_data['macd'].values[-5:])
                feature_vector.extend(feature_window_data['macd_signal'].values[-5:])
                feature_vector.extend(feature_window_data['bb_upper'].values[-5:])
                feature_vector.extend(feature_window_data['bb_lower'].values[-5:])
                feature_vector.extend(feature_window_data['price_change'].values[-5:])
                feature_vector.extend(feature_window_data['volatility'].values[-5:])
                
                features.append(feature_vector)
                
                # Célváltozó: jövőbeli záróár
                target_idx = i + self.feature_window + self.prediction_horizon - 1
                targets.append(df.iloc[target_idx]['close'])
            
            return np.array(features), np.array(targets)
        
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            return np.array([]), np.array([])
    
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
            
            logger.info(f"Training price predictor on {len(ohlcv_data)} samples")
            
            # Előkészíti a feature-öket és a célváltozókat
            X, y = self._prepare_features(ohlcv_data)
            
            if len(X) == 0 or len(y) == 0:
                logger.warning("No features or targets generated")
                return False
            
            # Felosztja a tanító és teszt adatokat
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Normalizálja a feature-öket
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Létrehozza és betanítja a modellt
            self.model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                n_jobs=self.n_jobs,
                random_state=42
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Kiértékeli a modellt
            y_pred = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"Model trained successfully. MSE: {mse:.4f}, R²: {r2:.4f}")
            
            self.is_trained = True
            self.last_training_time = datetime.now()
            
            return True
        
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def predict(self, ohlcv_data: List[List]) -> Optional[float]:
        """
        Előrejelzi a jövőbeli árat az OHLCV adatok alapján.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            Optional[float]: Az előrejelzett ár, vagy None hiba esetén
        """
        try:
            if not self.is_trained or self.model is None:
                logger.warning("Model is not trained yet")
                return None
            
            # Ellenőrzi, hogy van-e elég adat
            if len(ohlcv_data) < self.feature_window:
                logger.warning(f"Not enough data for prediction: {len(ohlcv_data)} < {self.feature_window}")
                return None
            
            # Előkészíti a feature-öket
            df = pd.DataFrame(ohlcv_data[-self.feature_window-30:], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Technikai indikátorok számítása
            # 1. Mozgóátlagok
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_10'] = df['close'].rolling(window=10).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            
            # 2. Relatív erősség index (RSI)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # 3. MACD
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            
            # 4. Bollinger sávok
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
            df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
            
            # 5. Árváltozás százalékban
            df['price_change'] = df['close'].pct_change()
            
            # 6. Volatilitás
            df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
            
            # Eltávolítja a NaN értékeket
            df = df.dropna()
            
            # Ellenőrzi, hogy van-e elég adat a feature-ök létrehozásához
            if len(df) < self.feature_window:
                logger.warning(f"Not enough data after preprocessing: {len(df)} < {self.feature_window}")
                return None
            
            # Létrehozza a feature vektort
            feature_window_data = df.iloc[-self.feature_window:]
            
            feature_vector = []
            
            # Záróárak az ablakban
            feature_vector.extend(feature_window_data['close'].values)
            
            # Technikai indikátorok
            feature_vector.extend(feature_window_data['sma_5'].values[-5:])
            feature_vector.extend(feature_window_data['sma_10'].values[-5:])
            feature_vector.extend(feature_window_data['sma_20'].values[-5:])
            feature_vector.extend(feature_window_data['rsi'].values[-5:])
            feature_vector.extend(feature_window_data['macd'].values[-5:])
            feature_vector.extend(feature_window_data['macd_signal'].values[-5:])
            feature_vector.extend(feature_window_data['bb_upper'].values[-5:])
            feature_vector.extend(feature_window_data['bb_lower'].values[-5:])
            feature_vector.extend(feature_window_data['price_change'].values[-5:])
            feature_vector.extend(feature_window_data['volatility'].values[-5:])
            
            # Normalizálja a feature-öket
            feature_vector_scaled = self.scaler.transform(np.array([feature_vector]))
            
            # Előrejelzi az árat
            predicted_price = self.model.predict(feature_vector_scaled)[0]
            
            logger.debug(f"Predicted price: {predicted_price:.2f}")
            return predicted_price
        
        except Exception as e:
            logger.error(f"Error predicting price: {str(e)}")
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
    
    def get_feature_importance(self) -> Optional[Dict]:
        """
        Visszaadja a feature-ök fontosságát.
        
        Returns:
            Optional[Dict]: A feature-ök fontossága, vagy None ha a modell nincs betanítva
        """
        if not self.is_trained or self.model is None:
            logger.warning("Model is not trained yet")
            return None
        
        try:
            # Feature nevek
            feature_names = [f"close_{i}" for i in range(self.feature_window)]
            feature_names.extend([f"sma_5_{i}" for i in range(5)])
            feature_names.extend([f"sma_10_{i}" for i in range(5)])
            feature_names.extend([f"sma_20_{i}" for i in range(5)])
            feature_names.extend([f"rsi_{i}" for i in range(5)])
            feature_names.extend([f"macd_{i}" for i in range(5)])
            feature_names.extend([f"macd_signal_{i}" for i in range(5)])
            feature_names.extend([f"bb_upper_{i}" for i in range(5)])
            feature_names.extend([f"bb_lower_{i}" for i in range(5)])
            feature_names.extend([f"price_change_{i}" for i in range(5)])
            feature_names.extend([f"volatility_{i}" for i in range(5)])
            
            # Feature fontosságok
            importances = self.model.feature_importances_
            
            # Rendezi a feature-öket fontosság szerint
            feature_importance = {}
            for name, importance in zip(feature_names, importances):
                feature_importance[name] = importance
            
            return feature_importance
        
        except Exception as e:
            logger.error(f"Error getting feature importance: {str(e)}")
            return None
