#!/usr/bin/env python3
"""Convert dust (small balances) to BNB"""
from api.binance_client import load_binance_client

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('=' * 80)
print('DUST CONVERTER - Kleine Beträge zu BNB konvertieren')
print('=' * 80)

# Assets to convert
dust_assets = ['BNB', 'SOL', 'OM', 'KAITO', 'INIT']

print('\nVersuche Dust zu konvertieren...\n')

for asset in dust_assets:
    try:
        # Get current balance
        balance_info = client.client.get_asset_balance(asset=asset)
        if balance_info:
            free = float(balance_info['free'])
            locked = float(balance_info['locked'])
            total = free + locked

            if total > 0:
                print(f'{asset}: {total:.8f}')
            else:
                print(f'{asset}: Kein Balance')
    except Exception as e:
        print(f'{asset}: Error - {e}')

print('\n' + '=' * 80)
print('ℹ️  INFO: Binance Dust Converter funktioniert nur über die Web/App UI')
print('Die API erlaubt leider keine automatische Konvertierung.')
print('\nManuelle Anleitung:')
print('1. Binance App/Website öffnen')
print('2. Wallet → Spot → Oben rechts "..." → "Convert small balance to BNB"')
print('3. Alle kleinen Assets auswählen und konvertieren')
print('=' * 80)
