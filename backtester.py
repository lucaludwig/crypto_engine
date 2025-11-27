"""Backtesting Framework for Crypto Trading Strategies

This module provides backtesting capabilities to validate trading recommendations
before risking real money.

Key metrics:
- Sharpe Ratio: Risk-adjusted returns
- Maximum Drawdown: Worst peak-to-trough decline
- Win Rate: Percentage of profitable trades
- Profit Factor: Ratio of gross profits to gross losses
"""
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class Trade:
    """Represents a single trade"""

    def __init__(self, symbol: str, entry_price: float, entry_time: datetime,
                 position_size: float, stop_loss: float, take_profit: float):
        self.symbol = symbol
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.position_size = position_size  # Fraction of portfolio
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
        self.profit_loss = None
        self.profit_loss_pct = None

    def close_trade(self, exit_price: float, exit_time: datetime, reason: str):
        """Close the trade and calculate P&L"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.exit_reason = reason

        # Calculate profit/loss
        price_change = (exit_price - self.entry_price) / self.entry_price
        self.profit_loss_pct = price_change * 100
        self.profit_loss = price_change * self.position_size  # Portfolio impact

    def is_open(self) -> bool:
        """Check if trade is still open"""
        return self.exit_price is None


class BacktestResult:
    """Stores backtesting results and metrics"""

    def __init__(self, trades: List[Trade], initial_capital: float = 10000):
        self.trades = trades
        self.initial_capital = initial_capital
        self._calculate_metrics()

    def _calculate_metrics(self):
        """Calculate all performance metrics"""
        if not self.trades:
            self._init_empty_metrics()
            return

        # Filter to closed trades only
        closed_trades = [t for t in self.trades if not t.is_open()]

        if not closed_trades:
            self._init_empty_metrics()
            return

        # Basic metrics
        self.total_trades = len(closed_trades)
        winning_trades = [t for t in closed_trades if t.profit_loss > 0]
        losing_trades = [t for t in closed_trades if t.profit_loss <= 0]

        self.winning_trades = len(winning_trades)
        self.losing_trades = len(losing_trades)
        self.win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0

        # Profit metrics
        self.gross_profit = sum(t.profit_loss for t in winning_trades)
        self.gross_loss = abs(sum(t.profit_loss for t in losing_trades))
        self.net_profit = self.gross_profit - self.gross_loss
        self.profit_factor = self.gross_profit / self.gross_loss if self.gross_loss > 0 else float('inf')

        # Return metrics
        self.total_return = self.net_profit
        self.total_return_pct = (self.net_profit / 1.0) * 100  # Assuming full capital deployment

        # Average trade metrics
        self.avg_win = self.gross_profit / self.winning_trades if self.winning_trades > 0 else 0
        self.avg_loss = self.gross_loss / self.losing_trades if self.losing_trades > 0 else 0
        self.avg_win_pct = np.mean([t.profit_loss_pct for t in winning_trades]) if winning_trades else 0
        self.avg_loss_pct = np.mean([t.profit_loss_pct for t in losing_trades]) if losing_trades else 0

        # Risk metrics
        self._calculate_drawdown()
        self._calculate_sharpe_ratio()

        # Trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in closed_trades]  # hours
        self.avg_trade_duration_hours = np.mean(durations) if durations else 0

    def _init_empty_metrics(self):
        """Initialize metrics with zeros"""
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.win_rate = 0
        self.gross_profit = 0
        self.gross_loss = 0
        self.net_profit = 0
        self.profit_factor = 0
        self.total_return = 0
        self.total_return_pct = 0
        self.avg_win = 0
        self.avg_loss = 0
        self.avg_win_pct = 0
        self.avg_loss_pct = 0
        self.max_drawdown = 0
        self.max_drawdown_pct = 0
        self.sharpe_ratio = 0
        self.avg_trade_duration_hours = 0

    def _calculate_drawdown(self):
        """Calculate maximum drawdown"""
        if not self.trades:
            self.max_drawdown = 0
            self.max_drawdown_pct = 0
            return

        # Build equity curve
        equity = 1.0  # Start with normalized capital
        peak = 1.0
        max_dd = 0

        for trade in self.trades:
            if trade.is_open():
                continue

            equity += trade.profit_loss
            if equity > peak:
                peak = equity

            drawdown = (peak - equity) / peak
            if drawdown > max_dd:
                max_dd = drawdown

        self.max_drawdown = max_dd
        self.max_drawdown_pct = max_dd * 100

    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.0):
        """Calculate Sharpe ratio (annualized)

        Sharpe Ratio = (Return - Risk Free Rate) / Standard Deviation of Returns
        """
        if not self.trades or len([t for t in self.trades if not t.is_open()]) < 2:
            self.sharpe_ratio = 0
            return

        returns = [t.profit_loss for t in self.trades if not t.is_open()]

        if len(returns) < 2:
            self.sharpe_ratio = 0
            return

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            self.sharpe_ratio = 0
            return

        # Annualized Sharpe (assuming daily trades, 365 days)
        sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(365)
        self.sharpe_ratio = sharpe

    def print_report(self):
        """Print comprehensive backtest report"""
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)

        print(f"\n📊 TRADE STATISTICS:")
        print(f"  Total Trades:        {self.total_trades}")
        print(f"  Winning Trades:      {self.winning_trades}")
        print(f"  Losing Trades:       {self.losing_trades}")
        print(f"  Win Rate:            {self.win_rate * 100:.1f}%")

        print(f"\n💰 PROFIT/LOSS:")
        print(f"  Gross Profit:        {self.gross_profit * 100:+.2f}%")
        print(f"  Gross Loss:          {self.gross_loss * 100:.2f}%")
        print(f"  Net Profit:          {self.net_profit * 100:+.2f}%")
        print(f"  Profit Factor:       {self.profit_factor:.2f}")

        print(f"\n📈 AVERAGE TRADE:")
        print(f"  Avg Win:             {self.avg_win * 100:+.2f}%")
        print(f"  Avg Loss:            {-self.avg_loss * 100:.2f}%")
        print(f"  Avg Duration:        {self.avg_trade_duration_hours:.1f} hours")

        print(f"\n⚠️  RISK METRICS:")
        print(f"  Max Drawdown:        {self.max_drawdown_pct:.2f}%")
        print(f"  Sharpe Ratio:        {self.sharpe_ratio:.2f}")

        # Interpretation
        print(f"\n💡 INTERPRETATION:")
        if self.sharpe_ratio > 2.0:
            print("  Sharpe Ratio: EXCELLENT (>2.0) - Very strong risk-adjusted returns")
        elif self.sharpe_ratio > 1.0:
            print("  Sharpe Ratio: GOOD (>1.0) - Solid risk-adjusted returns")
        elif self.sharpe_ratio > 0.5:
            print("  Sharpe Ratio: ACCEPTABLE (>0.5) - Modest risk-adjusted returns")
        else:
            print("  Sharpe Ratio: POOR (<0.5) - Weak or negative risk-adjusted returns")

        if self.profit_factor > 2.0:
            print("  Profit Factor: EXCELLENT (>2.0) - Wins are 2x+ larger than losses")
        elif self.profit_factor > 1.5:
            print("  Profit Factor: GOOD (>1.5) - Profitable strategy")
        elif self.profit_factor > 1.0:
            print("  Profit Factor: MARGINAL (>1.0) - Barely profitable")
        else:
            print("  Profit Factor: LOSING (<1.0) - Strategy loses money")

        if self.win_rate > 0.6:
            print("  Win Rate: HIGH (>60%) - Most trades are winners")
        elif self.win_rate > 0.5:
            print("  Win Rate: GOOD (>50%) - More wins than losses")
        else:
            print("  Win Rate: LOW (<50%) - More losses than wins")

        print("\n" + "=" * 80)


class CryptoBacktester:
    """Backtesting engine for crypto trading strategies"""

    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.trades: List[Trade] = []

    def simulate_recommendation_strategy(self,
                                        recommendations: List[Tuple[str, Dict]],
                                        hold_period_hours: int = 24,
                                        stop_loss_pct: float = 0.10,
                                        take_profit_pct: float = 0.20) -> BacktestResult:
        """Simulate trading based on recommendations

        Note: This is a SIMPLIFIED backtest using hypothetical outcomes
        Real backtesting requires historical price data

        Args:
            recommendations: List of (symbol, coin_data) tuples
            hold_period_hours: How long to hold position
            stop_loss_pct: Stop loss percentage (e.g., 0.10 = 10% loss)
            take_profit_pct: Take profit percentage (e.g., 0.20 = 20% gain)

        Returns:
            BacktestResult with all metrics
        """
        print("\n⚠️  IMPORTANT: This is a HYPOTHETICAL backtest!")
        print("Real backtesting requires historical price data.")
        print("This simulation uses probability models to estimate outcomes.\n")

        trades = []

        for symbol, coin_data in recommendations:
            # Get current data
            entry_price = coin_data['price']
            entry_time = datetime.now()

            # Position sizing (use Kelly if available, otherwise conservative)
            position_size = coin_data.get('kelly_position_size', 0.05)  # 5% default

            # Calculate TP/SL levels
            sl_price = entry_price * (1 - stop_loss_pct)
            tp_price = entry_price * (1 + take_profit_pct)

            # Create trade
            trade = Trade(symbol, entry_price, entry_time, position_size, sl_price, tp_price)

            # SIMULATE OUTCOME based on coin characteristics
            # This is where historical data would be used in real backtesting
            outcome = self._simulate_trade_outcome(coin_data, stop_loss_pct, take_profit_pct)

            exit_time = entry_time + timedelta(hours=hold_period_hours)
            trade.close_trade(outcome['exit_price'], exit_time, outcome['reason'])

            trades.append(trade)

        self.trades = trades
        return BacktestResult(trades, self.initial_capital)

    def _simulate_trade_outcome(self, coin_data: Dict, sl_pct: float, tp_pct: float) -> Dict:
        """Simulate trade outcome based on coin characteristics

        This is a PROBABILISTIC MODEL - not real data!
        """
        entry_price = coin_data['price']
        volatility = abs(coin_data['change_24h'])
        momentum = coin_data['change_24h']

        # Estimate probability of success based on indicators
        base_prob = 0.5  # 50% baseline

        # Adjust based on momentum
        if momentum > 10:
            base_prob += 0.15
        elif momentum > 5:
            base_prob += 0.10
        elif momentum < -10:
            base_prob -= 0.15

        # Adjust based on scores
        enhanced_score = coin_data.get('enhanced_score', coin_data.get('composite_score', 50))
        if enhanced_score > 75:
            base_prob += 0.10
        elif enhanced_score > 60:
            base_prob += 0.05

        # Penalize wash trading suspects
        if coin_data.get('wash_trading_suspicious', False):
            base_prob -= 0.20

        # Clip probability
        win_prob = np.clip(base_prob, 0.2, 0.8)

        # Simulate outcome
        if np.random.random() < win_prob:
            # Win - but not always full TP
            if np.random.random() < 0.7:
                # Hit full take profit
                exit_price = entry_price * (1 + tp_pct)
                reason = "Take Profit"
            else:
                # Partial profit
                partial_gain = np.random.uniform(0.05, tp_pct)
                exit_price = entry_price * (1 + partial_gain)
                reason = "Partial Profit"
        else:
            # Loss
            if np.random.random() < 0.6:
                # Hit stop loss
                exit_price = entry_price * (1 - sl_pct)
                reason = "Stop Loss"
            else:
                # Partial loss
                partial_loss = np.random.uniform(0.02, sl_pct)
                exit_price = entry_price * (1 - partial_loss)
                reason = "Partial Loss"

        return {
            'exit_price': exit_price,
            'reason': reason
        }

    def run_monte_carlo_simulation(self, recommendations: List[Tuple[str, Dict]],
                                  num_simulations: int = 100,
                                  hold_period_hours: int = 24,
                                  stop_loss_pct: float = 0.10,
                                  take_profit_pct: float = 0.20) -> Dict:
        """Run Monte Carlo simulation to estimate strategy robustness

        Args:
            recommendations: Trading recommendations to test
            num_simulations: Number of simulation runs
            hold_period_hours: Hold period for each trade
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage

        Returns:
            Dictionary with simulation statistics
        """
        print(f"\n🎲 Running {num_simulations} Monte Carlo simulations...")

        results = []
        for i in range(num_simulations):
            result = self.simulate_recommendation_strategy(
                recommendations,
                hold_period_hours,
                stop_loss_pct,
                take_profit_pct
            )
            results.append({
                'win_rate': result.win_rate,
                'net_profit': result.net_profit,
                'sharpe_ratio': result.sharpe_ratio,
                'max_drawdown': result.max_drawdown,
                'profit_factor': result.profit_factor
            })

        # Calculate statistics
        df_results = pd.DataFrame(results)

        monte_carlo_stats = {
            'mean_win_rate': df_results['win_rate'].mean(),
            'std_win_rate': df_results['win_rate'].std(),
            'mean_net_profit': df_results['net_profit'].mean(),
            'std_net_profit': df_results['net_profit'].std(),
            'mean_sharpe': df_results['sharpe_ratio'].mean(),
            'profitable_simulations_pct': (df_results['net_profit'] > 0).mean() * 100,
            'worst_case_profit': df_results['net_profit'].min(),
            'best_case_profit': df_results['net_profit'].max(),
            'median_profit': df_results['net_profit'].median(),
        }

        # Print summary
        print("\n" + "=" * 80)
        print("MONTE CARLO SIMULATION RESULTS")
        print("=" * 80)
        print(f"\nSimulations:              {num_simulations}")
        print(f"Mean Win Rate:            {monte_carlo_stats['mean_win_rate'] * 100:.1f}% ± {monte_carlo_stats['std_win_rate'] * 100:.1f}%")
        print(f"Mean Net Profit:          {monte_carlo_stats['mean_net_profit'] * 100:+.2f}% ± {monte_carlo_stats['std_net_profit'] * 100:.2f}%")
        print(f"Mean Sharpe Ratio:        {monte_carlo_stats['mean_sharpe']:.2f}")
        print(f"Profitable Simulations:   {monte_carlo_stats['profitable_simulations_pct']:.1f}%")
        print(f"\nProfit Range:")
        print(f"  Best Case:              {monte_carlo_stats['best_case_profit'] * 100:+.2f}%")
        print(f"  Median:                 {monte_carlo_stats['median_profit'] * 100:+.2f}%")
        print(f"  Worst Case:             {monte_carlo_stats['worst_case_profit'] * 100:+.2f}%")

        if monte_carlo_stats['profitable_simulations_pct'] > 70:
            print(f"\n✅ ROBUST: >70% of simulations were profitable")
        elif monte_carlo_stats['profitable_simulations_pct'] > 50:
            print(f"\n⚠️  MODERATE: 50-70% of simulations were profitable")
        else:
            print(f"\n❌ WEAK: <50% of simulations were profitable - HIGH RISK")

        print("=" * 80 + "\n")

        return monte_carlo_stats
