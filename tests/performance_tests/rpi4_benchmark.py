"""
RPI4 teljesítmény teszt
"""
import os
import sys
import time
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

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
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            cpu_count = cpuinfo.count('processor')
            model_name = "Unknown"
            for line in cpuinfo.split('\n'):
                if 'model name' in line:
                    model_name = line.split(':')[1].strip()
                    break
            
            cpu_info = {
                'cpu_count': cpu_count,
                'model_name': model_name
            }
        except:
            cpu_info = {
                'cpu_count': 4,  # Alapértelmezett érték Raspberry Pi 4-hez
                'model_name': "Unknown"
            }
        
        # Memória információ
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
            
            memory_info = {
                'total_mb': total / 1024,
                'free_mb': free / 1024,
                'buffers_mb': buffers / 1024,
                'cached_mb': cached / 1024,
                'available_mb': (free + buffers + cached) / 1024
            }
        except:
            memory_info = {
                'total_mb': 0,
                'free_mb': 0,
                'buffers_mb': 0,
                'cached_mb': 0,
                'available_mb': 0
            }
        
        # Tárhely információ
        try:
            df_output = os.popen('df -k /').read()
            lines = df_output.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    total = int(parts[1]) * 1024
                    used = int(parts[2]) * 1024
                    free = int(parts[3]) * 1024
                    
                    disk_info = {
                        'total_gb': total / (1024**3),
                        'used_gb': used / (1024**3),
                        'free_gb': free / (1024**3),
                        'percent': (used / total) * 100 if total > 0 else 0
                    }
                else:
                    disk_info = {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}
            else:
                disk_info = {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}
        except:
            disk_info = {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'percent': 0}
        
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
            'cpu_temp': cpu_temp
        }
        
        logger.info(f"CPU: {cpu_info['cpu_count']} mag, "
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
        
        # 500x500 mátrix szorzás (kisebb méret az RPI4-hez)
        size = 500
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
        limit = 50000  # Kisebb limit az RPI4-hez
        
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
        
        # 10MB tömb létrehozása (kisebb méret az RPI4-hez)
        # Javítás: int() hozzáadva a size-hoz, hogy egész számot kapjunk
        size = int(2.5 * 1024 * 1024)  # 2.5 millió elem (kb. 10MB)
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
        
        iterations = 50  # Kevesebb iteráció az RPI4-hez
        # Javítás: int() hozzáadva az alloc_size-hoz, hogy egész számot kapjunk
        alloc_size = int(0.5 * 1024 * 1024)  # 0.5MB (kisebb méret az RPI4-hez)
        
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
        
        # 50MB adatok írása (kisebb méret az RPI4-hez)
        size_mb = 50
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
        
        try:
            import requests
            
            # 5MB teszt fájl letöltése (kisebb méret az RPI4-hez)
            url = "https://speed.hetzner.de/5MB.bin"
            
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
        except ImportError:
            logger.error("A requests könyvtár nem érhető el")
            results['http_download'] = {
                'error': "A requests könyvtár nem érhető el"
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
            'apple.com'
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
        
        # Nagy DataFrame létrehozása (kisebb méret az RPI4-hez)
        rows = 50000
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
        
        # Idősor adatok létrehozása (kisebb méret az RPI4-hez)
        periods = 5000
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
                try:
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
                except:
                    cpu_percent = 0
                
                # Memória használat
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
                    memory_percent = (used / total) * 100 if total > 0 else 0
                    memory_used_mb = used / 1024
                except:
                    memory_percent = 0
                    memory_used_mb = 0
                
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
                    'memory_percent': memory_percent,
                    'memory_used_mb': memory_used_mb,
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

# Gyors teszt opció hozzáadása
def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='RPI4 teljesítmény teszt')
    parser.add_argument('--quick-test', action='store_true', help='Gyors teszt futtatása')
    return parser.parse_args()

# Teszt futtatása
if __name__ == '__main__':
    args = parse_args()
    
    # Gyors teszt esetén csak a CPU tesztet futtatjuk
    if args.quick_test:
        logger.info("Gyors teszt mód")
        benchmark = RPI4Benchmark()
        benchmark.collect_system_info()
        benchmark.test_cpu_performance()
        benchmark.save_results()
    else:
        benchmark = RPI4Benchmark()
        results = benchmark.run_all_tests()
    
    # Eredmények kiírása
    print("\n===== Benchmark eredmények =====")
    
    if 'cpu_performance' in benchmark.results:
        cpu_perf = benchmark.results['cpu_performance']
        print("\nCPU teljesítmény:")
        if 'matrix_multiplication' in cpu_perf:
            print(f"  Mátrix szorzás: {cpu_perf['matrix_multiplication']['time']:.2f} másodperc")
        if 'prime_search' in cpu_perf:
            print(f"  Prímszám keresés: {cpu_perf['prime_search']['time']:.2f} másodperc")
    
    if 'memory_performance' in benchmark.results:
        mem_perf = benchmark.results['memory_performance']
        print("\nMemória teljesítmény:")
        if 'array_operations' in mem_perf:
            print(f"  Tömb műveletek: {mem_perf['array_operations']['time']:.2f} másodperc")
            print(f"  Tömb méret: {mem_perf['array_operations']['size_mb']:.2f}MB")
        if 'memory_allocation' in mem_perf:
            print(f"  Memória allokáció: {mem_perf['memory_allocation']['time']:.2f} másodperc")
    
    if 'storage_performance' in benchmark.results:
        storage_perf = benchmark.results['storage_performance']
        print("\nTárhely teljesítmény:")
        if 'file_write' in storage_perf:
            print(f"  Fájl írás: {storage_perf['file_write']['time']:.2f} másodperc")
            print(f"  Írási sebesség: {storage_perf['file_write']['mb_per_second']:.2f}MB/s")
        if 'file_read' in storage_perf:
            print(f"  Fájl olvasás: {storage_perf['file_read']['time']:.2f} másodperc")
            print(f"  Olvasási sebesség: {storage_perf['file_read']['mb_per_second']:.2f}MB/s")
    
    if 'network_performance' in benchmark.results:
        net_perf = benchmark.results['network_performance']
        print("\nHálózati teljesítmény:")
        if 'http_download' in net_perf and 'error' not in net_perf['http_download']:
            print(f"  HTTP letöltés: {net_perf['http_download']['time']:.2f} másodperc")
            print(f"  Letöltési sebesség: {net_perf['http_download']['mb_per_second']:.2f}MB/s")
        if 'dns_resolution' in net_perf:
            print(f"  DNS feloldás: {net_perf['dns_resolution']['time']:.2f} másodperc")
            print(f"  Átlagos DNS feloldási idő: {net_perf['dns_resolution']['avg_time_ms']:.2f}ms")
    
    if 'data_processing' in benchmark.results:
        data_perf = benchmark.results['data_processing']
        print("\nAdatfeldolgozás teljesítmény:")
        if 'pandas_operations' in data_perf:
            print(f"  Pandas műveletek: {data_perf['pandas_operations']['time']:.2f} másodperc")
        if 'timeseries_operations' in data_perf:
            print(f"  Idősor műveletek: {data_perf['timeseries_operations']['time']:.2f} másodperc")
    
    print(f"\nRészletes eredmények és grafikonok: {benchmark.output_dir}")
