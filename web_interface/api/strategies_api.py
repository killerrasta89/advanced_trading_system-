"""
Web Interface API - Strategies API
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import json
import time
from datetime import datetime, timedelta

# Core komponensek importálása
from core.strategy_manager import StrategyManager
from core.trading_engine import TradingEngine

# Adatbázis modellek importálása
from database.models import db, Strategy, StrategyConfig

strategies_api = Blueprint('strategies_api', __name__)

@strategies_api.route('/api/strategies/list', methods=['GET'])
@login_required
def get_strategies_list():
    """
    Elérhető stratégiák listájának lekérdezése
    """
    try:
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégiák lekérdezése
        strategies = strategy_manager.get_available_strategies()
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': strategies,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@strategies_api.route('/api/strategies/active', methods=['GET'])
@login_required
def get_active_strategies():
    """
    Aktív stratégiák lekérdezése
    """
    try:
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Aktív stratégiák lekérdezése
        strategies = strategy_manager.get_active_strategies(current_user.id)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': strategies,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@strategies_api.route('/api/strategies/details/<strategy_id>', methods=['GET'])
@login_required
def get_strategy_details(strategy_id):
    """
    Stratégia részleteinek lekérdezése
    """
    try:
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégia részleteinek lekérdezése
        strategy = strategy_manager.get_strategy_details(strategy_id, current_user.id)
        
        if not strategy:
            return jsonify({
                'success': False,
                'error': 'Stratégia nem található',
                'timestamp': int(time.time())
            }), 404
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': strategy,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@strategies_api.route('/api/strategies/performance/<strategy_id>', methods=['GET'])
@login_required
def get_strategy_performance(strategy_id):
    """
    Stratégia teljesítményének lekérdezése
    """
    try:
        # Időszak paraméter
        period = request.args.get('period', 'month')
        
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
        
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégia teljesítményének lekérdezése
        performance = strategy_manager.get_strategy_performance(
            strategy_id,
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

@strategies_api.route('/api/strategies/create', methods=['POST'])
@login_required
def create_strategy():
    """
    Új stratégia létrehozása
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'strategy_type' not in data or 'symbol' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégia létrehozása
        strategy = strategy_manager.create_strategy(
            user_id=current_user.id,
            strategy_type=data.get('strategy_type'),
            symbol=data.get('symbol'),
            name=data.get('name'),
            config=data.get('config', {})
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': strategy,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@strategies_api.route('/api/strategies/update/<strategy_id>', methods=['PUT'])
@login_required
def update_strategy(strategy_id):
    """
    Stratégia frissítése
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
        
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégia frissítése
        strategy = strategy_manager.update_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id,
            name=data.get('name'),
            config=data.get('config')
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': strategy,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@strategies_api.route('/api/strategies/delete/<strategy_id>', methods=['DELETE'])
@login_required
def delete_strategy(strategy_id):
    """
    Stratégia törlése
    """
    try:
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégia törlése
        result = strategy_manager.delete_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
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

@strategies_api.route('/api/strategies/start/<strategy_id>', methods=['POST'])
@login_required
def start_strategy(strategy_id):
    """
    Stratégia indítása
    """
    try:
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégia indítása
        result = strategy_manager.start_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
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

@strategies_api.route('/api/strategies/stop/<strategy_id>', methods=['POST'])
@login_required
def stop_strategy(strategy_id):
    """
    Stratégia leállítása
    """
    try:
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégia leállítása
        result = strategy_manager.stop_strategy(
            strategy_id=strategy_id,
            user_id=current_user.id
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

@strategies_api.route('/api/strategies/backtest', methods=['POST'])
@login_required
def backtest_strategy():
    """
    Stratégia backtestje
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'strategy_type' not in data or 'symbol' not in data or 'start_date' not in data or 'end_date' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Stratégia backtestje
        result = trading_engine.backtest_strategy(
            user_id=current_user.id,
            strategy_type=data.get('strategy_type'),
            symbol=data.get('symbol'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            config=data.get('config', {})
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

@strategies_api.route('/api/strategies/compare', methods=['POST'])
@login_required
def compare_strategies():
    """
    Stratégiák összehasonlítása
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'strategy_ids' not in data or not isinstance(data.get('strategy_ids'), list):
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Strategy manager példányosítása
        strategy_manager = StrategyManager()
        
        # Stratégiák összehasonlítása
        result = strategy_manager.compare_strategies(
            user_id=current_user.id,
            strategy_ids=data.get('strategy_ids'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date')
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

@strategies_api.route('/api/strategies/optimize', methods=['POST'])
@login_required
def optimize_strategy():
    """
    Stratégia optimalizálása
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'strategy_type' not in data or 'symbol' not in data or 'parameters' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Stratégia optimalizálása
        result = trading_engine.optimize_strategy(
            user_id=current_user.id,
            strategy_type=data.get('strategy_type'),
            symbol=data.get('symbol'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            parameters=data.get('parameters'),
            optimization_metric=data.get('optimization_metric', 'sharpe_ratio')
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
