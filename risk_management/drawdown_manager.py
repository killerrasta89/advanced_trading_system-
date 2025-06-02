"""
Drawdown Manager - Kezeli és korlátozza a drawdown-t a kereskedési rendszerben.
"""
import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('drawdown_manager')

class DrawdownManager:
    """
    Kezeli és korlátozza a drawdown-t a kereskedési rendszerben,
    beleértve a maximális drawdown korlátozást, fokozatos pozíció
    méret csökkentést és automatikus helyreállítási mechanizmusokat.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a DrawdownManager-t a megadott konfigurációval.
        
        Args:
            config: A DrawdownManager konfigurációja
        """
        self.config = config
        
        # Konfigurációs beállítások
        self.max_drawdown_limit = config.get('max_drawdown_limit', 0.2)  # 20% maximális drawdown
        self.warning_drawdown_level = config.get('warning_drawdown_level', 0.1)  # 10% figyelmeztető szint
        self.position_size_reduction_levels = config.get('position_size_reduction_levels', {
            0.05: 0.9,  # 5% drawdown: 90% pozíció méret
            0.1: 0.75,  # 10% drawdown: 75% pozíció méret
            0.15: 0.5,  # 15% drawdown: 50% pozíció méret
            0.2: 0.0    # 20% drawdown: 0% pozíció méret (kereskedés leállítása)
        })
        self.recovery_threshold = config.get('recovery_threshold', 0.05)  # 5% helyreállítás a csúcstól
        
        # Állapot változók
        self.current_drawdown = 0.0
        self.peak_equity = 0.0
        self.is_trading_halted = False
        self.last_update_time = None
        
        # RPI4 optimalizáció
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        
        logger.info("DrawdownManager initialized")
    
    def update(self, current_equity: float) -> Dict:
        """
        Frissíti a drawdown állapotot az aktuális tőke alapján.
        
        Args:
            current_equity: Az aktuális tőke értéke
            
        Returns:
            Dict: A drawdown állapot
        """
        try:
            if current_equity <= 0:
                logger.warning(f"Invalid equity value: {current_equity}")
                return {
                    'current_drawdown': self.current_drawdown,
                    'peak_equity': self.peak_equity,
                    'is_trading_halted': self.is_trading_halted,
                    'error': 'Invalid equity value'
                }
            
            # Első frissítés
            if self.peak_equity == 0:
                self.peak_equity = current_equity
                self.current_drawdown = 0.0
                self.is_trading_halted = False
            
            # Új csúcs
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
                self.current_drawdown = 0.0
                
                # Helyreállítás ellenőrzése
                if self.is_trading_halted:
                    recovery_ratio = (current_equity - self.peak_equity * (1 - self.max_drawdown_limit)) / (self.peak_equity * self.recovery_threshold)
                    
                    if recovery_ratio >= 1.0:
                        logger.info(f"Trading resumed after recovery. Current equity: {current_equity}, Peak equity: {self.peak_equity}")
                        self.is_trading_halted = False
            
            # Drawdown számítása
            else:
                self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
                
                # Kereskedés leállítása, ha eléri a maximális drawdown-t
                if self.current_drawdown >= self.max_drawdown_limit and not self.is_trading_halted:
                    logger.warning(f"Trading halted due to max drawdown limit reached. Current drawdown: {self.current_drawdown:.2%}")
                    self.is_trading_halted = True
            
            self.last_update_time = datetime.now()
            
            return {
                'current_drawdown': self.current_drawdown,
                'peak_equity': self.peak_equity,
                'is_trading_halted': self.is_trading_halted,
                'timestamp': self.last_update_time
            }
        
        except Exception as e:
            logger.error(f"Error updating drawdown: {str(e)}")
            return {
                'current_drawdown': self.current_drawdown,
                'peak_equity': self.peak_equity,
                'is_trading_halted': self.is_trading_halted,
                'error': str(e)
            }
    
    def get_position_size_factor(self) -> float:
        """
        Visszaadja a pozíció méret faktort az aktuális drawdown alapján.
        
        Returns:
            float: A pozíció méret faktor (0.0 és 1.0 között)
        """
        try:
            # Ha a kereskedés le van állítva, akkor 0
            if self.is_trading_halted:
                return 0.0
            
            # Megkeresi a megfelelő csökkentési szintet
            for level, factor in sorted(self.position_size_reduction_levels.items(), reverse=True):
                if self.current_drawdown >= level:
                    return factor
            
            # Ha nincs drawdown, akkor 1.0
            return 1.0
        
        except Exception as e:
            logger.error(f"Error getting position size factor: {str(e)}")
            return 0.0
    
    def adjust_position_size(self, original_position_size: float) -> float:
        """
        Módosítja a pozíció méretet az aktuális drawdown alapján.
        
        Args:
            original_position_size: Az eredeti pozíció méret
            
        Returns:
            float: A módosított pozíció méret
        """
        try:
            # Ha a pozíció méret 0 vagy negatív, akkor nem módosít
            if original_position_size <= 0:
                return 0.0
            
            # Pozíció méret faktor
            factor = self.get_position_size_factor()
            
            # Módosított pozíció méret
            adjusted_position_size = original_position_size * factor
            
            if factor < 1.0:
                logger.info(f"Position size adjusted due to drawdown: {original_position_size} -> {adjusted_position_size} (factor: {factor})")
            
            return adjusted_position_size
        
        except Exception as e:
            logger.error(f"Error adjusting position size: {str(e)}")
            return 0.0
    
    def get_status(self) -> Dict:
        """
        Visszaadja a drawdown kezelő aktuális állapotát.
        
        Returns:
            Dict: A drawdown kezelő állapota
        """
        try:
            # Drawdown szint kategória
            if self.current_drawdown < self.warning_drawdown_level:
                drawdown_level = 'normal'
            elif self.current_drawdown < self.max_drawdown_limit:
                drawdown_level = 'warning'
            else:
                drawdown_level = 'critical'
            
            # Pozíció méret faktor
            position_size_factor = self.get_position_size_factor()
            
            return {
                'current_drawdown': self.current_drawdown,
                'drawdown_level': drawdown_level,
                'peak_equity': self.peak_equity,
                'is_trading_halted': self.is_trading_halted,
                'position_size_factor': position_size_factor,
                'max_drawdown_limit': self.max_drawdown_limit,
                'warning_drawdown_level': self.warning_drawdown_level,
                'last_update_time': self.last_update_time
            }
        
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {'error': str(e)}
    
    def reset(self) -> bool:
        """
        Visszaállítja a drawdown kezelőt alapállapotba.
        
        Returns:
            bool: Sikeres visszaállítás esetén True, egyébként False
        """
        try:
            self.current_drawdown = 0.0
            self.peak_equity = 0.0
            self.is_trading_halted = False
            self.last_update_time = datetime.now()
            
            logger.info("DrawdownManager reset to initial state")
            return True
        
        except Exception as e:
            logger.error(f"Error resetting drawdown manager: {str(e)}")
            return False
    
    def calculate_recovery_required(self) -> Dict:
        """
        Kiszámítja a helyreállításhoz szükséges nyereséget.
        
        Returns:
            Dict: A helyreállítási adatok
        """
        try:
            if self.current_drawdown <= 0 or self.peak_equity <= 0:
                return {
                    'recovery_percentage': 0.0,
                    'recovery_amount': 0.0
                }
            
            # Aktuális tőke
            current_equity = self.peak_equity * (1 - self.current_drawdown)
            
            # Helyreállításhoz szükséges százalékos nyereség
            recovery_percentage = self.current_drawdown / (1 - self.current_drawdown)
            
            # Helyreállításhoz szükséges összeg
            recovery_amount = self.peak_equity - current_equity
            
            return {
                'recovery_percentage': recovery_percentage,
                'recovery_amount': recovery_amount,
                'current_equity': current_equity,
                'peak_equity': self.peak_equity,
                'current_drawdown': self.current_drawdown
            }
        
        except Exception as e:
            logger.error(f"Error calculating recovery required: {str(e)}")
            return {'error': str(e)}
    
    def simulate_recovery_time(self, expected_monthly_return: float, expected_monthly_volatility: float, 
                              num_simulations: int = 1000) -> Dict:
        """
        Szimulálja a helyreállításhoz szükséges időt.
        
        Args:
            expected_monthly_return: Várható havi hozam
            expected_monthly_volatility: Várható havi volatilitás
            num_simulations: Szimulációk száma
            
        Returns:
            Dict: A helyreállítási idő szimulációs eredményei
        """
        try:
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                num_simulations = min(num_simulations, 100)
            
            if self.current_drawdown <= 0 or self.peak_equity <= 0:
                return {
                    'median_recovery_months': 0.0,
                    'mean_recovery_months': 0.0,
                    'min_recovery_months': 0.0,
                    'max_recovery_months': 0.0
                }
            
            # Aktuális tőke
            current_equity = self.peak_equity * (1 - self.current_drawdown)
            
            # Szimuláció
            recovery_months = []
            
            for _ in range(num_simulations):
                equity = current_equity
                months = 0
                
                while equity < self.peak_equity and months < 120:  # Maximum 10 év (120 hónap)
                    # Havi hozam szimulálása
                    monthly_return = np.random.normal(expected_monthly_return, expected_monthly_volatility)
                    equity *= (1 + monthly_return)
                    months += 1
                
                if equity >= self.peak_equity:
                    recovery_months.append(months)
                else:
                    recovery_months.append(float('inf'))  # Nem sikerült helyreállítani
            
            # Eredmények
            valid_recoveries = [m for m in recovery_months if m != float('inf')]
            
            if not valid_recoveries:
                return {
                    'median_recovery_months': float('inf'),
                    'mean_recovery_months': float('inf'),
                    'min_recovery_months': float('inf'),
                    'max_recovery_months': float('inf'),
                    'recovery_probability': 0.0
                }
            
            median_recovery = np.median(valid_recoveries)
            mean_recovery = np.mean(valid_recoveries)
            min_recovery = min(valid_recoveries)
            max_recovery = max(valid_recoveries)
            recovery_probability = len(valid_recoveries) / num_simulations
            
            return {
                'median_recovery_months': median_recovery,
                'mean_recovery_months': mean_recovery,
                'min_recovery_months': min_recovery,
                'max_recovery_months': max_recovery,
                'recovery_probability': recovery_probability,
                'current_drawdown': self.current_drawdown,
                'peak_equity': self.peak_equity,
                'current_equity': current_equity
            }
        
        except Exception as e:
            logger.error(f"Error simulating recovery time: {str(e)}")
            return {'error': str(e)}
