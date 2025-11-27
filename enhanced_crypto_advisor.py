#!/usr/bin/env python3
"""Enhanced Crypto Market Advisor - Professional Grade

Major improvements over original:
1. Professional technical indicators (RSI, MACD, Bollinger Bands)
2. Wash trading detection
3. BTC market correlation analysis
4. Kelly Criterion position sizing
5. Backtesting with Sharpe ratio and validation metrics
6. Enhanced safety warnings

WARNING: Even with these improvements, crypto trading is EXTREMELY RISKY.
This tool is for EDUCATIONAL PURPOSES ONLY.
"""
import argparse
from datetime import datetime
from colorama import Fore, Style, init
from tabulate import tabulate

from cmc_client import CoinMarketCapClient
from enhanced_analyzer import EnhancedCryptoAnalyzer
from backtester import CryptoBacktester

# Initialize colorama
init(autoreset=True)


def format_currency(value: float) -> str:
    """Format value as currency"""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    else:
        return f"${value:.2f}"


def format_percent(value: float) -> str:
    """Format percentage with color"""
    if value > 0:
        return f"{Fore.GREEN}+{value:.2f}%{Style.RESET_ALL}"
    elif value < 0:
        return f"{Fore.RED}{value:.2f}%{Style.RESET_ALL}"
    else:
        return f"{value:.2f}%"


def print_header():
    """Print application header with warnings"""
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}{Style.BRIGHT}ENHANCED CRYPTO MARKET ADVISOR - Professional Edition{Style.RESET_ALL}")
    print(f"{Fore.GREEN}v4.0 - With RSI, MACD, Bollinger Bands, Wash Trading Detection{Style.RESET_ALL}")
    print("=" * 80)
    print(f"{Fore.RED}{Style.BRIGHT}⚠️  CRITICAL WARNINGS - READ BEFORE USING ⚠️{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}1. This is NOT financial advice - FOR EDUCATIONAL USE ONLY")
    print(f"2. Crypto is EXTREMELY volatile - you can lose 100% of your investment")
    print(f"3. Even with improvements, NO algorithm can predict the future")
    print(f"4. Backtesting uses SIMULATED data - real results WILL differ")
    print(f"5. Past performance does NOT guarantee future results")
    print(f"6. Only invest what you can afford to LOSE COMPLETELY")
    print(f"7. This tool CANNOT detect all scams, rug pulls, or manipulations{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def print_recommendations(top_coins: list, show_details: bool = True):
    """Print enhanced recommendations with professional indicators"""
    if not top_coins:
        print(f"{Fore.RED}No safe recommendations found after filtering.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}This could mean:{Style.RESET_ALL}")
        print(f"  - Most coins show signs of wash trading")
        print(f"  - Market conditions are unfavorable")
        print(f"  - Insufficient high-quality opportunities")
        return

    print(f"{Fore.GREEN}{Style.BRIGHT}TOP {len(top_coins)} RECOMMENDATIONS (After Wash Trading Filter):{Style.RESET_ALL}\n")

    for i, (symbol, coin) in enumerate(top_coins, 1):
        print(f"{Fore.CYAN}{Style.BRIGHT}#{i} {coin['name']} ({symbol}){Style.RESET_ALL}")
        print("-" * 80)

        # Basic info
        print(f"  {Fore.YELLOW}Market Data:{Style.RESET_ALL}")
        basic_info = [
            ["Price", f"${coin['price']:.6f}" if coin['price'] < 1 else f"${coin['price']:.2f}"],
            ["Market Cap", format_currency(coin['market_cap'])],
            ["24h Volume", format_currency(coin['volume_24h'])],
            ["Enhanced Score", f"{Fore.GREEN}{coin['enhanced_score']:.2f}/100{Style.RESET_ALL}"],
        ]
        print(tabulate(basic_info, tablefmt="plain"))

        # Price changes
        print(f"\n  {Fore.CYAN}Price Performance:{Style.RESET_ALL}")
        changes = [
            ["1 Hour", format_percent(coin['change_1h'])],
            ["24 Hours", format_percent(coin['change_24h'])],
            ["7 Days", format_percent(coin['change_7d'])],
        ]
        print(tabulate(changes, tablefmt="plain"))

        # Professional Indicators
        print(f"\n  {Fore.MAGENTA}{Style.BRIGHT}Professional Technical Indicators:{Style.RESET_ALL}")
        indicators = [
            ["📊 RSI Signal", f"{coin['rsi_score']:.1f}/100"],
            ["📈 MACD Signal", f"{coin['macd_score']:.1f}/100"],
            ["📉 Bollinger Position", f"{coin['bollinger_score']:.1f}/100"],
            ["🔗 BTC Correlation", f"{coin['market_correlation_score']:.1f}/100"],
        ]
        print(tabulate(indicators, tablefmt="plain"))

        # Wash Trading Status
        print(f"\n  {Fore.YELLOW}Volume Analysis:{Style.RESET_ALL}")
        if coin['wash_trading_suspicious']:
            print(f"    {Fore.RED}⚠️  WARNING: Possible wash trading detected (confidence: {coin['wash_trading_confidence']:.0f}%){Style.RESET_ALL}")
        else:
            print(f"    {Fore.GREEN}✓ Volume appears legitimate{Style.RESET_ALL}")

        # Position Sizing
        print(f"\n  {Fore.GREEN}{Style.BRIGHT}Recommended Position Size:{Style.RESET_ALL}")
        kelly_size = coin['kelly_position_size']
        print(f"    Kelly Criterion: {kelly_size * 100:.1f}% of portfolio")
        print(f"    On $10,000 portfolio: ${10000 * kelly_size:.2f}")
        print(f"    {Fore.YELLOW}Note: This is optimal sizing for long-term growth{Style.RESET_ALL}")

        # Trading Setup
        current_price = coin['price']
        tp_conservative = current_price * 1.20
        sl_conservative = current_price * 0.90

        print(f"\n  {Fore.CYAN}Trading Setup (Conservative):{Style.RESET_ALL}")
        print(f"    Entry:       ${current_price:.6f}")
        print(f"    Take Profit: ${tp_conservative:.6f} (+20%)")
        print(f"    Stop Loss:   ${sl_conservative:.6f} (-10%)")

        # Risk Assessment
        risk_level = "EXTREME" if coin['risk_score'] >= 70 else "HIGH" if coin['risk_score'] >= 40 else "MEDIUM"
        risk_color = Fore.RED if risk_level == "EXTREME" else Fore.YELLOW
        print(f"\n  {Fore.CYAN}Risk Assessment:{Style.RESET_ALL} {risk_color}{Style.BRIGHT}{risk_level}{Style.RESET_ALL}")

        print(f"\n  {Fore.CYAN}More Info:{Style.RESET_ALL} https://coinmarketcap.com/currencies/{coin['slug']}/")
        print("\n")


def print_wash_trading_report(analyzer: EnhancedCryptoAnalyzer):
    """Print wash trading detection report"""
    report = analyzer.get_wash_trading_report()

    if report.empty:
        print(f"{Fore.GREEN}No wash trading detected in analyzed coins.{Style.RESET_ALL}\n")
        return

    print("=" * 80)
    print(f"{Fore.RED}{Style.BRIGHT}🚨 WASH TRADING DETECTION REPORT{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}The following coins show suspicious volume patterns:{Style.RESET_ALL}")
    print("=" * 80 + "\n")

    for idx, row in report.head(10).iterrows():  # Show top 10 suspects
        print(f"{Fore.RED}⚠️  {row['symbol']} ({row['name']}){Style.RESET_ALL}")
        print(f"   Confidence: {row['wash_trading_confidence']:.0f}%")
        print(f"   Volume Change: +{row['volume_change_24h']:.0f}%")
        print(f"   Price Change: {row['percent_change_24h']:+.1f}%")
        print(f"   Market Cap: {format_currency(row['market_cap'])}")
        print()

    print(f"{Fore.YELLOW}These coins have been EXCLUDED from recommendations.{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='Enhanced Crypto Market Advisor - Professional Edition'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Number of coins to analyze (default: 1000)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=5,
        help='Number of top recommendations (default: 5)'
    )
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run backtesting simulation on recommendations'
    )
    parser.add_argument(
        '--monte-carlo',
        action='store_true',
        help='Run Monte Carlo simulation (100 runs)'
    )
    parser.add_argument(
        '--show-wash-trading',
        action='store_true',
        help='Show detailed wash trading detection report'
    )

    args = parser.parse_args()

    try:
        # Print header with warnings
        print_header()

        # Fetch data
        print(f"{Fore.YELLOW}Fetching latest market data from CoinMarketCap...{Style.RESET_ALL}")
        client = CoinMarketCapClient()
        coins_data = client.get_latest_listings(limit=args.limit)

        if not coins_data:
            print(f"{Fore.RED}Failed to fetch data. Check your API key and connection.{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}Received data for {len(coins_data)} cryptocurrencies{Style.RESET_ALL}")

        # Analyze with enhanced analyzer
        print(f"{Fore.YELLOW}Running professional analysis (RSI, MACD, Bollinger, Wash Trading Detection)...{Style.RESET_ALL}\n")
        analyzer = EnhancedCryptoAnalyzer(coins_data)
        analyzer.calculate_comprehensive_scores()

        # Get safe recommendations (wash trading filtered)
        top_coins = analyzer.get_top_safe_recommendations(n=args.top)

        # Show wash trading report if requested
        if args.show_wash_trading:
            print_wash_trading_report(analyzer)

        # Print recommendations
        print_recommendations(top_coins)

        # Backtesting
        if args.backtest and top_coins:
            print("=" * 80)
            print(f"{Fore.CYAN}{Style.BRIGHT}BACKTESTING SIMULATION{Style.RESET_ALL}")
            print("=" * 80 + "\n")

            backtester = CryptoBacktester(initial_capital=10000)

            if args.monte_carlo:
                # Monte Carlo simulation
                monte_carlo_stats = backtester.run_monte_carlo_simulation(
                    top_coins,
                    num_simulations=100,
                    hold_period_hours=24,
                    stop_loss_pct=0.10,
                    take_profit_pct=0.20
                )
            else:
                # Single backtest
                result = backtester.simulate_recommendation_strategy(
                    top_coins,
                    hold_period_hours=24,
                    stop_loss_pct=0.10,
                    take_profit_pct=0.20
                )
                result.print_report()

        # Summary
        print("=" * 80)
        print(f"{Fore.CYAN}Analysis completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Coins analyzed: {len(analyzer.df)}{Style.RESET_ALL}")

        # Final warning
        print(f"\n{Fore.RED}{Style.BRIGHT}⚠️  REMEMBER: High risk = high potential loss!")
        print(f"Always do your own research (DYOR) before investing.{Style.RESET_ALL}")
        print("=" * 80 + "\n")

    except ValueError as e:
        print(f"{Fore.RED}Configuration Error: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Create a .env file with your CMC_API_KEY{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
        raise


if __name__ == "__main__":
    main()
