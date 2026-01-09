#!/usr/bin/env python3
"""Check current position P&L"""
import os
import json
from dotenv import load_dotenv
load_dotenv()

from core.infra.binance_market_data import BinanceMarketData

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET') or os.getenv('BINANCE_SECRET_KEY')
market_data = BinanceMarketData(api_key, api_secret)

# Load positions
with open('position_metadata.json', 'r') as f:
    positions = json.load(f)

print("=" * 80)
print("CURRENT POSITIONS (Last trade: Jan 2, 2026)")
print("=" * 80)

total_value = 0
total_cost = 0

for symbol, pos in positions.items():
    # Get current price
    current_price = market_data.get_current_price(symbol.replace('USDC', 'USDT'))
    if not current_price:
        current_price = market_data.get_current_price(symbol)

    entry = pos['entry_price']
    qty = pos['quantity']
    sl = pos['stop_loss']
    tp = pos['take_profit']

    cost = entry * qty
    value = current_price * qty if current_price else cost
    pnl_pct = ((current_price - entry) / entry * 100) if current_price else 0

    total_cost += cost
    total_value += value

    # Distance to SL and TP
    sl_dist = ((current_price - sl) / current_price * 100) if current_price else 0
    tp_dist = ((tp - current_price) / current_price * 100) if current_price else 0

    status = "🟢" if pnl_pct > 0 else "🔴"

    coin = symbol.replace('USDC', '')
    print(f"\n{status} {coin:8s}")
    print(f"   Entry: ${entry:.6f} → Current: ${current_price:.6f} ({pnl_pct:+.1f}%)")
    print(f"   Value: ${value:.2f} (cost: ${cost:.2f})")
    print(f"   SL: ${sl:.6f} ({sl_dist:.1f}% away) | TP: ${tp:.6f} ({tp_dist:.1f}% to go)")

print("\n" + "=" * 80)
total_pnl = total_value - total_cost
total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
print(f"TOTAL: ${total_value:.2f} | Cost: ${total_cost:.2f} | P&L: ${total_pnl:+.2f} ({total_pnl_pct:+.1f}%)")
print("=" * 80)
print("\n⚠️  Bot has NOT been running since Jan 2. No scans or trades in 4 days.")
