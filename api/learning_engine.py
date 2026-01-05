#!/usr/bin/env python3
"""Self-Learning Trading Engine - Learns from past trades to improve future decisions

Features:
- Pattern recognition: Identifies what works and what doesn't
- Adaptive filtering: Adjusts entry criteria based on historical performance
- Performance insights: Generates actionable recommendations
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class TradingLearningEngine:
    """Machine learning engine that analyzes trade history and optimizes strategy"""

    def __init__(self, trades_file: Path = None, load_instant_xp: bool = True):
        """Initialize learning engine

        Args:
            trades_file: Path to trades log JSON file
            load_instant_xp: If True, learn from historical trades immediately (INSTANT XP!)
        """
        if trades_file is None:
            trades_file = Path(__file__).parent.parent / "trades_log.json"

        self.trades_file = trades_file
        self.learnings_file = Path(__file__).parent.parent / "learnings.json"

        # Load data
        self.trades = self._load_trades()
        self.learnings = self._load_learnings()

        # WALK-FORWARD TESTING (ANTI-OVERFITTING!)
        self.freeze_mode = self.learnings.get('freeze_mode', False)
        self.frozen_filters = self.learnings.get('frozen_filters', None)
        self.frozen_weights = self.learnings.get('frozen_weights', None)
        self.trades_in_current_period = self.learnings.get('trades_in_current_period', 0)
        self.learning_period_length = 10  # Learn for 10 trades
        self.validation_period_length = 10  # Validate for 10 trades

        # A/B TESTING TRACKING
        self.ab_test_results = self.learnings.get('ab_test_results', {
            'adaptive_wins': 0,
            'adaptive_losses': 0,
            'default_would_win': 0,
            'default_would_lose': 0
        })

        # INSTANT XP: Learn from historical trades (GAME CHANGER!)
        if load_instant_xp and not self.learnings.get('instant_xp_loaded', False):
            self._load_instant_xp()

    def _load_trades(self) -> List[Dict]:
        """Load trade history"""
        if not self.trades_file.exists():
            return []

        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def _load_learnings(self) -> Dict:
        """Load previous learnings"""
        if not self.learnings_file.exists():
            return {
                'version': '1.0',
                'last_updated': None,
                'insights': {},
                'adaptive_filters': {
                    'min_score': 65,
                    'max_24h_change': 15,
                    'min_market_cap': 30_000_000,
                    'min_volume_change': 30
                },
                'patterns': {
                    'winners': {},
                    'losers': {}
                }
            }

        try:
            with open(self.learnings_file, 'r') as f:
                return json.load(f)
        except:
            return self._load_learnings()  # Return default

    def _save_learnings(self):
        """Save learnings to file"""
        self.learnings['last_updated'] = datetime.now().isoformat()

        # Save walk-forward state
        self.learnings['freeze_mode'] = self.freeze_mode
        self.learnings['frozen_filters'] = self.frozen_filters
        self.learnings['frozen_weights'] = self.frozen_weights
        self.learnings['trades_in_current_period'] = self.trades_in_current_period

        # Save A/B test results
        self.learnings['ab_test_results'] = self.ab_test_results

        with open(self.learnings_file, 'w') as f:
            json.dump(self.learnings, f, indent=2)

    def _load_instant_xp(self):
        """INSTANT XP: Learn from all historical trades immediately!

        GAME CHANGER - Bot starts with experience instead of at zero!
        """
        if not self.trades:
            print("📚 No historical trades found for Instant XP")
            return

        print(f"\n🧠 INSTANT XP LOADING...")
        print(f"   Found {len(self.trades)} historical trades")

        # Process only completed trades (BUY/SELL pairs with pnl_pct)
        completed_trades = [t for t in self.trades if 'pnl_pct' in t and t.get('pnl_pct') != 0]

        if not completed_trades:
            print("   No completed trades with P&L data found")
            self.learnings['instant_xp_loaded'] = True
            self._save_learnings()
            return

        # Temporarily disable walk-forward counter increments
        original_trades_count = self.trades_in_current_period

        learned_count = 0
        for trade in completed_trades:
            # Skip if already processed (has timestamp in patterns)
            symbol = trade.get('symbol', 'UNKNOWN')

            # Extract coin data if available (from newer trade logs)
            coin_data = None
            if 'coin_data' in trade:
                coin_data = trade['coin_data']
            elif all(k in trade for k in ['market_cap', 'enhanced_score', 'change_24h']):
                # Reconstruct coin_data from trade fields
                coin_data = {
                    'market_cap': trade.get('market_cap', 0),
                    'enhanced_score': trade.get('enhanced_score', 0),
                    'change_24h': trade.get('change_24h', 0),
                    'volume_change_24h': trade.get('volume_change_24h', 0),
                    'wash_trading_confidence': trade.get('wash_trading_confidence', 0)
                }

            # Analyze trade (this updates patterns)
            pnl_pct = trade['pnl_pct']
            entry_price = trade.get('price', 0)
            if entry_price > 0 and pnl_pct != 0:
                exit_price = entry_price * (1 + pnl_pct / 100)
                exit_type = trade.get('exit_type', 'FULL')

                # Call analyze_trade_outcome BUT skip walk-forward updates
                self.trades_in_current_period = original_trades_count
                self.analyze_trade_outcome(
                    symbol=symbol,
                    buy_price=entry_price,
                    sell_price=exit_price,
                    coin_data=coin_data,
                    exit_type=exit_type
                )
                learned_count += 1

        # Restore walk-forward counter
        self.trades_in_current_period = original_trades_count

        # Mark as loaded
        self.learnings['instant_xp_loaded'] = True
        self._save_learnings()

        print(f"   ✅ Learned from {learned_count} completed trades!")
        print(f"   🧠 Bot now has instant experience!\n")

    def analyze_trade_outcome(self, symbol: str, buy_price: float, sell_price: float,
                             coin_data: Dict = None, exit_type: str = 'FULL') -> Dict:
        """Analyze a completed trade and extract learnings

        Args:
            symbol: Trading pair symbol
            buy_price: Entry price
            sell_price: Exit price
            coin_data: Coin metrics at time of purchase
            exit_type: Exit type ('FULL', 'PARTIAL', 'TP', 'SL', 'TIME_EXIT', 'TRAILING')

        Returns:
            Analysis results
        """
        pnl_pct = ((sell_price - buy_price) / buy_price) * 100
        is_winner = pnl_pct > 0

        # Weight partial exits at 50% (since only half position closed)
        weight = 0.5 if exit_type == 'PARTIAL' else 1.0

        analysis = {
            'symbol': symbol,
            'pnl_pct': pnl_pct,
            'is_winner': is_winner,
            'exit_type': exit_type,
            'weight': weight,
            'timestamp': datetime.now().isoformat()
        }

        # Store coin characteristics for pattern recognition
        if coin_data:
            characteristics = {
                'market_cap': coin_data.get('market_cap', 0),
                'volume_24h': coin_data.get('volume_24h', 0),
                'change_24h': coin_data.get('change_24h', 0),
                'volume_change_24h': coin_data.get('volume_change_24h', 0),
                'enhanced_score': coin_data.get('enhanced_score', 0),
                'wash_trading_confidence': coin_data.get('wash_trading_confidence', 0)
            }

            analysis['characteristics'] = characteristics

            # Store in patterns
            pattern_type = 'winners' if is_winner else 'losers'
            if symbol not in self.learnings['patterns'][pattern_type]:
                self.learnings['patterns'][pattern_type][symbol] = []

            self.learnings['patterns'][pattern_type][symbol].append({
                'pnl_pct': pnl_pct,
                'exit_type': exit_type,
                'weight': weight,
                'characteristics': characteristics,
                'timestamp': datetime.now().isoformat()
            })

            # Save learnings
            self._save_learnings()

            # A/B TEST: Track what default strategy would have done
            self.add_ab_test_result(is_winner, coin_data)

        # WALK-FORWARD: Increment trade counter and check for period switch
        self.trades_in_current_period += 1

        if self.freeze_mode:
            # In validation period
            if self.trades_in_current_period >= self.validation_period_length:
                print(f"\n🔄 VALIDATION PERIOD COMPLETE ({self.validation_period_length} trades)")
                print(f"🧠 Switching to LEARNING MODE...")
                self.freeze_mode = False
                self.frozen_filters = None
                self.frozen_weights = None
                self.trades_in_current_period = 0
                self._save_learnings()
        else:
            # In learning period
            if self.trades_in_current_period >= self.learning_period_length:
                print(f"\n🔄 LEARNING PERIOD COMPLETE ({self.learning_period_length} trades)")
                print(f"❄️  Freezing parameters for VALIDATION...")
                # Freeze current adaptive filters and weights
                self.frozen_filters = self.learnings['adaptive_filters'].copy()
                if 'adaptive_weights' in self.learnings:
                    self.frozen_weights = self.learnings['adaptive_weights']['weights'].copy()
                self.freeze_mode = True
                self.trades_in_current_period = 0
                self._save_learnings()

        return analysis

    def get_pattern_insights(self) -> Dict:
        """Analyze patterns to identify what works

        Returns:
            Dict with insights about winners vs losers
        """
        winners = self.learnings['patterns']['winners']
        losers = self.learnings['patterns']['losers']

        insights = {
            'total_winners': sum(len(trades) for trades in winners.values()),
            'total_losers': sum(len(trades) for trades in losers.values()),
            'winner_characteristics': {},
            'loser_characteristics': {},
            'recommendations': []
        }

        if not winners and not losers:
            insights['recommendations'].append("No trades yet - learning will start after first exits")
            return insights

        # Aggregate characteristics for winners
        winner_data = defaultdict(list)
        for symbol, trades in winners.items():
            for trade in trades:
                chars = trade.get('characteristics', {})
                for key, value in chars.items():
                    if isinstance(value, (int, float)):
                        winner_data[key].append(value)

        # Aggregate characteristics for losers
        loser_data = defaultdict(list)
        for symbol, trades in losers.items():
            for trade in trades:
                chars = trade.get('characteristics', {})
                for key, value in chars.items():
                    if isinstance(value, (int, float)):
                        loser_data[key].append(value)

        # Calculate averages
        for key, values in winner_data.items():
            if values:
                insights['winner_characteristics'][key] = {
                    'avg': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values)
                }

        for key, values in loser_data.items():
            if values:
                insights['loser_characteristics'][key] = {
                    'avg': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values)
                }

        # Generate recommendations based on patterns
        insights['recommendations'] = self._generate_recommendations(
            insights['winner_characteristics'],
            insights['loser_characteristics']
        )

        return insights

    def _generate_recommendations(self, winners: Dict, losers: Dict) -> List[str]:
        """Generate actionable recommendations based on patterns

        Args:
            winners: Winner characteristics
            losers: Loser characteristics

        Returns:
            List of recommendations
        """
        recommendations = []

        # Compare market cap
        if 'market_cap' in winners and 'market_cap' in losers:
            winner_mcap = winners['market_cap']['median']
            loser_mcap = losers['market_cap']['median']

            if winner_mcap > loser_mcap * 1.5:
                recommendations.append(
                    f"🎯 Winners have higher market cap (${winner_mcap/1e6:.1f}M vs ${loser_mcap/1e6:.1f}M). "
                    f"Consider increasing min market cap filter."
                )
            elif loser_mcap > winner_mcap * 1.5:
                recommendations.append(
                    f"🎯 Losers have higher market cap. Consider lowering market cap filter to find gems."
                )

        # Compare scores
        if 'enhanced_score' in winners and 'enhanced_score' in losers:
            winner_score = winners['enhanced_score']['median']
            loser_score = losers['enhanced_score']['median']

            if winner_score > loser_score + 5:
                recommendations.append(
                    f"🎯 Winners have higher scores ({winner_score:.0f} vs {loser_score:.0f}). "
                    f"Consider increasing min_score filter."
                )

        # Compare 24h change at entry
        if 'change_24h' in winners and 'change_24h' in losers:
            winner_change = winners['change_24h']['median']
            loser_change = losers['change_24h']['median']

            if loser_change > winner_change + 3:
                recommendations.append(
                    f"⚠️ Losers were bought after bigger pumps ({loser_change:+.1f}% vs {winner_change:+.1f}%). "
                    f"Lower the max_24h_change filter (currently 15%)."
                )

        # Volume change comparison
        if 'volume_change_24h' in winners and 'volume_change_24h' in losers:
            winner_vol = winners['volume_change_24h']['median']
            loser_vol = losers['volume_change_24h']['median']

            if winner_vol > loser_vol * 1.5:
                recommendations.append(
                    f"🎯 Winners have stronger volume momentum ({winner_vol:.0f}% vs {loser_vol:.0f}%). "
                    f"Consider increasing min_volume_change filter."
                )

        # Wash trading pattern
        if 'wash_trading_confidence' in winners and 'wash_trading_confidence' in losers:
            winner_wash = winners['wash_trading_confidence']['median']
            loser_wash = losers['wash_trading_confidence']['median']

            if loser_wash > winner_wash + 10:
                recommendations.append(
                    f"⚠️ Losers have higher wash trading ({loser_wash:.0f}% vs {winner_wash:.0f}%). "
                    f"Tighten wash trading filter (<{int(winner_wash + 5)}%)."
                )

        # Market cap sweet spot analysis
        if 'market_cap' in winners and len(winners['market_cap']) > 0:
            winner_mcap_range = (winners['market_cap']['min'], winners['market_cap']['max'])
            recommendations.append(
                f"💎 Winner market cap range: ${winner_mcap_range[0]/1e6:.0f}M - ${winner_mcap_range[1]/1e6:.0f}M. "
                f"Focus on this range for best results."
            )

        if not recommendations:
            recommendations.append("✅ No clear patterns yet - need more trades for insights.")

        return recommendations

    def get_adaptive_filters(self) -> Dict:
        """Get current adaptive filters based on learnings

        WALK-FORWARD: Returns frozen filters during validation period!

        Returns:
            Dict with recommended filter values
        """
        # WALK-FORWARD: If in freeze mode, return frozen filters
        if self.freeze_mode and self.frozen_filters:
            print(f"❄️  Using FROZEN filters (Validation Period: Trade {self.trades_in_current_period}/{self.validation_period_length})")
            return self.frozen_filters.copy()

        insights = self.get_pattern_insights()
        filters = self.learnings['adaptive_filters'].copy()

        # Adjust filters based on insights
        winners = insights.get('winner_characteristics', {})
        losers = insights.get('loser_characteristics', {})

        # Adjust min_score if we have data
        if 'enhanced_score' in winners and 'enhanced_score' in losers:
            winner_score = winners['enhanced_score']['median']
            loser_score = losers['enhanced_score']['median']

            if winner_score > loser_score + 5:
                # Winners have significantly higher scores - increase threshold
                new_min_score = int((winner_score + loser_score) / 2)
                filters['min_score'] = max(filters['min_score'], new_min_score)

        # Adjust max_24h_change
        if 'change_24h' in winners and 'change_24h' in losers:
            loser_change = losers['change_24h']['median']
            winner_change = winners['change_24h']['median']

            if loser_change > winner_change + 3:
                # Losers were bought after bigger pumps - tighten filter
                filters['max_24h_change'] = min(filters['max_24h_change'], int(winner_change + 2))

        self.learnings['adaptive_filters'] = filters
        self._save_learnings()

        return filters

    def should_trade_coin(self, coin_data: Dict) -> Tuple[bool, str]:
        """Check if coin should be traded based on BEHAVIOR PATTERNS (not symbol!)

        This is crucial for shitcoins - we learn from patterns, not coin names!

        Args:
            coin_data: Coin characteristics (market_cap, score, change_24h, etc.)

        Returns:
            (should_trade, reason)
        """
        # Shitcoins are often NEW - focus on CURRENT behavior, not history!

        insights = self.get_pattern_insights()

        # If we have enough data, check against loser patterns
        if insights['total_losers'] >= 3:
            losers = insights.get('loser_characteristics', {})

            # Pattern: Losers often have specific characteristics
            # Check if this coin matches loser patterns

            # Example: If losers typically had change_24h > 15%
            if 'change_24h' in losers and 'change_24h' in coin_data:
                loser_avg_change = losers['change_24h']['avg']
                coin_change = coin_data['change_24h']

                # If this coin has similar pump to avg loser, be cautious
                if loser_avg_change > 10 and coin_change > loser_avg_change * 0.9:
                    return False, f"Pattern match: Similar pump to avg loser ({coin_change:.1f}% vs {loser_avg_change:.1f}%)"

            # Check score pattern
            if 'enhanced_score' in losers and 'enhanced_score' in coin_data:
                loser_avg_score = losers['enhanced_score']['avg']
                coin_score = coin_data['enhanced_score']

                # If this coin has similar score to avg loser
                if coin_score < loser_avg_score + 5:
                    return False, f"Pattern match: Score similar to avg loser ({coin_score:.0f} vs {loser_avg_score:.0f})"

        return True, "OK - Behavior pattern acceptable"

    def add_ab_test_result(self, is_winner: bool, coin_data: Dict = None):
        """Track A/B test results: Would default strategy have done better?

        Args:
            is_winner: Whether the trade was a winner (using adaptive strategy)
            coin_data: Coin characteristics at entry
        """
        if not coin_data:
            return

        # Default strategy filters (fixed, not adaptive)
        default_min_score = 65
        default_max_24h_change = 15
        default_min_market_cap = 30_000_000
        default_min_volume_change = 30

        # Check if DEFAULT strategy would have taken this trade
        score_ok = coin_data.get('enhanced_score', 0) >= default_min_score
        not_overextended = coin_data.get('change_24h', 0) < default_max_24h_change
        has_momentum = coin_data.get('volume_change_24h', 0) > default_min_volume_change
        sufficient_liquidity = coin_data.get('market_cap', 0) > default_min_market_cap

        would_default_trade = score_ok and not_overextended and has_momentum and sufficient_liquidity

        # Track results
        if is_winner:
            self.ab_test_results['adaptive_wins'] += 1
            if would_default_trade:
                self.ab_test_results['default_would_win'] += 1
        else:
            self.ab_test_results['adaptive_losses'] += 1
            if would_default_trade:
                self.ab_test_results['default_would_lose'] += 1

        self._save_learnings()

    def get_ab_test_summary(self) -> Dict:
        """Get A/B test performance comparison

        Returns:
            {
                'adaptive_win_rate': 0.55,
                'default_would_win_rate': 0.48,
                'adaptive_better': True,
                'confidence': 'low' | 'medium' | 'high'
            }
        """
        adaptive_total = self.ab_test_results['adaptive_wins'] + self.ab_test_results['adaptive_losses']
        default_total = self.ab_test_results['default_would_win'] + self.ab_test_results['default_would_lose']

        if adaptive_total == 0:
            return {
                'adaptive_win_rate': 0,
                'default_would_win_rate': 0,
                'adaptive_better': False,
                'confidence': 'none',
                'message': 'No trades yet'
            }

        adaptive_win_rate = self.ab_test_results['adaptive_wins'] / adaptive_total
        default_win_rate = self.ab_test_results['default_would_win'] / default_total if default_total > 0 else 0

        # Determine confidence based on sample size
        if adaptive_total < 20:
            confidence = 'low'
        elif adaptive_total < 50:
            confidence = 'medium'
        else:
            confidence = 'high'

        return {
            'adaptive_win_rate': adaptive_win_rate,
            'default_would_win_rate': default_win_rate,
            'adaptive_better': adaptive_win_rate > default_win_rate,
            'confidence': confidence,
            'adaptive_total': adaptive_total,
            'default_total': default_total,
            'improvement_pct': ((adaptive_win_rate - default_win_rate) / default_win_rate * 100) if default_win_rate > 0 else 0
        }

    def generate_learning_report(self) -> str:
        """Generate human-readable learning report

        Returns:
            Formatted report string
        """
        insights = self.get_pattern_insights()
        filters = self.learnings['adaptive_filters']

        report = []
        report.append("=" * 80)
        report.append("🧠 LEARNING ENGINE REPORT")
        report.append("=" * 80)
        report.append("")

        # Stats
        total_trades = insights['total_winners'] + insights['total_losers']
        win_rate = (insights['total_winners'] / total_trades * 100) if total_trades > 0 else 0

        report.append(f"📊 STATISTICS:")
        report.append(f"   Total Analyzed Trades: {total_trades}")
        report.append(f"   Winners: {insights['total_winners']}")
        report.append(f"   Losers: {insights['total_losers']}")
        report.append(f"   Win Rate: {win_rate:.1f}%")
        report.append("")

        # Current adaptive filters
        report.append(f"🎯 ADAPTIVE FILTERS:")
        report.append(f"   Min Score: {filters['min_score']}")
        report.append(f"   Max 24h Change: {filters['max_24h_change']}%")
        report.append(f"   Min Market Cap: ${filters['min_market_cap']/1e6:.1f}M")
        report.append(f"   Min Volume Change: {filters['min_volume_change']}%")
        report.append("")

        # WALK-FORWARD STATUS
        if self.freeze_mode:
            report.append(f"❄️  WALK-FORWARD: VALIDATION PERIOD")
            report.append(f"   Using frozen parameters (Trade {self.trades_in_current_period}/{self.validation_period_length})")
        else:
            report.append(f"🧠 WALK-FORWARD: LEARNING PERIOD")
            report.append(f"   Adapting parameters (Trade {self.trades_in_current_period}/{self.learning_period_length})")
        report.append("")

        # A/B TEST RESULTS
        ab_summary = self.get_ab_test_summary()
        if ab_summary.get('adaptive_total', 0) > 0:
            report.append(f"📊 A/B TEST: Adaptive vs. Default Strategy")
            report.append(f"   Adaptive Win Rate:  {ab_summary['adaptive_win_rate']*100:.1f}% ({ab_summary['adaptive_total']} trades)")
            report.append(f"   Default Win Rate:   {ab_summary['default_would_win_rate']*100:.1f}% ({ab_summary['default_total']} trades)")

            if ab_summary['adaptive_better']:
                report.append(f"   ✅ Adaptive is BETTER by {ab_summary['improvement_pct']:.1f}%")
            else:
                report.append(f"   ⚠️  Default would be BETTER - consider disabling adaptive!")

            report.append(f"   Confidence: {ab_summary['confidence'].upper()}")
            report.append("")

        # Adaptive Weights (META-LEARNING!)
        if 'adaptive_weights' in self.learnings and self.learnings['adaptive_weights']:
            aw = self.learnings['adaptive_weights']
            report.append(f"🧠 META-LEARNING (Adaptive Weights):")
            report.append(f"   Mode: {aw.get('weights', {}).get('mode', 'default').upper()}")
            report.append(f"   Confidence: {aw.get('confidence', 0):.1%}")

            if 'feature_importance' in aw:
                report.append(f"   Feature Importance:")
                sorted_features = sorted(aw['feature_importance'].items(),
                                       key=lambda x: x[1], reverse=True)
                for feature, importance in sorted_features[:3]:  # Top 3
                    report.append(f"      • {feature}: {importance:.1%}")

            if 'feature_correlations' in aw:
                report.append(f"   Feature Correlations with Success:")
                sorted_corr = sorted(aw['feature_correlations'].items(),
                                   key=lambda x: abs(x[1]), reverse=True)
                for feature, corr in sorted_corr[:3]:  # Top 3
                    direction = "↑" if corr > 0 else "↓"
                    report.append(f"      • {feature}: {corr:+.2f} {direction}")
            report.append("")

        # Recommendations
        if insights['recommendations']:
            report.append(f"💡 RECOMMENDATIONS:")
            for rec in insights['recommendations']:
                report.append(f"   {rec}")
            report.append("")

        # Winner vs Loser patterns
        if insights['winner_characteristics'] and insights['loser_characteristics']:
            report.append(f"📈 WINNER PATTERNS:")
            winners = insights['winner_characteristics']
            if 'enhanced_score' in winners:
                report.append(f"   Avg Score: {winners['enhanced_score']['avg']:.0f}")
            if 'market_cap' in winners:
                report.append(f"   Avg Market Cap: ${winners['market_cap']['avg']/1e6:.1f}M")
            if 'change_24h' in winners:
                report.append(f"   Avg 24h Change at Entry: {winners['change_24h']['avg']:+.1f}%")
            report.append("")

            report.append(f"📉 LOSER PATTERNS:")
            losers = insights['loser_characteristics']
            if 'enhanced_score' in losers:
                report.append(f"   Avg Score: {losers['enhanced_score']['avg']:.0f}")
            if 'market_cap' in losers:
                report.append(f"   Avg Market Cap: ${losers['market_cap']['avg']/1e6:.1f}M")
            if 'change_24h' in losers:
                report.append(f"   Avg 24h Change at Entry: {losers['change_24h']['avg']:+.1f}%")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def calculate_feature_importance(self) -> Dict:
        """Calculate importance of each score component based on trade outcomes

        This is the META-LEARNING core: Which features actually predict success?

        Returns:
            {
                'feature_correlations': {
                    'enhanced_score': 0.65,  # Strong positive correlation
                    'market_cap': -0.12,     # Weak negative
                    'volume_change_24h': 0.78,  # Very strong!
                    ...
                },
                'feature_importance': {
                    'volume_change_24h': 0.35,  # Normalized importance
                    'enhanced_score': 0.28,
                    ...
                },
                'confidence': 0.85  # How confident we are (based on sample size)
            }
        """
        winners = self.learnings['patterns']['winners']
        losers = self.learnings['patterns']['losers']

        total_trades = sum(len(trades) for trades in winners.values()) + \
                      sum(len(trades) for trades in losers.values())

        # Need at least 10 trades for meaningful correlations
        if total_trades < 10:
            return {
                'feature_correlations': {},
                'feature_importance': {},
                'confidence': 0.0,
                'message': f"Need 10+ trades for feature importance (have {total_trades})"
            }

        # Collect all trade outcomes with their characteristics
        trade_data = []

        for symbol, trades in winners.items():
            for trade in trades:
                chars = trade.get('characteristics', {})
                if chars:
                    outcome = {
                        'success': 1.0,  # Winner = 1
                        'pnl_pct': trade['pnl_pct'],
                        'weight': trade.get('weight', 1.0),
                        **chars
                    }
                    trade_data.append(outcome)

        for symbol, trades in losers.items():
            for trade in trades:
                chars = trade.get('characteristics', {})
                if chars:
                    outcome = {
                        'success': 0.0,  # Loser = 0
                        'pnl_pct': trade['pnl_pct'],
                        'weight': trade.get('weight', 1.0),
                        **chars
                    }
                    trade_data.append(outcome)

        if len(trade_data) < 10:
            return {
                'feature_correlations': {},
                'feature_importance': {},
                'confidence': 0.0,
                'message': "Not enough trades with characteristics"
            }

        # Calculate correlation between each feature and success
        feature_correlations = {}

        # Features we care about
        relevant_features = [
            'enhanced_score', 'market_cap', 'volume_24h', 'change_24h',
            'volume_change_24h', 'wash_trading_confidence'
        ]

        for feature in relevant_features:
            # Extract feature values and success outcomes
            feature_values = []
            success_values = []

            for trade in trade_data:
                if feature in trade and trade[feature] is not None:
                    feature_values.append(float(trade[feature]))
                    success_values.append(float(trade['success']))

            if len(feature_values) < 5:  # Need at least 5 samples
                continue

            # Calculate Pearson correlation coefficient
            # r = cov(X,Y) / (std(X) * std(Y))
            try:
                mean_feature = statistics.mean(feature_values)
                mean_success = statistics.mean(success_values)

                if len(feature_values) < 2:
                    continue

                std_feature = statistics.stdev(feature_values)
                std_success = statistics.stdev(success_values) if len(success_values) > 1 else 0

                if std_feature == 0 or std_success == 0:
                    # No variance - feature doesn't discriminate
                    correlation = 0.0
                else:
                    # Covariance
                    covariance = sum((f - mean_feature) * (s - mean_success)
                                   for f, s in zip(feature_values, success_values)) / len(feature_values)

                    correlation = covariance / (std_feature * std_success)

                feature_correlations[feature] = correlation

            except Exception as e:
                # Skip features that cause calculation errors
                print(f"Warning: Could not calculate correlation for {feature}: {e}")
                continue

        # Convert correlations to importance scores (absolute value, normalized)
        feature_importance = {}

        if feature_correlations:
            # Use absolute correlation (both positive and negative matter)
            abs_correlations = {k: abs(v) for k, v in feature_correlations.items()}
            total_abs_correlation = sum(abs_correlations.values())

            if total_abs_correlation > 0:
                feature_importance = {
                    k: v / total_abs_correlation
                    for k, v in abs_correlations.items()
                }

        # Calculate confidence based on sample size and consistency
        # More trades = higher confidence, up to 95% at 50+ trades
        confidence = min(0.95, (total_trades / 50) * 0.95)

        # Reduce confidence if correlations are very weak
        if feature_correlations:
            avg_abs_correlation = statistics.mean(abs(c) for c in feature_correlations.values())
            confidence *= min(1.0, avg_abs_correlation * 2)  # Scale by correlation strength

        return {
            'feature_correlations': feature_correlations,
            'feature_importance': feature_importance,
            'confidence': confidence,
            'sample_size': total_trades,
            'message': f"Analyzed {total_trades} trades"
        }

    def get_adaptive_weights(self, min_confidence: float = 0.3) -> Dict:
        """Get adaptive score weights based on learned feature importance

        WALK-FORWARD: Returns frozen weights during validation period!

        Args:
            min_confidence: Minimum confidence to use adaptive weights (default 0.3)

        Returns:
            {
                'weights': {
                    'volume_activity': 0.30,  # Optimized!
                    'momentum': 0.25,
                    'market_cap': 0.15,
                    ...
                },
                'mode': 'adaptive' | 'default' | 'frozen',
                'confidence': 0.75
            }
        """
        # Default weights (from enhanced_analyzer.py)
        default_weights = {
            'volume_activity': 0.25,
            'momentum': 0.22,
            'market_cap': 0.18,
            'macd': 0.08,
            'rsi': 0.07,
            'market_correlation': 0.05,
            'bollinger': 0.05,
            'volatility': 0.05,
            'wash_penalty': 0.3  # Penalty strength
        }

        # WALK-FORWARD: If in freeze mode, return frozen weights
        if self.freeze_mode and self.frozen_weights:
            print(f"❄️  Using FROZEN weights (Validation Period)")
            return {
                'weights': self.frozen_weights.copy(),
                'mode': 'frozen',
                'confidence': 1.0,
                'reason': 'Walk-forward validation period'
            }

        # Calculate feature importance
        importance_data = self.calculate_feature_importance()

        confidence = importance_data.get('confidence', 0.0)

        # INCREASED MINIMUM SAMPLE SIZE: Need 30+ trades for meaningful learning
        total_trades = importance_data.get('sample_size', 0)

        # Not enough data - use defaults
        if total_trades < 30:
            return {
                'weights': default_weights,
                'mode': 'default',
                'confidence': confidence,
                'reason': f'Need 30+ trades (have {total_trades})'
            }

        # Confidence too low - use defaults
        if confidence < min_confidence:
            return {
                'weights': default_weights,
                'mode': 'default',
                'confidence': confidence,
                'reason': importance_data.get('message', 'Insufficient data')
            }

        # Map learned feature importance to score components
        feature_importance = importance_data['feature_importance']
        feature_correlations = importance_data['feature_correlations']

        # Adaptive weights based on what actually predicts success
        adaptive_weights = default_weights.copy()

        # Volume change correlates with volume_activity score
        if 'volume_change_24h' in feature_importance:
            # Boost volume_activity weight if volume_change is important
            boost = feature_importance['volume_change_24h']
            adaptive_weights['volume_activity'] = default_weights['volume_activity'] * (1 + boost)

        # 24h price change correlates with momentum score
        if 'change_24h' in feature_importance:
            importance = feature_importance['change_24h']
            correlation = feature_correlations.get('change_24h', 0)

            # IMPORTANT: Negative correlation means we should REDUCE momentum weight
            # (coins that already pumped lose more often)
            if correlation < 0:
                adaptive_weights['momentum'] = default_weights['momentum'] * (1 - importance * 0.5)
            else:
                adaptive_weights['momentum'] = default_weights['momentum'] * (1 + importance * 0.5)

        # Market cap importance
        if 'market_cap' in feature_importance:
            boost = feature_importance['market_cap']
            adaptive_weights['market_cap'] = default_weights['market_cap'] * (1 + boost)

        # Enhanced score itself (meta!)
        if 'enhanced_score' in feature_importance:
            # If the score itself is predictive, trust it more
            # This is meta-learning: "Is my scoring system actually working?"
            score_importance = feature_importance['enhanced_score']

            # If score is very predictive, keep weights as-is (score already works!)
            # If score is NOT predictive, rely more on individual components
            if score_importance < 0.3:
                # Score not working well - boost individual feature weights
                for key in ['volume_activity', 'momentum', 'market_cap']:
                    adaptive_weights[key] *= 1.2

        # Wash trading penalty adjustment
        if 'wash_trading_confidence' in feature_correlations:
            correlation = feature_correlations['wash_trading_confidence']
            # If wash trading positively correlates with losing, increase penalty
            if correlation < 0:  # Negative correlation = good (low wash = winners)
                # Strengthen penalty
                adaptive_weights['wash_penalty'] = min(0.6, default_weights['wash_penalty'] * (1 + abs(correlation)))
            else:
                # Weaken penalty (wash trading doesn't matter much)
                adaptive_weights['wash_penalty'] = max(0.1, default_weights['wash_penalty'] * (1 - correlation))

        # Normalize weights (except wash_penalty) to sum to 1.0
        score_components = ['volume_activity', 'momentum', 'market_cap', 'macd',
                           'rsi', 'market_correlation', 'bollinger', 'volatility']

        total_weight = sum(adaptive_weights[k] for k in score_components)

        if total_weight > 0:
            for key in score_components:
                adaptive_weights[key] = adaptive_weights[key] / total_weight

        # BLENDING FOR 30-50 TRADES: Mix adaptive and default (cautious learning)
        if total_trades < 50:
            # Blend 50% adaptive, 50% default
            blended_weights = {}
            for key in default_weights:
                blended_weights[key] = 0.5 * default_weights[key] + 0.5 * adaptive_weights[key]

            print(f"⚖️  Using BLENDED weights (50% adaptive, 50% default) - {total_trades} trades")

            # Store blended weights
            self.learnings['adaptive_weights'] = {
                'weights': blended_weights,
                'confidence': confidence * 0.7,  # Reduced confidence for blended
                'last_updated': datetime.now().isoformat(),
                'feature_importance': feature_importance,
                'feature_correlations': feature_correlations,
                'blended': True,
                'sample_size': total_trades
            }
            self._save_learnings()

            return {
                'weights': blended_weights,
                'mode': 'blended',
                'confidence': confidence * 0.7,
                'feature_importance': feature_importance,
                'sample_size': total_trades
            }

        # FULL ADAPTIVE (50+ trades)
        print(f"🧠 Using FULL ADAPTIVE weights - {total_trades} trades, {confidence:.0%} confidence")

        # Store adaptive weights in learnings for persistence
        self.learnings['adaptive_weights'] = {
            'weights': adaptive_weights,
            'confidence': confidence,
            'last_updated': datetime.now().isoformat(),
            'feature_importance': feature_importance,
            'feature_correlations': feature_correlations,
            'blended': False,
            'sample_size': total_trades
        }
        self._save_learnings()

        return {
            'weights': adaptive_weights,
            'mode': 'adaptive',
            'confidence': confidence,
            'feature_importance': feature_importance,
            'sample_size': total_trades
        }


def main():
    """Test the learning engine"""
    engine = TradingLearningEngine()
    print(engine.generate_learning_report())


if __name__ == "__main__":
    main()
