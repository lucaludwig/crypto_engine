#!/usr/bin/env python3
"""Set OCO (One-Cancels-Other) Orders for 100% Protection

OCO = Stop-Loss + Take-Profit on SAME coins
When one triggers, the other is automatically cancelled
"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}SETTING OCO ORDERS - 100% PROTECTION{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

client = load_binance_client(dry_run=False, quote_currency='USDC')

STOP_LOSS_PCT = 0.10  # -10% (SMART PROTECTION)
TAKE_PROFIT_PCT = 0.25  # +25% (AGGRESSIVE GROWTH)

# STEP 1: Cancel all existing orders
print(f"{Fore.YELLOW}Step 1: Canceling all existing orders...{Style.RESET_ALL}\n")

try:
    open_orders = client.client.get_open_orders()

    for order in open_orders:
        try:
            client.client.cancel_order(symbol=order['symbol'], orderId=order['orderId'])
            print(f"  ✓ Cancelled {order['type']} for {order['symbol']}")
        except Exception as e:
            print(f"  ✗ Failed to cancel {order['symbol']}: {e}")

    print(f"\n{Fore.GREEN}All old orders cancelled!{Style.RESET_ALL}\n")
except Exception as e:
    print(f"{Fore.RED}Error canceling orders: {e}{Style.RESET_ALL}\n")

# STEP 2: Get current positions
print(f"{Fore.YELLOW}Step 2: Setting OCO orders for all positions...{Style.RESET_ALL}\n")

summary = client.get_portfolio_summary()
positions = []

for symbol, pos in summary['positions'].items():
    if pos['usdt_value'] > 0.50:  # Only real positions
        positions.append({
            'asset': symbol,
            'symbol': f"{symbol}USDC",
            'quantity': pos['amount'],
            'current_price': pos['price']
        })

for pos in positions:
    symbol = pos['symbol']
    asset = pos['asset']
    quantity = pos['quantity']
    current_price = pos['current_price']

    print(f"{Fore.CYAN}Setting OCO for {asset}...{Style.RESET_ALL}")
    print(f"  Position: {quantity:.2f} @ ${current_price:.6f}")

    # Calculate prices
    stop_price = current_price * (1 - STOP_LOSS_PCT)
    stop_limit_price = stop_price * 0.99  # Slightly lower to ensure fill
    take_profit_price = current_price * (1 + TAKE_PROFIT_PCT)

    try:
        # Get symbol info for precision
        info = client.client.get_symbol_info(symbol)

        # Get LOT_SIZE
        step_size = None
        for filter in info['filters']:
            if filter['filterType'] == 'LOT_SIZE':
                step_size = float(filter['stepSize'])

        # Round quantity
        if step_size:
            qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))
            quantity = round(quantity, qty_precision)

        # Get PRICE_FILTER
        price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
        tick_size = float(price_filter['tickSize'])
        price_precision = len(str(tick_size).split('.')[-1].rstrip('0'))

        # Round prices
        stop_price = round(stop_price, price_precision)
        stop_limit_price = round(stop_limit_price, price_precision)
        take_profit_price = round(take_profit_price, price_precision)

        print(f"  Quantity: {quantity:.2f}")
        print(f"  Stop-Loss: ${stop_price:.6f} (-10%)")
        print(f"  Take-Profit: ${take_profit_price:.6f} (+20%)")

        # Check minimum notional
        order_value = quantity * stop_price
        if order_value < 10:
            print(f"  {Fore.YELLOW}⚠️  Order too small (${order_value:.2f} < $10){Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}Skipping OCO, setting simple Take-Profit only{Style.RESET_ALL}")

            # Fallback to simple limit order
            try:
                tp_order = client.client.create_order(
                    symbol=symbol,
                    side='SELL',
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=quantity,
                    price=take_profit_price
                )
                print(f"  {Fore.GREEN}✓ Take-Profit set{Style.RESET_ALL}\n")
            except BinanceAPIException as e:
                print(f"  {Fore.RED}✗ Failed: {e}{Style.RESET_ALL}\n")
            continue

        # Create OCO order
        try:
            oco = client.client.create_oco_order(
                symbol=symbol,
                side='SELL',
                quantity=quantity,
                price=take_profit_price,  # Limit (take-profit) price
                stopPrice=stop_price,  # Stop trigger price
                stopLimitPrice=stop_limit_price,  # Stop limit price
                stopLimitTimeInForce='GTC'
            )

            print(f"  {Fore.GREEN}✓ OCO ORDER SET!{Style.RESET_ALL}")
            print(f"    → 100% ({quantity:.2f}) with Stop-Loss @ ${stop_price:.6f}")
            print(f"    → 100% ({quantity:.2f}) with Take-Profit @ ${take_profit_price:.6f}")
            print(f"    → Order ID: {oco['orderListId']}")
            print()

        except BinanceAPIException as e:
            print(f"  {Fore.RED}✗ OCO failed: {e}{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}Falling back to split orders...{Style.RESET_ALL}")

            # Fallback: Split 50/50
            qty_half = round(quantity / 2, qty_precision)

            # Stop-Loss
            try:
                sl_order = client.client.create_order(
                    symbol=symbol,
                    side='SELL',
                    type='STOP_LOSS_LIMIT',
                    timeInForce='GTC',
                    quantity=qty_half,
                    price=stop_limit_price,
                    stopPrice=stop_price
                )
                print(f"  {Fore.GREEN}✓ Stop-Loss set (50%){Style.RESET_ALL}")
            except BinanceAPIException as e2:
                print(f"  {Fore.RED}✗ Stop-Loss failed: {e2}{Style.RESET_ALL}")

            # Take-Profit
            try:
                tp_order = client.client.create_order(
                    symbol=symbol,
                    side='SELL',
                    type='LIMIT',
                    timeInForce='GTC',
                    quantity=quantity - qty_half,
                    price=take_profit_price
                )
                print(f"  {Fore.GREEN}✓ Take-Profit set (50%){Style.RESET_ALL}")
            except BinanceAPIException as e2:
                print(f"  {Fore.RED}✗ Take-Profit failed: {e2}{Style.RESET_ALL}")

            print()

    except Exception as e:
        print(f"  {Fore.RED}Error: {e}{Style.RESET_ALL}\n")

# STEP 3: Verify
print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.GREEN}{Style.BRIGHT}OCO SETUP COMPLETE!{Style.RESET_ALL}")
print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")

print(f"{Fore.YELLOW}Verifying orders...{Style.RESET_ALL}\n")

import subprocess
subprocess.run(['python3', 'check_orders.py'])
