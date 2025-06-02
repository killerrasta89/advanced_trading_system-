"""
Risk Calculator - Számítja a különböző kockázati metrikákat a kereskedési rendszerhez.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('risk_calculator')

class RiskCalculator:
    """
    Számítja a különböző kockázati metrikákat a kereskedési rendszerhez,
    beleértve a Value at Risk (VaR), Expected Shortfall (ES), Sharpe-ráta,
    Sortino-ráta, és egyéb teljesítmény mutatókat.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a RiskCalculator-t a megadott konfigurációval.
        
        Args:
            config: A RiskCalculator konfigurációja
        """
        self.config = config
        
        # Konfigurációs beállítások
        self.var_confidence_level = config.get('var_confidence_level', 0.95)  # VaR konfidencia szint
        self.risk_free_rate = config.get('risk_free_rate', 0.02)  # Kockázatmentes hozam (éves)
        self.drawdown_window = config.get('drawdown_window', 252)  # Drawdown számítási ablak (kereskedési napok)
        
        # RPI4 optimalizáció
        self.max_lookback = config.get('max_lookback', 252)  # Korlátozott visszatekintés
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        
        logger.info("RiskCalculator initialized")
    
    def calculate_var(self, returns: List[float], method: str = 'historical') -> Dict:
        """
        Kiszámítja a Value at Risk (VaR) értékét.
        
        Args:
            returns: Hozamok listája
            method: VaR számítási módszer ('historical', 'parametric', 'monte_carlo')
            
        Returns:
            Dict: A VaR értékek
        """
        try:
            if not returns:
                logger.warning("Empty returns list")
                return {'var': 0.0, 'error': 'Empty returns list'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(returns), self.max_lookback)
            returns = returns[-lookback:]
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                method = 'historical'  # Csak a historical módszert használja
            
            if method == 'historical':
                # Historical VaR
                var = self._calculate_historical_var(returns)
            elif method == 'parametric':
                # Parametric VaR
                var = self._calculate_parametric_var(returns)
            elif method == 'monte_carlo':
                # Monte Carlo VaR
                var = self._calculate_monte_carlo_var(returns)
            else:
                logger.warning(f"Unknown VaR method: {method}")
                var = self._calculate_historical_var(returns)
            
            return {
                'var': var,
                'method': method,
                'confidence_level': self.var_confidence_level,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating VaR: {str(e)}")
            return {'var': 0.0, 'error': str(e)}
    
    def _calculate_historical_var(self, returns: List[float]) -> float:
        """
        Kiszámítja a Historical VaR értékét.
        
        Args:
            returns: Hozamok listája
            
        Returns:
            float: A Historical VaR érték
        """
        try:
            # Rendezi a hozamokat növekvő sorrendbe
            sorted_returns = sorted(returns)
            
            # Meghatározza a percentilis indexét
            index = int(len(sorted_returns) * (1 - self.var_confidence_level))
            
            # Korlátozza az indexet
            index = max(0, min(len(sorted_returns) - 1, index))
            
            # Historical VaR
            var = -sorted_returns[index]
            
            return var
        
        except Exception as e:
            logger.error(f"Error calculating Historical VaR: {str(e)}")
            return 0.0
    
    def _calculate_parametric_var(self, returns: List[float]) -> float:
        """
        Kiszámítja a Parametric VaR értékét.
        
        Args:
            returns: Hozamok listája
            
        Returns:
            float: A Parametric VaR érték
        """
        try:
            # Átlag és szórás
            mean = np.mean(returns)
            std = np.std(returns)
            
            # Z-érték a konfidencia szinthez
            z = {
                0.90: 1.282,
                0.95: 1.645,
                0.99: 2.326
            }.get(self.var_confidence_level, 1.645)
            
            # Parametric VaR
            var = -(mean + z * std)
            
            return var
        
        except Exception as e:
            logger.error(f"Error calculating Parametric VaR: {str(e)}")
            return 0.0
    
    def _calculate_monte_carlo_var(self, returns: List[float]) -> float:
        """
        Kiszámítja a Monte Carlo VaR értékét.
        
        Args:
            returns: Hozamok listája
            
        Returns:
            float: A Monte Carlo VaR érték
        """
        try:
            # Átlag és szórás
            mean = np.mean(returns)
            std = np.std(returns)
            
            # Monte Carlo szimuláció
            np.random.seed(42)  # Reprodukálhatóság
            num_simulations = 10000
            simulated_returns = np.random.normal(mean, std, num_simulations)
            
            # Rendezi a szimulált hozamokat
            sorted_returns = np.sort(simulated_returns)
            
            # Meghatározza a percentilis indexét
            index = int(num_simulations * (1 - self.var_confidence_level))
            
            # Korlátozza az indexet
            index = max(0, min(num_simulations - 1, index))
            
            # Monte Carlo VaR
            var = -sorted_returns[index]
            
            return var
        
        except Exception as e:
            logger.error(f"Error calculating Monte Carlo VaR: {str(e)}")
            return 0.0
    
    def calculate_expected_shortfall(self, returns: List[float]) -> Dict:
        """
        Kiszámítja az Expected Shortfall (ES) értékét.
        
        Args:
            returns: Hozamok listája
            
        Returns:
            Dict: Az ES értékek
        """
        try:
            if not returns:
                logger.warning("Empty returns list")
                return {'es': 0.0, 'error': 'Empty returns list'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(returns), self.max_lookback)
            returns = returns[-lookback:]
            
            # Rendezi a hozamokat növekvő sorrendbe
            sorted_returns = sorted(returns)
            
            # Meghatározza a percentilis indexét
            index = int(len(sorted_returns) * (1 - self.var_confidence_level))
            
            # Korlátozza az indexet
            index = max(0, min(len(sorted_returns) - 1, index))
            
            # Expected Shortfall (átlag a VaR-nál rosszabb hozamokból)
            es = -np.mean(sorted_returns[:index+1])
            
            return {
                'es': es,
                'confidence_level': self.var_confidence_level,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating Expected Shortfall: {str(e)}")
            return {'es': 0.0, 'error': str(e)}
    
    def calculate_sharpe_ratio(self, returns: List[float], annualized: bool = True) -> Dict:
        """
        Kiszámítja a Sharpe-rátát.
        
        Args:
            returns: Hozamok listája
            annualized: Évesített Sharpe-ráta számítása
            
        Returns:
            Dict: A Sharpe-ráta értékek
        """
        try:
            if not returns:
                logger.warning("Empty returns list")
                return {'sharpe_ratio': 0.0, 'error': 'Empty returns list'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(returns), self.max_lookback)
            returns = returns[-lookback:]
            
            # Átlag és szórás
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                logger.warning("Zero standard deviation")
                return {'sharpe_ratio': 0.0, 'error': 'Zero standard deviation'}
            
            # Napi kockázatmentes hozam
            daily_risk_free = self.risk_free_rate / 252
            
            # Sharpe-ráta
            sharpe = (mean_return - daily_risk_free) / std_return
            
            # Évesített Sharpe-ráta
            if annualized:
                sharpe *= np.sqrt(252)
            
            return {
                'sharpe_ratio': sharpe,
                'annualized': annualized,
                'risk_free_rate': self.risk_free_rate,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {str(e)}")
            return {'sharpe_ratio': 0.0, 'error': str(e)}
    
    def calculate_sortino_ratio(self, returns: List[float], annualized: bool = True) -> Dict:
        """
        Kiszámítja a Sortino-rátát.
        
        Args:
            returns: Hozamok listája
            annualized: Évesített Sortino-ráta számítása
            
        Returns:
            Dict: A Sortino-ráta értékek
        """
        try:
            if not returns:
                logger.warning("Empty returns list")
                return {'sortino_ratio': 0.0, 'error': 'Empty returns list'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(returns), self.max_lookback)
            returns = returns[-lookback:]
            
            # Átlag
            mean_return = np.mean(returns)
            
            # Napi kockázatmentes hozam
            daily_risk_free = self.risk_free_rate / 252
            
            # Negatív hozamok
            negative_returns = [r for r in returns if r < 0]
            
            if not negative_returns:
                logger.warning("No negative returns")
                return {'sortino_ratio': float('inf'), 'error': 'No negative returns'}
            
            # Negatív hozamok szórása (downside deviation)
            downside_deviation = np.std(negative_returns)
            
            if downside_deviation == 0:
                logger.warning("Zero downside deviation")
                return {'sortino_ratio': 0.0, 'error': 'Zero downside deviation'}
            
            # Sortino-ráta
            sortino = (mean_return - daily_risk_free) / downside_deviation
            
            # Évesített Sortino-ráta
            if annualized:
                sortino *= np.sqrt(252)
            
            return {
                'sortino_ratio': sortino,
                'annualized': annualized,
                'risk_free_rate': self.risk_free_rate,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {str(e)}")
            return {'sortino_ratio': 0.0, 'error': str(e)}
    
    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict:
        """
        Kiszámítja a maximális drawdown-t.
        
        Args:
            equity_curve: Tőkegörbe (equity curve) listája
            
        Returns:
            Dict: A maximális drawdown értékek
        """
        try:
            if not equity_curve:
                logger.warning("Empty equity curve")
                return {'max_drawdown': 0.0, 'error': 'Empty equity curve'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(equity_curve), self.drawdown_window)
            equity_curve = equity_curve[-lookback:]
            
            # Maximális drawdown számítása
            max_dd = 0.0
            peak = equity_curve[0]
            peak_idx = 0
            trough = equity_curve[0]
            trough_idx = 0
            
            for i, value in enumerate(equity_curve):
                if value > peak:
                    peak = value
                    peak_idx = i
                    
                    # Új csúcs esetén újraindítja a trough keresést
                    trough = value
                    trough_idx = i
                
                if value < trough:
                    trough = value
                    trough_idx = i
                    
                    # Számítja a drawdown-t
                    dd = (trough - peak) / peak
                    
                    if dd < max_dd:
                        max_dd = dd
                        max_peak_idx = peak_idx
                        max_trough_idx = trough_idx
            
            # Abszolút érték (pozitív szám)
            max_dd = abs(max_dd)
            
            return {
                'max_drawdown': max_dd,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {str(e)}")
            return {'max_drawdown': 0.0, 'error': str(e)}
    
    def calculate_calmar_ratio(self, returns: List[float], equity_curve: List[float], annualized: bool = True) -> Dict:
        """
        Kiszámítja a Calmar-rátát.
        
        Args:
            returns: Hozamok listája
            equity_curve: Tőkegörbe (equity curve) listája
            annualized: Évesített Calmar-ráta számítása
            
        Returns:
            Dict: A Calmar-ráta értékek
        """
        try:
            if not returns or not equity_curve:
                logger.warning("Empty returns or equity curve")
                return {'calmar_ratio': 0.0, 'error': 'Empty returns or equity curve'}
            
            # Korlátozza a visszatekintést
            lookback = min(len(returns), self.max_lookback)
            returns = returns[-lookback:]
            
            # Átlag hozam
            mean_return = np.mean(returns)
            
            # Évesített hozam
            if annualized:
                annual_return = mean_return * 252
            else:
                annual_return = mean_return
            
            # Maximális drawdown
            max_dd_result = self.calculate_max_drawdown(equity_curve)
            max_dd = max_dd_result.get('max_drawdown', 0.0)
            
            if max_dd == 0:
                logger.warning("Zero max drawdown")
                return {'calmar_ratio': float('inf'), 'error': 'Zero max drawdown'}
            
            # Calmar-ráta
            calmar = annual_return / max_dd
            
            return {
                'calmar_ratio': calmar,
                'annualized': annualized,
                'max_drawdown': max_dd,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating Calmar ratio: {str(e)}")
            return {'calmar_ratio': 0.0, 'error': str(e)}
    
    def calculate_win_rate(self, trades: List[Dict]) -> Dict:
        """
        Kiszámítja a nyerési arányt.
        
        Args:
            trades: Kereskedések listája
            
        Returns:
            Dict: A nyerési arány értékek
        """
        try:
            if not trades:
                logger.warning("Empty trades list")
                return {'win_rate': 0.0, 'error': 'Empty trades list'}
            
            # Nyertes és vesztes kereskedések száma
            winning_trades = [trade for trade in trades if trade.get('pnl', 0.0) > 0]
            losing_trades = [trade for trade in trades if trade.get('pnl', 0.0) <= 0]
            
            # Nyerési arány
            win_rate = len(winning_trades) / len(trades)
            
            # Átlagos nyereség és veszteség
            avg_win = np.mean([trade.get('pnl', 0.0) for trade in winning_trades]) if winning_trades else 0.0
            avg_loss = np.mean([trade.get('pnl', 0.0) for trade in losing_trades]) if losing_trades else 0.0
            
            # Profit faktor
            profit_factor = abs(sum([trade.get('pnl', 0.0) for trade in winning_trades]) / 
                               sum([trade.get('pnl', 0.0) for trade in losing_trades])) if losing_trades and sum([trade.get('pnl', 0.0) for trade in losing_trades]) != 0 else float('inf')
            
            return {
                'win_rate': win_rate,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'total_trades': len(trades),
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'profit_factor': profit_factor,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating win rate: {str(e)}")
            return {'win_rate': 0.0, 'error': str(e)}
    
    def calculate_risk_metrics(self, returns: List[float], equity_curve: List[float], trades: List[Dict]) -> Dict:
        """
        Kiszámítja az összes kockázati metrikát.
        
        Args:
            returns: Hozamok listája
            equity_curve: Tőkegörbe (equity curve) listája
            trades: Kereskedések listája
            
        Returns:
            Dict: Az összes kockázati metrika
        """
        try:
            # Value at Risk
            var_result = self.calculate_var(returns)
            
            # Expected Shortfall
            es_result = self.calculate_expected_shortfall(returns)
            
            # Sharpe-ráta
            sharpe_result = self.calculate_sharpe_ratio(returns)
            
            # Sortino-ráta
            sortino_result = self.calculate_sortino_ratio(returns)
            
            # Maximális drawdown
            max_dd_result = self.calculate_max_drawdown(equity_curve)
            
            # Calmar-ráta
            calmar_result = self.calculate_calmar_ratio(returns, equity_curve)
            
            # Nyerési arány
            win_rate_result = self.calculate_win_rate(trades)
            
            # Összesített eredmények
            return {
                'var': var_result.get('var', 0.0),
                'es': es_result.get('es', 0.0),
                'sharpe_ratio': sharpe_result.get('sharpe_ratio', 0.0),
                'sortino_ratio': sortino_result.get('sortino_ratio', 0.0),
                'max_drawdown': max_dd_result.get('max_drawdown', 0.0),
                'calmar_ratio': calmar_result.get('calmar_ratio', 0.0),
                'win_rate': win_rate_result.get('win_rate', 0.0),
                'profit_factor': win_rate_result.get('profit_factor', 0.0),
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            return {'error': str(e)}
