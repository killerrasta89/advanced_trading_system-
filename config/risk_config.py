"""
Risk Config - Kockázatkezelési beállítások
"""
import json
import os

class RiskConfig:
    """
    Kockázatkezelési beállítások kezelése
    """
    
    # Alapértelmezett beállítások
    DEFAULT_SETTINGS = {
        # Általános kockázatkezelési beállítások
        'max_portfolio_risk_pct': 2.0,  # Maximális portfólió kockázat százalékban
        'max_position_size_pct': 5.0,   # Maximális pozíció méret százalékban
        'max_daily_drawdown_pct': 5.0,  # Maximális napi drawdown százalékban
        'max_total_drawdown_pct': 15.0, # Maximális teljes drawdown százalékban
        
        # Stop loss beállítások
        'default_stop_loss_pct': 2.0,   # Alapértelmezett stop loss százalékban
        'trailing_stop_enabled': True,   # Trailing stop engedélyezve
        'trailing_stop_activation_pct': 1.0, # Trailing stop aktiválási százalék
        'trailing_stop_distance_pct': 1.0,   # Trailing stop távolság százalékban
        
        # Take profit beállítások
        'default_take_profit_pct': 3.0,  # Alapértelmezett take profit százalékban
        'partial_take_profit_enabled': True, # Részleges take profit engedélyezve
        'partial_take_profit_levels': [   # Részleges take profit szintek
            {'pct': 1.0, 'size': 25.0},   # 1% profit: 25% pozíció zárása
            {'pct': 2.0, 'size': 25.0},   # 2% profit: további 25% pozíció zárása
            {'pct': 3.0, 'size': 25.0},   # 3% profit: további 25% pozíció zárása
            {'pct': 5.0, 'size': 25.0}    # 5% profit: maradék 25% pozíció zárása
        ],
        
        # Pozíció méretezés beállítások
        'position_sizing_method': 'risk_based',  # risk_based, fixed, kelly
        'fixed_position_size': 100.0,     # Fix pozíció méret (USDT)
        'risk_per_trade_pct': 1.0,        # Kockázat kereskedésenként (%)
        'kelly_fraction': 0.5,            # Kelly hányados (0-1)
        
        # Volatilitás alapú beállítások
        'volatility_adjustment_enabled': True,  # Volatilitás alapú beállítás engedélyezve
        'volatility_lookback_period': 20,       # Volatilitás visszatekintési periódus
        'volatility_risk_factor': 1.0,          # Volatilitás kockázati faktor
        'max_volatility_multiplier': 2.0,       # Maximális volatilitás szorzó
        'min_volatility_multiplier': 0.5,       # Minimális volatilitás szorzó
        
        # Korreláció beállítások
        'correlation_check_enabled': True,      # Korreláció ellenőrzés engedélyezve
        'correlation_lookback_period': 30,      # Korreláció visszatekintési periódus
        'max_correlation_threshold': 0.7,       # Maximális korreláció küszöbérték
        'max_correlated_positions': 3,          # Maximális korrelált pozíciók száma
        
        # Drawdown kezelés
        'drawdown_protection_enabled': True,    # Drawdown védelem engedélyezve
        'daily_drawdown_action': 'reduce_size', # reduce_size, pause_trading, stop_trading
        'total_drawdown_action': 'pause_trading', # reduce_size, pause_trading, stop_trading
        'drawdown_recovery_threshold': 50.0,    # Drawdown helyreállítási küszöbérték (%)
        
        # Kockázati limitek
        'max_open_trades': 10,                  # Maximális nyitott kereskedések száma
        'max_daily_trades': 20,                 # Maximális napi kereskedések száma
        'max_open_trades_per_pair': 3,          # Maximális nyitott kereskedések száma páronként
        'max_daily_trades_per_pair': 5,         # Maximális napi kereskedések száma páronként
        
        # Időzítés beállítások
        'trading_hours_enabled': False,         # Kereskedési órák engedélyezve
        'trading_hours_start': '09:00',         # Kereskedési órák kezdete
        'trading_hours_end': '17:00',           # Kereskedési órák vége
        'trading_days': [0, 1, 2, 3, 4, 5, 6],  # Kereskedési napok (0: hétfő, 6: vasárnap)
        
        # Piaci feltételek
        'market_condition_check_enabled': True, # Piaci feltételek ellenőrzése engedélyezve
        'market_trend_indicators': ['sma', 'ema', 'macd'], # Piaci trend indikátorok
        'market_volatility_indicators': ['atr', 'bollinger_bands'], # Piaci volatilitás indikátorok
        'market_volume_indicators': ['obv', 'volume_sma'], # Piaci volumen indikátorok
    }
    
    @classmethod
    def get_risk_settings(cls):
        """
        Kockázatkezelési beállítások lekérdezése
        
        Returns:
            dict: Kockázatkezelési beállítások
        """
        # Beállítások fájl elérési útja
        settings_file = os.path.join('config', 'risk_settings.json')
        
        # Ha a fájl létezik, betöltjük
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                # Alapértelmezett beállítások kiegészítése a betöltött beállításokkal
                merged_settings = cls.DEFAULT_SETTINGS.copy()
                merged_settings.update(settings)
                
                return merged_settings
            except Exception as e:
                print(f"Hiba a beállítások betöltése során: {e}")
                return cls.DEFAULT_SETTINGS
        else:
            # Ha a fájl nem létezik, létrehozzuk az alapértelmezett beállításokkal
            try:
                os.makedirs(os.path.dirname(settings_file), exist_ok=True)
                with open(settings_file, 'w') as f:
                    json.dump(cls.DEFAULT_SETTINGS, f, indent=4)
            except Exception as e:
                print(f"Hiba a beállítások mentése során: {e}")
            
            return cls.DEFAULT_SETTINGS
    
    @classmethod
    def update_risk_settings(cls, settings):
        """
        Kockázatkezelési beállítások frissítése
        
        Args:
            settings (dict): Frissítendő beállítások
            
        Returns:
            dict: Frissített kockázatkezelési beállítások
        """
        # Aktuális beállítások lekérdezése
        current_settings = cls.get_risk_settings()
        
        # Beállítások frissítése
        current_settings.update(settings)
        
        # Beállítások mentése
        settings_file = os.path.join('config', 'risk_settings.json')
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(current_settings, f, indent=4)
        except Exception as e:
            print(f"Hiba a beállítások mentése során: {e}")
        
        return current_settings
    
    @classmethod
    def get_setting(cls, key, default=None):
        """
        Egy beállítás lekérdezése
        
        Args:
            key (str): Beállítás kulcsa
            default: Alapértelmezett érték, ha a beállítás nem található
            
        Returns:
            Beállítás értéke vagy az alapértelmezett érték
        """
        settings = cls.get_risk_settings()
        return settings.get(key, default)
    
    @classmethod
    def set_setting(cls, key, value):
        """
        Egy beállítás beállítása
        
        Args:
            key (str): Beállítás kulcsa
            value: Beállítás értéke
            
        Returns:
            bool: Sikeres-e a beállítás
        """
        settings = cls.get_risk_settings()
        settings[key] = value
        
        # Beállítások mentése
        settings_file = os.path.join('config', 'risk_settings.json')
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Hiba a beállítások mentése során: {e}")
            return False
