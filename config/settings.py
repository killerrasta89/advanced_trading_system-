"""
Settings - Alap konfigurációk
"""
import os
import json
from datetime import datetime

class Settings:
    """
    Rendszer beállítások kezelése
    """
    
    # Alapértelmezett beállítások
    DEFAULT_SETTINGS = {
        # Általános beállítások
        'app_name': 'Advanced Trading System',
        'app_version': '1.0.0',
        'debug_mode': False,
        'log_level': 'INFO',
        'log_file': 'logs/system.log',
        'data_dir': 'data',
        
        # Adatbázis beállítások
        'db_type': 'sqlite',
        'db_name': 'data/trading.db',
        'db_backup_interval': 86400,  # 24 óra másodpercben
        
        # Kereskedési beállítások
        'default_exchange': 'binance',
        'default_timeframe': '1h',
        'default_symbols': ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'ADA/USDT', 'SOL/USDT'],
        'max_open_trades_per_user': 10,
        'max_daily_trades_per_user': 50,
        'min_order_amount_usdt': 10.0,
        'max_order_amount_usdt': 1000.0,
        
        # Piaci adatok beállítások
        'market_data_update_interval': 60,  # 1 perc másodpercben
        'ohlcv_history_limit': 1000,
        'price_data_retention_days': 90,
        
        # Értesítési beállítások
        'notification_enabled': True,
        'email_notification_enabled': True,
        'telegram_notification_enabled': True,
        'discord_notification_enabled': True,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_username': '',
        'smtp_password': '',
        'telegram_bot_token': '',
        'discord_webhook_url': '',
        
        # Teljesítmény optimalizálás
        'rpi4_optimization_enabled': True,
        'max_memory_usage_mb': 1500,  # 2GB RAM-ból max 1.5GB használata
        'max_cpu_usage_percent': 80,
        'max_threads': 4,
        'cache_enabled': True,
        'cache_max_size_mb': 200,
        'storage_cleanup_interval': 86400,  # 24 óra másodpercben
        
        # Web felület beállítások
        'web_host': '0.0.0.0',
        'web_port': 5000,
        'web_debug': False,
        'web_secret_key': 'advanced_trading_system_secret_key',
        'web_session_lifetime': 86400,  # 24 óra másodpercben
        'web_login_required': True,
        'web_allow_registration': True,
        'web_max_upload_size_mb': 10,
        
        # Backtesting beállítások
        'backtest_default_period': 90,  # 90 nap
        'backtest_max_period': 365,  # 1 év
        'backtest_default_deposit': 1000.0,  # USDT
        'backtest_default_commission': 0.1,  # 0.1%
        
        # Rendszer monitorozás
        'system_monitor_interval': 60,  # 1 perc másodpercben
        'health_check_interval': 300,  # 5 perc másodpercben
        'alert_threshold_cpu': 90,  # 90% CPU használat
        'alert_threshold_memory': 90,  # 90% memória használat
        'alert_threshold_disk': 90,  # 90% tárhely használat
        'alert_threshold_temperature': 80,  # 80°C
        
        # Frissítés és karbantartás
        'auto_update_check': True,
        'update_check_interval': 86400,  # 24 óra másodpercben
        'auto_backup_enabled': True,
        'backup_interval': 86400,  # 24 óra másodpercben
        'max_backups': 7,
        'maintenance_mode': False,
        'maintenance_schedule': '0 3 * * 0',  # Vasárnap 3:00
    }
    
    @classmethod
    def get_system_settings(cls):
        """
        Rendszer beállítások lekérdezése
        
        Returns:
            dict: Rendszer beállítások
        """
        # Beállítások fájl elérési útja
        settings_file = os.path.join('config', 'system_settings.json')
        
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
    def update_system_settings(cls, settings):
        """
        Rendszer beállítások frissítése
        
        Args:
            settings (dict): Frissítendő beállítások
            
        Returns:
            dict: Frissített rendszer beállítások
        """
        # Aktuális beállítások lekérdezése
        current_settings = cls.get_system_settings()
        
        # Beállítások frissítése
        current_settings.update(settings)
        
        # Beállítások mentése
        settings_file = os.path.join('config', 'system_settings.json')
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
        settings = cls.get_system_settings()
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
        settings = cls.get_system_settings()
        settings[key] = value
        
        # Beállítások mentése
        settings_file = os.path.join('config', 'system_settings.json')
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Hiba a beállítások mentése során: {e}")
            return False
