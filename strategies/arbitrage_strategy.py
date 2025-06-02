"""
Arbitrage Strategy - Arbitrázs kereskedési stratégia
"""
import logging
import numpy as np
from datetime import datetime
from strategies.base_strategy import BaseStrategy

class ArbitrageStrategy(BaseStrategy):
    """
    Arbitrázs stratégia implementációja
    
    A stratégia különböző tőzsdék közötti árkülönbségeket használja ki.
    Amikor egy eszköz ára jelentősen eltér két tőzsdén, a stratégia
    az olcsóbb tőzsdén vásárol és a drágábbon elad.
    """
    
    def __init__(self, name, symbol, timeframe, exchanges, risk_manager=None):
        """
        Inicializálja az Arbitrázs stratégiát
        
        Args:
            name: Stratégia neve
            symbol: Kereskedési szimbólum (pl. "BTC/USDT")
            timeframe: Időkeret (pl. "1h", "15m", "1d")
            exchanges: Tőzsde objektumok listája vagy szótára
            risk_manager: Kockázatkezelő objektum (opcionális)
        """
        # Az első tőzsdét használjuk alapértelmezettként
        if isinstance(exchanges, list):
            exchange = exchanges[0]
            self.exchanges = {exchange.name: exchange for exchange in exchanges}
        elif isinstance(exchanges, dict):
            exchange = list(exchanges.values())[0]
            self.exchanges = exchanges
        else:
            raise ValueError("Az exchanges paraméternek listának vagy szótárnak kell lennie")
        
        super().__init__(name, symbol, timeframe, exchange, risk_manager)
        
        # Arbitrázs stratégia specifikus beállítások
        self.config.update({
            'min_spread_pct': 0.5,     # Minimális spread százalék az arbitrázs indításához
            'max_spread_pct': 5.0,     # Maximális spread százalék (gyanús érték felett nem kereskedünk)
            'min_volume': 0.001,       # Minimális kereskedési mennyiség
            'max_volume': 1.0,         # Maximális kereskedési mennyiség
            'max_slippage_pct': 0.2,   # Maximális megengedett csúszás százalékban
            'execution_timeout': 60,   # Végrehajtási időkorlát másodpercben
            'balance_threshold_pct': 5.0, # Egyenleg küszöb százalék (figyelmeztetés, ha az egyenleg eltér)
            'rebalance_threshold_pct': 10.0, # Újraegyensúlyozási küszöb százalék
            'fee_threshold_pct': 0.3,  # Díj küszöb százalék (az arbitrázs lehetőségnek nagyobbnak kell lennie)
        })
        
        # Arbitrázs stratégia állapot
        self.opportunities = {}  # Arbitrázs lehetőségek: {id: {buy_exchange, sell_exchange, spread_pct, ...}}
        self.active_arbitrages = {}  # Aktív arbitrázsok: {id: {buy_order, sell_order, status, ...}}
        self.exchange_balances = {}  # Tőzsde egyenlegek: {exchange_name: {asset: amount, ...}}
        
    def initialize(self):
        """
        Arbitrázs stratégia inicializálása
        """
        super().initialize()
        self.logger.info("Arbitrázs stratégia inicializálása")
        self.logger.info(f"Tőzsdék: {list(self.exchanges.keys())}")
        
        # Egyenlegek lekérdezése
        self.update_balances()
    
    def update_balances(self):
        """
        Tőzsde egyenlegek frissítése
        """
        for name, exchange in self.exchanges.items():
            try:
                balance = exchange.fetch_balance()
                self.exchange_balances[name] = balance
                self.logger.debug(f"Egyenleg frissítve: {name}")
            except Exception as e:
                self.logger.error(f"Hiba az egyenleg lekérdezése során: {name}, {e}")
    
    def generate_signal(self, data):
        """
        Kereskedési jel generálása az adatok alapján
        
        Args:
            data: Piaci adatok (DataFrame) - ebben az esetben nem használjuk
            
        Returns:
            dict: Kereskedési jel vagy None
        """
        # Arbitrázs lehetőségek keresése
        opportunities = self.find_arbitrage_opportunities()
        
        # Ha nincs lehetőség, nincs jel
        if not opportunities:
            return None
        
        # A legjobb lehetőség kiválasztása
        best_opportunity = max(opportunities, key=lambda x: x['spread_pct'])
        
        # Ellenőrizzük, hogy a spread elég nagy-e
        if best_opportunity['spread_pct'] < self.config['min_spread_pct']:
            return None
        
        # Ellenőrizzük, hogy a spread nem gyanúsan nagy-e
        if best_opportunity['spread_pct'] > self.config['max_spread_pct']:
            self.logger.warning(f"Gyanúsan nagy spread: {best_opportunity['spread_pct']}%, kihagyás")
            return None
        
        # Ellenőrizzük, hogy a díjak után is nyereséges-e
        total_fee_pct = best_opportunity['buy_fee_pct'] + best_opportunity['sell_fee_pct']
        if best_opportunity['spread_pct'] <= total_fee_pct + self.config['fee_threshold_pct']:
            self.logger.debug(f"A spread ({best_opportunity['spread_pct']}%) nem elég nagy a díjak után ({total_fee_pct}%)")
            return None
        
        # Mennyiség kiszámítása
        volume = self.calculate_arbitrage_volume(best_opportunity)
        
        if volume < self.config['min_volume']:
            self.logger.debug(f"A számított mennyiség ({volume}) kisebb, mint a minimum ({self.config['min_volume']})")
            return None
        
        # Arbitrázs azonosító
        arbitrage_id = f"arb_{datetime.now().strftime('%Y%m%d%H%M%S')}_{best_opportunity['buy_exchange']}_{best_opportunity['sell_exchange']}"
        
        # Arbitrázs jel
        signal = {
            'action': 'arbitrage',
            'params': {
                'arbitrage_id': arbitrage_id,
                'buy_exchange': best_opportunity['buy_exchange'],
                'sell_exchange': best_opportunity['sell_exchange'],
                'symbol': self.symbol,
                'volume': volume,
                'buy_price': best_opportunity['buy_price'],
                'sell_price': best_opportunity['sell_price'],
                'spread_pct': best_opportunity['spread_pct'],
                'expected_profit': (best_opportunity['sell_price'] - best_opportunity['buy_price']) * volume,
                'expected_profit_pct': best_opportunity['spread_pct'] - total_fee_pct
            }
        }
        
        # Arbitrázs lehetőség mentése
        self.opportunities[arbitrage_id] = best_opportunity
        best_opportunity['volume'] = volume
        best_opportunity['timestamp'] = datetime.now().timestamp()
        
        return signal
    
    def find_arbitrage_opportunities(self):
        """
        Arbitrázs lehetőségek keresése
        
        Returns:
            list: Arbitrázs lehetőségek listája
        """
        opportunities = []
        
        # Ticker adatok lekérdezése minden tőzsdéről
        tickers = {}
        for name, exchange in self.exchanges.items():
            try:
                ticker = exchange.fetch_ticker(self.symbol)
                tickers[name] = ticker
                self.logger.debug(f"Ticker lekérdezve: {name}, bid: {ticker['bid']}, ask: {ticker['ask']}")
            except Exception as e:
                self.logger.error(f"Hiba a ticker lekérdezése során: {name}, {e}")
        
        # Minden tőzsde pár vizsgálata
        exchange_names = list(tickers.keys())
        for i in range(len(exchange_names)):
            for j in range(i + 1, len(exchange_names)):
                buy_exchange = exchange_names[i]
                sell_exchange = exchange_names[j]
                
                # Ellenőrizzük, hogy mindkét tőzsdén van-e ticker adat
                if buy_exchange not in tickers or sell_exchange not in tickers:
                    continue
                
                buy_ticker = tickers[buy_exchange]
                sell_ticker = tickers[sell_exchange]
                
                # Ellenőrizzük, hogy van-e érvényes ár
                if not buy_ticker['ask'] or not sell_ticker['bid']:
                    continue
                
                # Arbitrázs lehetőség 1: vásárlás az i. tőzsdén, eladás a j. tőzsdén
                if buy_ticker['ask'] < sell_ticker['bid']:
                    spread = sell_ticker['bid'] - buy_ticker['ask']
                    spread_pct = (spread / buy_ticker['ask']) * 100
                    
                    # Díjak lekérdezése
                    buy_fee_pct = self.get_fee(buy_exchange, 'buy')
                    sell_fee_pct = self.get_fee(sell_exchange, 'sell')
                    
                    opportunities.append({
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_price': buy_ticker['ask'],
                        'sell_price': sell_ticker['bid'],
                        'spread': spread,
                        'spread_pct': spread_pct,
                        'buy_volume': buy_ticker['askVolume'] if 'askVolume' in buy_ticker else None,
                        'sell_volume': sell_ticker['bidVolume'] if 'bidVolume' in sell_ticker else None,
                        'buy_fee_pct': buy_fee_pct,
                        'sell_fee_pct': sell_fee_pct
                    })
                
                # Arbitrázs lehetőség 2: vásárlás a j. tőzsdén, eladás az i. tőzsdén
                if sell_ticker['ask'] < buy_ticker['bid']:
                    spread = buy_ticker['bid'] - sell_ticker['ask']
                    spread_pct = (spread / sell_ticker['ask']) * 100
                    
                    # Díjak lekérdezése
                    buy_fee_pct = self.get_fee(sell_exchange, 'buy')
                    sell_fee_pct = self.get_fee(buy_exchange, 'sell')
                    
                    opportunities.append({
                        'buy_exchange': sell_exchange,
                        'sell_exchange': buy_exchange,
                        'buy_price': sell_ticker['ask'],
                        'sell_price': buy_ticker['bid'],
                        'spread': spread,
                        'spread_pct': spread_pct,
                        'buy_volume': sell_ticker['askVolume'] if 'askVolume' in sell_ticker else None,
                        'sell_volume': buy_ticker['bidVolume'] if 'bidVolume' in buy_ticker else None,
                        'buy_fee_pct': buy_fee_pct,
                        'sell_fee_pct': sell_fee_pct
                    })
        
        return opportunities
    
    def get_fee(self, exchange_name, side):
        """
        Kereskedési díj lekérdezése
        
        Args:
            exchange_name: Tőzsde neve
            side: Kereskedési oldal ('buy' vagy 'sell')
            
        Returns:
            float: Díj százalékban
        """
        try:
            exchange = self.exchanges[exchange_name]
            markets = exchange.load_markets()
            market = markets[self.symbol]
            
            # Díj lekérdezése
            if 'taker' in market:
                fee = market['taker'] * 100  # Százalékra konvertálás
            else:
                # Alapértelmezett díj
                fee = 0.1  # 0.1%
            
            return fee
        except Exception as e:
            self.logger.error(f"Hiba a díj lekérdezése során: {exchange_name}, {e}")
            # Alapértelmezett díj
            return 0.1  # 0.1%
    
    def calculate_arbitrage_volume(self, opportunity):
        """
        Arbitrázs mennyiség kiszámítása
        
        Args:
            opportunity: Arbitrázs lehetőség
            
        Returns:
            float: Kereskedési mennyiség
        """
        # Egyenlegek ellenőrzése
        buy_exchange = opportunity['buy_exchange']
        sell_exchange = opportunity['sell_exchange']
        
        # Alap eszköz és jegyzett eszköz (pl. BTC és USDT a BTC/USDT párban)
        symbol_parts = self.symbol.split('/')
        base_asset = symbol_parts[0]
        quote_asset = symbol_parts[1]
        
        # Egyenlegek lekérdezése
        self.update_balances()
        
        # Vásárláshoz szükséges egyenleg (jegyzett eszköz, pl. USDT)
        buy_balance = 0
        if buy_exchange in self.exchange_balances:
            exchange_balance = self.exchange_balances[buy_exchange]
            if 'free' in exchange_balance and quote_asset in exchange_balance['free']:
                buy_balance = exchange_balance['free'][quote_asset]
        
        # Eladáshoz szükséges egyenleg (alap eszköz, pl. BTC)
        sell_balance = 0
        if sell_exchange in self.exchange_balances:
            exchange_balance = self.exchange_balances[sell_exchange]
            if 'free' in exchange_balance and base_asset in exchange_balance['free']:
                sell_balance = exchange_balance['free'][base_asset]
        
        # Mennyiség kiszámítása a vásárlási egyenleg alapján
        buy_volume = buy_balance / opportunity['buy_price']
        
        # Mennyiség kiszámítása az eladási egyenleg alapján
        sell_volume = sell_balance
        
        # A kisebb mennyiséget választjuk
        volume = min(buy_volume, sell_volume)
        
        # Limitáljuk a mennyiséget
        volume = min(volume, self.config['max_volume'])
        
        # Kerekítés a tőzsde által támogatott pontosságra
        try:
            exchange = self.exchanges[buy_exchange]
            markets = exchange.load_markets()
            market = markets[self.symbol]
            
            # Mennyiség pontosság
            precision = market['precision']['amount']
            volume = round(volume, precision)
        except Exception as e:
            self.logger.error(f"Hiba a mennyiség kerekítése során: {e}")
            # Alapértelmezett kerekítés
            volume = round(volume, 8)
        
        return volume
    
    def execute_arbitrage(self, signal):
        """
        Arbitrázs végrehajtása
        
        Args:
            signal: Arbitrázs jel
            
        Returns:
            dict: Végrehajtás eredménye
        """
        params = signal['params']
        arbitrage_id = params['arbitrage_id']
        buy_exchange_name = params['buy_exchange']
        sell_exchange_name = params['sell_exchange']
        symbol = params['symbol']
        volume = params['volume']
        
        self.logger.info(f"Arbitrázs végrehajtása: {arbitrage_id}, {buy_exchange_name} -> {sell_exchange_name}, {volume} {symbol}")
        
        # Tőzsdék lekérdezése
        buy_exchange = self.exchanges[buy_exchange_name]
        sell_exchange = self.exchanges[sell_exchange_name]
        
        # Aktív arbitrázs létrehozása
        self.active_arbitrages[arbitrage_id] = {
            'id': arbitrage_id,
            'buy_exchange': buy_exchange_name,
            'sell_exchange': sell_exchange_name,
            'symbol': symbol,
            'volume': volume,
            'status': 'pending',
            'start_time': datetime.now().timestamp(),
            'buy_order': None,
            'sell_order': None,
            'buy_execution': None,
            'sell_execution': None,
            'profit': None,
            'profit_pct': None,
            'error': None
        }
        
        try:
            # Vásárlási megbízás
            buy_order = buy_exchange.create_market_buy_order(symbol, volume)
            self.active_arbitrages[arbitrage_id]['buy_order'] = buy_order
            self.active_arbitrages[arbitrage_id]['status'] = 'buy_executed'
            
            # Eladási megbízás
            sell_order = sell_exchange.create_market_sell_order(symbol, volume)
            self.active_arbitrages[arbitrage_id]['sell_order'] = sell_order
            self.active_arbitrages[arbitrage_id]['status'] = 'sell_executed'
            
            # Végrehajtás ellenőrzése
            buy_execution = buy_exchange.fetch_order(buy_order['id'], symbol)
            sell_execution = sell_exchange.fetch_order(sell_order['id'], symbol)
            
            self.active_arbitrages[arbitrage_id]['buy_execution'] = buy_execution
            self.active_arbitrages[arbitrage_id]['sell_execution'] = sell_execution
            
            # Profit számítása
            buy_cost = buy_execution['cost']
            sell_cost = sell_execution['cost']
            profit = sell_cost - buy_cost
            profit_pct = (profit / buy_cost) * 100
            
            self.active_arbitrages[arbitrage_id]['profit'] = profit
            self.active_arbitrages[arbitrage_id]['profit_pct'] = profit_pct
            self.active_arbitrages[arbitrage_id]['status'] = 'completed'
            
            self.logger.info(f"Arbitrázs végrehajtva: {arbitrage_id}, profit: {profit}, profit%: {profit_pct}%")
            
            # Teljesítmény frissítése
            self.update_performance({
                'profit': profit,
                'drawdown': 0
            })
            
            return {
                'success': True,
                'arbitrage_id': arbitrage_id,
                'profit': profit,
                'profit_pct': profit_pct
            }
            
        except Exception as e:
            self.logger.error(f"Hiba az arbitrázs végrehajtása során: {arbitrage_id}, {e}")
            self.active_arbitrages[arbitrage_id]['status'] = 'error'
            self.active_arbitrages[arbitrage_id]['error'] = str(e)
            
            return {
                'success': False,
                'arbitrage_id': arbitrage_id,
                'error': str(e)
            }
    
    def check_balance_discrepancies(self):
        """
        Egyenleg eltérések ellenőrzése
        
        Returns:
            list: Egyenleg eltérések listája
        """
        discrepancies = []
        
        # Egyenlegek frissítése
        self.update_balances()
        
        # Alap eszköz és jegyzett eszköz (pl. BTC és USDT a BTC/USDT párban)
        symbol_parts = self.symbol.split('/')
        base_asset = symbol_parts[0]
        quote_asset = symbol_parts[1]
        
        # Egyenlegek összegyűjtése
        base_balances = {}
        quote_balances = {}
        
        for name, balance in self.exchange_balances.items():
            if 'free' in balance:
                if base_asset in balance['free']:
                    base_balances[name] = balance['free'][base_asset]
                if quote_asset in balance['free']:
                    quote_balances[name] = balance['free'][quote_asset]
        
        # Átlagos egyenlegek
        if base_balances:
            avg_base_balance = sum(base_balances.values()) / len(base_balances)
        else:
            avg_base_balance = 0
        
        if quote_balances:
            avg_quote_balance = sum(quote_balances.values()) / len(quote_balances)
        else:
            avg_quote_balance = 0
        
        # Eltérések ellenőrzése
        for name, balance in base_balances.items():
            if avg_base_balance > 0:
                diff_pct = abs(balance - avg_base_balance) / avg_base_balance * 100
                if diff_pct > self.config['balance_threshold_pct']:
                    discrepancies.append({
                        'exchange': name,
                        'asset': base_asset,
                        'balance': balance,
                        'avg_balance': avg_base_balance,
                        'diff_pct': diff_pct
                    })
        
        for name, balance in quote_balances.items():
            if avg_quote_balance > 0:
                diff_pct = abs(balance - avg_quote_balance) / avg_quote_balance * 100
                if diff_pct > self.config['balance_threshold_pct']:
                    discrepancies.append({
                        'exchange': name,
                        'asset': quote_asset,
                        'balance': balance,
                        'avg_balance': avg_quote_balance,
                        'diff_pct': diff_pct
                    })
        
        return discrepancies
    
    def rebalance_exchanges(self):
        """
        Tőzsdék közötti egyenleg újraegyensúlyozása
        
        Returns:
            dict: Újraegyensúlyozás eredménye
        """
        # Egyenleg eltérések ellenőrzése
        discrepancies = self.check_balance_discrepancies()
        
        if not discrepancies:
            return {'success': True, 'message': 'Nincs szükség újraegyensúlyozásra'}
        
        # Alap eszköz és jegyzett eszköz (pl. BTC és USDT a BTC/USDT párban)
        symbol_parts = self.symbol.split('/')
        base_asset = symbol_parts[0]
        quote_asset = symbol_parts[1]
        
        # Újraegyensúlyozás végrehajtása
        results = []
        
        for discrepancy in discrepancies:
            if discrepancy['diff_pct'] > self.config['rebalance_threshold_pct']:
                exchange_name = discrepancy['exchange']
                asset = discrepancy['asset']
                current_balance = discrepancy['balance']
                target_balance = discrepancy['avg_balance']
                
                # Csak akkor egyensúlyozunk, ha jelentős az eltérés
                if current_balance > target_balance * 1.1:
                    # Túl sok az egyenleg, át kell vinni másik tőzsdére
                    amount_to_transfer = current_balance - target_balance
                    
                    # Célpont tőzsde kiválasztása (a legalacsonyabb egyenleggel rendelkező)
                    target_exchange = None
                    min_balance = float('inf')
                    
                    for name, balance in self.exchange_balances.items():
                        if name != exchange_name and 'free' in balance and asset in balance['free']:
                            if balance['free'][asset] < min_balance:
                                min_balance = balance['free'][asset]
                                target_exchange = name
                    
                    if target_exchange:
                        try:
                            # Kivonás a forrás tőzsdéről
                            exchange = self.exchanges[exchange_name]
                            withdrawal = exchange.withdraw(asset, amount_to_transfer, self.exchanges[target_exchange].deposit_address[asset])
                            
                            results.append({
                                'success': True,
                                'source_exchange': exchange_name,
                                'target_exchange': target_exchange,
                                'asset': asset,
                                'amount': amount_to_transfer,
                                'withdrawal_id': withdrawal['id'] if 'id' in withdrawal else None
                            })
                            
                        except Exception as e:
                            self.logger.error(f"Hiba az újraegyensúlyozás során: {exchange_name} -> {target_exchange}, {asset}, {e}")
                            
                            results.append({
                                'success': False,
                                'source_exchange': exchange_name,
                                'target_exchange': target_exchange,
                                'asset': asset,
                                'amount': amount_to_transfer,
                                'error': str(e)
                            })
        
        return {
            'success': True,
            'discrepancies': discrepancies,
            'rebalance_results': results
        }
    
    def get_active_arbitrages(self):
        """
        Aktív arbitrázsok lekérdezése
        
        Returns:
            dict: Aktív arbitrázsok
        """
        return self.active_arbitrages
    
    def get_arbitrage_opportunities(self):
        """
        Arbitrázs lehetőségek lekérdezése
        
        Returns:
            dict: Arbitrázs lehetőségek
        """
        return self.opportunities
