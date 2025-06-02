"""
Order Manager - Kezeli a kereskedési megbízásokat és azok életciklusát.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('order_manager')

class Order:
    """
    Egy kereskedési megbízást reprezentáló osztály.
    """
    def __init__(self, 
                 symbol: str, 
                 order_type: str, 
                 side: str, 
                 amount: float, 
                 price: Optional[float] = None,
                 strategy_id: Optional[int] = None):
        """
        Inicializálja a megbízást.
        
        Args:
            symbol: A kereskedési pár (pl. BTC/USDT)
            order_type: A megbízás típusa (market, limit, stb.)
            side: A megbízás iránya (buy, sell)
            amount: A kereskedni kívánt mennyiség
            price: Az ár (limit megbízásoknál)
            strategy_id: A stratégia azonosítója, amely létrehozta a megbízást
        """
        self.id = None  # Az exchange által adott ID
        self.symbol = symbol
        self.order_type = order_type
        self.side = side
        self.amount = amount
        self.price = price
        self.strategy_id = strategy_id
        self.status = "created"
        self.created_at = datetime.now()
        self.executed_at = None
        self.filled_amount = 0.0
        self.average_price = None
        self.exchange_id = None
    
    def to_dict(self) -> Dict:
        """
        A megbízás adatait szótár formájában adja vissza.
        
        Returns:
            Dict: A megbízás adatai
        """
        return {
            "id": self.id,
            "symbol": self.symbol,
            "order_type": self.order_type,
            "side": self.side,
            "amount": self.amount,
            "price": self.price,
            "strategy_id": self.strategy_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "filled_amount": self.filled_amount,
            "average_price": self.average_price,
            "exchange_id": self.exchange_id
        }

class OrderManager:
    """
    Kezeli a kereskedési megbízásokat és azok életciklusát.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja az OrderManager-t a megadott konfigurációval.
        
        Args:
            config: Az OrderManager konfigurációja
        """
        self.config = config
        self.is_running = False
        self.orders = []  # Aktív megbízások
        self.order_history = []  # Lezárt megbízások
        
        # Konfigurációs beállítások
        self.max_active_orders = config.get('max_active_orders', 100)
        self.max_order_history = config.get('max_order_history', 1000)
        
        logger.info("OrderManager initialized")
    
    def start(self) -> bool:
        """
        Elindítja az OrderManager-t.
        
        Returns:
            bool: Sikeres indítás esetén True, egyébként False
        """
        if self.is_running:
            logger.warning("OrderManager is already running")
            return False
        
        try:
            self.is_running = True
            logger.info("OrderManager started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to start OrderManager: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """
        Leállítja az OrderManager-t.
        
        Returns:
            bool: Sikeres leállítás esetén True, egyébként False
        """
        if not self.is_running:
            logger.warning("OrderManager is not running")
            return False
        
        try:
            self.is_running = False
            logger.info("OrderManager stopped successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping OrderManager: {str(e)}")
            return False
    
    def process_signals(self, signals: List[Dict], portfolio: Dict) -> List[Order]:
        """
        Feldolgozza a stratégiák által generált jelzéseket és létrehozza a megfelelő megbízásokat.
        
        Args:
            signals: A stratégiák által generált jelzések listája
            portfolio: A jelenlegi portfólió állapota
            
        Returns:
            List[Order]: A létrehozott megbízások listája
        """
        if not self.is_running:
            logger.warning("OrderManager is not running, cannot process signals")
            return []
        
        created_orders = []
        
        try:
            for signal in signals:
                # Ellenőrzi, hogy a jelzés érvényes-e
                if not self._validate_signal(signal, portfolio):
                    continue
                
                # Létrehozza a megbízást a jelzés alapján
                order = self._create_order_from_signal(signal)
                if order:
                    self.orders.append(order)
                    created_orders.append(order)
                    logger.info(f"Created {order.side} order for {order.symbol}: {order.amount} @ {order.price}")
            
            return created_orders
        
        except Exception as e:
            logger.error(f"Error processing signals: {str(e)}")
            return []
    
    def _validate_signal(self, signal: Dict, portfolio: Dict) -> bool:
        """
        Ellenőrzi, hogy a jelzés érvényes-e a jelenlegi portfólió állapota alapján.
        
        Args:
            signal: A stratégia által generált jelzés
            portfolio: A jelenlegi portfólió állapota
            
        Returns:
            bool: Érvényes jelzés esetén True, egyébként False
        """
        # Ellenőrzi a kötelező mezőket
        required_fields = ['symbol', 'side', 'amount', 'type']
        for field in required_fields:
            if field not in signal:
                logger.warning(f"Signal missing required field: {field}")
                return False
        
        # Ellenőrzi, hogy a limit megbízásoknak van-e ára
        if signal['type'] == 'limit' and 'price' not in signal:
            logger.warning("Limit order signal missing price")
            return False
        
        # Ellenőrzi, hogy van-e elég egyenleg a vásárláshoz
        if signal['side'] == 'buy':
            # Itt egyszerűsített ellenőrzés, a valós implementációban figyelembe kell venni a párt és a pontos egyenleget
            if portfolio.get('total_balance_usd', 0) <= 0:
                logger.warning("Insufficient balance for buy order")
                return False
        
        # Ellenőrzi, hogy van-e elég eszköz az eladáshoz
        if signal['side'] == 'sell':
            # Itt egyszerűsített ellenőrzés, a valós implementációban figyelembe kell venni a pontos eszköz mennyiséget
            symbol_base = signal['symbol'].split('/')[0]
            asset_balance = 0
            for asset in portfolio.get('assets', []):
                if asset.get('symbol') == symbol_base:
                    asset_balance = asset.get('amount', 0)
                    break
            
            if asset_balance < signal['amount']:
                logger.warning(f"Insufficient {symbol_base} balance for sell order")
                return False
        
        return True
    
    def _create_order_from_signal(self, signal: Dict) -> Optional[Order]:
        """
        Létrehoz egy megbízást a jelzés alapján.
        
        Args:
            signal: A stratégia által generált jelzés
            
        Returns:
            Optional[Order]: A létrehozott megbízás, vagy None hiba esetén
        """
        try:
            order = Order(
                symbol=signal['symbol'],
                order_type=signal['type'],
                side=signal['side'],
                amount=signal['amount'],
                price=signal.get('price'),
                strategy_id=signal.get('strategy_id')
            )
            return order
        
        except Exception as e:
            logger.error(f"Error creating order from signal: {str(e)}")
            return None
    
    def update_order_status(self, order_id: str, status: str, filled_amount: float = None, 
                           average_price: float = None, executed_at: datetime = None) -> bool:
        """
        Frissíti egy megbízás állapotát.
        
        Args:
            order_id: A megbízás azonosítója
            status: Az új állapot
            filled_amount: A teljesített mennyiség
            average_price: Az átlagos teljesítési ár
            executed_at: A teljesítés időpontja
            
        Returns:
            bool: Sikeres frissítés esetén True, egyébként False
        """
        try:
            # Megkeresi a megbízást az aktív megbízások között
            for order in self.orders:
                if order.id == order_id:
                    order.status = status
                    
                    if filled_amount is not None:
                        order.filled_amount = filled_amount
                    
                    if average_price is not None:
                        order.average_price = average_price
                    
                    if executed_at is not None:
                        order.executed_at = executed_at
                    
                    # Ha a megbízás lezárult, áthelyezi a történetbe
                    if status in ['filled', 'canceled', 'rejected', 'expired']:
                        self.orders.remove(order)
                        self.order_history.append(order)
                        
                        # Korlátozza a történet méretét
                        if len(self.order_history) > self.max_order_history:
                            self.order_history = self.order_history[-self.max_order_history:]
                    
                    logger.info(f"Updated order {order_id} status to {status}")
                    return True
            
            logger.warning(f"Order {order_id} not found")
            return False
        
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return False
    
    def get_active_orders(self) -> List[Dict]:
        """
        Visszaadja az aktív megbízások listáját.
        
        Returns:
            List[Dict]: Az aktív megbízások listája
        """
        return [order.to_dict() for order in self.orders]
    
    def get_order_history(self, limit: int = 100) -> List[Dict]:
        """
        Visszaadja a lezárt megbízások történetét.
        
        Args:
            limit: A visszaadandó megbízások maximális száma
            
        Returns:
            List[Dict]: A lezárt megbízások listája
        """
        return [order.to_dict() for order in self.order_history[-limit:]]
    
    def get_status(self) -> Dict:
        """
        Visszaadja az OrderManager állapotát.
        
        Returns:
            Dict: Az OrderManager állapota
        """
        return {
            "is_running": self.is_running,
            "active_orders_count": len(self.orders),
            "order_history_count": len(self.order_history)
        }
