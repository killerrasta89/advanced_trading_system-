#!/bin/bash

# Advanced Trading System automatikus indítás beállítása
# Raspberry Pi 4 optimalizált

# Könyvtár beállítása
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Crontab bejegyzés létrehozása
CRONTAB_LINE="@reboot $PROJECT_DIR/scripts/start.sh >> $PROJECT_DIR/logs/autostart.log 2>&1"

# Ellenőrzés, hogy a bejegyzés már létezik-e
if crontab -l 2>/dev/null | grep -q "$PROJECT_DIR/scripts/start.sh"; then
    echo "Az automatikus indítás már be van állítva."
else
    # Új crontab bejegyzés hozzáadása
    (crontab -l 2>/dev/null; echo "$CRONTAB_LINE") | crontab -
    echo "Automatikus indítás beállítva."
fi

# Systemd service létrehozása (alternatív módszer)
SERVICE_FILE="/etc/systemd/system/advanced-trading-system.service"

echo "Systemd service fájl létrehozása: $SERVICE_FILE"
sudo tee "$SERVICE_FILE" > /dev/null << EOL
[Unit]
Description=Advanced Trading System
After=network.target

[Service]
Type=forking
User=$(whoami)
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/scripts/start.sh
ExecStop=$PROJECT_DIR/scripts/stop.sh
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
