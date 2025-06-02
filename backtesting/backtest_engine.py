"""
Backtest Engine - Backtesting motor
"""
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging

class BacktestEngine:
    """
    Backtesting motor a stratégiák teszteléséhez
    """
    
    def __init__(self, strategy_type, symbol, timeframe, start_date, end_date, initial_balance=1000.0, commission=0.1):
        """
        Inicializálás
        
        Args:
            strategy_type (str): Stratégia típusa
            symbol (str): Szimbólum
            timeframe (str): Időkeret
            start_date (datetime): Kezdő dátum
            end_date (datetime): Végső dátum
            initial_balance (float): Kezdő egyenleg
            commission (float): Jutalék százalékban
        """
        self.strategy_type = strategy_type
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.commission = commission
        
        self.data = None
        self.strategy = None
        self.results = None
        self.trades = []
        
        self.logger = logging.getLogger(__name__)
    
    def load_data(self):
        """
        Adatok betöltése
        
        Returns:
            bool: Sikeres-e a betöltés
        """
        try:
            # Adatok elérési útja
            data_file = os.path.join('data', 'price_data', f'{self.symbol.replace("/", "_")}_{self.timeframe}.csv')
            
            if not os.path.exists(data_file):
                self.logger.error(f"Adatfájl nem található: {data_file}")
                return False
            
            # Adatok betöltése
            self.data = pd.read_csv(data_file)
            
            # Dátum oszlop konvertálása
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            
            # Adatok szűrése a megadott időszakra
            self.data = self.data[(self.data['timestamp'] >= self.start_date) & (self.data['timestamp'] <= self.end_date)]
            
            if len(self.data) == 0:
                self.logger.error(f"Nincs adat a megadott időszakra: {self.start_date} - {self.end_date}")
                return False
            
            self.logger.info(f"Adatok betöltve: {len(self.data)} sor")
            return True
        
        except Exception as e:
            self.logger.error(f"Hiba az adatok betöltése során: {e}")
            return False
    
    def initialize_strategy(self, config=None):
        """
        Stratégia inicializálása
        
        Args:
            config (dict): Stratégia konfiguráció
            
        Returns:
            bool: Sikeres-e az inicializálás
        """
        try:
            # Stratégia importálása
            if self.strategy_type == 'grid_trading':
                from strategies.grid_trading import GridTradingStrategy
                self.strategy = GridTradingStrategy(config)
            elif self.strategy_type == 'dca_strategy':
                from strategies.dca_strategy import DCAStrategy
                self.strategy = DCAStrategy(config)
            elif self.strategy_type == 'momentum_strategy':
                from strategies.momentum_strategy import MomentumStrategy
                self.strategy = MomentumStrategy(config)
            elif self.strategy_type == 'mean_reversion':
                from strategies.mean_reversion import MeanReversionStrategy
                self.strategy = MeanReversionStrategy(config)
            elif self.strategy_type == 'arbitrage_strategy':
                from strategies.arbitrage_strategy import ArbitrageStrategy
                self.strategy = ArbitrageStrategy(config)
            else:
                self.logger.error(f"Nem támogatott stratégia típus: {self.strategy_type}")
                return False
            
            self.logger.info(f"Stratégia inicializálva: {self.strategy_type}")
            return True
        
        except Exception as e:
            self.logger.error(f"Hiba a stratégia inicializálása során: {e}")
            return False
    
    def run_backtest(self):
        """
        Backtest futtatása
        
        Returns:
            dict: Backtest eredmények
        """
        try:
            if self.data is None:
                self.logger.error("Nincsenek betöltve adatok")
                return None
            
            if self.strategy is None:
                self.logger.error("Nincs inicializálva stratégia")
                return None
            
            # Backtest futtatása
            self.logger.info("Backtest futtatása...")
            
            # Kezdő egyenleg
            balance = self.initial_balance
            equity = balance
            
            # Eredmények inicializálása
            results = {
                'initial_balance': self.initial_balance,
                'final_balance': 0.0,
                'profit_loss': 0.0,
                'profit_loss_pct': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_profit': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'equity_curve': [],
                'drawdown_curve': [],
                'trades': []
            }
            
            # Egyenleg és drawdown görbék
            equity_curve = []
            drawdown_curve = []
            max_equity = balance
            
            # Kereskedések
            trades = []
            
            # Backtest futtatása
            for i, row in self.data.iterrows():
                # Stratégia futtatása az aktuális adatokon
                signals = self.strategy.generate_signals(row)
                
                # Kereskedések végrehajtása
                for signal in signals:
                    # Kereskedés létrehozása
                    trade = {
                        'timestamp': row['timestamp'],
                        'symbol': self.symbol,
                        'side': signal['side'],
                        'price': row['close'],
                        'amount': signal['amount'],
                        'commission': signal['amount'] * row['close'] * self.commission / 100,
                        'profit_loss': 0.0,
                        'profit_loss_pct': 0.0,
                        'balance_after': 0.0,
                        'equity_after': 0.0
                    }
                    
                    # Kereskedés végrehajtása
                    if signal['side'] == 'buy':
                        # Vásárlás
                        cost = trade['amount'] * trade['price'] + trade['commission']
                        balance -= cost
                    else:
                        # Eladás
                        revenue = trade['amount'] * trade['price'] - trade['commission']
                        balance += revenue
                        
                        # Profit/veszteség számítása
                        trade['profit_loss'] = revenue - (trade['amount'] * signal['entry_price'])
                        trade['profit_loss_pct'] = trade['profit_loss'] / (trade['amount'] * signal['entry_price']) * 100
                    
                    # Egyenleg és equity frissítése
                    trade['balance_after'] = balance
                    equity = balance
                    trade['equity_after'] = equity
                    
                    # Kereskedés hozzáadása
                    trades.append(trade)
                
                # Egyenleg görbe frissítése
                equity_curve.append({
                    'timestamp': row['timestamp'],
                    'equity': equity
                })
                
                # Max equity frissítése
                if equity > max_equity:
                    max_equity = equity
                
                # Drawdown számítása
                drawdown = max_equity - equity
                drawdown_pct = drawdown / max_equity * 100
                
                # Drawdown görbe frissítése
                drawdown_curve.append({
                    'timestamp': row['timestamp'],
                    'drawdown': drawdown,
                    'drawdown_pct': drawdown_pct
                })
            
            # Eredmények számítása
            results['final_balance'] = balance
            results['profit_loss'] = balance - self.initial_balance
            results['profit_loss_pct'] = results['profit_loss'] / self.initial_balance * 100
            
            # Max drawdown
            max_drawdown_record = max(drawdown_curve, key=lambda x: x['drawdown'])
            results['max_drawdown'] = max_drawdown_record['drawdown']
            results['max_drawdown_pct'] = max_drawdown_record['drawdown_pct']
            
            # Kereskedési statisztikák
            results['total_trades'] = len(trades)
            results['winning_trades'] = len([t for t in trades if t['profit_loss'] > 0])
            results['losing_trades'] = len([t for t in trades if t['profit_loss'] < 0])
            
            if results['total_trades'] > 0:
                results['win_rate'] = results['winning_trades'] / results['total_trades'] * 100
            
            # Átlagos profit és veszteség
            winning_trades = [t for t in trades if t['profit_loss'] > 0]
            losing_trades = [t for t in trades if t['profit_loss'] < 0]
            
            if len(winning_trades) > 0:
                results['avg_profit'] = sum([t['profit_loss'] for t in winning_trades]) / len(winning_trades)
            
            if len(losing_trades) > 0:
                results['avg_loss'] = sum([t['profit_loss'] for t in losing_trades]) / len(losing_trades)
            
            # Profit faktor
            total_profit = sum([t['profit_loss'] for t in winning_trades])
            total_loss = sum([t['profit_loss'] for t in losing_trades])
            
            if total_loss != 0:
                results['profit_factor'] = abs(total_profit / total_loss)
            
            # Görbék
            results['equity_curve'] = equity_curve
            results['drawdown_curve'] = drawdown_curve
            results['trades'] = trades
            
            # Eredmények mentése
            self.results = results
            self.trades = trades
            
            self.logger.info(f"Backtest befejezve. Eredmény: {results['profit_loss_pct']:.2f}%")
            
            return results
        
        except Exception as e:
            self.logger.error(f"Hiba a backtest futtatása során: {e}")
            return None
    
    def save_results(self, filename=None):
        """
        Eredmények mentése
        
        Args:
            filename (str): Fájlnév
            
        Returns:
            bool: Sikeres-e a mentés
        """
        try:
            if self.results is None:
                self.logger.error("Nincsenek eredmények a mentéshez")
                return False
            
            # Eredmények könyvtár létrehozása
            results_dir = os.path.join('data', 'backtest_results')
            os.makedirs(results_dir, exist_ok=True)
            
            # Fájlnév generálása, ha nincs megadva
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{self.strategy_type}_{self.symbol.replace('/', '_')}_{self.timeframe}_{timestamp}.json"
            
            # Teljes elérési út
            filepath = os.path.join(results_dir, filename)
            
            # Eredmények mentése
            with open(filepath, 'w') as f:
                json.dump(self.results, f, indent=4, default=str)
            
            self.logger.info(f"Eredmények mentve: {filepath}")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Hiba az eredmények mentése során: {e}")
            return False
