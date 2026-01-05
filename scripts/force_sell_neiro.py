#!/usr/bin/env python3
"""Force sell all NEIRO"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
import math

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

symbol = 'NEIRO'
pair = f'{symbol}USDC'

print(f'{Fore.CYAN}Liquidating ALL NEIRO{Style.RESET_ALL}\n')

# Step 1: Cancel ALL orders
print('Canceling all NEIRO orders...', end=' ')
try:
    orders = client.client.get_open_orders(symbol=pair)
    for order in orders:
        try:
            client.client.cancel_order(symbol=pair, orderId=order['orderId'])
        except:
            pass
    print(f'{Fore.GREEN}✓ Canceled {len(orders)} orders{Style.RESET_ALL}')
except Exception as e:
    print(f'{Fore.YELLOW}{e}{Style.RESET_ALL}')

# Step 2: Wait a moment for balance to free up
import time
time.sleep(2)

# Step 3: Get total free balance
balance = client.client.get_asset_balance(asset=symbol)
free = float(balance['free'])
locked = float(balance['locked'])
total = free + locked

print(f'Balance: Free={free:.0f}, Locked={locked:.0f}, Total={total:.0f}')

if total < 10:
    print(f'{Fore.GREEN}No significant NEIRO balance to sell{Style.RESET_ALL}')
    exit(0)

# Step 4: Sell everything (use free amount only, locked should be freed now)
balance_after = client.client.get_asset_balance(asset=symbol)
amount = float(balance_after['free'])

if amount < 10:
    print(f'{Fore.YELLOW}No free balance after canceling orders{Style.RESET_ALL}')
    exit(0)

# Get precision
info = client.client.get_symbol_info(pair)
lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
step_size = float(lot_filter['stepSize'])
qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

# Floor to avoid insufficient balance
amount_adjusted = math.floor(amount / step_size) * step_size
amount_final = round(amount_adjusted, qty_precision)
qty_str = f"{amount_final:.{qty_precision}f}"

ticker = client.client.get_symbol_ticker(symbol=pair)
current_price = float(ticker['price'])
estimated_value = amount_final * current_price

print(f'Selling {amount_final:.0f} NEIRO (~${estimated_value:.2f})...', end=' ')

try:
    order = client.client.create_order(
        symbol=pair,
        side='SELL',
        type='MARKET',
        quantity=qty_str
    )

    filled_value = sum([float(fill['price']) * float(fill['qty']) for fill in order.get('fills', [])])
    print(f'{Fore.GREEN}✓ SOLD for ${filled_value:.2f} USDC{Style.RESET_ALL}')

except Exception as e:
    print(f'{Fore.RED}Error: {e}{Style.RESET_ALL}')

# Final balance
summary = client.get_portfolio_summary()
print(f'\n{Fore.GREEN}New balance: ${summary["total_balance_usdt"]:.2f} USDC{Style.RESET_ALL}')
