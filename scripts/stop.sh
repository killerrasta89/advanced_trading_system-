#!/bin/bash

# Advanced Trading System leállítási script
# Raspberry Pi 4 optimalizált

# Könyvtár beállítása
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Naplózás beállítása
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/shutdown_$(date +%Y%m%d_%H%M%S).log"

# Függvény a naplózáshoz
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" | tee -a "$LOG_FILE"
}

# Rendszer leállítása
log "===== Advanced Trading System leállítása ====="

# Trading Engine leállítása
if [ -f "$PROJECT_DIR/trading_engine.pid" ]; then
    TRADING_ENGINE_PID=$(cat "$PROJECT_DIR/trading_engine.pid")
    if ps -p $TRADING_ENGINE_PID > /dev/null; then
        log "Trading Engine leállítása (PID: $TRADING_ENGINE_PID)..."
        kill $TRADING_ENGINE_PID
        sleep 2
        
        # Ellenőrzés, hogy leállt-e
        if ps -p $TRADING_ENGINE_PID > /dev/null; then
            log "Trading Engine még fut, kényszerített leállítás..."
            kill -9 $TRADING_ENGINE_PID
            sleep 1
        fi
        
        if ps -p $TRADING_ENGINE_PID > /dev/null; then
            log "HIBA: Trading Engine nem állt le!"
        else
            log "Trading Engine sikeresen leállt"
        fi
    else
        log "Trading Engine már nem fut"
    fi
    rm -f "$PROJECT_DIR/trading_engine.pid"
else
    log "Trading Engine PID fájl nem található"
fi

# Webes felület leállítása
if [ -f "$PROJECT_DIR/web_interface.pid" ]; then
    WEB_INTERFACE_PID=$(cat "$PROJECT_DIR/web_interface.pid")
    if ps -p $WEB_INTERFACE_PID > /dev/null; then
        log "Webes felület leállítása (PID: $WEB_INTERFACE_PID)..."
        kill $WEB_INTERFACE_PID
        sleep 2
        
        # Ellenőrzés, hogy leállt-e
        if ps -p $WEB_INTERFACE_PID > /dev/null; then
            log "Webes felület még fut, kényszerített leállítás..."
            kill -9 $WEB_INTERFACE_PID
            sleep 1
        fi
        
        if ps -p $WEB_INTERFACE_PID > /dev/null; then
            log "HIBA: Webes felület nem állt le!"
        else
            log "Webes felület sikeresen leállt"
        fi
    else
        log "Webes felület már nem fut"
    fi
    rm -f "$PROJECT_DIR/web_interface.pid"
else
    log "Webes felület PID fájl nem található"
fi

# Egyéb folyamatok ellenőrzése és leállítása
log "Egyéb kapcsolódó folyamatok ellenőrzése..."
PYTHON_PROCESSES=$(ps aux | grep "python.*advanced_trading_system" | grep -v grep | awk '{print $2}')
if [ -n "$PYTHON_PROCESSES" ]; then
    log "További Python folyamatok leállítása: $PYTHON_PROCESSES"
    for pid in $PYTHON_PROCESSES; do
        kill $pid 2>/dev/null
    done
    sleep 2
    
    # Kényszerített leállítás, ha szükséges
    REMAINING_PROCESSES=$(ps aux | grep "python.*advanced_trading_system" | grep -v grep | awk '{print $2}')
    if [ -n "$REMAINING_PROCESSES" ]; then
        log "Kényszerített leállítás: $REMAINING_PROCESSES"
        for pid in $REMAINING_PROCESSES; do
            kill -9 $pid 2>/dev/null
        done
    fi
fi

log "===== Advanced Trading System leállítása befejezve ====="

# Kilépés
exit 0
