"""
Web Interface API - Portfolio API
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import json
import time
from datetime import datetime, timedelta

# Core komponensek importálása
from core.portfolio_manager import PortfolioManager
from core.market_data_manager import MarketDataManager

# Adatbázis modellek importálása
from database.models import db, Portfolio, Trade, Asset

portfolio_api = Blueprint('portfolio_api', __name__)

@portfolio_api.route('/api/portfolio/summary', methods=['GET'])
@login_required
def get_portfolio_summary():
    """
    Portfólió összefoglaló lekérdezése
    """
    try:
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Portfólió adatok lekérdezése
        portfolio_data = portfolio_manager.get_portfolio_summary(current_user.id)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': portfolio_data,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@portfolio_api.route('/api/portfolio/assets', methods=['GET'])
@login_required
def get_portfolio_assets():
    """
    Portfólió eszközök lekérdezése
    """
    try:
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Portfólió eszközök lekérdezése
        assets = portfolio_manager.get_portfolio_assets(current_user.id)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': assets,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@portfolio_api.route('/api/portfolio/performance', methods=['GET'])
@login_required
def get_portfolio_performance():
    """
    Portfólió teljesítmény lekérdezése
    """
    try:
        # Időszak paraméter
        period = request.args.get('period', 'day')
        
        # Időszak kezdete és vége
        end_date = datetime.now()
        
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Alapértelmezett: 30 nap
        
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Portfólió teljesítmény lekérdezése
        performance = portfolio_manager.get_portfolio_performance(
            current_user.id, 
            start_date, 
            end_date
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': performance,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@portfolio_api.route('/api/portfolio/trades', methods=['GET'])
@login_required
def get_portfolio_trades():
    """
    Portfólió kereskedések lekérdezése
    """
    try:
        # Paginálás paraméterek
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Szűrés paraméterek
        symbol = request.args.get('symbol')
        strategy = request.args.get('strategy')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Kereskedések lekérdezése
        trades, total = portfolio_manager.get_trades(
            current_user.id,
            page=page,
            per_page=per_page,
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': trades,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@portfolio_api.route('/api/portfolio/metrics', methods=['GET'])
@login_required
def get_portfolio_metrics():
    """
    Portfólió metrikák lekérdezése
    """
    try:
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Portfólió metrikák lekérdezése
        metrics = portfolio_manager.get_portfolio_metrics(current_user.id)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': metrics,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@portfolio_api.route('/api/portfolio/allocation', methods=['GET'])
@login_required
def get_portfolio_allocation():
    """
    Portfólió allokáció lekérdezése
    """
    try:
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Portfólió allokáció lekérdezése
        allocation = portfolio_manager.get_portfolio_allocation(current_user.id)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': allocation,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@portfolio_api.route('/api/portfolio/rebalance', methods=['POST'])
@login_required
def rebalance_portfolio():
    """
    Portfólió újraegyensúlyozása
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
        
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Portfólió újraegyensúlyozása
        result = portfolio_manager.rebalance_portfolio(
            current_user.id,
            data.get('target_allocation')
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

@portfolio_api.route('/api/portfolio/deposit', methods=['POST'])
@login_required
def deposit_to_portfolio():
    """
    Befizetés a portfólióba
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'asset' not in data or 'amount' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Befizetés a portfólióba
        result = portfolio_manager.deposit(
            current_user.id,
            data.get('asset'),
            float(data.get('amount')),
            data.get('description', 'Befizetés')
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

@portfolio_api.route('/api/portfolio/withdraw', methods=['POST'])
@login_required
def withdraw_from_portfolio():
    """
    Kifizetés a portfólióból
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'asset' not in data or 'amount' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Kifizetés a portfólióból
        result = portfolio_manager.withdraw(
            current_user.id,
            data.get('asset'),
            float(data.get('amount')),
            data.get('description', 'Kifizetés')
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

@portfolio_api.route('/api/portfolio/history', methods=['GET'])
@login_required
def get_portfolio_history():
    """
    Portfólió történet lekérdezése
    """
    try:
        # Időszak paraméter
        period = request.args.get('period', 'month')
        interval = request.args.get('interval', 'day')
        
        # Időszak kezdete és vége
        end_date = datetime.now()
        
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        elif period == 'year':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Alapértelmezett: 30 nap
        
        # Portfólió manager példányosítása
        portfolio_manager = PortfolioManager()
        
        # Portfólió történet lekérdezése
        history = portfolio_manager.get_portfolio_history(
            current_user.id,
            start_date,
            end_date,
            interval
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': history,
            'period': period,
            'interval': interval,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500
