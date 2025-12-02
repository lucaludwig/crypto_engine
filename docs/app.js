// Configuration
const API_URL = '/api/analyze'; // Vercel serverless function
// No need to update - works automatically!

// Elements
const analyzeBtn = document.getElementById('analyzeBtn');
const limitSelect = document.getElementById('limitSelect');
const topSelect = document.getElementById('topSelect');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');

// Stats elements
const totalRecs = document.getElementById('totalRecs');
const totalAnalyzed = document.getElementById('totalAnalyzed');
const totalFiltered = document.getElementById('totalFiltered');
const lastUpdate = document.getElementById('lastUpdate');

// Category elements
const spotList = document.getElementById('spotList');
const spotCount = document.getElementById('spotCount');

// Event Listener
analyzeBtn.addEventListener('click', analyzeMarket);

async function analyzeMarket() {
    // Reset UI
    error.classList.add('hidden');
    results.classList.add('hidden');
    loading.classList.remove('hidden');
    analyzeBtn.disabled = true;

    try {
        const limit = limitSelect.value;
        const top = topSelect.value;

        const response = await fetch(`${API_URL}?limit=${limit}&top=${top}`);
        const data = await response.json();

        if (!response.ok) {
            const msg = data?.error || `API error: ${response.status}`;
            throw new Error(msg);
        }

        // Display results
        displayStats(data);
        displayRecommendations(data.spot);

        loading.classList.add('hidden');
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
    const total = data.spot.length;
    totalRecs.textContent = total;
    totalAnalyzed.textContent = data.total_analyzed;
    totalFiltered.textContent = data.filtered;

    const now = new Date();
    lastUpdate.textContent = now.toLocaleTimeString();
}

function displayRecommendations(spotCoins) {
    spotList.innerHTML = '';
    spotCount.textContent = spotCoins.length;

    spotCoins.forEach((coin, index) => {
        spotList.appendChild(createCoinCard(coin, index + 1));
    });
}

function createCoinCard(coin, rank) {
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

    const hasContractInfo = coin.contract_address;
    const contractSection = hasContractInfo ? `
        <div class="contract-info">
            <div class="contract-label">Contract ${coin.platform ? `(${coin.platform})` : ''}</div>
            <div class="contract-address">${coin.contract_address}</div>
        </div>` : '';

    card.innerHTML = `
        <div class="coin-header">
            <div>
                <div class="coin-title">#${rank} ${coin.symbol}</div>
                <div class="stat-name">${coin.name}</div>
            </div>
            <div>
                <div class="coin-price">${priceFormatted}</div>
                <span class="coin-score">Score ${coin.score}</span>
            </div>
        </div>

        <div class="coin-stats">
            <div class="stat">
                <span class="stat-name">Market Cap</span>
                <span class="stat-val">${formatCurrency(coin.market_cap)}</span>
            </div>
            <div class="stat">
                <span class="stat-name">Volume 24h</span>
                <span class="stat-val">${formatCurrency(coin.volume_24h)}</span>
            </div>
            <div class="stat">
                <span class="stat-name">24h</span>
                <span class="stat-val ${change24Class}">${coin.change_24h >= 0 ? '+' : ''}${coin.change_24h.toFixed(2)}%</span>
            </div>
            <div class="stat">
                <span class="stat-name">7d</span>
                <span class="stat-val ${change7Class}">${coin.change_7d >= 0 ? '+' : ''}${coin.change_7d.toFixed(2)}%</span>
            </div>
            <div class="stat">
                <span class="stat-name">Vol Δ</span>
                <span class="stat-val ${volChangeClass}">${coin.volume_change_24h >= 0 ? '+' : ''}${coin.volume_change_24h.toFixed(1)}%</span>
            </div>
        </div>

        <div class="coin-trading">
            <div class="trading-row">
                <span class="trading-label">Take Profit</span>
                <span class="trading-value">${coin.take_profit.toFixed(6)} <span class="target-gain">(+${coin.target_pct || 20}%)</span></span>
            </div>
            <div class="trading-row">
                <span class="trading-label">Stop Loss</span>
                <span class="trading-value negative">${coin.stop_loss.toFixed(6)}</span>
            </div>
            <div class="trading-row">
                <span class="trading-label">Expected Time</span>
                <span class="trading-value timeframe">${coin.timeframe || '1-3 days'}</span>
            </div>
        </div>

        ${contractSection}

        <div class="coin-actions">
            <a href="https://www.binance.com/en/trade/${coin.symbol}_USDT?type=spot" target="_blank" rel="noopener" class="btn-binance">
                Buy on Binance
            </a>
            <a href="https://coinmarketcap.com/currencies/${coin.slug}/" target="_blank" rel="noopener" class="link-cmc">
                View Details →
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
