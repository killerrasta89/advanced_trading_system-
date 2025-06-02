"""
Market Data Manager - Kezeli a piaci adatok lekérdezését és tárolását.
"""
import logging
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.utils.logger import setup_logger

logger = setup_logger('market_data_manager')

class MarketDataManager:
    """
    Kezeli a piaci adatok lekérdezését, tárolását és hozzáférését.
    Biztosítja a friss árfolyam és egyéb piaci adatokat a kereskedési rendszer számára.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a MarketDataManager-t a megadott konfigurációval.
        
        Args:
            config: A MarketDataManager konfigurációja
        """
        self.config = config
        self.is_running = False
        self.data_thread = None
        self.market_data = {}  # Szimbólum -> adatok
        
        # Konfigurációs beállítások
        self.update_interval = config.get('update_interval', 10)  # másodperc
        self.symbols = config.get('symbols', ['BTC/USDT', 'ETH/USDT', 'ADA/USDT'])
        self.timeframes = config.get('timeframes', ['1m', '5m', '15m', '1h', '4h', '1d'])
        self.max_candles = config.get('max_candles', 1000)  # Maximális gyertyák száma timeframe-enként
        self.exchanges = config.get('exchanges', ['binance'])
        
        logger.info("MarketDataManager initialized")
    
    def start(self) -> bool:
        """
        Elindítja a MarketDataManager-t és a piaci adatok frissítését.
        
        Returns:
            bool: Sikeres indítás esetén True, egyébként False
        """
        if self.is_running:
            logger.warning("MarketDataManager is already running")
            return False
        
        try:
            self.is_running = True
            
            # Inicializálja a piaci adatokat
            self._initialize_market_data()
            
            # Elindítja az adatfrissítési szálat
            self.data_thread = threading.Thread(target=self._data_update_loop)
            self.data_thread.daemon = True
            self.data_thread.start()
            
            logger.info("MarketDataManager started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start MarketDataManager: {str(e)}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Leállítja a MarketDataManager-t.
        
        Returns:
            bool: Sikeres leállítás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("MarketDataManager is not running")
            return False
        
        try:
            self.is_running = False
            
            if self.data_thread and self.data_thread.is_alive():
                self.data_thread.join(timeout=10)
            
            logger.info("MarketDataManager stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping MarketDataManager: {str(e)}")
            return False
    
    def _initialize_market_data(self) -> None:
        """
        Inicializálja a piaci adatokat minden szimbólumra és időkeretre.
        """
        try:
            for symbol in self.symbols:
                self.market_data[symbol] = {
                    'ticker': {
                        'last': 0.0,
                        'bid': 0.0,
                        'ask': 0.0,
                        'volume': 0.0,
                        'timestamp': None
                    },
                    'ohlcv': {timeframe: [] for timeframe in self.timeframes},
                    'orderbook': {
                        'bids': [],
                        'asks': [],
                        'timestamp': None
                    }
                }
            
            # Kezdeti adatok lekérdezése
            self._update_market_data()
            
            logger.info("Market data initialized")
        
        except Exception as e:
            logger.error(f"Error initializing market data: {str(e)}")
    
    def _data_update_loop(self) -> None:
        """
        Periodikusan frissíti a piaci adatokat.
        """
        logger.info("Market data update loop started")
        
        while self.is_running:
            try:
                start_time = time.time()
                
                # Frissíti a piaci adatokat
                self._update_market_data()
                
                # Kiszámítja a várakozási időt
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            except Exception as e:
                logger.error(f"Error in market data update loop: {str(e)}")
                time.sleep(self.update_interval)
        
        logger.info("Market data update loop stopped")
    
    def _update_market_data(self) -> None:
        """
        Frissíti a piaci adatokat minden szimbólumra és időkeretre.
        """
        try:
            # Valós implementációban itt lekérdeznénk az adatokat az exchange API-ból
            # Most csak példa adatokat generálunk
            
            current_time = datetime.now()
            
            for symbol in self.symbols:
                # Ticker adatok frissítése
                if symbol == 'BTC/USDT':
                    last_price = 40000.0 + (current_time.second / 60.0) * 1000.0  # Példa áringadozás
                elif symbol == 'ETH/USDT':
                    last_price = 2000.0 + (current_time.second / 60.0) * 50.0
                else:  # ADA/USDT
                    last_price = 0.5 + (current_time.second / 60.0) * 0.05
                
                self.market_data[symbol]['ticker'] = {
                    'last': last_price,
                    'bid': last_price * 0.999,
                    'ask': last_price * 1.001,
                    'volume': 1000000.0 + (current_time.minute * 10000.0),
                    'timestamp': current_time
                }
                
                # OHLCV adatok frissítése (csak az 1m időkeretre, a többit ebből számolnánk)
                if len(self.market_data[symbol]['ohlcv']['1m']) == 0:
                    # Inicializálás, ha még nincs adat
                    for i in range(100):
                        candle_time = current_time - timedelta(minutes=100-i)
                        base_price = last_price * (0.9 + 0.2 * (i / 100.0))
                        
                        candle = {
                            'timestamp': candle_time,
                            'open': base_price * 0.99,
                            'high': base_price * 1.02,
                            'low': base_price * 0.98,
                            'close': base_price,
                            'volume': 100000.0 + (i * 1000.0)
                        }
                        self.market_data[symbol]['ohlcv']['1m'].append(candle)
                else:
                    # Új gyertya hozzáadása
                    last_candle = self.market_data[symbol]['ohlcv']['1m'][-1]
                    
                    # Ha új perc kezdődött, új gyertyát adunk hozzá
                    if current_time.minute != last_candle['timestamp'].minute:
                        new_candle = {
                            'timestamp': current_time.replace(second=0, microsecond=0),
                            'open': last_candle['close'],
                            'high': max(last_candle['close'], last_price),
                            'low': min(last_candle['close'], last_price),
                            'close': last_price,
                            'volume': 10000.0 + (current_time.second * 100.0)
                        }
                        self.market_data[symbol]['ohlcv']['1m'].append(new_candle)
                        
                        # Korlátozza a gyertyák számát
                        if len(self.market_data[symbol]['ohlcv']['1m']) > self.max_candles:
                            self.market_data[symbol]['ohlcv']['1m'] = self.market_data[symbol]['ohlcv']['1m'][-self.max_candles:]
                    else:
                        # Frissíti az aktuális gyertyát
                        last_candle['high'] = max(last_candle['high'], last_price)
                        last_candle['low'] = min(last_candle['low'], last_price)
                        last_candle['close'] = last_price
                        last_candle['volume'] += 100.0
                
                # Orderbook adatok frissítése
                self.market_data[symbol]['orderbook'] = {
                    'bids': [
                        [last_price * 0.999, 2.0],
                        [last_price * 0.998, 5.0],
                        [last_price * 0.997, 10.0],
                        [last_price * 0.996, 15.0],
                        [last_price * 0.995, 20.0]
                    ],
                    'asks': [
                        [last_price * 1.001, 2.0],
                        [last_price * 1.002, 5.0],
                        [last_price * 1.003, 10.0],
                        [last_price * 1.004, 15.0],
                        [last_price * 1.005, 20.0]
                    ],
                    'timestamp': current_time
                }
            
            logger.debug("Market data updated")
        
        except Exception as e:
            logger.error(f"Error updating market data: {str(e)}")
    
    def get_latest_data(self) -> Dict:
        """
        Visszaadja a legfrissebb piaci adatokat minden szimbólumra.
        
        Returns:
            Dict: A legfrissebb piaci adatok
        """
        return self.market_data
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Visszaadja egy adott szimbólum ticker adatait.
        
        Args:
            symbol: A szimbólum (pl. BTC/USDT)
            
        Returns:
            Optional[Dict]: A ticker adatok, vagy None ha a szimbólum nem található
        """
        if symbol in self.market_data:
            return self.market_data[symbol]['ticker']
        return None
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> Optional[List]:
        """
        Visszaadja egy adott szimbólum OHLCV adatait.
        
        Args:
            symbol: A szimbólum (pl. BTC/USDT)
            timeframe: Az időkeret (pl. 1m, 5m, 15m, 1h, 4h, 1d)
            limit: A visszaadandó gyertyák maximális száma
            
        Returns:
            Optional[List]: Az OHLCV adatok, vagy None ha a szimbólum vagy időkeret nem található
        """
        if symbol in self.market_data and timeframe in self.market_data[symbol]['ohlcv']:
            return self.market_data[symbol]['ohlcv'][timeframe][-limit:]
        return None
    
    def get_orderbook(self, symbol: str) -> Optional[Dict]:
        """
        Visszaadja egy adott szimbólum orderbook adatait.
        
        Args:
            symbol: A szimbólum (pl. BTC/USDT)
            
        Returns:
            Optional[Dict]: Az orderbook adatok, vagy None ha a szimbólum nem található
        """
        if symbol in self.market_data:
            return self.market_data[symbol]['orderbook']
        return None
    
    def get_status(self) -> Dict:
        """
        Visszaadja a MarketDataManager állapotát.
        
        Returns:
            Dict: A MarketDataManager állapota
        """
        return {
            "is_running": self.is_running,
            "symbols_count": len(self.symbols),
            "timeframes": self.timeframes,
            "update_interval": self.update_interval
        }
