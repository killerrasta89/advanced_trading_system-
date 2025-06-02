"""
Correlation Analyzer - Elemzi az eszközök közötti korrelációt a portfólió diverzifikációhoz.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('correlation_analyzer')

class CorrelationAnalyzer:
    """
    Elemzi az eszközök közötti korrelációt a portfólió diverzifikációhoz,
    beleértve a korreláció mátrix számítását, korreláció alapú klaszterezést
    és diverzifikációs ajánlásokat.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a CorrelationAnalyzer-t a megadott konfigurációval.
        
        Args:
            config: A CorrelationAnalyzer konfigurációja
        """
        self.config = config
        
        # Konfigurációs beállítások
        self.correlation_window = config.get('correlation_window', 30)  # Korreláció számítási ablak
        self.correlation_threshold = config.get('correlation_threshold', 0.7)  # Magas korreláció küszöbérték
        self.update_interval = config.get('update_interval', 24 * 60 * 60)  # Frissítési intervallum másodpercben
        
        # Korreláció adatok tárolása
        self.correlation_matrix = {}
        self.correlation_clusters = {}
        self.last_update_time = None
        
        # RPI4 optimalizáció
        self.max_lookback = config.get('max_lookback', 100)  # Korlátozott visszatekintés
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        self.max_symbols = config.get('max_symbols', 20)  # Maximális szimbólumok száma
        
        logger.info("CorrelationAnalyzer initialized")
    
    def update_correlation_matrix(self, price_data: Dict[str, List[float]]) -> Dict:
        """
        Frissíti a korreláció mátrixot az árfolyam adatok alapján.
        
        Args:
            price_data: Árfolyam adatok szimbólumonként
            
        Returns:
            Dict: A korreláció mátrix
        """
        try:
            if not price_data:
                logger.warning("Empty price data")
                return {}
            
            # Korlátozza a szimbólumok számát RPI4 optimalizációhoz
            if self.simplify_calculations and len(price_data) > self.max_symbols:
                logger.warning(f"Too many symbols ({len(price_data)}), limiting to {self.max_symbols}")
                symbols = list(price_data.keys())[:self.max_symbols]
                price_data = {symbol: price_data[symbol] for symbol in symbols}
            
            # Konvertálja az árfolyam adatokat DataFrame-mé
            df = pd.DataFrame(price_data)
            
            # Korlátozza a visszatekintést
            lookback = min(df.shape[0], self.correlation_window, self.max_lookback)
            df = df.tail(lookback)
            
            # Hozamok számítása
            returns = df.pct_change().dropna()
            
            # Korreláció mátrix számítása
            correlation_matrix = returns.corr().to_dict()
            
            # Frissíti a korreláció mátrixot
            self.correlation_matrix = correlation_matrix
            self.last_update_time = datetime.now()
            
            # Frissíti a korreláció klasztereket
            self._update_correlation_clusters()
            
            logger.info(f"Correlation matrix updated for {len(correlation_matrix)} symbols")
            
            return self.correlation_matrix
        
        except Exception as e:
            logger.error(f"Error updating correlation matrix: {str(e)}")
            return {}
    
    def _update_correlation_clusters(self) -> None:
        """
        Frissíti a korreláció klasztereket a korreláció mátrix alapján.
        """
        try:
            if not self.correlation_matrix:
                logger.warning("Empty correlation matrix, cannot update clusters")
                return
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Egyszerű klaszterezés: magas korrelációjú párok csoportosítása
                clusters = []
                processed_symbols = set()
                
                symbols = list(self.correlation_matrix.keys())
                
                for symbol1 in symbols:
                    if symbol1 in processed_symbols:
                        continue
                    
                    cluster = [symbol1]
                    processed_symbols.add(symbol1)
                    
                    for symbol2 in symbols:
                        if symbol2 in processed_symbols or symbol2 == symbol1:
                            continue
                        
                        # Ellenőrzi a korrelációt
                        correlation = self.correlation_matrix[symbol1].get(symbol2, 0.0)
                        
                        if abs(correlation) >= self.correlation_threshold:
                            cluster.append(symbol2)
                            processed_symbols.add(symbol2)
                    
                    if len(cluster) > 1:
                        clusters.append(cluster)
                
                # Hozzáadja a még nem feldolgozott szimbólumokat egyedi klaszterként
                for symbol in symbols:
                    if symbol not in processed_symbols:
                        clusters.append([symbol])
                
                self.correlation_clusters = {
                    'clusters': clusters,
                    'timestamp': datetime.now()
                }
            
            else:
                # Fejlettebb klaszterezés: hierarchikus klaszterezés
                # Itt most csak egy egyszerű példa implementáció
                
                # Konvertálja a korreláció mátrixot távolság mátrixszá
                # (1 - abs(korreláció)) -> alacsony korreláció = nagy távolság
                distance_matrix = {}
                
                symbols = list(self.correlation_matrix.keys())
                
                for symbol1 in symbols:
                    distance_matrix[symbol1] = {}
                    for symbol2 in symbols:
                        correlation = self.correlation_matrix[symbol1].get(symbol2, 0.0)
                        distance = 1.0 - abs(correlation)
                        distance_matrix[symbol1][symbol2] = distance
                
                # Egyszerű hierarchikus klaszterezés
                clusters = []
                processed_symbols = set()
                
                while len(processed_symbols) < len(symbols):
                    # Kiválaszt egy még nem feldolgozott szimbólumot
                    seed_symbol = next(symbol for symbol in symbols if symbol not in processed_symbols)
                    
                    # Új klaszter a seed szimbólummal
                    cluster = [seed_symbol]
                    processed_symbols.add(seed_symbol)
                    
                    # Hozzáadja a közeli szimbólumokat a klaszterhez
                    for symbol in symbols:
                        if symbol in processed_symbols:
                            continue
                        
                        # Ellenőrzi a távolságot a klaszter minden elemével
                        min_distance = min(distance_matrix[seed_symbol][symbol] for seed_symbol in cluster)
                        
                        if min_distance <= 0.3:  # Távolság küszöbérték (0.3 = 0.7 korreláció)
                            cluster.append(symbol)
                            processed_symbols.add(symbol)
                    
                    clusters.append(cluster)
                
                self.correlation_clusters = {
                    'clusters': clusters,
                    'timestamp': datetime.now()
                }
        
        except Exception as e:
            logger.error(f"Error updating correlation clusters: {str(e)}")
    
    def get_correlation(self, symbol1: str, symbol2: str) -> Optional[float]:
        """
        Visszaadja két szimbólum közötti korrelációt.
        
        Args:
            symbol1: Az első szimbólum
            symbol2: A második szimbólum
            
        Returns:
            Optional[float]: A korreláció érték, vagy None ha nem található
        """
        try:
            if not self.correlation_matrix:
                logger.warning("Empty correlation matrix")
                return None
            
            if symbol1 not in self.correlation_matrix:
                logger.warning(f"Symbol {symbol1} not found in correlation matrix")
                return None
            
            if symbol2 not in self.correlation_matrix[symbol1]:
                logger.warning(f"Symbol {symbol2} not found in correlation matrix for {symbol1}")
                return None
            
            return self.correlation_matrix[symbol1][symbol2]
        
        except Exception as e:
            logger.error(f"Error getting correlation between {symbol1} and {symbol2}: {str(e)}")
            return None
    
    def get_correlation_matrix(self) -> Dict:
        """
        Visszaadja a teljes korreláció mátrixot.
        
        Returns:
            Dict: A korreláció mátrix
        """
        return self.correlation_matrix
    
    def get_correlation_clusters(self) -> Dict:
        """
        Visszaadja a korreláció klasztereket.
        
        Returns:
            Dict: A korreláció klaszterek
        """
        return self.correlation_clusters
    
    def get_highly_correlated_pairs(self, threshold: Optional[float] = None) -> List[Tuple[str, str, float]]:
        """
        Visszaadja a magas korrelációjú párokat.
        
        Args:
            threshold: Korreláció küszöbérték (opcionális, alapértelmezett: self.correlation_threshold)
            
        Returns:
            List[Tuple[str, str, float]]: A magas korrelációjú párok listája (szimbólum1, szimbólum2, korreláció)
        """
        try:
            if not self.correlation_matrix:
                logger.warning("Empty correlation matrix")
                return []
            
            if threshold is None:
                threshold = self.correlation_threshold
            
            highly_correlated_pairs = []
            
            symbols = list(self.correlation_matrix.keys())
            
            for i, symbol1 in enumerate(symbols):
                for symbol2 in symbols[i+1:]:  # Csak a mátrix felső háromszögét nézi
                    correlation = self.correlation_matrix[symbol1].get(symbol2, 0.0)
                    
                    if abs(correlation) >= threshold:
                        highly_correlated_pairs.append((symbol1, symbol2, correlation))
            
            # Rendezi a párokat korreláció szerint (csökkenő sorrendben)
            highly_correlated_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            return highly_correlated_pairs
        
        except Exception as e:
            logger.error(f"Error getting highly correlated pairs: {str(e)}")
            return []
    
    def get_diversification_recommendations(self, portfolio_symbols: List[str]) -> Dict:
        """
        Ajánlásokat ad a portfólió diverzifikációjához.
        
        Args:
            portfolio_symbols: A portfólióban lévő szimbólumok listája
            
        Returns:
            Dict: Diverzifikációs ajánlások
        """
        try:
            if not self.correlation_matrix:
                logger.warning("Empty correlation matrix")
                return {'error': 'Empty correlation matrix'}
            
            if not portfolio_symbols:
                logger.warning("Empty portfolio symbols")
                return {'error': 'Empty portfolio symbols'}
            
            # Ellenőrzi, hogy a szimbólumok szerepelnek-e a korreláció mátrixban
            valid_symbols = [symbol for symbol in portfolio_symbols if symbol in self.correlation_matrix]
            
            if not valid_symbols:
                logger.warning("No valid symbols in portfolio")
                return {'error': 'No valid symbols in portfolio'}
            
            # Átlagos korreláció a portfólión belül
            avg_correlation = 0.0
            pair_count = 0
            
            for i, symbol1 in enumerate(valid_symbols):
                for symbol2 in valid_symbols[i+1:]:
                    correlation = self.correlation_matrix[symbol1].get(symbol2, 0.0)
                    avg_correlation += abs(correlation)
                    pair_count += 1
            
            if pair_count > 0:
                avg_correlation /= pair_count
            
            # Magas korrelációjú párok a portfólión belül
            highly_correlated_pairs = []
            
            for i, symbol1 in enumerate(valid_symbols):
                for symbol2 in valid_symbols[i+1:]:
                    correlation = self.correlation_matrix[symbol1].get(symbol2, 0.0)
                    
                    if abs(correlation) >= self.correlation_threshold:
                        highly_correlated_pairs.append((symbol1, symbol2, correlation))
            
            # Rendezi a párokat korreláció szerint (csökkenő sorrendben)
            highly_correlated_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            
            # Ajánlott eltávolítandó szimbólumok (a magas korrelációjú párokból)
            symbols_to_remove = set()
            
            for symbol1, symbol2, correlation in highly_correlated_pairs:
                # Ha mindkét szimbólum még a portfólióban van, akkor az egyiket eltávolítja
                if symbol1 not in symbols_to_remove and symbol2 not in symbols_to_remove:
                    # Az alacsonyabb súlyút távolítja el (itt most egyszerűen a második)
                    symbols_to_remove.add(symbol2)
            
            # Ajánlott hozzáadandó szimbólumok (alacsony korreláció a portfólióval)
            symbols_to_add = []
            
            all_symbols = list(self.correlation_matrix.keys())
            
            for symbol in all_symbols:
                if symbol in valid_symbols:
                    continue
                
                # Átlagos korreláció a portfólióval
                avg_corr_with_portfolio = 0.0
                
                for portfolio_symbol in valid_symbols:
                    correlation = self.correlation_matrix[symbol].get(portfolio_symbol, 0.0)
                    avg_corr_with_portfolio += abs(correlation)
                
                if valid_symbols:
                    avg_corr_with_portfolio /= len(valid_symbols)
                
                # Ha az átlagos korreláció alacsony, akkor ajánlja
                if avg_corr_with_portfolio < 0.3:  # Alacsony korreláció küszöbérték
                    symbols_to_add.append((symbol, avg_corr_with_portfolio))
            
            # Rendezi az ajánlott szimbólumokat korreláció szerint (növekvő sorrendben)
            symbols_to_add.sort(key=lambda x: x[1])
            
            # Korlátozza az ajánlások számát
            symbols_to_add = symbols_to_add[:5]  # Maximum 5 ajánlás
            
            return {
                'avg_correlation': avg_correlation,
                'highly_correlated_pairs': highly_correlated_pairs,
                'symbols_to_remove': list(symbols_to_remove),
                'symbols_to_add': [symbol for symbol, _ in symbols_to_add],
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error getting diversification recommendations: {str(e)}")
            return {'error': str(e)}
    
    def calculate_portfolio_diversification_score(self, portfolio_symbols: List[str]) -> Dict:
        """
        Kiszámítja a portfólió diverzifikációs pontszámát.
        
        Args:
            portfolio_symbols: A portfólióban lévő szimbólumok listája
            
        Returns:
            Dict: A diverzifikációs pontszám
        """
        try:
            if not self.correlation_matrix:
                logger.warning("Empty correlation matrix")
                return {'diversification_score': 0.0, 'error': 'Empty correlation matrix'}
            
            if not portfolio_symbols:
                logger.warning("Empty portfolio symbols")
                return {'diversification_score': 0.0, 'error': 'Empty portfolio symbols'}
            
            # Ellenőrzi, hogy a szimbólumok szerepelnek-e a korreláció mátrixban
            valid_symbols = [symbol for symbol in portfolio_symbols if symbol in self.correlation_matrix]
            
            if not valid_symbols:
                logger.warning("No valid symbols in portfolio")
                return {'diversification_score': 0.0, 'error': 'No valid symbols in portfolio'}
            
            # Átlagos abszolút korreláció a portfólión belül
            avg_correlation = 0.0
            pair_count = 0
            
            for i, symbol1 in enumerate(valid_symbols):
                for symbol2 in valid_symbols[i+1:]:
                    correlation = self.correlation_matrix[symbol1].get(symbol2, 0.0)
                    avg_correlation += abs(correlation)
                    pair_count += 1
            
            if pair_count > 0:
                avg_correlation /= pair_count
            
            # Diverzifikációs pontszám (1 - átlagos korreláció)
            # 0 = nincs diverzifikáció, 1 = tökéletes diverzifikáció
            diversification_score = 1.0 - avg_correlation
            
            return {
                'diversification_score': diversification_score,
                'avg_correlation': avg_correlation,
                'valid_symbols': valid_symbols,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating portfolio diversification score: {str(e)}")
            return {'diversification_score': 0.0, 'error': str(e)}
    
    def needs_update(self) -> bool:
        """
        Ellenőrzi, hogy a korreláció mátrixnak szüksége van-e frissítésre.
        
        Returns:
            bool: True, ha a korreláció mátrixnak frissítésre van szüksége, egyébként False
        """
        if not self.correlation_matrix or self.last_update_time is None:
            return True
        
        elapsed_seconds = (datetime.now() - self.last_update_time).total_seconds()
        return elapsed_seconds >= self.update_interval
    
    def get_correlation_heatmap_data(self) -> Dict:
        """
        Visszaadja a korreláció hőtérkép adatokat.
        
        Returns:
            Dict: A korreláció hőtérkép adatok
        """
        try:
            if not self.correlation_matrix:
                logger.warning("Empty correlation matrix")
                return {'error': 'Empty correlation matrix'}
            
            symbols = list(self.correlation_matrix.keys())
            
            # Hőtérkép adatok
            heatmap_data = []
            
            for symbol1 in symbols:
                for symbol2 in symbols:
                    correlation = self.correlation_matrix[symbol1].get(symbol2, 0.0)
                    
                    heatmap_data.append({
                        'x': symbol1,
                        'y': symbol2,
                        'value': correlation
                    })
            
            return {
                'symbols': symbols,
                'data': heatmap_data,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error getting correlation heatmap data: {str(e)}")
            return {'error': str(e)}
