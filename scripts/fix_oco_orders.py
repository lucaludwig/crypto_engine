#!/usr/bin/env python3
"""Fix current positions with proper OCO orders"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('=' * 80)
print(f'{Fore.CYAN}{Style.BRIGHT}FIXING OCO ORDERS FOR CURRENT POSITIONS{Style.RESET_ALL}')
print('=' * 80)

# Get current positions
summary = client.get_portfolio_summary()

positions_to_fix = []
for symbol, pos in summary['positions'].items():
    if pos['usdt_value'] > 0.5:
        positions_to_fix.append({
            'symbol': symbol,
            'amount': pos['amount'],
            'entry_price': pos['price'],
            'value': pos['usdt_value']
        })

print(f"\nFound {len(positions_to_fix)} positions to protect:\n")

for pos in positions_to_fix:
    symbol = pos['symbol']
    entry_price = pos['entry_price']

    # Get EXACT balance from Binance (don't use calculated)
    try:
        balance = client.client.get_asset_balance(asset=symbol)
        amount = float(balance['free'])
    except:
        amount = pos['amount']

    print(f"{Fore.CYAN}{symbol}:{Style.RESET_ALL}")
    print(f"   Amount: {amount:.8f}")
    print(f"   Entry: ${entry_price:.8f}")
    print(f"   Value: ${pos['value']:.2f}")

    # Cancel existing orders first
    try:
        print(f"\n   {Fore.YELLOW}Canceling old orders...{Style.RESET_ALL}")
        old_orders = client.client.get_open_orders(symbol=f"{symbol}USDC")
        for order in old_orders:
            client.client.cancel_order(symbol=f"{symbol}USDC", orderId=order['orderId'])
            print(f"   ✓ Canceled order {order['orderId']}")
    except Exception as e:
        print(f"   ℹ️  No old orders to cancel: {e}")

    # Calculate OCO prices
    stop_loss_pct = 0.25  # -25%
    take_profit_pct = 0.35  # +35%

    stop_price = entry_price * (1 - stop_loss_pct)
    stop_limit_price = stop_price * 0.99  # Slightly below stop
    take_profit_price = entry_price * (1 + take_profit_pct)

    # Get symbol info for precision
    try:
        info = client.client.get_symbol_info(f"{symbol}USDC")

        # Get price precision
        price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
        tick_size = float(price_filter['tickSize'])
        price_precision = len(str(tick_size).split('.')[-1].rstrip('0'))

        # Get quantity precision
        lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
        step_size = float(lot_filter['stepSize'])
        qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

        # Round values
        stop_price = round(stop_price, price_precision)
        stop_limit_price = round(stop_limit_price, price_precision)
        take_profit_price = round(take_profit_price, price_precision)

        # For quantity, use floor division to step_size to avoid exceeding balance
        import math
        amount_adjusted = math.floor(amount / step_size) * step_size
        amount = round(amount_adjusted, qty_precision)

        print(f"\n   {Fore.GREEN}Setting OCO Order:{Style.RESET_ALL}")
        print(f"   🛑 Stop-Loss: ${stop_price:.8f} (-25%)")
        print(f"   🎯 Take-Profit: ${take_profit_price:.8f} (+35%)")
        print(f"   📊 Quantity: {amount:.4f}")

        # Format prices as strings without scientific notation
        tp_str = f"{take_profit_price:.{price_precision}f}"
        sl_str = f"{stop_price:.{price_precision}f}"
        sl_limit_str = f"{stop_limit_price:.{price_precision}f}"
        qty_str = f"{amount:.{qty_precision}f}"

        print(f"   Debug: TP={tp_str}, SL={sl_str}, Qty={qty_str}")

        # Create OCO order (new Binance API format)
        oco_order = client.client.create_oco_order(
            symbol=f"{symbol}USDC",
            side='SELL',
            quantity=qty_str,
            aboveType='LIMIT_MAKER',  # Take-profit
            abovePrice=tp_str,
            belowType='STOP_LOSS_LIMIT',  # Stop-loss
            belowStopPrice=sl_str,
            belowPrice=sl_limit_str,
            belowTimeInForce='GTC'
        )

        print(f"   {Fore.GREEN}✅ OCO Order Created!{Style.RESET_ALL}")
        print(f"   Order List ID: {oco_order['orderListId']}")

    except Exception as e:
        print(f"   {Fore.RED}❌ Failed: {e}{Style.RESET_ALL}")

    print()

print('=' * 80)
print(f"{Fore.GREEN}All positions now protected with proper OCO orders!{Style.RESET_ALL}")
print('=' * 80)
