"""
Strategy Config - Stratégia beállítások
"""
import json
import os

class StrategyConfig:
    """
    Stratégia beállítások kezelése
    """
    
    @staticmethod
    def get_default_config(strategy_type):
        """
        Alapértelmezett konfiguráció lekérdezése stratégia típus alapján
        
        Args:
            strategy_type (str): Stratégia típusa
            
        Returns:
            dict: Alapértelmezett konfiguráció
        """
        if strategy_type == 'grid_trading':
            return {
                'grid_levels': 5,
                'upper_price': 0,  # 0 = automatikus
                'lower_price': 0,  # 0 = automatikus
                'quantity_per_grid': 0.01,
                'price_deviation_pct': 2.0,
                'take_profit_pct': 1.0,
                'stop_loss_pct': 5.0,
                'trailing_stop': False,
                'trailing_stop_pct': 1.0,
                'rebalance_interval': 86400,  # 24 óra másodpercben
                'max_open_positions': 10,
                'use_indicators': True,
                'indicators': ['rsi', 'bollinger_bands']
            }
        elif strategy_type == 'dca_strategy':
            return {
                'base_order_size': 10.0,  # USDT
                'safety_order_size': 20.0,  # USDT
                'max_safety_orders': 3,
                'price_deviation_pct': 2.5,
                'safety_order_step_scale': 1.5,
                'safety_order_volume_scale': 1.5,
                'take_profit_pct': 3.0,
                'stop_loss_pct': 15.0,
                'trailing_stop': True,
                'trailing_stop_pct': 1.0,
                'cooldown_period': 86400,  # 24 óra másodpercben
                'max_active_deals': 5
            }
        elif strategy_type == 'momentum_strategy':
            return {
                'lookback_period': 14,
                'entry_threshold': 0.5,
                'exit_threshold': -0.2,
                'position_size_pct': 10.0,
                'max_positions': 5,
                'take_profit_pct': 5.0,
                'stop_loss_pct': 3.0,
                'trailing_stop': True,
                'trailing_stop_pct': 1.0,
                'indicators': ['rsi', 'macd', 'adx'],
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'macd_fast': 12,
                'macd_slow': 26,
                'macd_signal': 9,
                'adx_period': 14,
                'adx_threshold': 25
            }
        elif strategy_type == 'mean_reversion':
            return {
                'lookback_period': 20,
                'entry_std_dev': 2.0,
                'exit_std_dev': 0.5,
                'position_size_pct': 10.0,
                'max_positions': 5,
                'take_profit_pct': 3.0,
                'stop_loss_pct': 5.0,
                'max_holding_period': 86400,  # 24 óra másodpercben
                'indicators': ['bollinger_bands', 'rsi', 'stochastic'],
                'bollinger_period': 20,
                'bollinger_std_dev': 2.0,
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'stochastic_k_period': 14,
                'stochastic_d_period': 3,
                'stochastic_overbought': 80,
                'stochastic_oversold': 20
            }
        elif strategy_type == 'arbitrage_strategy':
            return {
                'min_spread_pct': 0.5,
                'max_spread_pct': 5.0,
                'position_size_pct': 20.0,
                'max_positions': 3,
                'max_slippage_pct': 0.2,
                'max_execution_time': 10,  # másodperc
                'exchanges': ['binance', 'kraken', 'coinbase'],
                'recheck_interval': 60,  # másodperc
                'auto_withdraw': False,
                'min_volume_usd': 10000.0
            }
        else:
            return {}
    
    @staticmethod
    def load_config(strategy_id):
        """
        Konfiguráció betöltése
        
        Args:
            strategy_id (int): Stratégia azonosító
            
        Returns:
            dict: Konfiguráció
        """
        config_file = os.path.join('data', 'strategies', f'strategy_{strategy_id}.json')
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Hiba a konfiguráció betöltése során: {e}")
                return {}
        else:
            return {}
    
    @staticmethod
    def save_config(strategy_id, config):
        """
        Konfiguráció mentése
        
        Args:
            strategy_id (int): Stratégia azonosító
            config (dict): Konfiguráció
            
        Returns:
            bool: Sikeres-e a mentés
        """
        config_dir = os.path.join('data', 'strategies')
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, f'strategy_{strategy_id}.json')
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Hiba a konfiguráció mentése során: {e}")
            return False
    
    @staticmethod
    def validate_config(strategy_type, config):
        """
        Konfiguráció validálása
        
        Args:
            strategy_type (str): Stratégia típusa
            config (dict): Konfiguráció
            
        Returns:
            tuple: (bool, str) - Érvényes-e a konfiguráció, hibaüzenet
        """
        # Alapértelmezett konfiguráció lekérdezése
        default_config = StrategyConfig.get_default_config(strategy_type)
        
        # Kötelező mezők ellenőrzése
        for key in default_config:
            if key not in config:
                return False, f"Hiányzó mező: {key}"
        
        # Típus ellenőrzés
        for key, value in config.items():
            if key in default_config:
                if not isinstance(value, type(default_config[key])):
                    return False, f"Érvénytelen típus: {key} - {type(value)} != {type(default_config[key])}"
        
        # Stratégia-specifikus validáció
        if strategy_type == 'grid_trading':
            if config['grid_levels'] < 2 or config['grid_levels'] > 100:
                return False, "A grid_levels értékének 2 és 100 között kell lennie"
            
            if config['price_deviation_pct'] <= 0:
                return False, "A price_deviation_pct értékének nagyobbnak kell lennie, mint 0"
        
        elif strategy_type == 'dca_strategy':
            if config['base_order_size'] <= 0:
                return False, "A base_order_size értékének nagyobbnak kell lennie, mint 0"
            
            if config['max_safety_orders'] < 0 or config['max_safety_orders'] > 10:
                return False, "A max_safety_orders értékének 0 és 10 között kell lennie"
        
        elif strategy_type == 'momentum_strategy':
            if config['lookback_period'] < 1:
                return False, "A lookback_period értékének legalább 1-nek kell lennie"
            
            if config['position_size_pct'] <= 0 or config['position_size_pct'] > 100:
                return False, "A position_size_pct értékének 0 és 100 között kell lennie"
        
        elif strategy_type == 'mean_reversion':
            if config['entry_std_dev'] <= 0:
                return False, "Az entry_std_dev értékének nagyobbnak kell lennie, mint 0"
            
            if config['exit_std_dev'] < 0:
                return False, "Az exit_std_dev értékének legalább 0-nak kell lennie"
        
        elif strategy_type == 'arbitrage_strategy':
            if config['min_spread_pct'] <= 0:
                return False, "A min_spread_pct értékének nagyobbnak kell lennie, mint 0"
            
            if config['min_spread_pct'] >= config['max_spread_pct']:
                return False, "A min_spread_pct értékének kisebbnek kell lennie, mint a max_spread_pct"
        
        return True, ""
