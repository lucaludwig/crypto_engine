"""Walk-Forward Testing

Implements walk-forward validation with IS/OOS splits:
1. Split data 70% In-Sample, 30% Out-of-Sample
2. Run backtest on IS data (validation)
3. Run backtest on OOS data (blind test, FROZEN PARAMETERS)
4. Compare IS vs OOS performance
5. Reject if OOS drops > 30% vs IS

This is the GOLD STANDARD for strategy validation.
"""
from typing import Dict, List, Tuple
from datetime import datetime
import json

from core.backtest.event_engine import BacktestEngine
from core.backtest.metrics import MetricsCalculator
from core.backtest.fee_slippage import FeeSlippageModel


class WalkForwardTest:
    """Conducts walk-forward validation test

    Process:
    1. Load IS and OOS data
    2. Run backtest on IS (parameters frozen)
    3. Run backtest on OOS (same parameters, blind test)
    4. Calculate metrics for both
    5. Validate OOS performance
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        max_positions: int = 4
    ):
        """Initialize walk-forward test

        Args:
            initial_capital: Starting capital for each test
            max_positions: Max simultaneous positions
        """
        self.initial_capital = initial_capital
        self.max_positions = max_positions

        self.metrics_calc = MetricsCalculator()
        self.fee_model = FeeSlippageModel()

    def run_backtest(
        self,
        data: Dict[str, List[Dict]],
        name: str = "Backtest"
    ) -> Dict:
        """Run backtest on data

        Args:
            data: Dict of symbol -> bars
            name: Test name (e.g., "In-Sample", "Out-of-Sample")

        Returns:
            Backtest results with metrics
        """
        print(f"\n{'='*80}")
        print(f"RUNNING {name.upper()}")
        print(f"{'='*80}\n")

        # Initialize engine
        engine = BacktestEngine(
            initial_capital=self.initial_capital,
            max_positions=self.max_positions
        )

        # Get all timestamps (assume all symbols have same timestamps)
        first_symbol = list(data.keys())[0]
        timestamps = [bar['timestamp'] for bar in data[first_symbol]]

        print(f"Period: {timestamps[0].date()} to {timestamps[-1].date()}")
        print(f"Bars: {len(timestamps)}")
        print(f"Symbols: {len(data)}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}\n")

        # Event loop
        signals_generated = 0
        trades_opened = 0

        for i, timestamp in enumerate(timestamps):
            # Add market data for all symbols at this timestamp
            for symbol in data:
                if i < len(data[symbol]):
                    bar = data[symbol][i]
                    engine.add_market_data(symbol, bar)

            # Manage existing positions
            engine.manage_positions()

            # Check for new signals (only if we have room for more positions)
            if len(engine.positions) < self.max_positions:
                for symbol in data:
                    if symbol in engine.positions:
                        continue

                    signal = engine.check_for_signals(symbol)
                    if signal:
                        signals_generated += 1
                        engine.execute_signal(signal)
                        trades_opened += 1

            # Update equity
            engine.update_equity()

            # Progress display
            if (i + 1) % 5000 == 0:
                pct = (i + 1) / len(timestamps) * 100
                print(f"  Progress: {pct:.1f}% ({i+1}/{len(timestamps)} bars) | Trades: {len(engine.trades)} | Open: {len(engine.positions)}")

        # Close any remaining positions
        for symbol in list(engine.positions.keys()):
            if symbol in data:
                final_price = data[symbol][-1]['close']
                engine._close_position(symbol, final_price, "End of Test")

        # Get results
        results = engine.get_results()

        print(f"\n{'='*80}")
        print(f"{name.upper()} RESULTS")
        print(f"{'='*80}")
        print(f"Signals Generated:  {signals_generated}")
        print(f"Trades Opened:      {trades_opened}")
        print(f"Trades Completed:   {len(results['trades'])}")
        print(f"Final Capital:      ${results['final_capital']:,.2f}")
        print(f"Total P&L:          ${results['total_pnl']:,.2f} ({results['total_return_pct']:+.2f}%)")

        # Calculate metrics
        metrics = self.metrics_calc.calculate_all_metrics(
            results['trades'],
            results['equity_curve'],
            self.initial_capital
        )

        print(f"\nKEY METRICS:")
        print(f"Expectancy:         ${metrics['expectancy']:.2f} per trade")
        print(f"Profit Factor:      {metrics['profit_factor']:.2f}")
        print(f"Max Drawdown:       {metrics['max_dd_pct']:.2f}%")
        print(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print(f"Win Rate:           {metrics['win_rate']:.1f}%")
        print(f"Avg Win:            ${metrics['avg_win']:.2f} ({metrics['avg_win_pct']:+.2f}%)")
        print(f"Avg Loss:           ${metrics['avg_loss']:.2f} ({metrics['avg_loss_pct']:.2f}%)")

        return {
            'name': name,
            'results': results,
            'metrics': metrics,
            'signals_generated': signals_generated
        }

    def run_is_oos_test(
        self,
        is_data: Dict[str, List[Dict]],
        oos_data: Dict[str, List[Dict]]
    ) -> Dict:
        """Run complete IS/OOS validation test

        Args:
            is_data: In-Sample data (70%)
            oos_data: Out-of-Sample data (30%)

        Returns:
            Complete test results with validation
        """
        print(f"\n{'#'*80}")
        print(f"WALK-FORWARD VALIDATION TEST")
        print(f"{'#'*80}\n")

        # Fee model info
        fee_info = self.fee_model.get_cost_summary()
        print(f"Fee Model: {fee_info['description']}")
        print(f"Round-Trip Cost: {fee_info['round_trip_cost_pct']:.3f}%")
        print(f"Minimum Profitable Move: {self.fee_model.minimum_profitable_move():.3f}%\n")

        # Run IS test
        is_results = self.run_backtest(is_data, "In-Sample (IS)")

        # Run OOS test (FROZEN PARAMETERS!)
        print(f"\n{'⚠️ '*40}")
        print(f"OOS TEST: PARAMETERS ARE FROZEN - NO TWEAKING ALLOWED!")
        print(f"{'⚠️ '*40}\n")

        oos_results = self.run_backtest(oos_data, "Out-of-Sample (OOS)")

        # Validation
        print(f"\n{'='*80}")
        print(f"VALIDATION")
        print(f"{'='*80}\n")

        # Check IS metrics
        is_validation = self.metrics_calc.passes_validation(is_results['metrics'])

        print(f"IN-SAMPLE VALIDATION:")
        print(f"  Expectancy > 0:       {'✓' if is_validation['expectancy_positive'] else '✗'} ({is_results['metrics']['expectancy']:.2f})")
        print(f"  Profit Factor > 1.8:  {'✓' if is_validation['profit_factor_target'] else '✗'} ({is_results['metrics']['profit_factor']:.2f})")
        print(f"  Max DD < 25%:         {'✓' if is_validation['max_dd_acceptable'] else '✗'} ({is_results['metrics']['max_dd_pct']:.2f}%)")
        print(f"  Sharpe Ratio > 1.5:   {'✓' if is_validation['sharpe_ratio_target'] else '✗'} ({is_results['metrics']['sharpe_ratio']:.2f})")
        print(f"  Overall:              {'✓ PASSED' if is_validation['all_passed'] else '✗ FAILED'}\n")

        # Check OOS metrics
        oos_validation = self.metrics_calc.passes_validation(oos_results['metrics'])

        print(f"OUT-OF-SAMPLE VALIDATION:")
        print(f"  Expectancy > 0:       {'✓' if oos_validation['expectancy_positive'] else '✗'} ({oos_results['metrics']['expectancy']:.2f})")
        print(f"  Profit Factor > 1.8:  {'✓' if oos_validation['profit_factor_target'] else '✗'} ({oos_results['metrics']['profit_factor']:.2f})")
        print(f"  Max DD < 25%:         {'✓' if oos_validation['max_dd_acceptable'] else '✗'} ({oos_results['metrics']['max_dd_pct']:.2f}%)")
        print(f"  Sharpe Ratio > 1.5:   {'✓' if oos_validation['sharpe_ratio_target'] else '✗'} ({oos_results['metrics']['sharpe_ratio']:.2f})")
        print(f"  Overall:              {'✓ PASSED' if oos_validation['all_passed'] else '✗ FAILED'}\n")

        # Compare IS vs OOS
        comparison = self.metrics_calc.compare_is_oos(
            is_results['metrics'],
            oos_results['metrics']
        )

        print(f"IS vs OOS COMPARISON:")
        print(f"  Expectancy Drop:      {comparison['expectancy_drop_pct']:+.1f}%")
        print(f"  Profit Factor Drop:   {comparison['profit_factor_drop_pct']:+.1f}%")
        print(f"  Sharpe Ratio Drop:    {comparison['sharpe_drop_pct']:+.1f}%")
        print(f"  Overall Degradation:  {comparison['overall_drop_pct']:.1f}%")
        print(f"  Overfitted?:          {'✗ YES' if comparison['overfitted'] else '✓ NO'} (Target: < 30% drop)")
        print(f"  OOS Acceptable?:      {'✓ YES' if comparison['acceptable'] else '✗ NO'}\n")

        # Final verdict
        print(f"\n{'='*80}")
        print(f"FINAL VERDICT")
        print(f"{'='*80}\n")

        ready_for_live = (
            is_validation['all_passed'] and
            oos_validation['all_passed'] and
            comparison['acceptable']
        )

        if ready_for_live:
            print(f"✅ STRATEGY VALIDATED - READY FOR LIVE TRADING!")
            print(f"\nAll requirements met:")
            print(f"  ✓ IS metrics pass all targets")
            print(f"  ✓ OOS metrics pass all targets")
            print(f"  ✓ OOS degradation < 30%")
        else:
            print(f"❌ STRATEGY REJECTED - NOT READY FOR LIVE TRADING!")
            print(f"\nFailures:")
            if not is_validation['all_passed']:
                print(f"  ✗ IS metrics do not meet targets")
            if not oos_validation['all_passed']:
                print(f"  ✗ OOS metrics do not meet targets")
            if not comparison['acceptable']:
                print(f"  ✗ OOS degradation > 30% (overfitted)")

        print(f"\n{'='*80}\n")

        return {
            'is_results': is_results,
            'oos_results': oos_results,
            'is_validation': is_validation,
            'oos_validation': oos_validation,
            'comparison': comparison,
            'ready_for_live': ready_for_live,
            'timestamp': datetime.now().isoformat()
        }

    def save_results(self, results: Dict, filename: str = "backtest_results.json"):
        """Save test results to file

        Args:
            results: Results dict from run_is_oos_test
            filename: Output filename
        """
        # Prepare results for JSON (remove non-serializable objects)
        serializable = {
            'timestamp': results['timestamp'],
            'ready_for_live': results['ready_for_live'],
            'is_metrics': results['is_results']['metrics'],
            'oos_metrics': results['oos_results']['metrics'],
            'is_validation': results['is_validation'],
            'oos_validation': results['oos_validation'],
            'comparison': results['comparison'],
            'is_trades_count': len(results['is_results']['results']['trades']),
            'oos_trades_count': len(results['oos_results']['results']['trades']),
            'is_signals': results['is_results']['signals_generated'],
            'oos_signals': results['oos_results']['signals_generated']
        }

        try:
            with open(filename, 'w') as f:
                json.dump(serializable, f, indent=2)
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results: {e}")
