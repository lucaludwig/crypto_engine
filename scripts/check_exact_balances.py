#!/usr/bin/env python3
"""Check exact balances including locked amounts"""
from api.binance_client import load_binance_client

client = load_binance_client(dry_run=False, quote_currency='USDC')

print("Checking exact balances for LUNC and AIXBT...\n")

for asset in ['LUNC', 'AIXBT']:
    try:
        balance = client.client.get_asset_balance(asset=asset)
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked

        print(f"{asset}:")
        print(f"  Free: {free:.8f}")
        print(f"  Locked: {locked:.8f}")
        print(f"  Total: {total:.8f}")
        print()
    except Exception as e:
        print(f"{asset}: Error - {e}\n")
