#!/usr/bin/env python3
"""Fix remaining stop-loss orders for small positions"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}FIXING REMAINING STOP-LOSS ORDERS{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

client = load_binance_client(dry_run=False, quote_currency='USDC')

# For small positions, we need to set stop-loss for the remaining quantity
# (the part not covered by take-profit)

fixes = [
    {'symbol': 'ONTUSDC', 'asset': 'ONT', 'qty': 71.59, 'current_price': 0.0762},
    {'symbol': 'ANIMEUSDC', 'asset': 'ANIME', 'qty': 682.59, 'current_price': 0.0079},
]

STOP_LOSS_PCT = 0.10

for fix in fixes:
    symbol = fix['symbol']
    asset = fix['asset']
    quantity = fix['qty']
    current_price = fix['current_price']

    print(f"{Fore.CYAN}Setting Stop-Loss for {asset}...{Style.RESET_ALL}")
    print(f"  Remaining quantity: {quantity:.2f}")
    print(f"  Current price: ${current_price:.6f}")

    # Calculate stop price
    stop_price = current_price * (1 - STOP_LOSS_PCT)

    # Get symbol info
    try:
        info = client.client.get_symbol_info(symbol)

        # Get LOT_SIZE
        step_size = None
        for filter in info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                step_size = float(filter['stepSize'])

        # Round quantity
        if step_size:
            qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))
            quantity = round(quantity, qty_precision)

        # Get PRICE_FILTER
        price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
        tick_size = float(price_filter['tickSize'])
        price_precision = len(str(tick_size).split('.')[-1].rstrip('0'))

        # Round price
        stop_price = round(stop_price, price_precision)

        print(f"  Stop-Loss: ${stop_price:.6f} (-10%)")
        print(f"  Quantity: {quantity:.2f}")

        # Check if order value meets minimum
        order_value = quantity * stop_price
        print(f"  Order value: ${order_value:.2f}")

        if order_value < 10:
            print(f"  {Fore.YELLOW}⚠️  Order too small (${order_value:.2f} < $10 min){Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}Skipping - position too small to protect individually{Style.RESET_ALL}\n")
            continue

        # Place Stop-Loss
        try:
            sl_order = client.client.create_order(
                symbol=symbol,
                side='SELL',
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=stop_price,
                stopPrice=stop_price
            )
            print(f"  {Fore.GREEN}✓ Stop-Loss set!{Style.RESET_ALL}\n")
        except BinanceAPIException as e:
            print(f"  {Fore.RED}✗ Failed: {e}{Style.RESET_ALL}\n")

    except Exception as e:
        print(f"  {Fore.RED}Error: {e}{Style.RESET_ALL}\n")

print(f"{Fore.GREEN}Done!{Style.RESET_ALL}\n")

import subprocess
subprocess.run(['python3', 'check_orders.py'])
