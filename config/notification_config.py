"""
Notification Config - Értesítési beállítások
"""
import json
import os

class NotificationConfig:
    """
    Értesítési beállítások kezelése
    """
    
    # Alapértelmezett beállítások
    DEFAULT_SETTINGS = {
        # Általános értesítési beállítások
        'notifications_enabled': True,
        'notification_types': {
            'trade_executed': True,
            'trade_closed': True,
            'stop_loss_triggered': True,
            'take_profit_triggered': True,
            'strategy_started': True,
            'strategy_stopped': True,
            'system_error': True,
            'balance_update': False,
            'price_alert': False
        },
        
        # Email értesítések
        'email_enabled': True,
        'email_provider': 'smtp',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'smtp_username': '',
        'smtp_password': '',
        'email_from': '',
        'email_to': [],
        'email_subject_prefix': '[Advanced Trading System]',
        
        # Telegram értesítések
        'telegram_enabled': False,
        'telegram_bot_token': '',
        'telegram_chat_ids': [],
        
        # Discord értesítések
        'discord_enabled': False,
        'discord_webhook_url': '',
        
        # Webhook értesítések
        'webhook_enabled': False,
        'webhook_url': '',
        'webhook_headers': {},
        
        # Értesítési szintek
        'notification_levels': {
            'info': True,
            'warning': True,
            'error': True,
            'critical': True
        },
        
        # Értesítési időszakok
        'notification_hours_enabled': False,
        'notification_hours_start': '09:00',
        'notification_hours_end': '22:00',
        'notification_days': [0, 1, 2, 3, 4, 5, 6],  # 0: hétfő, 6: vasárnap
        
        # Értesítési gyakoriság
        'notification_frequency': {
            'max_per_minute': 10,
            'max_per_hour': 60,
            'max_per_day': 100
        },
        
        # Értesítési formátumok
        'notification_formats': {
            'trade_executed': '{time} - {strategy} stratégia {side} {amount} {symbol} áron: {price}',
            'trade_closed': '{time} - {strategy} stratégia lezárta a {symbol} pozíciót. Eredmény: {pnl} ({pnl_pct}%)',
            'stop_loss_triggered': '{time} - Stop loss aktiválva: {symbol} áron: {price}',
            'take_profit_triggered': '{time} - Take profit aktiválva: {symbol} áron: {price}',
            'strategy_started': '{time} - {strategy} stratégia elindítva',
            'strategy_stopped': '{time} - {strategy} stratégia leállítva',
            'system_error': '{time} - Rendszerhiba: {error}',
            'balance_update': '{time} - Egyenleg frissítve: {balance}',
            'price_alert': '{time} - Árfolyam riasztás: {symbol} elérte a(z) {price} árat'
        }
    }
    
    @classmethod
    def get_notification_settings(cls):
        """
        Értesítési beállítások lekérdezése
        
        Returns:
            dict: Értesítési beállítások
        """
        # Beállítások fájl elérési útja
        settings_file = os.path.join('config', 'notification_settings.json')
        
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
    def update_notification_settings(cls, settings):
        """
        Értesítési beállítások frissítése
        
        Args:
            settings (dict): Frissítendő beállítások
            
        Returns:
            dict: Frissített értesítési beállítások
        """
        # Aktuális beállítások lekérdezése
        current_settings = cls.get_notification_settings()
        
        # Beállítások frissítése
        current_settings.update(settings)
        
        # Beállítások mentése
        settings_file = os.path.join('config', 'notification_settings.json')
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
        settings = cls.get_notification_settings()
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
        settings = cls.get_notification_settings()
        settings[key] = value
        
        # Beállítások mentése
        settings_file = os.path.join('config', 'notification_settings.json')
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Hiba a beállítások mentése során: {e}")
            return False
    
    @classmethod
    def is_notification_enabled(cls, notification_type):
        """
        Értesítés engedélyezettségének ellenőrzése
        
        Args:
            notification_type (str): Értesítés típusa
            
        Returns:
            bool: Engedélyezett-e az értesítés
        """
        settings = cls.get_notification_settings()
        
        # Ellenőrizzük, hogy az értesítések engedélyezve vannak-e
        if not settings.get('notifications_enabled', True):
            return False
        
        # Ellenőrizzük, hogy az adott típusú értesítés engedélyezve van-e
        notification_types = settings.get('notification_types', {})
        return notification_types.get(notification_type, True)
    
    @classmethod
    def get_notification_format(cls, notification_type):
        """
        Értesítési formátum lekérdezése
        
        Args:
            notification_type (str): Értesítés típusa
            
        Returns:
            str: Értesítési formátum
        """
        settings = cls.get_notification_settings()
        notification_formats = settings.get('notification_formats', {})
        return notification_formats.get(notification_type, '{time} - {message}')
