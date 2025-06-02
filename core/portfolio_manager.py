"""
Portfolio Manager - Kezeli a felhasználó portfólióját és annak állapotát.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('portfolio_manager')

class PortfolioManager:
    """
    Kezeli a felhasználó portfólióját, nyomon követi az eszközök egyenlegét
    és értékét, valamint frissíti a portfólió állapotát a végrehajtott megbízások alapján.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a PortfolioManager-t a megadott konfigurációval.
        
        Args:
            config: A PortfolioManager konfigurációja
        """
        self.config = config
        self.is_running = False
        self.portfolio = {
            "total_value_usd": 0.0,
            "assets": [],
            "performance": {
                "daily": 0.0,
                "weekly": 0.0,
                "monthly": 0.0,
                "all_time": 0.0
            },
            "last_updated": None
        }
        
        # Konfigurációs beállítások
        self.update_interval = config.get('update_interval', 60)  # másodperc
        self.exchanges = config.get('exchanges', [])
        
        logger.info("PortfolioManager initialized")
    
    def start(self) -> bool:
        """
        Elindítja a PortfolioManager-t.
        
        Returns:
            bool: Sikeres indítás esetén True, egyébként False
        """
        if self.is_running:
            logger.warning("PortfolioManager is already running")
            return False
        
        try:
            self.is_running = True
            # Inicializálja a portfóliót
            self.update_portfolio()
            logger.info("PortfolioManager started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start PortfolioManager: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """
        Leállítja a PortfolioManager-t.
        
        Returns:
            bool: Sikeres leállítás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("PortfolioManager is not running")
            return False
        
        try:
            self.is_running = False
            logger.info("PortfolioManager stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping PortfolioManager: {str(e)}")
            return False
    
    def update_portfolio(self) -> Dict:
        """
        Frissíti a portfólió állapotát az összes konfigurált exchange-ről lekérdezve az egyenlegeket.
        
        Returns:
            Dict: A frissített portfólió állapota
        """
        if not self.is_running:
            logger.warning("PortfolioManager is not running, cannot update portfolio")
            return self.portfolio
        
        try:
            # Itt valós implementációban lekérdezzük az egyenlegeket az exchange-ekről
            # Most csak egy példa implementációt adunk
            
            # Példa adatok (valós implementációban ez az exchange API-ból jönne)
            assets = [
                {"symbol": "BTC", "amount": 0.5, "value_usd": 20000.0},
                {"symbol": "ETH", "amount": 5.0, "value_usd": 10000.0},
                {"symbol": "ADA", "amount": 1000.0, "value_usd": 500.0}
            ]
            
            # Kiszámítja a teljes értéket
            total_value = sum(asset["value_usd"] for asset in assets)
            
            # Frissíti a portfóliót
            self.portfolio["assets"] = assets
            self.portfolio["total_value_usd"] = total_value
            self.portfolio["last_updated"] = datetime.now()
            
            # Példa teljesítmény adatok (valós implementációban ez historikus adatokból számolódna)
            self.portfolio["performance"] = {
                "daily": 2.5,
                "weekly": -1.2,
                "monthly": 5.7,
                "all_time": 15.3
            }
            
            logger.info(f"Portfolio updated, total value: ${total_value:.2f}")
            return self.portfolio
        
        except Exception as e:
            logger.error(f"Error updating portfolio: {str(e)}")
            return self.portfolio
    
    def update_after_execution(self, execution_results: List[Dict]) -> Dict:
        """
        Frissíti a portfólió állapotát a végrehajtott megbízások alapján.
        
        Args:
            execution_results: A végrehajtott megbízások eredményei
            
        Returns:
            Dict: A frissített portfólió állapota
        """
        if not self.is_running:
            logger.warning("PortfolioManager is not running, cannot update after execution")
            return self.portfolio
        
        try:
            # Valós implementációban itt frissítenénk a portfóliót a végrehajtott megbízások alapján
            # Most csak egy példa implementációt adunk
            
            for result in execution_results:
                logger.info(f"Processing execution result: {result}")
                
                # Példa logika a portfólió frissítésére
                symbol = result.get("symbol", "").split("/")[0]  # Pl. BTC/USDT -> BTC
                side = result.get("side", "")
                amount = result.get("filled_amount", 0.0)
                price = result.get("average_price", 0.0)
                
                if side == "buy":
                    # Hozzáadja az eszközt a portfólióhoz vagy növeli a meglévő mennyiséget
                    asset_found = False
                    for asset in self.portfolio["assets"]:
                        if asset["symbol"] == symbol:
                            asset["amount"] += amount
                            asset["value_usd"] += amount * price
                            asset_found = True
                            break
                    
                    if not asset_found:
                        self.portfolio["assets"].append({
                            "symbol": symbol,
                            "amount": amount,
                            "value_usd": amount * price
                        })
                
                elif side == "sell":
                    # Csökkenti az eszköz mennyiségét a portfólióban
                    for asset in self.portfolio["assets"]:
                        if asset["symbol"] == symbol:
                            asset["amount"] -= amount
                            asset["value_usd"] -= amount * price
                            
                            # Ha a mennyiség 0 vagy kevesebb, eltávolítja az eszközt
                            if asset["amount"] <= 0:
                                self.portfolio["assets"].remove(asset)
                            break
            
            # Újraszámítja a teljes értéket
            self.portfolio["total_value_usd"] = sum(asset["value_usd"] for asset in self.portfolio["assets"])
            self.portfolio["last_updated"] = datetime.now()
            
            logger.info(f"Portfolio updated after execution, total value: ${self.portfolio['total_value_usd']:.2f}")
            return self.portfolio
        
        except Exception as e:
            logger.error(f"Error updating portfolio after execution: {str(e)}")
            return self.portfolio
    
    def get_asset_balance(self, symbol: str) -> float:
        """
        Visszaadja egy adott eszköz egyenlegét.
        
        Args:
            symbol: Az eszköz szimbóluma (pl. BTC)
            
        Returns:
            float: Az eszköz egyenlege
        """
        for asset in self.portfolio["assets"]:
            if asset["symbol"] == symbol:
                return asset["amount"]
        return 0.0
    
    def get_asset_value(self, symbol: str) -> float:
        """
        Visszaadja egy adott eszköz értékét USD-ben.
        
        Args:
            symbol: Az eszköz szimbóluma (pl. BTC)
            
        Returns:
            float: Az eszköz értéke USD-ben
        """
        for asset in self.portfolio["assets"]:
            if asset["symbol"] == symbol:
                return asset["value_usd"]
        return 0.0
    
    def get_portfolio(self) -> Dict:
        """
        Visszaadja a teljes portfólió állapotát.
        
        Returns:
            Dict: A portfólió állapota
        """
        return self.portfolio
    
    def get_status(self) -> Dict:
        """
        Visszaadja a PortfolioManager állapotát.
        
        Returns:
            Dict: A PortfolioManager állapota
        """
        return {
            "is_running": self.is_running,
            "total_value_usd": self.portfolio["total_value_usd"],
            "assets_count": len(self.portfolio["assets"]),
            "last_updated": self.portfolio["last_updated"].isoformat() if self.portfolio["last_updated"] else None
        }
