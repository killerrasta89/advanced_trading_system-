"""
Trading Engine - A fő kereskedési motor, amely koordinálja a kereskedési folyamatokat.
"""
import time
import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime

from src.core.order_manager import OrderManager
from src.core.portfolio_manager import PortfolioManager
from src.core.market_data_manager import MarketDataManager
from src.core.strategy_manager import StrategyManager
from src.core.execution_engine import ExecutionEngine
from src.utils.logger import setup_logger

logger = setup_logger('trading_engine')

class TradingEngine:
    """
    A fő kereskedési motor, amely koordinálja a különböző komponenseket és
    biztosítja a kereskedési rendszer működését.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a kereskedési motort a megadott konfigurációval.
        
        Args:
            config: A kereskedési motor konfigurációja
        """
        self.config = config
        self.is_running = False
        self.last_run_time = None
        
        # Inicializálja a fő komponenseket
        self.order_manager = OrderManager(config.get('order_manager', {}))
        self.portfolio_manager = PortfolioManager(config.get('portfolio_manager', {}))
        self.market_data_manager = MarketDataManager(config.get('market_data_manager', {}))
        self.strategy_manager = StrategyManager(config.get('strategy_manager', {}))
        self.execution_engine = ExecutionEngine(config.get('execution_engine', {}))
        
        # Trading loop beállítások
        self.trading_interval = config.get('trading_interval', 5)  # másodperc
        self.trading_thread = None
        
        logger.info("Trading Engine initialized")
    
    def start(self) -> bool:
        """
        Elindítja a kereskedési motort.
        
        Returns:
            bool: Sikeres indítás esetén True, egyébként False
        """
        if self.is_running:
            logger.warning("Trading Engine is already running")
            return False
        
        try:
            # Inicializálja és elindítja a komponenseket
            self.market_data_manager.start()
            self.portfolio_manager.start()
            self.strategy_manager.start()
            self.order_manager.start()
            self.execution_engine.start()
            
            # Elindítja a fő kereskedési ciklust
            self.is_running = True
            self.trading_thread = threading.Thread(target=self._trading_loop)
            self.trading_thread.daemon = True
            self.trading_thread.start()
            
            logger.info("Trading Engine started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start Trading Engine: {str(e)}")
            self.stop()
            return False
    
    def stop(self) -> bool:
        """
        Leállítja a kereskedési motort.
        
        Returns:
            bool: Sikeres leállítás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("Trading Engine is not running")
            return False
        
        try:
            # Leállítja a komponenseket
            self.is_running = False
            
            if self.trading_thread and self.trading_thread.is_alive():
                self.trading_thread.join(timeout=10)
            
            self.execution_engine.stop()
            self.order_manager.stop()
            self.strategy_manager.stop()
            self.portfolio_manager.stop()
            self.market_data_manager.stop()
            
            logger.info("Trading Engine stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Trading Engine: {str(e)}")
            return False
    
    def _trading_loop(self) -> None:
        """
        A fő kereskedési ciklus, amely periodikusan végrehajtja a kereskedési logikát.
        """
        logger.info("Trading loop started")
        
        while self.is_running:
            try:
                cycle_start_time = time.time()
                self.last_run_time = datetime.now()
                
                # 1. Frissíti a piaci adatokat
                market_data = self.market_data_manager.get_latest_data()
                
                # 2. Frissíti a portfólió állapotát
                portfolio = self.portfolio_manager.update_portfolio()
                
                # 3. Futtatja a stratégiákat az aktuális piaci adatokon
                signals = self.strategy_manager.execute_strategies(market_data, portfolio)
                
                # 4. Létrehozza és kezeli a megbízásokat a jelzések alapján
                orders = self.order_manager.process_signals(signals, portfolio)
                
                # 5. Végrehajtja a megbízásokat
                execution_results = self.execution_engine.execute_orders(orders)
                
                # 6. Frissíti a portfóliót a végrehajtott megbízások alapján
                self.portfolio_manager.update_after_execution(execution_results)
                
                # Naplózza a ciklus teljesítményét
                cycle_duration = time.time() - cycle_start_time
                logger.debug(f"Trading cycle completed in {cycle_duration:.4f} seconds")
                
                # Vár a következő ciklusig, figyelembe véve a feldolgozási időt
                sleep_time = max(0, self.trading_interval - cycle_duration)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                time.sleep(self.trading_interval)  # Hiba esetén is vár a következő ciklusig
        
        logger.info("Trading loop stopped")
    
    def get_status(self) -> Dict:
        """
        Visszaadja a kereskedési motor aktuális állapotát.
        
        Returns:
            Dict: A kereskedési motor állapota
        """
        return {
            "is_running": self.is_running,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "order_manager": self.order_manager.get_status(),
            "portfolio_manager": self.portfolio_manager.get_status(),
            "market_data_manager": self.market_data_manager.get_status(),
            "strategy_manager": self.strategy_manager.get_status(),
            "execution_engine": self.execution_engine.get_status()
        }
