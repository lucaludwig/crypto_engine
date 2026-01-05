#!/usr/bin/env python3
"""Sell NEIRO and switch to USDT quote currency"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

print('='*80)
print(f'{Fore.CYAN}{Style.BRIGHT}SWITCHING TO USDT QUOTE CURRENCY{Style.RESET_ALL}')
print('='*80)
print(f'\n{Fore.YELLOW}Reason: More trading pairs available on USDT{Style.RESET_ALL}')
print(f'{Fore.YELLOW}Updated: Conservative TP targets (10-25% instead of 35-50%){Style.RESET_ALL}\n')

# First, sell all NEIRO with USDC client
client_usdc = load_binance_client(dry_run=False, quote_currency='USDC')

symbol = 'NEIRO'
pair = f'{symbol}USDC'

print(f'{Fore.CYAN}Step 1: Liquidating NEIRO position{Style.RESET_ALL}\n')

# Cancel OCO orders
try:
    print(f'  Canceling OCO orders...', end=' ')
    orders = client_usdc.client.get_open_orders(symbol=pair)
    for order in orders:
        client_usdc.client.cancel_order(symbol=pair, orderId=order['orderId'])
    print(f'{Fore.GREEN}✓{Style.RESET_ALL}')
except Exception as e:
    print(f'{Fore.YELLOW}No orders to cancel{Style.RESET_ALL}')

# Get exact balance
try:
    balance = client_usdc.client.get_asset_balance(asset=symbol)
    amount = float(balance['free']) + float(balance['locked'])

    if amount > 0:
        # Get precision
        info = client_usdc.client.get_symbol_info(pair)
        lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
        step_size = float(lot_filter['stepSize'])
        qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

        import math
        amount_adjusted = math.floor(amount / step_size) * step_size
        amount = round(amount_adjusted, qty_precision)
        qty_str = f"{amount:.{qty_precision}f}"

        ticker = client_usdc.client.get_symbol_ticker(symbol=pair)
        current_price = float(ticker['price'])
        estimated_value = amount * current_price

        print(f'  Selling {amount:.0f} {symbol} (~${estimated_value:.2f} USDC)...', end=' ')

        # Market sell
        order = client_usdc.client.create_order(
            symbol=pair,
            side='SELL',
            type='MARKET',
            quantity=qty_str
        )

        filled_value = sum([float(fill['price']) * float(fill['qty']) for fill in order.get('fills', [])])
        print(f'{Fore.GREEN}✓ SOLD for ${filled_value:.2f}{Style.RESET_ALL}')
    else:
        print(f'  No NEIRO balance')

except Exception as e:
    print(f'  {Fore.RED}Error: {e}{Style.RESET_ALL}')

# Check final USDC balance
summary = client_usdc.get_portfolio_summary()
usdc_balance = summary['total_balance_usdt']

print(f'\n{Fore.GREEN}USDC Balance: ${usdc_balance:.2f}{Style.RESET_ALL}')

print(f'\n{Fore.CYAN}Step 2: Converting USDC to USDT{Style.RESET_ALL}\n')

# Convert USDC to USDT
try:
    # Check if USDC/USDT pair exists
    usdc_info = client_usdc.client.get_symbol_info('USDCUSDT')

    if usdc_balance > 1:
        # Get precision
        lot_filter = [f for f in usdc_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
        step_size = float(lot_filter['stepSize'])
        qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

        amount_adjusted = math.floor(usdc_balance / step_size) * step_size
        amount = round(amount_adjusted, qty_precision)
        qty_str = f"{amount:.{qty_precision}f}"

        print(f'  Swapping {amount:.2f} USDC to USDT...', end=' ')

        # Sell USDC for USDT
        order = client_usdc.client.create_order(
            symbol='USDCUSDT',
            side='SELL',
            type='MARKET',
            quantity=qty_str
        )

        usdt_received = sum([float(fill['price']) * float(fill['qty']) for fill in order.get('fills', [])])
        print(f'{Fore.GREEN}✓ Received ${usdt_received:.2f} USDT{Style.RESET_ALL}')

except Exception as e:
    print(f'  {Fore.YELLOW}Note: {e}{Style.RESET_ALL}')
    print(f'  {Fore.YELLOW}Manual conversion may be needed via Binance Convert{Style.RESET_ALL}')

print('\n' + '='*80)
print(f'{Fore.GREEN}Ready to trade with USDT! More pairs available.{Style.RESET_ALL}')
print(f'{Fore.GREEN}Conservative targets: TP 10-25%, SL 10-25%{Style.RESET_ALL}')
print('='*80 + '\n')
