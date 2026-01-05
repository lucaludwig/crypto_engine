#!/usr/bin/env python3
"""Liquidate current positions to free up capital for better opportunities"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('='*80)
print(f'{Fore.CYAN}{Style.BRIGHT}LIQUIDATING WEAK POSITIONS{Style.RESET_ALL}')
print('='*80)
print(f'\n{Fore.YELLOW}Reason: All positions are NOT in top 100 (weak fundamentals){Style.RESET_ALL}')
print(f'{Fore.YELLOW}Better opportunities available with scores 85-98{Style.RESET_ALL}\n')

positions_to_sell = ['XVG', 'LUNC', 'AIXBT']

for symbol in positions_to_sell:
    pair = f'{symbol}USDC'

    print(f'\n{Fore.CYAN}Processing {symbol}:{Style.RESET_ALL}')

    # Cancel OCO orders first
    try:
        print(f'  Canceling OCO orders...', end=' ')
        orders = client.client.get_open_orders(symbol=pair)
        for order in orders:
            client.client.cancel_order(symbol=pair, orderId=order['orderId'])
        print(f'{Fore.GREEN}✓{Style.RESET_ALL}')
    except Exception as e:
        print(f'{Fore.RED}Error: {e}{Style.RESET_ALL}')

    # Get exact balance
    try:
        balance = client.client.get_asset_balance(asset=symbol)
        amount = float(balance['free']) + float(balance['locked'])

        if amount > 0:
            # Get symbol info for precision
            info = client.client.get_symbol_info(pair)
            lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
            step_size = float(lot_filter['stepSize'])
            qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

            # Floor to avoid insufficient balance
            import math
            amount_adjusted = math.floor(amount / step_size) * step_size
            amount = round(amount_adjusted, qty_precision)
            qty_str = f"{amount:.{qty_precision}f}"

            # Get current price for estimate
            ticker = client.client.get_symbol_ticker(symbol=pair)
            current_price = float(ticker['price'])
            estimated_value = amount * current_price

            print(f'  Selling {amount:.4f} {symbol} (~${estimated_value:.2f} USDC)...', end=' ')

            # Market sell
            order = client.client.create_order(
                symbol=pair,
                side='SELL',
                type='MARKET',
                quantity=qty_str
            )

            filled_qty = float(order.get('executedQty', 0))
            filled_value = sum([float(fill['price']) * float(fill['qty']) for fill in order.get('fills', [])])

            print(f'{Fore.GREEN}✓ SOLD{Style.RESET_ALL}')
            print(f'  Received: ${filled_value:.2f} USDC')
        else:
            print(f'  No balance to sell')

    except Exception as e:
        print(f'  {Fore.RED}Error: {e}{Style.RESET_ALL}')

print('\n' + '='*80)
print(f'{Fore.GREEN}Liquidation complete! Capital freed for better opportunities.{Style.RESET_ALL}')
print('='*80)

# Show new balance
summary = client.get_portfolio_summary()
print(f'\n{Fore.CYAN}New Balance: ${summary["total_balance_usdt"]:.2f} USDC{Style.RESET_ALL}')
print(f'{Fore.GREEN}Bot will automatically trade top opportunities in next cycle!{Style.RESET_ALL}\n')
