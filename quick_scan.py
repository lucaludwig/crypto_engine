#!/usr/bin/env python3
"""Quick scan to see how close we are to buy signals"""
import os
import sys
from dotenv import load_dotenv
import numpy as np

load_dotenv()

from core.infra.binance_market_data import BinanceMarketData
from core.strategy.compression_detector import CompressionDetector
from core.strategy.breakout_trigger import BreakoutTrigger, Direction

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET') or os.getenv('BINANCE_SECRET_KEY')

market_data = BinanceMarketData(api_key, api_secret)
compression_detector = CompressionDetector()
breakout_trigger = BreakoutTrigger()

print("Scanning top 50 coins by volume...\n")

symbols = market_data.get_top_symbols_by_volume(limit=50)

results = []

for symbol in symbols:
    try:
        klines = market_data.get_klines(symbol, market_data.TIMEFRAME_5M, limit=500)
        if not klines:
            continue

        # Check compression
        is_compressed, comp_details = compression_detector.is_compressed(
            klines['highs'], klines['lows'], klines['closes']
        )

        # Check breakout conditions even if not compressed
        opens = klines['opens']
        highs = klines['highs']
        lows = klines['lows']
        closes = klines['closes']
        volumes = klines['volumes']

        # Volume
        avg_volume = np.mean(volumes[-21:-1])
        current_volume = volumes[-1]
        vol_mult = current_volume / avg_volume if avg_volume > 0 else 0
        vol_needed = breakout_trigger.VOLUME_MULTIPLIER
        vol_pct = (vol_mult / vol_needed) * 100

        # Price break
        range_highs = highs[-25:-1]
        range_lows = lows[-25:-1]
        max_high = np.max(range_highs)
        min_low = np.min(range_lows)
        current_close = closes[-1]

        if current_close < max_high:
            price_distance = ((max_high - current_close) / current_close) * 100
            price_break_pct = ((current_close - min_low) / (max_high - min_low)) * 100
        else:
            price_distance = 0
            price_break_pct = 100

        # RSI
        rsi = breakout_trigger.calculate_rsi(closes)
        rsi_in_range = 55 <= rsi <= 70 if rsi else False

        # Wick check
        body = abs(closes[-1] - opens[-1])
        upper_wick = highs[-1] - max(opens[-1], closes[-1])
        wick_pct = (upper_wick / body * 100) if body > 0 else 999

        results.append({
            'symbol': symbol,
            'compressed': is_compressed,
            'vol_mult': vol_mult,
            'vol_pct': vol_pct,
            'price_to_break': price_distance,
            'price_in_range_pct': price_break_pct,
            'rsi': rsi,
            'rsi_ok': rsi_in_range,
            'wick_pct': wick_pct,
            'wick_ok': wick_pct <= 30
        })
    except Exception as e:
        continue

# Sort by closest to buy
results.sort(key=lambda x: (
    -int(x['compressed']),  # Compressed first
    -x['vol_pct'],  # Higher volume % first
    x['price_to_break']  # Closer to breakout first
))

print("=" * 100)
print(f"{'Symbol':12} | {'Compr':6} | {'Vol':6} | {'Vol%':6} | {'ToBreak':8} | {'RSI':5} | {'RSI OK':6} | {'Wick%':6}")
print("=" * 100)

for r in results[:25]:
    vol_color = "🟢" if r['vol_pct'] >= 100 else "🟡" if r['vol_pct'] >= 70 else "🔴"
    price_color = "🟢" if r['price_to_break'] <= 0.5 else "🟡" if r['price_to_break'] <= 2 else "🔴"
    rsi_color = "🟢" if r['rsi_ok'] else "🟡" if r['rsi'] and 50 <= r['rsi'] <= 75 else "🔴"
    wick_color = "🟢" if r['wick_ok'] else "🔴"

    print(f"{r['symbol']:12} | {'✓' if r['compressed'] else '✗':6} | {r['vol_mult']:.2f}x | {r['vol_pct']:5.0f}% | {r['price_to_break']:6.2f}% | {r['rsi']:5.1f} | {'✓' if r['rsi_ok'] else '✗':6} | {r['wick_pct']:5.0f}%")

# Summary
compressed_count = sum(1 for r in results if r['compressed'])
close_to_vol = sum(1 for r in results if r['vol_pct'] >= 70)
close_to_price = sum(1 for r in results if r['price_to_break'] <= 2)
rsi_ready = sum(1 for r in results if r['rsi_ok'])

print("\n" + "=" * 100)
print("SUMMARY - How close are we to buying?")
print("=" * 100)
print(f"Coins in compression:      {compressed_count}/{len(results)}")
print(f"Volume ≥70% of threshold:  {close_to_vol}/{len(results)}")
print(f"Price within 2% of break:  {close_to_price}/{len(results)}")
print(f"RSI in range (55-70):      {rsi_ready}/{len(results)}")

# Find best opportunities
best = [r for r in results if r['compressed'] and r['vol_pct'] >= 50 and r['price_to_break'] <= 3]
if best:
    print(f"\n🎯 CLOSEST TO BUY:")
    for b in best[:5]:
        conditions_met = sum([
            b['vol_pct'] >= 100,
            b['price_to_break'] <= 0,
            b['rsi_ok'],
            b['wick_ok']
        ])
        print(f"  {b['symbol']:12} - {conditions_met}/4 conditions | Vol: {b['vol_mult']:.2f}x ({b['vol_pct']:.0f}%) | Break: {b['price_to_break']:.2f}% away | RSI: {b['rsi']:.1f}")
else:
    print("\n⏸️  No coins close to triggering buy signals right now")
