#!/usr/bin/env python3
"""Check active stop-loss and take-profit orders"""
from api.binance_client import load_binance_client

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('=' * 80)
print('AKTIVE SCHUTZ-ORDERS (Stop-Loss & Take-Profit)')
print('=' * 80)

symbols_to_check = ['XVGUSDC', 'ONTUSDC', 'ANIMEUSDC']

for symbol in symbols_to_check:
    try:
        orders = client.client.get_open_orders(symbol=symbol)

        if orders:
            print(f'\n{symbol}:')
            for order in orders:
                order_type = order['type']
                side = order['side']
                price = float(order.get('stopPrice', order.get('price', 0)))
                qty = float(order['origQty'])

                if order_type == 'STOP_LOSS_LIMIT':
                    print(f'  🛑 Stop-Loss: SELL {qty} @ ${price:.6f}')
                elif order_type == 'LIMIT' and side == 'SELL':
                    print(f'  🎯 Take-Profit: SELL {qty} @ ${price:.6f}')
                else:
                    print(f'  {order_type}: {side} {qty} @ ${price:.6f}')
        else:
            print(f'\n{symbol}: ⚠️  KEINE SCHUTZ-ORDERS AKTIV!')

    except Exception as e:
        print(f'\n{symbol}: Fehler - {e}')

print('\n' + '=' * 80)
