"""
DCA Strategy - Dollar Cost Averaging stratégia
"""
import logging
import numpy as np
from datetime import datetime, timedelta
from strategies.base_strategy import BaseStrategy

class DCAStrategy(BaseStrategy):
    """
    Dollar Cost Averaging (DCA) stratégia implementációja
    
    A stratégia rendszeres időközönként vásárol, függetlenül az ártól,
    így átlagolja a vásárlási árat hosszú távon.
    """
    
    def __init__(self, name, symbol, timeframe, exchange, risk_manager=None):
        """
        Inicializálja a DCA stratégiát
        
        Args:
            name: Stratégia neve
            symbol: Kereskedési szimbólum (pl. "BTC/USDT")
            timeframe: Időkeret (pl. "1h", "15m", "1d")
            exchange: Tőzsde objektum
            risk_manager: Kockázatkezelő objektum (opcionális)
        """
        super().__init__(name, symbol, timeframe, exchange, risk_manager)
        
        # DCA stratégia specifikus beállítások
        self.config.update({
            'interval': 'daily',  # 'hourly', 'daily', 'weekly', 'monthly'
            'amount': 0,          # Vásárlási összeg
            'start_date': None,   # Kezdő dátum
            'end_date': None,     # Befejezés dátuma (opcionális)
            'max_purchases': 0,   # Maximális vásárlások száma (opcionális)
            'day_of_week': None,  # Hét napja (0-6, hétfő-vasárnap) 'weekly' intervallumhoz
            'day_of_month': None, # Hónap napja (1-31) 'monthly' intervallumhoz
            'hour_of_day': 0,     # Nap órája (0-23) 'daily' és 'weekly' intervallumhoz
        })
        
        # DCA állapot
        self.last_purchase_time = None
        self.purchase_count = 0
        self.next_purchase_time = None
        
    def initialize(self):
        """
        DCA stratégia inicializálása
        """
        super().initialize()
        self.logger.info("DCA stratégia inicializálása")
        
        # Ellenőrizzük, hogy a szükséges konfigurációs beállítások megvannak-e
        if self.config['amount'] <= 0:
            self.logger.error("Érvénytelen összeg! A vásárlási összegnek pozitívnak kell lennie.")
            return
        
        if self.config['interval'] not in ['hourly', 'daily', 'weekly', 'monthly']:
            self.logger.error("Érvénytelen intervallum! Az intervallumnak 'hourly', 'daily', 'weekly' vagy 'monthly' kell lennie.")
            return
        
        # Kezdő dátum beállítása, ha nincs megadva
        if self.config['start_date'] is None:
            self.config['start_date'] = datetime.now()
        
        # Következő vásárlás idejének kiszámítása
        self.calculate_next_purchase_time()
        
    def calculate_next_purchase_time(self):
        """
        Következő vásárlás idejének kiszámítása
        """
        if self.last_purchase_time is None:
            # Első vásárlás
            next_time = self.config['start_date']
        else:
            # Következő vásárlás az intervallum alapján
            next_time = self.last_purchase_time
            
            if self.config['interval'] == 'hourly':
                next_time = next_time + timedelta(hours=1)
            
            elif self.config['interval'] == 'daily':
                next_time = next_time + timedelta(days=1)
                next_time = next_time.replace(hour=self.config['hour_of_day'], minute=0, second=0, microsecond=0)
            
            elif self.config['interval'] == 'weekly':
                # Következő hét adott napja
                days_ahead = self.config['day_of_week'] - next_time.weekday()
                if days_ahead <= 0:  # Ha már elmúlt ezen a héten, akkor a következő hétre
                    days_ahead += 7
                
                next_time = next_time + timedelta(days=days_ahead)
                next_time = next_time.replace(hour=self.config['hour_of_day'], minute=0, second=0, microsecond=0)
            
            elif self.config['interval'] == 'monthly':
                # Következő hónap adott napja
                month = next_time.month + 1
                year = next_time.year
                
                if month > 12:
                    month = 1
                    year += 1
                
                # Ellenőrizzük, hogy a nap érvényes-e az adott hónapban
                day = min(self.config['day_of_month'], self._days_in_month(year, month))
                
                next_time = next_time.replace(year=year, month=month, day=day, hour=self.config['hour_of_day'], 
                                             minute=0, second=0, microsecond=0)
        
        self.next_purchase_time = next_time
        self.logger.info(f"Következő vásárlás ideje: {self.next_purchase_time}")
    
    def _days_in_month(self, year, month):
        """
        Adott hónap napjainak száma
        
        Args:
            year: Év
            month: Hónap (1-12)
            
        Returns:
            int: Napok száma
        """
        if month == 2:
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                return 29
            return 28
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            return 31
    
    def generate_signal(self, data):
        """
        Kereskedési jel generálása az adatok alapján
        
        Args:
            data: Piaci adatok (DataFrame)
            
        Returns:
            dict: Kereskedési jel vagy None
        """
        # Aktuális idő
        current_time = datetime.now()
        
        # Ellenőrizzük, hogy elértük-e a maximális vásárlások számát
        if self.config['max_purchases'] > 0 and self.purchase_count >= self.config['max_purchases']:
            return None
        
        # Ellenőrizzük, hogy elértük-e a befejezés dátumát
        if self.config['end_date'] is not None and current_time > self.config['end_date']:
            return None
        
        # Ellenőrizzük, hogy elérkezett-e a következő vásárlás ideje
        if self.next_purchase_time is not None and current_time >= self.next_purchase_time:
            # Aktuális ár
            current_price = data['close'].iloc[-1]
            
            # Mennyiség kiszámítása
            quantity = self.config['amount'] / current_price
            
            # Vásárlási jel
            signal = {
                'action': 'buy',
                'price': current_price,
                'volume': quantity,
                'type': 'market',
                'params': {
                    'dca_purchase_number': self.purchase_count + 1,
                    'dca_purchase_time': current_time.isoformat()
                }
            }
            
            # Frissítjük az állapotot
            self.last_purchase_time = current_time
            self.purchase_count += 1
            
            # Következő vásárlás idejének kiszámítása
            self.calculate_next_purchase_time()
            
            return signal
        
        return None
    
    def get_average_purchase_price(self):
        """
        Átlagos vásárlási ár kiszámítása
        
        Returns:
            float: Átlagos vásárlási ár
        """
        # Implementáció a konkrét tőzsde API-tól függ
        # Itt egy egyszerű becslést adunk
        if self.performance['total_trades'] > 0:
            return self.performance['total_profit'] / self.performance['total_trades']
        return 0
    
    def get_dca_status(self):
        """
        DCA stratégia állapotának lekérdezése
        
        Returns:
            dict: DCA állapot
        """
        return {
            'purchase_count': self.purchase_count,
            'last_purchase_time': self.last_purchase_time,
            'next_purchase_time': self.next_purchase_time,
            'average_purchase_price': self.get_average_purchase_price(),
            'total_invested': self.config['amount'] * self.purchase_count,
            'max_purchases': self.config['max_purchases'],
            'remaining_purchases': self.config['max_purchases'] - self.purchase_count if self.config['max_purchases'] > 0 else None
        }
