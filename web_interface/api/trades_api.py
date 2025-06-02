"""
Web Interface API - Trades API
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import json
import time
from datetime import datetime, timedelta

# Core komponensek importálása
from core.order_manager import OrderManager
from core.trading_engine import TradingEngine
from core.market_data_manager import MarketDataManager

# Adatbázis modellek importálása
from database.models import db, Trade, Order

trades_api = Blueprint('trades_api', __name__)

@trades_api.route('/api/trades/recent', methods=['GET'])
@login_required
def get_recent_trades():
    """
    Legutóbbi kereskedések lekérdezése
    """
    try:
        # Paginálás paraméterek
        limit = int(request.args.get('limit', 20))
        
        # Order manager példányosítása
        order_manager = OrderManager()
        
        # Legutóbbi kereskedések lekérdezése
        trades = order_manager.get_recent_trades(current_user.id, limit)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': trades,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@trades_api.route('/api/trades/history', methods=['GET'])
@login_required
def get_trade_history():
    """
    Kereskedési történet lekérdezése
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
        trade_type = request.args.get('type')  # buy, sell
        status = request.args.get('status')  # open, closed
        
        # Order manager példányosítása
        order_manager = OrderManager()
        
        # Kereskedési történet lekérdezése
        trades, total = order_manager.get_trade_history(
            current_user.id,
            page=page,
            per_page=per_page,
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            trade_type=trade_type,
            status=status
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

@trades_api.route('/api/trades/open', methods=['GET'])
@login_required
def get_open_trades():
    """
    Nyitott kereskedések lekérdezése
    """
    try:
        # Order manager példányosítása
        order_manager = OrderManager()
        
        # Nyitott kereskedések lekérdezése
        trades = order_manager.get_open_trades(current_user.id)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': trades,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@trades_api.route('/api/trades/create', methods=['POST'])
@login_required
def create_trade():
    """
    Új kereskedés létrehozása
    """
    try:
        # Kérés adatok
        data = request.get_json()
        
        if not data or 'symbol' not in data or 'side' not in data or 'amount' not in data:
            return jsonify({
                'success': False,
                'error': 'Hiányzó adatok',
                'timestamp': int(time.time())
            }), 400
        
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Kereskedés létrehozása
        trade = trading_engine.create_manual_trade(
            user_id=current_user.id,
            symbol=data.get('symbol'),
            side=data.get('side'),
            amount=float(data.get('amount')),
            price=float(data.get('price')) if 'price' in data else None,
            order_type=data.get('order_type', 'market'),
            stop_loss=float(data.get('stop_loss')) if 'stop_loss' in data else None,
            take_profit=float(data.get('take_profit')) if 'take_profit' in data else None
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': trade,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@trades_api.route('/api/trades/close/<trade_id>', methods=['POST'])
@login_required
def close_trade(trade_id):
    """
    Kereskedés lezárása
    """
    try:
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Kereskedés lezárása
        result = trading_engine.close_trade(
            user_id=current_user.id,
            trade_id=trade_id
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

@trades_api.route('/api/trades/update/<trade_id>', methods=['PUT'])
@login_required
def update_trade(trade_id):
    """
    Kereskedés frissítése
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
        
        # Trading engine példányosítása
        trading_engine = TradingEngine()
        
        # Kereskedés frissítése
        result = trading_engine.update_trade(
            user_id=current_user.id,
            trade_id=trade_id,
            stop_loss=float(data.get('stop_loss')) if 'stop_loss' in data else None,
            take_profit=float(data.get('take_profit')) if 'take_profit' in data else None
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

@trades_api.route('/api/trades/performance', methods=['GET'])
@login_required
def get_trade_performance():
    """
    Kereskedési teljesítmény lekérdezése
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
        
        # Order manager példányosítása
        order_manager = OrderManager()
        
        # Kereskedési teljesítmény lekérdezése
        performance = order_manager.get_trade_performance(
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

@trades_api.route('/api/trades/statistics', methods=['GET'])
@login_required
def get_trade_statistics():
    """
    Kereskedési statisztikák lekérdezése
    """
    try:
        # Időszak paraméter
        period = request.args.get('period', 'all')
        
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
        elif period == 'all':
            start_date = None
        else:
            start_date = None  # Alapértelmezett: összes
        
        # Order manager példányosítása
        order_manager = OrderManager()
        
        # Kereskedési statisztikák lekérdezése
        statistics = order_manager.get_trade_statistics(
            current_user.id,
            start_date,
            end_date
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': statistics,
            'period': period,
            'start_date': start_date.isoformat() if start_date else None,
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

@trades_api.route('/api/trades/orders', methods=['GET'])
@login_required
def get_orders():
    """
    Megbízások lekérdezése
    """
    try:
        # Paginálás paraméterek
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # Szűrés paraméterek
        symbol = request.args.get('symbol')
        status = request.args.get('status')  # open, closed, canceled
        order_type = request.args.get('type')  # market, limit, stop
        
        # Order manager példányosítása
        order_manager = OrderManager()
        
        # Megbízások lekérdezése
        orders, total = order_manager.get_orders(
            current_user.id,
            page=page,
            per_page=per_page,
            symbol=symbol,
            status=status,
            order_type=order_type
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': orders,
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

@trades_api.route('/api/trades/cancel-order/<order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    """
    Megbízás törlése
    """
    try:
        # Order manager példányosítása
        order_manager = OrderManager()
        
        # Megbízás törlése
        result = order_manager.cancel_order(
            user_id=current_user.id,
            order_id=order_id
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
