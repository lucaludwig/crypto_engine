# CADVI Pro - Web Application

Professional Crypto Market Advisor with web interface.

## 🎯 Features

- **One-Click Analysis**: Refresh recommendations with a button
- **30 Recommendations**: 10 each for Binance Spot, Futures, and Web3 Wallet
- **Professional Analysis**: RSI, MACD, Bollinger Bands, Wash Trading Detection
- **Beautiful UI**: Modern, responsive design
- **GitHub Pages**: Frontend hosted for free
- **Contract Addresses**: For Web3 tokens (search on Binance)

## 📁 Project Structure

```
cadvi/
├── backend/              # Python Flask API
│   ├── api.py           # Main API endpoint
│   ├── requirements.txt # Python dependencies
│   └── Procfile         # For deployment
├── docs/                # Frontend (GitHub Pages)
│   ├── index.html       # Main page
│   ├── style.css        # Styling
│   └── app.js           # JavaScript logic
├── enhanced_analyzer.py # Analysis engine
├── cmc_client.py        # CoinMarketCap client
└── pro_advisor.py       # CLI version
```

## 🚀 Deployment

### Step 1: Deploy Backend API

**Option A: Railway.app (Recommended - Free)**

1. Go to [Railway.app](https://railway.app)
2. Click "Start a New Project"
3. Connect your GitHub repository
4. Select the `backend` folder
5. Add environment variable: `CMC_API_KEY=your_api_key`
6. Deploy
7. Copy the deployed URL (e.g., `https://yourapp.railway.app`)

**Option B: Render.com (Free)**

1. Go to [Render.com](https://render.com)
2. Create "New Web Service"
3. Connect GitHub repo
4. Root Directory: `backend`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `gunicorn api:app`
7. Add environment variable: `CMC_API_KEY=your_api_key`
8. Deploy
9. Copy the URL

**Option C: Heroku**

```bash
cd backend
heroku create your-app-name
heroku config:set CMC_API_KEY=your_api_key
git push heroku main
```

### Step 2: Update Frontend API URL

1. Open `docs/app.js`
2. Line 2: Update `API_URL` with your deployed backend URL:
   ```javascript
   const API_URL = 'https://your-api-url.com/api/analyze';
   ```
3. Save and commit

### Step 3: Enable GitHub Pages

1. Go to your repository on GitHub
2. Settings → Pages
3. Source: Deploy from branch
4. Branch: `main`, Folder: `/docs`
5. Save
6. Your site will be live at: `https://lucaludwig.github.io/crypto_engine/`

## 🔧 Local Development

### Backend (Terminal 1)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set API key
export CMC_API_KEY=your_key_here

# Run server
python api.py
```

Backend runs at: `http://localhost:5000`

### Frontend (Terminal 2)

```bash
cd docs
python3 -m http.server 8000
```

Frontend runs at: `http://localhost:8000`

**Update `app.js` for local testing:**
```javascript
const API_URL = 'http://localhost:5000/api/analyze';
```

## 📊 API Endpoints

### GET /api/analyze

**Parameters:**
- `limit` (optional): Number of coins to analyze (default: 1000)
- `top` (optional): Number of spot picks to return (default: 10)

**Example:**
```
GET /api/analyze?limit=1000&top=10
```

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "total_analyzed": 987,
  "filtered": 143,
  "spot": [
    {
      "symbol": "KAITO",
      "name": "Kaito AI",
      "price": 0.1234,
      "market_cap": 125000000,
      "volume_24h": 6500000,
      "change_24h": 18.5,
      "change_7d": 52.1,
      "volume_change_24h": 240.3,
      "score": 92.4,
      "position_size": 6.5,
      "take_profit": 0.1481,
      "stop_loss": 0.1110,
      "risk_level": "HIGH",
      "wash_trading_suspicious": false,
      "wash_trading_confidence": 12.5,
      "contract_address": "0x1234...abcd",
      "platform": "Ethereum",
      "slug": "kaito-ai"
    }
  ]
}
```

### GET /api/health

Health check endpoint.

## 🔐 Environment Variables

**Backend (.env or deployment config):**
```
CMC_API_KEY=your_coinmarketcap_api_key
PORT=5000  # Optional, defaults to 5000
```

Get your free API key: https://coinmarketcap.com/api/

## ⚠️ Important Notes

1. **CoinMarketCap Free Tier**: 333 API calls/day
2. **Not Financial Advice**: Educational purposes only
3. **High Risk**: Crypto is extremely volatile
4. **DYOR**: Always do your own research
5. **Stop Losses**: Always use them!

## 🎨 Customization

### Change Colors

Edit `docs/style.css`:
```css
/* Line 8: Main gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Change Results Per Category

Edit `docs/index.html`:
```html
<!-- Line 37: Default value -->
<option value="10" selected>10</option>
```

## 📱 Mobile Responsive

The UI automatically adapts to mobile devices.

## 🐛 Troubleshooting

**"API error: 500"**
- Check if backend is deployed and running
- Verify CMC_API_KEY is set in backend environment

**"Failed to fetch"**
- Update API_URL in `docs/app.js`
- Check CORS is enabled (already in api.py)

**Empty results**
- Check API rate limits (333 calls/day on free tier)
- Verify API key is valid

## 📄 License

MIT License - Free to use and modify

---

**🚀 Your Web App is Ready!**

1. Deploy backend → Get URL
2. Update `docs/app.js` with API URL
3. Push to GitHub
4. Enable GitHub Pages
5. Visit your live site!
