#!/usr/bin/env python3
"""Check NEIRO position status"""
from api.binance_client import load_binance_client

client = load_binance_client(dry_run=False, quote_currency='USDC')

# Check OCO orders
orders = client.client.get_open_orders(symbol='NEIROUSDC')
print('NEIRO OCO Orders:\n')

if orders:
    for order in orders:
        print(f'Order ID: {order["orderId"]} | Type: {order["type"]} | Side: {order["side"]}')
        print(f'Price: {order.get("price", order.get("stopPrice", "N/A"))} | Qty: {order["origQty"]}')
        if 'orderListId' in order and order['orderListId'] != -1:
            print(f'✅ Part of OCO Order List: {order["orderListId"]}')
        print()
else:
    print('⚠️ No OCO orders found!')

# Get current performance
ticker = client.client.get_symbol_ticker(symbol='NEIROUSDC')
current_price = float(ticker['price'])
entry_price = 0.000122

pnl_pct = ((current_price - entry_price) / entry_price) * 100

print(f'\nCurrent Price: ${current_price:.6f}')
print(f'Entry Price: ${entry_price:.6f}')
print(f'P&L: {pnl_pct:+.2f}%')
