#!/usr/bin/env python3
"""Cleanup Script - Sell all old positions and start fresh

This script will:
1. Sell all current positions (except USDT)
2. Use all available USDT to trade top opportunities
3. Set stop-loss and take-profit on new positions
"""
import argparse
from colorama import Fore, Style, init
from api.binance_client import load_binance_client

init(autoreset=True)


def cleanup_old_positions(client, dry_run: bool = True):
    """Sell all old positions"""
    summary = client.get_portfolio_summary()

    if not summary['positions']:
        print(f"{Fore.YELLOW}No positions to close{Style.RESET_ALL}\n")
        return

    print(f"{Fore.CYAN}Closing {len(summary['positions'])} old positions...{Style.RESET_ALL}\n")

    for symbol, pos in summary['positions'].items():
        # Keep stablecoins
        if symbol in ['USDT', 'USDC', 'BUSD', 'DAI']:
            print(f"Keeping {symbol}: {pos['amount']:.4f} (stablecoin)")
            continue

        print(f"Closing {symbol}: {pos['amount']:.4f} @ ${pos['price']:.6f} (${pos['usdt_value']:.2f})")

        result = client.close_position(symbol, reason="Cleanup - closing old positions")

        if result:
            print(f"{Fore.GREEN}✓ Closed{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.RED}✗ Failed{Style.RESET_ALL}\n")

    # Sync account to update balance
    client._sync_account_state()
    summary = client.get_portfolio_summary()

    print(f"{Fore.GREEN}Cleanup complete!{Style.RESET_ALL}")
    print(f"Available USDT: ${summary['total_balance_usdt']:.2f}\n")


def main():
    parser = argparse.ArgumentParser(description='Cleanup old positions and prepare for trading')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Simulate without real trades')
    parser.add_argument('--live', action='store_true', help='Execute real trades (CAREFUL!)')
    parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt (USE WITH CAUTION!)')

    args = parser.parse_args()
    dry_run = not args.live

    mode = "DRY RUN MODE 🧪" if dry_run else "LIVE TRADING MODE 🔴"
    mode_color = Fore.YELLOW if dry_run else Fore.RED

    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}CLEANUP OLD POSITIONS{Style.RESET_ALL}")
    print(f"{mode_color}{Style.BRIGHT}{mode}{Style.RESET_ALL}")
    print("="*80 + "\n")

    if not dry_run and not args.confirm:
        print(f"{Fore.RED}{Style.BRIGHT}⚠️  LIVE MODE - WILL SELL YOUR POSITIONS ⚠️{Style.RESET_ALL}")
        print(f"{Fore.RED}Use --confirm flag to proceed{Style.RESET_ALL}")
        return

    # Load client
    client = load_binance_client(dry_run=dry_run)

    # Show current state
    summary = client.get_portfolio_summary()
    print(f"Current balance: ${summary['total_balance_usdt']:.2f} USDT")
    print(f"Current positions: {len(summary['positions'])}\n")

    # Cleanup
    cleanup_old_positions(client, dry_run)

    print(f"{Fore.GREEN}Ready to trade with fresh capital!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Run: python auto_trader.py --live{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
