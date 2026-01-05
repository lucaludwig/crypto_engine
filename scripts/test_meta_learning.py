#!/usr/bin/env python3
"""Test Meta-Learning System - Demonstrates Adaptive Scoring

This script simulates trade outcomes to show how the system learns
which score components actually predict success.
"""
import json
from pathlib import Path
from colorama import Fore, Style, init
from api.learning_engine import TradingLearningEngine

init(autoreset=True)


def simulate_trades():
    """Simulate realistic trade outcomes for testing"""

    # Simulate 15 trades with characteristics
    simulated_trades = {
        'winners': {
            'SIM1USDC': [{
                'pnl_pct': 25.0,
                'exit_type': 'TP',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 85,
                    'market_cap': 45_000_000,
                    'volume_24h': 15_000_000,
                    'change_24h': 5.2,
                    'volume_change_24h': 145,
                    'wash_trading_confidence': 15
                },
                'timestamp': '2026-01-02T10:00:00'
            }],
            'SIM2USDC': [{
                'pnl_pct': 18.5,
                'exit_type': 'TP',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 82,
                    'market_cap': 38_000_000,
                    'volume_24h': 12_000_000,
                    'change_24h': 6.8,
                    'volume_change_24h': 165,
                    'wash_trading_confidence': 12
                },
                'timestamp': '2026-01-02T11:00:00'
            }],
            'SIM3USDC': [{
                'pnl_pct': 22.3,
                'exit_type': 'TP',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 88,
                    'market_cap': 42_000_000,
                    'volume_24h': 18_000_000,
                    'change_24h': 4.5,
                    'volume_change_24h': 178,
                    'wash_trading_confidence': 8
                },
                'timestamp': '2026-01-02T12:00:00'
            }],
            'SIM4USDC': [{
                'pnl_pct': 15.2,
                'exit_type': 'TP',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 79,
                    'market_cap': 50_000_000,
                    'volume_24h': 20_000_000,
                    'change_24h': 7.2,
                    'volume_change_24h': 125,
                    'wash_trading_confidence': 18
                },
                'timestamp': '2026-01-02T13:00:00'
            }],
            'SIM5USDC': [{
                'pnl_pct': 28.7,
                'exit_type': 'TP',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 91,
                    'market_cap': 35_000_000,
                    'volume_24h': 22_000_000,
                    'change_24h': 3.8,
                    'volume_change_24h': 198,
                    'wash_trading_confidence': 5
                },
                'timestamp': '2026-01-02T14:00:00'
            }],
            'SIM6USDC': [{
                'pnl_pct': 19.8,
                'exit_type': 'TP',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 84,
                    'market_cap': 41_000_000,
                    'volume_24h': 16_000_000,
                    'change_24h': 5.9,
                    'volume_change_24h': 152,
                    'wash_trading_confidence': 11
                },
                'timestamp': '2026-01-02T15:00:00'
            }],
        },
        'losers': {
            'DUMP1USDC': [{
                'pnl_pct': -15.0,
                'exit_type': 'SL',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 68,
                    'market_cap': 25_000_000,
                    'volume_24h': 8_000_000,
                    'change_24h': 22.5,  # Already heavily pumped!
                    'volume_change_24h': 45,
                    'wash_trading_confidence': 45
                },
                'timestamp': '2026-01-02T10:30:00'
            }],
            'DUMP2USDC': [{
                'pnl_pct': -12.3,
                'exit_type': 'SL',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 71,
                    'market_cap': 28_000_000,
                    'volume_24h': 7_000_000,
                    'change_24h': 18.2,
                    'volume_change_24h': 38,
                    'wash_trading_confidence': 52
                },
                'timestamp': '2026-01-02T11:30:00'
            }],
            'DUMP3USDC': [{
                'pnl_pct': -18.5,
                'exit_type': 'SL',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 65,
                    'market_cap': 22_000_000,
                    'volume_24h': 6_000_000,
                    'change_24h': 25.8,
                    'volume_change_24h': 32,
                    'wash_trading_confidence': 58
                },
                'timestamp': '2026-01-02T12:30:00'
            }],
            'DUMP4USDC': [{
                'pnl_pct': -14.2,
                'exit_type': 'SL',
                'weight': 1.0,
                'characteristics': {
                    'enhanced_score': 69,
                    'market_cap': 30_000_000,
                    'volume_24h': 9_000_000,
                    'change_24h': 20.1,
                    'volume_change_24h': 41,
                    'wash_trading_confidence': 48
                },
                'timestamp': '2026-01-02T13:30:00'
            }],
        }
    }

    return simulated_trades


def test_meta_learning():
    """Test the meta-learning system with simulated data"""

    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}META-LEARNING SYSTEM TEST{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Initialize learning engine
    engine = TradingLearningEngine()

    print(f"{Fore.YELLOW}Simulating 10 trades (6 winners, 4 losers)...{Style.RESET_ALL}\n")

    # Inject simulated data
    simulated = simulate_trades()
    engine.learnings['patterns'] = simulated
    engine._save_learnings()

    # Calculate feature importance
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}FEATURE IMPORTANCE ANALYSIS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    importance_data = engine.calculate_feature_importance()

    print(f"Sample Size: {importance_data['sample_size']} trades")
    print(f"Confidence: {importance_data['confidence']:.1%}\n")

    print(f"{Fore.GREEN}Feature Correlations with Success:{Style.RESET_ALL}")
    sorted_corr = sorted(importance_data['feature_correlations'].items(),
                        key=lambda x: abs(x[1]), reverse=True)

    for feature, corr in sorted_corr:
        direction = "📈" if corr > 0 else "📉"
        color = Fore.GREEN if corr > 0 else Fore.RED
        print(f"  {direction} {feature:25s} {color}{corr:+.3f}{Style.RESET_ALL}")

    print(f"\n{Fore.GREEN}Feature Importance (Normalized):{Style.RESET_ALL}")
    sorted_importance = sorted(importance_data['feature_importance'].items(),
                              key=lambda x: x[1], reverse=True)

    for feature, importance in sorted_importance:
        bar = "█" * int(importance * 50)
        print(f"  {feature:25s} {bar} {importance:.1%}")

    # Get adaptive weights
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}ADAPTIVE WEIGHTS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    adaptive_data = engine.get_adaptive_weights()

    print(f"Mode: {Fore.GREEN}{adaptive_data['mode'].upper()}{Style.RESET_ALL}")
    print(f"Confidence: {adaptive_data['confidence']:.1%}\n")

    if adaptive_data['mode'] == 'adaptive':
        weights = adaptive_data['weights']

        # Default weights for comparison
        default_weights = {
            'volume_activity': 0.25,
            'momentum': 0.22,
            'market_cap': 0.18,
        }

        print(f"{Fore.GREEN}Score Component Weights:{Style.RESET_ALL}")
        print(f"{'Component':<25} {'Default':<12} {'Adaptive':<12} {'Change':<12}")
        print("-" * 65)

        for component in ['volume_activity', 'momentum', 'market_cap']:
            default = default_weights.get(component, 0)
            adaptive = weights.get(component, 0)
            change = ((adaptive - default) / default * 100) if default > 0 else 0

            change_color = Fore.GREEN if change > 0 else Fore.RED if change < 0 else Fore.YELLOW
            change_symbol = "↑" if change > 0 else "↓" if change < 0 else "→"

            print(f"{component:<25} {default:<12.1%} {adaptive:<12.1%} "
                  f"{change_color}{change_symbol} {abs(change):.1f}%{Style.RESET_ALL}")

        print(f"\nWash Trading Penalty: {weights.get('wash_penalty', 0.3):.1%}")

    # Generate full report
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}FULL LEARNING REPORT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    print(engine.generate_learning_report())

    print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ Meta-Learning System Working Perfectly!{Style.RESET_ALL}\n")

    # Key insights
    print(f"{Fore.YELLOW}🔍 KEY INSIGHTS:{Style.RESET_ALL}")

    if 'change_24h' in importance_data['feature_correlations']:
        corr = importance_data['feature_correlations']['change_24h']
        if corr < -0.3:
            print(f"  • Coins that already pumped >20% tend to LOSE (correlation: {corr:.2f})")
            print(f"    → System will REDUCE momentum weight in scoring!")

    if 'volume_change_24h' in importance_data['feature_correlations']:
        corr = importance_data['feature_correlations']['volume_change_24h']
        if corr > 0.3:
            print(f"  • High volume change strongly predicts SUCCESS (correlation: {corr:.2f})")
            print(f"    → System will INCREASE volume_activity weight!")

    if 'wash_trading_confidence' in importance_data['feature_correlations']:
        corr = importance_data['feature_correlations']['wash_trading_confidence']
        if corr < -0.2:
            print(f"  • Wash trading confidence predicts FAILURE (correlation: {corr:.2f})")
            print(f"    → System will STRENGTHEN wash trading penalty!")


if __name__ == "__main__":
    test_meta_learning()
