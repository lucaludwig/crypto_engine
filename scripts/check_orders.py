#!/usr/bin/env python3
"""Check all open orders on Binance"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}OPEN ORDERS STATUS{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

# Get all open orders
try:
    open_orders = client.client.get_open_orders()

    if not open_orders:
        print(f"{Fore.RED}⚠️  NO OPEN ORDERS FOUND!{Style.RESET_ALL}")
        print(f"{Fore.RED}Your positions are NOT protected by stop-loss/take-profit!{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.GREEN}Found {len(open_orders)} open orders:{Style.RESET_ALL}\n")

        for order in open_orders:
            symbol = order['symbol']
            side = order['side']
            order_type = order['type']
            price = float(order.get('price', 0))
            stop_price = float(order.get('stopPrice', 0))
            qty = float(order['origQty'])

            if order_type == 'STOP_LOSS_LIMIT':
                print(f"{Fore.RED}🛑 STOP-LOSS:{Style.RESET_ALL} {symbol}")
                print(f"   Sell {qty:.2f} @ ${stop_price:.6f}")
            elif order_type == 'LIMIT':
                print(f"{Fore.GREEN}🎯 TAKE-PROFIT:{Style.RESET_ALL} {symbol}")
                print(f"   Sell {qty:.2f} @ ${price:.6f}")
            else:
                print(f"📋 {order_type}: {symbol}")
                print(f"   {side} {qty:.2f} @ ${price:.6f}")
            print()

except Exception as e:
    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}\n")

# Show positions without protection
summary = client.get_portfolio_summary()

if summary['positions']:
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}YOUR POSITIONS:{Style.RESET_ALL}\n")

    for symbol, pos in summary['positions'].items():
        if pos['usdt_value'] > 0.10:
            print(f"{symbol:8s} {pos['amount']:.2f} @ ${pos['price']:.6f} = ${pos['usdt_value']:.2f}")

    print(f"\n{Fore.YELLOW}⚠️  Make sure EVERY position has Stop-Loss & Take-Profit!{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
