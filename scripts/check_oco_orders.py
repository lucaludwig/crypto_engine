#!/usr/bin/env python3
"""Check OCO protection orders for current positions"""
from api.binance_client import load_binance_client

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('Checking OCO orders for current positions...\n')

for symbol in ['XVG', 'LUNC', 'AIXBT']:
    try:
        orders = client.client.get_open_orders(symbol=f'{symbol}USDC')
        print(f'{symbol}USDC:')
        if orders:
            for order in orders:
                print(f'  Order ID: {order["orderId"]} | Type: {order["type"]} | Side: {order["side"]}')
                print(f'  Price: {order.get("price", order.get("stopPrice", "N/A"))} | Qty: {order["origQty"]}')
                if 'orderListId' in order and order['orderListId'] != -1:
                    print(f'  ✅ Part of OCO Order List: {order["orderListId"]}')
                print()
        else:
            print(f'  ⚠️ No open orders found!\n')
    except Exception as e:
        print(f'  Error: {e}\n')
