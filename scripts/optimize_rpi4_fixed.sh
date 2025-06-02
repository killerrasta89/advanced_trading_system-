#!/bin/bash
# RPI4 Optimalizációs és Tesztelési Script - Javított verzió
# Advanced Trading System

# Könyvtár beállítása
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "===== Advanced Trading System - RPI4 Optimalizáció és Tesztelés ====="
echo "Kezdés: $(date)"
echo "Projekt könyvtár: $PROJECT_DIR"
echo

# Könyvtárak létrehozása, ha nem léteznek
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data"
mkdir -p "$PROJECT_DIR/config"
mkdir -p "$PROJECT_DIR/utils"
mkdir -p "$PROJECT_DIR/tests/performance_tests"

# Naplózás beállítása
LOG_FILE="$PROJECT_DIR/logs/optimize_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

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

# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/config/db_config.py" ]; then
    cat > "$PROJECT_DIR/config/db_config.py" << EOF
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
    echo "SQLite konfigurációs fájl létrehozva: $PROJECT_DIR/config/db_config.py"
else
    echo "SQLite konfigurációs fájl már létezik: $PROJECT_DIR/config/db_config.py"
fi

echo "SQLite optimalizálás kész."

echo "Memória kezelés optimalizálása..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/utils/memory_manager.py" ]; then
    echo "Memória kezelő fájl nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/utils/memory_manager.py"
else
    echo "Memória kezelő fájl megtalálva: $PROJECT_DIR/utils/memory_manager.py"
fi
echo "Memória kezelés optimalizálása kész."

echo "CPU optimalizálás..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/utils/cpu_optimizer.py" ]; then
    echo "CPU optimalizáló fájl nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/utils/cpu_optimizer.py"
else
    echo "CPU optimalizáló fájl megtalálva: $PROJECT_DIR/utils/cpu_optimizer.py"
fi
echo "CPU optimalizálás kész."

echo "Hálózati optimalizálás..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/utils/network_manager.py" ]; then
    echo "Hálózati kezelő fájl nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/utils/network_manager.py"
else
    echo "Hálózati kezelő fájl megtalálva: $PROJECT_DIR/utils/network_manager.py"
fi
echo "Hálózati optimalizálás kész."

echo "Tárhely optimalizálás..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/utils/storage_optimizer.py" ]; then
    echo "Tárhely optimalizáló fájl nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/utils/storage_optimizer.py"
else
    echo "Tárhely optimalizáló fájl megtalálva: $PROJECT_DIR/utils/storage_optimizer.py"
fi
echo "Tárhely optimalizálás kész."

echo "Teljesítmény tesztelés..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/tests/performance_tests/rpi4_benchmark.py" ]; then
    echo "Teljesítmény teszt fájl nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/tests/performance_tests/rpi4_benchmark.py"
else
    echo "Teljesítmény teszt fájl megtalálva: $PROJECT_DIR/tests/performance_tests/rpi4_benchmark.py"
fi
echo "Teljesítmény tesztelés kész."

echo "Rendszer indítási script ellenőrzése..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/scripts/start.sh" ]; then
    echo "Indítási script nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/scripts/start.sh"
else
    echo "Indítási script megtalálva: $PROJECT_DIR/scripts/start.sh"
    # Futtatási jogosultság ellenőrzése
    if [ ! -x "$PROJECT_DIR/scripts/start.sh" ]; then
        chmod +x "$PROJECT_DIR/scripts/start.sh"
        echo "Futtatási jogosultság beállítva."
    fi
fi
echo "Rendszer indítási script ellenőrzése kész."

echo "Rendszer leállítási script ellenőrzése..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/scripts/stop.sh" ]; then
    echo "Leállítási script nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/scripts/stop.sh"
else
    echo "Leállítási script megtalálva: $PROJECT_DIR/scripts/stop.sh"
    # Futtatási jogosultság ellenőrzése
    if [ ! -x "$PROJECT_DIR/scripts/stop.sh" ]; then
        chmod +x "$PROJECT_DIR/scripts/stop.sh"
        echo "Futtatási jogosultság beállítva."
    fi
fi
echo "Rendszer leállítási script ellenőrzése kész."

echo "Automatikus indítás script ellenőrzése..."
# Ellenőrizzük, hogy a fájl létezik-e már
if [ ! -f "$PROJECT_DIR/scripts/setup_autostart.sh" ]; then
    echo "Automatikus indítás script nem található, létrehozás helyett kihagyva."
    echo "Elvárt útvonal: $PROJECT_DIR/scripts/setup_autostart.sh"
else
    echo "Automatikus indítás script megtalálva: $PROJECT_DIR/scripts/setup_autostart.sh"
    # Futtatási jogosultság ellenőrzése
    if [ ! -x "$PROJECT_DIR/scripts/setup_autostart.sh" ]; then
        chmod +x "$PROJECT_DIR/scripts/setup_autostart.sh"
        echo "Futtatási jogosultság beállítva."
    fi
fi
echo "Automatikus indítás script ellenőrzése kész."

echo "Teljesítmény tesztelés futtatása..."
if [ -f "$PROJECT_DIR/tests/performance_tests/rpi4_benchmark.py" ]; then
    cd "$PROJECT_DIR/tests/performance_tests"
    # Csak rövid tesztet futtatunk, hogy ne tartson sokáig
    python3 rpi4_benchmark.py --quick-test
    cd "$PROJECT_DIR"
else
    echo "Teljesítmény teszt fájl nem található, tesztelés kihagyva."
fi
echo "Teljesítmény tesztelés befejezve."

echo "===== Advanced Trading System - RPI4 Optimalizáció és Tesztelés Befejezve ====="
echo "Befejezés: $(date)"
echo "Napló fájl: $LOG_FILE"

# Visszatérés az eredeti könyvtárba
cd - > /dev/null
