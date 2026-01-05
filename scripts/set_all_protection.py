#!/usr/bin/env python3
"""Set full protection (Stop-Loss + Take-Profit) for all positions"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}SETTING FULL PROTECTION - AUTOMATED{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

client = load_binance_client(dry_run=False, quote_currency='USDC')

# STEP 1: Cancel all existing orders
print(f"{Fore.YELLOW}Step 1: Canceling all existing orders...{Style.RESET_ALL}\n")

try:
    open_orders = client.client.get_open_orders()

    for order in open_orders:
        try:
            client.client.cancel_order(symbol=order['symbol'], orderId=order['orderId'])
            print(f"  ✓ Cancelled {order['type']} for {order['symbol']}")
        except Exception as e:
            print(f"  ✗ Failed to cancel {order['symbol']}: {e}")

    print(f"\n{Fore.GREEN}All old orders cancelled!{Style.RESET_ALL}\n")
except Exception as e:
    print(f"{Fore.RED}Error canceling orders: {e}{Style.RESET_ALL}\n")

# STEP 2: Get current positions
print(f"{Fore.YELLOW}Step 2: Getting current positions...{Style.RESET_ALL}\n")

summary = client.get_portfolio_summary()
positions = []

for symbol, pos in summary['positions'].items():
    if pos['usdt_value'] > 0.50:  # Only real positions, skip dust
        positions.append({
            'asset': symbol,
            'symbol': f"{symbol}USDC",
            'quantity': pos['amount'],
            'current_price': pos['price']
        })
        print(f"  Found: {symbol} - {pos['amount']:.2f} @ ${pos['price']:.6f}")

print()

# STEP 3: Set protection for each position
STOP_LOSS_PCT = 0.10  # -10%
TAKE_PROFIT_PCT = 0.20  # +20%

print(f"{Fore.YELLOW}Step 3: Setting Stop-Loss & Take-Profit...{Style.RESET_ALL}\n")

for pos in positions:
    symbol = pos['symbol']
    asset = pos['asset']
    quantity = pos['quantity']
    current_price = pos['current_price']

    print(f"{Fore.CYAN}Processing {asset}...{Style.RESET_ALL}")
    print(f"  Position: {quantity:.2f} @ ${current_price:.6f}")

    # Calculate prices
    stop_price = current_price * (1 - STOP_LOSS_PCT)
    tp_price = current_price * (1 + TAKE_PROFIT_PCT)

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

        # Round prices
        stop_price = round(stop_price, price_precision)
        tp_price = round(tp_price, price_precision)

        print(f"  Stop-Loss: ${stop_price:.6f} (-10%)")
        print(f"  Take-Profit: ${tp_price:.6f} (+20%)")

        # Split quantity: 50% for Stop-Loss, 50% for Take-Profit
        qty_half = round(quantity / 2, qty_precision)

        # Adjust to ensure we use full quantity
        qty_sl = qty_half
        qty_tp = round(quantity - qty_half, qty_precision)

        print(f"  Strategy: Split position")
        print(f"    - {qty_sl:.2f} with Stop-Loss")
        print(f"    - {qty_tp:.2f} with Take-Profit")

        # Place Stop-Loss for half
        try:
            sl_order = client.client.create_order(
                symbol=symbol,
                side='SELL',
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=qty_sl,
                price=stop_price,
                stopPrice=stop_price
            )
            print(f"  {Fore.GREEN}✓ Stop-Loss set for {qty_sl:.2f} {asset}{Style.RESET_ALL}")
        except BinanceAPIException as e:
            print(f"  {Fore.RED}✗ Stop-Loss failed: {e}{Style.RESET_ALL}")

        # Place Take-Profit for other half
        try:
            tp_order = client.client.create_order(
                symbol=symbol,
                side='SELL',
                type='LIMIT',
                timeInForce='GTC',
                quantity=qty_tp,
                price=tp_price
            )
            print(f"  {Fore.GREEN}✓ Take-Profit set for {qty_tp:.2f} {asset}{Style.RESET_ALL}")
        except BinanceAPIException as e:
            print(f"  {Fore.RED}✗ Take-Profit failed: {e}{Style.RESET_ALL}")

        print()

    except Exception as e:
        print(f"  {Fore.RED}Error: {e}{Style.RESET_ALL}\n")

# STEP 4: Verify
print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.GREEN}{Style.BRIGHT}PROTECTION SETUP COMPLETE!{Style.RESET_ALL}")
print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")

print(f"{Fore.YELLOW}Verifying orders...{Style.RESET_ALL}\n")

import subprocess
subprocess.run(['python3', 'check_orders.py'])
