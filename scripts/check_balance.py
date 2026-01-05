#!/usr/bin/env python3
"""Check full Binance account balance"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False)

# Get account info
account = client.client.get_account()

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}FULL ACCOUNT BALANCE{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

total_usdt_value = 0
positions = []

for balance in account['balances']:
    asset = balance['asset']
    free = float(balance['free'])
    locked = float(balance['locked'])
    total = free + locked

    if total > 0:
        # Try to get USDT value
        usdt_value = 0
        price = 0

        if asset == 'USDT':
            usdt_value = total
            price = 1.0
        elif asset in ['USDC', 'BUSD', 'DAI']:
            usdt_value = total
            price = 1.0
        else:
            # Try to get price
            try:
                ticker = client.client.get_symbol_ticker(symbol=f"{asset}USDT")
                price = float(ticker['price'])
                usdt_value = total * price
            except:
                try:
                    ticker = client.client.get_symbol_ticker(symbol=f"{asset}BTC")
                    btc_price = float(ticker['price'])
                    btc_usdt = client.client.get_symbol_ticker(symbol="BTCUSDT")
                    btc_usdt_price = float(btc_usdt['price'])
                    price = btc_price * btc_usdt_price
                    usdt_value = total * price
                except:
                    # Can't get price
                    pass

        total_usdt_value += usdt_value

        positions.append({
            'asset': asset,
            'total': total,
            'free': free,
            'locked': locked,
            'price': price,
            'usdt_value': usdt_value
        })

# Sort by USDT value
positions.sort(key=lambda x: x['usdt_value'], reverse=True)

# Print positions
for pos in positions:
    if pos['usdt_value'] > 0.01:  # Only show positions > $0.01
        locked_str = f" ({pos['locked']:.4f} locked)" if pos['locked'] > 0 else ""

        if pos['price'] > 0:
            print(f"{pos['asset']:10s} {pos['total']:15.4f}{locked_str:20s} @ ${pos['price']:12.6f} = ${pos['usdt_value']:10.2f}")
        else:
            print(f"{pos['asset']:10s} {pos['total']:15.4f}{locked_str:20s} (no price data)")

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.GREEN}{Style.BRIGHT}TOTAL VALUE: ${total_usdt_value:.2f} USDT (~€{total_usdt_value * 0.95:.2f}){Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
