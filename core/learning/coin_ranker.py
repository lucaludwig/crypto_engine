"""Coin Ranker - Learning-Based Coin Prioritization

ALLOWED:
✅ Rank coins by historical win rate
✅ Adjust coin priority (whitelist better performers)
✅ Track which coins produce best results

NOT ALLOWED:
❌ Change setup parameters (BB, ATR, etc.)
❌ Change risk parameters
❌ Change entry/exit logic

Minimum 100 trades required before learning activates.
"""
import json
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import numpy as np


class CoinRanker:
    """Ranks coins based on historical performance

    Tracks:
    - Win rate per coin
    - Average profit per coin
    - Total trades per coin
    - Expectancy per coin

    Uses data to prioritize coins that historically perform better.
    """

    MIN_TRADES_FOR_LEARNING = 100  # Need 100 trades before learning kicks in
    MIN_TRADES_PER_COIN = 3  # Need 3 trades per coin for ranking

    def __init__(self, state_file: str = "coin_ranker_state.json"):
        """Initialize coin ranker

        Args:
            state_file: Path to state persistence file
        """
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                print(f"Warning: Could not load coin ranker state: {e}")

        # Default state
        return {
            'coins': {},  # {symbol: {wins, losses, total_profit_pct, trades}}
            'total_trades': 0
        }

    def _save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save coin ranker state: {e}")

    def record_trade(self, symbol: str, profit_pct: float):
        """Record a trade result

        Args:
            symbol: Trading symbol
            profit_pct: Profit/loss percentage
        """
        if symbol not in self.state['coins']:
            self.state['coins'][symbol] = {
                'wins': 0,
                'losses': 0,
                'total_profit_pct': 0.0,
                'trades': 0
            }

        coin_data = self.state['coins'][symbol]

        # Update stats
        if profit_pct > 0:
            coin_data['wins'] += 1
        else:
            coin_data['losses'] += 1

        coin_data['total_profit_pct'] += profit_pct
        coin_data['trades'] += 1

        self.state['total_trades'] += 1

        self._save_state()

    def get_coin_stats(self, symbol: str) -> Optional[Dict]:
        """Get statistics for a coin

        Args:
            symbol: Trading symbol

        Returns:
            Stats dict or None if no data
        """
        if symbol not in self.state['coins']:
            return None

        coin_data = self.state['coins'][symbol]

        if coin_data['trades'] == 0:
            return None

        win_rate = coin_data['wins'] / coin_data['trades']
        avg_profit = coin_data['total_profit_pct'] / coin_data['trades']
        expectancy = avg_profit  # Simplified expectancy

        return {
            'symbol': symbol,
            'trades': coin_data['trades'],
            'wins': coin_data['wins'],
            'losses': coin_data['losses'],
            'win_rate': win_rate,
            'avg_profit_pct': avg_profit,
            'expectancy': expectancy,
            'total_profit_pct': coin_data['total_profit_pct']
        }

    def is_learning_active(self) -> bool:
        """Check if learning has enough data to be active

        Returns:
            True if we have enough trades for learning
        """
        return self.state['total_trades'] >= self.MIN_TRADES_FOR_LEARNING

    def get_coin_score(self, symbol: str) -> float:
        """Get priority score for a coin (0-100)

        Higher score = higher priority

        Args:
            symbol: Trading symbol

        Returns:
            Priority score
        """
        if not self.is_learning_active():
            return 50.0  # Neutral score if not enough data

        stats = self.get_coin_stats(symbol)

        if stats is None or stats['trades'] < self.MIN_TRADES_PER_COIN:
            return 50.0  # Neutral score for new coins

        # Calculate score based on:
        # 1. Win rate (0-40 points)
        # 2. Expectancy (0-60 points)

        win_rate_score = stats['win_rate'] * 40
        expectancy_score = min(60, max(0, 30 + stats['expectancy'] * 3))  # Centered at 30

        score = win_rate_score + expectancy_score

        return max(0, min(100, score))

    def rank_coins(self, symbols: List[str]) -> List[Tuple[str, float]]:
        """Rank a list of coins by priority

        Args:
            symbols: List of trading symbols

        Returns:
            List of (symbol, score) tuples, sorted by score descending
        """
        scored_coins = []

        for symbol in symbols:
            score = self.get_coin_score(symbol)
            scored_coins.append((symbol, score))

        # Sort by score descending
        scored_coins.sort(key=lambda x: x[1], reverse=True)

        return scored_coins

    def get_top_coins(self, symbols: List[str], n: int = 10) -> List[str]:
        """Get top N coins by priority

        Args:
            symbols: List of candidate symbols
            n: Number of top coins to return

        Returns:
            List of top symbols
        """
        ranked = self.rank_coins(symbols)
        return [symbol for symbol, score in ranked[:n]]

    def should_prioritize_coin(self, symbol: str) -> bool:
        """Check if coin should be prioritized (score > 60)

        Args:
            symbol: Trading symbol

        Returns:
            True if coin should be prioritized
        """
        score = self.get_coin_score(symbol)
        return score > 60.0

    def get_performance_summary(self) -> Dict:
        """Get overall performance summary

        Returns:
            Summary statistics
        """
        if self.state['total_trades'] == 0:
            return {
                'total_trades': 0,
                'learning_active': False,
                'coins_tracked': 0
            }

        # Calculate overall stats
        all_stats = []
        for symbol in self.state['coins']:
            stats = self.get_coin_stats(symbol)
            if stats and stats['trades'] >= self.MIN_TRADES_PER_COIN:
                all_stats.append(stats)

        # Sort by expectancy
        all_stats.sort(key=lambda x: x['expectancy'], reverse=True)

        best_performers = all_stats[:10] if len(all_stats) >= 10 else all_stats
        worst_performers = all_stats[-10:] if len(all_stats) >= 10 else []

        return {
            'total_trades': self.state['total_trades'],
            'learning_active': self.is_learning_active(),
            'coins_tracked': len(self.state['coins']),
            'coins_with_data': len(all_stats),
            'best_performers': [
                {
                    'symbol': s['symbol'],
                    'trades': s['trades'],
                    'win_rate': s['win_rate'],
                    'expectancy': s['expectancy']
                }
                for s in best_performers
            ],
            'worst_performers': [
                {
                    'symbol': s['symbol'],
                    'trades': s['trades'],
                    'win_rate': s['win_rate'],
                    'expectancy': s['expectancy']
                }
                for s in worst_performers
            ]
        }
