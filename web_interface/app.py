"""
Web Interface App - A fő Flask alkalmazás
"""
import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from datetime import timedelta
import logging

# Adatbázis importálása
from database.models import db, User

# API Blueprint-ek importálása
from web_interface.api.portfolio_api import portfolio_api
from web_interface.api.trades_api import trades_api
from web_interface.api.strategies_api import strategies_api
from web_interface.api.settings_api import settings_api
from web_interface.api.market_data_api import market_data_api

# Útvonal Blueprint-ek importálása
from src.routes.main import main_bp
from src.routes.api import api_bp

# Konfiguráció importálása
from config.settings import Settings

def create_app():
    """
    Flask alkalmazás létrehozása
    
    Returns:
        Flask: Flask alkalmazás
    """
    # Flask alkalmazás létrehozása
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Konfiguráció beállítása
    configure_app(app)
    
    # Adatbázis inicializálása
    init_db(app)
    
    # Login manager inicializálása
    init_login_manager(app)
    
    # Blueprint-ek regisztrálása
    register_blueprints(app)
    
    # Hibaoldalak beállítása
    register_error_handlers(app)
    
    # Kontextus processzorok beállítása
    register_context_processors(app)
    
    # Jinja2 szűrők beállítása
    register_jinja_filters(app)
    
    return app

def configure_app(app):
    """
    Flask alkalmazás konfigurálása
    
    Args:
        app (Flask): Flask alkalmazás
    """
    # Titkos kulcs beállítása
    app.config['SECRET_KEY'] = Settings.get_setting('web_secret_key', 'advanced_trading_system_secret_key')
    
    # Munkamenet élettartam beállítása
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=Settings.get_setting('web_session_lifetime', 86400))
    
    # SQLAlchemy beállítások
    db_type = Settings.get_setting('db_type', 'sqlite')
    
    if db_type == 'sqlite':
        db_path = Settings.get_setting('db_name', 'data/trading.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    elif db_type == 'mysql':
        db_host = Settings.get_setting('db_host', 'localhost')
        db_port = Settings.get_setting('db_port', 3306)
        db_name = Settings.get_setting('db_name', 'trading')
        db_user = Settings.get_setting('db_user', 'root')
        db_password = Settings.get_setting('db_password', '')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Debug mód beállítása
    app.config['DEBUG'] = Settings.get_setting('web_debug', False)
    
    # Feltöltési mappa beállítása
    app.config['UPLOAD_FOLDER'] = os.path.join('data', 'uploads')
    
    # Max feltöltési méret beállítása
    app.config['MAX_CONTENT_LENGTH'] = Settings.get_setting('web_max_upload_size_mb', 10) * 1024 * 1024

def init_db(app):
    """
    Adatbázis inicializálása
    
    Args:
        app (Flask): Flask alkalmazás
    """
    db.init_app(app)
    
    # Migráció inicializálása
    migrate = Migrate(app, db)
    
    # Adatbázis létrehozása, ha nem létezik
    with app.app_context():
        db.create_all()
        
        # Admin felhasználó létrehozása, ha nem létezik
        if not User.query.filter_by(username='admin').first():
            from werkzeug.security import generate_password_hash
            
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin'),
                is_active=True,
                is_admin=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            logging.info("Admin felhasználó létrehozva")

def init_login_manager(app):
    """
    Login manager inicializálása
    
    Args:
        app (Flask): Flask alkalmazás
    """
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Kérjük, jelentkezzen be a folytatáshoz'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

def register_blueprints(app):
    """
    Blueprint-ek regisztrálása
    
    Args:
        app (Flask): Flask alkalmazás
    """
    # Fő Blueprint-ek
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # API Blueprint-ek
    app.register_blueprint(portfolio_api)
    app.register_blueprint(trades_api)
    app.register_blueprint(strategies_api)
    app.register_blueprint(settings_api)
    app.register_blueprint(market_data_api)

def register_error_handlers(app):
    """
    Hibaoldalak beállítása
    
    Args:
        app (Flask): Flask alkalmazás
    """
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

def register_context_processors(app):
    """
    Kontextus processzorok beállítása
    
    Args:
        app (Flask): Flask alkalmazás
    """
    @app.context_processor
    def inject_settings():
        """
        Beállítások injektálása a sablonokba
        """
        return {
            'app_name': Settings.get_setting('app_name', 'Advanced Trading System'),
            'app_version': Settings.get_setting('app_version', '1.0.0')
        }

def register_jinja_filters(app):
    """
    Jinja2 szűrők beállítása
    
    Args:
        app (Flask): Flask alkalmazás
    """
    @app.template_filter('format_number')
    def format_number(value):
        """
        Szám formázása
        """
        if value is None:
            return '-'
        
        try:
            if isinstance(value, int):
                return f"{value:,}".replace(',', ' ')
            elif isinstance(value, float):
                if value >= 1000:
                    return f"{value:,.2f}".replace(',', ' ')
                else:
                    return f"{value:.6f}".rstrip('0').rstrip('.')
            else:
                return value
        except:
            return value
    
    @app.template_filter('format_datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        """
        Dátum formázása
        """
        if value is None:
            return '-'
        
        try:
            return value.strftime(format)
        except:
            return value
    
    @app.template_filter('format_price')
    def format_price(value, currency='USDT'):
        """
        Ár formázása
        """
        if value is None:
            return '-'
        
        try:
            if value >= 1000:
                return f"{value:,.2f} {currency}".replace(',', ' ')
            elif value >= 1:
                return f"{value:.2f} {currency}"
            else:
                return f"{value:.8f} {currency}".rstrip('0').rstrip('.')
        except:
            return value
