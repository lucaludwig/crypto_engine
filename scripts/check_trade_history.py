#!/usr/bin/env python3
"""Check recent trade history"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from datetime import datetime

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}RECENT TRADE HISTORY{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

# Check trades for ONT
symbols_to_check = ['ONTUSDC', 'XVGUSDC', 'ANIMEUSDC']

for symbol in symbols_to_check:
    print(f"{Fore.CYAN}Checking {symbol}...{Style.RESET_ALL}")

    try:
        # Get recent trades
        trades = client.client.get_my_trades(symbol=symbol, limit=10)

        if trades:
            for trade in trades:
                trade_time = datetime.fromtimestamp(trade['time'] / 1000)
                side = 'BUY' if trade['isBuyer'] else 'SELL'
                qty = float(trade['qty'])
                price = float(trade['price'])
                total = qty * price

                color = Fore.GREEN if side == 'BUY' else Fore.RED

                print(f"  {color}{side}{Style.RESET_ALL} {qty:.2f} @ ${price:.6f} = ${total:.2f}")
                print(f"  Time: {trade_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Commission: {trade['commission']} {trade['commissionAsset']}")
                print()
        else:
            print(f"  No trades found\n")

    except Exception as e:
        print(f"  {Fore.YELLOW}Cannot check (pair may not exist): {e}{Style.RESET_ALL}\n")

# Check all order history
print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}RECENT ORDERS (Last 24h){Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

for symbol in symbols_to_check:
    try:
        orders = client.client.get_all_orders(symbol=symbol, limit=5)

        if orders:
            print(f"{Fore.CYAN}{symbol}:{Style.RESET_ALL}")
            for order in orders:
                order_time = datetime.fromtimestamp(order['time'] / 1000)
                status = order['status']
                order_type = order['type']
                side = order['side']
                price = float(order.get('price', 0))
                qty = float(order['origQty'])
                filled = float(order['executedQty'])

                status_color = Fore.GREEN if status == 'FILLED' else Fore.YELLOW if status == 'NEW' else Fore.RED

                print(f"  {status_color}{status}{Style.RESET_ALL} | {side} {order_type} | {qty:.2f} @ ${price:.6f}")
                print(f"  Filled: {filled:.2f} | Time: {order_time.strftime('%H:%M:%S')}")
                print()

    except Exception as e:
        print(f"{symbol}: {Fore.YELLOW}{e}{Style.RESET_ALL}\n")

print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
