#!/usr/bin/env python3
"""Monitor Auto-Trader Status"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init
import subprocess

init(autoreset=True)

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.CYAN}{Style.BRIGHT}AUTO-TRADER STATUS{Style.RESET_ALL}")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

# Check if process is running
try:
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    auto_trader_running = 'auto_trader.py' in result.stdout and '--live' in result.stdout

    if auto_trader_running:
        print(f"{Fore.GREEN}✓ Auto-Trader is RUNNING{Style.RESET_ALL}")

        # Extract process ID
        for line in result.stdout.split('\n'):
            if 'auto_trader.py' in line and '--live' in line and 'grep' not in line:
                parts = line.split()
                pid = parts[1]
                print(f"  Process ID: {pid}")
                break
    else:
        print(f"{Fore.RED}⊗ Auto-Trader is NOT running{Style.RESET_ALL}")
        print(f"  Start with: python auto_trader.py --live --continuous --confirm\n")
        exit(1)
except Exception as e:
    print(f"{Fore.RED}Error checking process: {e}{Style.RESET_ALL}\n")

# Load client and show portfolio
print()
client = load_binance_client(dry_run=False, quote_currency='USDC')
summary = client.get_portfolio_summary()

print(f"{Fore.CYAN}PORTFOLIO:{Style.RESET_ALL}")
print(f"  Total Balance:     ${summary['total_balance_usdt']:.2f}")

pnl = summary['pnl_usdt']
pnl_pct = summary['pnl_pct']
pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED
print(f"  Total P&L:         {pnl_color}{pnl:+.2f} USDT ({pnl_pct:+.2f}%){Style.RESET_ALL}")
print(f"  Daily P&L:         {pnl_color}{summary['daily_pnl']:+.2f} USDT{Style.RESET_ALL}")
print(f"  Exposure:          ${summary['total_exposure_usdt']:.2f} ({summary['exposure_pct']:.1f}%)")
print(f"  Open Positions:    {summary['positions_count']}")

if summary['positions']:
    print(f"\n{Fore.CYAN}OPEN POSITIONS:{Style.RESET_ALL}")
    for symbol, pos in summary['positions'].items():
        if pos['usdt_value'] > 0.10:  # Skip dust
            print(f"  {symbol:8s} {pos['amount']:.2f} @ ${pos['price']:.6f} = ${pos['usdt_value']:.2f}")

# Trading statistics
stats = client.get_trade_statistics()
if stats['total_trades'] > 0:
    print(f"\n{Fore.CYAN}TRADING STATS:{Style.RESET_ALL}")
    print(f"  Total Trades:      {stats['total_trades']}")
    print(f"  Closed Trades:     {stats['closed_trades']}")
    if stats['closed_trades'] > 0:
        win_rate = stats['win_rate'] * 100
        win_rate_color = Fore.GREEN if win_rate >= 50 else Fore.RED
        print(f"  Win Rate:          {win_rate_color}{win_rate:.1f}%{Style.RESET_ALL}")
        print(f"  Avg Win:           {Fore.GREEN}+{stats['avg_win_pct']:.2f}%{Style.RESET_ALL}")
        print(f"  Avg Loss:          {Fore.RED}-{stats['avg_loss_pct']:.2f}%{Style.RESET_ALL}")

# Show recent log
print(f"\n{Fore.CYAN}RECENT ACTIVITY (last 10 lines):{Style.RESET_ALL}")
try:
    with open('auto_trader.log', 'r') as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(f"  {line.rstrip()}")
except:
    print(f"  {Fore.YELLOW}No log file found{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
print(f"{Fore.YELLOW}Commands:{Style.RESET_ALL}")
print(f"  Monitor:           python monitor.py")
print(f"  Stop Trading:      kill <process_id>")
print(f"  View Full Log:     tail -f auto_trader.log")
print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
