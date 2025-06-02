"""
Technical Indicators - Technikai indikátorok implementációja
"""
import numpy as np
import pandas as pd

class TechnicalIndicators:
    """
    Technikai indikátorok számítása
    """
    
    @staticmethod
    def sma(data, period=14):
        """
        Simple Moving Average (SMA) számítása
        
        Args:
            data (array-like): Adatok
            period (int): Periódus
            
        Returns:
            array-like: SMA értékek
        """
        return pd.Series(data).rolling(window=period).mean().values
    
    @staticmethod
    def ema(data, period=14):
        """
        Exponential Moving Average (EMA) számítása
        
        Args:
            data (array-like): Adatok
            period (int): Periódus
            
        Returns:
            array-like: EMA értékek
        """
        return pd.Series(data).ewm(span=period, adjust=False).mean().values
    
    @staticmethod
    def rsi(data, period=14):
        """
        Relative Strength Index (RSI) számítása
        
        Args:
            data (array-like): Adatok
            period (int): Periódus
            
        Returns:
            array-like: RSI értékek
        """
        delta = pd.Series(data).diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.values
    
    @staticmethod
    def macd(data, fast_period=12, slow_period=26, signal_period=9):
        """
        Moving Average Convergence Divergence (MACD) számítása
        
        Args:
            data (array-like): Adatok
            fast_period (int): Gyors periódus
            slow_period (int): Lassú periódus
            signal_period (int): Jelzés periódus
            
        Returns:
            tuple: (MACD, Signal, Histogram)
        """
        ema_fast = pd.Series(data).ewm(span=fast_period, adjust=False).mean()
        ema_slow = pd.Series(data).ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line.values, signal_line.values, histogram.values
    
    @staticmethod
    def bollinger_bands(data, period=20, std_dev=2):
        """
        Bollinger Bands számítása
        
        Args:
            data (array-like): Adatok
            period (int): Periódus
            std_dev (float): Standard deviáció szorzó
            
        Returns:
            tuple: (Upper Band, Middle Band, Lower Band)
        """
        middle_band = pd.Series(data).rolling(window=period).mean()
        std = pd.Series(data).rolling(window=period).std()
        
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band.values, middle_band.values, lower_band.values
    
    @staticmethod
    def atr(high, low, close, period=14):
        """
        Average True Range (ATR) számítása
        
        Args:
            high (array-like): Magas árak
            low (array-like): Alacsony árak
            close (array-like): Záró árak
            period (int): Periódus
            
        Returns:
            array-like: ATR értékek
        """
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.values
    
    @staticmethod
    def stochastic(high, low, close, k_period=14, d_period=3):
        """
        Stochastic Oscillator számítása
        
        Args:
            high (array-like): Magas árak
            low (array-like): Alacsony árak
            close (array-like): Záró árak
            k_period (int): %K periódus
            d_period (int): %D periódus
            
        Returns:
            tuple: (%K, %D)
        """
        high_roll = pd.Series(high).rolling(window=k_period)
        low_roll = pd.Series(low).rolling(window=k_period)
        
        highest_high = high_roll.max()
        lowest_low = low_roll.min()
        
        k = 100 * (pd.Series(close) - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()
        
        return k.values, d.values
    
    @staticmethod
    def adx(high, low, close, period=14):
        """
        Average Directional Index (ADX) számítása
        
        Args:
            high (array-like): Magas árak
            low (array-like): Alacsony árak
            close (array-like): Záró árak
            period (int): Periódus
            
        Returns:
            tuple: (ADX, +DI, -DI)
        """
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        # True Range
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Smoothed Directional Movement and True Range
        tr_smooth = pd.Series(tr).rolling(window=period).sum()
        plus_dm_smooth = pd.Series(plus_dm).rolling(window=period).sum()
        minus_dm_smooth = pd.Series(minus_dm).rolling(window=period).sum()
        
        # Directional Indicators
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        # Directional Index
        dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di))
        
        # Average Directional Index
        adx = pd.Series(dx).rolling(window=period).mean()
        
        return adx.values, plus_di.values, minus_di.values
    
    @staticmethod
    def ichimoku(high, low, close, tenkan_period=9, kijun_period=26, senkou_b_period=52, displacement=26):
        """
        Ichimoku Cloud számítása
        
        Args:
            high (array-like): Magas árak
            low (array-like): Alacsony árak
            close (array-like): Záró árak
            tenkan_period (int): Tenkan-sen periódus
            kijun_period (int): Kijun-sen periódus
            senkou_b_period (int): Senkou Span B periódus
            displacement (int): Eltolás
            
        Returns:
            tuple: (Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, Chikou Span)
        """
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        # Tenkan-sen (Conversion Line)
        tenkan_high = high.rolling(window=tenkan_period).max()
        tenkan_low = low.rolling(window=tenkan_period).min()
        tenkan_sen = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line)
        kijun_high = high.rolling(window=kijun_period).max()
        kijun_low = low.rolling(window=kijun_period).min()
        kijun_sen = (kijun_high + kijun_low) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
        
        # Senkou Span B (Leading Span B)
        senkou_high = high.rolling(window=senkou_b_period).max()
        senkou_low = low.rolling(window=senkou_b_period).min()
        senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)
        
        # Chikou Span (Lagging Span)
        chikou_span = close.shift(-displacement)
        
        return tenkan_sen.values, kijun_sen.values, senkou_span_a.values, senkou_span_b.values, chikou_span.values
    
    @staticmethod
    def fibonacci_retracement(high, low):
        """
        Fibonacci Retracement szintek számítása
        
        Args:
            high (float): Legmagasabb ár
            low (float): Legalacsonyabb ár
            
        Returns:
            dict: Fibonacci szintek
        """
        diff = high - low
        
        return {
            '0.0': low,
            '0.236': low + 0.236 * diff,
            '0.382': low + 0.382 * diff,
            '0.5': low + 0.5 * diff,
            '0.618': low + 0.618 * diff,
            '0.786': low + 0.786 * diff,
            '1.0': high
        }
    
    @staticmethod
    def pivot_points(high, low, close, method='standard'):
        """
        Pivot Points számítása
        
        Args:
            high (float): Előző időszak legmagasabb ára
            low (float): Előző időszak legalacsonyabb ára
            close (float): Előző időszak záró ára
            method (str): Számítási módszer (standard, fibonacci, camarilla, woodie)
            
        Returns:
            dict: Pivot pontok
        """
        if method == 'standard':
            pivot = (high + low + close) / 3
            s1 = (2 * pivot) - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)
            r1 = (2 * pivot) - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)
            
            return {
                'pivot': pivot,
                's1': s1,
                's2': s2,
                's3': s3,
                'r1': r1,
                'r2': r2,
                'r3': r3
            }
        
        elif method == 'fibonacci':
            pivot = (high + low + close) / 3
            s1 = pivot - 0.382 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            s3 = pivot - 1.0 * (high - low)
            r1 = pivot + 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
            r3 = pivot + 1.0 * (high - low)
            
            return {
                'pivot': pivot,
                's1': s1,
                's2': s2,
                's3': s3,
                'r1': r1,
                'r2': r2,
                'r3': r3
            }
        
        elif method == 'camarilla':
            pivot = (high + low + close) / 3
            s1 = close - 1.1 * (high - low) / 12
            s2 = close - 1.1 * (high - low) / 6
            s3 = close - 1.1 * (high - low) / 4
            s4 = close - 1.1 * (high - low) / 2
            r1 = close + 1.1 * (high - low) / 12
            r2 = close + 1.1 * (high - low) / 6
            r3 = close + 1.1 * (high - low) / 4
            r4 = close + 1.1 * (high - low) / 2
            
            return {
                'pivot': pivot,
                's1': s1,
                's2': s2,
                's3': s3,
                's4': s4,
                'r1': r1,
                'r2': r2,
                'r3': r3,
                'r4': r4
            }
        
        elif method == 'woodie':
            pivot = (high + low + 2 * close) / 4
            s1 = (2 * pivot) - high
            s2 = pivot - (high - low)
            s3 = s1 - (high - low)
            s4 = s3 - (high - low)
            r1 = (2 * pivot) - low
            r2 = pivot + (high - low)
            r3 = r1 + (high - low)
            r4 = r3 + (high - low)
            
            return {
                'pivot': pivot,
                's1': s1,
                's2': s2,
                's3': s3,
                's4': s4,
                'r1': r1,
                'r2': r2,
                'r3': r3,
                'r4': r4
            }
        
        else:
            raise ValueError(f"Nem támogatott számítási módszer: {method}")
