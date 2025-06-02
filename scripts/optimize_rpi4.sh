#!/bin/bash

# RPI4 Optimalizációs és Tesztelési Script
# Advanced Trading System

echo "===== Advanced Trading System - RPI4 Optimalizáció és Tesztelés ====="
echo "Kezdés: $(date)"
echo

# Rendszer információk lekérdezése
echo "===== Rendszer információk ====="
echo "Kernel verzió: $(uname -r)"
echo "CPU információ:"
lscpu | grep "Model name"
echo "Memória információ:"
free -h
echo "Tárhely információ:"
df -h | grep -E "Filesystem|/$"
echo

# Python környezet ellenőrzése
echo "===== Python környezet ====="
echo "Python verzió:"
python3 --version
echo "Telepített csomagok:"
pip3 list
echo

# Memória használat optimalizálása
echo "===== Memória használat optimalizálása ====="
echo "SQLite optimalizálás..."
cat > advanced_trading_system/config/db_config.py << EOF
"""
Adatbázis konfigurációs beállítások - RPI4 optimalizált
"""

# SQLite beállítások
SQLITE_CONFIG = {
    'PRAGMA': [
        'journal_mode = WAL',       # Write-Ahead Logging mód a jobb teljesítményért
        'synchronous = NORMAL',     # Csökkentett szinkronizáció a jobb teljesítményért
        'cache_size = 5000',        # Cache méret növelése (kb. 5MB)
        'temp_store = MEMORY',      # Ideiglenes táblák memóriában tárolása
        'mmap_size = 30000000',     # Memory-mapped I/O engedélyezése (kb. 30MB)
    ],
    'POOL_SIZE': 1,                 # Connection pool mérete
    'TIMEOUT': 30,                  # Kapcsolat timeout másodpercben
}

# Adatbázis fájl elérési útja
DATABASE_PATH = 'sqlite:///data/trading_system.db'

# Adatbázis biztonsági mentés beállítások
BACKUP = {
    'ENABLED': True,
    'INTERVAL_HOURS': 24,           # Biztonsági mentés gyakorisága órákban
    'MAX_BACKUPS': 7,               # Megtartott biztonsági mentések maximális száma
    'COMPRESSION': True,            # Biztonsági mentések tömörítése
}
EOF
echo "SQLite optimalizálás kész."

echo "Memória kezelés optimalizálása..."
cat > advanced_trading_system/utils/memory_manager.py << EOF
"""
Memória kezelő - RPI4 optimalizált
"""
import gc
import os
import psutil
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

class MemoryManager:
    """Memória használat kezelése és optimalizálása RPI4 környezetben"""
    
    def __init__(self, threshold_percent=80, check_interval=60):
        """
        Inicializálja a memória kezelőt
        
        Args:
            threshold_percent: Riasztási küszöb százalékban
            check_interval: Ellenőrzési időköz másodpercben
        """
        self.threshold_percent = threshold_percent
        self.check_interval = check_interval
        self.last_check = 0
        self.process = psutil.Process(os.getpid())
        
    def get_memory_usage(self):
        """Visszaadja a jelenlegi memória használatot"""
        # Folyamat memória használata
        process_memory = self.process.memory_info().rss / 1024 / 1024  # MB-ban
        
        # Rendszer memória használata
        system_memory = psutil.virtual_memory()
        
        return {
            'process_mb': process_memory,
            'system_percent': system_memory.percent,
            'system_available_mb': system_memory.available / 1024 / 1024,
            'system_total_mb': system_memory.total / 1024 / 1024
        }
    
    def check_memory(self, force_gc=False):
        """
        Ellenőrzi a memória használatot és szükség esetén intézkedik
        
        Args:
            force_gc: Kényszerített garbage collection
            
        Returns:
            dict: Memória használati adatok
        """
        current_time = time.time()
        
        # Csak a megadott időközönként ellenőriz, kivéve ha force_gc=True
        if not force_gc and current_time - self.last_check < self.check_interval:
            return None
            
        self.last_check = current_time
        memory_usage = self.get_memory_usage()
        
        # Memória használat naplózása
        logger.debug(f"Memória használat: Folyamat={memory_usage['process_mb']:.2f}MB, "
                    f"Rendszer={memory_usage['system_percent']}%, "
                    f"Elérhető={memory_usage['system_available_mb']:.2f}MB")
        
        # Garbage collection, ha a memória használat meghaladja a küszöböt vagy force_gc=True
        if force_gc or memory_usage['system_percent'] > self.threshold_percent:
            logger.info(f"Garbage collection indítása (Memória használat: {memory_usage['system_percent']}%)")
            collected = gc.collect()
            logger.info(f"Garbage collection befejezve: {collected} objektum felszabadítva")
            
            # Frissített memória használat
            memory_usage = self.get_memory_usage()
            logger.info(f"Memória használat GC után: Folyamat={memory_usage['process_mb']:.2f}MB, "
                       f"Rendszer={memory_usage['system_percent']}%")
        
        return memory_usage
    
    def optimize_dataframe(self, df):
        """
        Pandas DataFrame memória használatának optimalizálása
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            DataFrame: Optimalizált DataFrame
        """
        # Numerikus oszlopok típusának optimalizálása
        for col in df.select_dtypes(include=['int']).columns:
            # Értéktartomány meghatározása
            col_min, col_max = df[col].min(), df[col].max()
            
            # Megfelelő integer típus kiválasztása
            if col_min >= 0:
                if col_max < 256:
                    df[col] = df[col].astype('uint8')
                elif col_max < 65536:
                    df[col] = df[col].astype('uint16')
                elif col_max < 4294967296:
                    df[col] = df[col].astype('uint32')
            else:
                if col_min > -128 and col_max < 128:
                    df[col] = df[col].astype('int8')
                elif col_min > -32768 and col_max < 32768:
                    df[col] = df[col].astype('int16')
                elif col_min > -2147483648 and col_max < 2147483648:
                    df[col] = df[col].astype('int32')
        
        # Float oszlopok típusának optimalizálása
        for col in df.select_dtypes(include=['float']).columns:
            df[col] = df[col].astype('float32')
            
        # Kategorikus oszlopok optimalizálása
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # Ha az egyedi értékek aránya alacsony
                df[col] = df[col].astype('category')
                
        return df
    
    def memory_efficient(max_size_mb=100):
        """
        Dekorátor nagy memóriaigényű függvényekhez
        
        Args:
            max_size_mb: Maximális memóriahasználat MB-ban
            
        Returns:
            Dekorált függvény
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Memória használat ellenőrzése a függvény előtt
                memory_manager = MemoryManager()
                before_usage = memory_manager.get_memory_usage()
                
                # Garbage collection kényszerítése
                gc.collect()
                
                # Függvény futtatása
                result = func(*args, **kwargs)
                
                # Memória használat ellenőrzése a függvény után
                after_usage = memory_manager.get_memory_usage()
                used_mb = after_usage['process_mb'] - before_usage['process_mb']
                
                logger.debug(f"Függvény memória használat: {func.__name__}: {used_mb:.2f}MB")
                
                # Figyelmeztetés, ha a memória használat túl magas
                if used_mb > max_size_mb:
                    logger.warning(f"Magas memória használat: {func.__name__}: {used_mb:.2f}MB > {max_size_mb}MB")
                
                # Garbage collection a függvény után
                gc.collect()
                
                return result
            return wrapper
        return decorator

# Globális memória kezelő példány
memory_manager = MemoryManager()

# Memória használat ellenőrzése időközönként
def start_memory_monitoring(interval=300):
    """
    Elindítja a memória használat rendszeres ellenőrzését
    
    Args:
        interval: Ellenőrzési időköz másodpercben
    """
    import threading
    
    def monitor_memory():
        while True:
            memory_manager.check_memory()
            time.sleep(interval)
    
    # Háttérszál indítása
    thread = threading.Thread(target=monitor_memory, daemon=True)
    thread.start()
    logger.info(f"Memória monitoring elindítva ({interval} másodperces időközzel)")
EOF
echo "Memória kezelés optimalizálása kész."

echo "CPU optimalizálás..."
cat > advanced_trading_system/utils/cpu_optimizer.py << EOF
"""
CPU optimalizáló - RPI4 optimalizált
"""
import os
import psutil
import logging
import multiprocessing
from functools import wraps
import time
import threading

logger = logging.getLogger(__name__)

class CPUOptimizer:
    """CPU használat optimalizálása RPI4 környezetben"""
    
    def __init__(self, max_cpu_percent=80, check_interval=30):
        """
        Inicializálja a CPU optimalizálót
        
        Args:
            max_cpu_percent: Maximális CPU használat százalékban
            check_interval: Ellenőrzési időköz másodpercben
        """
        self.max_cpu_percent = max_cpu_percent
        self.check_interval = check_interval
        self.last_check = 0
        self.process = psutil.Process(os.getpid())
        self.cpu_count = multiprocessing.cpu_count()
        self.throttling = False
        
    def get_cpu_usage(self):
        """Visszaadja a jelenlegi CPU használatot"""
        # Folyamat CPU használata
        process_percent = self.process.cpu_percent(interval=0.1) / self.cpu_count
        
        # Rendszer CPU használata
        system_percent = psutil.cpu_percent(interval=0.1)
        
        # CPU hőmérséklet (csak Raspberry Pi-n működik)
        cpu_temp = None
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                cpu_temp = float(f.read()) / 1000.0
        except:
            pass
        
        return {
            'process_percent': process_percent,
            'system_percent': system_percent,
            'cpu_count': self.cpu_count,
            'cpu_temp': cpu_temp
        }
    
    def check_cpu(self):
        """
        Ellenőrzi a CPU használatot és szükség esetén intézkedik
        
        Returns:
            dict: CPU használati adatok
        """
        current_time = time.time()
        
        # Csak a megadott időközönként ellenőriz
        if current_time - self.last_check < self.check_interval:
            return None
            
        self.last_check = current_time
        cpu_usage = self.get_cpu_usage()
        
        # CPU használat naplózása
        logger.debug(f"CPU használat: Folyamat={cpu_usage['process_percent']:.2f}%, "
                    f"Rendszer={cpu_usage['system_percent']}%, "
                    f"Hőmérséklet={cpu_usage['cpu_temp']}°C")
        
        # CPU használat szabályozása, ha meghaladja a küszöböt
        if cpu_usage['system_percent'] > self.max_cpu_percent:
            if not self.throttling:
                logger.warning(f"CPU használat túl magas: {cpu_usage['system_percent']}% > {self.max_cpu_percent}%")
                logger.info("CPU korlátozás aktiválva")
                self.throttling = True
        elif self.throttling and cpu_usage['system_percent'] < self.max_cpu_percent - 10:
            logger.info(f"CPU használat normalizálódott: {cpu_usage['system_percent']}%")
            logger.info("CPU korlátozás deaktiválva")
            self.throttling = False
        
        return cpu_usage
    
    def cpu_intensive(max_percent=50, priority=None):
        """
        Dekorátor CPU-intenzív függvényekhez
        
        Args:
            max_percent: Maximális CPU használat százalékban
            priority: Folyamat prioritás (nice érték, -20 és 19 között)
            
        Returns:
            Dekorált függvény
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Eredeti prioritás mentése
                original_priority = os.getpriority(os.PRIO_PROCESS, 0)
                
                # Prioritás beállítása, ha meg van adva
                if priority is not None:
                    try:
                        os.setpriority(os.PRIO_PROCESS, 0, priority)
                        logger.debug(f"Folyamat prioritás beállítva: {priority}")
                    except:
                        logger.warning(f"Nem sikerült beállítani a folyamat prioritást: {priority}")
                
                # CPU használat ellenőrzése
                cpu_optimizer = CPUOptimizer()
                cpu_usage = cpu_optimizer.get_cpu_usage()
                
                # Várakozás, ha a CPU használat túl magas
                while cpu_usage['system_percent'] > max_percent:
                    logger.debug(f"Várakozás a CPU használat csökkenésére: {cpu_usage['system_percent']}% > {max_percent}%")
                    time.sleep(1)
                    cpu_usage = cpu_optimizer.get_cpu_usage()
                
                # Függvény futtatása
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Futási idő naplózása
                logger.debug(f"Függvény futási idő: {func.__name__}: {execution_time:.2f} másodperc")
                
                # Eredeti prioritás visszaállítása
                if priority is not None:
                    try:
                        os.setpriority(os.PRIO_PROCESS, 0, original_priority)
                    except:
                        pass
                
                return result
            return wrapper
        return decorator
    
    def parallel_execution(self, func, items, max_workers=None):
        """
        Párhuzamos végrehajtás a CPU magok optimális kihasználásával
        
        Args:
            func: Végrehajtandó függvény
            items: Bemeneti elemek listája
            max_workers: Maximális worker szálak száma (None = CPU magok száma)
            
        Returns:
            list: Eredmények listája
        """
        if max_workers is None:
            # Alapértelmezetten a CPU magok számának 75%-a
            max_workers = max(1, int(self.cpu_count * 0.75))
        
        logger.debug(f"Párhuzamos végrehajtás indítása: {len(items)} elem, {max_workers} worker")
        
        results = []
        with multiprocessing.Pool(processes=max_workers) as pool:
            results = pool.map(func, items)
            
        return results

# Globális CPU optimalizáló példány
cpu_optimizer = CPUOptimizer()

# CPU használat ellenőrzése időközönként
def start_cpu_monitoring(interval=60):
    """
    Elindítja a CPU használat rendszeres ellenőrzését
    
    Args:
        interval: Ellenőrzési időköz másodpercben
    """
    def monitor_cpu():
        while True:
            cpu_optimizer.check_cpu()
            time.sleep(interval)
    
    # Háttérszál indítása
    thread = threading.Thread(target=monitor_cpu, daemon=True)
    thread.start()
    logger.info(f"CPU monitoring elindítva ({interval} másodperces időközzel)")
EOF
echo "CPU optimalizálás kész."

echo "Hálózati optimalizálás..."
cat > advanced_trading_system/utils/network_manager.py << EOF
"""
Hálózati kezelő - RPI4 optimalizált
"""
import logging
import time
import socket
import requests
import threading
import queue
from functools import wraps
import random

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
        self.session = requests.Session()
        self.request_queue = queue.Queue()
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
        # Timeout beállítása, ha nincs megadva
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout
        
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
                response = self.session.request(method, url, **kwargs)
                
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
EOF
echo "Hálózati optimalizálás kész."

echo "Tárhely optimalizálás..."
cat > advanced_trading_system/utils/storage_optimizer.py << EOF
"""
Tárhely optimalizáló - RPI4 optimalizált
"""
import os
import logging
import shutil
import gzip
import json
import pickle
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StorageOptimizer:
    """Tárhely használat optimalizálása RPI4 környezetben"""
    
    def __init__(self, data_dir='data', log_dir='logs', max_log_days=7, max_data_days=30):
        """
        Inicializálja a tárhely optimalizálót
        
        Args:
            data_dir: Adatok könyvtára
            log_dir: Naplófájlok könyvtára
            max_log_days: Naplófájlok maximális megőrzési ideje napokban
            max_data_days: Adatok maximális megőrzési ideje napokban
        """
        self.data_dir = data_dir
        self.log_dir = log_dir
        self.max_log_days = max_log_days
        self.max_data_days = max_data_days
        
    def get_storage_usage(self):
        """Visszaadja a jelenlegi tárhely használatot"""
        # Rendszer tárhely használata
        disk = shutil.disk_usage('/')
        
        # Adatok és naplók mérete
        data_size = self._get_directory_size(self.data_dir)
        log_size = self._get_directory_size(self.log_dir)
        
        return {
            'total_gb': disk.total / (1024**3),
            'used_gb': disk.used / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent': disk.used / disk.total * 100,
            'data_mb': data_size / (1024**2),
            'log_mb': log_size / (1024**2)
        }
    
    def _get_directory_size(self, directory):
        """
        Visszaadja egy könyvtár méretét bájtokban
        
        Args:
            directory: Könyvtár elérési útja
            
        Returns:
            int: Könyvtár mérete bájtokban
        """
        total_size = 0
        
        if not os.path.exists(directory):
            return total_size
            
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
                    
        return total_size
    
    def cleanup_old_files(self):
        """
        Régi fájlok törlése
        
        Returns:
            dict: Törölt fájlok statisztikái
        """
        stats = {
            'logs_deleted': 0,
            'logs_size': 0,
            'data_deleted': 0,
            'data_size': 0
        }
        
        # Régi naplófájlok törlése
        stats.update(self._cleanup_directory(self.log_dir, self.max_log_days, 'logs'))
        
        # Régi adatfájlok törlése
        stats.update(self._cleanup_directory(self.data_dir, self.max_data_days, 'data'))
        
        logger.info(f"Tisztítás befejezve: {stats['logs_deleted']} naplófájl törölve ({stats['logs_size'] / 1024**2:.2f}MB), "
                   f"{stats['data_deleted']} adatfájl törölve ({stats['data_size'] / 1024**2:.2f}MB)")
        
        return stats
    
    def _cleanup_directory(self, directory, max_days, file_type):
        """
        Régi fájlok törlése egy könyvtárból
        
        Args:
            directory: Könyvtár elérési útja
            max_days: Maximális megőrzési idő napokban
            file_type: Fájl típus ('logs' vagy 'data')
            
        Returns:
            dict: Törölt fájlok statisztikái
        """
        stats = {
            f'{file_type}_deleted': 0,
            f'{file_type}_size': 0
        }
        
        if not os.path.exists(directory):
            return stats
            
        # Határidő kiszámítása
        cutoff_date = datetime.now() - timedelta(days=max_days)
        cutoff_timestamp = cutoff_date.timestamp()
        
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                
                if os.path.isfile(file_path):
                    # Fájl módosítási idejének ellenőrzése
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_timestamp:
                        # Fájl méretének mentése
                        file_size = os.path.getsize(file_path)
                        stats[f'{file_type}_size'] += file_size
                        
                        # Fájl törlése
                        try:
                            os.remove(file_path)
                            stats[f'{file_type}_deleted'] += 1
                            logger.debug(f"Fájl törölve: {file_path} ({file_size / 1024:.2f}KB)")
                        except Exception as e:
                            logger.warning(f"Nem sikerült törölni a fájlt: {file_path}, {e}")
        
        return stats
    
    def compress_file(self, file_path, delete_original=True):
        """
        Fájl tömörítése gzip formátumba
        
        Args:
            file_path: Tömörítendő fájl elérési útja
            delete_original: Eredeti fájl törlése tömörítés után
            
        Returns:
            str: Tömörített fájl elérési útja
        """
        if not os.path.exists(file_path):
            logger.warning(f"A tömörítendő fájl nem létezik: {file_path}")
            return None
            
        compressed_path = f"{file_path}.gz"
        
        try:
            # Fájl tömörítése
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Eredeti fájl törlése, ha szükséges
            if delete_original:
                os.remove(file_path)
                
            # Tömörítési arány kiszámítása
            original_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            compressed_size = os.path.getsize(compressed_path)
            ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            logger.debug(f"Fájl tömörítve: {file_path} -> {compressed_path}, "
                        f"méret: {original_size / 1024:.2f}KB -> {compressed_size / 1024:.2f}KB, "
                        f"arány: {ratio:.2f}%")
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"Hiba a fájl tömörítése során: {file_path}, {e}")
            return None
    
    def decompress_file(self, compressed_path, delete_compressed=True):
        """
        Gzip fájl kitömörítése
        
        Args:
            compressed_path: Tömörített fájl elérési útja
            delete_compressed: Tömörített fájl törlése kitömörítés után
            
        Returns:
            str: Kitömörített fájl elérési útja
        """
        if not os.path.exists(compressed_path):
            logger.warning(f"A kitömörítendő fájl nem létezik: {compressed_path}")
            return None
            
        # Eredeti fájlnév meghatározása
        if compressed_path.endswith('.gz'):
            original_path = compressed_path[:-3]
        else:
            original_path = f"{compressed_path}.decompressed"
            
        try:
            # Fájl kitömörítése
            with gzip.open(compressed_path, 'rb') as f_in:
                with open(original_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Tömörített fájl törlése, ha szükséges
            if delete_compressed:
                os.remove(compressed_path)
                
            logger.debug(f"Fájl kitömörítve: {compressed_path} -> {original_path}")
            
            return original_path
            
        except Exception as e:
            logger.error(f"Hiba a fájl kitömörítése során: {compressed_path}, {e}")
            return None
    
    def save_data_efficient(self, data, file_path, format='json', compress=True):
        """
        Adatok hatékony mentése
        
        Args:
            data: Mentendő adatok
            file_path: Cél fájl elérési útja
            format: Formátum ('json' vagy 'pickle')
            compress: Tömörítés engedélyezése
            
        Returns:
            str: Mentett fájl elérési útja
        """
        # Könyvtár létrehozása, ha nem létezik
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            # Adatok mentése a megadott formátumban
            if format == 'json':
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            elif format == 'pickle':
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            else:
                logger.error(f"Ismeretlen formátum: {format}")
                return None
                
            # Fájl tömörítése, ha szükséges
            if compress:
                return self.compress_file(file_path)
            else:
                return file_path
                
        except Exception as e:
            logger.error(f"Hiba az adatok mentése során: {file_path}, {e}")
            return None
    
    def load_data_efficient(self, file_path, format='json'):
        """
        Adatok hatékony betöltése
        
        Args:
            file_path: Betöltendő fájl elérési útja
            format: Formátum ('json' vagy 'pickle')
            
        Returns:
            object: Betöltött adatok
        """
        # Tömörített fájl ellenőrzése
        is_compressed = file_path.endswith('.gz')
        actual_path = file_path
        
        if is_compressed:
            # Fájl kitömörítése
            actual_path = self.decompress_file(file_path, delete_compressed=False)
            if not actual_path:
                return None
        
        try:
            # Adatok betöltése a megadott formátumban
            if format == 'json' or (is_compressed and file_path.endswith('.json.gz')):
                with open(actual_path, 'r') as f:
                    data = json.load(f)
            elif format == 'pickle' or (is_compressed and file_path.endswith('.pickle.gz')):
                with open(actual_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                logger.error(f"Ismeretlen formátum: {format}")
                return None
                
            # Ideiglenes kitömörített fájl törlése
            if is_compressed and os.path.exists(actual_path):
                os.remove(actual_path)
                
            return data
                
        except Exception as e:
            logger.error(f"Hiba az adatok betöltése során: {file_path}, {e}")
            
            # Ideiglenes kitömörített fájl törlése hiba esetén is
            if is_compressed and actual_path != file_path and os.path.exists(actual_path):
                os.remove(actual_path)
                
            return None

# Globális tárhely optimalizáló példány
storage_optimizer = StorageOptimizer()

# Tárhely tisztítás időközönként
def start_storage_cleanup(interval=86400):  # 24 óra
    """
    Elindítja a tárhely rendszeres tisztítását
    
    Args:
        interval: Tisztítási időköz másodpercben
    """
    def cleanup_storage():
        while True:
            storage_usage = storage_optimizer.get_storage_usage()
            logger.info(f"Tárhely használat: {storage_usage['percent']:.2f}%, "
                       f"Szabad: {storage_usage['free_gb']:.2f}GB, "
                       f"Adatok: {storage_usage['data_mb']:.2f}MB, "
                       f"Naplók: {storage_usage['log_mb']:.2f}MB")
            
            # Tisztítás, ha a tárhely használat magas
            if storage_usage['percent'] > 80:
                logger.warning(f"Magas tárhely használat: {storage_usage['percent']:.2f}%, tisztítás indítása")
                storage_optimizer.cleanup_old_files()
            else:
                # Rendszeres tisztítás
                storage_optimizer.cleanup_old_files()
                
            time.sleep(interval)
    
    # Háttérszál indítása
    thread = threading.Thread(target=cleanup_storage, daemon=True)
    thread.start()
    logger.info(f"Tárhely tisztítás elindítva ({interval / 3600:.1f} óránként)")
EOF
echo "Tárhely optimalizálás kész."

echo "Teljesítmény tesztelés..."
cat > advanced_trading_system/tests/performance_tests/rpi4_benchmark.py << EOF
"""
RPI4 teljesítmény teszt
"""
import os
import sys
import time
import logging
import psutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Projekt gyökérkönyvtárának hozzáadása a Python elérési úthoz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Naplózás beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RPI4Benchmark:
    """Raspberry Pi 4 teljesítmény teszt"""
    
    def __init__(self, output_dir='benchmark_results'):
        """
        Inicializálja a teljesítmény tesztet
        
        Args:
            output_dir: Eredmények könyvtára
        """
        self.output_dir = output_dir
        self.results = {}
        self.metrics = []
        
        # Könyvtár létrehozása, ha nem létezik
        os.makedirs(output_dir, exist_ok=True)
        
    def run_all_tests(self):
        """
        Összes teszt futtatása
        
        Returns:
            dict: Teszt eredmények
        """
        logger.info("RPI4 teljesítmény teszt indítása")
        
        # Rendszer információk
        self.collect_system_info()
        
        # CPU teszt
        self.test_cpu_performance()
        
        # Memória teszt
        self.test_memory_performance()
        
        # Tárhely teszt
        self.test_storage_performance()
        
        # Hálózati teszt
        self.test_network_performance()
        
        # Adatfeldolgozás teszt
        self.test_data_processing()
        
        # Eredmények mentése
        self.save_results()
        
        logger.info("RPI4 teljesítmény teszt befejezve")
        return self.results
    
    def collect_system_info(self):
        """Rendszer információk gyűjtése"""
        logger.info("Rendszer információk gyűjtése")
        
        # CPU információ
        cpu_info = {
            'cpu_count': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'cpu_freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'cpu_freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else None
        }
        
        # Memória információ
        memory = psutil.virtual_memory()
        memory_info = {
            'total_mb': memory.total / (1024**2),
            'available_mb': memory.available / (1024**2),
            'percent': memory.percent
        }
        
        # Tárhely információ
        disk = psutil.disk_usage('/')
        disk_info = {
            'total_gb': disk.total / (1024**3),
            'free_gb': disk.free / (1024**3),
            'percent': disk.percent
        }
        
        # Hálózati információ
        net_io = psutil.net_io_counters()
        net_info = {
            'bytes_sent_mb': net_io.bytes_sent / (1024**2),
            'bytes_recv_mb': net_io.bytes_recv / (1024**2)
        }
        
        # CPU hőmérséklet
        cpu_temp = None
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                cpu_temp = float(f.read()) / 1000.0
        except:
            pass
        
        # Rendszer információk mentése
        self.results['system_info'] = {
            'timestamp': datetime.now().isoformat(),
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'network': net_info,
            'cpu_temp': cpu_temp
        }
        
        logger.info(f"CPU: {cpu_info['cpu_count_logical']} logikai mag, "
                   f"Memória: {memory_info['total_mb']:.2f}MB, "
                   f"Tárhely: {disk_info['total_gb']:.2f}GB, "
                   f"CPU hőmérséklet: {cpu_temp}°C")
    
    def test_cpu_performance(self):
        """CPU teljesítmény teszt"""
        logger.info("CPU teljesítmény teszt indítása")
        
        results = {}
        
        # Metrika gyűjtés indítása
        self.start_metrics_collection()
        
        # Mátrix műveletek teszt
        logger.info("Mátrix műveletek teszt")
        start_time = time.time()
        
        # 1000x1000 mátrix szorzás
        size = 1000
        matrix_a = np.random.rand(size, size)
        matrix_b = np.random.rand(size, size)
        
        for _ in range(3):
            result = np.matmul(matrix_a, matrix_b)
        
        matrix_time = time.time() - start_time
        results['matrix_multiplication'] = {
            'time': matrix_time,
            'size': size,
            'operations_per_second': size**3 / matrix_time
        }
        
        logger.info(f"Mátrix szorzás: {matrix_time:.2f} másodperc")
        
        # Prímszám keresés teszt
        logger.info("Prímszám keresés teszt")
        start_time = time.time()
        
        def is_prime(n):
            if n <= 1:
                return False
            if n <= 3:
                return True
            if n % 2 == 0 or n % 3 == 0:
                return False
            i = 5
            while i * i <= n:
                if n % i == 0 or n % (i + 2) == 0:
                    return False
                i += 6
            return True
        
        prime_count = 0
        limit = 100000
        
        for i in range(2, limit):
            if is_prime(i):
                prime_count += 1
        
        prime_time = time.time() - start_time
        results['prime_search'] = {
            'time': prime_time,
            'limit': limit,
            'prime_count': prime_count,
            'numbers_per_second': limit / prime_time
        }
        
        logger.info(f"Prímszám keresés: {prime_time:.2f} másodperc, {prime_count} prímszám")
        
        # Metrika gyűjtés leállítása
        metrics = self.stop_metrics_collection()
        results['metrics'] = metrics
        
        # Eredmények mentése
        self.results['cpu_performance'] = results
    
    def test_memory_performance(self):
        """Memória teljesítmény teszt"""
        logger.info("Memória teljesítmény teszt indítása")
        
        results = {}
        
        # Metrika gyűjtés indítása
        self.start_metrics_collection()
        
        # Nagy tömb létrehozása és műveletek
        logger.info("Nagy tömb műveletek teszt")
        start_time = time.time()
        
        # 100MB tömb létrehozása
        size = 25 * 1024 * 1024  # 25 millió elem (kb. 100MB)
        data = np.random.rand(size)
        
        # Műveletek a tömbön
        data_sum = np.sum(data)
        data_mean = np.mean(data)
        data_std = np.std(data)
        data_sorted = np.sort(data)
        
        array_time = time.time() - start_time
        results['array_operations'] = {
            'time': array_time,
            'size_mb': size * 8 / (1024**2),  # 8 byte per float64
            'sum': data_sum,
            'mean': data_mean,
            'std': data_std,
            'mb_per_second': size * 8 / (1024**2) / array_time
        }
        
        logger.info(f"Tömb műveletek: {array_time:.2f} másodperc, "
                   f"Méret: {size * 8 / (1024**2):.2f}MB")
        
        # Memória allokáció és felszabadítás teszt
        logger.info("Memória allokáció teszt")
        start_time = time.time()
        
        iterations = 100
        alloc_size = 1 * 1024 * 1024  # 1MB
        
        for _ in range(iterations):
            # Memória allokáció
            data = np.random.rand(alloc_size)
            # Művelet a memórián
            result = np.sum(data)
            # Memória felszabadítás (Python garbage collector)
            del data
        
        alloc_time = time.time() - start_time
        results['memory_allocation'] = {
            'time': alloc_time,
            'iterations': iterations,
            'size_per_iteration_mb': alloc_size * 8 / (1024**2),
            'total_size_mb': iterations * alloc_size * 8 / (1024**2),
            'mb_per_second': iterations * alloc_size * 8 / (1024**2) / alloc_time
        }
        
        logger.info(f"Memória allokáció: {alloc_time:.2f} másodperc, "
                   f"Összes méret: {iterations * alloc_size * 8 / (1024**2):.2f}MB")
        
        # Metrika gyűjtés leállítása
        metrics = self.stop_metrics_collection()
        results['metrics'] = metrics
        
        # Eredmények mentése
        self.results['memory_performance'] = results
    
    def test_storage_performance(self):
        """Tárhely teljesítmény teszt"""
        logger.info("Tárhely teljesítmény teszt indítása")
        
        results = {}
        
        # Metrika gyűjtés indítása
        self.start_metrics_collection()
        
        # Teszt fájl elérési útja
        test_file = os.path.join(self.output_dir, 'storage_test.dat')
        
        # Fájl írás teszt
        logger.info("Fájl írás teszt")
        start_time = time.time()
        
        # 100MB adatok írása
        size_mb = 100
        chunk_size = 1024 * 1024  # 1MB
        chunks = size_mb
        
        with open(test_file, 'wb') as f:
            for _ in range(chunks):
                f.write(os.urandom(chunk_size))
        
        write_time = time.time() - start_time
        results['file_write'] = {
            'time': write_time,
            'size_mb': size_mb,
            'mb_per_second': size_mb / write_time
        }
        
        logger.info(f"Fájl írás: {write_time:.2f} másodperc, "
                   f"Sebesség: {size_mb / write_time:.2f}MB/s")
        
        # Fájl olvasás teszt
        logger.info("Fájl olvasás teszt")
        start_time = time.time()
        
        # Fájl olvasása
        with open(test_file, 'rb') as f:
            while f.read(chunk_size):
                pass
        
        read_time = time.time() - start_time
        results['file_read'] = {
            'time': read_time,
            'size_mb': size_mb,
            'mb_per_second': size_mb / read_time
        }
        
        logger.info(f"Fájl olvasás: {read_time:.2f} másodperc, "
                   f"Sebesség: {size_mb / read_time:.2f}MB/s")
        
        # Fájl törlése
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Metrika gyűjtés leállítása
        metrics = self.stop_metrics_collection()
        results['metrics'] = metrics
        
        # Eredmények mentése
        self.results['storage_performance'] = results
    
    def test_network_performance(self):
        """Hálózati teljesítmény teszt"""
        logger.info("Hálózati teljesítmény teszt indítása")
        
        results = {}
        
        # Metrika gyűjtés indítása
        self.start_metrics_collection()
        
        # HTTP letöltés teszt
        logger.info("HTTP letöltés teszt")
        start_time = time.time()
        
        import requests
        
        # 10MB teszt fájl letöltése
        url = "https://speed.hetzner.de/10MB.bin"
        
        try:
            response = requests.get(url, stream=True, timeout=30)
            content_length = int(response.headers.get('content-length', 0))
            
            # Adatok olvasása
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    downloaded += len(chunk)
            
            download_time = time.time() - start_time
            size_mb = content_length / (1024**2)
            
            results['http_download'] = {
                'time': download_time,
                'size_mb': size_mb,
                'mb_per_second': size_mb / download_time,
                'url': url
            }
            
            logger.info(f"HTTP letöltés: {download_time:.2f} másodperc, "
                       f"Méret: {size_mb:.2f}MB, "
                       f"Sebesség: {size_mb / download_time:.2f}MB/s")
                       
        except Exception as e:
            logger.error(f"Hiba a HTTP letöltés során: {e}")
            results['http_download'] = {
                'error': str(e)
            }
        
        # DNS feloldás teszt
        logger.info("DNS feloldás teszt")
        start_time = time.time()
        
        import socket
        
        domains = [
            'google.com',
            'facebook.com',
            'amazon.com',
            'microsoft.com',
            'apple.com',
            'netflix.com',
            'twitter.com',
            'instagram.com',
            'linkedin.com',
            'github.com'
        ]
        
        resolved = 0
        total_time = 0
        
        for domain in domains:
            try:
                domain_start = time.time()
                socket.gethostbyname(domain)
                domain_time = time.time() - domain_start
                total_time += domain_time
                resolved += 1
            except Exception as e:
                logger.warning(f"Nem sikerült feloldani a domaint: {domain}, {e}")
        
        dns_time = time.time() - start_time
        
        results['dns_resolution'] = {
            'time': dns_time,
            'domains': domains,
            'resolved': resolved,
            'avg_time_ms': (total_time / resolved) * 1000 if resolved > 0 else 0
        }
        
        logger.info(f"DNS feloldás: {dns_time:.2f} másodperc, "
                   f"Feloldva: {resolved}/{len(domains)}, "
                   f"Átlagos idő: {(total_time / resolved) * 1000:.2f}ms")
        
        # Metrika gyűjtés leállítása
        metrics = self.stop_metrics_collection()
        results['metrics'] = metrics
        
        # Eredmények mentése
        self.results['network_performance'] = results
    
    def test_data_processing(self):
        """Adatfeldolgozás teljesítmény teszt"""
        logger.info("Adatfeldolgozás teljesítmény teszt indítása")
        
        results = {}
        
        # Metrika gyűjtés indítása
        self.start_metrics_collection()
        
        # Pandas DataFrame műveletek
        logger.info("Pandas DataFrame műveletek teszt")
        start_time = time.time()
        
        # Nagy DataFrame létrehozása
        rows = 100000
        cols = 10
        
        df = pd.DataFrame(np.random.randn(rows, cols), 
                         columns=[f'col_{i}' for i in range(cols)])
        
        # Műveletek a DataFrame-en
        df['col_sum'] = df.sum(axis=1)
        df['col_mean'] = df.mean(axis=1)
        df['col_max'] = df.max(axis=1)
        df['col_min'] = df.min(axis=1)
        
        # Csoportosítás és aggregálás
        df['group'] = np.random.randint(0, 100, size=rows)
        grouped = df.groupby('group').agg({
            'col_0': 'mean',
            'col_1': 'sum',
            'col_2': 'min',
            'col_3': 'max',
            'col_sum': 'mean'
        })
        
        # Rendezés
        df_sorted = df.sort_values('col_sum', ascending=False)
        
        # Szűrés
        df_filtered = df[df['col_sum'] > 0]
        
        pandas_time = time.time() - start_time
        results['pandas_operations'] = {
            'time': pandas_time,
            'rows': rows,
            'cols': cols,
            'operations_per_second': rows / pandas_time
        }
        
        logger.info(f"Pandas műveletek: {pandas_time:.2f} másodperc, "
                   f"Sorok: {rows}, Oszlopok: {cols}")
        
        # Idősor adatok feldolgozása
        logger.info("Idősor adatok feldolgozása teszt")
        start_time = time.time()
        
        # Idősor adatok létrehozása
        periods = 10000
        freq = 'T'  # Perc
        
        ts = pd.Series(np.random.randn(periods), 
                      index=pd.date_range('2025-01-01', periods=periods, freq=freq))
        
        # Mozgóátlag számítása
        ts_ma_5 = ts.rolling(window=5).mean()
        ts_ma_20 = ts.rolling(window=20).mean()
        
        # Exponenciális mozgóátlag
        ts_ema_5 = ts.ewm(span=5).mean()
        ts_ema_20 = ts.ewm(span=20).mean()
        
        # Újramintavételezés
        ts_daily = ts.resample('D').mean()
        ts_hourly = ts.resample('H').mean()
        
        # Időeltolás
        ts_shift_1 = ts.shift(1)
        ts_shift_5 = ts.shift(5)
        
        # Százalékos változás
        ts_pct_change = ts.pct_change()
        
        timeseries_time = time.time() - start_time
        results['timeseries_operations'] = {
            'time': timeseries_time,
            'periods': periods,
            'freq': freq,
            'operations_per_second': periods / timeseries_time
        }
        
        logger.info(f"Idősor műveletek: {timeseries_time:.2f} másodperc, "
                   f"Időpontok: {periods}")
        
        # Metrika gyűjtés leállítása
        metrics = self.stop_metrics_collection()
        results['metrics'] = metrics
        
        # Eredmények mentése
        self.results['data_processing'] = results
    
    def start_metrics_collection(self):
        """Metrika gyűjtés indítása"""
        self.metrics = []
        self.metrics_start_time = time.time()
        
        # Háttérszál indítása a metrikák gyűjtéséhez
        self.metrics_running = True
        
        def collect_metrics():
            while self.metrics_running:
                # CPU használat
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Memória használat
                memory = psutil.virtual_memory()
                
                # CPU hőmérséklet
                cpu_temp = None
                try:
                    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                        cpu_temp = float(f.read()) / 1000.0
                except:
                    pass
                
                # Metrika mentése
                self.metrics.append({
                    'timestamp': time.time() - self.metrics_start_time,
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / (1024**2),
                    'cpu_temp': cpu_temp
                })
                
                # Várakozás a következő mérésig
                time.sleep(0.5)
        
        import threading
        self.metrics_thread = threading.Thread(target=collect_metrics)
        self.metrics_thread.daemon = True
        self.metrics_thread.start()
    
    def stop_metrics_collection(self):
        """
        Metrika gyűjtés leállítása
        
        Returns:
            list: Gyűjtött metrikák
        """
        self.metrics_running = False
        
        # Várakozás a szál befejezésére
        if hasattr(self, 'metrics_thread') and self.metrics_thread.is_alive():
            self.metrics_thread.join(timeout=1.0)
        
        return self.metrics
    
    def save_results(self):
        """Eredmények mentése"""
        # Eredmények mentése JSON formátumban
        import json
        
        # Timestamp hozzáadása
        self.results['timestamp'] = datetime.now().isoformat()
        
        # Eredmények mentése
        result_file = os.path.join(self.output_dir, 'rpi4_benchmark_results.json')
        with open(result_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Eredmények mentve: {result_file}")
        
        # Grafikonok generálása
        self.generate_plots()
    
    def generate_plots(self):
        """Grafikonok generálása az eredményekből"""
        # CPU teljesítmény grafikon
        if 'cpu_performance' in self.results and 'metrics' in self.results['cpu_performance']:
            metrics = self.results['cpu_performance']['metrics']
            
            plt.figure(figsize=(10, 6))
            
            # CPU használat
            plt.subplot(2, 1, 1)
            plt.plot([m['timestamp'] for m in metrics], [m['cpu_percent'] for m in metrics], 'b-', label='CPU %')
            plt.title('CPU használat a CPU teszt során')
            plt.xlabel('Idő (másodperc)')
            plt.ylabel('CPU használat (%)')
            plt.grid(True)
            plt.legend()
            
            # CPU hőmérséklet
            plt.subplot(2, 1, 2)
            plt.plot([m['timestamp'] for m in metrics], [m['cpu_temp'] for m in metrics], 'r-', label='CPU hőmérséklet')
            plt.title('CPU hőmérséklet a CPU teszt során')
            plt.xlabel('Idő (másodperc)')
            plt.ylabel('Hőmérséklet (°C)')
            plt.grid(True)
            plt.legend()
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'cpu_performance.png'))
            plt.close()
        
        # Memória teljesítmény grafikon
        if 'memory_performance' in self.results and 'metrics' in self.results['memory_performance']:
            metrics = self.results['memory_performance']['metrics']
            
            plt.figure(figsize=(10, 6))
            
            # Memória használat
            plt.subplot(2, 1, 1)
            plt.plot([m['timestamp'] for m in metrics], [m['memory_percent'] for m in metrics], 'g-', label='Memória %')
            plt.title('Memória használat a memória teszt során')
            plt.xlabel('Idő (másodperc)')
            plt.ylabel('Memória használat (%)')
            plt.grid(True)
            plt.legend()
            
            # Memória használat MB-ban
            plt.subplot(2, 1, 2)
            plt.plot([m['timestamp'] for m in metrics], [m['memory_used_mb'] for m in metrics], 'm-', label='Memória használat')
            plt.title('Memória használat a memória teszt során')
            plt.xlabel('Idő (másodperc)')
            plt.ylabel('Memória használat (MB)')
            plt.grid(True)
            plt.legend()
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, 'memory_performance.png'))
            plt.close()
        
        # Összesített teljesítmény grafikon
        plt.figure(figsize=(12, 8))
        
        # CPU teljesítmény
        if 'cpu_performance' in self.results:
            cpu_perf = self.results['cpu_performance']
            if 'matrix_multiplication' in cpu_perf and 'prime_search' in cpu_perf:
                plt.subplot(2, 2, 1)
                plt.bar(['Mátrix szorzás', 'Prímszám keresés'], 
                       [cpu_perf['matrix_multiplication']['time'], cpu_perf['prime_search']['time']])
                plt.title('CPU teljesítmény')
                plt.ylabel('Idő (másodperc)')
                plt.grid(True)
        
        # Memória teljesítmény
        if 'memory_performance' in self.results:
            mem_perf = self.results['memory_performance']
            if 'array_operations' in mem_perf and 'memory_allocation' in mem_perf:
                plt.subplot(2, 2, 2)
                plt.bar(['Tömb műveletek', 'Memória allokáció'], 
                       [mem_perf['array_operations']['time'], mem_perf['memory_allocation']['time']])
                plt.title('Memória teljesítmény')
                plt.ylabel('Idő (másodperc)')
                plt.grid(True)
        
        # Tárhely teljesítmény
        if 'storage_performance' in self.results:
            storage_perf = self.results['storage_performance']
            if 'file_write' in storage_perf and 'file_read' in storage_perf:
                plt.subplot(2, 2, 3)
                plt.bar(['Fájl írás', 'Fájl olvasás'], 
                       [storage_perf['file_write']['mb_per_second'], storage_perf['file_read']['mb_per_second']])
                plt.title('Tárhely teljesítmény')
                plt.ylabel('Sebesség (MB/s)')
                plt.grid(True)
        
        # Adatfeldolgozás teljesítmény
        if 'data_processing' in self.results:
            data_perf = self.results['data_processing']
            if 'pandas_operations' in data_perf and 'timeseries_operations' in data_perf:
                plt.subplot(2, 2, 4)
                plt.bar(['Pandas műveletek', 'Idősor műveletek'], 
                       [data_perf['pandas_operations']['time'], data_perf['timeseries_operations']['time']])
                plt.title('Adatfeldolgozás teljesítmény')
                plt.ylabel('Idő (másodperc)')
                plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'overall_performance.png'))
        plt.close()

# Teszt futtatása
if __name__ == '__main__':
    benchmark = RPI4Benchmark()
    results = benchmark.run_all_tests()
    
    # Eredmények kiírása
    print("\n===== Benchmark eredmények =====")
    
    if 'cpu_performance' in results:
        cpu_perf = results['cpu_performance']
        print("\nCPU teljesítmény:")
        if 'matrix_multiplication' in cpu_perf:
            print(f"  Mátrix szorzás: {cpu_perf['matrix_multiplication']['time']:.2f} másodperc")
        if 'prime_search' in cpu_perf:
            print(f"  Prímszám keresés: {cpu_perf['prime_search']['time']:.2f} másodperc")
    
    if 'memory_performance' in results:
        mem_perf = results['memory_performance']
        print("\nMemória teljesítmény:")
        if 'array_operations' in mem_perf:
            print(f"  Tömb műveletek: {mem_perf['array_operations']['time']:.2f} másodperc")
            print(f"  Tömb méret: {mem_perf['array_operations']['size_mb']:.2f}MB")
        if 'memory_allocation' in mem_perf:
            print(f"  Memória allokáció: {mem_perf['memory_allocation']['time']:.2f} másodperc")
    
    if 'storage_performance' in results:
        storage_perf = results['storage_performance']
        print("\nTárhely teljesítmény:")
        if 'file_write' in storage_perf:
            print(f"  Fájl írás: {storage_perf['file_write']['time']:.2f} másodperc")
            print(f"  Írási sebesség: {storage_perf['file_write']['mb_per_second']:.2f}MB/s")
        if 'file_read' in storage_perf:
            print(f"  Fájl olvasás: {storage_perf['file_read']['time']:.2f} másodperc")
            print(f"  Olvasási sebesség: {storage_perf['file_read']['mb_per_second']:.2f}MB/s")
    
    if 'network_performance' in results:
        net_perf = results['network_performance']
        print("\nHálózati teljesítmény:")
        if 'http_download' in net_perf and 'error' not in net_perf['http_download']:
            print(f"  HTTP letöltés: {net_perf['http_download']['time']:.2f} másodperc")
            print(f"  Letöltési sebesség: {net_perf['http_download']['mb_per_second']:.2f}MB/s")
        if 'dns_resolution' in net_perf:
            print(f"  DNS feloldás: {net_perf['dns_resolution']['time']:.2f} másodperc")
            print(f"  Átlagos DNS feloldási idő: {net_perf['dns_resolution']['avg_time_ms']:.2f}ms")
    
    if 'data_processing' in results:
        data_perf = results['data_processing']
        print("\nAdatfeldolgozás teljesítmény:")
        if 'pandas_operations' in data_perf:
            print(f"  Pandas műveletek: {data_perf['pandas_operations']['time']:.2f} másodperc")
        if 'timeseries_operations' in data_perf:
            print(f"  Idősor műveletek: {data_perf['timeseries_operations']['time']:.2f} másodperc")
    
    print(f"\nRészletes eredmények és grafikonok: {benchmark.output_dir}")
EOF
echo "Teljesítmény tesztelés kész."

echo "Rendszer indítási script létrehozása..."
cat > advanced_trading_system/scripts/start.sh << EOF
#!/bin/bash

# Advanced Trading System indítási script
# Raspberry Pi 4 optimalizált

# Könyvtár beállítása
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="\$(dirname "\$SCRIPT_DIR")"
cd "\$PROJECT_DIR"

# Naplózás beállítása
LOG_DIR="\$PROJECT_DIR/logs"
mkdir -p "\$LOG_DIR"
LOG_FILE="\$LOG_DIR/startup_\$(date +%Y%m%d_%H%M%S).log"

# Függvény a naplózáshoz
log() {
    echo "\$(date +"%Y-%m-%d %H:%M:%S") - \$1" | tee -a "\$LOG_FILE"
}

# Rendszer információk kiírása
log "===== Advanced Trading System indítása ====="
log "Projekt könyvtár: \$PROJECT_DIR"
log "Kernel verzió: \$(uname -r)"
log "CPU információ: \$(lscpu | grep "Model name" | sed 's/Model name:[[:space:]]*//')"
log "Memória: \$(free -h | grep Mem | awk '{print \$2}')"
log "Tárhely: \$(df -h / | grep / | awk '{print \$2}')"

# Virtuális környezet aktiválása
if [ -d "\$PROJECT_DIR/venv" ]; then
    log "Virtuális környezet aktiválása..."
    source "\$PROJECT_DIR/venv/bin/activate"
else
    log "HIBA: Virtuális környezet nem található!"
    exit 1
fi

# Függőségek ellenőrzése
log "Függőségek ellenőrzése..."
pip list > "\$LOG_DIR/pip_list.txt"

# Adatkönyvtárak létrehozása
log "Adatkönyvtárak létrehozása..."
mkdir -p "\$PROJECT_DIR/data/market_data"
mkdir -p "\$PROJECT_DIR/data/backtest_results"
mkdir -p "\$PROJECT_DIR/data/models"

# Rendszer erőforrás használat optimalizálása
log "Rendszer erőforrás használat optimalizálása..."

# Alacsony prioritás beállítása
renice 10 \$$ > /dev/null
log "Folyamat prioritás beállítva: \$(nice)"

# Memória limit beállítása (1.5GB)
ulimit -v 1572864
log "Memória limit beállítva: \$(ulimit -v) KB"

# Adatbázis inicializálása
log "Adatbázis inicializálása..."
python -m advanced_trading_system.database.migrations

# Trading Engine indítása
log "Trading Engine indítása..."
nohup python -m advanced_trading_system.core.trading_engine > "\$LOG_DIR/trading_engine.log" 2>&1 &
TRADING_ENGINE_PID=\$!
log "Trading Engine elindítva (PID: \$TRADING_ENGINE_PID)"

# Webes felület indítása
log "Webes felület indítása..."
nohup python -m advanced_trading_system.web_interface.app > "\$LOG_DIR/web_interface.log" 2>&1 &
WEB_INTERFACE_PID=\$!
log "Webes felület elindítva (PID: \$WEB_INTERFACE_PID)"

# PID-ek mentése
echo "\$TRADING_ENGINE_PID" > "\$PROJECT_DIR/trading_engine.pid"
echo "\$WEB_INTERFACE_PID" > "\$PROJECT_DIR/web_interface.pid"

# Várakozás a szolgáltatások elindulására
log "Várakozás a szolgáltatások elindulására..."
sleep 5

# Ellenőrzés, hogy a szolgáltatások futnak-e
if ps -p \$TRADING_ENGINE_PID > /dev/null; then
    log "Trading Engine sikeresen elindult"
else
    log "HIBA: Trading Engine nem indult el!"
fi

if ps -p \$WEB_INTERFACE_PID > /dev/null; then
    log "Webes felület sikeresen elindult"
else
    log "HIBA: Webes felület nem indult el!"
fi

# Webes felület URL kiírása
log "Webes felület elérhető: http://localhost:5000"
log "===== Advanced Trading System indítása befejezve ====="

# Kilépés
exit 0
EOF
chmod +x advanced_trading_system/scripts/start.sh
echo "Rendszer indítási script létrehozva."

echo "Rendszer leállítási script létrehozása..."
cat > advanced_trading_system/scripts/stop.sh << EOF
#!/bin/bash

# Advanced Trading System leállítási script
# Raspberry Pi 4 optimalizált

# Könyvtár beállítása
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="\$(dirname "\$SCRIPT_DIR")"
cd "\$PROJECT_DIR"

# Naplózás beállítása
LOG_DIR="\$PROJECT_DIR/logs"
mkdir -p "\$LOG_DIR"
LOG_FILE="\$LOG_DIR/shutdown_\$(date +%Y%m%d_%H%M%S).log"

# Függvény a naplózáshoz
log() {
    echo "\$(date +"%Y-%m-%d %H:%M:%S") - \$1" | tee -a "\$LOG_FILE"
}

# Rendszer leállítása
log "===== Advanced Trading System leállítása ====="

# Trading Engine leállítása
if [ -f "\$PROJECT_DIR/trading_engine.pid" ]; then
    TRADING_ENGINE_PID=\$(cat "\$PROJECT_DIR/trading_engine.pid")
    if ps -p \$TRADING_ENGINE_PID > /dev/null; then
        log "Trading Engine leállítása (PID: \$TRADING_ENGINE_PID)..."
        kill \$TRADING_ENGINE_PID
        sleep 2
        
        # Ellenőrzés, hogy leállt-e
        if ps -p \$TRADING_ENGINE_PID > /dev/null; then
            log "Trading Engine még fut, kényszerített leállítás..."
            kill -9 \$TRADING_ENGINE_PID
            sleep 1
        fi
        
        if ps -p \$TRADING_ENGINE_PID > /dev/null; then
            log "HIBA: Trading Engine nem állt le!"
        else
            log "Trading Engine sikeresen leállt"
        fi
    else
        log "Trading Engine már nem fut"
    fi
    rm -f "\$PROJECT_DIR/trading_engine.pid"
else
    log "Trading Engine PID fájl nem található"
fi

# Webes felület leállítása
if [ -f "\$PROJECT_DIR/web_interface.pid" ]; then
    WEB_INTERFACE_PID=\$(cat "\$PROJECT_DIR/web_interface.pid")
    if ps -p \$WEB_INTERFACE_PID > /dev/null; then
        log "Webes felület leállítása (PID: \$WEB_INTERFACE_PID)..."
        kill \$WEB_INTERFACE_PID
        sleep 2
        
        # Ellenőrzés, hogy leállt-e
        if ps -p \$WEB_INTERFACE_PID > /dev/null; then
            log "Webes felület még fut, kényszerített leállítás..."
            kill -9 \$WEB_INTERFACE_PID
            sleep 1
        fi
        
        if ps -p \$WEB_INTERFACE_PID > /dev/null; then
            log "HIBA: Webes felület nem állt le!"
        else
            log "Webes felület sikeresen leállt"
        fi
    else
        log "Webes felület már nem fut"
    fi
    rm -f "\$PROJECT_DIR/web_interface.pid"
else
    log "Webes felület PID fájl nem található"
fi

# Egyéb folyamatok ellenőrzése és leállítása
log "Egyéb kapcsolódó folyamatok ellenőrzése..."
PYTHON_PROCESSES=\$(ps aux | grep "python.*advanced_trading_system" | grep -v grep | awk '{print \$2}')
if [ -n "\$PYTHON_PROCESSES" ]; then
    log "További Python folyamatok leállítása: \$PYTHON_PROCESSES"
    for pid in \$PYTHON_PROCESSES; do
        kill \$pid 2>/dev/null
    done
    sleep 2
    
    # Kényszerített leállítás, ha szükséges
    REMAINING_PROCESSES=\$(ps aux | grep "python.*advanced_trading_system" | grep -v grep | awk '{print \$2}')
    if [ -n "\$REMAINING_PROCESSES" ]; then
        log "Kényszerített leállítás: \$REMAINING_PROCESSES"
        for pid in \$REMAINING_PROCESSES; do
            kill -9 \$pid 2>/dev/null
        done
    fi
fi

log "===== Advanced Trading System leállítása befejezve ====="

# Kilépés
exit 0
EOF
chmod +x advanced_trading_system/scripts/stop.sh
echo "Rendszer leállítási script létrehozva."

echo "Automatikus indítás beállítása..."
cat > advanced_trading_system/scripts/setup_autostart.sh << EOF
#!/bin/bash

# Advanced Trading System automatikus indítás beállítása
# Raspberry Pi 4 optimalizált

# Könyvtár beállítása
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="\$(dirname "\$SCRIPT_DIR")"

# Crontab bejegyzés létrehozása
CRONTAB_LINE="@reboot \$PROJECT_DIR/scripts/start.sh >> \$PROJECT_DIR/logs/autostart.log 2>&1"

# Ellenőrzés, hogy a bejegyzés már létezik-e
if crontab -l 2>/dev/null | grep -q "\$PROJECT_DIR/scripts/start.sh"; then
    echo "Az automatikus indítás már be van állítva."
else
    # Új crontab bejegyzés hozzáadása
    (crontab -l 2>/dev/null; echo "\$CRONTAB_LINE") | crontab -
    echo "Automatikus indítás beállítva."
fi

# Systemd service létrehozása (alternatív módszer)
SERVICE_FILE="/etc/systemd/system/advanced-trading-system.service"

echo "Systemd service fájl létrehozása: \$SERVICE_FILE"
sudo tee "\$SERVICE_FILE" > /dev/null << EOL
[Unit]
Description=Advanced Trading System
After=network.target

[Service]
Type=forking
User=\$(whoami)
WorkingDirectory=\$PROJECT_DIR
ExecStart=\$PROJECT_DIR/scripts/start.sh
ExecStop=\$PROJECT_DIR/scripts/stop.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Systemd service engedélyezése
echo "Systemd service engedélyezése..."
sudo systemctl daemon-reload
sudo systemctl enable advanced-trading-system.service

echo "Automatikus indítás beállítása kész."
echo "A rendszer a következő újraindításkor automatikusan elindul."
echo "Kézi indításhoz használja: sudo systemctl start advanced-trading-system"
echo "Kézi leállításhoz használja: sudo systemctl stop advanced-trading-system"
echo "Állapot ellenőrzéséhez használja: sudo systemctl status advanced-trading-system"

exit 0
EOF
chmod +x advanced_trading_system/scripts/setup_autostart.sh
echo "Automatikus indítás beállítása kész."

echo "Teljesítmény tesztelés futtatása..."
cd advanced_trading_system/tests/performance_tests
python3 rpi4_benchmark.py
cd ../../..
echo "Teljesítmény tesztelés befejezve."

echo "===== Advanced Trading System - RPI4 Optimalizáció és Tesztelés Befejezve ====="
echo "Befejezés: $(date)"
