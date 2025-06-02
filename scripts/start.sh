#!/bin/bash

# Advanced Trading System indítási script
# Raspberry Pi 4 optimalizált

# Könyvtár beállítása
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Naplózás beállítása
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/startup_$(date +%Y%m%d_%H%M%S).log"

# Függvény a naplózáshoz
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" | tee -a "$LOG_FILE"
}

# Rendszer információk kiírása
log "===== Advanced Trading System indítása ====="
log "Projekt könyvtár: $PROJECT_DIR"
log "Kernel verzió: $(uname -r)"
log "CPU információ: $(lscpu | grep "Model name" | sed 's/Model name:[[:space:]]*//')"
log "Memória: $(free -h | grep Mem | awk '{print $2}')"
log "Tárhely: $(df -h / | grep / | awk '{print $2}')"

# Virtuális környezet aktiválása
if [ -d "$PROJECT_DIR/venv" ]; then
    log "Virtuális környezet aktiválása..."
    source "$PROJECT_DIR/venv/bin/activate"
else
    log "HIBA: Virtuális környezet nem található!"
    exit 1
fi

# Függőségek ellenőrzése
log "Függőségek ellenőrzése..."
pip list > "$LOG_DIR/pip_list.txt"

# Adatkönyvtárak létrehozása
log "Adatkönyvtárak létrehozása..."
mkdir -p "$PROJECT_DIR/data/market_data"
mkdir -p "$PROJECT_DIR/data/backtest_results"
mkdir -p "$PROJECT_DIR/data/models"

# Rendszer erőforrás használat optimalizálása
log "Rendszer erőforrás használat optimalizálása..."

# Alacsony prioritás beállítása
renice 10 $$ > /dev/null
log "Folyamat prioritás beállítva: $(nice)"

# Memória limit beállítása (1.5GB)
ulimit -v 1572864
log "Memória limit beállítva: $(ulimit -v) KB"

# Adatbázis inicializálása
log "Adatbázis inicializálása..."
python -m advanced_trading_system.database.migrations

# Trading Engine indítása
log "Trading Engine indítása..."
nohup python -m advanced_trading_system.core.trading_engine > "$LOG_DIR/trading_engine.log" 2>&1 &
TRADING_ENGINE_PID=$!
log "Trading Engine elindítva (PID: $TRADING_ENGINE_PID)"

# Webes felület indítása
log "Webes felület indítása..."
nohup python -m advanced_trading_system.web_interface.app > "$LOG_DIR/web_interface.log" 2>&1 &
WEB_INTERFACE_PID=$!
log "Webes felület elindítva (PID: $WEB_INTERFACE_PID)"

# PID-ek mentése
echo "$TRADING_ENGINE_PID" > "$PROJECT_DIR/trading_engine.pid"
echo "$WEB_INTERFACE_PID" > "$PROJECT_DIR/web_interface.pid"

# Várakozás a szolgáltatások elindulására
log "Várakozás a szolgáltatások elindulására..."
sleep 5

# Ellenőrzés, hogy a szolgáltatások futnak-e
if ps -p $TRADING_ENGINE_PID > /dev/null; then
    log "Trading Engine sikeresen elindult"
else
    log "HIBA: Trading Engine nem indult el!"
fi

if ps -p $WEB_INTERFACE_PID > /dev/null; then
    log "Webes felület sikeresen elindult"
else
    log "HIBA: Webes felület nem indult el!"
fi

# Webes felület URL kiírása
log "Webes felület elérhető: http://localhost:5000"
log "===== Advanced Trading System indítása befejezve ====="

# Kilépés
exit 0
