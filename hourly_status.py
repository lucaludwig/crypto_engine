#!/usr/bin/env python3
"""Hourly Status Reporter for Telegram

Runs continuously and sends status updates every hour.
Can also be called once via --now flag.

Usage:
  python hourly_status.py        # Run continuously (hourly updates)
  python hourly_status.py --now  # Send one status now and exit
"""
import os
import sys
import time
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.telegram_notifier import notifier

load_dotenv()


def get_portfolio_status():
    """Fetch current portfolio status from Binance Spot"""
    client = Client(
        os.getenv('BINANCE_API_KEY'),
        os.getenv('BINANCE_SECRET_KEY')
    )

    # Get account information (Spot)
    account_info = client.get_account()
    balances = account_info['balances']

    # Filter for non-zero balances (excluding small dust)
    active_balances = [b for b in balances if float(b['free']) + float(b['locked']) > 0.0001]

    # Get USDC balance
    usdc_data = next((b for b in balances if b['asset'] == 'USDC'), None)
    balance = float(usdc_data['free']) if usdc_data else 0.0

    # Load local positions from positions.json (as tracked by the bot)
    positions_file = os.path.join(os.path.dirname(__file__), 'positions.json')
    pos_list = []
    total_pnl = 0
    total_cost = 0

    import json
    if os.path.exists(positions_file):
        try:
            with open(positions_file, 'r') as f:
                tracked_positions = json.load(f)

            for symbol, pos in tracked_positions.items():
                # Get current price
                ticker = client.get_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                entry_price = pos['entry_price']
                quantity = pos['quantity']

                pnl = (current_price - entry_price) * quantity
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                cost = quantity * entry_price

                total_pnl += pnl
                total_cost += cost

                pos_list.append({
                    'symbol': symbol,
                    'pnl_pct': pnl_pct,
                    'pnl': pnl,
                    'tp_away': 0  # Spot bot uses trailing stop, not static TP orders
                })
        except Exception as e:
            print(f"Error reading positions.json: {e}")

    # Sort by PnL (best first)
    pos_list.sort(key=lambda x: x['pnl_pct'], reverse=True)

    # Calculate total PnL percentage
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    # Check if bot is running
    bot_running = os.path.exists(os.path.join(os.path.dirname(__file__), 'bot.pid'))

    return balance, total_pnl, total_pnl_pct, pos_list, bot_running


def send_status():
    """Send current status to Telegram"""
    try:
        balance, total_pnl, total_pnl_pct, positions, bot_running = get_portfolio_status()
        success = notifier.notify_hourly_status(
            balance=balance,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            positions=positions,
            bot_running=bot_running
        )
        if success:
            print(f"[{datetime.now().strftime('%H:%M')}] Status sent to Telegram")
        else:
            print(f"[{datetime.now().strftime('%H:%M')}] Failed to send status")
        return success
    except Exception as e:
        print(f"Error: {e}")
        return False


def run_hourly():
    """Run continuously, sending status every hour"""
    print("Hourly Status Reporter started")
    print("Sending updates every hour on the hour...")
    print("Press Ctrl+C to stop\n")

    # Send initial status
    send_status()

    while True:
        # Calculate seconds until next hour
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0)
        if now.minute > 0 or now.second > 0:
            next_hour = next_hour.replace(hour=(now.hour + 1) % 24)
            if now.hour == 23:
                # Handle day rollover
                from datetime import timedelta
                next_hour = next_hour + timedelta(days=1)

        wait_seconds = (next_hour - now).total_seconds()
        print(f"Next update at {next_hour.strftime('%H:%M')} (in {int(wait_seconds/60)} min)")

        time.sleep(wait_seconds)
        send_status()


if __name__ == '__main__':
    if '--now' in sys.argv:
        # Send one status and exit
        send_status()
    else:
        # Run continuously
        try:
            run_hourly()
        except KeyboardInterrupt:
            print("\nStopped.")
