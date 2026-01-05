# 🚀 Deployment Anleitung - CADVI Pro Web App

## Schritt 1: Backend auf Railway.app deployen (5 Minuten)

### 1.1 Account erstellen
1. Gehe zu [railway.app](https://railway.app)
2. Klicke "Login" → "Login with GitHub"
3. Authorisiere Railway

### 1.2 Neues Projekt erstellen
1. Klicke "+ New Project"
2. Wähle "Deploy from GitHub repo"
3. Wähle: `lucaludwig/crypto_engine`
4. Klicke "Deploy Now"

### 1.3 Backend konfigurieren
1. Gehe zu "Settings" (Zahnrad)
2. Root Directory: **`backend`**
3. Build Command: **`pip install -r requirements.txt`**
4. Start Command: **`gunicorn api:app`**

### 1.4 API Key hinzufügen
1. Gehe zu "Variables" Tab
2. Klicke "New Variable"
3. Name: **`CMC_API_KEY`**
4. Value: **Dein CoinMarketCap API Key**
5. Klicke "Add"

### 1.5 URL kopieren
1. Gehe zu "Settings"
2. Kopiere die "Public Domain" URL (z.B. `https://your-app.railway.app`)
3. **Diese URL brauchst du gleich!**

---

## Schritt 2: Frontend konfigurieren (2 Minuten)

### 2.1 API URL updaten
1. Öffne `docs/app.js` in einem Editor
2. Zeile 2: Ersetze `https://your-api-url.com` mit deiner Railway URL:
   ```javascript
   const API_URL = 'https://your-app.railway.app/api/analyze';
   ```
3. Speichern

### 2.2 Änderungen zu GitHub pushen
```bash
cd /Users/l.ludwig/Documents/Private/cadvi
git add docs/app.js
git commit -m "Update API URL for deployment"
git push
```

---

## Schritt 3: GitHub Pages aktivieren (3 Minuten)

### 3.1 Repository Settings öffnen
1. Gehe zu [github.com/lucaludwig/crypto_engine](https://github.com/lucaludwig/crypto_engine)
2. Klicke "Settings" (oben rechts)

### 3.2 Pages konfigurieren
1. Im linken Menü: "Pages"
2. Source: **Deploy from a branch**
3. Branch: **`main`**
4. Folder: **`/docs`**
5. Klicke "Save"

### 3.3 Warten auf Deployment
1. Nach 1-2 Minuten ist die Seite live
2. URL: **https://lucaludwig.github.io/crypto_engine/**
3. Diese URL kannst du teilen!

---

## ✅ Fertig! Deine Web App ist live!

**Frontend (GitHub Pages):**
- URL: https://lucaludwig.github.io/crypto_engine/
- Kostenlos, unbegrenzt

**Backend (Railway):**
- URL: https://your-app.railway.app
- Kostenlos: $5 Credits/Monat (reicht für ca. 50-100 Analysen/Tag)

---

## 🧪 Testen

1. Öffne https://lucaludwig.github.io/crypto_engine/
2. Klicke "Analyze Market Now"
3. Nach 10-30 Sekunden siehst du die Ergebnisse:
   - 10 Binance Spot Empfehlungen
   - 10 Binance Futures Empfehlungen
   - 10 Binance Web3 Wallet Empfehlungen

---

## 🔧 Troubleshooting

### Problem: "API error: Failed to fetch"

**Lösung:**
1. Prüfe ob Railway Backend läuft:
   - Öffne: `https://your-app.railway.app/api/health`
   - Sollte zeigen: `{"status": "ok"}`
2. Prüfe `docs/app.js` Zeile 2 - ist die URL korrekt?
3. Prüfe Railway Logs auf Fehler

### Problem: "API error: 500"

**Lösung:**
1. Gehe zu Railway Dashboard
2. Öffne dein Projekt → "Deployments"
3. Klicke auf den letzten Deployment
4. Schaue in die "Logs"
5. Häufig: CMC_API_KEY fehlt oder ist falsch

### Problem: GitHub Pages zeigt alte Version

**Lösung:**
1. Gehe zu GitHub → Settings → Pages
2. Warte 2-3 Minuten nach Push
3. Leere Browser Cache (Cmd+Shift+R auf Mac)

### Problem: CoinMarketCap API Limit erreicht

**Lösung:**
- Free Tier: 333 Calls/Tag
- 1 Analyse = 1 Call
- Warte bis nächster Tag oder upgrade Plan

---

## 💰 Kosten

### Railway.app
- **Free Tier**: $5 Credits/Monat
- **1 API Call** ≈ 5-10 Sekunden Rechenzeit
- **Geschätzt**: 50-100 Analysen/Tag kostenlos
- **Wenn überschritten**: $0.000231/GB-second

### CoinMarketCap API
- **Free Tier**: 333 Calls/Tag (ca. 10,000/Monat)
- **Völlig ausreichend** für persönlichen Gebrauch

### GitHub Pages
- **Kostenlos**: Unbegrenzt
- Perfekt für Static Websites

**Total: Kostenlos für persönlichen Gebrauch!**

---

## 🔄 Updates deployen

### Code ändern:
```bash
cd /Users/l.ludwig/Documents/Private/cadvi

# Änderungen machen...

git add .
git commit -m "Deine Änderung beschreiben"
git push
```

- **Backend**: Railway deployt automatisch neu (2-3 Minuten)
- **Frontend**: GitHub Pages updated automatisch (2-3 Minuten)

---

## 🎨 Anpassungen

### Farben ändern
Editiere `docs/style.css` Zeile 8:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Mehr Empfehlungen pro Kategorie
Editiere `docs/index.html` Zeile 37:
```html
<option value="15" selected>15</option>
```

### Standard Coins-Limit ändern
Editiere `docs/index.html` Zeile 31:
```html
<option value="2000" selected>2000</option>
```

---

## 📱 Teilen

**Deine Live-URL:**
```
https://lucaludwig.github.io/crypto_engine/
```

**QR Code erstellen:**
1. Gehe zu [qr-code-generator.com](https://www.qr-code-generator.com/)
2. URL einfügen
3. QR Code downloaden

---

## 🛡️ Sicherheit

### API Key schützen
- ✅ API Key ist **nur im Backend** (Railway)
- ✅ Nicht im Frontend sichtbar
- ✅ Nicht in GitHub (`.env` ist in `.gitignore`)
- ✅ Sicher!

### Railway API Key ändern
1. Railway Dashboard
2. Variables → CMC_API_KEY
3. Neuen Wert einfügen
4. Automatischer Neustart

---

## 🎉 Fertig!

Du hast jetzt eine professionelle Web-App:
- ✅ Hosted auf GitHub Pages
- ✅ Backend auf Railway
- ✅ One-Click Refresh
- ✅ 30 Empfehlungen
- ✅ Professionelle Analyse
- ✅ Kostenlos nutzbar

**Viel Erfolg mit CADVI Pro! 🚀**
