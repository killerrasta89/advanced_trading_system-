"""
Binance Connector - Kezeli a Binance tőzsdével való kommunikációt.
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('binance_connector')

class BinanceConnector:
    """
    Kezeli a Binance tőzsdével való kommunikációt.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a BinanceConnector-t a megadott konfigurációval.
        
        Args:
            config: A Binance kapcsolat konfigurációja
        """
        self.config = config
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.is_testnet = config.get('testnet', False)
        self.rate_limit_per_second = config.get('rate_limit_per_second', 10)
        self.last_request_time = 0
        
        # Raspberry Pi optimalizáció: csökkentett rate limit
        if config.get('rpi_optimization', True):
            self.rate_limit_per_second = min(self.rate_limit_per_second, 5)
        
        logger.info("BinanceConnector initialized")
    
    def _respect_rate_limit(self) -> None:
        """
        Betartja a rate limitet a kérések között.
        """
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit_per_second
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def get_ticker(self, symbol: str) -> Optional[Dict]:
        """
        Lekérdezi egy adott szimbólum ticker adatait.
        
        Args:
            symbol: A szimbólum (pl. BTC/USDT)
            
        Returns:
            Optional[Dict]: A ticker adatok, vagy None hiba esetén
        """
        try:
            self._respect_rate_limit()
            
            # Valós implementációban itt lenne a Binance API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Binance formátumra
            binance_symbol = symbol.replace('/', '')
            
            # Példa ticker adatok
            ticker = {
                'symbol': binance_symbol,
                'price': 40000.0 if 'BTC' in symbol else (2000.0 if 'ETH' in symbol else 0.5),
                'volume': 1000000.0,
                'timestamp': datetime.now().timestamp() * 1000
            }
            
            logger.debug(f"Got ticker for {symbol}: {ticker}")
            return ticker
        
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {str(e)}")
            return None
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> Optional[Dict]:
        """
        Lekérdezi egy adott szimbólum orderbook adatait.
        
        Args:
            symbol: A szimbólum (pl. BTC/USDT)
            limit: A visszaadandó árszintek maximális száma
            
        Returns:
            Optional[Dict]: Az orderbook adatok, vagy None hiba esetén
        """
        try:
            self._respect_rate_limit()
            
            # Valós implementációban itt lenne a Binance API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Binance formátumra
            binance_symbol = symbol.replace('/', '')
            
            # Példa ár az orderbook generálásához
            base_price = 40000.0 if 'BTC' in symbol else (2000.0 if 'ETH' in symbol else 0.5)
            
            # Példa orderbook adatok
            orderbook = {
                'symbol': binance_symbol,
                'bids': [[base_price * (1 - 0.001 * i), 1.0 / (i + 1)] for i in range(limit)],
                'asks': [[base_price * (1 + 0.001 * i), 1.0 / (i + 1)] for i in range(limit)],
                'timestamp': datetime.now().timestamp() * 1000
            }
            
            logger.debug(f"Got orderbook for {symbol}")
            return orderbook
        
        except Exception as e:
            logger.error(f"Error getting orderbook for {symbol}: {str(e)}")
            return None
    
    def get_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> Optional[List]:
        """
        Lekérdezi egy adott szimbólum OHLCV adatait.
        
        Args:
            symbol: A szimbólum (pl. BTC/USDT)
            timeframe: Az időkeret (pl. 1m, 5m, 15m, 1h, 4h, 1d)
            limit: A visszaadandó gyertyák maximális száma
            
        Returns:
            Optional[List]: Az OHLCV adatok, vagy None hiba esetén
        """
        try:
            self._respect_rate_limit()
            
            # Valós implementációban itt lenne a Binance API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Binance formátumra
            binance_symbol = symbol.replace('/', '')
            
            # Példa ár az OHLCV generálásához
            base_price = 40000.0 if 'BTC' in symbol else (2000.0 if 'ETH' in symbol else 0.5)
            
            # Időkeret konvertálása milliszekundumra
            timeframe_ms = {
                '1m': 60 * 1000,
                '5m': 5 * 60 * 1000,
                '15m': 15 * 60 * 1000,
                '1h': 60 * 60 * 1000,
                '4h': 4 * 60 * 60 * 1000,
                '1d': 24 * 60 * 60 * 1000
            }.get(timeframe, 60 * 1000)
            
            # Példa OHLCV adatok
            current_time = int(datetime.now().timestamp() * 1000)
            ohlcv = []
            
            for i in range(limit):
                timestamp = current_time - (limit - i) * timeframe_ms
                price_factor = 1 + 0.1 * (i / limit) * (1 if i % 2 == 0 else -1)
                
                candle = [
                    timestamp,  # timestamp
                    base_price * price_factor * 0.99,  # open
                    base_price * price_factor * 1.02,  # high
                    base_price * price_factor * 0.98,  # low
                    base_price * price_factor,  # close
                    1000.0 + i * 10  # volume
                ]
                ohlcv.append(candle)
            
            logger.debug(f"Got OHLCV for {symbol}, timeframe {timeframe}")
            return ohlcv
        
        except Exception as e:
            logger.error(f"Error getting OHLCV for {symbol}, timeframe {timeframe}: {str(e)}")
            return None
    
    def get_balance(self) -> Optional[Dict]:
        """
        Lekérdezi a számla egyenlegét.
        
        Returns:
            Optional[Dict]: Az egyenleg adatok, vagy None hiba esetén
        """
        try:
            self._respect_rate_limit()
            
            # Valós implementációban itt lenne a Binance API hívás
            # Most csak példa adatokat adunk vissza
            
            # Példa egyenleg adatok
            balance = {
                'BTC': {'free': 0.5, 'used': 0.1, 'total': 0.6},
                'ETH': {'free': 5.0, 'used': 1.0, 'total': 6.0},
                'ADA': {'free': 1000.0, 'used': 0.0, 'total': 1000.0},
                'USDT': {'free': 10000.0, 'used': 5000.0, 'total': 15000.0}
            }
            
            logger.debug("Got balance")
            return balance
        
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            return None
    
    def execute_order(self, order) -> Optional[Dict]:
        """
        Végrehajtja a megbízást.
        
        Args:
            order: A megbízás
            
        Returns:
            Optional[Dict]: A végrehajtási eredmény, vagy None hiba esetén
        """
        try:
            self._respect_rate_limit()
            
            # Valós implementációban itt lenne a Binance API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Binance formátumra
            binance_symbol = order.symbol.replace('/', '')
            
            # Példa végrehajtási eredmény
            execution_result = {
                'symbol': order.symbol,
                'order_id': f"binance_{int(time.time() * 1000)}",
                'client_order_id': f"client_{int(time.time() * 1000)}",
                'side': order.side,
                'type': order.order_type,
                'price': order.price if order.price else (40000.0 if 'BTC' in order.symbol else (2000.0 if 'ETH' in order.symbol else 0.5)),
                'amount': order.amount,
                'filled_amount': order.amount,
                'average_price': order.price if order.price else (40000.0 if 'BTC' in order.symbol else (2000.0 if 'ETH' in order.symbol else 0.5)),
                'status': 'filled',
                'timestamp': datetime.now().timestamp() * 1000
            }
            
            # Beállítja az exchange ID-t az order objektumban
            order.id = execution_result['order_id']
            order.exchange_id = 'binance'
            order.status = 'filled'
            order.executed_at = datetime.now()
            order.filled_amount = order.amount
            order.average_price = execution_result['average_price']
            
            logger.info(f"Executed order: {order.to_dict()}")
            return execution_result
        
        except Exception as e:
            logger.error(f"Error executing order: {str(e)}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Visszavon egy megbízást.
        
        Args:
            order_id: A megbízás azonosítója
            
        Returns:
            bool: Sikeres visszavonás esetén True, egyébként False
        """
        try:
            self._respect_rate_limit()
            
            # Valós implementációban itt lenne a Binance API hívás
            # Most csak példa adatokat adunk vissza
            
            logger.info(f"Canceled order: {order_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error canceling order {order_id}: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Lekérdezi egy megbízás állapotát.
        
        Args:
            order_id: A megbízás azonosítója
            
        Returns:
            Optional[Dict]: A megbízás állapota, vagy None hiba esetén
        """
        try:
            self._respect_rate_limit()
            
            # Valós implementációban itt lenne a Binance API hívás
            # Most csak példa adatokat adunk vissza
            
            # Példa megbízás állapot
            order_status = {
                'order_id': order_id,
                'symbol': 'BTCUSDT',
                'side': 'buy',
                'type': 'limit',
                'price': 40000.0,
                'amount': 0.1,
                'filled_amount': 0.1,
                'average_price': 40000.0,
                'status': 'filled',
                'timestamp': datetime.now().timestamp() * 1000
            }
            
            logger.debug(f"Got order status for {order_id}")
            return order_status
        
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {str(e)}")
            return None
