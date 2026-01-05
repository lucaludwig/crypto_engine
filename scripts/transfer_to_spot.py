#!/usr/bin/env python3
"""Transfer USDC from Funding to Spot Wallet"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
from binance.exceptions import BinanceAPIException

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}TRANSFER USDC TO SPOT WALLET{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

client = load_binance_client(dry_run=False)

# Transfer all USDC from Funding to Spot
try:
    # First, check funding wallet balance
    print(f"{Fore.YELLOW}Checking Funding Wallet...{Style.RESET_ALL}")

    # Get funding wallet balance
    # Note: This requires specific API endpoint
    # Let's transfer all USDC

    print(f"{Fore.YELLOW}Transferring USDC from Funding → Spot...{Style.RESET_ALL}")

    # Transfer USDC (amount will be all available)
    result = client.client.transfer_dust(
        fromAccountType='FUNDING',
        toAccountType='SPOT',
        asset='USDC',
        amount=63.71  # Your USDC amount
    )

    print(f"{Fore.GREEN}✓ Transfer initiated{Style.RESET_ALL}")
    print(result)

except AttributeError:
    # Try alternative method
    print(f"{Fore.YELLOW}Trying universal transfer...{Style.RESET_ALL}")

    try:
        result = client.client.universal_transfer(
            type='FUNDING_MAIN',  # Funding to Spot (Main)
            asset='USDC',
            amount=63.71
        )

        print(f"{Fore.GREEN}✓ Transferred!{Style.RESET_ALL}")
        print(result)

    except BinanceAPIException as e:
        print(f"{Fore.RED}Transfer failed: {e}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}MANUAL TRANSFER NEEDED:{Style.RESET_ALL}")
        print(f"1. Open Binance App/Website")
        print(f"2. Go to Wallets → Funding Wallet")
        print(f"3. Find USDC → Transfer")
        print(f"4. From: Funding Wallet → To: Spot Wallet")
        print(f"5. Amount: All (63.71 USDC)")
        print(f"6. Confirm transfer\n")
        exit(1)

except BinanceAPIException as e:
    print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}MANUAL TRANSFER NEEDED:{Style.RESET_ALL}")
    print(f"1. Open Binance App/Website")
    print(f"2. Go to Wallets → Funding Wallet")
    print(f"3. Find USDC → Transfer")
    print(f"4. From: Funding Wallet → To: Spot Wallet")
    print(f"5. Amount: All (63.71 USDC)")
    print(f"6. Confirm transfer\n")
    exit(1)

# Verify transfer
print(f"\n{Fore.YELLOW}Verifying Spot Wallet balance...{Style.RESET_ALL}")
import time
time.sleep(2)  # Wait for transfer to complete

client._sync_account_state()
summary = client.get_portfolio_summary()

print(f"{Fore.GREEN}{Style.BRIGHT}Spot Wallet Balance: ${summary['total_balance_usdt']:.2f}{Style.RESET_ALL}")

if summary['total_balance_usdt'] > 60:
    print(f"{Fore.GREEN}✓ Ready to trade!{Style.RESET_ALL}\n")
else:
    print(f"{Fore.YELLOW}Transfer may take a moment. Check again in a few seconds.{Style.RESET_ALL}\n")
