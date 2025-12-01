"""Vercel Serverless Function - Optimized Crypto Analysis API

Now with:
- Smart dynamic targets based on volatility (not fixed +20%)
- Aggressive filtering for high-probability picks
- Realistic timeframe estimates
"""
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


def calculate_smart_target(coin: dict) -> tuple:
    """Calculate realistic target price based on volatility

    Returns: (target_price, target_pct, timeframe_estimate)
    """
    current_price = coin['price']
    vol_24h = abs(coin['change_24h'])
    vol_7d = abs(coin['change_7d'])

    # High volatility = bigger targets achievable faster
    if vol_24h > 20 or vol_7d > 50:
        target_pct = 0.20  # +20%
        timeframe = "1-3 days"
    elif vol_24h > 12 or vol_7d > 30:
        target_pct = 0.15  # +15%
        timeframe = "2-5 days"
    elif vol_24h > 8 or vol_7d > 20:
        target_pct = 0.12  # +12%
        timeframe = "3-7 days"
    else:
        target_pct = 0.08  # +8%
        timeframe = "1-2 weeks"

    target_price = current_price * (1 + target_pct)
    return target_price, target_pct, timeframe


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse query parameters
            query = urlparse(self.path).query
            params = parse_qs(query)

            limit = int(params.get('limit', ['1000'])[0])
            top = int(params.get('top', ['10'])[0])
            min_score = int(params.get('min_score', ['65'])[0])

            # Fetch and analyze
            client = CoinMarketCapClient()
            coins_data = client.get_latest_listings(limit=limit)

            if not coins_data:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Failed to fetch data from CoinMarketCap (check API key/limit)'}).encode())
                return

            analyzer = EnhancedCryptoAnalyzer(coins_data)
            analyzer.calculate_comprehensive_scores()

            # Get more candidates for aggressive filtering
            all_spot = analyzer.get_top_by_category('spot', n=50)

            # AGGRESSIVE FILTERING for high-probability targets
            filtered = []
            for symbol, coin in all_spot:
                # Must meet ALL criteria:
                score_ok = coin['enhanced_score'] >= min_score
                not_overextended = coin['change_24h'] < 30  # Not already pumped too much
                has_momentum = coin['volume_change_24h'] > 30  # Volume increasing
                wash_clean = coin['wash_trading_confidence'] < 40  # Low wash trading risk
                sufficient_liquidity = coin['market_cap'] > 30_000_000  # $30M+ mcap

                if score_ok and not_overextended and has_momentum and wash_clean and sufficient_liquidity:
                    filtered.append((symbol, coin))

            # Take top N after filtering
            top_picks = filtered[:top]

            # Format response with smart targets
            def format_coin(symbol, coin_data):
                target_price, target_pct, timeframe = calculate_smart_target(coin_data)

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
                    'take_profit': round(target_price, 8),
                    'target_pct': round(target_pct * 100, 1),  # NEW: Actual target %
                    'timeframe': timeframe,  # NEW: Expected time to target
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
                'spot': [format_coin(s, c) for s, c in top_picks]
            }

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except ValueError as e:
            # Configuration errors (e.g., missing API key)
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
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
