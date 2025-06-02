"""
Exchange Factory - Létrehoz és kezel különböző tőzsde kapcsolatokat.
"""
import logging
from typing import Dict, Optional

from src.exchanges.binance_connector import BinanceConnector
from src.exchanges.kraken_connector import KrakenConnector
from src.exchanges.coinbase_connector import CoinbaseConnector
from src.utils.logger import setup_logger

logger = setup_logger('exchange_factory')

class ExchangeFactory:
    """
    Factory osztály a különböző tőzsde kapcsolatok létrehozásához.
    """
    
    def __init__(self):
        """
        Inicializálja az ExchangeFactory-t.
        """
        logger.info("ExchangeFactory initialized")
    
    def create_exchange(self, exchange_type: str, config: Dict) -> Optional:
        """
        Létrehoz egy tőzsde kapcsolatot a megadott típus és konfiguráció alapján.
        
        Args:
            exchange_type: A tőzsde típusa (pl. binance, kraken, coinbase)
            config: A tőzsde konfigurációja
            
        Returns:
            Optional: A létrehozott tőzsde kapcsolat, vagy None hiba esetén
        """
        try:
            exchange_type = exchange_type.lower()
            
            if exchange_type == 'binance':
                return BinanceConnector(config)
            elif exchange_type == 'kraken':
                return KrakenConnector(config)
            elif exchange_type == 'coinbase':
                return CoinbaseConnector(config)
            else:
                logger.warning(f"Unsupported exchange type: {exchange_type}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating exchange {exchange_type}: {str(e)}")
            return None
