#!/usr/bin/env python3
"""Check current prices and P&L for open positions"""
from api.binance_client import load_binance_client
from colorama import Fore, Style, init

init(autoreset=True)

client = load_binance_client(dry_run=False, quote_currency='USDC')

print('=' * 80)
print(f'{Fore.CYAN}{Style.BRIGHT}AKTUELLE POSITIONEN - LIVE P&L{Style.RESET_ALL}')
print('=' * 80)

summary = client.get_portfolio_summary()

print(f"\n💰 PORTFOLIO:")
print(f"   Balance: ${summary['total_balance_usdt']:.2f} USDT")
pnl_color = Fore.GREEN if summary['pnl_usdt'] >= 0 else Fore.RED
print(f"   P&L: {pnl_color}{summary['pnl_usdt']:+.2f} USDT ({summary['pnl_pct']:+.2f}%){Style.RESET_ALL}")
print(f"   Exposure: {summary['exposure_pct']:.1f}%")
print(f"   Free Capital: ${summary['total_balance_usdt'] - summary['total_exposure_usdt']:.2f}")

print(f"\n📊 POSITIONEN ({summary['positions_count']}):\n")

for symbol, pos in summary['positions'].items():
    if pos['usdt_value'] > 0.5:
        # Get current price
        try:
            ticker = client.client.get_symbol_ticker(symbol=f"{symbol}USDC")
            current_price = float(ticker['price'])
        except:
            try:
                ticker = client.client.get_symbol_ticker(symbol=f"{symbol}USDT")
                current_price = float(ticker['price'])
            except:
                current_price = pos['price']

        # Calculate P&L
        entry_price = pos['price']
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        pnl_usdt = pos['usdt_value'] * (pnl_pct / 100)

        # Color based on P&L
        if pnl_pct >= 0:
            color = Fore.GREEN
            symbol_text = f"✅ {symbol}"
        else:
            color = Fore.RED
            symbol_text = f"📉 {symbol}"

        print(f"{symbol_text}")
        print(f"   Amount: {pos['amount']:.4f}")
        print(f"   Entry: ${entry_price:.6f}")
        print(f"   Current: ${current_price:.6f}")
        print(f"   Value: ${pos['usdt_value']:.2f}")
        print(f"   P&L: {color}{pnl_pct:+.2f}% (${pnl_usdt:+.2f}){Style.RESET_ALL}")

        # Distance to targets
        tp_target = entry_price * 1.35  # +35%
        sl_target = entry_price * 0.75  # -25%

        tp_distance = ((tp_target - current_price) / current_price) * 100
        sl_distance = ((current_price - sl_target) / current_price) * 100

        print(f"   🎯 Take-Profit: ${tp_target:.6f} ({tp_distance:+.1f}% away)")
        print(f"   🛑 Stop-Loss: ${sl_target:.6f} ({sl_distance:+.1f}% away)")
        print()

print('=' * 80)
