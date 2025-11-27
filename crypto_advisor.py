#!/usr/bin/env python3
"""Crypto Market Advisor - High Risk/High Return Recommendations"""
import argparse
from datetime import datetime
from colorama import Fore, Style, init
from tabulate import tabulate

from cmc_client import CoinMarketCapClient
from analyzer import CryptoAnalyzer

# Initialize colorama for colored terminal output
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
    """Print application header"""
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}{Style.BRIGHT}CRYPTO MARKET ADVISOR - High Risk / High Return Analysis{Style.RESET_ALL}")
    print(f"{Fore.GREEN}v3.0 - Pro Day Trader Algorithm (Multi-Timeframe Confirmation){Style.RESET_ALL}")
    print(f"{Fore.CYAN}Optimized for 4-24h holds | Filters out minute-by-minute noise{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Disclaimer: This is for educational purposes only. Not financial advice!{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def print_recommendations(top_coins: list):
    """Print formatted recommendations"""
    if not top_coins:
        print(f"{Fore.RED}No recommendations found. Please check your API connection.{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}{Style.BRIGHT}TOP 5 HIGH RISK / HIGH RETURN COINS FOR NEXT 24H:{Style.RESET_ALL}\n")

    for i, (symbol, coin) in enumerate(top_coins, 1):
        print(f"{Fore.CYAN}{Style.BRIGHT}#{i} {coin['name']} ({symbol}){Style.RESET_ALL}")
        print("-" * 80)

        # Identification info
        print(f"  {Fore.YELLOW}Identification:{Style.RESET_ALL}")
        id_info = [
            ["CoinMarketCap ID", coin['cmc_id']],
            ["CMC Slug", coin['slug']],
        ]
        if coin['platform']:
            id_info.append(["Platform/Chain", coin['platform']])
        if coin['contract_address']:
            contract_short = coin['contract_address'][:10] + "..." + coin['contract_address'][-8:] if len(coin['contract_address']) > 20 else coin['contract_address']
            id_info.append(["Contract", contract_short])
        print(tabulate(id_info, tablefmt="plain"))

        # Basic info table
        print(f"\n  {Fore.YELLOW}Market Data:{Style.RESET_ALL}")
        basic_info = [
            ["Price", f"${coin['price']:.6f}" if coin['price'] < 1 else f"${coin['price']:.2f}"],
            ["Market Cap", format_currency(coin['market_cap'])],
            ["24h Volume", format_currency(coin['volume_24h'])],
            ["Composite Score", f"{Fore.YELLOW}{coin['composite_score']:.2f}/100{Style.RESET_ALL}"],
        ]
        print(tabulate(basic_info, tablefmt="plain"))

        # Price changes
        print(f"\n  {Fore.CYAN}Price Changes:{Style.RESET_ALL}")
        changes = [
            ["1 Hour", format_percent(coin['change_1h'])],
            ["24 Hours", format_percent(coin['change_24h'])],
            ["7 Days", format_percent(coin['change_7d'])],
        ]
        print(tabulate(changes, tablefmt="plain", colalign=("left", "right")))

        # Volume Analysis (NEW - MOST IMPORTANT)
        print(f"\n  {Fore.YELLOW}Volume Analysis:{Style.RESET_ALL}")
        volume_info = [
            ["24h Volume Change", f"{format_percent(coin['volume_change_24h'])}"],
            ["Volume/MCap Ratio", f"{(coin['volume_24h'] / coin['market_cap'] * 100):.1f}%"],
        ]
        print(tabulate(volume_info, tablefmt="plain"))

        # Score breakdown (IMPROVED - showing all new scores)
        print(f"\n  {Fore.CYAN}Score Breakdown:{Style.RESET_ALL}")
        scores = [
            ["🔥 Unusual Volume Spike", f"{coin['unusual_volume_score']:.1f}/100 (25% weight)"],
            ["📈 Momentum", f"{coin['momentum_score']:.1f}/100 (20% weight)"],
            ["📊 Trend Strength", f"{coin['trend_strength_score']:.1f}/100 (15% weight)"],
            ["💹 Volume Activity", f"{coin['activity_score']:.1f}/100 (15% weight)"],
            ["⚠️  Risk Level (MCap)", f"{coin['risk_score']:.1f}/100 (15% weight)"],
            ["📉 Volatility", f"{coin['volatility_score']:.1f}/100 (5% weight)"],
            ["🔄 RSI Signal", f"{coin['rsi_like_score']:.1f}/100 (5% weight)"],
        ]
        print(tabulate(scores, tablefmt="plain"))

        # Risk assessment
        risk_level = "EXTREME" if coin['risk_score'] >= 70 else "HIGH" if coin['risk_score'] >= 40 else "MEDIUM"
        risk_color = Fore.RED if risk_level == "EXTREME" else Fore.YELLOW if risk_level == "HIGH" else Fore.GREEN
        print(f"\n  {Fore.CYAN}Risk Assessment:{Style.RESET_ALL} {risk_color}{Style.BRIGHT}{risk_level} RISK{Style.RESET_ALL}")

        # Why this coin (IMPROVED - focus on most important signals)
        print(f"\n  {Fore.CYAN}Key Signals (Pro Trader Perspective):{Style.RESET_ALL}")
        factors = []

        # Volume signals (MOST IMPORTANT)
        if coin['unusual_volume_score'] > 80:
            factors.append(f"    {Fore.RED}🚨{Style.RESET_ALL} EXTREME volume spike (+{coin['volume_change_24h']:.0f}%) - Whale activity!")
        elif coin['unusual_volume_score'] > 50:
            factors.append(f"    {Fore.YELLOW}⚡{Style.RESET_ALL} Unusual volume spike (+{coin['volume_change_24h']:.0f}%) - Growing interest")

        # Momentum signals
        if coin['momentum_score'] > 70:
            factors.append(f"    {Fore.GREEN}✓{Style.RESET_ALL} Very strong momentum across multiple timeframes")
        elif coin['momentum_score'] > 50:
            factors.append(f"    {Fore.GREEN}✓{Style.RESET_ALL} Strong positive momentum")

        # Trend strength
        if coin['trend_strength_score'] > 60:
            factors.append(f"    {Fore.GREEN}✓{Style.RESET_ALL} Consistent uptrend with acceleration")

        # RSI-like signals
        if coin['rsi_like_score'] > 40:
            factors.append(f"    {Fore.CYAN}↗{Style.RESET_ALL} Reversal signal - bouncing from oversold")

        # Traditional signals
        if coin['activity_score'] > 100:
            factors.append(f"    {Fore.GREEN}✓{Style.RESET_ALL} Exceptional trading activity")
        elif coin['activity_score'] > 70:
            factors.append(f"    {Fore.GREEN}✓{Style.RESET_ALL} High trading activity")

        if coin['risk_score'] >= 70:
            factors.append(f"    {Fore.YELLOW}!{Style.RESET_ALL} Small market cap (higher risk/reward)")

        if coin['change_24h'] > 20:
            factors.append(f"    {Fore.GREEN}✓{Style.RESET_ALL} Exceptional 24h performance (+{coin['change_24h']:.1f}%)")
        elif coin['change_24h'] > 10:
            factors.append(f"    {Fore.GREEN}✓{Style.RESET_ALL} Strong 24h performance (+{coin['change_24h']:.1f}%)")

        for factor in factors:
            print(factor)

        # Trading Platform Detection
        print(f"\n  {Fore.MAGENTA}Trading Platform:{Style.RESET_ALL}")
        if coin['contract_address']:
            platform_info = coin['platform'] if coin['platform'] else "Unknown Chain"
            print(f"    🔗 Token on {platform_info}")
            print(f"    📍 Contract: {coin['contract_address'][:10]}...{coin['contract_address'][-8:]}")
            print(f"    {Fore.YELLOW}⚠️  Likely DEX only (Uniswap, PancakeSwap, etc.){Style.RESET_ALL}")
            print(f"    {Fore.YELLOW}⚠️  NOT available on Binance/Coinbase (centralized exchanges){Style.RESET_ALL}")
            print(f"    {Fore.CYAN}→ Use: Binance Web3 Wallet, MetaMask, or DEX directly{Style.RESET_ALL}")
        else:
            print(f"    🏦 Native coin (Layer-1 blockchain)")
            print(f"    {Fore.GREEN}✓ Likely available on major exchanges{Style.RESET_ALL}")
            print(f"    {Fore.CYAN}→ Check: Binance, Coinbase, Kraken{Style.RESET_ALL}")

        # Trading Strategy with TP/SL Values
        print(f"\n  {Fore.YELLOW}{Style.BRIGHT}TRADING SETUPS (Copy to Binance/Exchange):{Style.RESET_ALL}")
        current_price = coin['price']

        # Conservative setup
        tp_conservative = current_price * 1.20
        sl_trigger_conservative = current_price * 0.90
        sl_limit_conservative = current_price * 0.88

        # Aggressive setup
        tp_aggressive = current_price * 1.50
        sl_trigger_aggressive = current_price * 0.85
        sl_limit_aggressive = current_price * 0.83

        # Moonshot setup
        tp_moonshot = current_price * 2.00
        sl_trigger_moonshot = current_price * 0.80
        sl_limit_moonshot = current_price * 0.78

        print(f"\n  {Fore.GREEN}Conservative (+20% / -10%):{Style.RESET_ALL}")
        print(f"    TP Limit:    ${tp_conservative:.6f}")
        print(f"    SL Trigger:  ${sl_trigger_conservative:.6f}")
        print(f"    SL Limit:    ${sl_limit_conservative:.6f}")

        print(f"\n  {Fore.YELLOW}Aggressive (+50% / -15%):{Style.RESET_ALL}")
        print(f"    TP Limit:    ${tp_aggressive:.6f}")
        print(f"    SL Trigger:  ${sl_trigger_aggressive:.6f}")
        print(f"    SL Limit:    ${sl_limit_aggressive:.6f}")

        print(f"\n  {Fore.RED}Moonshot (+100% / -20%):{Style.RESET_ALL}")
        print(f"    TP Limit:    ${tp_moonshot:.6f}")
        print(f"    SL Trigger:  ${sl_trigger_moonshot:.6f}")
        print(f"    SL Limit:    ${sl_limit_moonshot:.6f}")

        # Add direct link to CoinMarketCap
        cmc_url = f"https://coinmarketcap.com/currencies/{coin['slug']}/"
        print(f"\n  {Fore.CYAN}More Info:{Style.RESET_ALL} {cmc_url}")
        print(f"  {Fore.CYAN}Check Markets Tab to see all exchanges where {symbol} is listed{Style.RESET_ALL}")

        print("\n")


def print_trading_summary(top_coins: list):
    """Print compact TP/SL summary for all coins"""
    print("=" * 80)
    print(f"{Fore.YELLOW}{Style.BRIGHT}QUICK TRADING SETUP GUIDE - COPY THESE VALUES:{Style.RESET_ALL}")
    print("=" * 80 + "\n")

    for i, (symbol, coin) in enumerate(top_coins, 1):
        current_price = coin['price']

        # Calculate setups
        tp_conservative = current_price * 1.20
        sl_trigger_conservative = current_price * 0.90
        sl_limit_conservative = current_price * 0.88

        tp_aggressive = current_price * 1.50
        sl_trigger_aggressive = current_price * 0.85
        sl_limit_aggressive = current_price * 0.83

        tp_moonshot = current_price * 2.00
        sl_trigger_moonshot = current_price * 0.80
        sl_limit_moonshot = current_price * 0.78

        print(f"{Fore.CYAN}{Style.BRIGHT}#{i} {coin['name']} ({symbol}){Style.RESET_ALL} - Current: ${current_price:.6f}")
        print("-" * 80)

        # Platform warning
        if coin['contract_address']:
            print(f"  {Fore.YELLOW}⚠️  DEX Token ({coin['platform']}) - Use Binance Web3 Wallet or DEX{Style.RESET_ALL}")
        else:
            print(f"  {Fore.GREEN}✓ Native Coin - Available on major exchanges{Style.RESET_ALL}")

        print(f"\n  {Fore.GREEN}Conservative Setup (+20% / -10%):{Style.RESET_ALL}")
        print(f"    TP Limit:    {tp_conservative:.6f}")
        print(f"    SL Trigger:  {sl_trigger_conservative:.6f}")
        print(f"    SL Limit:    {sl_limit_conservative:.6f}")

        print(f"\n  {Fore.YELLOW}Aggressive Setup (+50% / -15%):{Style.RESET_ALL}")
        print(f"    TP Limit:    {tp_aggressive:.6f}")
        print(f"    SL Trigger:  {sl_trigger_aggressive:.6f}")
        print(f"    SL Limit:    {sl_limit_aggressive:.6f}")

        print(f"\n  {Fore.RED}Moonshot Setup (+100% / -20%):{Style.RESET_ALL}")
        print(f"    TP Limit:    {tp_moonshot:.6f}")
        print(f"    SL Trigger:  {sl_trigger_moonshot:.6f}")
        print(f"    SL Limit:    {sl_limit_moonshot:.6f}")

        print("\n")

    print("=" * 80)
    print(f"{Fore.CYAN}💡 How to use on Binance/Exchange:{Style.RESET_ALL}")
    print(f"  1. Go to Spot Trading")
    print(f"  2. Select coin pair (e.g., KAITO/USDT)")
    print(f"  3. Choose 'OCO' order type")
    print(f"  4. Copy the values above")
    print(f"  5. Set amount and click 'Sell'")
    print("=" * 80 + "\n")


def print_summary(total_analyzed: int):
    """Print analysis summary"""
    print("=" * 80)
    print(f"{Fore.CYAN}Analysis completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Total coins analyzed: {total_analyzed}{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='Crypto Market Advisor - Find high risk/high return opportunities'
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
        help='Number of top recommendations to show (default: 5)'
    )
    args = parser.parse_args()

    try:
        # Print header
        print_header()

        # Fetch data from CoinMarketCap
        print(f"{Fore.YELLOW}Fetching latest market data from CoinMarketCap...{Style.RESET_ALL}")
        client = CoinMarketCapClient()
        coins_data = client.get_latest_listings(limit=args.limit)

        if not coins_data:
            print(f"{Fore.RED}Failed to fetch data. Please check your API key and connection.{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}Received data for {len(coins_data)} cryptocurrencies{Style.RESET_ALL}")

        # Analyze coins
        print(f"{Fore.YELLOW}Analyzing high-risk/high-return opportunities...{Style.RESET_ALL}\n")
        analyzer = CryptoAnalyzer(coins_data)
        analyzer.calculate_scores()

        # Get separate recommendations
        top_binance_spot = analyzer.get_top_binance_spot_coins(n=args.top)
        top_binance_wallet = analyzer.get_top_binance_wallet_coins(n=args.top)

        # Binance Spot Section
        print("=" * 80)
        print(f"{Fore.GREEN}{Style.BRIGHT}🏦 TOP {args.top} FOR BINANCE SPOT TRADING{Style.RESET_ALL}")
        print(f"{Fore.GREEN}Trade directly on Binance Exchange - Easy OCO Orders{Style.RESET_ALL}")
        print("=" * 80 + "\n")

        if top_binance_spot:
            for i, (symbol, coin) in enumerate(top_binance_spot, 1):
                price = coin['price']
                tp_agg = price * 1.50
                sl_trig = price * 0.85
                sl_lim = price * 0.83

                print(f"{Fore.CYAN}#{i} {symbol}{Style.RESET_ALL} ({coin['name']}) - ${price:.6f} | Score: {coin['composite_score']:.0f}/100")
                print(f"   {format_percent(coin['change_24h'])} 24h | Vol: {format_percent(coin['volume_change_24h'])}")
                print(f"   {Fore.YELLOW}TP:{Style.RESET_ALL} {tp_agg:.6f}  {Fore.RED}SL Trigger:{Style.RESET_ALL} {sl_trig:.6f}  {Fore.RED}SL Limit:{Style.RESET_ALL} {sl_lim:.6f}")
                print("")
        else:
            print(f"{Fore.YELLOW}No Binance coins found in top scores{Style.RESET_ALL}\n")

        # Binance Wallet Section
        print("=" * 80)
        print(f"{Fore.MAGENTA}{Style.BRIGHT}💼 TOP {args.top} FOR BINANCE WEB3 WALLET{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}Use Binance Wallet - NOT on Binance Exchange - Manual Trading!{Style.RESET_ALL}")
        print("=" * 80 + "\n")

        if top_binance_wallet:
            for i, (symbol, coin) in enumerate(top_binance_wallet, 1):
                price = coin['price']
                tp_agg = price * 1.50
                sl_trig = price * 0.85
                sl_lim = price * 0.83

                print(f"{Fore.CYAN}#{i} {symbol}{Style.RESET_ALL} ({coin['name']}) - ${price:.6f} | Score: {coin['composite_score']:.0f}/100")
                print(f"   {format_percent(coin['change_24h'])} 24h | Vol: {format_percent(coin['volume_change_24h'])}")
                print(f"   Chain: {coin['platform']} | Contract: {coin['contract_address'][:12]}...")
                print(f"   {Fore.YELLOW}TP:{Style.RESET_ALL} {tp_agg:.6f}  {Fore.RED}SL Trigger:{Style.RESET_ALL} {sl_trig:.6f}  {Fore.RED}SL Limit:{Style.RESET_ALL} {sl_lim:.6f} {Fore.YELLOW}(Manual!){Style.RESET_ALL}")
                print("")
        else:
            print(f"{Fore.YELLOW}No Binance Wallet tokens found in top scores{Style.RESET_ALL}\n")

        # Short footer
        print("=" * 80)
        print(f"{Fore.CYAN}Analyzed: {len(analyzer.df)} coins | {datetime.now().strftime('%H:%M:%S')}{Style.RESET_ALL}")
        print(f"{Fore.RED}⚠ High risk! Not financial advice. DYOR!{Style.RESET_ALL}\n")

    except ValueError as e:
        print(f"{Fore.RED}Configuration Error: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please create a .env file with your CMC_API_KEY{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}See .env.example for the required format{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
        raise


if __name__ == "__main__":
    main()
