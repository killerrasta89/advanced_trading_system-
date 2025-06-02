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
        try:
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
        except Exception as e:
            logger.error(f"Hiba a tárhely használat lekérdezése során: {e}")
            return {
                'total_gb': 0,
                'used_gb': 0,
                'free_gb': 0,
                'percent': 0,
                'data_mb': 0,
                'log_mb': 0
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
    import threading
    
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
