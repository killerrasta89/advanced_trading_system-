import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

# Konfiguráció betöltése
load_dotenv()

# Alkalmazás inicializálása
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-trading-system')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trading_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Adatbázis inicializálása
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Login manager inicializálása
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Naplózás beállítása
if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/trading_system.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Trading System startup')

# Blueprint regisztrálása
from src.routes.main import main_bp
from src.routes.api import api_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/health')
def health_check():
    return jsonify({"status": "ok", "version": "1.0.0"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
