#!/usr/bin/env python3
"""Transfer USDC from Funding to Spot Wallet (Correct Method)"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}TRANSFER USDC: FUNDING → SPOT{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

client = load_binance_client(dry_run=False)

amount = 63.71  # Your USDC amount

print(f"Transferring {amount} USDC from Funding Wallet to Spot Wallet...\n")

try:
    # Universal Transfer: FUNDING → MAIN (Spot)
    result = client.client.universal_transfer(
        type='FUNDING_MAIN',
        asset='USDC',
        amount=amount
    )

    print(f"{Fore.GREEN}✓ Transfer successful!{Style.RESET_ALL}")
    print(f"Transaction ID: {result.get('tranId', 'N/A')}")

except BinanceAPIException as e:
    print(f"{Fore.RED}API Transfer failed: {e}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}PLEASE DO MANUAL TRANSFER:{Style.RESET_ALL}")
    print(f"1. Open Binance App or binance.com")
    print(f"2. Go to: Wallets → Overview")
    print(f"3. Click 'Transfer' between wallets")
    print(f"4. From: Funding Wallet")
    print(f"5. To: Spot Wallet")
    print(f"6. Coin: USDC")
    print(f"7. Amount: {amount} (or 'Max')")
    print(f"8. Confirm")
    print(f"\n{Fore.CYAN}After transfer, run: python auto_trader.py --live{Style.RESET_ALL}\n")
    exit(1)

# Verify
import time
print(f"\n{Fore.YELLOW}Waiting 3 seconds for transfer to complete...{Style.RESET_ALL}")
time.sleep(3)

client._sync_account_state()
summary = client.get_portfolio_summary()

print(f"{Fore.GREEN}{Style.BRIGHT}\nSpot Wallet Balance: ${summary['total_balance_usdt']:.2f}{Style.RESET_ALL}")

if summary['total_balance_usdt'] > 60:
    print(f"{Fore.GREEN}✓ READY TO TRADE!{Style.RESET_ALL}\n")
    print(f"{Fore.CYAN}Start trading with: python auto_trader.py --live{Style.RESET_ALL}\n")
else:
    print(f"{Fore.YELLOW}If balance not updated, wait a moment and check again.{Style.RESET_ALL}\n")
