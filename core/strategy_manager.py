"""
Strategy Manager - Kezeli a kereskedési stratégiákat és azok végrehajtását.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('strategy_manager')

class StrategyManager:
    """
    Kezeli a kereskedési stratégiákat, koordinálja azok végrehajtását,
    és összegyűjti a generált kereskedési jelzéseket.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a StrategyManager-t a megadott konfigurációval.
        
        Args:
            config: A StrategyManager konfigurációja
        """
        self.config = config
        self.is_running = False
        self.strategies = []
        
        # Konfigurációs beállítások
        self.max_active_strategies = config.get('max_active_strategies', 10)
        
        logger.info("StrategyManager initialized")
    
    def start(self) -> bool:
        """
        Elindítja a StrategyManager-t.
        
        Returns:
            bool: Sikeres indítás esetén True, egyébként False
        """
        if self.is_running:
            logger.warning("StrategyManager is already running")
            return False
        
        try:
            self.is_running = True
            self._load_strategies()
            logger.info("StrategyManager started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start StrategyManager: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """
        Leállítja a StrategyManager-t.
        
        Returns:
            bool: Sikeres leállítás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("StrategyManager is not running")
            return False
        
        try:
            self.is_running = False
            logger.info("StrategyManager stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping StrategyManager: {str(e)}")
            return False
    
    def _load_strategies(self) -> None:
        """
        Betölti a konfigurált stratégiákat.
        """
        try:
            # Valós implementációban itt betöltenénk a stratégiákat az adatbázisból
            # Most csak példa stratégiákat hozunk létre
            
            # Példa Grid Trading stratégia
            grid_strategy = {
                "id": 1,
                "name": "BTC/USDT Grid Trading",
                "type": "grid_trading",
                "symbol": "BTC/USDT",
                "is_active": True,
                "config": {
                    "upper_price": 45000.0,
                    "lower_price": 35000.0,
                    "grid_levels": 10,
                    "investment_amount": 10000.0,
                    "stop_loss_percentage": 5.0
                }
            }
            
            # Példa DCA stratégia
            dca_strategy = {
                "id": 2,
                "name": "ETH/USDT DCA",
                "type": "dca_strategy",
                "symbol": "ETH/USDT",
                "is_active": True,
                "config": {
                    "base_order_size": 100.0,
                    "interval_hours": 24,
                    "max_orders": 10,
                    "price_deviation_threshold": 5.0
                }
            }
            
            self.strategies = [grid_strategy, dca_strategy]
            logger.info(f"Loaded {len(self.strategies)} strategies")
        
        except Exception as e:
            logger.error(f"Error loading strategies: {str(e)}")
            self.strategies = []
    
    def execute_strategies(self, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja az aktív stratégiákat az aktuális piaci adatokon és portfólión.
        
        Args:
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        if not self.is_running:
            logger.warning("StrategyManager is not running, cannot execute strategies")
            return []
        
        signals = []
        
        try:
            for strategy in self.strategies:
                if not strategy.get("is_active", False):
                    continue
                
                logger.debug(f"Executing strategy: {strategy['name']}")
                
                # A stratégia típusa alapján végrehajtja a megfelelő stratégiát
                strategy_type = strategy.get("type", "")
                
                if strategy_type == "grid_trading":
                    strategy_signals = self._execute_grid_strategy(strategy, market_data, portfolio)
                elif strategy_type == "dca_strategy":
                    strategy_signals = self._execute_dca_strategy(strategy, market_data, portfolio)
                elif strategy_type == "momentum_strategy":
                    strategy_signals = self._execute_momentum_strategy(strategy, market_data, portfolio)
                elif strategy_type == "mean_reversion":
                    strategy_signals = self._execute_mean_reversion_strategy(strategy, market_data, portfolio)
                elif strategy_type == "arbitrage_strategy":
                    strategy_signals = self._execute_arbitrage_strategy(strategy, market_data, portfolio)
                elif strategy_type == "ml_strategy":
                    strategy_signals = self._execute_ml_strategy(strategy, market_data, portfolio)
                elif strategy_type == "scalping_strategy":
                    strategy_signals = self._execute_scalping_strategy(strategy, market_data, portfolio)
                elif strategy_type == "portfolio_rebalance":
                    strategy_signals = self._execute_portfolio_rebalance_strategy(strategy, market_data, portfolio)
                else:
                    logger.warning(f"Unknown strategy type: {strategy_type}")
                    strategy_signals = []
                
                # Hozzáadja a stratégia azonosítóját a jelzésekhez
                for signal in strategy_signals:
                    signal["strategy_id"] = strategy["id"]
                
                signals.extend(strategy_signals)
            
            logger.info(f"Generated {len(signals)} trading signals")
            return signals
        
        except Exception as e:
            logger.error(f"Error executing strategies: {str(e)}")
            return []
    
    def _execute_grid_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja a Grid Trading stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        signals = []
        
        try:
            symbol = strategy.get("symbol", "")
            config = strategy.get("config", {})
            
            if symbol not in market_data:
                logger.warning(f"Symbol {symbol} not found in market data")
                return []
            
            # Kinyeri a szükséges konfigurációs paramétereket
            upper_price = config.get("upper_price", 0.0)
            lower_price = config.get("lower_price", 0.0)
            grid_levels = config.get("grid_levels", 0)
            
            if grid_levels <= 0 or upper_price <= lower_price:
                logger.warning(f"Invalid grid configuration for {symbol}")
                return []
            
            # Kiszámítja a grid szinteket
            price_step = (upper_price - lower_price) / grid_levels
            grid_prices = [lower_price + i * price_step for i in range(grid_levels + 1)]
            
            # Lekéri az aktuális árat
            current_price = market_data[symbol]["ticker"]["last"]
            
            # Meghatározza a legközelebbi grid szintet
            closest_level = min(range(len(grid_prices)), key=lambda i: abs(grid_prices[i] - current_price))
            
            # Ha az ár a grid szint alatt van, vásárlási jelzést generál
            if current_price < grid_prices[closest_level] * 0.99:
                signals.append({
                    "symbol": symbol,
                    "type": "limit",
                    "side": "buy",
                    "amount": 0.01,  # Példa mennyiség
                    "price": current_price * 1.001
                })
            
            # Ha az ár a grid szint felett van, eladási jelzést generál
            elif current_price > grid_prices[closest_level] * 1.01:
                signals.append({
                    "symbol": symbol,
                    "type": "limit",
                    "side": "sell",
                    "amount": 0.01,  # Példa mennyiség
                    "price": current_price * 0.999
                })
            
            return signals
        
        except Exception as e:
            logger.error(f"Error executing grid strategy: {str(e)}")
            return []
    
    def _execute_dca_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja a Dollar Cost Averaging stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        signals = []
        
        try:
            symbol = strategy.get("symbol", "")
            config = strategy.get("config", {})
            
            if symbol not in market_data:
                logger.warning(f"Symbol {symbol} not found in market data")
                return []
            
            # Kinyeri a szükséges konfigurációs paramétereket
            base_order_size = config.get("base_order_size", 0.0)
            
            # Példa: minden futtatáskor 5% eséllyel generál vásárlási jelzést
            # Valós implementációban ez időzítés alapján történne
            import random
            if random.random() < 0.05:
                signals.append({
                    "symbol": symbol,
                    "type": "market",
                    "side": "buy",
                    "amount": base_order_size
                })
            
            return signals
        
        except Exception as e:
            logger.error(f"Error executing DCA strategy: {str(e)}")
            return []
    
    def _execute_momentum_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja a Momentum stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        # Példa implementáció, valós esetben itt lenne a momentum stratégia logikája
        return []
    
    def _execute_mean_reversion_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja a Mean Reversion stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        # Példa implementáció, valós esetben itt lenne a mean reversion stratégia logikája
        return []
    
    def _execute_arbitrage_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja az Arbitrage stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        # Példa implementáció, valós esetben itt lenne az arbitrage stratégia logikája
        return []
    
    def _execute_ml_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja a Machine Learning stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        # Példa implementáció, valós esetben itt lenne az ML stratégia logikája
        return []
    
    def _execute_scalping_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja a Scalping stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        # Példa implementáció, valós esetben itt lenne a scalping stratégia logikája
        return []
    
    def _execute_portfolio_rebalance_strategy(self, strategy: Dict, market_data: Dict, portfolio: Dict) -> List[Dict]:
        """
        Végrehajtja a Portfolio Rebalancing stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            market_data: Az aktuális piaci adatok
            portfolio: Az aktuális portfólió állapota
            
        Returns:
            List[Dict]: A generált kereskedési jelzések listája
        """
        # Példa implementáció, valós esetben itt lenne a portfolio rebalancing stratégia logikája
        return []
    
    def add_strategy(self, strategy: Dict) -> bool:
        """
        Hozzáad egy új stratégiát.
        
        Args:
            strategy: A stratégia konfigurációja
            
        Returns:
            bool: Sikeres hozzáadás esetén True, egyébként False
        """
        try:
            if len(self.strategies) >= self.max_active_strategies:
                logger.warning(f"Cannot add more strategies, maximum limit reached: {self.max_active_strategies}")
                return False
            
            # Ellenőrzi, hogy a stratégia azonosítója egyedi-e
            for existing_strategy in self.strategies:
                if existing_strategy.get("id") == strategy.get("id"):
                    logger.warning(f"Strategy with ID {strategy.get('id')} already exists")
                    return False
            
            self.strategies.append(strategy)
            logger.info(f"Added new strategy: {strategy.get('name')}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding strategy: {str(e)}")
            return False
    
    def update_strategy(self, strategy_id: int, updates: Dict) -> bool:
        """
        Frissít egy meglévő stratégiát.
        
        Args:
            strategy_id: A stratégia azonosítója
            updates: A frissítendő mezők
            
        Returns:
            bool: Sikeres frissítés esetén True, egyébként False
        """
        try:
            for i, strategy in enumerate(self.strategies):
                if strategy.get("id") == strategy_id:
                    # Frissíti a stratégiát
                    for key, value in updates.items():
                        strategy[key] = value
                    
                    self.strategies[i] = strategy
                    logger.info(f"Updated strategy: {strategy.get('name')}")
                    return True
            
            logger.warning(f"Strategy with ID {strategy_id} not found")
            return False
        
        except Exception as e:
            logger.error(f"Error updating strategy: {str(e)}")
            return False
    
    def remove_strategy(self, strategy_id: int) -> bool:
        """
        Eltávolít egy stratégiát.
        
        Args:
            strategy_id: A stratégia azonosítója
            
        Returns:
            bool: Sikeres eltávolítás esetén True, egyébként False
        """
        try:
            for i, strategy in enumerate(self.strategies):
                if strategy.get("id") == strategy_id:
                    removed_strategy = self.strategies.pop(i)
                    logger.info(f"Removed strategy: {removed_strategy.get('name')}")
                    return True
            
            logger.warning(f"Strategy with ID {strategy_id} not found")
            return False
        
        except Exception as e:
            logger.error(f"Error removing strategy: {str(e)}")
            return False
    
    def get_strategies(self) -> List[Dict]:
        """
        Visszaadja az összes stratégiát.
        
        Returns:
            List[Dict]: A stratégiák listája
        """
        return self.strategies
    
    def get_active_strategies(self) -> List[Dict]:
        """
        Visszaadja az aktív stratégiákat.
        
        Returns:
            List[Dict]: Az aktív stratégiák listája
        """
        return [strategy for strategy in self.strategies if strategy.get("is_active", False)]
    
    def get_strategy(self, strategy_id: int) -> Optional[Dict]:
        """
        Visszaad egy adott stratégiát.
        
        Args:
            strategy_id: A stratégia azonosítója
            
        Returns:
            Optional[Dict]: A stratégia, vagy None ha nem található
        """
        for strategy in self.strategies:
            if strategy.get("id") == strategy_id:
                return strategy
        return None
    
    def get_status(self) -> Dict:
        """
        Visszaadja a StrategyManager állapotát.
        
        Returns:
            Dict: A StrategyManager állapota
        """
        return {
            "is_running": self.is_running,
            "total_strategies": len(self.strategies),
            "active_strategies": len(self.get_active_strategies())
        }
