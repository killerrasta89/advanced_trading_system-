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
