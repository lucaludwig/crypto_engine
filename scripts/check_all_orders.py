#!/usr/bin/env python3
"""Check all open orders for current positions"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('=' * 80)
print(f'{Fore.CYAN}{Style.BRIGHT}ALL OPEN ORDERS CHECK{Style.RESET_ALL}')
print('=' * 80)

# Get current positions
summary = client.get_portfolio_summary()

print(f"\n💰 Current Positions:")
for symbol, pos in summary['positions'].items():
    if pos['usdt_value'] > 0.5:
        print(f"   {symbol}: {pos['amount']:.4f} (${pos['usdt_value']:.2f})")

print(f"\n📋 CHECKING ALL OPEN ORDERS:\n")

# Check orders for current positions
for symbol in ['XVG', 'LUNC', 'AIXBT']:
    print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}{symbol}USDC:{Style.RESET_ALL}")

    try:
        orders = client.client.get_open_orders(symbol=f"{symbol}USDC")

        if not orders:
            print(f"   {Fore.RED}⚠️  NO PROTECTION ORDERS!{Style.RESET_ALL}")
        else:
            print(f"   {Fore.GREEN}✅ {len(orders)} active order(s){Style.RESET_ALL}\n")

            for order in orders:
                order_type = order['type']
                side = order['side']
                price = float(order.get('stopPrice', order.get('price', 0)))
                qty = float(order['origQty'])
                order_id = order['orderId']

                if order_type == 'STOP_LOSS_LIMIT':
                    print(f"   🛑 Stop-Loss:")
                    print(f"      Type: {order_type}")
                    print(f"      Quantity: {qty}")
                    print(f"      Trigger: ${price:.8f}")
                    print(f"      Order ID: {order_id}")
                elif order_type == 'LIMIT' and side == 'SELL':
                    print(f"   🎯 Take-Profit:")
                    print(f"      Type: {order_type}")
                    print(f"      Quantity: {qty}")
                    print(f"      Price: ${price:.8f}")
                    print(f"      Order ID: {order_id}")
                else:
                    print(f"   ℹ️  Other Order:")
                    print(f"      Type: {order_type}")
                    print(f"      Side: {side}")
                    print(f"      Quantity: {qty}")
                    print(f"      Price: ${price:.8f}")
                    print(f"      Order ID: {order_id}")
                print()

    except Exception as e:
        print(f"   {Fore.RED}Error: {e}{Style.RESET_ALL}")

    print()

print('=' * 80)
print(f"\n{Fore.YELLOW}⚠️  IMPORTANT:{Style.RESET_ALL}")
print("   These are SEPARATE orders, NOT OCO (One-Cancels-Other)!")
print("   If one triggers, the other stays active.")
print("   This could cause issues if both trigger.")
print()
print(f"{Fore.GREEN}💡 SOLUTION:{Style.RESET_ALL}")
print("   We should use proper OCO orders instead!")
print('=' * 80)
