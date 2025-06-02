"""
CPU optimalizáló - RPI4 optimalizált
"""
import os
import logging
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
        self.cpu_count = self._get_cpu_count()
        self.throttling = False
        
    def _get_cpu_count(self):
        """Visszaadja a CPU magok számát"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            return cpuinfo.count('processor')
        except:
            # Fallback, ha nem sikerül olvasni a /proc/cpuinfo fájlt
            try:
                import multiprocessing
                return multiprocessing.cpu_count()
            except:
                return 4  # Alapértelmezett érték Raspberry Pi 4-hez
    
    def get_cpu_usage(self):
        """Visszaadja a jelenlegi CPU használatot"""
        try:
            # CPU használat lekérdezése
            with open('/proc/stat', 'r') as f:
                cpu_stat = f.readline().split()
            
            # CPU idők kiszámítása
            user = float(cpu_stat[1])
            nice = float(cpu_stat[2])
            system = float(cpu_stat[3])
            idle = float(cpu_stat[4])
            iowait = float(cpu_stat[5])
            irq = float(cpu_stat[6])
            softirq = float(cpu_stat[7])
            
            # Összes és idle idő
            cpu_all = user + nice + system + idle + iowait + irq + softirq
            cpu_idle = idle + iowait
            
            # Előző értékek mentése
            if hasattr(self, 'prev_cpu_all') and hasattr(self, 'prev_cpu_idle'):
                # CPU használat százalékban
                diff_all = cpu_all - self.prev_cpu_all
                diff_idle = cpu_idle - self.prev_cpu_idle
                diff_usage = (1000 * (diff_all - diff_idle) / diff_all + 5) / 10
                cpu_percent = diff_usage
            else:
                cpu_percent = 0
            
            # Értékek frissítése
            self.prev_cpu_all = cpu_all
            self.prev_cpu_idle = cpu_idle
            
            # CPU hőmérséklet (csak Raspberry Pi-n működik)
            cpu_temp = None
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    cpu_temp = float(f.read()) / 1000.0
            except:
                pass
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': self.cpu_count,
                'cpu_temp': cpu_temp
            }
        except Exception as e:
            logger.error(f"Hiba a CPU használat lekérdezése során: {e}")
            return {
                'cpu_percent': 0,
                'cpu_count': self.cpu_count,
                'cpu_temp': None
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
        logger.debug(f"CPU használat: {cpu_usage['cpu_percent']:.2f}%, "
                    f"Magok: {cpu_usage['cpu_count']}, "
                    f"Hőmérséklet: {cpu_usage['cpu_temp']}°C")
        
        # CPU használat szabályozása, ha meghaladja a küszöböt
        if cpu_usage['cpu_percent'] > self.max_cpu_percent:
            if not self.throttling:
                logger.warning(f"CPU használat túl magas: {cpu_usage['cpu_percent']:.2f}% > {self.max_cpu_percent}%")
                logger.info("CPU korlátozás aktiválva")
                self.throttling = True
        elif self.throttling and cpu_usage['cpu_percent'] < self.max_cpu_percent - 10:
            logger.info(f"CPU használat normalizálódott: {cpu_usage['cpu_percent']:.2f}%")
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
                try:
                    original_priority = os.getpriority(os.PRIO_PROCESS, 0)
                except:
                    original_priority = 0
                
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
                while cpu_usage['cpu_percent'] > max_percent:
                    logger.debug(f"Várakozás a CPU használat csökkenésére: {cpu_usage['cpu_percent']:.2f}% > {max_percent}%")
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
        
        try:
            import multiprocessing
            with multiprocessing.Pool(processes=max_workers) as pool:
                results = pool.map(func, items)
        except:
            # Fallback, ha a multiprocessing nem működik
            results = []
            for item in items:
                results.append(func(item))
            
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
