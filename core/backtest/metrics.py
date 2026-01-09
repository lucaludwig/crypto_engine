"""Performance Metrics Calculator

Calculates all required KPIs for strategy validation:
- Expectancy per Trade
- Profit Factor
- Max Drawdown
- Sharpe Ratio
- Win Rate
- Average Win/Loss
- Consecutive Wins/Losses

TARGET METRICS (Pre-Live Requirements):
- Expectancy per Trade: > $0
- Profit Factor: > 1.8
- Max Drawdown: < 25%
- Sharpe Ratio: > 1.5
- OOS Performance: < 30% drop vs IS
"""
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime


class MetricsCalculator:
    """Calculates comprehensive performance metrics

    Uses industry-standard formulas for all metrics.
    """

    def __init__(self):
        """Initialize metrics calculator"""
        pass

    def calculate_expectancy(self, trades: List[Dict]) -> float:
        """Calculate expectancy per trade (average P&L per trade)

        Formula: Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)

        Args:
            trades: List of trade dicts with 'pnl' key

        Returns:
            Expectancy in $ per trade
        """
        if not trades:
            return 0.0

        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [abs(t['pnl']) for t in trades if t['pnl'] <= 0]

        if not wins and not losses:
            return 0.0

        win_rate = len(wins) / len(trades)
        loss_rate = 1 - win_rate

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0

        expectancy = (win_rate * avg_win) - (loss_rate * avg_loss)

        return expectancy

    def calculate_profit_factor(self, trades: List[Dict]) -> float:
        """Calculate profit factor

        Formula: Profit Factor = Gross Profit / Gross Loss

        Args:
            trades: List of trade dicts

        Returns:
            Profit Factor (>1 = profitable, >1.8 = target)
        """
        if not trades:
            return 0.0

        gross_profit = sum(t['pnl'] for t in trades if t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades if t['pnl'] <= 0))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict:
        """Calculate maximum drawdown

        Args:
            equity_curve: List of equity values over time

        Returns:
            Dict with max DD %, max DD $, peak, trough
        """
        if not equity_curve:
            return {'max_dd_pct': 0.0, 'max_dd_value': 0.0}

        equity = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100

        max_dd_pct = abs(np.min(drawdown))
        max_dd_idx = np.argmin(drawdown)

        # Find peak before max DD
        peak_idx = np.argmax(equity[:max_dd_idx+1]) if max_dd_idx > 0 else 0
        peak_value = equity[peak_idx]
        trough_value = equity[max_dd_idx]
        max_dd_value = peak_value - trough_value

        return {
            'max_dd_pct': max_dd_pct,
            'max_dd_value': max_dd_value,
            'peak_value': peak_value,
            'trough_value': trough_value,
            'peak_idx': peak_idx,
            'trough_idx': max_dd_idx
        }

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.0,
        periods_per_year: int = 252
    ) -> float:
        """Calculate Sharpe Ratio

        Formula: Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns
        Annualized.

        Args:
            returns: List of returns (as decimals, e.g., 0.02 for 2%)
            risk_free_rate: Annual risk-free rate (default: 0)
            periods_per_year: Trading periods per year (252 for daily)

        Returns:
            Annualized Sharpe Ratio
        """
        if not returns or len(returns) < 2:
            return 0.0

        returns_arr = np.array(returns)

        if np.std(returns_arr) == 0:
            return 0.0

        # Calculate excess returns
        excess_returns = returns_arr - (risk_free_rate / periods_per_year)

        # Sharpe ratio
        sharpe = np.mean(excess_returns) / np.std(excess_returns)

        # Annualize
        sharpe_annual = sharpe * np.sqrt(periods_per_year)

        return sharpe_annual

    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate

        Args:
            trades: List of trades

        Returns:
            Win rate as percentage (0-100)
        """
        if not trades:
            return 0.0

        wins = sum(1 for t in trades if t['pnl'] > 0)
        return (wins / len(trades)) * 100

    def calculate_avg_win_loss(self, trades: List[Dict]) -> Dict:
        """Calculate average win and loss

        Args:
            trades: List of trades

        Returns:
            Dict with avg_win, avg_loss, avg_win_pct, avg_loss_pct
        """
        if not trades:
            return {'avg_win': 0, 'avg_loss': 0, 'avg_win_pct': 0, 'avg_loss_pct': 0}

        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] <= 0]

        win_pcts = [t['pnl_pct'] for t in trades if t['pnl'] > 0]
        loss_pcts = [t['pnl_pct'] for t in trades if t['pnl'] <= 0]

        return {
            'avg_win': np.mean(wins) if wins else 0,
            'avg_loss': np.mean(losses) if losses else 0,
            'avg_win_pct': np.mean(win_pcts) if win_pcts else 0,
            'avg_loss_pct': np.mean(loss_pcts) if loss_pcts else 0
        }

    def calculate_consecutive_wins_losses(self, trades: List[Dict]) -> Dict:
        """Calculate max consecutive wins/losses

        Args:
            trades: List of trades

        Returns:
            Dict with max consecutive wins and losses
        """
        if not trades:
            return {'max_consecutive_wins': 0, 'max_consecutive_losses': 0}

        # Get win/loss sequence
        sequence = [1 if t['pnl'] > 0 else -1 for t in trades]

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for result in sequence:
            if result == 1:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return {
            'max_consecutive_wins': max_wins,
            'max_consecutive_losses': max_losses
        }

    def calculate_all_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[float],
        initial_capital: float
    ) -> Dict:
        """Calculate all performance metrics

        Args:
            trades: List of completed trades
            equity_curve: Equity curve over time
            initial_capital: Starting capital

        Returns:
            Complete metrics dict
        """
        if not trades:
            return self._empty_metrics()

        # Calculate daily returns for Sharpe
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            returns.append(ret)

        # Calculate all metrics
        expectancy = self.calculate_expectancy(trades)
        profit_factor = self.calculate_profit_factor(trades)
        max_dd = self.calculate_max_drawdown(equity_curve)
        sharpe = self.calculate_sharpe_ratio(returns)
        win_rate = self.calculate_win_rate(trades)
        avg_stats = self.calculate_avg_win_loss(trades)
        consec = self.calculate_consecutive_wins_losses(trades)

        # Summary stats
        total_trades = len(trades)
        wins = sum(1 for t in trades if t['pnl'] > 0)
        losses = total_trades - wins

        total_pnl = sum(t['pnl'] for t in trades)
        total_return_pct = (total_pnl / initial_capital) * 100

        final_capital = equity_curve[-1] if equity_curve else initial_capital

        return {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'expectancy': expectancy,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'avg_win': avg_stats['avg_win'],
            'avg_loss': avg_stats['avg_loss'],
            'avg_win_pct': avg_stats['avg_win_pct'],
            'avg_loss_pct': avg_stats['avg_loss_pct'],
            'max_dd_pct': max_dd['max_dd_pct'],
            'max_dd_value': max_dd['max_dd_value'],
            'sharpe_ratio': sharpe,
            'max_consecutive_wins': consec['max_consecutive_wins'],
            'max_consecutive_losses': consec['max_consecutive_losses'],
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'equity_curve': equity_curve
        }

    def _empty_metrics(self) -> Dict:
        """Return empty metrics dict"""
        return {
            'total_trades': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'expectancy': 0,
            'profit_factor': 0,
            'total_pnl': 0,
            'total_return_pct': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_win_pct': 0,
            'avg_loss_pct': 0,
            'max_dd_pct': 0,
            'max_dd_value': 0,
            'sharpe_ratio': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'initial_capital': 0,
            'final_capital': 0
        }

    def passes_validation(self, metrics: Dict) -> Dict:
        """Check if metrics pass validation requirements

        TARGET METRICS:
        - Expectancy > 0
        - Profit Factor > 1.8
        - Max Drawdown < 25%
        - Sharpe Ratio > 1.5

        Args:
            metrics: Metrics dict from calculate_all_metrics

        Returns:
            Dict with pass/fail for each requirement
        """
        checks = {
            'expectancy_positive': metrics['expectancy'] > 0,
            'profit_factor_target': metrics['profit_factor'] > 1.8,
            'max_dd_acceptable': metrics['max_dd_pct'] < 25.0,
            'sharpe_ratio_target': metrics['sharpe_ratio'] > 1.5,
            'all_passed': False
        }

        checks['all_passed'] = all([
            checks['expectancy_positive'],
            checks['profit_factor_target'],
            checks['max_dd_acceptable'],
            checks['sharpe_ratio_target']
        ])

        return checks

    def compare_is_oos(self, is_metrics: Dict, oos_metrics: Dict) -> Dict:
        """Compare In-Sample vs Out-of-Sample performance

        OOS must not drop > 30% vs IS

        Args:
            is_metrics: In-Sample metrics
            oos_metrics: Out-of-Sample metrics

        Returns:
            Comparison dict with degradation percentages
        """
        if is_metrics['expectancy'] == 0:
            expectancy_drop = 100.0
        else:
            expectancy_drop = ((is_metrics['expectancy'] - oos_metrics['expectancy']) / abs(is_metrics['expectancy'])) * 100

        if is_metrics['profit_factor'] == 0:
            pf_drop = 100.0
        else:
            pf_drop = ((is_metrics['profit_factor'] - oos_metrics['profit_factor']) / is_metrics['profit_factor']) * 100

        sharpe_drop = ((is_metrics['sharpe_ratio'] - oos_metrics['sharpe_ratio']) / abs(is_metrics['sharpe_ratio'])) * 100 if is_metrics['sharpe_ratio'] != 0 else 100.0

        # Overall degradation (average of key metrics)
        overall_drop = np.mean([expectancy_drop, pf_drop, sharpe_drop])

        return {
            'expectancy_drop_pct': expectancy_drop,
            'profit_factor_drop_pct': pf_drop,
            'sharpe_drop_pct': sharpe_drop,
            'overall_drop_pct': overall_drop,
            'overfitted': overall_drop > 30.0,
            'acceptable': overall_drop <= 30.0
        }
