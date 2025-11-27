// Configuration
const API_URL = 'https://your-api-url.com/api/analyze'; // UPDATE THIS AFTER DEPLOYMENT
// For local testing: const API_URL = 'http://localhost:5000/api/analyze';

// Elements
const analyzeBtn = document.getElementById('analyzeBtn');
const limitSelect = document.getElementById('limitSelect');
const topSelect = document.getElementById('topSelect');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const stats = document.getElementById('stats');
const results = document.getElementById('results');

// Stats elements
const totalRecs = document.getElementById('totalRecs');
const totalAnalyzed = document.getElementById('totalAnalyzed');
const totalFiltered = document.getElementById('totalFiltered');
const lastUpdate = document.getElementById('lastUpdate');

// Category elements
const spotList = document.getElementById('spotList');
const futuresList = document.getElementById('futuresList');
const web3List = document.getElementById('web3List');
const spotCount = document.getElementById('spotCount');
const futuresCount = document.getElementById('futuresCount');
const web3Count = document.getElementById('web3Count');

// Event Listener
analyzeBtn.addEventListener('click', analyzeMarket);

async function analyzeMarket() {
    // Reset UI
    error.classList.add('hidden');
    stats.classList.add('hidden');
    results.classList.add('hidden');
    loading.classList.remove('hidden');
    analyzeBtn.disabled = true;

    try {
        const limit = limitSelect.value;
        const top = topSelect.value;

        const response = await fetch(`${API_URL}?limit=${limit}&top=${top}`);

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();

        // Display results
        displayStats(data);
        displayRecommendations(data.categories);

        loading.classList.add('hidden');
        stats.classList.remove('hidden');
        results.classList.remove('hidden');

    } catch (err) {
        loading.classList.add('hidden');
        error.classList.remove('hidden');
        error.textContent = `Error: ${err.message}. Make sure the API is deployed and the API_URL in app.js is correct.`;
    } finally {
        analyzeBtn.disabled = false;
    }
}

function displayStats(data) {
    const total = data.categories.spot.length + data.categories.futures.length + data.categories.web3.length;
    totalRecs.textContent = total;
    totalAnalyzed.textContent = data.total_analyzed;
    totalFiltered.textContent = data.filtered;

    const now = new Date();
    lastUpdate.textContent = now.toLocaleTimeString();
}

function displayRecommendations(categories) {
    spotList.innerHTML = '';
    futuresList.innerHTML = '';
    web3List.innerHTML = '';

    spotCount.textContent = categories.spot.length;
    futuresCount.textContent = categories.futures.length;
    web3Count.textContent = categories.web3.length;

    categories.spot.forEach((coin, index) => {
        spotList.appendChild(createCoinCard(coin, index + 1));
    });

    categories.futures.forEach((coin, index) => {
        futuresList.appendChild(createCoinCard(coin, index + 1));
    });

    categories.web3.forEach((coin, index) => {
        web3List.appendChild(createCoinCard(coin, index + 1, true));
    });
}

function createCoinCard(coin, rank, isWeb3 = false) {
    const card = document.createElement('div');
    card.className = 'coin-card';

    const priceFormatted = coin.price < 1
        ? `$${coin.price.toFixed(6)}`
        : `$${coin.price.toFixed(2)}`;

    const change24Class = coin.change_24h >= 0 ? 'positive' : 'negative';
    const change7Class = coin.change_7d >= 0 ? 'positive' : 'negative';
    const volChangeClass = coin.volume_change_24h >= 0 ? 'positive' : 'negative';

    const riskClass = coin.risk_level === 'EXTREME' ? 'risk-extreme'
                     : coin.risk_level === 'HIGH' ? 'risk-high'
                     : 'risk-medium';

    const washBadge = coin.wash_trading_suspicious
        ? `<span class="wash-badge">⚠️ Wash: ${coin.wash_trading_confidence}%</span>`
        : `<span class="clean-badge">✓ Clean</span>`;

    const contractSection = isWeb3 && coin.contract_address ? `
        <div class="contract-info">
            <strong>📍 Contract Address (${coin.platform}):</strong>
            <div class="contract-address">${coin.contract_address}</div>
            <small>→ Search this on Binance Web3 Wallet</small>
        </div>
    ` : '';

    card.innerHTML = `
        <div class="coin-header">
            <div>
                <div class="coin-title">#${rank} ${coin.symbol}</div>
                <div style="color: #666; font-size: 0.9rem;">${coin.name}</div>
            </div>
            <div style="text-align: right;">
                <div class="coin-price">${priceFormatted}</div>
                <span class="coin-score">Score: ${coin.score}</span>
            </div>
        </div>

        <div class="coin-stats">
            <div class="stat">
                <span class="stat-name">Market Cap:</span>
                <span class="stat-val">${formatCurrency(coin.market_cap)}</span>
            </div>
            <div class="stat">
                <span class="stat-name">Volume 24h:</span>
                <span class="stat-val">${formatCurrency(coin.volume_24h)}</span>
            </div>
            <div class="stat">
                <span class="stat-name">24h Change:</span>
                <span class="stat-val ${change24Class}">${coin.change_24h >= 0 ? '+' : ''}${coin.change_24h.toFixed(2)}%</span>
            </div>
            <div class="stat">
                <span class="stat-name">7d Change:</span>
                <span class="stat-val ${change7Class}">${coin.change_7d >= 0 ? '+' : ''}${coin.change_7d.toFixed(2)}%</span>
            </div>
            <div class="stat">
                <span class="stat-name">Vol Change:</span>
                <span class="stat-val ${volChangeClass}">${coin.volume_change_24h >= 0 ? '+' : ''}${coin.volume_change_24h.toFixed(1)}%</span>
            </div>
        </div>

        <div class="coin-trading">
            <div class="trading-row">
                <span class="trading-label">Position Size:</span>
                <span class="trading-value" style="color: #16a34a; font-size: 1.1rem;">${coin.position_size}%</span>
            </div>
            <div class="trading-row">
                <span class="trading-label">Take Profit:</span>
                <span class="trading-value" style="color: #eab308;">$${coin.take_profit.toFixed(6)}</span>
            </div>
            <div class="trading-row">
                <span class="trading-label">Stop Loss:</span>
                <span class="trading-value" style="color: #ef4444;">$${coin.stop_loss.toFixed(6)}</span>
            </div>
            <div class="trading-row">
                <span class="trading-label">Risk Level:</span>
                <span class="risk-badge ${riskClass}">${coin.risk_level}</span>
            </div>
            <div class="trading-row">
                <span class="trading-label">Volume Check:</span>
                ${washBadge}
            </div>
        </div>

        ${contractSection}

        <div style="margin-top: 10px; text-align: right;">
            <a href="https://coinmarketcap.com/currencies/${coin.slug}/"
               target="_blank"
               style="color: #667eea; text-decoration: none; font-size: 0.9rem;">
                View on CoinMarketCap →
            </a>
        </div>
    `;

    return card;
}

function formatCurrency(value) {
    if (value >= 1_000_000_000) {
        return `$${(value / 1_000_000_000).toFixed(2)}B`;
    } else if (value >= 1_000_000) {
        return `$${(value / 1_000_000).toFixed(2)}M`;
    } else if (value >= 1_000) {
        return `$${(value / 1_000).toFixed(2)}K`;
    } else {
        return `$${value.toFixed(2)}`;
    }
}
