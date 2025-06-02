"""
Pattern Recognition - Felismeri a technikai mintákat az árfolyamgrafikonon.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('pattern_recognition')

class PatternRecognition:
    """
    Felismeri a technikai mintákat az árfolyamgrafikonon, mint például
    támasz/ellenállás szintek, trendvonalak, gyertyaformációk és chart minták.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a PatternRecognition-t a megadott konfigurációval.
        
        Args:
            config: A PatternRecognition konfigurációja
        """
        self.config = config
        
        # Konfigurációs beállítások
        self.min_pattern_points = config.get('min_pattern_points', 3)  # Minimum pontok száma egy minta felismeréséhez
        self.support_resistance_lookback = config.get('support_resistance_lookback', 100)  # Visszatekintési időszak
        self.candlestick_patterns = config.get('candlestick_patterns', [
            'doji', 'hammer', 'inverted_hammer', 'engulfing', 'morning_star', 'evening_star'
        ])
        self.chart_patterns = config.get('chart_patterns', [
            'head_and_shoulders', 'double_top', 'double_bottom', 'triangle', 'flag', 'wedge'
        ])
        
        # RPI4 optimalizáció
        self.max_lookback = config.get('max_lookback', 200)  # Korlátozott visszatekintés
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        
        logger.info("PatternRecognition initialized")
    
    def analyze(self, ohlcv_data: List[List]) -> Dict:
        """
        Elemzi az OHLCV adatokat és felismeri a mintákat.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            Dict: A felismert minták
        """
        try:
            if len(ohlcv_data) < self.min_pattern_points:
                logger.warning(f"Not enough data points for pattern recognition: {len(ohlcv_data)} < {self.min_pattern_points}")
                return {}
            
            # Konvertálja az OHLCV adatokat DataFrame-mé
            df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Felismeri a különböző mintákat
            patterns = {}
            
            # 1. Támasz/ellenállás szintek
            patterns['support_resistance'] = self._identify_support_resistance(df)
            
            # 2. Trendvonalak
            patterns['trendlines'] = self._identify_trendlines(df)
            
            # 3. Gyertyaformációk
            patterns['candlestick_patterns'] = self._identify_candlestick_patterns(df)
            
            # 4. Chart minták
            patterns['chart_patterns'] = self._identify_chart_patterns(df)
            
            logger.info(f"Pattern analysis completed, found: {self._count_patterns(patterns)} patterns")
            return patterns
        
        except Exception as e:
            logger.error(f"Error analyzing patterns: {str(e)}")
            return {}
    
    def _count_patterns(self, patterns: Dict) -> int:
        """
        Megszámolja a felismert minták számát.
        
        Args:
            patterns: A felismert minták
            
        Returns:
            int: A minták száma
        """
        count = 0
        
        # Támasz/ellenállás szintek
        if 'support_resistance' in patterns:
            count += len(patterns['support_resistance'].get('support', []))
            count += len(patterns['support_resistance'].get('resistance', []))
        
        # Trendvonalak
        if 'trendlines' in patterns:
            count += len(patterns['trendlines'].get('uptrend', []))
            count += len(patterns['trendlines'].get('downtrend', []))
        
        # Gyertyaformációk
        if 'candlestick_patterns' in patterns:
            for pattern_type, occurrences in patterns['candlestick_patterns'].items():
                count += len(occurrences)
        
        # Chart minták
        if 'chart_patterns' in patterns:
            for pattern_type, occurrences in patterns['chart_patterns'].items():
                count += len(occurrences)
        
        return count
    
    def _identify_support_resistance(self, df: pd.DataFrame) -> Dict:
        """
        Azonosítja a támasz és ellenállás szinteket.
        
        Args:
            df: OHLCV adatok DataFrame-ben
            
        Returns:
            Dict: A támasz és ellenállás szintek
        """
        try:
            # Korlátozza a visszatekintést
            lookback = min(self.support_resistance_lookback, len(df), self.max_lookback)
            df_subset = df.tail(lookback)
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Egyszerű módszer: lokális minimumok és maximumok keresése
                support_levels = []
                resistance_levels = []
                
                # Lokális minimumok (támasz)
                for i in range(2, len(df_subset) - 2):
                    if (df_subset.iloc[i]['low'] < df_subset.iloc[i-1]['low'] and 
                        df_subset.iloc[i]['low'] < df_subset.iloc[i-2]['low'] and
                        df_subset.iloc[i]['low'] < df_subset.iloc[i+1]['low'] and
                        df_subset.iloc[i]['low'] < df_subset.iloc[i+2]['low']):
                        
                        support_levels.append({
                            'price': df_subset.iloc[i]['low'],
                            'timestamp': df_subset.iloc[i]['timestamp'],
                            'strength': 1.0  # Egyszerűsített erősség
                        })
                
                # Lokális maximumok (ellenállás)
                for i in range(2, len(df_subset) - 2):
                    if (df_subset.iloc[i]['high'] > df_subset.iloc[i-1]['high'] and 
                        df_subset.iloc[i]['high'] > df_subset.iloc[i-2]['high'] and
                        df_subset.iloc[i]['high'] > df_subset.iloc[i+1]['high'] and
                        df_subset.iloc[i]['high'] > df_subset.iloc[i+2]['high']):
                        
                        resistance_levels.append({
                            'price': df_subset.iloc[i]['high'],
                            'timestamp': df_subset.iloc[i]['timestamp'],
                            'strength': 1.0  # Egyszerűsített erősség
                        })
            
            else:
                # Fejlettebb módszer: hisztogram alapú szintek keresése
                # Árak hisztogramja
                price_range = df_subset['high'].max() - df_subset['low'].min()
                bin_size = price_range / 50  # 50 bin
                
                # Alacsony árak hisztogramja
                low_hist, low_bins = np.histogram(df_subset['low'], bins=50)
                
                # Magas árak hisztogramja
                high_hist, high_bins = np.histogram(df_subset['high'], bins=50)
                
                # Támasz szintek (lokális csúcsok az alacsony árak hisztogramjában)
                support_levels = []
                for i in range(1, len(low_hist) - 1):
                    if low_hist[i] > low_hist[i-1] and low_hist[i] > low_hist[i+1] and low_hist[i] > 2:
                        price = (low_bins[i] + low_bins[i+1]) / 2
                        support_levels.append({
                            'price': price,
                            'timestamp': None,  # Nincs konkrét időpont
                            'strength': float(low_hist[i]) / low_hist.max()  # Normalizált erősség
                        })
                
                # Ellenállás szintek (lokális csúcsok a magas árak hisztogramjában)
                resistance_levels = []
                for i in range(1, len(high_hist) - 1):
                    if high_hist[i] > high_hist[i-1] and high_hist[i] > high_hist[i+1] and high_hist[i] > 2:
                        price = (high_bins[i] + high_bins[i+1]) / 2
                        resistance_levels.append({
                            'price': price,
                            'timestamp': None,  # Nincs konkrét időpont
                            'strength': float(high_hist[i]) / high_hist.max()  # Normalizált erősség
                        })
            
            # Összevonja a közeli szinteket
            support_levels = self._merge_close_levels(support_levels)
            resistance_levels = self._merge_close_levels(resistance_levels)
            
            return {
                'support': support_levels,
                'resistance': resistance_levels
            }
        
        except Exception as e:
            logger.error(f"Error identifying support/resistance levels: {str(e)}")
            return {'support': [], 'resistance': []}
    
    def _merge_close_levels(self, levels: List[Dict]) -> List[Dict]:
        """
        Összevonja a közeli árszinteket.
        
        Args:
            levels: Árszintek listája
            
        Returns:
            List[Dict]: Az összevont árszintek
        """
        if not levels:
            return []
        
        # Rendezi az árszinteket ár szerint
        sorted_levels = sorted(levels, key=lambda x: x['price'])
        
        # Összevonja a közeli szinteket
        merged_levels = []
        current_level = sorted_levels[0]
        
        for level in sorted_levels[1:]:
            # Ha a szint közel van az aktuális szinthez, összevonja őket
            if abs(level['price'] - current_level['price']) / current_level['price'] < 0.01:  # 1% különbség
                # Súlyozott átlag az erősség alapján
                total_strength = current_level['strength'] + level['strength']
                current_level['price'] = (current_level['price'] * current_level['strength'] + 
                                         level['price'] * level['strength']) / total_strength
                current_level['strength'] = total_strength
            else:
                merged_levels.append(current_level)
                current_level = level
        
        merged_levels.append(current_level)
        return merged_levels
    
    def _identify_trendlines(self, df: pd.DataFrame) -> Dict:
        """
        Azonosítja a trendvonalakat.
        
        Args:
            df: OHLCV adatok DataFrame-ben
            
        Returns:
            Dict: A trendvonalak
        """
        try:
            # Korlátozza a visszatekintést
            lookback = min(len(df), self.max_lookback)
            df_subset = df.tail(lookback)
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Egyszerű módszer: lineáris regresszió az utolsó N gyertyára
                n_candles = min(20, len(df_subset))
                last_n = df_subset.tail(n_candles)
                
                # Időpontok konvertálása számokká (x tengely)
                x = np.arange(n_candles)
                
                # Záróárak (y tengely)
                y = last_n['close'].values
                
                # Lineáris regresszió
                slope, intercept = np.polyfit(x, y, 1)
                
                # Trendvonal pontok
                start_price = intercept
                end_price = intercept + slope * (n_candles - 1)
                
                # Trendirány meghatározása
                if slope > 0:
                    trendlines = {
                        'uptrend': [{
                            'start': {'price': start_price, 'timestamp': last_n.iloc[0]['timestamp']},
                            'end': {'price': end_price, 'timestamp': last_n.iloc[-1]['timestamp']},
                            'slope': slope,
                            'strength': abs(slope) / start_price  # Normalizált meredekség
                        }],
                        'downtrend': []
                    }
                else:
                    trendlines = {
                        'uptrend': [],
                        'downtrend': [{
                            'start': {'price': start_price, 'timestamp': last_n.iloc[0]['timestamp']},
                            'end': {'price': end_price, 'timestamp': last_n.iloc[-1]['timestamp']},
                            'slope': slope,
                            'strength': abs(slope) / start_price  # Normalizált meredekség
                        }]
                    }
            
            else:
                # Fejlettebb módszer: lokális minimumok/maximumok közötti trendvonalak
                # Lokális minimumok keresése
                local_mins = []
                for i in range(2, len(df_subset) - 2):
                    if (df_subset.iloc[i]['low'] < df_subset.iloc[i-1]['low'] and 
                        df_subset.iloc[i]['low'] < df_subset.iloc[i-2]['low'] and
                        df_subset.iloc[i]['low'] < df_subset.iloc[i+1]['low'] and
                        df_subset.iloc[i]['low'] < df_subset.iloc[i+2]['low']):
                        
                        local_mins.append((i, df_subset.iloc[i]['timestamp'], df_subset.iloc[i]['low']))
                
                # Lokális maximumok keresése
                local_maxs = []
                for i in range(2, len(df_subset) - 2):
                    if (df_subset.iloc[i]['high'] > df_subset.iloc[i-1]['high'] and 
                        df_subset.iloc[i]['high'] > df_subset.iloc[i-2]['high'] and
                        df_subset.iloc[i]['high'] > df_subset.iloc[i+1]['high'] and
                        df_subset.iloc[i]['high'] > df_subset.iloc[i+2]['high']):
                        
                        local_maxs.append((i, df_subset.iloc[i]['timestamp'], df_subset.iloc[i]['high']))
                
                # Emelkedő trendvonalak (lokális minimumok között)
                uptrends = []
                for i in range(len(local_mins) - 1):
                    for j in range(i + 1, len(local_mins)):
                        idx1, ts1, price1 = local_mins[i]
                        idx2, ts2, price2 = local_mins[j]
                        
                        # Csak emelkedő trendvonalak
                        if price2 > price1:
                            # Ellenőrzi, hogy a trendvonal alatt van-e minden gyertya
                            valid_trendline = True
                            slope = (price2 - price1) / (idx2 - idx1)
                            
                            for k in range(idx1 + 1, idx2):
                                expected_price = price1 + slope * (k - idx1)
                                if df_subset.iloc[k]['low'] < expected_price:
                                    valid_trendline = False
                                    break
                            
                            if valid_trendline:
                                uptrends.append({
                                    'start': {'price': price1, 'timestamp': ts1},
                                    'end': {'price': price2, 'timestamp': ts2},
                                    'slope': slope,
                                    'strength': (idx2 - idx1) / len(df_subset)  # Normalizált hossz
                                })
                
                # Csökkenő trendvonalak (lokális maximumok között)
                downtrends = []
                for i in range(len(local_maxs) - 1):
                    for j in range(i + 1, len(local_maxs)):
                        idx1, ts1, price1 = local_maxs[i]
                        idx2, ts2, price2 = local_maxs[j]
                        
                        # Csak csökkenő trendvonalak
                        if price2 < price1:
                            # Ellenőrzi, hogy a trendvonal felett van-e minden gyertya
                            valid_trendline = True
                            slope = (price2 - price1) / (idx2 - idx1)
                            
                            for k in range(idx1 + 1, idx2):
                                expected_price = price1 + slope * (k - idx1)
                                if df_subset.iloc[k]['high'] > expected_price:
                                    valid_trendline = False
                                    break
                            
                            if valid_trendline:
                                downtrends.append({
                                    'start': {'price': price1, 'timestamp': ts1},
                                    'end': {'price': price2, 'timestamp': ts2},
                                    'slope': slope,
                                    'strength': (idx2 - idx1) / len(df_subset)  # Normalizált hossz
                                })
                
                trendlines = {
                    'uptrend': uptrends,
                    'downtrend': downtrends
                }
            
            return trendlines
        
        except Exception as e:
            logger.error(f"Error identifying trendlines: {str(e)}")
            return {'uptrend': [], 'downtrend': []}
    
    def _identify_candlestick_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Azonosítja a gyertyaformációkat.
        
        Args:
            df: OHLCV adatok DataFrame-ben
            
        Returns:
            Dict: A gyertyaformációk
        """
        try:
            # Korlátozza a visszatekintést
            lookback = min(len(df), self.max_lookback)
            df_subset = df.tail(lookback)
            
            patterns = {pattern: [] for pattern in self.candlestick_patterns}
            
            # Doji
            if 'doji' in self.candlestick_patterns:
                for i in range(len(df_subset)):
                    row = df_subset.iloc[i]
                    body_size = abs(row['close'] - row['open'])
                    total_size = row['high'] - row['low']
                    
                    if total_size > 0 and body_size / total_size < 0.1:  # Doji: test mérete < 10% teljes méret
                        patterns['doji'].append({
                            'timestamp': row['timestamp'],
                            'price': row['close'],
                            'strength': 1.0 - (body_size / total_size)  # Erősség: minél kisebb a test, annál erősebb
                        })
            
            # Hammer (Kalapács)
            if 'hammer' in self.candlestick_patterns:
                for i in range(1, len(df_subset)):
                    prev_row = df_subset.iloc[i-1]
                    row = df_subset.iloc[i]
                    
                    # Downtrend
                    if row['open'] < prev_row['close']:
                        body_size = abs(row['close'] - row['open'])
                        lower_shadow = min(row['open'], row['close']) - row['low']
                        upper_shadow = row['high'] - max(row['open'], row['close'])
                        
                        # Hammer: alsó árnyék legalább 2x test méret, felső árnyék kicsi
                        if body_size > 0 and lower_shadow > 2 * body_size and upper_shadow < 0.2 * body_size:
                            patterns['hammer'].append({
                                'timestamp': row['timestamp'],
                                'price': row['close'],
                                'strength': lower_shadow / body_size  # Erősség: minél nagyobb az alsó árnyék, annál erősebb
                            })
            
            # Inverted Hammer (Fordított Kalapács)
            if 'inverted_hammer' in self.candlestick_patterns:
                for i in range(1, len(df_subset)):
                    prev_row = df_subset.iloc[i-1]
                    row = df_subset.iloc[i]
                    
                    # Downtrend
                    if row['open'] < prev_row['close']:
                        body_size = abs(row['close'] - row['open'])
                        lower_shadow = min(row['open'], row['close']) - row['low']
                        upper_shadow = row['high'] - max(row['open'], row['close'])
                        
                        # Inverted Hammer: felső árnyék legalább 2x test méret, alsó árnyék kicsi
                        if body_size > 0 and upper_shadow > 2 * body_size and lower_shadow < 0.2 * body_size:
                            patterns['inverted_hammer'].append({
                                'timestamp': row['timestamp'],
                                'price': row['close'],
                                'strength': upper_shadow / body_size  # Erősség: minél nagyobb a felső árnyék, annál erősebb
                            })
            
            # Engulfing (Elnyelő)
            if 'engulfing' in self.candlestick_patterns:
                for i in range(1, len(df_subset)):
                    prev_row = df_subset.iloc[i-1]
                    row = df_subset.iloc[i]
                    
                    prev_body_size = abs(prev_row['close'] - prev_row['open'])
                    body_size = abs(row['close'] - row['open'])
                    
                    # Bullish Engulfing: előző gyertya bearish, aktuális gyertya bullish és nagyobb
                    if (prev_row['close'] < prev_row['open'] and  # Előző bearish
                        row['close'] > row['open'] and  # Aktuális bullish
                        row['open'] < prev_row['close'] and  # Aktuális open < előző close
                        row['close'] > prev_row['open']):  # Aktuális close > előző open
                        
                        patterns['engulfing'].append({
                            'timestamp': row['timestamp'],
                            'price': row['close'],
                            'type': 'bullish',
                            'strength': body_size / prev_body_size  # Erősség: minél nagyobb a test az előzőhöz képest, annál erősebb
                        })
                    
                    # Bearish Engulfing: előző gyertya bullish, aktuális gyertya bearish és nagyobb
                    elif (prev_row['close'] > prev_row['open'] and  # Előző bullish
                          row['close'] < row['open'] and  # Aktuális bearish
                          row['open'] > prev_row['close'] and  # Aktuális open > előző close
                          row['close'] < prev_row['open']):  # Aktuális close < előző open
                        
                        patterns['engulfing'].append({
                            'timestamp': row['timestamp'],
                            'price': row['close'],
                            'type': 'bearish',
                            'strength': body_size / prev_body_size  # Erősség: minél nagyobb a test az előzőhöz képest, annál erősebb
                        })
            
            # Morning Star (Hajnalcsillag)
            if 'morning_star' in self.candlestick_patterns and len(df_subset) >= 3:
                for i in range(2, len(df_subset)):
                    first_row = df_subset.iloc[i-2]
                    middle_row = df_subset.iloc[i-1]
                    last_row = df_subset.iloc[i]
                    
                    first_body_size = abs(first_row['close'] - first_row['open'])
                    middle_body_size = abs(middle_row['close'] - middle_row['open'])
                    last_body_size = abs(last_row['close'] - last_row['open'])
                    
                    # Morning Star: első gyertya bearish és nagy, középső kicsi, utolsó bullish és nagy
                    if (first_row['close'] < first_row['open'] and  # Első bearish
                        middle_body_size < 0.3 * first_body_size and  # Középső kicsi
                        last_row['close'] > last_row['open'] and  # Utolsó bullish
                        last_row['close'] > (first_row['open'] + first_row['close']) / 2):  # Utolsó close > első középpont
                        
                        patterns['morning_star'].append({
                            'timestamp': last_row['timestamp'],
                            'price': last_row['close'],
                            'strength': last_body_size / first_body_size  # Erősség: utolsó és első test aránya
                        })
            
            # Evening Star (Estcsillag)
            if 'evening_star' in self.candlestick_patterns and len(df_subset) >= 3:
                for i in range(2, len(df_subset)):
                    first_row = df_subset.iloc[i-2]
                    middle_row = df_subset.iloc[i-1]
                    last_row = df_subset.iloc[i]
                    
                    first_body_size = abs(first_row['close'] - first_row['open'])
                    middle_body_size = abs(middle_row['close'] - middle_row['open'])
                    last_body_size = abs(last_row['close'] - last_row['open'])
                    
                    # Evening Star: első gyertya bullish és nagy, középső kicsi, utolsó bearish és nagy
                    if (first_row['close'] > first_row['open'] and  # Első bullish
                        middle_body_size < 0.3 * first_body_size and  # Középső kicsi
                        last_row['close'] < last_row['open'] and  # Utolsó bearish
                        last_row['close'] < (first_row['open'] + first_row['close']) / 2):  # Utolsó close < első középpont
                        
                        patterns['evening_star'].append({
                            'timestamp': last_row['timestamp'],
                            'price': last_row['close'],
                            'strength': last_body_size / first_body_size  # Erősség: utolsó és első test aránya
                        })
            
            return patterns
        
        except Exception as e:
            logger.error(f"Error identifying candlestick patterns: {str(e)}")
            return {pattern: [] for pattern in self.candlestick_patterns}
    
    def _identify_chart_patterns(self, df: pd.DataFrame) -> Dict:
        """
        Azonosítja a chart mintákat.
        
        Args:
            df: OHLCV adatok DataFrame-ben
            
        Returns:
            Dict: A chart minták
        """
        try:
            # Korlátozza a visszatekintést
            lookback = min(len(df), self.max_lookback)
            df_subset = df.tail(lookback)
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Egyszerűsített implementáció: csak a legutolsó néhány gyertyát vizsgálja
                return {pattern: [] for pattern in self.chart_patterns}
            
            patterns = {pattern: [] for pattern in self.chart_patterns}
            
            # Lokális minimumok és maximumok keresése
            local_mins = []
            for i in range(2, len(df_subset) - 2):
                if (df_subset.iloc[i]['low'] < df_subset.iloc[i-1]['low'] and 
                    df_subset.iloc[i]['low'] < df_subset.iloc[i-2]['low'] and
                    df_subset.iloc[i]['low'] < df_subset.iloc[i+1]['low'] and
                    df_subset.iloc[i]['low'] < df_subset.iloc[i+2]['low']):
                    
                    local_mins.append((i, df_subset.iloc[i]['timestamp'], df_subset.iloc[i]['low']))
            
            local_maxs = []
            for i in range(2, len(df_subset) - 2):
                if (df_subset.iloc[i]['high'] > df_subset.iloc[i-1]['high'] and 
                    df_subset.iloc[i]['high'] > df_subset.iloc[i-2]['high'] and
                    df_subset.iloc[i]['high'] > df_subset.iloc[i+1]['high'] and
                    df_subset.iloc[i]['high'] > df_subset.iloc[i+2]['high']):
                    
                    local_maxs.append((i, df_subset.iloc[i]['timestamp'], df_subset.iloc[i]['high']))
            
            # Head and Shoulders (Fej és vállak)
            if 'head_and_shoulders' in self.chart_patterns and len(local_maxs) >= 3:
                for i in range(len(local_maxs) - 2):
                    left_shoulder_idx, left_shoulder_ts, left_shoulder_price = local_maxs[i]
                    head_idx, head_ts, head_price = local_maxs[i+1]
                    right_shoulder_idx, right_shoulder_ts, right_shoulder_price = local_maxs[i+2]
                    
                    # Ellenőrzi a fej és vállak mintát
                    if (head_idx > left_shoulder_idx and head_idx < right_shoulder_idx and
                        head_price > left_shoulder_price and head_price > right_shoulder_price and
                        abs(left_shoulder_price - right_shoulder_price) / left_shoulder_price < 0.1):  # Vállak közel azonos magasságban
                        
                        # Neckline (nyakvonal) keresése
                        neckline_price = (left_shoulder_price + right_shoulder_price) / 2
                        
                        patterns['head_and_shoulders'].append({
                            'timestamp': right_shoulder_ts,
                            'price': right_shoulder_price,
                            'neckline': neckline_price,
                            'strength': (head_price - neckline_price) / neckline_price  # Erősség: fej magassága a nyakvonalhoz képest
                        })
            
            # Double Top (Dupla csúcs)
            if 'double_top' in self.chart_patterns and len(local_maxs) >= 2:
                for i in range(len(local_maxs) - 1):
                    first_top_idx, first_top_ts, first_top_price = local_maxs[i]
                    second_top_idx, second_top_ts, second_top_price = local_maxs[i+1]
                    
                    # Ellenőrzi a dupla csúcs mintát
                    if (second_top_idx - first_top_idx > 5 and  # Elegendő távolság a csúcsok között
                        abs(first_top_price - second_top_price) / first_top_price < 0.05):  # Csúcsok közel azonos magasságban
                        
                        # Neckline (nyakvonal) keresése
                        min_price = float('inf')
                        for j in range(first_top_idx, second_top_idx):
                            min_price = min(min_price, df_subset.iloc[j]['low'])
                        
                        patterns['double_top'].append({
                            'timestamp': second_top_ts,
                            'price': second_top_price,
                            'neckline': min_price,
                            'strength': (second_top_price - min_price) / min_price  # Erősség: csúcs magassága a nyakvonalhoz képest
                        })
            
            # Double Bottom (Dupla mélypont)
            if 'double_bottom' in self.chart_patterns and len(local_mins) >= 2:
                for i in range(len(local_mins) - 1):
                    first_bottom_idx, first_bottom_ts, first_bottom_price = local_mins[i]
                    second_bottom_idx, second_bottom_ts, second_bottom_price = local_mins[i+1]
                    
                    # Ellenőrzi a dupla mélypont mintát
                    if (second_bottom_idx - first_bottom_idx > 5 and  # Elegendő távolság a mélypontok között
                        abs(first_bottom_price - second_bottom_price) / first_bottom_price < 0.05):  # Mélypontok közel azonos szinten
                        
                        # Neckline (nyakvonal) keresése
                        max_price = float('-inf')
                        for j in range(first_bottom_idx, second_bottom_idx):
                            max_price = max(max_price, df_subset.iloc[j]['high'])
                        
                        patterns['double_bottom'].append({
                            'timestamp': second_bottom_ts,
                            'price': second_bottom_price,
                            'neckline': max_price,
                            'strength': (max_price - second_bottom_price) / second_bottom_price  # Erősség: nyakvonal magassága a mélyponthoz képest
                        })
            
            # Triangle (Háromszög)
            if 'triangle' in self.chart_patterns and len(local_maxs) >= 2 and len(local_mins) >= 2:
                # Csak az utolsó néhány lokális maximumot és minimumot vizsgálja
                recent_maxs = local_maxs[-3:]
                recent_mins = local_mins[-3:]
                
                if len(recent_maxs) >= 2 and len(recent_mins) >= 2:
                    # Ellenőrzi a csökkenő maximumokat
                    descending_maxs = all(recent_maxs[i][2] > recent_maxs[i+1][2] for i in range(len(recent_maxs)-1))
                    
                    # Ellenőrzi a növekvő minimumokat
                    ascending_mins = all(recent_mins[i][2] < recent_mins[i+1][2] for i in range(len(recent_mins)-1))
                    
                    # Szimmetrikus háromszög
                    if descending_maxs and ascending_mins:
                        patterns['triangle'].append({
                            'timestamp': max(recent_maxs[-1][1], recent_mins[-1][1]),
                            'price': (recent_maxs[-1][2] + recent_mins[-1][2]) / 2,
                            'type': 'symmetrical',
                            'strength': 1.0 - abs(recent_maxs[-1][2] - recent_mins[-1][2]) / recent_maxs[-1][2]  # Erősség: minél közelebb a csúcs és mélypont, annál erősebb
                        })
                    
                    # Emelkedő háromszög
                    elif not descending_maxs and ascending_mins:
                        patterns['triangle'].append({
                            'timestamp': max(recent_maxs[-1][1], recent_mins[-1][1]),
                            'price': (recent_maxs[-1][2] + recent_mins[-1][2]) / 2,
                            'type': 'ascending',
                            'strength': (recent_mins[-1][2] - recent_mins[0][2]) / recent_mins[0][2]  # Erősség: minimumok emelkedése
                        })
                    
                    # Csökkenő háromszög
                    elif descending_maxs and not ascending_mins:
                        patterns['triangle'].append({
                            'timestamp': max(recent_maxs[-1][1], recent_mins[-1][1]),
                            'price': (recent_maxs[-1][2] + recent_mins[-1][2]) / 2,
                            'type': 'descending',
                            'strength': (recent_maxs[0][2] - recent_maxs[-1][2]) / recent_maxs[0][2]  # Erősség: maximumok csökkenése
                        })
            
            return patterns
        
        except Exception as e:
            logger.error(f"Error identifying chart patterns: {str(e)}")
            return {pattern: [] for pattern in self.chart_patterns}
