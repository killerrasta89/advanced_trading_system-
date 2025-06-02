"""
Kraken Connector - Kezeli a Kraken tőzsdével való kommunikációt.
"""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('kraken_connector')

class KrakenConnector:
    """
    Kezeli a Kraken tőzsdével való kommunikációt.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a KrakenConnector-t a megadott konfigurációval.
        
        Args:
            config: A Kraken kapcsolat konfigurációja
        """
        self.config = config
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.rate_limit_per_second = config.get('rate_limit_per_second', 5)
        self.last_request_time = 0
        
        # Raspberry Pi optimalizáció: csökkentett rate limit
        if config.get('rpi_optimization', True):
            self.rate_limit_per_second = min(self.rate_limit_per_second, 3)
        
        logger.info("KrakenConnector initialized")
    
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
    
    def _convert_symbol_format(self, symbol: str) -> str:
        """
        Konvertálja a szimbólum formátumot Kraken formátumra.
        
        Args:
            symbol: A szimbólum (pl. BTC/USDT)
            
        Returns:
            str: A Kraken formátumú szimbólum
        """
        # Kraken speciális formátumot használ
        if '/' in symbol:
            base, quote = symbol.split('/')
            if quote == 'USDT':
                quote = 'USD'  # Kraken USD-t használ USDT helyett
            return f"X{base}Z{quote}"
        return symbol
    
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
            
            # Valós implementációban itt lenne a Kraken API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Kraken formátumra
            kraken_symbol = self._convert_symbol_format(symbol)
            
            # Példa ticker adatok
            ticker = {
                'symbol': kraken_symbol,
                'price': 39800.0 if 'BTC' in symbol else (1980.0 if 'ETH' in symbol else 0.48),
                'volume': 900000.0,
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
            
            # Valós implementációban itt lenne a Kraken API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Kraken formátumra
            kraken_symbol = self._convert_symbol_format(symbol)
            
            # Példa ár az orderbook generálásához
            base_price = 39800.0 if 'BTC' in symbol else (1980.0 if 'ETH' in symbol else 0.48)
            
            # Példa orderbook adatok
            orderbook = {
                'symbol': kraken_symbol,
                'bids': [[base_price * (1 - 0.001 * i), 0.8 / (i + 1)] for i in range(limit)],
                'asks': [[base_price * (1 + 0.001 * i), 0.8 / (i + 1)] for i in range(limit)],
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
            
            # Valós implementációban itt lenne a Kraken API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Kraken formátumra
            kraken_symbol = self._convert_symbol_format(symbol)
            
            # Példa ár az OHLCV generálásához
            base_price = 39800.0 if 'BTC' in symbol else (1980.0 if 'ETH' in symbol else 0.48)
            
            # Időkeret konvertálása másodpercre (Kraken másodpercben adja meg)
            timeframe_sec = {
                '1m': 60,
                '5m': 5 * 60,
                '15m': 15 * 60,
                '1h': 60 * 60,
                '4h': 4 * 60 * 60,
                '1d': 24 * 60 * 60
            }.get(timeframe, 60)
            
            # Példa OHLCV adatok
            current_time = int(datetime.now().timestamp())
            ohlcv = []
            
            for i in range(limit):
                timestamp = current_time - (limit - i) * timeframe_sec
                price_factor = 1 + 0.08 * (i / limit) * (1 if i % 2 == 0 else -1)
                
                candle = [
                    timestamp,  # timestamp
                    base_price * price_factor * 0.99,  # open
                    base_price * price_factor * 1.01,  # high
                    base_price * price_factor * 0.98,  # low
                    base_price * price_factor,  # close
                    900.0 + i * 8  # volume
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
            
            # Valós implementációban itt lenne a Kraken API hívás
            # Most csak példa adatokat adunk vissza
            
            # Példa egyenleg adatok
            balance = {
                'XXBT': {'free': 0.4, 'used': 0.05, 'total': 0.45},  # BTC Kraken formátumban
                'XETH': {'free': 4.0, 'used': 0.5, 'total': 4.5},    # ETH Kraken formátumban
                'ADA': {'free': 800.0, 'used': 0.0, 'total': 800.0},
                'ZUSD': {'free': 8000.0, 'used': 4000.0, 'total': 12000.0}  # USD Kraken formátumban
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
            
            # Valós implementációban itt lenne a Kraken API hívás
            # Most csak példa adatokat adunk vissza
            
            # Szimbólum formátum konvertálása Kraken formátumra
            kraken_symbol = self._convert_symbol_format(order.symbol)
            
            # Példa végrehajtási eredmény
            execution_result = {
                'symbol': order.symbol,
                'order_id': f"kraken_{int(time.time() * 1000)}",
                'client_order_id': f"client_{int(time.time() * 1000)}",
                'side': order.side,
                'type': order.order_type,
                'price': order.price if order.price else (39800.0 if 'BTC' in order.symbol else (1980.0 if 'ETH' in order.symbol else 0.48)),
                'amount': order.amount,
                'filled_amount': order.amount,
                'average_price': order.price if order.price else (39800.0 if 'BTC' in order.symbol else (1980.0 if 'ETH' in order.symbol else 0.48)),
                'status': 'filled',
                'timestamp': datetime.now().timestamp() * 1000
            }
            
            # Beállítja az exchange ID-t az order objektumban
            order.id = execution_result['order_id']
            order.exchange_id = 'kraken'
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
            
            # Valós implementációban itt lenne a Kraken API hívás
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
            
            # Valós implementációban itt lenne a Kraken API hívás
            # Most csak példa adatokat adunk vissza
            
            # Példa megbízás állapot
            order_status = {
                'order_id': order_id,
                'symbol': 'XXBTZUSD',  # BTC/USD Kraken formátumban
                'side': 'buy',
                'type': 'limit',
                'price': 39800.0,
                'amount': 0.1,
                'filled_amount': 0.1,
                'average_price': 39800.0,
                'status': 'filled',
                'timestamp': datetime.now().timestamp() * 1000
            }
            
            logger.debug(f"Got order status for {order_id}")
            return order_status
        
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {str(e)}")
            return None
