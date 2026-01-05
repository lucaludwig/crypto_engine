#!/usr/bin/env python3
"""
Sync existing positions into position_metadata.json

This script retrieves current open positions and OCO orders from Binance
and populates the position_metadata.json file so the position monitor
can track them properly.
"""
import os
import json
from datetime import datetime
from binance.client import Client

def sync_positions():
    """Sync existing positions to metadata"""

    # Initialize Binance client
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')  # Note: Docker uses BINANCE_SECRET_KEY

    if not api_key or not api_secret:
        raise ValueError("BINANCE_API_KEY and BINANCE_SECRET_KEY must be set in environment")

    print(f"API Key: {api_key[:10]}...")
    print(f"API Secret: {'*' * 20}")

    client = Client(api_key, api_secret)

    # Get account balances
    account = client.get_account()
    balances = {b['asset']: float(b['free']) + float(b['locked'])
                for b in account['balances']
                if float(b['free']) + float(b['locked']) > 0}

    # Get all open OCO orders
    oco_orders = client.get_open_oco_orders()

    # Build OCO map: symbol -> {list_id, stop_price, limit_price}
    oco_map = {}
    for oco in oco_orders:
        symbol = oco['symbol']
        list_id = oco['orderListId']

        stop_price = None
        limit_price = None

        print(f"\nProcessing OCO for {symbol} (List ID: {list_id}):")

        # Get individual order details for each order in the OCO
        try:
            for order_summary in oco['orders']:
                order_id = order_summary['orderId']

                # Fetch full order details
                order_info = client.get_order(symbol=symbol, orderId=order_id)
                order_type = order_info.get('type', '')

                print(f"  {order_type}: Price={order_info.get('price')}, Stop={order_info.get('stopPrice')}, Status={order_info.get('status')}")

                if 'STOP_LOSS' in order_type:
                    stop_price = float(order_info.get('stopPrice', 0))
                elif 'LIMIT' in order_type:
                    limit_price = float(order_info.get('price', 0))

        except Exception as e:
            print(f"  ⚠️ Error fetching details: {e}")
            continue

        if stop_price and limit_price:
            oco_map[symbol] = {
                'list_id': list_id,
                'stop_price': stop_price,
                'limit_price': limit_price
            }
            print(f"  ✓ Stop: ${stop_price:.6f}, Limit: ${limit_price:.6f}")
        else:
            print(f"  ⚠️ Skipped - missing stop ({stop_price}) or limit ({limit_price})")

    # Get current prices
    prices = {}
    for symbol in oco_map.keys():
        ticker = client.get_symbol_ticker(symbol=symbol)
        prices[symbol] = float(ticker['price'])

    # Build position metadata
    metadata = {}

    for symbol, oco_info in oco_map.items():
        # Extract base asset (remove USDC/USDT/BUSD)
        base_asset = symbol.replace('USDC', '').replace('USDT', '').replace('BUSD', '')

        # Check if we have balance for this asset
        if base_asset not in balances:
            continue

        quantity = balances[base_asset]
        current_price = prices[symbol]

        # Calculate entry price from stop loss (assuming 15-18% SL)
        # entry_price = stop_loss / (1 - sl_pct)
        # We'll estimate using current price for now
        stop_price = oco_info['stop_price']
        limit_price = oco_info['limit_price']

        # Estimate entry price from SL (assume ~15% SL on average)
        estimated_entry = stop_price / (1 - 0.15)

        metadata[symbol] = {
            'entry_time': datetime.now().isoformat(),  # Unknown, use current time
            'entry_price': estimated_entry,
            'quantity': quantity,
            'quantity_remaining': quantity,
            'stop_loss': stop_price,
            'take_profit': limit_price,
            'oco_order_list_id': oco_info['list_id'],
            'trailing_enabled': False,
            'partial_taken': False,
            'dca_count': 0,
            'coin_data': {},
            'adjustments': [],
            'note': 'Imported from existing positions'
        }

        print(f"✓ Synced {symbol}:")
        print(f"  Quantity: {quantity:.4f}")
        print(f"  Entry Price: ${estimated_entry:.6f} (estimated)")
        print(f"  Current Price: ${current_price:.6f}")
        print(f"  Stop Loss: ${stop_price:.6f}")
        print(f"  Take Profit: ${limit_price:.6f}")
        print(f"  OCO List ID: {oco_info['list_id']}")
        print()

    # Save metadata
    metadata_file = 'position_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Synced {len(metadata)} positions to {metadata_file}")
    print("Position monitor can now track these positions!")

if __name__ == '__main__':
    try:
        sync_positions()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
