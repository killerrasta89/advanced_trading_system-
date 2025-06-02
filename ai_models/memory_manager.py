"""
Memória kezelő - RPI4 optimalizált
"""
import gc
import os
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
        
    def get_memory_usage(self):
        """Visszaadja a jelenlegi memória használatot"""
        # Rendszer memória használata
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                
            mem_info = {}
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().split(' ')[0]
                    mem_info[key] = int(value)
            
            total = mem_info.get('MemTotal', 0)
            free = mem_info.get('MemFree', 0)
            buffers = mem_info.get('Buffers', 0)
            cached = mem_info.get('Cached', 0)
            
            used = total - free - buffers - cached
            percent = (used / total) * 100 if total > 0 else 0
            
            return {
                'total_mb': total / 1024,
                'used_mb': used / 1024,
                'free_mb': (free + buffers + cached) / 1024,
                'percent': percent
            }
        except Exception as e:
            logger.error(f"Hiba a memória használat lekérdezése során: {e}")
            return {
                'total_mb': 0,
                'used_mb': 0,
                'free_mb': 0,
                'percent': 0
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
        logger.debug(f"Memória használat: {memory_usage['percent']:.2f}%, "
                    f"Használt={memory_usage['used_mb']:.2f}MB, "
                    f"Szabad={memory_usage['free_mb']:.2f}MB")
        
        # Garbage collection, ha a memória használat meghaladja a küszöböt vagy force_gc=True
        if force_gc or memory_usage['percent'] > self.threshold_percent:
            logger.info(f"Garbage collection indítása (Memória használat: {memory_usage['percent']:.2f}%)")
            collected = gc.collect()
            logger.info(f"Garbage collection befejezve: {collected} objektum felszabadítva")
            
            # Frissített memória használat
            memory_usage = self.get_memory_usage()
            logger.info(f"Memória használat GC után: {memory_usage['percent']:.2f}%, "
                       f"Használt={memory_usage['used_mb']:.2f}MB, "
                       f"Szabad={memory_usage['free_mb']:.2f}MB")
        
        return memory_usage
    
    def optimize_dataframe(self, df):
        """
        Pandas DataFrame memória használatának optimalizálása
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            DataFrame: Optimalizált DataFrame
        """
        try:
            import pandas as pd
            import numpy as np
            
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
        except Exception as e:
            logger.error(f"Hiba a DataFrame optimalizálása során: {e}")
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
                used_mb = after_usage['used_mb'] - before_usage['used_mb']
                
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
