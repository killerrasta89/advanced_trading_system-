"""
Position Sizer - Meghatározza a kereskedési pozíciók optimális méretét.
"""
import logging
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('position_sizer')

class PositionSizer:
    """
    Meghatározza a kereskedési pozíciók optimális méretét különböző
    kockázatkezelési módszerek alapján, mint például fix kockázat,
    volatilitás alapú méretezés, és Kelly-kritérium.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a PositionSizer-t a megadott konfigurációval.
        
        Args:
            config: A PositionSizer konfigurációja
        """
        self.config = config
        
        # Konfigurációs beállítások
        self.default_risk_per_trade = config.get('default_risk_per_trade', 0.01)  # 1% kockázat tranzakciónként
        self.max_position_size = config.get('max_position_size', 0.2)  # Maximum 20% egy pozícióra
        self.position_sizing_method = config.get('position_sizing_method', 'fixed_risk')  # Alapértelmezett méretezési módszer
        self.kelly_fraction = config.get('kelly_fraction', 0.5)  # Kelly-kritérium töredéke (konzervatívabb)
        
        # RPI4 optimalizáció
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        
        logger.info("PositionSizer initialized")
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: Optional[float],
                               account_balance: float, market_data: Dict, strategy_data: Dict) -> Dict:
        """
        Kiszámítja az optimális pozíció méretet.
        
        Args:
            symbol: A kereskedési szimbólum
            entry_price: A belépési ár
            stop_loss: A stop loss ár (opcionális)
            account_balance: A számlaegyenleg
            market_data: Piaci adatok
            strategy_data: Stratégia adatok
            
        Returns:
            Dict: A pozíció méret adatok
        """
        try:
            # Ellenőrzi a bemeneti adatokat
            if entry_price <= 0:
                logger.warning(f"Invalid entry price: {entry_price}")
                return {'position_size': 0.0, 'error': 'Invalid entry price'}
            
            if account_balance <= 0:
                logger.warning(f"Invalid account balance: {account_balance}")
                return {'position_size': 0.0, 'error': 'Invalid account balance'}
            
            # Kiválasztja a megfelelő méretezési módszert
            if self.position_sizing_method == 'fixed_risk':
                result = self._fixed_risk_position_size(symbol, entry_price, stop_loss, account_balance, market_data)
            elif self.position_sizing_method == 'volatility_based':
                result = self._volatility_based_position_size(symbol, entry_price, account_balance, market_data)
            elif self.position_sizing_method == 'kelly_criterion':
                result = self._kelly_criterion_position_size(symbol, entry_price, account_balance, market_data, strategy_data)
            elif self.position_sizing_method == 'equal_weight':
                result = self._equal_weight_position_size(symbol, entry_price, account_balance, market_data, strategy_data)
            else:
                logger.warning(f"Unknown position sizing method: {self.position_sizing_method}")
                result = self._fixed_risk_position_size(symbol, entry_price, stop_loss, account_balance, market_data)
            
            # Korlátozza a pozíció méretet
            max_size = account_balance * self.max_position_size
            if result['position_size'] > max_size:
                logger.info(f"Position size limited from {result['position_size']} to {max_size}")
                result['position_size'] = max_size
                result['limited'] = True
            
            # Hozzáadja a számítási módszert
            result['method'] = self.position_sizing_method
            
            return result
        
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return {'position_size': 0.0, 'error': str(e)}
    
    def _fixed_risk_position_size(self, symbol: str, entry_price: float, stop_loss: Optional[float],
                                 account_balance: float, market_data: Dict) -> Dict:
        """
        Kiszámítja a pozíció méretet fix kockázat alapján.
        
        Args:
            symbol: A kereskedési szimbólum
            entry_price: A belépési ár
            stop_loss: A stop loss ár
            account_balance: A számlaegyenleg
            market_data: Piaci adatok
            
        Returns:
            Dict: A pozíció méret adatok
        """
        try:
            # Kockáztatott összeg
            risk_amount = account_balance * self.default_risk_per_trade
            
            # Ha nincs stop loss, akkor ATR alapján számol
            if stop_loss is None:
                # ATR (Average True Range) alapú stop loss
                atr = self._calculate_atr(symbol, market_data)
                if atr <= 0:
                    logger.warning(f"Invalid ATR: {atr}")
                    return {'position_size': 0.0, 'error': 'Invalid ATR'}
                
                # Stop loss távolság (2 * ATR)
                stop_distance = 2 * atr
                
                # Stop loss ár
                stop_loss = entry_price * (1 - stop_distance) if market_data.get('signal', {}).get('direction') == 'buy' else entry_price * (1 + stop_distance)
            
            # Stop loss távolság
            stop_distance = abs(entry_price - stop_loss) / entry_price
            
            if stop_distance <= 0:
                logger.warning(f"Invalid stop distance: {stop_distance}")
                return {'position_size': 0.0, 'error': 'Invalid stop distance'}
            
            # Pozíció méret
            position_size = risk_amount / (entry_price * stop_distance)
            
            return {
                'position_size': position_size,
                'risk_amount': risk_amount,
                'stop_loss': stop_loss,
                'stop_distance': stop_distance
            }
        
        except Exception as e:
            logger.error(f"Error calculating fixed risk position size: {str(e)}")
            return {'position_size': 0.0, 'error': str(e)}
    
    def _volatility_based_position_size(self, symbol: str, entry_price: float,
                                       account_balance: float, market_data: Dict) -> Dict:
        """
        Kiszámítja a pozíció méretet volatilitás alapján.
        
        Args:
            symbol: A kereskedési szimbólum
            entry_price: A belépési ár
            account_balance: A számlaegyenleg
            market_data: Piaci adatok
            
        Returns:
            Dict: A pozíció méret adatok
        """
        try:
            # Kockáztatott összeg
            risk_amount = account_balance * self.default_risk_per_trade
            
            # ATR (Average True Range)
            atr = self._calculate_atr(symbol, market_data)
            if atr <= 0:
                logger.warning(f"Invalid ATR: {atr}")
                return {'position_size': 0.0, 'error': 'Invalid ATR'}
            
            # Volatilitás alapú pozíció méret
            # Alacsonyabb volatilitás = nagyobb pozíció, magasabb volatilitás = kisebb pozíció
            volatility = atr / entry_price
            
            if volatility <= 0:
                logger.warning(f"Invalid volatility: {volatility}")
                return {'position_size': 0.0, 'error': 'Invalid volatility'}
            
            # Pozíció méret
            position_size = risk_amount / (entry_price * volatility * 2)  # 2 * ATR stop loss
            
            # Stop loss ár
            stop_loss = entry_price * (1 - 2 * volatility) if market_data.get('signal', {}).get('direction') == 'buy' else entry_price * (1 + 2 * volatility)
            
            return {
                'position_size': position_size,
                'risk_amount': risk_amount,
                'stop_loss': stop_loss,
                'volatility': volatility
            }
        
        except Exception as e:
            logger.error(f"Error calculating volatility based position size: {str(e)}")
            return {'position_size': 0.0, 'error': str(e)}
    
    def _kelly_criterion_position_size(self, symbol: str, entry_price: float,
                                      account_balance: float, market_data: Dict, strategy_data: Dict) -> Dict:
        """
        Kiszámítja a pozíció méretet Kelly-kritérium alapján.
        
        Args:
            symbol: A kereskedési szimbólum
            entry_price: A belépési ár
            account_balance: A számlaegyenleg
            market_data: Piaci adatok
            strategy_data: Stratégia adatok
            
        Returns:
            Dict: A pozíció méret adatok
        """
        try:
            # Stratégia teljesítmény adatok
            win_rate = strategy_data.get('win_rate', 0.5)  # Alapértelmezett 50% nyerési arány
            avg_win = strategy_data.get('avg_win', 0.02)  # Alapértelmezett 2% átlagos nyereség
            avg_loss = strategy_data.get('avg_loss', 0.01)  # Alapértelmezett 1% átlagos veszteség
            
            # Ellenőrzi az adatokat
            if win_rate <= 0 or win_rate >= 1:
                logger.warning(f"Invalid win rate: {win_rate}")
                win_rate = 0.5
            
            if avg_win <= 0:
                logger.warning(f"Invalid average win: {avg_win}")
                avg_win = 0.02
            
            if avg_loss <= 0:
                logger.warning(f"Invalid average loss: {avg_loss}")
                avg_loss = 0.01
            
            # Kelly-képlet: f* = (p * b - q) / b
            # ahol f* = optimális tét, p = nyerési valószínűség, q = vesztési valószínűség (1-p), b = nyereség/veszteség arány
            
            # Nyereség/veszteség arány
            b = avg_win / avg_loss
            
            # Kelly-kritérium
            kelly = (win_rate * b - (1 - win_rate)) / b
            
            # Korlátozza a Kelly-értéket
            kelly = max(0, min(1, kelly))
            
            # Alkalmazza a Kelly-töredéket (konzervatívabb)
            kelly *= self.kelly_fraction
            
            # Pozíció méret
            position_size = account_balance * kelly
            
            # ATR (Average True Range)
            atr = self._calculate_atr(symbol, market_data)
            
            # Stop loss ár (ha van ATR)
            stop_loss = None
            if atr > 0:
                volatility = atr / entry_price
                stop_loss = entry_price * (1 - 2 * volatility) if market_data.get('signal', {}).get('direction') == 'buy' else entry_price * (1 + 2 * volatility)
            
            return {
                'position_size': position_size,
                'kelly': kelly,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'stop_loss': stop_loss
            }
        
        except Exception as e:
            logger.error(f"Error calculating Kelly criterion position size: {str(e)}")
            return {'position_size': 0.0, 'error': str(e)}
    
    def _equal_weight_position_size(self, symbol: str, entry_price: float,
                                   account_balance: float, market_data: Dict, strategy_data: Dict) -> Dict:
        """
        Kiszámítja a pozíció méretet egyenlő súlyozás alapján.
        
        Args:
            symbol: A kereskedési szimbólum
            entry_price: A belépési ár
            account_balance: A számlaegyenleg
            market_data: Piaci adatok
            strategy_data: Stratégia adatok
            
        Returns:
            Dict: A pozíció méret adatok
        """
        try:
            # Aktív stratégiák száma
            num_strategies = strategy_data.get('active_strategies', 1)
            
            # Maximum pozíciók száma stratégiánként
            max_positions_per_strategy = strategy_data.get('max_positions_per_strategy', 5)
            
            # Teljes pozíciók száma
            total_positions = num_strategies * max_positions_per_strategy
            
            # Egyenlő súlyozás
            weight = 1.0 / total_positions
            
            # Pozíció méret
            position_size = account_balance * weight
            
            # ATR (Average True Range)
            atr = self._calculate_atr(symbol, market_data)
            
            # Stop loss ár (ha van ATR)
            stop_loss = None
            if atr > 0:
                volatility = atr / entry_price
                stop_loss = entry_price * (1 - 2 * volatility) if market_data.get('signal', {}).get('direction') == 'buy' else entry_price * (1 + 2 * volatility)
            
            return {
                'position_size': position_size,
                'weight': weight,
                'num_strategies': num_strategies,
                'max_positions_per_strategy': max_positions_per_strategy,
                'stop_loss': stop_loss
            }
        
        except Exception as e:
            logger.error(f"Error calculating equal weight position size: {str(e)}")
            return {'position_size': 0.0, 'error': str(e)}
    
    def _calculate_atr(self, symbol: str, market_data: Dict) -> float:
        """
        Kiszámítja az ATR (Average True Range) értékét.
        
        Args:
            symbol: A kereskedési szimbólum
            market_data: Piaci adatok
            
        Returns:
            float: Az ATR érték
        """
        try:
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Ha van ATR a piaci adatokban, akkor azt használja
                if 'atr' in market_data:
                    return market_data['atr']
                
                # Ha nincs ATR, de van volatilitás, akkor abból számol
                if 'volatility' in market_data:
                    # Becsült ATR a volatilitásból
                    last_price = market_data.get('ticker', {}).get('last', 0.0)
                    if last_price > 0:
                        return market_data['volatility'] * last_price
                
                # Ha nincs sem ATR, sem volatilitás, akkor az utolsó árból becsül
                last_price = market_data.get('ticker', {}).get('last', 0.0)
                if last_price > 0:
                    # Alapértelmezett 2% volatilitás
                    return last_price * 0.02
                
                return 0.0
            
            else:
                # Ha van OHLCV adat, akkor abból számol
                if 'ohlcv' in market_data and '1d' in market_data['ohlcv'] and len(market_data['ohlcv']['1d']) >= 14:
                    ohlcv_data = market_data['ohlcv']['1d'][-14:]
                    
                    # True Range számítása
                    tr_values = []
                    
                    for i in range(1, len(ohlcv_data)):
                        high = ohlcv_data[i][2]
                        low = ohlcv_data[i][3]
                        prev_close = ohlcv_data[i-1][4]
                        
                        tr1 = high - low
                        tr2 = abs(high - prev_close)
                        tr3 = abs(low - prev_close)
                        
                        tr = max(tr1, tr2, tr3)
                        tr_values.append(tr)
                    
                    # ATR (14 napos átlag)
                    atr = sum(tr_values) / len(tr_values)
                    return atr
                
                # Ha nincs OHLCV adat, akkor az utolsó árból becsül
                last_price = market_data.get('ticker', {}).get('last', 0.0)
                if last_price > 0:
                    # Alapértelmezett 2% volatilitás
                    return last_price * 0.02
                
                return 0.0
        
        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")
            return 0.0
    
    def adjust_position_for_correlation(self, position_size: float, symbol: str, 
                                       portfolio: Dict, correlation_data: Dict) -> float:
        """
        Módosítja a pozíció méretet a korreláció alapján.
        
        Args:
            position_size: Az eredeti pozíció méret
            symbol: A kereskedési szimbólum
            portfolio: A portfólió adatok
            correlation_data: Korreláció adatok
            
        Returns:
            float: A módosított pozíció méret
        """
        try:
            # Ha nincs korreláció adat, vagy a pozíció méret 0, akkor nem módosít
            if not correlation_data or position_size <= 0:
                return position_size
            
            # Portfólió eszközök
            portfolio_symbols = [asset.get('symbol') for asset in portfolio.get('assets', [])]
            
            # Ha a szimbólum már a portfólióban van, vagy nincs más eszköz, akkor nem módosít
            if symbol in portfolio_symbols or not portfolio_symbols:
                return position_size
            
            # Átlagos korreláció a portfólió eszközökkel
            correlations = []
            
            for portfolio_symbol in portfolio_symbols:
                if portfolio_symbol in correlation_data and symbol in correlation_data[portfolio_symbol]:
                    correlations.append(abs(correlation_data[portfolio_symbol][symbol]))
            
            if not correlations:
                return position_size
            
            avg_correlation = sum(correlations) / len(correlations)
            
            # Korreláció alapú módosítás
            # Magasabb korreláció = kisebb pozíció
            correlation_factor = 1.0 - avg_correlation
            
            # Korlátozza a faktort
            correlation_factor = max(0.2, min(1.0, correlation_factor))
            
            # Módosított pozíció méret
            adjusted_position_size = position_size * correlation_factor
            
            logger.debug(f"Position size adjusted for correlation: {position_size} -> {adjusted_position_size} (factor: {correlation_factor})")
            
            return adjusted_position_size
        
        except Exception as e:
            logger.error(f"Error adjusting position for correlation: {str(e)}")
            return position_size
    
    def adjust_position_for_volatility(self, position_size: float, symbol: str, market_data: Dict) -> float:
        """
        Módosítja a pozíció méretet a volatilitás alapján.
        
        Args:
            position_size: Az eredeti pozíció méret
            symbol: A kereskedési szimbólum
            market_data: Piaci adatok
            
        Returns:
            float: A módosított pozíció méret
        """
        try:
            # Ha a pozíció méret 0, akkor nem módosít
            if position_size <= 0:
                return position_size
            
            # Ha a méretezési módszer már volatilitás alapú, akkor nem módosít
            if self.position_sizing_method == 'volatility_based':
                return position_size
            
            # ATR (Average True Range)
            atr = self._calculate_atr(symbol, market_data)
            
            # Ha nincs ATR, akkor nem módosít
            if atr <= 0:
                return position_size
            
            # Utolsó ár
            last_price = market_data.get('ticker', {}).get('last', 0.0)
            
            # Ha nincs utolsó ár, akkor nem módosít
            if last_price <= 0:
                return position_size
            
            # Volatilitás
            volatility = atr / last_price
            
            # Normalizált volatilitás (0.01 = 1% volatilitás)
            normalized_volatility = min(0.1, volatility) / 0.02  # 2% az alapértelmezett
            
            # Volatilitás alapú módosítás
            # Magasabb volatilitás = kisebb pozíció
            volatility_factor = 1.0 / normalized_volatility
            
            # Korlátozza a faktort
            volatility_factor = max(0.2, min(2.0, volatility_factor))
            
            # Módosított pozíció méret
            adjusted_position_size = position_size * volatility_factor
            
            logger.debug(f"Position size adjusted for volatility: {position_size} -> {adjusted_position_size} (factor: {volatility_factor})")
            
            return adjusted_position_size
        
        except Exception as e:
            logger.error(f"Error adjusting position for volatility: {str(e)}")
            return position_size
