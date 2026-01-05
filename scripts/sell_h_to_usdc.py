#!/usr/bin/env python3
"""Sell Humanity Protocol (H) to USDC"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}SELLING H (Humanity Protocol) TO USDC{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

client = load_binance_client(dry_run=False)
account = client.client.get_account()

# Find H balance
h_balance = 0
for balance in account['balances']:
    if balance['asset'] == 'H':
        h_balance = float(balance['free'])
        break

if h_balance == 0:
    print(f"{Fore.RED}No H balance found{Style.RESET_ALL}\n")
    exit(1)

print(f"H Balance: {h_balance:.4f}")

# Try different trading pairs
pairs_to_try = ['HUSDC', 'HUSDT', 'HBTC']

pair_found = None
for pair in pairs_to_try:
    try:
        ticker = client.client.get_symbol_ticker(symbol=pair)
        price = float(ticker['price'])
        pair_found = pair
        print(f"Found pair: {pair} @ ${price:.6f}")
        break
    except:
        continue

if not pair_found:
    print(f"{Fore.RED}Cannot find trading pair for H{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Trying to find all H pairs...{Style.RESET_ALL}")

    # Get all symbols
    exchange_info = client.client.get_exchange_info()
    h_pairs = [s['symbol'] for s in exchange_info['symbols'] if 'H' in s['symbol'] and s['status'] == 'TRADING']

    print(f"Available pairs with H: {h_pairs[:20]}")
    exit(1)

# Get symbol info for precision
info = client.client.get_symbol_info(symbol=pair_found)

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
    quantity = round(h_balance, precision)
else:
    quantity = h_balance

print(f"Selling quantity: {quantity} H")

# Check minimum
if min_qty and quantity < min_qty:
    print(f"{Fore.RED}Amount {quantity} below minimum {min_qty}{Style.RESET_ALL}")
    exit(1)

# Estimate proceeds
try:
    ticker = client.client.get_symbol_ticker(symbol=pair_found)
    price = float(ticker['price'])
    estimated_proceeds = quantity * price
    print(f"Estimated proceeds: ~${estimated_proceeds:.2f}")
except:
    pass

print(f"\n{Fore.RED}Executing SELL order...{Style.RESET_ALL}")

try:
    # Market sell
    order = client.client.order_market_sell(symbol=pair_found, quantity=quantity)

    print(f"{Fore.GREEN}✓ SOLD {quantity} H!{Style.RESET_ALL}")
    print(f"Order ID: {order['orderId']}")
    print(f"Status: {order['status']}")

    if pair_found != 'HUSDC':
        print(f"\n{Fore.YELLOW}Note: Sold to {pair_found.replace('H', '')}. You may need to convert to USDC.{Style.RESET_ALL}")

except BinanceAPIException as e:
    print(f"{Fore.RED}Order failed: {e}{Style.RESET_ALL}")
    exit(1)

# Show new balance
print(f"\n{Fore.GREEN}Checking new balance...{Style.RESET_ALL}")
client._sync_account_state()
summary = client.get_portfolio_summary()

print(f"{Fore.GREEN}{Style.BRIGHT}Total balance: ${summary['total_balance_usdt']:.2f}{Style.RESET_ALL}")
print(f"{Fore.GREEN}Ready to trade!{Style.RESET_ALL}\n")
