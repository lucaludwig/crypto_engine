#!/usr/bin/env python3
"""Backfill Coin Data for Existing Positions

This script fetches CoinMarketCap data for positions that were imported
without coin_data, so the Learning Engine can properly analyze them when they exit.
"""
import json
from pathlib import Path
import pandas as pd
from colorama import Fore, Style, init

from api.cmc_client import CoinMarketCapClient
from api.enhanced_analyzer import EnhancedCryptoAnalyzer

init(autoreset=True)


def backfill_coin_data():
    """Backfill coin_data for positions with empty coin_data"""

    metadata_file = Path(__file__).parent / "position_metadata.json"

    if not metadata_file.exists():
        print(f"{Fore.RED}No position_metadata.json found{Style.RESET_ALL}")
        return

    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}BACKFILL COIN DATA{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    # Find positions with empty coin_data
    positions_to_backfill = []
    for symbol, pos_data in metadata.items():
        coin_data = pos_data.get('coin_data', {})
        if not coin_data or len(coin_data) == 0:
            # Extract base asset (e.g., API3 from API3USDC)
            base_asset = symbol.replace('USDC', '').replace('USDT', '').replace('BUSD', '')
            positions_to_backfill.append((symbol, base_asset, pos_data))

    if not positions_to_backfill:
        print(f"{Fore.GREEN}✓ All positions already have coin_data{Style.RESET_ALL}")
        return

    print(f"{Fore.YELLOW}Found {len(positions_to_backfill)} positions without coin_data:{Style.RESET_ALL}")
    for symbol, base_asset, _ in positions_to_backfill:
        print(f"  • {symbol} ({base_asset})")
    print()

    # Fetch CoinMarketCap data
    print(f"{Fore.YELLOW}Fetching CoinMarketCap data...{Style.RESET_ALL}", end=" ", flush=True)
    client = CoinMarketCapClient()
    coins_data = client.get_latest_listings(limit=1000)

    if not coins_data:
        print(f"{Fore.RED}Failed to fetch CoinMarketCap data{Style.RESET_ALL}")
        return

    print(f"{Fore.GREEN}✓{Style.RESET_ALL}")

    # Analyze to get scores
    print(f"{Fore.YELLOW}Calculating scores...{Style.RESET_ALL}", end=" ", flush=True)
    analyzer = EnhancedCryptoAnalyzer(coins_data)
    analyzer.calculate_comprehensive_scores()
    print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

    # Match positions with analyzed data (from DataFrame)
    updated_count = 0
    df = analyzer.df  # Get the processed DataFrame

    for symbol, base_asset, pos_data in positions_to_backfill:
        # Find coin in analyzed DataFrame
        coin_rows = df[df['symbol'] == base_asset]

        if coin_rows.empty:
            print(f"{Fore.YELLOW}⚠ {symbol}: Not found in analyzed data{Style.RESET_ALL}")
            continue

        coin_found = coin_rows.iloc[0]

        # Extract relevant characteristics
        coin_data = {
            'symbol': coin_found['symbol'],
            'name': coin_found['name'],
            'price': float(coin_found['price']),
            'market_cap': float(coin_found['market_cap']),
            'volume_24h': float(coin_found['volume_24h']),
            'change_24h': float(coin_found.get('percent_change_24h', 0)),
            'volume_change_24h': float(coin_found.get('volume_change_24h', 0)),
            'enhanced_score': float(coin_found.get('enhanced_score', 0)),
            'kelly_position_size': float(coin_found.get('kelly_position_size', 0.05)),
            'wash_trading_confidence': float(coin_found.get('wash_trading_confidence', 50)),
            'market_cap_rank': int(coin_found.get('market_cap_rank', 999)) if pd.notna(coin_found.get('market_cap_rank')) else 999
        }

        # Update metadata
        metadata[symbol]['coin_data'] = coin_data
        updated_count += 1

        score = coin_data['enhanced_score']
        mcap = coin_data['market_cap']
        change = coin_data['change_24h']

        print(f"{Fore.GREEN}✓ {symbol}:{Style.RESET_ALL}")
        print(f"   Score: {score:.0f} | MCap: ${mcap/1e6:.1f}M | 24h: {change:+.1f}%")

    if updated_count == 0:
        print(f"\n{Fore.YELLOW}No positions were updated{Style.RESET_ALL}")
        return

    # Save updated metadata
    print(f"\n{Fore.YELLOW}Saving updated metadata...{Style.RESET_ALL}", end=" ", flush=True)
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

    print(f"{Fore.GREEN}{Style.BRIGHT}✓ Successfully backfilled {updated_count} positions!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Next steps:{Style.RESET_ALL}")
    print(f"  1. Upload to Oracle Cloud: scp -i oracle_key position_metadata.json ubuntu@129.159.223.48:~/cadvi/")
    print(f"  2. Learning Engine will now learn from these positions when they exit!")


if __name__ == "__main__":
    backfill_coin_data()
