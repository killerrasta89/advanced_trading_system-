"""
API Blueprint - API útvonalak kezelése
"""
from flask import Blueprint, jsonify, request
import time

# API Blueprint létrehozása
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/', methods=['GET'])
def api_index():
    """
    API főoldal
    """
    return jsonify({
        'success': True,
        'message': 'Advanced Trading System API',
        'version': '1.0.0',
        'timestamp': int(time.time())
    })

@api_bp.route('/status', methods=['GET'])
def api_status():
    """
    API státusz
    """
    return jsonify({
        'success': True,
        'status': 'online',
        'timestamp': int(time.time())
    })

@api_bp.route('/endpoints', methods=['GET'])
def api_endpoints():
    """
    API végpontok listája
    """
    endpoints = [
        {
            'path': '/api/',
            'methods': ['GET'],
            'description': 'API főoldal'
        },
        {
            'path': '/api/status',
            'methods': ['GET'],
            'description': 'API státusz'
        },
        {
            'path': '/api/endpoints',
            'methods': ['GET'],
            'description': 'API végpontok listája'
        },
        {
            'path': '/api/portfolio/*',
            'methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'description': 'Portfólió kezelés'
        },
        {
            'path': '/api/trades/*',
            'methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'description': 'Kereskedések kezelése'
        },
        {
            'path': '/api/strategies/*',
            'methods': ['GET', 'POST', 'PUT', 'DELETE'],
            'description': 'Stratégiák kezelése'
        },
        {
            'path': '/api/market/*',
            'methods': ['GET'],
            'description': 'Piaci adatok lekérdezése'
        },
        {
            'path': '/api/settings/*',
            'methods': ['GET', 'PUT'],
            'description': 'Beállítások kezelése'
        }
    ]
    
    return jsonify({
        'success': True,
        'data': endpoints,
        'timestamp': int(time.time())
    })

# További API végpontok importálása
# Ezek a Blueprint-ek a web_interface/app.py fájlban vannak regisztrálva
