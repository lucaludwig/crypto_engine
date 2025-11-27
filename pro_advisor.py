#!/usr/bin/env python3
"""Professional Crypto Advisor - Clean & Concise Output

Full professional analysis under the hood:
- RSI, MACD, Bollinger Bands
- Wash trading detection
- BTC correlation analysis
- Kelly Criterion position sizing
- Safety filtering

Simple, actionable output.
"""
import argparse
from datetime import datetime
from colorama import Fore, Style, init

from cmc_client import CoinMarketCapClient
from enhanced_analyzer import EnhancedCryptoAnalyzer

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


def print_compact_header():
    """Print compact header"""
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}{Style.BRIGHT}CADVI PRO - Crypto Market Advisor{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠️  Not financial advice | High risk | DYOR | Only invest what you can lose{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def print_category_recommendations(top_coins: list, category_name: str, verbose: bool = False):
    """Print recommendations for a specific category"""
    if not top_coins:
        print(f"{Fore.YELLOW}No safe recommendations found for {category_name}.{Style.RESET_ALL}\n")
        return

    print(f"{Fore.GREEN}{Style.BRIGHT}TOP {len(top_coins)} - {category_name.upper()}:{Style.RESET_ALL}\n")

    for i, (symbol, coin) in enumerate(top_coins, 1):
        # Header line
        price_str = f"${coin['price']:.6f}" if coin['price'] < 1 else f"${coin['price']:.2f}"
        name_str = f"#{i} {symbol} ({coin['name'][:25]}{'...' if len(coin['name']) > 25 else ''})"

        print(f"{Fore.CYAN}{Style.BRIGHT}{name_str}{Style.RESET_ALL} {price_str} | Score: {coin['enhanced_score']:.0f}")

        # Market data
        print(f"   MCap: {format_currency(coin['market_cap'])} | Vol: {format_currency(coin['volume_24h'])}")
        print(f"   24h: {format_percent(coin['change_24h'])} | 7d: {format_percent(coin['change_7d'])} | Vol: {format_percent(coin['volume_change_24h'])}")

        if verbose:
            # Technical indicators
            print(f"   Tech: RSI {coin['rsi_score']:.0f} | MACD {coin['macd_score']:.0f} | BB {coin['bollinger_score']:.0f} | BTC {coin['market_correlation_score']:.0f}")

        # Position sizing (no dollar amount)
        kelly_size = coin['kelly_position_size']
        print(f"   {Fore.GREEN}Position: {kelly_size * 100:.1f}%{Style.RESET_ALL}", end="")

        # Trading setup
        current_price = coin['price']
        tp = current_price * 1.20
        sl = current_price * 0.90
        print(f" | {Fore.YELLOW}TP: ${tp:.6f}{Style.RESET_ALL} | {Fore.RED}SL: ${sl:.6f}{Style.RESET_ALL}")

        # For Web3, show contract address prominently
        if coin['contract_address']:
            contract = coin['contract_address']
            platform = coin['platform']
            print(f"   {Fore.MAGENTA}{Style.BRIGHT}Contract ({platform}):{Style.RESET_ALL} {contract}")
            print(f"   {Fore.MAGENTA}→ Search this on Binance Web3 Wallet{Style.RESET_ALL}")

        # Risk level
        risk = "EXTREME" if coin['risk_score'] >= 70 else "HIGH" if coin['risk_score'] >= 40 else "MEDIUM"
        risk_color = Fore.RED if risk == "EXTREME" else Fore.YELLOW
        print(f"   Risk: {risk_color}{risk}{Style.RESET_ALL}", end="")

        # Wash trading warning
        if coin['wash_trading_suspicious']:
            print(f" | {Fore.RED}⚠️  Wash: {coin['wash_trading_confidence']:.0f}%{Style.RESET_ALL}")
        else:
            print(f" | {Fore.GREEN}✓ Clean{Style.RESET_ALL}")

        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='CADVI Pro - Professional Crypto Market Advisor'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=1000,
        help='Coins to analyze (default: 1000)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=10,
        help='Top recommendations (default: 10)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed technical indicators'
    )
    parser.add_argument(
        '--show-filtered',
        action='store_true',
        help='Show coins filtered by wash trading detection'
    )

    args = parser.parse_args()

    try:
        # Header
        print_compact_header()

        # Fetch data
        print(f"{Fore.YELLOW}Fetching data...{Style.RESET_ALL}", end=" ", flush=True)
        client = CoinMarketCapClient()
        coins_data = client.get_latest_listings(limit=args.limit)

        if not coins_data:
            print(f"{Fore.RED}Failed. Check API key.{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}✓{Style.RESET_ALL}")

        # Analyze
        print(f"{Fore.YELLOW}Analyzing (RSI, MACD, Bollinger, Wash Trading)...{Style.RESET_ALL}", end=" ", flush=True)
        analyzer = EnhancedCryptoAnalyzer(coins_data)
        analyzer.calculate_comprehensive_scores()
        print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

        # Get recommendations by category
        top_spot = analyzer.get_top_by_category('spot', n=args.top)
        top_futures = analyzer.get_top_by_category('futures', n=args.top)
        top_web3 = analyzer.get_top_by_category('web3', n=args.top)

        # Show filtered coins if requested
        if args.show_filtered:
            wash_report = analyzer.get_wash_trading_report()
            if not wash_report.empty:
                print(f"{Fore.RED}Filtered {len(wash_report)} suspicious coins (wash trading detected){Style.RESET_ALL}\n")

        # Print results by category
        print("=" * 80)
        print_category_recommendations(top_spot, "Binance Spot", verbose=args.verbose)

        print("=" * 80)
        print_category_recommendations(top_futures, "Binance Futures", verbose=args.verbose)

        print("=" * 80)
        print_category_recommendations(top_web3, "Binance Web3 Wallet", verbose=args.verbose)

        # Footer
        print("=" * 80)
        filtered_count = len(analyzer.df[analyzer.df['wash_trading_suspicious'] == True])
        total_recommendations = len(top_spot) + len(top_futures) + len(top_web3)
        print(f"{Fore.CYAN}Total: {total_recommendations} recommendations (Spot: {len(top_spot)}, Futures: {len(top_futures)}, Web3: {len(top_web3)}){Style.RESET_ALL}")
        print(f"{Fore.CYAN}Analyzed: {len(analyzer.df)} coins | Filtered: {filtered_count} suspicious | {datetime.now().strftime('%H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.RED}⚠️  High risk! Not financial advice!{Style.RESET_ALL}\n")

    except ValueError as e:
        print(f"{Fore.RED}Config error: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Create .env file with CMC_API_KEY{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        raise


if __name__ == "__main__":
    main()
