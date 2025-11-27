#!/usr/bin/env python3
"""Flask API for CADVI Pro - Crypto Market Advisor"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cmc_client import CoinMarketCapClient
from enhanced_analyzer import EnhancedCryptoAnalyzer

app = Flask(__name__)
CORS(app)  # Enable CORS for GitHub Pages

@app.route('/')
def home():
    return jsonify({
        'name': 'CADVI Pro API',
        'version': '1.0',
        'endpoints': {
            '/api/analyze': 'GET - Get crypto recommendations',
            '/api/health': 'GET - Health check'
        }
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'message': 'API is running'})

@app.route('/api/analyze')
def analyze():
    try:
        # Get parameters
        limit = request.args.get('limit', default=1000, type=int)
        top = request.args.get('top', default=10, type=int)

        # Fetch data
        client = CoinMarketCapClient()
        coins_data = client.get_latest_listings(limit=limit)

        if not coins_data:
            return jsonify({'error': 'Failed to fetch data from CoinMarketCap'}), 500

        # Analyze
        analyzer = EnhancedCryptoAnalyzer(coins_data)
        analyzer.calculate_comprehensive_scores()

        # Get recommendations by category
        spot_coins = analyzer.get_top_by_category('spot', n=top)
        futures_coins = analyzer.get_top_by_category('futures', n=top)
        web3_coins = analyzer.get_top_by_category('web3', n=top)

        # Format response
        def format_coin(symbol, coin_data):
            return {
                'symbol': symbol,
                'name': coin_data['name'],
                'price': coin_data['price'],
                'market_cap': coin_data['market_cap'],
                'volume_24h': coin_data['volume_24h'],
                'change_24h': coin_data['change_24h'],
                'change_7d': coin_data['change_7d'],
                'volume_change_24h': coin_data['volume_change_24h'],
                'score': round(coin_data['enhanced_score'], 1),
                'position_size': round(coin_data['kelly_position_size'] * 100, 1),
                'take_profit': round(coin_data['price'] * 1.20, 8),
                'stop_loss': round(coin_data['price'] * 0.90, 8),
                'risk_level': 'EXTREME' if coin_data['risk_score'] >= 70 else 'HIGH' if coin_data['risk_score'] >= 40 else 'MEDIUM',
                'wash_trading_suspicious': coin_data['wash_trading_suspicious'],
                'wash_trading_confidence': round(coin_data['wash_trading_confidence'], 1),
                'contract_address': coin_data.get('contract_address', ''),
                'platform': coin_data.get('platform', ''),
                'slug': coin_data['slug']
            }

        response = {
            'timestamp': coins_data[0].get('last_updated', ''),
            'total_analyzed': len(analyzer.df),
            'filtered': len(analyzer.df[analyzer.df['wash_trading_suspicious'] == True]),
            'categories': {
                'spot': [format_coin(s, c) for s, c in spot_coins],
                'futures': [format_coin(s, c) for s, c in futures_coins],
                'web3': [format_coin(s, c) for s, c in web3_coins]
            }
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
