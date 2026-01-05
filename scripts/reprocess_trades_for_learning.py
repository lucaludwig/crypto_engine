#!/usr/bin/env python3
"""Reprocess old trades to feed them to the learning engine

This script retroactively processes trades that were logged without coin_data,
fetching the data from CoinMarketCap and feeding it to the learning engine.

Use this after fixing the position monitor to catch up on missed learning.
"""
import json
from pathlib import Path
from api.learning_engine import TradingLearningEngine
from api.cmc_client import CoinMarketCapClient

def main():
    print("🔄 Reprocessing old trades for learning engine...\n")

    # Load files (handle both direct run and scripts/ subfolder run)
    if Path("trades_log.json").exists():
        trades_file = Path("trades_log.json")
        learnings_file = Path("learnings.json")
    else:
        trades_file = Path(__file__).parent.parent / "trades_log.json"
        learnings_file = Path(__file__).parent.parent / "learnings.json"

    if not trades_file.exists():
        print("❌ No trades_log.json found")
        return

    with open(trades_file, 'r') as f:
        trades = json.load(f)

    # Filter for sell trades (exits) only
    exits = [t for t in trades if t.get('side') == 'SELL' and t.get('exit_type')]

    print(f"Found {len(exits)} exit trades to process")

    # Initialize learning engine and CMC client
    learning_engine = TradingLearningEngine()
    cmc_client = CoinMarketCapClient()

    # Fetch CMC data once
    print("Fetching CoinMarketCap data...")
    coins_data = cmc_client.get_latest_listings(limit=500)
    if not coins_data:
        print("❌ Failed to fetch CMC data")
        return

    # Build lookup dict
    cmc_lookup = {coin['symbol']: coin for coin in coins_data}

    processed = 0
    skipped = 0

    for exit_trade in exits:
        symbol = exit_trade.get('symbol', '')
        base_asset = symbol.replace('USDC', '').replace('USDT', '').replace('BUSD', '')

        # Find matching BUY trade for entry price
        entry_price = exit_trade.get('entry_price')
        if not entry_price:
            # Try to find the buy trade
            for t in reversed(trades):
                if (t.get('side') == 'BUY' and
                    base_asset in t.get('symbol', '')):
                    entry_price = t.get('price')
                    break

        if not entry_price:
            print(f"  ⊗ Skipping {symbol}: No entry price found")
            skipped += 1
            continue

        exit_price = exit_trade.get('price', 0)

        # Get coin data from CMC
        coin_data = cmc_lookup.get(base_asset)

        if not coin_data:
            print(f"  ⊗ Skipping {symbol}: Not found on CMC")
            skipped += 1
            continue

        # Feed to learning engine
        try:
            learning_engine.analyze_trade_outcome(
                symbol=symbol,
                buy_price=entry_price,
                sell_price=exit_price,
                coin_data=coin_data
            )
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            status = "WIN" if pnl_pct > 0 else "LOSS"
            print(f"  ✓ Processed {symbol}: {status} {pnl_pct:+.1f}%")
            processed += 1
        except Exception as e:
            print(f"  ⊗ Failed to process {symbol}: {e}")
            skipped += 1

    print(f"\n✅ Done!")
    print(f"Processed: {processed}")
    print(f"Skipped: {skipped}")

    # Show updated learning stats
    with open(learnings_file, 'r') as f:
        learnings = json.load(f)

    experiences = len(learnings.get('experiences', []))
    print(f"\nLearning Engine now has {experiences} experiences")

if __name__ == "__main__":
    main()
