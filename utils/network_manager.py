"""
Hálózati kezelő - RPI4 optimalizált
"""
import logging
import time
import socket
import threading
import random
from functools import wraps

logger = logging.getLogger(__name__)

class NetworkManager:
    """Hálózati kapcsolatok kezelése és optimalizálása RPI4 környezetben"""
    
    def __init__(self, max_retries=5, retry_delay=5, timeout=30):
        """
        Inicializálja a hálózati kezelőt
        
        Args:
            max_retries: Maximális újrapróbálkozások száma
            retry_delay: Újrapróbálkozások közötti késleltetés másodpercben
            timeout: Kapcsolat timeout másodpercben
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.rate_limits = {}
        
    def check_connection(self, host="8.8.8.8", port=53, timeout=3):
        """
        Ellenőrzi az internet kapcsolatot
        
        Args:
            host: Ellenőrizendő host
            port: Ellenőrizendő port
            timeout: Kapcsolat timeout másodpercben
            
        Returns:
            bool: True, ha van internet kapcsolat, egyébként False
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception as e:
            logger.warning(f"Nincs internet kapcsolat: {e}")
            return False
    
    def request_with_retry(self, method, url, **kwargs):
        """
        HTTP kérés küldése újrapróbálkozással
        
        Args:
            method: HTTP metódus ('get', 'post', stb.)
            url: Cél URL
            **kwargs: Requests könyvtár paraméterei
            
        Returns:
            Response: HTTP válasz
        """
        try:
            import requests
            
            # Timeout beállítása, ha nincs megadva
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout
            
            # Session létrehozása
            session = requests.Session()
            
            # Rate limit ellenőrzése
            domain = url.split('/')[2]
            if domain in self.rate_limits:
                rate_limit = self.rate_limits[domain]
                current_time = time.time()
                
                # Várakozás, ha túl gyakran küldünk kérést
                if current_time - rate_limit['last_request'] < rate_limit['min_interval']:
                    wait_time = rate_limit['min_interval'] - (current_time - rate_limit['last_request'])
                    logger.debug(f"Rate limit várakozás: {domain}, {wait_time:.2f} másodperc")
                    time.sleep(wait_time)
                
                # Utolsó kérés idejének frissítése
                self.rate_limits[domain]['last_request'] = time.time()
            
            # Kérés küldése újrapróbálkozással
            retries = 0
            last_exception = None
            
            while retries <= self.max_retries:
                try:
                    response = session.request(method, url, **kwargs)
                    
                    # HTTP hiba ellenőrzése
                    if response.status_code >= 400:
                        logger.warning(f"HTTP hiba: {response.status_code}, {url}")
                        
                        # 429 Too Many Requests esetén rate limit beállítása
                        if response.status_code == 429:
                            retry_after = int(response.headers.get('Retry-After', self.retry_delay * 2))
                            logger.warning(f"Rate limit elérve: {domain}, várakozás {retry_after} másodperc")
                            
                            # Rate limit beállítása
                            self.rate_limits[domain] = {
                                'min_interval': max(1, retry_after / 10),  # Konzervatív beállítás
                                'last_request': time.time()
                            }
                            
                            time.sleep(retry_after)
                            retries += 1
                            continue
                        
                        # 5xx szerver hiba esetén újrapróbálkozás
                        if response.status_code >= 500:
                            retries += 1
                            if retries <= self.max_retries:
                                wait_time = self.retry_delay * retries
                                logger.warning(f"Szerver hiba, újrapróbálkozás {retries}/{self.max_retries} {wait_time} másodperc múlva")
                                time.sleep(wait_time)
                                continue
                    
                    return response
                    
                except (requests.exceptions.RequestException, socket.timeout) as e:
                    last_exception = e
                    retries += 1
                    
                    if retries <= self.max_retries:
                        wait_time = self.retry_delay * retries
                        logger.warning(f"Hálózati hiba: {e}, újrapróbálkozás {retries}/{self.max_retries} {wait_time} másodperc múlva")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Hálózati hiba, nem sikerült kapcsolódni: {url}, {e}")
                        raise
            
            # Ha minden újrapróbálkozás sikertelen
            if last_exception:
                raise last_exception
            
            return None
        except ImportError:
            logger.error("A requests könyvtár nem érhető el")
            return None
    
    def get(self, url, **kwargs):
        """
        GET kérés küldése
        
        Args:
            url: Cél URL
            **kwargs: Requests könyvtár paraméterei
            
        Returns:
            Response: HTTP válasz
        """
        return self.request_with_retry('get', url, **kwargs)
    
    def post(self, url, **kwargs):
        """
        POST kérés küldése
        
        Args:
            url: Cél URL
            **kwargs: Requests könyvtár paraméterei
            
        Returns:
            Response: HTTP válasz
        """
        return self.request_with_retry('post', url, **kwargs)
    
    def set_rate_limit(self, domain, min_interval):
        """
        Rate limit beállítása egy domainhez
        
        Args:
            domain: Domain név
            min_interval: Minimális időköz két kérés között másodpercben
        """
        self.rate_limits[domain] = {
            'min_interval': min_interval,
            'last_request': 0
        }
        logger.debug(f"Rate limit beállítva: {domain}, {min_interval} másodperc")
    
    def network_resilient(max_retries=None, retry_delay=None):
        """
        Dekorátor hálózati műveletekhez
        
        Args:
            max_retries: Maximális újrapróbálkozások száma
            retry_delay: Újrapróbálkozások közötti késleltetés másodpercben
            
        Returns:
            Dekorált függvény
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                network_manager = NetworkManager()
                
                # Paraméterek felülírása, ha meg vannak adva
                if max_retries is not None:
                    network_manager.max_retries = max_retries
                if retry_delay is not None:
                    network_manager.retry_delay = retry_delay
                
                # Újrapróbálkozás logika
                retries = 0
                last_exception = None
                
                while retries <= network_manager.max_retries:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        retries += 1
                        
                        if retries <= network_manager.max_retries:
                            # Exponenciális backoff jitter-rel
                            base_delay = network_manager.retry_delay * (2 ** (retries - 1))
                            jitter = random.uniform(0, 0.1 * base_delay)
                            wait_time = base_delay + jitter
                            
                            logger.warning(f"Hiba a hálózati művelet során: {e}, "
                                          f"újrapróbálkozás {retries}/{network_manager.max_retries} "
                                          f"{wait_time:.2f} másodperc múlva")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Hálózati művelet sikertelen: {e}")
                            raise
                
                # Ha minden újrapróbálkozás sikertelen
                if last_exception:
                    raise last_exception
                
                return None
            return wrapper
        return decorator

# Globális hálózati kezelő példány
network_manager = NetworkManager()

# Exchange-specifikus rate limitek beállítása
network_manager.set_rate_limit('api.binance.com', 0.5)  # 2 kérés/másodperc
network_manager.set_rate_limit('api.kraken.com', 1.0)   # 1 kérés/másodperc
network_manager.set_rate_limit('api.coinbase.com', 0.25)  # 4 kérés/másodperc
