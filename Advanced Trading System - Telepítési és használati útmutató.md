# Advanced Trading System - Telepítési és használati útmutató

## Rendszerkövetelmények
- Raspberry Pi 4 (legalább 2GB RAM)
- Raspbian OS (Buster vagy újabb)
- Python 3.7+
- Internet kapcsolat

## Telepítés

### 1. Rendszer letöltése
```bash
git clone https://github.com/yourusername/advanced_trading_system.git
cd advanced_trading_system
```

### 2. Függőségek telepítése
```bash
# Virtuális környezet létrehozása
python3 -m venv venv
source venv/bin/activate

# Függőségek telepítése
pip install -r requirements.txt
```

### 3. Konfigurálás
1. Másolja a `config/settings.py.example` fájlt `config/settings.py` néven
2. Szerkessze a beállításokat az Ön igényei szerint
3. Adja meg az API kulcsokat a `config/exchange_config.py` fájlban

### 4. Rendszer optimalizálása
```bash
# Optimalizációs script futtatása
bash scripts/optimize_rpi4_fixed.sh
```

### 5. Automatikus indítás beállítása (opcionális)
```bash
# Automatikus indítás beállítása
bash scripts/setup_autostart.sh
```

## Használat

### Rendszer indítása
```bash
bash scripts/start.sh
```

### Webes felület elérése
A webes felület a következő címen érhető el:
```
http://az-ön-raspberry-pi-ip-címe:5000
```

### Rendszer leállítása
```bash
bash scripts/stop.sh
```

## Funkciók

### Kereskedési stratégiák
- **Grid Trading**: Meghatározott ársávokban automatikus vételi és eladási megbízások
- **DCA (Dollar Cost Averaging)**: Rendszeres időközönként történő vásárlás
- **Momentum**: Trendkövető stratégia
- **Mean Reversion**: Átlaghoz visszatérő stratégia
- **Arbitrage**: Tőzsdék közötti árkülönbségek kihasználása
- **Sentiment**: Piaci hangulat alapú kereskedés

### Kockázatkezelés
- Pozícióméretezés volatilitás alapján
- Drawdown kezelés
- Korreláció elemzés
- Stop-loss és take-profit beállítások

### Monitoring
- Teljesítménymutatók valós időben
- Portfólió értékelés
- Stratégia összehasonlítás
- Rendszer egészség monitorozás

## Hibaelhárítás

### Naplófájlok
A naplófájlok a `logs` könyvtárban találhatók:
- `trading_engine.log`: Kereskedési motor naplója
- `web_interface.log`: Webes felület naplója
- `optimize_*.log`: Optimalizációs folyamat naplója

### Gyakori problémák

#### A rendszer nem indul el
- Ellenőrizze, hogy minden függőség telepítve van-e
- Ellenőrizze a naplófájlokat a részletes hibaüzenetekért
- Ellenőrizze, hogy a konfigurációs fájlok helyesen vannak-e beállítva

#### Magas memóriahasználat
- Csökkentse az egyidejűleg futó stratégiák számát
- Állítsa be a memória limitet a `config/settings.py` fájlban

#### Lassú teljesítmény
- Csökkentse az adatgyűjtés gyakoriságát
- Használja a `scripts/optimize_rpi4_fixed.sh` scriptet a rendszer optimalizálásához

## Támogatás
Ha kérdése vagy problémája van, kérjük, nyisson egy issue-t a GitHub repository-ban.

## Licenc
Ez a projekt MIT licenc alatt áll. Részletekért lásd a LICENSE fájlt.
