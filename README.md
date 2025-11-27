# Crypto Market Advisor (CADVI)

Ein Python-basiertes CLI-Tool zur Identifizierung von High-Risk/High-Return Kryptowährungen für die nächsten 24 Stunden.

## Features

- **Echtzeitdaten** von CoinMarketCap API
- **Multi-Faktor-Analyse**:
  - Volatilitätsanalyse (1h, 24h, 7d Preisbewegungen)
  - Market Cap Risikobewertung
  - Handelsvolumen und Aktivität
  - Momentum-Indikatoren
- **Intelligentes Scoring-System** mit gewichteten Faktoren
- **Farbcodierte CLI-Ausgabe** für bessere Lesbarkeit
- **Top 5 Empfehlungen** mit detaillierten Metriken

## Installation

1. **Repository klonen** (falls noch nicht geschehen)

2. **Python Virtual Environment erstellen**:
```bash
python3 -m venv venv
source venv/bin/activate  # Auf macOS/Linux
# oder
venv\Scripts\activate  # Auf Windows
```

3. **Dependencies installieren**:
```bash
pip install -r requirements.txt
```

4. **CoinMarketCap API Key einrichten**:
   - Gehe zu [CoinMarketCap API](https://pro.coinmarketcap.com/signup)
   - Erstelle einen kostenlosen Account
   - Kopiere deinen API Key
   - Erstelle eine `.env` Datei:
   ```bash
   cp .env.example .env
   ```
   - Füge deinen API Key in die `.env` Datei ein:
   ```
   CMC_API_KEY=dein_api_key_hier
   ```

## Verwendung

### Basic Usage

```bash
python crypto_advisor.py
```

Dies analysiert die Top 200 Coins und zeigt die Top 5 High-Risk/High-Return Empfehlungen.

### Erweiterte Optionen

```bash
# Mehr Coins analysieren (z.B. Top 500)
python crypto_advisor.py --limit 500

# Top 10 Empfehlungen anzeigen
python crypto_advisor.py --top 10

# Kombiniert
python crypto_advisor.py --limit 500 --top 10
```

### Hilfe anzeigen

```bash
python crypto_advisor.py --help
```

## Wie funktioniert der Analyzer?

### Scoring-Algorithmus

Das Tool berechnet einen **Composite Score** basierend auf vier Hauptfaktoren:

1. **Volatilitätsscore (25%)**: Misst die Preisschwankungen über verschiedene Zeiträume
2. **Market Cap Risikoscore (30%)**: Kleinere Market Caps = höheres Risiko/höhere potenzielle Returns
3. **Volumen-Aktivitätsscore (25%)**: Verhältnis von Handelsvolumen zu Market Cap
4. **Momentumscore (20%)**: Positive Preistrends und Aufwärtsbewegungen

### Market Cap Risikokategorien

- **Micro Cap** (< $50M): EXTREME RISK - Höchstes Potenzial
- **Small Cap** ($50M - $250M): HIGH RISK - Hohes Potenzial
- **Mid Cap** ($250M - $2B): MEDIUM RISK - Moderates Potenzial
- **Large Cap** (> $2B): LOW RISK - Geringeres Potenzial

### Ausschlusskriterien

Das Tool filtert automatisch heraus:
- Stablecoins (USDT, USDC, BUSD, DAI, etc.)
- Coins ohne Handelsvolumen
- Coins mit extrem niedriger Market Cap (< $100K)

## Beispiel-Ausgabe

```
================================================================================
CRYPTO MARKET ADVISOR - High Risk / High Return Analysis
Disclaimer: This is for educational purposes only. Not financial advice!
================================================================================

Fetching latest market data from CoinMarketCap...
Received data for 200 cryptocurrencies
Analyzing high-risk/high-return opportunities...

TOP 5 HIGH RISK / HIGH RETURN COINS FOR NEXT 24H:

#1 ExampleCoin (EXC)
--------------------------------------------------------------------------------
Price                 $0.234567
Market Cap            $45.2M
24h Volume            $12.5M
Composite Score       87.45/100

  Price Changes:
  1 Hour              +5.23%
  24 Hours            +18.45%
  7 Days              +42.10%

  Score Breakdown:
  Volatility          75.3/100
  Risk Level          100.0/100
  Volume Activity     85.0/100
  Momentum            78.5/100

  Risk Assessment: EXTREME RISK

  Key Factors:
    ✓ Strong positive momentum
    ✓ High trading activity
    ✓ High volatility (potential for big moves)
    ! Small market cap (higher risk/reward)
    ✓ Strong 24h performance (+18.5%)
```

## Wichtige Hinweise

### Disclaimer

- Dieses Tool ist **NUR für Bildungszwecke**
- Dies ist **KEINE Finanzberatung**
- Investiere nur, was du dir leisten kannst zu verlieren
- High-Risk Coins können genauso schnell fallen wie sie steigen
- **DYOR** (Do Your Own Research) ist essentiell

### Limitierungen

- **CoinMarketCap Free Tier**: Limitiert auf 333 API Calls/Tag
- **Keine Garantien**: Vergangene Performance ist kein Indikator für zukünftige Ergebnisse
- **Marktvolatilität**: Crypto-Märkte sind extrem volatil und unvorhersehbar
- **Technische Analyse**: Berücksichtigt keine Fundamentaldaten, News oder Events

## Technische Details

### Projektstruktur

```
cadvi/
├── crypto_advisor.py   # Hauptprogramm mit CLI Interface
├── cmc_client.py       # CoinMarketCap API Client
├── analyzer.py         # Analyse- und Scoring-Engine
├── requirements.txt    # Python Dependencies
├── .env.example        # Beispiel für Environment Variables
├── .env               # Deine API Keys (nicht im Git!)
└── README.md          # Diese Datei
```

### Dependencies

- **requests**: HTTP-Requests für API-Calls
- **python-dotenv**: Environment Variable Management
- **pandas**: Datenanalyse und -manipulation
- **tabulate**: Formatierte Tabellenausgabe
- **colorama**: Farbige Terminal-Ausgabe

## Troubleshooting

### "CoinMarketCap API key is required"
- Stelle sicher, dass die `.env` Datei existiert
- Überprüfe, dass `CMC_API_KEY` korrekt gesetzt ist
- Keine Leerzeichen um das `=` Zeichen

### "Failed to fetch data"
- Überprüfe deine Internetverbindung
- Stelle sicher, dass dein API Key gültig ist
- Überprüfe, ob du dein API Call Limit erreicht hast (333/Tag für Free Tier)

### Keine Empfehlungen / Leere Ausgabe
- Erhöhe das `--limit` (mehr Coins analysieren)
- Überprüfe die API-Response auf Fehler
- Stelle sicher, dass die CoinMarketCap API erreichbar ist

## Weiterentwicklung

Mögliche Erweiterungen:
- Machine Learning für bessere Vorhersagen
- Integration weiterer APIs (TradingView, Binance, etc.)
- Historische Backtesting-Funktionalität
- Web Dashboard mit Live-Updates
- Benachrichtigungen bei bestimmten Bedingungen
- Social Media Sentiment Analysis
- On-Chain Metriken Integration

## Lizenz

MIT License - Frei verwendbar für persönliche und kommerzielle Zwecke.

## Support

Bei Fragen oder Problemen, bitte ein Issue erstellen oder den Code direkt anpassen.

---

**Remember: Crypto is volatile. Trade responsibly!**
