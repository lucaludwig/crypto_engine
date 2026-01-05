# ⚡ Quick Deploy - 3 Schritte in 10 Minuten

## 1️⃣ Backend auf Railway (5 Min)

1. **railway.app** → Login with GitHub
2. **+ New Project** → Deploy from GitHub → `lucaludwig/crypto_engine`
3. **Settings**:
   - Root Directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `gunicorn api:app`
4. **Variables** → New Variable:
   - Name: `CMC_API_KEY`
   - Value: Dein API Key
5. **Kopiere die URL** (z.B. `https://xyz.railway.app`)

## 2️⃣ Frontend konfigurieren (2 Min)

1. Öffne `docs/app.js`
2. Zeile 2: Ersetze URL:
   ```javascript
   const API_URL = 'https://xyz.railway.app/api/analyze';
   ```
3. Terminal:
   ```bash
   git add docs/app.js
   git commit -m "Update API URL"
   git push
   ```

## 3️⃣ GitHub Pages aktivieren (3 Min)

1. **github.com/lucaludwig/crypto_engine** → Settings
2. **Pages** → Source: Branch `main`, Folder `/docs`
3. **Save**
4. Warte 2 Minuten
5. **Fertig!** → https://lucaludwig.github.io/crypto_engine/

---

## ✅ Checklist

- [ ] Railway Backend deployed
- [ ] API URL in `docs/app.js` updated
- [ ] Zu GitHub gepusht
- [ ] GitHub Pages aktiviert
- [ ] Website getestet (Button klicken!)

---

## 🧪 Testen

URL öffnen → "Analyze Market Now" klicken → Ergebnisse nach 10-30 Sek.

---

## 🆘 Hilfe

**Backend nicht erreichbar?**
- Öffne: `https://your-url.railway.app/api/health`
- Sollte: `{"status":"ok"}` zeigen

**Frontend zeigt Fehler?**
- Prüfe `docs/app.js` Zeile 2 (richtige URL?)
- Leere Browser Cache (Cmd+Shift+R)

**Detaillierte Anleitung:** `DEPLOYMENT.md`

---

**Viel Erfolg! 🚀**
