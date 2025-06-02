"""
Execution Engine - Végrehajtja a kereskedési megbízásokat a különböző tőzsdéken.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger
from src.exchanges.exchange_factory import ExchangeFactory

logger = setup_logger('execution_engine')

class ExecutionEngine:
    """
    Végrehajtja a kereskedési megbízásokat a különböző tőzsdéken.
    Kezeli a megbízások küldését, nyomon követését és a végrehajtási eredmények visszaadását.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja az ExecutionEngine-t a megadott konfigurációval.
        
        Args:
            config: Az ExecutionEngine konfigurációja
        """
        self.config = config
        self.is_running = False
        self.exchange_factory = ExchangeFactory()
        self.exchanges = {}  # Exchange név -> Exchange objektum
        
        # Konfigurációs beállítások
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1.0)  # másodperc
        
        logger.info("ExecutionEngine initialized")
    
    def start(self) -> bool:
        """
        Elindítja az ExecutionEngine-t.
        
        Returns:
            bool: Sikeres indítás esetén True, egyébként False
        """
        if self.is_running:
            logger.warning("ExecutionEngine is already running")
            return False
        
        try:
            self.is_running = True
            self._initialize_exchanges()
            logger.info("ExecutionEngine started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start ExecutionEngine: {str(e)}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Leállítja az ExecutionEngine-t.
        
        Returns:
            bool: Sikeres leállítás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("ExecutionEngine is not running")
            return False
        
        try:
            self.is_running = False
            logger.info("ExecutionEngine stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping ExecutionEngine: {str(e)}")
            return False
    
    def _initialize_exchanges(self) -> None:
        """
        Inicializálja a konfigurált tőzsdéket.
        """
        try:
            # Valós implementációban itt betöltenénk a tőzsdéket az adatbázisból
            # Most csak példa tőzsdéket hozunk létre
            
            exchange_configs = self.config.get('exchanges', [
                {"name": "binance", "api_key": "demo_key", "api_secret": "demo_secret"},
                {"name": "kraken", "api_key": "demo_key", "api_secret": "demo_secret"},
                {"name": "coinbase", "api_key": "demo_key", "api_secret": "demo_secret"}
            ])
            
            for exchange_config in exchange_configs:
                exchange_name = exchange_config.get('name')
                if not exchange_name:
                    continue
                
                exchange = self.exchange_factory.create_exchange(exchange_name, exchange_config)
                if exchange:
                    self.exchanges[exchange_name] = exchange
                    logger.info(f"Initialized exchange: {exchange_name}")
            
            logger.info(f"Initialized {len(self.exchanges)} exchanges")
        
        except Exception as e:
            logger.error(f"Error initializing exchanges: {str(e)}")
            self.exchanges = {}
    
    def execute_orders(self, orders: List) -> List[Dict]:
        """
        Végrehajtja a megbízásokat a megfelelő tőzsdéken.
        
        Args:
            orders: A végrehajtandó megbízások listája
            
        Returns:
            List[Dict]: A végrehajtási eredmények listája
        """
        if not self.is_running:
            logger.warning("ExecutionEngine is not running, cannot execute orders")
            return []
        
        execution_results = []
        
        try:
            for order in orders:
                # Meghatározza a megfelelő tőzsdét
                exchange_name = self._determine_exchange_for_order(order)
                if not exchange_name or exchange_name not in self.exchanges:
                    logger.warning(f"No suitable exchange found for order: {order.to_dict()}")
                    continue
                
                exchange = self.exchanges[exchange_name]
                
                # Végrehajtja a megbízást
                result = self._execute_order_with_retry(exchange, order)
                if result:
                    execution_results.append(result)
            
            logger.info(f"Executed {len(execution_results)} orders")
            return execution_results
        
        except Exception as e:
            logger.error(f"Error executing orders: {str(e)}")
            return execution_results
    
    def _determine_exchange_for_order(self, order) -> Optional[str]:
        """
        Meghatározza a megfelelő tőzsdét egy adott megbízáshoz.
        
        Args:
            order: A megbízás
            
        Returns:
            Optional[str]: A tőzsde neve, vagy None ha nem található megfelelő tőzsde
        """
        # Valós implementációban itt lenne a tőzsde kiválasztási logika
        # Most egyszerűen a Binance-t használjuk minden megbízáshoz
        return "binance" if "binance" in self.exchanges else None
    
    def _execute_order_with_retry(self, exchange, order) -> Optional[Dict]:
        """
        Végrehajtja a megbízást újrapróbálkozással hiba esetén.
        
        Args:
            exchange: A tőzsde objektum
            order: A megbízás
            
        Returns:
            Optional[Dict]: A végrehajtási eredmény, vagy None hiba esetén
        """
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Végrehajtja a megbízást
                result = exchange.execute_order(order)
                
                if result:
                    logger.info(f"Order executed successfully: {order.to_dict()}")
                    return result
                
                logger.warning(f"Failed to execute order, retrying: {order.to_dict()}")
                retries += 1
                
                # Vár a következő próbálkozás előtt
                import time
                time.sleep(self.retry_delay)
            
            except Exception as e:
                logger.error(f"Error executing order: {str(e)}")
                retries += 1
                
                # Vár a következő próbálkozás előtt
                import time
                time.sleep(self.retry_delay)
        
        logger.error(f"Failed to execute order after {self.max_retries} retries: {order.to_dict()}")
        return None
    
    def cancel_order(self, order_id: str, exchange_name: str) -> bool:
        """
        Visszavon egy megbízást.
        
        Args:
            order_id: A megbízás azonosítója
            exchange_name: A tőzsde neve
            
        Returns:
            bool: Sikeres visszavonás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("ExecutionEngine is not running, cannot cancel order")
            return False
        
        try:
            if exchange_name not in self.exchanges:
                logger.warning(f"Exchange {exchange_name} not found")
                return False
            
            exchange = self.exchanges[exchange_name]
            result = exchange.cancel_order(order_id)
            
            if result:
                logger.info(f"Order {order_id} canceled successfully")
                return True
            
            logger.warning(f"Failed to cancel order {order_id}")
            return False
        
        except Exception as e:
            logger.error(f"Error canceling order: {str(e)}")
            return False
    
    def get_order_status(self, order_id: str, exchange_name: str) -> Optional[Dict]:
        """
        Lekérdezi egy megbízás állapotát.
        
        Args:
            order_id: A megbízás azonosítója
            exchange_name: A tőzsde neve
            
        Returns:
            Optional[Dict]: A megbízás állapota, vagy None hiba esetén
        """
        if not self.is_running:
            logger.warning("ExecutionEngine is not running, cannot get order status")
            return None
        
        try:
            if exchange_name not in self.exchanges:
                logger.warning(f"Exchange {exchange_name} not found")
                return None
            
            exchange = self.exchanges[exchange_name]
            return exchange.get_order_status(order_id)
        
        except Exception as e:
            logger.error(f"Error getting order status: {str(e)}")
            return None
    
    def get_status(self) -> Dict:
        """
        Visszaadja az ExecutionEngine állapotát.
        
        Returns:
            Dict: Az ExecutionEngine állapota
        """
        return {
            "is_running": self.is_running,
            "exchanges": list(self.exchanges.keys()),
            "max_retries": self.max_retries
        }
