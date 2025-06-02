"""
Exchange Config - Exchange specifikus beállítások
"""
import json
import os

class ExchangeConfig:
    """
    Exchange beállítások kezelése
    """
    
    # Támogatott tőzsdék
    SUPPORTED_EXCHANGES = ['binance', 'kraken', 'coinbase']
    
    # Alapértelmezett beállítások
    DEFAULT_SETTINGS = {
        'binance': {
            'base_url': 'https://api.binance.com',
            'websocket_url': 'wss://stream.binance.com:9443/ws',
            'rate_limit': {
                'requests_per_minute': 1200,
                'orders_per_second': 10,
                'orders_per_day': 100000
            },
            'fees': {
                'maker': 0.1,  # %
                'taker': 0.1,  # %
                'withdraw': {
                    'BTC': 0.0005,
                    'ETH': 0.005,
                    'USDT': 1.0
                }
            },
            'min_order_size': {
                'BTC': 0.0001,
                'ETH': 0.001,
                'USDT': 10.0
            },
            'precision': {
                'price': {
                    'BTC': 2,
                    'ETH': 2,
                    'USDT': 2
                },
                'amount': {
                    'BTC': 6,
                    'ETH': 5,
                    'USDT': 2
                }
            },
            'timeframes': ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'],
            'default_timeframe': '1h',
            'has_websocket': True,
            'has_futures': True,
            'has_margin': True,
            'has_swap': True
        },
        'kraken': {
            'base_url': 'https://api.kraken.com',
            'websocket_url': 'wss://ws.kraken.com',
            'rate_limit': {
                'requests_per_minute': 1000,
                'orders_per_second': 5,
                'orders_per_day': 50000
            },
            'fees': {
                'maker': 0.16,  # %
                'taker': 0.26,  # %
                'withdraw': {
                    'BTC': 0.0005,
                    'ETH': 0.005,
                    'USDT': 2.5
                }
            },
            'min_order_size': {
                'BTC': 0.0001,
                'ETH': 0.001,
                'USDT': 10.0
            },
            'precision': {
                'price': {
                    'BTC': 1,
                    'ETH': 1,
                    'USDT': 2
                },
                'amount': {
                    'BTC': 8,
                    'ETH': 8,
                    'USDT': 2
                }
            },
            'timeframes': ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '2w', '1M'],
            'default_timeframe': '1h',
            'has_websocket': True,
            'has_futures': False,
            'has_margin': True,
            'has_swap': False
        },
        'coinbase': {
            'base_url': 'https://api.exchange.coinbase.com',
            'websocket_url': 'wss://ws-feed.exchange.coinbase.com',
            'rate_limit': {
                'requests_per_minute': 900,
                'orders_per_second': 3,
                'orders_per_day': 30000
            },
            'fees': {
                'maker': 0.5,  # %
                'taker': 0.5,  # %
                'withdraw': {
                    'BTC': 0.0001,
                    'ETH': 0.001,
                    'USDT': 1.0
                }
            },
            'min_order_size': {
                'BTC': 0.001,
                'ETH': 0.01,
                'USDT': 10.0
            },
            'precision': {
                'price': {
                    'BTC': 2,
                    'ETH': 2,
                    'USDT': 2
                },
                'amount': {
                    'BTC': 8,
                    'ETH': 8,
                    'USDT': 2
                }
            },
            'timeframes': ['1m', '5m', '15m', '1h', '6h', '1d'],
            'default_timeframe': '1h',
            'has_websocket': True,
            'has_futures': False,
            'has_margin': False,
            'has_swap': False
        }
    }
    
    @classmethod
    def get_exchange_settings(cls, exchange):
        """
        Exchange beállítások lekérdezése
        
        Args:
            exchange (str): Exchange neve
            
        Returns:
            dict: Exchange beállítások
        """
        if exchange not in cls.SUPPORTED_EXCHANGES:
            raise ValueError(f"Nem támogatott exchange: {exchange}")
        
        # Beállítások fájl elérési útja
        settings_file = os.path.join('config', 'exchange_settings.json')
        
        # Ha a fájl létezik, betöltjük
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                if exchange in settings:
                    # Alapértelmezett beállítások kiegészítése a betöltött beállításokkal
                    merged_settings = cls.DEFAULT_SETTINGS[exchange].copy()
                    merged_settings.update(settings[exchange])
                    
                    return merged_settings
                else:
                    return cls.DEFAULT_SETTINGS[exchange]
            except Exception as e:
                print(f"Hiba a beállítások betöltése során: {e}")
                return cls.DEFAULT_SETTINGS[exchange]
        else:
            return cls.DEFAULT_SETTINGS[exchange]
    
    @classmethod
    def update_exchange_settings(cls, exchange, settings):
        """
        Exchange beállítások frissítése
        
        Args:
            exchange (str): Exchange neve
            settings (dict): Frissítendő beállítások
            
        Returns:
            dict: Frissített exchange beállítások
        """
        if exchange not in cls.SUPPORTED_EXCHANGES:
            raise ValueError(f"Nem támogatott exchange: {exchange}")
        
        # Beállítások fájl elérési útja
        settings_file = os.path.join('config', 'exchange_settings.json')
        
        # Aktuális beállítások lekérdezése
        current_settings = {}
        
        # Ha a fájl létezik, betöltjük
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    current_settings = json.load(f)
            except Exception as e:
                print(f"Hiba a beállítások betöltése során: {e}")
        
        # Exchange beállítások frissítése
        if exchange not in current_settings:
            current_settings[exchange] = cls.DEFAULT_SETTINGS[exchange].copy()
        
        current_settings[exchange].update(settings)
        
        # Beállítások mentése
        try:
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(current_settings, f, indent=4)
        except Exception as e:
            print(f"Hiba a beállítások mentése során: {e}")
        
        return current_settings[exchange]
    
    @classmethod
    def get_supported_timeframes(cls, exchange):
        """
        Támogatott időkeretek lekérdezése
        
        Args:
            exchange (str): Exchange neve
            
        Returns:
            list: Támogatott időkeretek
        """
        settings = cls.get_exchange_settings(exchange)
        return settings.get('timeframes', [])
    
    @classmethod
    def get_default_timeframe(cls, exchange):
        """
        Alapértelmezett időkeret lekérdezése
        
        Args:
            exchange (str): Exchange neve
            
        Returns:
            str: Alapértelmezett időkeret
        """
        settings = cls.get_exchange_settings(exchange)
        return settings.get('default_timeframe', '1h')
    
    @classmethod
    def get_fee(cls, exchange, fee_type='taker'):
        """
        Díj lekérdezése
        
        Args:
            exchange (str): Exchange neve
            fee_type (str): Díj típusa (maker, taker)
            
        Returns:
            float: Díj százalékban
        """
        settings = cls.get_exchange_settings(exchange)
        return settings.get('fees', {}).get(fee_type, 0.1)
    
    @classmethod
    def get_min_order_size(cls, exchange, symbol):
        """
        Minimális megbízás méret lekérdezése
        
        Args:
            exchange (str): Exchange neve
            symbol (str): Szimbólum
            
        Returns:
            float: Minimális megbízás méret
        """
        settings = cls.get_exchange_settings(exchange)
        return settings.get('min_order_size', {}).get(symbol, 0.0001)
    
    @classmethod
    def get_precision(cls, exchange, symbol, precision_type='price'):
        """
        Pontosság lekérdezése
        
        Args:
            exchange (str): Exchange neve
            symbol (str): Szimbólum
            precision_type (str): Pontosság típusa (price, amount)
            
        Returns:
            int: Pontosság
        """
        settings = cls.get_exchange_settings(exchange)
        return settings.get('precision', {}).get(precision_type, {}).get(symbol, 2)
