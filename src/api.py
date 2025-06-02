"""
API Blueprint - API útvonalak a webes felülethez
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import json
import os
import time
from datetime import datetime, timedelta
import psutil

# Adatbázis modellek importálása
from src.models.models import db, User, Settings, TradeLog, PerformanceMetrics, SystemStatus, Notification

# Blueprint létrehozása
api_bp = Blueprint('api_bp', __name__)

# API - Rendszer állapot
@api_bp.route('/system/status', methods=['GET'])
@login_required
def system_status():
    # Rendszer állapot lekérdezése
    status = SystemStatus.query.order_by(SystemStatus.timestamp.desc()).first()
    
    # Valós rendszer erőforrás használat
    cpu_usage = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    
    # CPU hőmérséklet (csak Raspberry Pi-n működik)
    cpu_temp = None
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            cpu_temp = float(f.read()) / 1000.0
    except:
        cpu_temp = 45.0  # Szimulált érték, ha nem sikerül kiolvasni
    
    # Hálózati forgalom
    net_io = psutil.net_io_counters()
    
    # Válasz összeállítása
    response = {
        "timestamp": datetime.now().isoformat(),
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "disk_usage": disk_usage,
        "cpu_temp": cpu_temp,
        "network": {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv
        },
        "trading_engine_status": status.status if status else "unknown",
        "active_strategies": status.active_strategies if status else 0
    }
    
    return jsonify(response)

# API - Rendszer állapot történet
@api_bp.route('/system/history', methods=['GET'])
@login_required
def system_history():
    # Paraméterek
    hours = request.args.get('hours', default=24, type=int)
    
    # Időkorlát
    time_limit = datetime.now() - timedelta(hours=hours)
    
    # Rendszer állapot előzmények
    statuses = SystemStatus.query.filter(SystemStatus.timestamp >= time_limit).order_by(SystemStatus.timestamp.asc()).all()
    
    # Válasz összeállítása
    response = {
        "timestamps": [status.timestamp.isoformat() for status in statuses],
        "cpu_usage": [status.cpu_usage for status in statuses],
        "memory_usage": [status.memory_usage for status in statuses],
        "disk_usage": [status.disk_usage for status in statuses],
        "active_strategies": [status.active_strategies for status in statuses]
    }
    
    return jsonify(response)

# API - Portfólió adatok
@api_bp.route('/portfolio/summary', methods=['GET'])
@login_required
def portfolio_summary():
    # Portfólió adatok (szimulált adatok)
    portfolio_assets = [
        {"symbol": "BTC", "amount": 0.5, "value_usd": 22500.0, "allocation": 45.0, "avg_price": 42000.0, "current_price": 45000.0, "pnl": 1500.0, "pnl_percent": 7.1},
        {"symbol": "ETH", "amount": 5.0, "value_usd": 16000.0, "allocation": 32.0, "avg_price": 3000.0, "current_price": 3200.0, "pnl": 1000.0, "pnl_percent": 6.7},
        {"symbol": "BNB", "amount": 20.0, "value_usd": 8400.0, "allocation": 16.8, "avg_price": 400.0, "current_price": 420.0, "pnl": 400.0, "pnl_percent": 5.0},
        {"symbol": "USDT", "amount": 3100.0, "value_usd": 3100.0, "allocation": 6.2, "avg_price": 1.0, "current_price": 1.0, "pnl": 0.0, "pnl_percent": 0.0}
    ]
    
    # Portfólió összesítés
    portfolio_summary = {
        "total_value": sum(asset["value_usd"] for asset in portfolio_assets),
        "total_pnl": sum(asset["pnl"] for asset in portfolio_assets),
        "total_pnl_percent": sum(asset["pnl"] for asset in portfolio_assets) / sum(asset["value_usd"] for asset in portfolio_assets) * 100 if sum(asset["value_usd"] for asset in portfolio_assets) > 0 else 0,
        "asset_count": len(portfolio_assets),
        "assets": portfolio_assets
    }
    
    return jsonify(portfolio_summary)

# API - Portfólió történet
@api_bp.route('/portfolio/history', methods=['GET'])
@login_required
def portfolio_history():
    # Paraméterek
    days = request.args.get('days', default=30, type=int)
    
    # Portfólió történet (szimulált adatok)
    history = []
    
    # Kezdeti érték
    initial_value = 45000.0
    
    # Generál napi adatokat
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        
        # Szimulált napi változás (-1% és +1% között)
        daily_change = (((i * 7) % 10) - 5) / 500.0  # Determinisztikus, de változatos értékek
        
        # Kumulatív érték
        value = initial_value * (1 + daily_change * (i+1))
        
        history.append({
            "date": date,
            "value": value,
            "change_percent": daily_change * 100
        })
    
    return jsonify(history)

# API - Kereskedési előzmények
@api_bp.route('/trades/history', methods=['GET'])
@login_required
def trade_history():
    # Paraméterek
    limit = request.args.get('limit', default=50, type=int)
    symbol = request.args.get('symbol', default=None, type=str)
    strategy = request.args.get('strategy', default=None, type=str)
    
    # Lekérdezés építése
    query = TradeLog.query
    
    if symbol:
        query = query.filter(TradeLog.symbol == symbol)
    
    if strategy:
        query = query.filter(TradeLog.strategy == strategy)
    
    # Kereskedési előzmények lekérdezése
    trades = query.order_by(TradeLog.timestamp.desc()).limit(limit).all()
    
    # Válasz összeállítása
    response = []
    
    for trade in trades:
        response.append({
            "id": trade.id,
            "symbol": trade.symbol,
            "side": trade.side,
            "quantity": trade.quantity,
            "price": trade.price,
            "timestamp": trade.timestamp.isoformat(),
            "strategy": trade.strategy,
            "pnl": trade.pnl,
            "status": trade.status,
            "exchange": trade.exchange
        })
    
    return jsonify(response)

# API - Stratégiák
@api_bp.route('/strategies', methods=['GET'])
@login_required
def strategies():
    # Stratégiák (szimulált adatok)
    strategies = [
        {
            "id": 1,
            "name": "Grid Trading",
            "description": "Automatikus vételi és eladási megbízások létrehozása előre meghatározott ársávokon belül.",
            "status": "active",
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "performance": {
                "profit": 2.5,
                "trades": 12,
                "win_rate": 75.0,
                "avg_profit": 0.21
            }
        },
        {
            "id": 2,
            "name": "DCA (Dollar Cost Averaging)",
            "description": "Rendszeres időközönként történő vásárlás az átlagos bekerülési ár optimalizálásához.",
            "status": "active",
            "symbols": ["BTC/USDT"],
            "performance": {
                "profit": 1.8,
                "trades": 8,
                "win_rate": 62.5,
                "avg_profit": 0.23
            }
        },
        {
            "id": 3,
            "name": "Momentum",
            "description": "Trendkövető stratégia, amely a piaci momentum alapján kereskedik.",
            "status": "paused",
            "symbols": ["BNB/USDT", "SOL/USDT"],
            "performance": {
                "profit": -0.5,
                "trades": 3,
                "win_rate": 33.3,
                "avg_profit": -0.17
            }
        },
        {
            "id": 4,
            "name": "Mean Reversion",
            "description": "Az átlaghoz való visszatérés elvén alapuló stratégia.",
            "status": "inactive",
            "symbols": [],
            "performance": {
                "profit": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0
            }
        },
        {
            "id": 5,
            "name": "Arbitrage",
            "description": "Különböző piacok közötti árkülönbségek kihasználása.",
            "status": "inactive",
            "symbols": [],
            "performance": {
                "profit": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0
            }
        },
        {
            "id": 6,
            "name": "ML Prediction",
            "description": "Gépi tanulás alapú árfolyam előrejelzés.",
            "status": "inactive",
            "symbols": [],
            "performance": {
                "profit": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "avg_profit": 0.0
            }
        }
    ]
    
    return jsonify(strategies)

# API - Stratégia részletek
@api_bp.route('/strategy/<int:strategy_id>', methods=['GET'])
@login_required
def strategy_details(strategy_id):
    # Stratégia adatok (szimulált adatok)
    strategies = [
        {
            "id": 1,
            "name": "Grid Trading",
            "description": "Automatikus vételi és eladási megbízások létrehozása előre meghatározott ársávokon belül.",
            "status": "active",
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "parameters": {
                "grid_levels": 10,
                "upper_price": 50000,
                "lower_price": 40000,
                "investment_amount": 5000,
                "take_profit": 2.0,
                "stop_loss": 5.0
            },
            "performance": {
                "profit": 2.5,
                "trades": 12,
                "win_rate": 75.0,
                "avg_profit": 0.21,
                "max_drawdown": 1.2,
                "sharpe_ratio": 1.8
            }
        },
        {
            "id": 2,
            "name": "DCA (Dollar Cost Averaging)",
            "description": "Rendszeres időközönként történő vásárlás az átlagos bekerülési ár optimalizálásához.",
            "status": "active",
            "symbols": ["BTC/USDT"],
            "parameters": {
                "interval_hours": 24,
                "investment_amount": 100,
                "total_periods": 30,
                "completed_periods": 8
            },
            "performance": {
                "profit": 1.8,
                "trades": 8,
                "win_rate": 62.5,
                "avg_profit": 0.23,
                "max_drawdown": 0.8,
                "sharpe_ratio": 1.5
            }
        },
        {
            "id": 3,
            "name": "Momentum",
            "description": "Trendkövető stratégia, amely a piaci momentum alapján kereskedik.",
            "status": "paused",
            "symbols": ["BNB/USDT", "SOL/USDT"],
            "parameters": {
                "lookback_period": 14,
                "threshold": 0.1,
                "position_size": 10.0,
                "take_profit": 5.0,
                "stop_loss": 2.0
            },
            "performance": {
                "profit": -0.5,
                "trades": 3,
                "win_rate": 33.3,
                "avg_profit": -0.17,
                "max_drawdown": 1.5,
                "sharpe_ratio": -0.3
            }
        }
    ]
    
    # Keresse meg a stratégiát az ID alapján
    strategy = next((s for s in strategies if s["id"] == strategy_id), None)
    
    if not strategy:
        return jsonify({"error": "Strategy not found"}), 404
    
    return jsonify(strategy)

# API - Stratégia indítása/leállítása
@api_bp.route('/strategy/<int:strategy_id>/toggle', methods=['POST'])
@login_required
def toggle_strategy(strategy_id):
    # Stratégia adatok (szimulált adatok)
    strategies = [
        {
            "id": 1,
            "name": "Grid Trading",
            "status": "active"
        },
        {
            "id": 2,
            "name": "DCA (Dollar Cost Averaging)",
            "status": "active"
        },
        {
            "id": 3,
            "name": "Momentum",
            "status": "paused"
        }
    ]
    
    # Keresse meg a stratégiát az ID alapján
    strategy = next((s for s in strategies if s["id"] == strategy_id), None)
    
    if not strategy:
        return jsonify({"error": "Strategy not found"}), 404
    
    # Akció lekérdezése
    data = request.get_json()
    action = data.get('action')
    
    if action not in ['start', 'pause', 'stop']:
        return jsonify({"error": "Invalid action"}), 400
    
    # Stratégia állapot módosítása (szimulált)
    new_status = {
        'start': 'active',
        'pause': 'paused',
        'stop': 'inactive'
    }[action]
    
    # Értesítés létrehozása
    notification = Notification(
        type='info',
        message=f"A(z) {strategy['name']} stratégia állapota megváltozott: {new_status}"
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        "id": strategy_id,
        "name": strategy["name"],
        "status": new_status,
        "message": f"Strategy {strategy['name']} {action}ed successfully"
    })

# API - Piaci adatok
@api_bp.route('/market/data', methods=['GET'])
@login_required
def market_data():
    # Paraméterek
    symbol = request.args.get('symbol', default='BTC/USDT', type=str)
    
    # Piaci adatok (szimulált adatok)
    market_data = {
        "BTC/USDT": {
            "symbol": "BTC/USDT",
            "price": 45000.0,
            "change": 1.2,
            "high": 45500.0,
            "low": 44200.0,
            "volume": 1250.5,
            "bid": 44990.0,
            "ask": 45010.0
        },
        "ETH/USDT": {
            "symbol": "ETH/USDT",
            "price": 3200.0,
            "change": -0.5,
            "high": 3250.0,
            "low": 3180.0,
            "volume": 8500.2,
            "bid": 3199.0,
            "ask": 3201.0
        },
        "BNB/USDT": {
            "symbol": "BNB/USDT",
            "price": 420.0,
            "change": 0.8,
            "high": 425.0,
            "low": 415.0,
            "volume": 12500.0,
            "bid": 419.5,
            "ask": 420.5
        }
    }
    
    if symbol in market_data:
        return jsonify(market_data[symbol])
    else:
        return jsonify({"error": "Symbol not found"}), 404

# API - Piaci adatok lista
@api_bp.route('/market/list', methods=['GET'])
@login_required
def market_list():
    # Piaci adatok (szimulált adatok)
    market_data = [
        {
            "symbol": "BTC/USDT",
            "price": 45000.0,
            "change": 1.2,
            "volume": 1250.5
        },
        {
            "symbol": "ETH/USDT",
            "price": 3200.0,
            "change": -0.5,
            "volume": 8500.2
        },
        {
            "symbol": "BNB/USDT",
            "price": 420.0,
            "change": 0.8,
            "volume": 12500.0
        },
        {
            "symbol": "SOL/USDT",
            "price": 120.0,
            "change": 2.5,
            "volume": 18000.0
        },
        {
            "symbol": "ADA/USDT",
            "price": 0.55,
            "change": -1.2,
            "volume": 25000.0
        },
        {
            "symbol": "XRP/USDT",
            "price": 0.48,
            "change": 0.3,
            "volume": 30000.0
        }
    ]
    
    return jsonify(market_data)

# API - Teljesítmény metrikák
@api_bp.route('/performance/metrics', methods=['GET'])
@login_required
def performance_metrics():
    # Paraméterek
    strategy = request.args.get('strategy', default=None, type=str)
    
    # Lekérdezés építése
    query = PerformanceMetrics.query
    
    if strategy:
        query = query.filter(PerformanceMetrics.strategy == strategy)
    
    # Teljesítmény metrikák lekérdezése
    metrics = query.order_by(PerformanceMetrics.timestamp.desc()).first()
    
    if not metrics:
        # Szimulált adatok, ha nincs valós adat
        return jsonify({
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy or "all",
            "sharpe_ratio": 1.8,
            "sortino_ratio": 2.1,
            "max_drawdown": 5.2,
            "win_rate": 68.5,
            "profit_factor": 1.5,
            "total_trades": 25,
            "profitable_trades": 17,
            "losing_trades": 8
        })
    
    # Válasz összeállítása
    response = {
        "timestamp": metrics.timestamp.isoformat(),
        "strategy": metrics.strategy,
        "sharpe_ratio": metrics.sharpe_ratio,
        "sortino_ratio": metrics.sortino_ratio,
        "max_drawdown": metrics.max_drawdown,
        "win_rate": metrics.win_rate,
        "profit_factor": metrics.profit_factor,
        "total_trades": metrics.total_trades,
        "profitable_trades": metrics.profitable_trades,
        "losing_trades": metrics.losing_trades
    }
    
    return jsonify(response)

# API - Értesítések
@api_bp.route('/notifications', methods=['GET'])
@login_required
def notifications():
    # Paraméterek
    limit = request.args.get('limit', default=10, type=int)
    unread_only = request.args.get('unread_only', default=False, type=bool)
    
    # Lekérdezés építése
    query = Notification.query
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    # Értesítések lekérdezése
    notifications = query.order_by(Notification.timestamp.desc()).limit(limit).all()
    
    # Válasz összeállítása
    response = []
    
    for notification in notifications:
        response.append({
            "id": notification.id,
            "timestamp": notification.timestamp.isoformat(),
            "type": notification.type,
            "message": notification.message,
            "is_read": notification.is_read
        })
    
    return jsonify(response)

# API - Értesítés olvasottnak jelölése
@api_bp.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    
    return jsonify({"success": True})

# API - Összes értesítés olvasottnak jelölése
@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.update({Notification.is_read: True})
    db.session.commit()
    
    return jsonify({"success": True})

# API - Beállítások lekérdezése
@api_bp.route('/settings', methods=['GET'])
@login_required
def get_settings():
    # Beállítások lekérdezése
    settings = Settings.query.all()
    
    # Válasz összeállítása
    response = {}
    
    for setting in settings:
        try:
            # Próbálja JSON-ként értelmezni
            response[setting.key] = json.loads(setting.value)
        except:
            # Ha nem sikerül, akkor szövegként kezeli
            response[setting.key] = setting.value
    
    # Ha nincsenek beállítások, akkor alapértelmezett értékek
    if not response:
        response = {
            "trading_enabled": True,
            "max_open_trades": 5,
            "default_risk_per_trade": 1.0,
            "telegram_notifications": True,
            "email_notifications": False,
            "primary_exchange": "Binance",
            "test_mode": True
        }
    
    return jsonify(response)

# API - Beállítások módosítása
@api_bp.route('/settings', methods=['POST'])
@login_required
def update_settings():
    # Csak admin felhasználók módosíthatják a beállításokat
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Beállítások lekérdezése
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Beállítások módosítása
    for key, value in data.items():
        # Érték konvertálása JSON-né
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        else:
            value_str = str(value)
        
        # Beállítás keresése
        setting = Settings.query.filter_by(key=key).first()
        
        if setting:
            # Meglévő beállítás módosítása
            setting.value = value_str
        else:
            # Új beállítás létrehozása
            setting = Settings(key=key, value=value_str)
            db.session.add(setting)
    
    db.session.commit()
    
    # Értesítés létrehozása
    notification = Notification(
        type='info',
        message="A rendszer beállításai frissítve lettek"
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({"success": True})

# API - Backtesting
@api_bp.route('/backtesting/run', methods=['POST'])
@login_required
def run_backtest():
    # Backtesting paraméterek
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Kötelező paraméterek ellenőrzése
    required_params = ['strategy_id', 'symbol', 'timeframe', 'start_date', 'end_date', 'initial_capital']
    
    for param in required_params:
        if param not in data:
            return jsonify({"error": f"Missing required parameter: {param}"}), 400
    
    # Szimulált backtesting eredmény
    result = {
        "id": int(time.time()),
        "strategy": "Grid Trading" if data['strategy_id'] == 1 else "Momentum" if data['strategy_id'] == 3 else "Unknown",
        "symbol": data['symbol'],
        "timeframe": data['timeframe'],
        "start_date": data['start_date'],
        "end_date": data['end_date'],
        "initial_capital": data['initial_capital'],
        "final_capital": data['initial_capital'] * 1.025,  # Szimulált 2.5% nyereség
        "profit": 2.5,
        "max_drawdown": 1.2,
        "sharpe_ratio": 1.8,
        "trades": 12,
        "win_rate": 75.0,
        "execution_time": 5.2  # Szimulált végrehajtási idő másodpercben
    }
    
    # Értesítés létrehozása
    notification = Notification(
        type='success',
        message=f"Backtesting sikeresen lefutott: {result['strategy']} a(z) {result['symbol']} szimbólumon"
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify(result)

# API - Backtesting eredmények
@api_bp.route('/backtesting/results', methods=['GET'])
@login_required
def backtest_results():
    # Szimulált backtesting eredmények
    results = [
        {
            "id": 1,
            "strategy": "Grid Trading",
            "symbol": "BTC/USDT",
            "timeframe": "1h",
            "start_date": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "end_date": datetime.now().strftime('%Y-%m-%d'),
            "initial_capital": 10000,
            "final_capital": 10250,
            "profit": 2.5,
            "max_drawdown": 1.2,
            "sharpe_ratio": 1.8,
            "trades": 12,
            "win_rate": 75.0
        },
        {
            "id": 2,
            "strategy": "Momentum",
            "symbol": "ETH/USDT",
            "timeframe": "4h",
            "start_date": (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
            "end_date": datetime.now().strftime('%Y-%m-%d'),
            "initial_capital": 5000,
            "final_capital": 5150,
            "profit": 3.0,
            "max_drawdown": 1.5,
            "sharpe_ratio": 1.6,
            "trades": 8,
            "win_rate": 62.5
        }
    ]
    
    return jsonify(results)

# API - Felhasználók (csak admin)
@api_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    # Csak admin felhasználók férhetnek hozzá
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Felhasználók lekérdezése
    users = User.query.all()
    
    # Válasz összeállítása
    response = []
    
    for user in users:
        response.append({
            "id": user.id,
            "username": user.username,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        })
    
    return jsonify(response)

# API - Felhasználó létrehozása (csak admin)
@api_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    # Csak admin felhasználók férhetnek hozzá
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Felhasználó adatok
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Kötelező paraméterek ellenőrzése
    required_params = ['username', 'password']
    
    for param in required_params:
        if param not in data:
            return jsonify({"error": f"Missing required parameter: {param}"}), 400
    
    # Ellenőrzi, hogy a felhasználónév már létezik-e
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists"}), 400
    
    # Új felhasználó létrehozása
    user = User(
        username=data['username'],
        password=data['password'],  # Valós rendszerben használj jelszó hashelést!
        is_admin=data.get('is_admin', False)
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Értesítés létrehozása
    notification = Notification(
        type='info',
        message=f"Új felhasználó létrehozva: {user.username}"
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat()
    })

# API - Felhasználó törlése (csak admin)
@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    # Csak admin felhasználók férhetnek hozzá
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    # Nem törölheti saját magát
    if user_id == current_user.id:
        return jsonify({"error": "Cannot delete yourself"}), 400
    
    # Felhasználó keresése
    user = User.query.get_or_404(user_id)
    
    # Felhasználó törlése
    db.session.delete(user)
    db.session.commit()
    
    # Értesítés létrehozása
    notification = Notification(
        type='info',
        message=f"Felhasználó törölve: {user.username}"
    )
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({"success": True})
