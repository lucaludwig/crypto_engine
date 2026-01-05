#!/usr/bin/env python3
"""Show ALL balances (even small ones)"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False)
account = client.client.get_account()

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}ALL ACCOUNT BALANCES{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

all_balances = []

for balance in account['balances']:
    asset = balance['asset']
    free = float(balance['free'])
    locked = float(balance['locked'])
    total = free + locked

    if total > 0:
        all_balances.append({
            'asset': asset,
            'free': free,
            'locked': locked,
            'total': total
        })

all_balances.sort(key=lambda x: x['total'], reverse=True)

print(f"{'Asset':<15} {'Free':<20} {'Locked':<20} {'Total':<20}")
print(f"{'-'*80}")

for b in all_balances:
    locked_str = f"{b['locked']:.8f}" if b['locked'] > 0 else "-"
    print(f"{b['asset']:<15} {b['free']:<20.8f} {locked_str:<20} {b['total']:<20.8f}")

print(f"\n{Fore.CYAN}Total assets: {len(all_balances)}{Style.RESET_ALL}\n")
