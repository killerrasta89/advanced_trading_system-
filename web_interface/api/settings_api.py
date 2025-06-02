"""
Web Interface API - Settings API
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import json
import time
from datetime import datetime

# Core komponensek importálása
from core.trading_engine import TradingEngine
from config.settings import Settings

# Adatbázis modellek importálása
from database.models import db, UserSettings

settings_api = Blueprint('settings_api', __name__)

@settings_api.route('/api/settings/user', methods=['GET'])
@login_required
def get_user_settings():
    """
    Felhasználói beállítások lekérdezése
    """
    try:
        # Beállítások lekérdezése
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            # Alapértelmezett beállítások
            settings = UserSettings(
                user_id=current_user.id,
                trading_enabled=False,
                notification_email=current_user.email,
                notification_telegram=None,
                notification_discord=None,
                risk_level='medium',
                max_open_trades=5,
                max_daily_trades=20,
                default_position_size=1.0,
                stop_loss_pct=2.0,
                take_profit_pct=3.0,
                ui_theme='light',
                ui_language='hu',
                ui_timezone='Europe/Budapest',
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.session.add(settings)
            db.session.commit()
        
        # Beállítások szótárrá alakítása
        settings_dict = {
            'trading_enabled': settings.trading_enabled,
            'notification_email': settings.notification_email,
            'notification_telegram': settings.notification_telegram,
            'notification_discord': settings.notification_discord,
            'risk_level': settings.risk_level,
            'max_open_trades': settings.max_open_trades,
            'max_daily_trades': settings.max_daily_trades,
            'default_position_size': settings.default_position_size,
            'stop_loss_pct': settings.stop_loss_pct,
            'take_profit_pct': settings.take_profit_pct,
            'ui_theme': settings.ui_theme,
            'ui_language': settings.ui_language,
            'ui_timezone': settings.ui_timezone,
            'created_at': settings.created_at.isoformat() if settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
        }
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': settings_dict,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/user', methods=['PUT'])
@login_required
def update_user_settings():
    """
    Felhasználói beállítások frissítése
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Beállítások lekérdezése
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            # Új beállítások létrehozása
            settings = UserSettings(
                user_id=current_user.id,
                created_at=datetime.now()
            )
            db.session.add(settings)
        
        # Beállítások frissítése
        if 'trading_enabled' in data:
            settings.trading_enabled = data['trading_enabled']
        if 'notification_email' in data:
            settings.notification_email = data['notification_email']
        if 'notification_telegram' in data:
            settings.notification_telegram = data['notification_telegram']
        if 'notification_discord' in data:
            settings.notification_discord = data['notification_discord']
        if 'risk_level' in data:
            settings.risk_level = data['risk_level']
        if 'max_open_trades' in data:
            settings.max_open_trades = data['max_open_trades']
        if 'max_daily_trades' in data:
            settings.max_daily_trades = data['max_daily_trades']
        if 'default_position_size' in data:
            settings.default_position_size = data['default_position_size']
        if 'stop_loss_pct' in data:
            settings.stop_loss_pct = data['stop_loss_pct']
        if 'take_profit_pct' in data:
            settings.take_profit_pct = data['take_profit_pct']
        if 'ui_theme' in data:
            settings.ui_theme = data['ui_theme']
        if 'ui_language' in data:
            settings.ui_language = data['ui_language']
        if 'ui_timezone' in data:
            settings.ui_timezone = data['ui_timezone']
        
        settings.updated_at = datetime.now()
        
        # Mentés
        db.session.commit()
        
        # Beállítások szótárrá alakítása
        settings_dict = {
            'trading_enabled': settings.trading_enabled,
            'notification_email': settings.notification_email,
            'notification_telegram': settings.notification_telegram,
            'notification_discord': settings.notification_discord,
            'risk_level': settings.risk_level,
            'max_open_trades': settings.max_open_trades,
            'max_daily_trades': settings.max_daily_trades,
            'default_position_size': settings.default_position_size,
            'stop_loss_pct': settings.stop_loss_pct,
            'take_profit_pct': settings.take_profit_pct,
            'ui_theme': settings.ui_theme,
            'ui_language': settings.ui_language,
            'ui_timezone': settings.ui_timezone,
            'created_at': settings.created_at.isoformat() if settings.created_at else None,
            'updated_at': settings.updated_at.isoformat() if settings.updated_at else None
        }
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': settings_dict,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/system', methods=['GET'])
@login_required
def get_system_settings():
    """
    Rendszer beállítások lekérdezése
    """
    try:
        # Rendszer beállítások lekérdezése
        settings = Settings.get_system_settings()
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': settings,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/system', methods=['PUT'])
@login_required
def update_system_settings():
    """
    Rendszer beállítások frissítése (csak admin felhasználók számára)
    """
    try:
        # Ellenőrizzük, hogy a felhasználó admin-e
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Nincs jogosultság',
                'timestamp': int(time.time())
            }), 403
        
        # Kérés adatok
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Rendszer beállítások frissítése
        settings = Settings.update_system_settings(data)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': settings,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/exchanges', methods=['GET'])
@login_required
def get_exchange_settings():
    """
    Tőzsde beállítások lekérdezése
    """
    try:
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Tőzsde beállítások lekérdezése
        exchange_settings = trading_engine.get_exchange_settings(current_user.id)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': exchange_settings,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/exchanges', methods=['PUT'])
@login_required
def update_exchange_settings():
    """
    Tőzsde beállítások frissítése
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'exchange' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Tőzsde beállítások frissítése
        result = trading_engine.update_exchange_settings(
            user_id=current_user.id,
            exchange=data.get('exchange'),
            api_key=data.get('api_key'),
            api_secret=data.get('api_secret'),
            passphrase=data.get('passphrase'),
            is_enabled=data.get('is_enabled', True)
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': result,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/notifications', methods=['GET'])
@login_required
def get_notification_settings():
    """
    Értesítési beállítások lekérdezése
    """
    try:
        # Beállítások lekérdezése
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            # Alapértelmezett beállítások
            notification_settings = {
                'email': {
                    'enabled': True,
                    'address': current_user.email
                },
                'telegram': {
                    'enabled': False,
                    'chat_id': None
                },
                'discord': {
                    'enabled': False,
                    'webhook_url': None
                },
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
                }
            }
        else:
            # Beállítások szótárrá alakítása
            notification_settings = {
                'email': {
                    'enabled': settings.notification_email is not None,
                    'address': settings.notification_email
                },
                'telegram': {
                    'enabled': settings.notification_telegram is not None,
                    'chat_id': settings.notification_telegram
                },
                'discord': {
                    'enabled': settings.notification_discord is not None,
                    'webhook_url': settings.notification_discord
                },
                'notification_types': json.loads(settings.notification_types) if settings.notification_types else {
                    'trade_executed': True,
                    'trade_closed': True,
                    'stop_loss_triggered': True,
                    'take_profit_triggered': True,
                    'strategy_started': True,
                    'strategy_stopped': True,
                    'system_error': True,
                    'balance_update': False,
                    'price_alert': False
                }
            }
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': notification_settings,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/notifications', methods=['PUT'])
@login_required
def update_notification_settings():
    """
    Értesítési beállítások frissítése
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Beállítások lekérdezése
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        
        if not settings:
            # Új beállítások létrehozása
            settings = UserSettings(
                user_id=current_user.id,
                created_at=datetime.now()
            )
            db.session.add(settings)
        
        # Beállítások frissítése
        if 'email' in data:
            if data['email'].get('enabled', True):
                settings.notification_email = data['email'].get('address', current_user.email)
            else:
                settings.notification_email = None
        
        if 'telegram' in data:
            if data['telegram'].get('enabled', False):
                settings.notification_telegram = data['telegram'].get('chat_id')
            else:
                settings.notification_telegram = None
        
        if 'discord' in data:
            if data['discord'].get('enabled', False):
                settings.notification_discord = data['discord'].get('webhook_url')
            else:
                settings.notification_discord = None
        
        if 'notification_types' in data:
            settings.notification_types = json.dumps(data['notification_types'])
        
        settings.updated_at = datetime.now()
        
        # Mentés
        db.session.commit()
        
        # Beállítások szótárrá alakítása
        notification_settings = {
            'email': {
                'enabled': settings.notification_email is not None,
                'address': settings.notification_email
            },
            'telegram': {
                'enabled': settings.notification_telegram is not None,
                'chat_id': settings.notification_telegram
            },
            'discord': {
                'enabled': settings.notification_discord is not None,
                'webhook_url': settings.notification_discord
            },
            'notification_types': json.loads(settings.notification_types) if settings.notification_types else {
                'trade_executed': True,
                'trade_closed': True,
                'stop_loss_triggered': True,
                'take_profit_triggered': True,
                'strategy_started': True,
                'strategy_stopped': True,
                'system_error': True,
                'balance_update': False,
                'price_alert': False
            }
        }
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': notification_settings,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@settings_api.route('/api/settings/test-notification', methods=['POST'])
@login_required
def test_notification():
    """
    Értesítés tesztelése
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'type' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        notification_type = data.get('type')
        
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Értesítés tesztelése
        result = trading_engine.test_notification(
            user_id=current_user.id,
            notification_type=notification_type
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': result,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500
