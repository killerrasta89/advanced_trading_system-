"""
Web Interface API - Market Data API
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import json
import time
from datetime import datetime, timedelta

# Core komponensek importálása
from core.market_data_manager import MarketDataManager

market_data_api = Blueprint('market_data_api', __name__)

@market_data_api.route('/api/market/symbols', methods=['GET'])
@login_required
def get_symbols():
    """
    Elérhető szimbólumok lekérdezése
    """
    try:
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Szimbólumok lekérdezése
        exchange = request.args.get('exchange', 'binance')
        symbols = market_data_manager.get_symbols(exchange)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': symbols,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/ticker', methods=['GET'])
@login_required
def get_ticker():
    """
    Ticker adatok lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        exchange = request.args.get('exchange', 'binance')
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Ticker lekérdezése
        ticker = market_data_manager.get_ticker(symbol, exchange)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': ticker,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/ohlcv', methods=['GET'])
@login_required
def get_ohlcv():
    """
    OHLCV adatok lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        exchange = request.args.get('exchange', 'binance')
        timeframe = request.args.get('timeframe', '1h')
        limit = int(request.args.get('limit', 100))
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # OHLCV adatok lekérdezése
        ohlcv = market_data_manager.get_ohlcv(symbol, timeframe, limit, exchange)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': ohlcv,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/orderbook', methods=['GET'])
@login_required
def get_orderbook():
    """
    Orderbook lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        exchange = request.args.get('exchange', 'binance')
        limit = int(request.args.get('limit', 20))
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Orderbook lekérdezése
        orderbook = market_data_manager.get_orderbook(symbol, limit, exchange)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': orderbook,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/trades', methods=['GET'])
@login_required
def get_trades():
    """
    Piaci kereskedések lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        exchange = request.args.get('exchange', 'binance')
        limit = int(request.args.get('limit', 50))
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Kereskedések lekérdezése
        trades = market_data_manager.get_trades(symbol, limit, exchange)
        
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

@market_data_api.route('/api/market/indicators', methods=['GET'])
@login_required
def get_indicators():
    """
    Technikai indikátorok lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        exchange = request.args.get('exchange', 'binance')
        timeframe = request.args.get('timeframe', '1h')
        indicators = request.args.get('indicators', 'rsi,macd,bollinger_bands')
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Indikátorok lekérdezése
        indicator_data = market_data_manager.get_indicators(
            symbol, 
            timeframe, 
            indicators.split(','), 
            exchange
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': indicator_data,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/price-prediction', methods=['GET'])
@login_required
def get_price_prediction():
    """
    Árfolyam előrejelzés lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        exchange = request.args.get('exchange', 'binance')
        timeframe = request.args.get('timeframe', '1h')
        periods = int(request.args.get('periods', 24))
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Árfolyam előrejelzés lekérdezése
        prediction = market_data_manager.get_price_prediction(
            symbol, 
            timeframe, 
            periods, 
            exchange
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': prediction,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/sentiment', methods=['GET'])
@login_required
def get_market_sentiment():
    """
    Piaci hangulat lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Piaci hangulat lekérdezése
        sentiment = market_data_manager.get_market_sentiment(symbol)
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': sentiment,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/arbitrage-opportunities', methods=['GET'])
@login_required
def get_arbitrage_opportunities():
    """
    Arbitrázs lehetőségek lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        min_spread = float(request.args.get('min_spread', 0.5))
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Arbitrázs lehetőségek lekérdezése
        opportunities = market_data_manager.get_arbitrage_opportunities(
            symbol, 
            min_spread
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': opportunities,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/heatmap', methods=['GET'])
@login_required
def get_market_heatmap():
    """
    Piaci heatmap lekérdezése
    """
    try:
        # Paraméterek
        market = request.args.get('market', 'crypto')
        timeframe = request.args.get('timeframe', '1d')
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Heatmap lekérdezése
        heatmap = market_data_manager.get_market_heatmap(
            market, 
            timeframe
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': heatmap,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/correlation', methods=['GET'])
@login_required
def get_correlation():
    """
    Korreláció lekérdezése
    """
    try:
        # Paraméterek
        symbols = request.args.get('symbols', 'BTC/USDT,ETH/USDT,XRP/USDT')
        timeframe = request.args.get('timeframe', '1d')
        period = int(request.args.get('period', 30))
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Korreláció lekérdezése
        correlation = market_data_manager.get_correlation(
            symbols.split(','), 
            timeframe, 
            period
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': correlation,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500

@market_data_api.route('/api/market/volatility', methods=['GET'])
@login_required
def get_volatility():
    """
    Volatilitás lekérdezése
    """
    try:
        # Paraméterek
        symbol = request.args.get('symbol', 'BTC/USDT')
        exchange = request.args.get('exchange', 'binance')
        timeframe = request.args.get('timeframe', '1d')
        period = int(request.args.get('period', 30))
        
        # Market data manager példányosítása
        market_data_manager = MarketDataManager()
        
        # Volatilitás lekérdezése
        volatility = market_data_manager.get_volatility(
            symbol, 
            timeframe, 
            period, 
            exchange
        )
        
        # Válasz összeállítása
        response = {
            'success': True,
            'data': volatility,
            'timestamp': int(time.time())
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': int(time.time())
        }), 500
