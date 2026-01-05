#!/usr/bin/env python3
"""Analyze current positions vs available opportunities"""
from api.cmc_client import CoinMarketCapClient
from api.enhanced_analyzer import EnhancedCryptoAnalyzer
from colorama import Fore, Style, init

init(autoreset=True)

# Get market data
client = CoinMarketCapClient()
coins_data = client.get_latest_listings(limit=1000)

# Analyze
analyzer = EnhancedCryptoAnalyzer(coins_data)
analyzer.calculate_comprehensive_scores()

# Get top opportunities
all_coins = analyzer.get_top_by_category('spot', n=100)

print('='*80)
print(f'{Fore.CYAN}{Style.BRIGHT}POSITION ANALYSIS{Style.RESET_ALL}')
print('='*80)

# Check current positions
current_positions = ['XVG', 'LUNC', 'AIXBT']

print(f'\n{Fore.YELLOW}Current Holdings:{Style.RESET_ALL}\n')

for symbol in current_positions:
    coin_tuple = next((c for c in all_coins if c[0] == symbol), None)
    if coin_tuple:
        coin = coin_tuple[1]
        score = coin.get('enhanced_score', coin.get('score', 0))
        rank = all_coins.index(coin_tuple) + 1

        print(f'{symbol}:')
        print(f'  Score: {score}')
        print(f'  Rank: #{rank} in top 100')
        print(f'  24h Change: {coin["change_24h"]:+.1f}%')
        print(f'  Volume Change: {coin["volume_change_24h"]:+.0f}%')
        print(f'  Market Cap: ${coin["market_cap"]/1e6:.1f}M')

        # Quality assessment
        if score >= 85:
            quality = f'{Fore.GREEN}Excellent{Style.RESET_ALL}'
        elif score >= 75:
            quality = f'{Fore.YELLOW}Good{Style.RESET_ALL}'
        elif score >= 65:
            quality = f'{Fore.YELLOW}Fair{Style.RESET_ALL}'
        else:
            quality = f'{Fore.RED}Weak{Style.RESET_ALL}'

        print(f'  Quality: {quality}')
        print()
    else:
        print(f'{symbol}: {Fore.RED}NOT IN TOP 100 - WEAK FUNDAMENTALS{Style.RESET_ALL}\n')

print('='*80)
print(f'{Fore.GREEN}Top 10 Available Opportunities:{Style.RESET_ALL}\n')

for i, coin_tuple in enumerate(all_coins[:10], 1):
    symbol, coin = coin_tuple
    score = coin.get('enhanced_score', coin.get('score', 0))
    print(f'#{i} {symbol:8s} Score: {score:.0f} | 24h: {coin["change_24h"]:+6.1f}% | Vol: {coin["volume_change_24h"]:+6.0f}% | MCap: ${coin["market_cap"]/1e6:6.1f}M')

print('\n' + '='*80)
