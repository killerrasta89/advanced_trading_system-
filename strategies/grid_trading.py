"""
Grid Trading Strategy - Rács kereskedési stratégia
"""
import logging
import numpy as np
from strategies.base_strategy import BaseStrategy

class GridTradingStrategy(BaseStrategy):
    """
    Grid Trading (Rács kereskedési) stratégia implementációja
    
    A stratégia egy ár tartományt feloszt egyenlő részekre (rácsokra),
    és minden rácsnál vételi vagy eladási megbízásokat helyez el.
    Amikor az ár lefelé mozog, a stratégia vásárol, amikor felfelé, akkor elad.
    """
    
    def __init__(self, name, symbol, timeframe, exchange, risk_manager=None):
        """
        Inicializálja a Grid Trading stratégiát
        
        Args:
            name: Stratégia neve
            symbol: Kereskedési szimbólum (pl. "BTC/USDT")
            timeframe: Időkeret (pl. "1h", "15m", "1d")
            exchange: Tőzsde objektum
            risk_manager: Kockázatkezelő objektum (opcionális)
        """
        super().__init__(name, symbol, timeframe, exchange, risk_manager)
        
        # Grid stratégia specifikus beállítások
        self.config.update({
            'upper_price': 0,      # Felső árhatár
            'lower_price': 0,      # Alsó árhatár
            'grid_levels': 10,     # Rács szintek száma
            'quantity_per_grid': 0, # Mennyiség rácsszintenként
            'grid_spacing_type': 'arithmetic', # 'arithmetic' vagy 'geometric'
            'take_profit_pct': 1.0, # Take profit százalék
            'stop_loss_pct': 2.0,   # Stop loss százalék
        })
        
        # Grid szintek és megbízások
        self.grid_levels = []
        self.active_orders = {}
        
    def initialize(self):
        """
        Grid stratégia inicializálása
        """
        super().initialize()
        self.logger.info("Grid Trading stratégia inicializálása")
        
        # Ellenőrizzük, hogy a szükséges konfigurációs beállítások megvannak-e
        if self.config['upper_price'] <= 0 or self.config['lower_price'] <= 0:
            self.logger.error("Érvénytelen ár határok! Felső és alsó árhatárok beállítása szükséges.")
            return
        
        if self.config['upper_price'] <= self.config['lower_price']:
            self.logger.error("Érvénytelen ár határok! A felső árhatárnak nagyobbnak kell lennie az alsó árhatárnál.")
            return
        
        if self.config['grid_levels'] < 2:
            self.logger.error("Érvénytelen rács szintek! Legalább 2 rács szint szükséges.")
            return
        
        if self.config['quantity_per_grid'] <= 0:
            self.logger.error("Érvénytelen mennyiség! A rácsszintenkénti mennyiségnek pozitívnak kell lennie.")
            return
        
        # Grid szintek kiszámítása
        self.calculate_grid_levels()
        
    def calculate_grid_levels(self):
        """
        Grid szintek kiszámítása a konfigurációs beállítások alapján
        """
        upper_price = self.config['upper_price']
        lower_price = self.config['lower_price']
        grid_levels = self.config['grid_levels']
        
        self.grid_levels = []
        
        if self.config['grid_spacing_type'] == 'arithmetic':
            # Aritmetikai felosztás (egyenlő távolságok)
            step = (upper_price - lower_price) / (grid_levels - 1)
            for i in range(grid_levels):
                price = lower_price + i * step
                self.grid_levels.append(round(price, 8))
        else:
            # Geometriai felosztás (százalékos távolságok)
            ratio = (upper_price / lower_price) ** (1 / (grid_levels - 1))
            for i in range(grid_levels):
                price = lower_price * (ratio ** i)
                self.grid_levels.append(round(price, 8))
        
        self.logger.info(f"Grid szintek kiszámítva: {self.grid_levels}")
    
    def generate_signal(self, data):
        """
        Kereskedési jel generálása az adatok alapján
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            dict: Kereskedési jel vagy None
        """
        if len(data) < 2:
            return None
        
        # Aktuális ár
        current_price = data['close'].iloc[-1]
        
        # Ha az ár kívül esik a grid tartományon, nincs jel
        if current_price < self.config['lower_price'] or current_price > self.config['upper_price']:
            return None
        
        # Meghatározzuk, hogy melyik két grid szint között van az ár
        for i in range(len(self.grid_levels) - 1):
            lower_grid = self.grid_levels[i]
            upper_grid = self.grid_levels[i + 1]
            
            if lower_grid <= current_price < upper_grid:
                # Előző ár
                previous_price = data['close'].iloc[-2]
                
                # Ha az ár átlépett egy grid szintet
                if previous_price < lower_grid and current_price >= lower_grid:
                    # Eladási jel a felső grid szintnél
                    return {
                        'action': 'sell',
                        'price': upper_grid,
                        'volume': self.config['quantity_per_grid'],
                        'type': 'limit',
                        'params': {
                            'grid_level': i + 1
                        }
                    }
                elif previous_price >= upper_grid and current_price < upper_grid:
                    # Vételi jel az alsó grid szintnél
                    return {
                        'action': 'buy',
                        'price': lower_grid,
                        'volume': self.config['quantity_per_grid'],
                        'type': 'limit',
                        'params': {
                            'grid_level': i
                        }
                    }
        
        return None
    
    def place_initial_orders(self):
        """
        Kezdeti megbízások elhelyezése minden grid szinten
        
        Returns:
            list: Elhelyezett megbízások listája
        """
        orders = []
        current_price = self.exchange.get_ticker(self.symbol)['last']
        
        for i, price in enumerate(self.grid_levels):
            # Az aktuális ár alatti szinteken vételi megbízások
            if price < current_price:
                order = {
                    'action': 'buy',
                    'price': price,
                    'volume': self.config['quantity_per_grid'],
                    'type': 'limit',
                    'params': {
                        'grid_level': i
                    }
                }
                orders.append(order)
            
            # Az aktuális ár feletti szinteken eladási megbízások
            elif price > current_price:
                order = {
                    'action': 'sell',
                    'price': price,
                    'volume': self.config['quantity_per_grid'],
                    'type': 'limit',
                    'params': {
                        'grid_level': i
                    }
                }
                orders.append(order)
        
        self.logger.info(f"Kezdeti megbízások: {len(orders)}")
        return orders
    
    def handle_filled_order(self, order):
        """
        Teljesült megbízás kezelése
        
        Args:
            order: Teljesült megbízás adatai
            
        Returns:
            dict: Új megbízás vagy None
        """
        grid_level = order['params']['grid_level']
        
        # Ha vételi megbízás teljesült, eladási megbízást helyezünk el egy szinttel feljebb
        if order['action'] == 'buy' and grid_level < len(self.grid_levels) - 1:
            sell_price = self.grid_levels[grid_level + 1]
            new_order = {
                'action': 'sell',
                'price': sell_price,
                'volume': self.config['quantity_per_grid'],
                'type': 'limit',
                'params': {
                    'grid_level': grid_level + 1
                }
            }
            return new_order
        
        # Ha eladási megbízás teljesült, vételi megbízást helyezünk el egy szinttel lejjebb
        elif order['action'] == 'sell' and grid_level > 0:
            buy_price = self.grid_levels[grid_level - 1]
            new_order = {
                'action': 'buy',
                'price': buy_price,
                'volume': self.config['quantity_per_grid'],
                'type': 'limit',
                'params': {
                    'grid_level': grid_level - 1
                }
            }
            return new_order
        
        return None
    
    def adjust_grid_levels(self, new_upper_price=None, new_lower_price=None, new_grid_levels=None):
        """
        Grid szintek módosítása
        
        Args:
            new_upper_price: Új felső árhatár (opcionális)
            new_lower_price: Új alsó árhatár (opcionális)
            new_grid_levels: Új rács szintek száma (opcionális)
            
        Returns:
            bool: Sikeres módosítás
        """
        # Beállítások frissítése
        if new_upper_price is not None:
            self.config['upper_price'] = new_upper_price
        
        if new_lower_price is not None:
            self.config['lower_price'] = new_lower_price
        
        if new_grid_levels is not None:
            self.config['grid_levels'] = new_grid_levels
        
        # Ellenőrzés
        if self.config['upper_price'] <= self.config['lower_price']:
            self.logger.error("Érvénytelen ár határok! A felső árhatárnak nagyobbnak kell lennie az alsó árhatárnál.")
            return False
        
        if self.config['grid_levels'] < 2:
            self.logger.error("Érvénytelen rács szintek! Legalább 2 rács szint szükséges.")
            return False
        
        # Grid szintek újraszámítása
        self.calculate_grid_levels()
        
        # Aktív megbízások törlése
        for order_id in self.active_orders:
            self.exchange.cancel_order(order_id, self.symbol)
        
        self.active_orders = {}
        
        # Új megbízások elhelyezése
        initial_orders = self.place_initial_orders()
        for order in initial_orders:
            try:
                result = self.exchange.create_order(
                    self.symbol,
                    order['type'],
                    order['action'],
                    order['volume'],
                    order['price']
                )
                self.active_orders[result['id']] = order
            except Exception as e:
                self.logger.error(f"Hiba a megbízás elhelyezése során: {e}")
        
        return True
    
    def calculate_profit(self):
        """
        Stratégia nyereségének kiszámítása
        
        Returns:
            float: Nyereség
        """
        # Implementáció a konkrét tőzsde API-tól függ
        # Itt egy egyszerű becslést adunk
        return self.performance['total_profit'] - self.performance['total_loss']
