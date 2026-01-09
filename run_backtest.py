#!/usr/bin/env python3
"""Backtest Runner - Walk-Forward Validation

MANDATORY BEFORE LIVE TRADING:

This script runs a complete walk-forward validation test:
1. Downloads historical data from Binance
2. Splits into In-Sample (70%) and Out-of-Sample (30%)
3. Runs backtest on IS data
4. Runs backtest on OOS data (FROZEN PARAMETERS)
5. Validates against target metrics
6. Generates report

TARGET METRICS (Required for LIVE):
- Expectancy per Trade: > $0
- Profit Factor: > 1.8
- Max Drawdown: < 25%
- Sharpe Ratio: > 1.5
- OOS Degradation: < 30% vs IS

Usage:
    python run_backtest.py --months 12 --symbols 20 --capital 10000

IMPORTANT: This uses the SAME strategy code as the live bot!
"""
import argparse
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from core.backtest.data_loader import DataLoader
from core.backtest.walk_forward import WalkForwardTest
from core.infra.binance_market_data import BinanceMarketData

load_dotenv()


def main():
    """Main backtest runner"""
    parser = argparse.ArgumentParser(description="Run Walk-Forward Backtest")
    parser.add_argument('--months', type=int, default=12, help='Months of historical data (default: 12)')
    parser.add_argument('--symbols', type=int, default=20, help='Number of top symbols to test (default: 20)')
    parser.add_argument('--capital', type=float, default=10000.0, help='Initial capital (default: 10000)')
    parser.add_argument('--interval', type=str, default='5m', help='Timeframe (default: 5m)')
    parser.add_argument('--max-positions', type=int, default=4, help='Max positions (default: 4)')
    parser.add_argument('--is-pct', type=float, default=0.70, help='In-Sample percentage (default: 0.70)')

    args = parser.parse_args()

    print(f"\n{'#'*80}")
    print(f"VOLATILITY BREAKOUT STRATEGY - BACKTEST")
    print(f"{'#'*80}\n")

    # Load API keys
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET') or os.getenv('BINANCE_SECRET_KEY')

    if not api_key or not api_secret:
        print("❌ Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env")
        return

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.months * 30)

    print(f"Configuration:")
    print(f"  Period:          {start_date.date()} to {end_date.date()} ({args.months} months)")
    print(f"  Interval:        {args.interval}")
    print(f"  Initial Capital: ${args.capital:,.2f}")
    print(f"  Max Positions:   {args.max_positions}")
    print(f"  Top Symbols:     {args.symbols}")
    print(f"  IS/OOS Split:    {args.is_pct*100:.0f}% / {(1-args.is_pct)*100:.0f}%\n")

    # Get top symbols (with stablecoin filter!)
    print("Fetching top symbols (filtering stablecoins)...")
    market_data = BinanceMarketData(api_key, api_secret)
    top_symbols = market_data.get_top_symbols_by_volume(limit=args.symbols * 2)  # Get extra to account for filtering

    # Filter and limit
    symbols = top_symbols[:args.symbols]
    print(f"✓ Selected {len(symbols)} symbols for backtest\n")

    # Download historical data
    data_loader = DataLoader(api_key, api_secret)

    print(f"{'='*80}")
    print(f"DOWNLOADING HISTORICAL DATA")
    print(f"{'='*80}\n")

    data = data_loader.download_multiple_symbols(
        symbols,
        args.interval,
        start_date,
        end_date
    )

    if not data:
        print("❌ Error: No data downloaded")
        return

    # Validate data
    print(f"\nValidating data...")
    validation = data_loader.validate_data(data)

    print(f"  Total Symbols:   {validation['total_symbols']}")
    print(f"  Valid Symbols:   {validation['valid_symbols']}")
    print(f"  Bars per Symbol: {validation['min_bars']} - {validation['max_bars']} (avg: {validation['avg_bars']:.0f})")

    if validation['invalid_symbols']:
        print(f"\n  Invalid Symbols:")
        for symbol, reason in validation['invalid_symbols']:
            print(f"    {symbol}: {reason}")

    # Remove invalid symbols
    valid_data = {s: d for s, d in data.items() if s not in [x[0] for x in validation['invalid_symbols']]}

    if len(valid_data) < 5:
        print(f"\n❌ Error: Not enough valid symbols ({len(valid_data)}). Need at least 5.")
        return

    print(f"\n✓ Using {len(valid_data)} valid symbols for backtest\n")

    # Split IS/OOS
    is_data, oos_data = data_loader.split_data_is_oos(valid_data, is_pct=args.is_pct)

    # Run walk-forward test
    print(f"{'='*80}")
    print(f"STARTING WALK-FORWARD VALIDATION")
    print(f"{'='*80}\n")

    test = WalkForwardTest(
        initial_capital=args.capital,
        max_positions=args.max_positions
    )

    results = test.run_is_oos_test(is_data, oos_data)

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"backtest_results_{timestamp}.json"
    test.save_results(results, results_file)

    # Print final recommendation
    print(f"\n{'#'*80}")
    print(f"RECOMMENDATION")
    print(f"{'#'*80}\n")

    if results['ready_for_live']:
        print(f"✅ The strategy is VALIDATED and shows consistent performance.")
        print(f"\n   IS Performance:")
        print(f"     - Expectancy: ${results['is_results']['metrics']['expectancy']:.2f}")
        print(f"     - Profit Factor: {results['is_results']['metrics']['profit_factor']:.2f}")
        print(f"     - Sharpe: {results['is_results']['metrics']['sharpe_ratio']:.2f}")
        print(f"\n   OOS Performance:")
        print(f"     - Expectancy: ${results['oos_results']['metrics']['expectancy']:.2f}")
        print(f"     - Profit Factor: {results['oos_results']['metrics']['profit_factor']:.2f}")
        print(f"     - Sharpe: {results['oos_results']['metrics']['sharpe_ratio']:.2f}")
        print(f"\n   Degradation: {results['comparison']['overall_drop_pct']:.1f}% (Target: < 30%)")
        print(f"\n   ✓ You may proceed with LIVE TRADING.")
        print(f"   ⚠️  Start with SMALL capital and monitor closely!\n")
    else:
        print(f"❌ The strategy FAILED validation.")
        print(f"\n   Issues:")

        if not results['is_validation']['all_passed']:
            print(f"     - In-Sample metrics do not meet targets")
            if not results['is_validation']['expectancy_positive']:
                print(f"       ✗ Expectancy: ${results['is_results']['metrics']['expectancy']:.2f} (need > 0)")
            if not results['is_validation']['profit_factor_target']:
                print(f"       ✗ Profit Factor: {results['is_results']['metrics']['profit_factor']:.2f} (need > 1.8)")
            if not results['is_validation']['max_dd_acceptable']:
                print(f"       ✗ Max DD: {results['is_results']['metrics']['max_dd_pct']:.2f}% (need < 25%)")
            if not results['is_validation']['sharpe_ratio_target']:
                print(f"       ✗ Sharpe: {results['is_results']['metrics']['sharpe_ratio']:.2f} (need > 1.5)")

        if not results['oos_validation']['all_passed']:
            print(f"     - Out-of-Sample metrics do not meet targets")

        if not results['comparison']['acceptable']:
            print(f"     - OOS degradation too high: {results['comparison']['overall_drop_pct']:.1f}% (need < 30%)")
            print(f"       This indicates OVERFITTING!")

        print(f"\n   ❌ DO NOT trade this strategy live.")
        print(f"   ⚠️  Consider:")
        print(f"       - Adjusting parameters (but beware of curve fitting!)")
        print(f"       - Testing longer time periods")
        print(f"       - Trying different markets")
        print(f"       - Fundamentally reviewing the strategy logic\n")

    print(f"{'#'*80}\n")


if __name__ == '__main__':
    main()
