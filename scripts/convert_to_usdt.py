#!/usr/bin/env python3
"""Convert all assets to USDT for trading"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

def find_trading_pair(client, asset: str):
    """Find available trading pair for asset"""
    pairs_to_try = [
        f"{asset}USDT",
        f"{asset}USDC",
        f"{asset}BTC",
        f"USDT{asset}",  # Inverted
    ]

    for pair in pairs_to_try:
        try:
            client.client.get_symbol_ticker(symbol=pair)
            return pair
        except:
            continue

    return None

def convert_asset_to_usdt(client, asset: str, amount: float):
    """Convert asset to USDT"""

    if asset in ['USDT', 'USDC']:
        print(f"{Fore.GREEN}{asset} is already a stablecoin, keeping it{Style.RESET_ALL}")
        return True

    # Find trading pair
    pair = find_trading_pair(client, asset)

    if not pair:
        print(f"{Fore.RED}Cannot find trading pair for {asset}{Style.RESET_ALL}")
        return False

    print(f"Found pair: {pair}")

    # Get symbol info for precision
    try:
        info = client.client.get_symbol_info(symbol=pair)

        step_size = None
        min_qty = None
        min_notional = 0

        for filter in info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                step_size = float(filter['stepSize'])
                min_qty = float(filter['minQty'])
            elif filter['filterType'] == 'NOTIONAL' or filter['filterType'] == 'MIN_NOTIONAL':
                min_notional = float(filter.get('minNotional', filter.get('notional', 0)))

        # Round quantity to valid precision
        if step_size:
            precision = len(str(step_size).split('.')[-1].rstrip('0'))
            amount = round(amount, precision)

        # Check minimum
        if min_qty and amount < min_qty:
            print(f"{Fore.RED}Amount {amount} below minimum {min_qty}{Style.RESET_ALL}")
            return False

        # Check if we're selling or buying USDT
        if pair.endswith('USDT') or pair.endswith('USDC'):
            # Sell asset for USDT/USDC
            print(f"Selling {amount} {asset}...")
            order = client.client.order_market_sell(symbol=pair, quantity=amount)
        else:
            # Inverted pair - buy USDT with asset
            print(f"Converting {amount} {asset} to USDT...")
            order = client.client.order_market_buy(symbol=pair, quantity=amount)

        print(f"{Fore.GREEN}✓ Converted {asset} to USDT{Style.RESET_ALL}")
        return True

    except BinanceAPIException as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return False

def main():
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}CONVERT ALL ASSETS TO USDT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    client = load_binance_client(dry_run=False)
    account = client.client.get_account()

    assets_to_convert = []

    # Find all assets
    for balance in account['balances']:
        asset = balance['asset']
        free = float(balance['free'])

        if free > 0 and asset not in ['USDT', 'BNB']:  # Keep BNB for fees
            # Get USDT value
            usdt_value = 0

            if asset in ['USDC', 'BUSD', 'DAI']:
                usdt_value = free
            else:
                try:
                    ticker = client.client.get_symbol_ticker(symbol=f"{asset}USDT")
                    price = float(ticker['price'])
                    usdt_value = free * price
                except:
                    pass

            if usdt_value > 1.0:  # Only convert if worth >$1
                assets_to_convert.append({
                    'asset': asset,
                    'amount': free,
                    'usdt_value': usdt_value
                })

    if not assets_to_convert:
        print(f"{Fore.YELLOW}No assets to convert{Style.RESET_ALL}\n")
        return

    print(f"{Fore.YELLOW}Assets to convert:{Style.RESET_ALL}")
    for a in assets_to_convert:
        print(f"  {a['asset']:10s} {a['amount']:.4f} (~${a['usdt_value']:.2f})")

    print(f"\n{Fore.RED}This will convert all to USDT for trading!{Style.RESET_ALL}")

    # Convert each asset
    for a in assets_to_convert:
        print(f"\n{Fore.CYAN}Converting {a['asset']}...{Style.RESET_ALL}")
        convert_asset_to_usdt(client, a['asset'], a['amount'])

    # Show final balance
    print(f"\n{Fore.GREEN}Conversion complete!{Style.RESET_ALL}")

    # Sync and show balance
    client._sync_account_state()
    summary = client.get_portfolio_summary()
    print(f"{Fore.GREEN}{Style.BRIGHT}Available for trading: ${summary['total_balance_usdt']:.2f} USDT{Style.RESET_ALL}\n")

if __name__ == "__main__":
    main()
