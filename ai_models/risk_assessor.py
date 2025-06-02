"""
Risk Assessor - Értékeli a kereskedési kockázatokat különböző szempontok alapján.
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

from src.utils.logger import setup_logger

logger = setup_logger('risk_assessor')

class RiskAssessor:
    """
    Értékeli a kereskedési kockázatokat különböző szempontok alapján,
    beleértve a piaci volatilitást, korrelációt, és a portfólió kockázatát.
    """
    
    def __init__(self, config: Dict):
        """
        Inicializálja a RiskAssessor-t a megadott konfigurációval.
        
        Args:
            config: A RiskAssessor konfigurációja
        """
        self.config = config
        
        # Konfigurációs beállítások
        self.risk_thresholds = config.get('risk_thresholds', {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8
        })
        self.volatility_window = config.get('volatility_window', 20)  # Volatilitás számításához használt időablak
        self.correlation_window = config.get('correlation_window', 30)  # Korreláció számításához használt időablak
        self.max_drawdown_threshold = config.get('max_drawdown_threshold', 0.2)  # 20% maximális drawdown
        
        # RPI4 optimalizáció
        self.max_lookback = config.get('max_lookback', 100)  # Korlátozott visszatekintés
        self.simplify_calculations = config.get('simplify_calculations', True)  # Egyszerűsített számítások
        
        logger.info("RiskAssessor initialized")
    
    def assess_market_risk(self, market_data: Dict) -> Dict:
        """
        Értékeli a piaci kockázatot a megadott piaci adatok alapján.
        
        Args:
            market_data: Piaci adatok
            
        Returns:
            Dict: A piaci kockázat értékelése
        """
        try:
            risk_assessment = {}
            
            for symbol, data in market_data.items():
                if 'ohlcv' not in data or '1h' not in data['ohlcv'] or not data['ohlcv']['1h']:
                    logger.warning(f"No OHLCV data for {symbol}")
                    continue
                
                # Korlátozza a visszatekintést
                lookback = min(len(data['ohlcv']['1h']), self.max_lookback)
                ohlcv_data = data['ohlcv']['1h'][-lookback:]
                
                # Volatilitás számítása
                volatility = self._calculate_volatility(ohlcv_data)
                
                # Trend erősség számítása
                trend_strength = self._calculate_trend_strength(ohlcv_data)
                
                # Volumen anomália detektálása
                volume_anomaly = self._detect_volume_anomaly(ohlcv_data)
                
                # Ár momentum számítása
                price_momentum = self._calculate_price_momentum(ohlcv_data)
                
                # Kockázati szint meghatározása
                risk_level = self._determine_risk_level(volatility, trend_strength, volume_anomaly, price_momentum)
                
                risk_assessment[symbol] = {
                    'risk_level': risk_level,
                    'volatility': volatility,
                    'trend_strength': trend_strength,
                    'volume_anomaly': volume_anomaly,
                    'price_momentum': price_momentum,
                    'timestamp': datetime.now()
                }
            
            logger.info(f"Market risk assessment completed for {len(risk_assessment)} symbols")
            return risk_assessment
        
        except Exception as e:
            logger.error(f"Error assessing market risk: {str(e)}")
            return {}
    
    def assess_position_risk(self, position: Dict, market_data: Dict) -> Dict:
        """
        Értékeli egy adott pozíció kockázatát.
        
        Args:
            position: A pozíció adatai
            market_data: Piaci adatok
            
        Returns:
            Dict: A pozíció kockázatának értékelése
        """
        try:
            symbol = position.get('symbol')
            
            if not symbol or symbol not in market_data:
                logger.warning(f"No market data for position symbol: {symbol}")
                return {}
            
            # Pozíció adatok
            entry_price = position.get('entry_price', 0.0)
            current_price = market_data[symbol]['ticker']['last']
            position_size = position.get('amount', 0.0)
            position_value = position_size * current_price
            
            # Nyereség/veszteség számítása
            pnl_percentage = (current_price - entry_price) / entry_price if entry_price > 0 else 0.0
            
            # Stop loss és take profit szintek
            stop_loss = position.get('stop_loss')
            take_profit = position.get('take_profit')
            
            # Kockázat/nyereség arány számítása
            risk_reward_ratio = None
            if stop_loss and take_profit and entry_price:
                potential_loss = abs(entry_price - stop_loss) / entry_price
                potential_gain = abs(take_profit - entry_price) / entry_price
                risk_reward_ratio = potential_gain / potential_loss if potential_loss > 0 else None
            
            # Pozíció kockázati szint meghatározása
            position_risk = self._determine_position_risk(
                position_value,
                pnl_percentage,
                risk_reward_ratio,
                market_data[symbol].get('volatility', 0.0)
            )
            
            return {
                'symbol': symbol,
                'position_risk': position_risk,
                'pnl_percentage': pnl_percentage,
                'risk_reward_ratio': risk_reward_ratio,
                'position_value': position_value,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error assessing position risk: {str(e)}")
            return {}
    
    def assess_portfolio_risk(self, portfolio: Dict, market_data: Dict) -> Dict:
        """
        Értékeli a teljes portfólió kockázatát.
        
        Args:
            portfolio: A portfólió adatai
            market_data: Piaci adatok
            
        Returns:
            Dict: A portfólió kockázatának értékelése
        """
        try:
            assets = portfolio.get('assets', [])
            
            if not assets:
                logger.warning("Empty portfolio")
                return {
                    'portfolio_risk': 'low',
                    'diversification_score': 0.0,
                    'correlation_risk': 'low',
                    'concentration_risk': 'low',
                    'drawdown_risk': 'low',
                    'timestamp': datetime.now()
                }
            
            # Portfólió érték
            total_value = portfolio.get('total_value_usd', 0.0)
            
            # Koncentráció kockázat
            concentration_risk = self._calculate_concentration_risk(assets, total_value)
            
            # Diverzifikáció pontszám
            diversification_score = self._calculate_diversification_score(assets)
            
            # Korreláció kockázat
            correlation_risk = self._calculate_correlation_risk(assets, market_data)
            
            # Drawdown kockázat
            drawdown_risk = self._calculate_drawdown_risk(portfolio)
            
            # Portfólió kockázati szint meghatározása
            portfolio_risk = self._determine_portfolio_risk(
                concentration_risk,
                diversification_score,
                correlation_risk,
                drawdown_risk
            )
            
            return {
                'portfolio_risk': portfolio_risk,
                'diversification_score': diversification_score,
                'correlation_risk': correlation_risk,
                'concentration_risk': concentration_risk,
                'drawdown_risk': drawdown_risk,
                'timestamp': datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {str(e)}")
            return {}
    
    def _calculate_volatility(self, ohlcv_data: List) -> float:
        """
        Kiszámítja a volatilitást az OHLCV adatok alapján.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            float: A volatilitás értéke
        """
        try:
            # Korlátozza a visszatekintést
            window = min(self.volatility_window, len(ohlcv_data))
            
            if window < 2:
                return 0.0
            
            # Záróárak
            closes = [candle[4] for candle in ohlcv_data[-window:]]
            
            # Napi hozamok
            returns = [np.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
            
            # Volatilitás (szórás)
            volatility = np.std(returns) * np.sqrt(365)  # Éves volatilitás
            
            return volatility
        
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return 0.0
    
    def _calculate_trend_strength(self, ohlcv_data: List) -> float:
        """
        Kiszámítja a trend erősségét az OHLCV adatok alapján.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            float: A trend erőssége (-1.0 és 1.0 között, ahol -1.0 erős lefelé trend, 1.0 erős felfelé trend)
        """
        try:
            # Korlátozza a visszatekintést
            window = min(self.volatility_window, len(ohlcv_data))
            
            if window < 5:
                return 0.0
            
            # Záróárak
            closes = [candle[4] for candle in ohlcv_data[-window:]]
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Egyszerű trend erősség: utolsó és első ár különbsége
                return (closes[-1] - closes[0]) / closes[0]
            
            # Fejlettebb módszer: lineáris regresszió
            x = np.arange(len(closes))
            slope, _ = np.polyfit(x, closes, 1)
            
            # Normalizált meredekség
            normalized_slope = slope * len(closes) / closes[0]
            
            # Korlátozza -1.0 és 1.0 közé
            return max(-1.0, min(1.0, normalized_slope))
        
        except Exception as e:
            logger.error(f"Error calculating trend strength: {str(e)}")
            return 0.0
    
    def _detect_volume_anomaly(self, ohlcv_data: List) -> float:
        """
        Detektálja a volumen anomáliákat az OHLCV adatok alapján.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            float: A volumen anomália mértéke (0.0 és 1.0 között, ahol 0.0 nincs anomália, 1.0 erős anomália)
        """
        try:
            # Korlátozza a visszatekintést
            window = min(self.volatility_window, len(ohlcv_data))
            
            if window < 5:
                return 0.0
            
            # Volumenek
            volumes = [candle[5] for candle in ohlcv_data[-window:]]
            
            # Átlagos volumen
            avg_volume = np.mean(volumes[:-1])  # Az utolsó kivételével
            
            if avg_volume == 0:
                return 0.0
            
            # Utolsó volumen
            last_volume = volumes[-1]
            
            # Volumen anomália
            volume_ratio = last_volume / avg_volume
            
            # Normalizált anomália érték
            if volume_ratio <= 1.0:
                return 0.0
            elif volume_ratio >= 3.0:
                return 1.0
            else:
                return (volume_ratio - 1.0) / 2.0
        
        except Exception as e:
            logger.error(f"Error detecting volume anomaly: {str(e)}")
            return 0.0
    
    def _calculate_price_momentum(self, ohlcv_data: List) -> float:
        """
        Kiszámítja az ár momentumot az OHLCV adatok alapján.
        
        Args:
            ohlcv_data: OHLCV adatok listája
            
        Returns:
            float: Az ár momentum értéke (-1.0 és 1.0 között)
        """
        try:
            # Korlátozza a visszatekintést
            window = min(self.volatility_window, len(ohlcv_data))
            
            if window < 10:
                return 0.0
            
            # Záróárak
            closes = [candle[4] for candle in ohlcv_data[-window:]]
            
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations:
                # Rövid távú változás (utolsó 3 gyertya)
                short_term = (closes[-1] - closes[-3]) / closes[-3]
                
                # Középtávú változás (utolsó 7 gyertya)
                medium_term = (closes[-1] - closes[-7]) / closes[-7]
                
                # Hosszú távú változás (teljes ablak)
                long_term = (closes[-1] - closes[0]) / closes[0]
                
                # Súlyozott momentum
                momentum = 0.5 * short_term + 0.3 * medium_term + 0.2 * long_term
            
            else:
                # Fejlettebb módszer: exponenciálisan súlyozott momentum
                weights = np.exp(np.linspace(0, 1, window))
                weights = weights / np.sum(weights)
                
                returns = [np.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
                returns.insert(0, 0)  # Az első hozam 0
                
                momentum = np.sum(weights * returns)
            
            # Korlátozza -1.0 és 1.0 közé
            return max(-1.0, min(1.0, momentum * 10))  # Skálázás a jobb értelmezhetőség érdekében
        
        except Exception as e:
            logger.error(f"Error calculating price momentum: {str(e)}")
            return 0.0
    
    def _determine_risk_level(self, volatility: float, trend_strength: float, 
                             volume_anomaly: float, price_momentum: float) -> str:
        """
        Meghatározza a kockázati szintet a különböző metrikák alapján.
        
        Args:
            volatility: A volatilitás értéke
            trend_strength: A trend erőssége
            volume_anomaly: A volumen anomália mértéke
            price_momentum: Az ár momentum értéke
            
        Returns:
            str: A kockázati szint ('low', 'medium', 'high', 'extreme')
        """
        try:
            # Súlyozott kockázati pontszám
            risk_score = (
                0.4 * min(1.0, volatility * 5) +  # Volatilitás (max 20% -> 1.0)
                0.2 * abs(trend_strength) +  # Trend erősség abszolút értéke
                0.2 * volume_anomaly +  # Volumen anomália
                0.2 * abs(price_momentum)  # Momentum abszolút értéke
            )
            
            # Kockázati szint meghatározása
            if risk_score < self.risk_thresholds['low']:
                return 'low'
            elif risk_score < self.risk_thresholds['medium']:
                return 'medium'
            elif risk_score < self.risk_thresholds['high']:
                return 'high'
            else:
                return 'extreme'
        
        except Exception as e:
            logger.error(f"Error determining risk level: {str(e)}")
            return 'medium'  # Alapértelmezett érték hiba esetén
    
    def _determine_position_risk(self, position_value: float, pnl_percentage: float, 
                                risk_reward_ratio: Optional[float], market_volatility: float) -> str:
        """
        Meghatározza egy pozíció kockázati szintjét.
        
        Args:
            position_value: A pozíció értéke
            pnl_percentage: A nyereség/veszteség százalékban
            risk_reward_ratio: A kockázat/nyereség arány
            market_volatility: A piaci volatilitás
            
        Returns:
            str: A kockázati szint ('low', 'medium', 'high', 'extreme')
        """
        try:
            # Pozíció méret kockázat (nagyobb pozíció = nagyobb kockázat)
            size_risk = min(1.0, position_value / 10000.0)  # 10,000 USD felett maximális
            
            # Veszteség kockázat (nagyobb veszteség = nagyobb kockázat)
            loss_risk = 0.0
            if pnl_percentage < 0:
                loss_risk = min(1.0, abs(pnl_percentage) * 5)  # 20% veszteség felett maximális
            
            # Kockázat/nyereség arány kockázat
            rr_risk = 0.5  # Alapértelmezett közepes kockázat
            if risk_reward_ratio is not None:
                if risk_reward_ratio >= 3.0:
                    rr_risk = 0.0  # Alacsony kockázat
                elif risk_reward_ratio >= 2.0:
                    rr_risk = 0.25  # Alacsony-közepes kockázat
                elif risk_reward_ratio >= 1.0:
                    rr_risk = 0.5  # Közepes kockázat
                else:
                    rr_risk = 1.0  # Magas kockázat
            
            # Volatilitás kockázat
            volatility_risk = min(1.0, market_volatility * 5)  # 20% volatilitás felett maximális
            
            # Súlyozott kockázati pontszám
            risk_score = (
                0.3 * size_risk +
                0.3 * loss_risk +
                0.2 * rr_risk +
                0.2 * volatility_risk
            )
            
            # Kockázati szint meghatározása
            if risk_score < self.risk_thresholds['low']:
                return 'low'
            elif risk_score < self.risk_thresholds['medium']:
                return 'medium'
            elif risk_score < self.risk_thresholds['high']:
                return 'high'
            else:
                return 'extreme'
        
        except Exception as e:
            logger.error(f"Error determining position risk: {str(e)}")
            return 'medium'  # Alapértelmezett érték hiba esetén
    
    def _calculate_concentration_risk(self, assets: List[Dict], total_value: float) -> str:
        """
        Kiszámítja a koncentráció kockázatot.
        
        Args:
            assets: Az eszközök listája
            total_value: A portfólió teljes értéke
            
        Returns:
            str: A koncentráció kockázat szintje ('low', 'medium', 'high', 'extreme')
        """
        try:
            if not assets or total_value <= 0:
                return 'low'
            
            # Eszközök értéke
            asset_values = [asset.get('value_usd', 0.0) for asset in assets]
            
            # Legnagyobb eszköz aránya
            max_concentration = max(asset_values) / total_value if total_value > 0 else 0.0
            
            # Koncentráció kockázat meghatározása
            if max_concentration < 0.3:
                return 'low'  # Kevesebb mint 30% egy eszközben
            elif max_concentration < 0.5:
                return 'medium'  # 30-50% egy eszközben
            elif max_concentration < 0.7:
                return 'high'  # 50-70% egy eszközben
            else:
                return 'extreme'  # Több mint 70% egy eszközben
        
        except Exception as e:
            logger.error(f"Error calculating concentration risk: {str(e)}")
            return 'medium'  # Alapértelmezett érték hiba esetén
    
    def _calculate_diversification_score(self, assets: List[Dict]) -> float:
        """
        Kiszámítja a diverzifikáció pontszámot.
        
        Args:
            assets: Az eszközök listája
            
        Returns:
            float: A diverzifikáció pontszám (0.0 és 1.0 között, ahol 1.0 teljesen diverzifikált)
        """
        try:
            if not assets:
                return 0.0
            
            # Eszközök száma
            num_assets = len(assets)
            
            if num_assets <= 1:
                return 0.0
            
            # Eszközök értéke
            asset_values = [asset.get('value_usd', 0.0) for asset in assets]
            total_value = sum(asset_values)
            
            if total_value <= 0:
                return 0.0
            
            # Eszközök aránya
            asset_weights = [value / total_value for value in asset_values]
            
            # Herfindahl-Hirschman Index (HHI)
            hhi = sum([weight ** 2 for weight in asset_weights])
            
            # Normalizált diverzifikáció pontszám
            # HHI értéke 1/n (tökéletes diverzifikáció) és 1 (teljes koncentráció) között van
            # Átskálázzuk 0 és 1 közé, ahol 1 a tökéletes diverzifikáció
            min_hhi = 1.0 / num_assets
            normalized_score = (1.0 - hhi) / (1.0 - min_hhi)
            
            return max(0.0, min(1.0, normalized_score))
        
        except Exception as e:
            logger.error(f"Error calculating diversification score: {str(e)}")
            return 0.5  # Alapértelmezett érték hiba esetén
    
    def _calculate_correlation_risk(self, assets: List[Dict], market_data: Dict) -> str:
        """
        Kiszámítja a korreláció kockázatot.
        
        Args:
            assets: Az eszközök listája
            market_data: Piaci adatok
            
        Returns:
            str: A korreláció kockázat szintje ('low', 'medium', 'high', 'extreme')
        """
        try:
            # Egyszerűsített számítások RPI4-re
            if self.simplify_calculations or len(assets) <= 1:
                return 'medium'  # Alapértelmezett érték egyszerűsített módban
            
            # Eszközök szimbólumai
            symbols = [asset.get('symbol') for asset in assets]
            
            # Záróárak gyűjtése
            price_data = {}
            for symbol in symbols:
                if symbol in market_data and 'ohlcv' in market_data[symbol] and '1d' in market_data[symbol]['ohlcv']:
                    ohlcv = market_data[symbol]['ohlcv']['1d']
                    lookback = min(self.correlation_window, len(ohlcv))
                    closes = [candle[4] for candle in ohlcv[-lookback:]]
                    price_data[symbol] = closes
            
            if len(price_data) <= 1:
                return 'medium'  # Nem elég adat a korrelációhoz
            
            # Korrelációs mátrix számítása
            correlation_matrix = {}
            for symbol1 in price_data:
                correlation_matrix[symbol1] = {}
                for symbol2 in price_data:
                    if symbol1 == symbol2:
                        correlation_matrix[symbol1][symbol2] = 1.0
                        continue
                    
                    # Közös hosszúság meghatározása
                    min_length = min(len(price_data[symbol1]), len(price_data[symbol2]))
                    
                    if min_length < 5:
                        correlation_matrix[symbol1][symbol2] = 0.0
                        continue
                    
                    # Záróárak
                    closes1 = price_data[symbol1][-min_length:]
                    closes2 = price_data[symbol2][-min_length:]
                    
                    # Hozamok
                    returns1 = [np.log(closes1[i] / closes1[i-1]) for i in range(1, len(closes1))]
                    returns2 = [np.log(closes2[i] / closes2[i-1]) for i in range(1, len(closes2))]
                    
                    # Korreláció
                    correlation = np.corrcoef(returns1, returns2)[0, 1]
                    
                    correlation_matrix[symbol1][symbol2] = correlation
            
            # Átlagos abszolút korreláció
            correlations = []
            for symbol1 in correlation_matrix:
                for symbol2 in correlation_matrix[symbol1]:
                    if symbol1 != symbol2:
                        correlations.append(abs(correlation_matrix[symbol1][symbol2]))
            
            avg_correlation = np.mean(correlations) if correlations else 0.0
            
            # Korreláció kockázat meghatározása
            if avg_correlation < 0.3:
                return 'low'  # Alacsony korreláció
            elif avg_correlation < 0.5:
                return 'medium'  # Közepes korreláció
            elif avg_correlation < 0.7:
                return 'high'  # Magas korreláció
            else:
                return 'extreme'  # Extrém magas korreláció
        
        except Exception as e:
            logger.error(f"Error calculating correlation risk: {str(e)}")
            return 'medium'  # Alapértelmezett érték hiba esetén
    
    def _calculate_drawdown_risk(self, portfolio: Dict) -> str:
        """
        Kiszámítja a drawdown kockázatot.
        
        Args:
            portfolio: A portfólió adatai
            
        Returns:
            str: A drawdown kockázat szintje ('low', 'medium', 'high', 'extreme')
        """
        try:
            # Portfólió teljesítmény
            performance = portfolio.get('performance', {})
            
            # Drawdown
            drawdown = abs(performance.get('drawdown', 0.0))
            
            # Drawdown kockázat meghatározása
            if drawdown < 0.05:
                return 'low'  # Kevesebb mint 5% drawdown
            elif drawdown < 0.1:
                return 'medium'  # 5-10% drawdown
            elif drawdown < self.max_drawdown_threshold:
                return 'high'  # 10-20% drawdown
            else:
                return 'extreme'  # Több mint 20% drawdown
        
        except Exception as e:
            logger.error(f"Error calculating drawdown risk: {str(e)}")
            return 'medium'  # Alapértelmezett érték hiba esetén
    
    def _determine_portfolio_risk(self, concentration_risk: str, diversification_score: float,
                                 correlation_risk: str, drawdown_risk: str) -> str:
        """
        Meghatározza a portfólió kockázati szintjét.
        
        Args:
            concentration_risk: A koncentráció kockázat szintje
            diversification_score: A diverzifikáció pontszám
            correlation_risk: A korreláció kockázat szintje
            drawdown_risk: A drawdown kockázat szintje
            
        Returns:
            str: A portfólió kockázati szintje ('low', 'medium', 'high', 'extreme')
        """
        try:
            # Kockázati szintek számértékre konvertálása
            risk_values = {
                'low': 0.0,
                'medium': 0.33,
                'high': 0.67,
                'extreme': 1.0
            }
            
            # Súlyozott kockázati pontszám
            risk_score = (
                0.3 * risk_values[concentration_risk] +
                0.2 * (1.0 - diversification_score) +  # Alacsonyabb diverzifikáció = magasabb kockázat
                0.2 * risk_values[correlation_risk] +
                0.3 * risk_values[drawdown_risk]
            )
            
            # Kockázati szint meghatározása
            if risk_score < 0.25:
                return 'low'
            elif risk_score < 0.5:
                return 'medium'
            elif risk_score < 0.75:
                return 'high'
            else:
                return 'extreme'
        
        except Exception as e:
            logger.error(f"Error determining portfolio risk: {str(e)}")
            return 'medium'  # Alapértelmezett érték hiba esetén
