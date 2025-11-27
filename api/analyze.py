"""Vercel Serverless Function - Crypto Analysis API"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse


# Ensure local imports work in the Vercel runtime
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from cmc_client import CoinMarketCapClient
from enhanced_analyzer import EnhancedCryptoAnalyzer


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            query = urlparse(self.path).query
            params = parse_qs(query)

            limit = int(params.get('limit', ['1000'])[0])
            top = int(params.get('top', ['10'])[0])

            # Fetch and analyze
            client = CoinMarketCapClient()
            coins_data = client.get_latest_listings(limit=limit)

            if not coins_data:
                self.send_error(500, 'Failed to fetch data from CoinMarketCap')
                return

            analyzer = EnhancedCryptoAnalyzer(coins_data)
            analyzer.calculate_comprehensive_scores()

            # Get recommendations
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

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
