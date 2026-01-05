#!/usr/bin/env python3
"""Analyze trading performance and positions"""
from api.binance_client import load_binance_client
from datetime import datetime
import json

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('=' * 80)
print('PERFORMANCE ANALYSE')
print('=' * 80)

# Portfolio Status
summary = client.get_portfolio_summary()
print(f"\n💰 PORTFOLIO:")
print(f"   Balance: ${summary['total_balance_usdt']:.2f} USDT")
print(f"   P&L: {summary['pnl_usdt']:+.2f} USDT ({summary['pnl_pct']:+.2f}%)")
print(f"   Exposure: {summary['exposure_pct']:.1f}%")

# Check all positions with current P&L
print(f"\n📊 POSITIONEN ({summary['positions_count']}):")
for symbol, pos in summary['positions'].items():
    if pos['usdt_value'] > 0.5:  # Only positions > $0.50
        print(f"   {symbol:8s} ${pos['usdt_value']:>8.2f}")

# Load trade history
with open('trades_log.json', 'r') as f:
    trades = json.load(f)

print(f"\n📈 TRADE HISTORY:")
print(f"   Total Trades: {len(trades)}")

# Analyze recent trades
buys = [t for t in trades if t['side'] == 'BUY']
sells = [t for t in trades if t['side'] == 'SELL']

print(f"   Buys: {len(buys)}")
print(f"   Sells: {len(sells)}")

if sells:
    print(f"\n🔴 VERKÄUFE (letzte 10):")
    for sell in sells[-10:]:
        symbol = sell['symbol']
        timestamp = sell['timestamp']
        reason = sell.get('reason', 'Unknown')
        print(f"   {timestamp[:16]} | {symbol:12s} | Grund: {reason}")

# Check for stop-loss triggers
stop_loss_count = sum(1 for s in sells if 'stop' in s.get('reason', '').lower())
print(f"\n⚠️  Stop-Loss Verkäufe: {stop_loss_count}/{len(sells)}")

# Get current open orders
print(f"\n🛡️ AKTIVE SCHUTZ-ORDERS:")
for symbol in ['XVGUSDC', 'ONTUSDC', 'ANIMEUSDC']:
    try:
        orders = client.client.get_open_orders(symbol=symbol)
        if orders:
            for order in orders:
                if order['type'] == 'STOP_LOSS_LIMIT':
                    stop_price = float(order['stopPrice'])
                    # Get current price
                    ticker = client.client.get_symbol_ticker(symbol=symbol)
                    current_price = float(ticker['price'])
                    distance = ((current_price - stop_price) / current_price) * 100
                    print(f"   {symbol}: Stop @ ${stop_price:.6f} ({distance:+.1f}% entfernt)")
    except:
        pass

print('\n' + '=' * 80)
