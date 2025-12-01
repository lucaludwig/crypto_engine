#!/usr/bin/env python3
"""Quick Trade Advisor - Optimized for Set & Forget Limit Orders

Simple workflow:
1. Run this script
2. Buy recommended coins on Binance
3. Set limit sell at target price shown
4. Wait for fill (minutes to days)
5. Repeat

Optimizations:
- Realistic targets based on volatility
- High-probability picks only
- Clean, scannable output
- Binance Spot only
"""
import argparse
from datetime import datetime
from colorama import Fore, Style, init

from api.cmc_client import CoinMarketCapClient
from api.enhanced_analyzer import EnhancedCryptoAnalyzer

init(autoreset=True)


def calculate_smart_target(coin: dict) -> tuple[float, str]:
    """Calculate realistic target price based on volatility

    Returns: (target_price, timeframe_estimate)
    """
    current_price = coin['price']
    vol_24h = abs(coin['change_24h'])
    vol_7d = abs(coin['change_7d'])

    # High volatility = bigger targets achievable faster
    if vol_24h > 20 or vol_7d > 50:
        target_pct = 0.20  # +20%
        timeframe = "1-3 days"
    elif vol_24h > 12 or vol_7d > 30:
        target_pct = 0.15  # +15%
        timeframe = "2-5 days"
    elif vol_24h > 8 or vol_7d > 20:
        target_pct = 0.12  # +12%
        timeframe = "3-7 days"
    else:
        target_pct = 0.08  # +8%
        timeframe = "1-2 weeks"

    target_price = current_price * (1 + target_pct)
    return target_price, timeframe


def format_price(price: float) -> str:
    """Format price with appropriate decimals"""
    if price < 0.00001:
        return f"${price:.8f}"
    elif price < 0.001:
        return f"${price:.6f}"
    elif price < 1:
        return f"${price:.4f}"
    elif price < 100:
        return f"${price:.2f}"
    else:
        return f"${price:.0f}"


def print_quick_list(coins: list):
    """Print ultra-clean, scannable list for quick execution"""
    if not coins:
        print(f"{Fore.RED}No high-probability opportunities right now. Try again later.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}{Style.BRIGHT}🎯 TOP PICKS - READY TO TRADE:{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}Symbol      Entry         Target        Gain      Time       Score{Style.RESET_ALL}")
    print("-" * 75)

    for i, (symbol, coin) in enumerate(coins, 1):
        entry = coin['price']
        target, timeframe = calculate_smart_target(coin)
        gain_pct = ((target - entry) / entry) * 100
        score = coin['enhanced_score']

        # Color code by urgency/quality
        if score > 75:
            color = Fore.GREEN
        elif score > 65:
            color = Fore.YELLOW
        else:
            color = Fore.WHITE

        print(f"{color}{symbol:8s}    {format_price(entry):12s}  {format_price(target):12s}  "
              f"+{gain_pct:5.1f}%   {timeframe:10s}  {score:.0f}{Style.RESET_ALL}")

    print("\n" + "=" * 75)
    print(f"{Fore.CYAN}How to execute:{Style.RESET_ALL}")
    print(f"1. Open Binance Spot")
    print(f"2. Search for symbol (e.g., 'RENDER')")
    print(f"3. Market BUY")
    print(f"4. Set LIMIT SELL at target price")
    print(f"5. Wait for fill, then run again")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Quick Trade Advisor - Optimized for limit orders')
    parser.add_argument('--limit', type=int, default=1000, help='Coins to analyze (default: 1000)')
    parser.add_argument('--top', type=int, default=5, help='Top picks to show (default: 5)')
    parser.add_argument('--min-score', type=int, default=65, help='Minimum score threshold (default: 65)')

    args = parser.parse_args()

    try:
        # Header
        print(f"\n{Fore.CYAN}{Style.BRIGHT}⚡ QUICK TRADE ADVISOR{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Set & Forget Limit Orders | Binance Spot Only{Style.RESET_ALL}")
        print(f"{Fore.RED}⚠️  High Risk - Not Financial Advice{Style.RESET_ALL}\n")

        # Fetch
        print(f"{Fore.YELLOW}Fetching CoinMarketCap data...{Style.RESET_ALL}", end=" ", flush=True)
        client = CoinMarketCapClient()
        coins_data = client.get_latest_listings(limit=args.limit)

        if not coins_data:
            print(f"{Fore.RED}Failed. Check API key.{Style.RESET_ALL}")
            return
        print(f"{Fore.GREEN}✓{Style.RESET_ALL}")

        # Analyze
        print(f"{Fore.YELLOW}Analyzing opportunities...{Style.RESET_ALL}", end=" ", flush=True)
        analyzer = EnhancedCryptoAnalyzer(coins_data)
        analyzer.calculate_comprehensive_scores()
        print(f"{Fore.GREEN}✓{Style.RESET_ALL}")

        # Get recommendations with aggressive filtering
        all_spot = analyzer.get_top_by_category('spot', n=50)  # Get more candidates

        # AGGRESSIVE FILTERING for high-probability targets
        filtered = []
        for symbol, coin in all_spot:
            # Must meet ALL criteria:
            score_ok = coin['enhanced_score'] >= args.min_score
            not_overextended = coin['change_24h'] < 30  # Not already pumped too much
            has_momentum = coin['volume_change_24h'] > 30  # Volume increasing
            wash_clean = coin['wash_trading_confidence'] < 40  # Low wash trading risk
            sufficient_liquidity = coin['market_cap'] > 30_000_000  # $30M+ mcap

            if score_ok and not_overextended and has_momentum and wash_clean and sufficient_liquidity:
                filtered.append((symbol, coin))

        # Take top N after filtering
        top_picks = filtered[:args.top]

        # Display
        print_quick_list(top_picks)

        # Footer
        print(f"{Fore.CYAN}Analysis: {len(analyzer.df)} coins | Filtered to: {len(filtered)} | Showing: {len(top_picks)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}\n")

    except ValueError as e:
        print(f"{Fore.RED}Config error: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Create .env file with CMC_API_KEY{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        raise


if __name__ == "__main__":
    main()
