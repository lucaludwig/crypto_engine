#!/usr/bin/env python3
"""Set Stop-Loss and Take-Profit for existing positions"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}SETTING PROTECTION ORDERS{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

client = load_binance_client(dry_run=False, quote_currency='USDC')
summary = client.get_portfolio_summary()

positions_to_protect = [
    {'symbol': 'XVGUSDC', 'asset': 'XVG', 'qty': 1988.11, 'entry': 0.005541},
    {'symbol': 'ONTUSDC', 'asset': 'ONT', 'qty': 285.73, 'entry': 0.0768},
    {'symbol': 'ANIMEUSDC', 'asset': 'ANIME', 'qty': 1365.29, 'entry': 0.00807},
]

STOP_LOSS_PCT = 0.10  # -10%
TAKE_PROFIT_PCT = 0.20  # +20%

for pos in positions_to_protect:
    symbol = pos['symbol']
    asset = pos['asset']
    quantity = pos['qty']
    entry_price = pos['entry']

    print(f"{Fore.CYAN}Setting orders for {asset}...{Style.RESET_ALL}")
    print(f"  Position: {quantity:.2f} @ ${entry_price:.6f}")

    # Calculate prices
    stop_price = entry_price * (1 - STOP_LOSS_PCT)
    tp_price = entry_price * (1 + TAKE_PROFIT_PCT)

    # Get symbol info for precision
    try:
        info = client.client.get_symbol_info(symbol)

        # Get LOT_SIZE filter
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

        # Round prices
        stop_price = round(stop_price, price_precision)
        tp_price = round(tp_price, price_precision)

        print(f"  Stop-Loss: ${stop_price:.6f} (-{STOP_LOSS_PCT*100:.0f}%)")
        print(f"  Take-Profit: ${tp_price:.6f} (+{TAKE_PROFIT_PCT*100:.0f}%)")

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
            print(f"  {Fore.GREEN}✓ Stop-Loss set!{Style.RESET_ALL}")
        except BinanceAPIException as e:
            print(f"  {Fore.RED}✗ Stop-Loss failed: {e}{Style.RESET_ALL}")

        # Place Take-Profit
        try:
            tp_order = client.client.create_order(
                symbol=symbol,
                side='SELL',
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=tp_price
            )
            print(f"  {Fore.GREEN}✓ Take-Profit set!{Style.RESET_ALL}")
        except BinanceAPIException as e:
            print(f"  {Fore.RED}✗ Take-Profit failed: {e}{Style.RESET_ALL}")

        print()

    except Exception as e:
        print(f"  {Fore.RED}Error: {e}{Style.RESET_ALL}\n")

print(f"{Fore.GREEN}Done! Checking orders...{Style.RESET_ALL}\n")

# Verify
import subprocess
subprocess.run(['python3', 'check_orders.py'])
