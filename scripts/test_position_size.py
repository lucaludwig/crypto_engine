#!/usr/bin/env python3
"""Debug position sizing"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

print(f"\n{Fore.CYAN}DEBUGGING POSITION SIZING{Style.RESET_ALL}\n")

# Get portfolio summary
summary = client.get_portfolio_summary()

print(f"Total Balance: ${summary['total_balance_usdt']:.2f}")
print(f"Current Exposure: ${summary['total_exposure_usdt']:.2f}")
print(f"Exposure %: {summary['exposure_pct']:.2f}%")
print(f"Trading Enabled: {summary['trading_enabled']}")

# Try to calculate position for a symbol
kelly = 0.10
test_symbol = "STRAXUSDC"

print(f"\n{Fore.CYAN}Testing position size for {test_symbol}:{Style.RESET_ALL}")
print(f"Kelly fraction: {kelly}")

# Calculate
max_position = client.current_balance_usdt * client.MAX_POSITION_SIZE_PCT
max_exposure = client.current_balance_usdt * client.MAX_TOTAL_EXPOSURE_PCT
current_exposure = sum(pos['usdt_value'] for pos in client.positions.values())
available_exposure = max_exposure - current_exposure

print(f"\nMax position size (5%): ${max_position:.2f}")
print(f"Max total exposure (30%): ${max_exposure:.2f}")
print(f"Current exposure: ${current_exposure:.2f}")
print(f"Available exposure: ${available_exposure:.2f}")

kelly_position = client.current_balance_usdt * kelly
print(f"Kelly suggested position (10%): ${kelly_position:.2f}")

safe_position = min(kelly_position, max_position, available_exposure)
print(f"Safe position (min of all): ${safe_position:.2f}")

if safe_position < client.MIN_ORDER_VALUE_USDT:
    print(f"{Fore.RED}Position too small! Min required: ${client.MIN_ORDER_VALUE_USDT}{Style.RESET_ALL}")
else:
    print(f"{Fore.GREEN}Position size OK!{Style.RESET_ALL}")

# Test actual function
position_size = client.calculate_position_size(test_symbol, kelly)
print(f"\nActual calculate_position_size returned: ${position_size:.2f}\n")
