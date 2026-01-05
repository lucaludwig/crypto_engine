# 🤖 CADVI Auto-Trader

**Automated Cryptocurrency Trading Bot** with professional risk management

---

## ✨ Features

✅ **Fully Automated Trading**
- Scans 1000+ coins every 30 minutes
- Automatically buys top opportunities (Score 70+)
- Sets Stop-Loss (-10%) and Take-Profit (+20%) automatically
- Re-invests profits automatically

✅ **Professional Risk Management**
- Max 20% per position
- Max 80% total exposure
- -10% daily loss limit (auto-shutdown)

✅ **24/7 Cloud Deployment Ready**
- Docker containerized
- One-command deployment

---

## 📁 Project Structure

```
cadvi/
├── auto_trader.py          # Main trading bot
├── monitor.py              # Bot status monitor
├── quick_trade.py          # Manual quick trading
├── pro_advisor.py          # Advanced advisor
├── api/                    # Core trading logic
│   ├── binance_client.py   # Binance integration
│   ├── position_monitor.py # Position management
│   ├── learning_engine.py  # AI learning system
│   └── ...
├── scripts/                # Utility scripts
│   ├── check_*.py          # Status check tools
│   ├── analyze_*.py        # Analysis tools
│   └── ...
├── docs/                   # Documentation
│   ├── CLOUD_DEPLOYMENT.md
│   ├── ORACLE_CLOUD_SETUP.md
│   └── ...
└── deployment/             # Deployment scripts
    └── deploy_*.sh
```

---

## 🚀 Quick Start

### Local Trading
```bash
# Monitor status
python monitor.py

# Check orders
python scripts/check_orders.py
```

### Cloud Deployment
See [docs/CLOUD_DEPLOYMENT.md](docs/CLOUD_DEPLOYMENT.md)

---

## 📊 Your Bot is Running

**Status:** Check with `python monitor.py`

**Stop Bot:** `kill 27881` (or check process with `ps aux | grep auto_trader`)

**View Logs:** `tail -f auto_trader.log`

---

⚠️ **High Risk - Not Financial Advice - Trade at Your Own Risk**
