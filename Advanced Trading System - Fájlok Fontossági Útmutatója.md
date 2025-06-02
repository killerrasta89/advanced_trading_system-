# Advanced Trading System - Fájlok Fontossági Útmutatója

## Alapvető (Kötelező) Fájlok

Ezek a fájlok elengedhetetlenek a rendszer alapvető működéséhez. Ezek nélkül a rendszer nem fog elindulni vagy súlyos hibákat fog produkálni.

### Fő Alkalmazás
- `main.py` - A rendszer belépési pontja
- `requirements.txt` - Függőségek listája

### Konfiguráció
- `config/settings.py` - Alap konfigurációs beállítások
- `config/db_config.py` - Adatbázis konfigurációk

### Core Komponensek
- `core/trading_engine.py` - Fő trading motor
- `core/order_manager.py` - Order kezelés
- `core/portfolio_manager.py` - Portfólió kezelés
- `core/market_data_manager.py` - Piaci adatok kezelése
- `core/strategy_manager.py` - Stratégia koordinátor
- `core/execution_engine.py` - Végrehajtási motor

### Adatbázis
- `database/models.py` - Adatbázis modellek

### Web Felület
- `web_interface/app.py` - Flask alkalmazás
- `src/routes/main.py` - Fő útvonalak
- `src/routes/api.py` - API útvonalak
- `web_interface/templates/base.html` - Alap HTML sablon

### Segédprogramok
- `utils/logger.py` - Naplózás
- `utils/memory_manager.py` - Memória kezelés (RPI4)
- `utils/cpu_optimizer.py` - CPU optimalizálás (RPI4)

### Scriptek
- `scripts/start.sh` - Indító script
- `scripts/stop.sh` - Leállító script

## Fontos (Ajánlott) Fájlok

Ezek a fájlok fontosak a rendszer teljes funkcionalitásához, de a rendszer alapszinten működni fog nélkülük is. Hiányuk esetén bizonyos funkciók nem lesznek elérhetők.

### Konfiguráció
- `config/strategy_config.py` - Stratégia beállítások
- `config/exchange_config.py` - Exchange specifikus beállítások
- `config/risk_config.py` - Kockázatkezelési beállítások
- `config/notification_config.py` - Értesítési beállítások

### Stratégiák
- `strategies/base_strategy.py` - Alap stratégia osztály
- `strategies/grid_trading.py` - Grid trading stratégia
- `strategies/dca_strategy.py` - Dollar Cost Averaging stratégia
- `strategies/momentum_strategy.py` - Momentum stratégia
- `strategies/mean_reversion.py` - Mean Reversion stratégia
- `strategies/arbitrage_strategy.py` - Arbitrázs stratégia

### Web API
- `web_interface/api/portfolio_api.py` - Portfólió API
- `web_interface/api/trades_api.py` - Kereskedések API
- `web_interface/api/strategies_api.py` - Stratégiák API
- `web_interface/api/settings_api.py` - Beállítások API
- `web_interface/api/market_data_api.py` - Piaci adatok API

### Exchanges
- `exchanges/exchange_factory.py` - Exchange factory
- `exchanges/binance_connector.py` - Binance connector
- `exchanges/kraken_connector.py` - Kraken connector
- `exchanges/coinbase_connector.py` - Coinbase connector

## Opcionális (Kiterjesztett) Fájlok

Ezek a fájlok opcionálisak, és a rendszer kiterjesztett funkcióit biztosítják. Hiányuk esetén a rendszer továbbra is működni fog, de bizonyos speciális funkciók nem lesznek elérhetők.

### AI/ML Modellek
- `ai_models/price_predictor.py` - Árfolyam előrejelzés
- `ai_models/sentiment_analyzer.py` - Hangulat elemzés
- `ai_models/pattern_recognition.py` - Mintázat felismerés
- `ai_models/risk_assessor.py` - Kockázat értékelés
- `ai_models/market_regime_detector.py` - Piaci rezsim detektálás

### Kockázatkezelés
- `risk_management/position_sizer.py` - Pozíció méretezés
- `risk_management/risk_calculator.py` - Kockázat számítás
- `risk_management/drawdown_manager.py` - Drawdown kezelés
- `risk_management/volatility_manager.py` - Volatilitás kezelés
- `risk_management/correlation_analyzer.py` - Korreláció elemzés

### Indikátorok
- `indicators/technical_indicators.py` - Technikai indikátorok
- `indicators/custom_indicators.py` - Egyedi indikátorok
- `indicators/volume_indicators.py` - Volumen indikátorok
- `indicators/market_structure.py` - Piaci struktúra

### Backtesting
- `backtesting/backtest_engine.py` - Backtest motor
- `backtesting/performance_analyzer.py` - Teljesítmény elemzés
- `backtesting/monte_carlo.py` - Monte Carlo szimuláció
- `backtesting/walk_forward_analysis.py` - Walk-forward analízis

### Monitorozás
- `monitoring/performance_monitor.py` - Teljesítmény monitorozás
- `monitoring/system_monitor.py` - Rendszer monitorozás
- `monitoring/alert_manager.py` - Riasztás kezelés
- `monitoring/health_checker.py` - Egészség ellenőrzés

### Értesítések
- `notifications/telegram_bot.py` - Telegram bot
- `notifications/discord_bot.py` - Discord bot
- `notifications/email_notifier.py` - Email értesítések
- `notifications/webhook_notifier.py` - Webhook értesítések

### Adatbázis
- `database/migrations.py` - Migrációk
- `database/price_data_handler.py` - Árfolyam adat kezelés
- `database/trade_data_handler.py` - Kereskedési adat kezelés

### Docker
- `docker/Dockerfile` - Dockerfile
- `docker/docker-compose.yml` - Docker Compose
- `docker/requirements.txt` - Docker függőségek

### Dokumentáció
- `docs/api_documentation.md` - API dokumentáció
- `docs/user_guide.md` - Felhasználói útmutató
- `docs/deployment_guide.md` - Telepítési útmutató
- `docs/validation_report.md` - Validációs jelentés

## Hiányzó Fájlok Kezelése

Ha hiányzik egy fájl, a következő lehetőségek közül választhat:

1. **Létrehozhatja minimális implementációval**: Minden hiányzó fájlt létrehozhat egy alapvető osztály vagy függvény definícióval, amit később bővíthet.

2. **Fokozatosan implementálhatja**: A rendszer használata közben, ahogy szükség van rájuk, implementálhatja a hiányzó funkciókat.

3. **Módosíthatja a függőségeket**: A main.py és más fájlokban módosíthatja az importokat, hogy ne hivatkozzanak a hiányzó fájlokra.

### Példa minimális implementációra:

```python
"""
Minimális implementáció - [Fájlnév]
"""

class [OsztályNév]:
    """
    [Osztály leírása] - Minimális implementáció
    """
    
    def __init__(self):
        """
        Inicializálás
        """
        print("[OsztályNév] inicializálva - Minimális implementáció")
    
    def [Metódus](self, *args, **kwargs):
        """
        [Metódus leírása] - Minimális implementáció
        """
        print(f"[OsztályNév].[Metódus] meghívva - Minimális implementáció")
        return None
```

## Rendszer Indítása Hiányzó Fájlokkal

Ha hiányzó fájlokkal szeretné indítani a rendszert, a következő lépéseket kövesse:

1. Győződjön meg róla, hogy az összes **Alapvető (Kötelező)** fájl létezik.
2. Hozza létre a hiányzó **Fontos (Ajánlott)** fájlokat minimális implementációval.
3. Az **Opcionális (Kiterjesztett)** fájlokat fokozatosan implementálhatja, ahogy szükség van rájuk.

A rendszer indításához használja a `scripts/start.sh` scriptet, vagy közvetlenül futtassa a `main.py` fájlt:

```bash
python main.py
```

Ha hibát tapasztal, ellenőrizze a naplófájlokat a `logs/` könyvtárban, és hozza létre a hiányzó fájlokat minimális implementációval.
