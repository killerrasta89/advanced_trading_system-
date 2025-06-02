"""
Sentiment Analyzer - Elemzi a piaci hangulatot különböző forrásokból.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import re
import random  # Csak a példa implementációhoz

from src.utils.logger import setup_logger

logger = setup_logger('sentiment_analyzer')

class SentimentAnalyzer:
    """
    Elemzi a piaci hangulatot különböző forrásokból, mint hírek, közösségi média és piaci adatok.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a SentimentAnalyzer-t a megadott konfigurációval.
        
        Args:
            config: A SentimentAnalyzer konfigurációja
        """
        self.config = config
        self.is_running = False
        self.last_update_time = None
        
        # Konfigurációs beállítások
        self.update_interval = config.get('update_interval', 3600)  # másodperc
        self.sources = config.get('sources', ['news', 'social_media', 'market_data'])
        self.symbols = config.get('symbols', ['BTC', 'ETH', 'ADA'])
        
        # Sentiment adatok tárolása
        self.sentiment_data = {symbol: {'overall': 0.0, 'sources': {}} for symbol in self.symbols}
        
        # RPI4 optimalizáció
        self.max_sources = config.get('max_sources', 3)  # Korlátozott források száma
        self.max_history = config.get('max_history', 24)  # Korlátozott előzmények
        
        logger.info("SentimentAnalyzer initialized")
    
    def start(self) -> bool:
        """
        Elindítja a SentimentAnalyzer-t.
        
        Returns:
            bool: Sikeres indítás esetén True, egyébként False
        """
        if self.is_running:
            logger.warning("SentimentAnalyzer is already running")
            return False
        
        try:
            self.is_running = True
            self._update_sentiment()
            logger.info("SentimentAnalyzer started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start SentimentAnalyzer: {str(e)}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Leállítja a SentimentAnalyzer-t.
        
        Returns:
            bool: Sikeres leállítás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("SentimentAnalyzer is not running")
            return False
        
        try:
            self.is_running = False
            logger.info("SentimentAnalyzer stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping SentimentAnalyzer: {str(e)}")
            return False
    
    def _update_sentiment(self) -> None:
        """
        Frissíti a sentiment adatokat az összes konfigurált forrásból.
        """
        try:
            if not self.is_running:
                logger.warning("SentimentAnalyzer is not running, cannot update sentiment")
                return
            
            logger.info("Updating sentiment data")
            
            for symbol in self.symbols:
                # Frissíti a sentiment adatokat minden forrásból
                source_sentiments = {}
                
                if 'news' in self.sources:
                    source_sentiments['news'] = self._analyze_news_sentiment(symbol)
                
                if 'social_media' in self.sources:
                    source_sentiments['social_media'] = self._analyze_social_media_sentiment(symbol)
                
                if 'market_data' in self.sources:
                    source_sentiments['market_data'] = self._analyze_market_data_sentiment(symbol)
                
                # Kiszámítja az átlagos sentiment-et
                overall_sentiment = sum(source_sentiments.values()) / len(source_sentiments) if source_sentiments else 0.0
                
                # Frissíti a sentiment adatokat
                self.sentiment_data[symbol] = {
                    'overall': overall_sentiment,
                    'sources': source_sentiments,
                    'timestamp': datetime.now()
                }
            
            self.last_update_time = datetime.now()
            logger.info("Sentiment data updated successfully")
        
        except Exception as e:
            logger.error(f"Error updating sentiment data: {str(e)}")
    
    def _analyze_news_sentiment(self, symbol: str) -> float:
        """
        Elemzi a hírek hangulatát egy adott szimbólumra.
        
        Args:
            symbol: A szimbólum (pl. BTC)
            
        Returns:
            float: A sentiment érték (-1.0 és 1.0 között)
        """
        try:
            # Valós implementációban itt lenne a hírek lekérdezése és elemzése
            # Most csak egy példa implementációt adunk
            
            # Példa: véletlenszerű sentiment érték, de a BTC általában pozitívabb
            base_sentiment = 0.2 if symbol == 'BTC' else (0.1 if symbol == 'ETH' else 0.0)
            random_factor = random.uniform(-0.5, 0.5)
            sentiment = base_sentiment + random_factor
            
            # Korlátozza a sentiment értéket -1.0 és 1.0 közé
            sentiment = max(-1.0, min(1.0, sentiment))
            
            logger.debug(f"News sentiment for {symbol}: {sentiment:.2f}")
            return sentiment
        
        except Exception as e:
            logger.error(f"Error analyzing news sentiment for {symbol}: {str(e)}")
            return 0.0
    
    def _analyze_social_media_sentiment(self, symbol: str) -> float:
        """
        Elemzi a közösségi média hangulatát egy adott szimbólumra.
        
        Args:
            symbol: A szimbólum (pl. BTC)
            
        Returns:
            float: A sentiment érték (-1.0 és 1.0 között)
        """
        try:
            # Valós implementációban itt lenne a közösségi média adatok lekérdezése és elemzése
            # Most csak egy példa implementációt adunk
            
            # Példa: véletlenszerű sentiment érték, de az ETH általában pozitívabb a közösségi médiában
            base_sentiment = 0.1 if symbol == 'BTC' else (0.3 if symbol == 'ETH' else 0.0)
            random_factor = random.uniform(-0.6, 0.6)
            sentiment = base_sentiment + random_factor
            
            # Korlátozza a sentiment értéket -1.0 és 1.0 közé
            sentiment = max(-1.0, min(1.0, sentiment))
            
            logger.debug(f"Social media sentiment for {symbol}: {sentiment:.2f}")
            return sentiment
        
        except Exception as e:
            logger.error(f"Error analyzing social media sentiment for {symbol}: {str(e)}")
            return 0.0
    
    def _analyze_market_data_sentiment(self, symbol: str) -> float:
        """
        Elemzi a piaci adatok hangulatát egy adott szimbólumra.
        
        Args:
            symbol: A szimbólum (pl. BTC)
            
        Returns:
            float: A sentiment érték (-1.0 és 1.0 között)
        """
        try:
            # Valós implementációban itt lenne a piaci adatok lekérdezése és elemzése
            # Most csak egy példa implementációt adunk
            
            # Példa: véletlenszerű sentiment érték, de az ADA általában pozitívabb a piaci adatok alapján
            base_sentiment = 0.0 if symbol == 'BTC' else (0.1 if symbol == 'ETH' else 0.2)
            random_factor = random.uniform(-0.4, 0.4)
            sentiment = base_sentiment + random_factor
            
            # Korlátozza a sentiment értéket -1.0 és 1.0 közé
            sentiment = max(-1.0, min(1.0, sentiment))
            
            logger.debug(f"Market data sentiment for {symbol}: {sentiment:.2f}")
            return sentiment
        
        except Exception as e:
            logger.error(f"Error analyzing market data sentiment for {symbol}: {str(e)}")
            return 0.0
    
    def get_sentiment(self, symbol: str) -> Optional[Dict]:
        """
        Visszaadja a sentiment adatokat egy adott szimbólumra.
        
        Args:
            symbol: A szimbólum (pl. BTC)
            
        Returns:
            Optional[Dict]: A sentiment adatok, vagy None ha a szimbólum nem található
        """
        if not self.is_running:
            logger.warning("SentimentAnalyzer is not running")
            return None
        
        # Ellenőrzi, hogy frissíteni kell-e a sentiment adatokat
        if self.last_update_time is None or (datetime.now() - self.last_update_time).total_seconds() >= self.update_interval:
            self._update_sentiment()
        
        if symbol in self.sentiment_data:
            return self.sentiment_data[symbol]
        
        logger.warning(f"Symbol {symbol} not found in sentiment data")
        return None
    
    def get_all_sentiments(self) -> Dict:
        """
        Visszaadja az összes sentiment adatot.
        
        Returns:
            Dict: Az összes sentiment adat
        """
        if not self.is_running:
            logger.warning("SentimentAnalyzer is not running")
            return {}
        
        # Ellenőrzi, hogy frissíteni kell-e a sentiment adatokat
        if self.last_update_time is None or (datetime.now() - self.last_update_time).total_seconds() >= self.update_interval:
            self._update_sentiment()
        
        return self.sentiment_data
    
    def get_sentiment_summary(self) -> Dict:
        """
        Visszaadja a sentiment adatok összefoglalóját.
        
        Returns:
            Dict: A sentiment adatok összefoglalója
        """
        if not self.is_running:
            logger.warning("SentimentAnalyzer is not running")
            return {}
        
        # Ellenőrzi, hogy frissíteni kell-e a sentiment adatokat
        if self.last_update_time is None or (datetime.now() - self.last_update_time).total_seconds() >= self.update_interval:
            self._update_sentiment()
        
        summary = {}
        
        for symbol, data in self.sentiment_data.items():
            summary[symbol] = {
                'overall': data.get('overall', 0.0),
                'timestamp': data.get('timestamp', datetime.now()).isoformat() if 'timestamp' in data else None
            }
        
        return summary
