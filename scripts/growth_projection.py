#!/usr/bin/env python3
"""Growth Projection Calculator - $60 to 1 BTC Journey

Calculates realistic timelines based on different win rates and trading frequency.
"""
from datetime import datetime, timedelta
from colorama import Fore, Style, init
import math

init(autoreset=True)

# Current state
STARTING_BALANCE = 60.0
TARGET_BTC_PRICE = 95000.0  # Current BTC price
TARGET_BALANCE = TARGET_BTC_PRICE

# Trading parameters
POSITION_SIZE_PCT = 0.50  # 50% of capital per trade
TAKE_PROFIT_PCT = 0.35    # +35% target
STOP_LOSS_PCT = 0.25      # -25% stop

# Trading frequency (after first exit frees up capital)
TRADES_PER_WEEK = 3  # Conservative: 3 trades per week (positions close via TP/SL)

print("=" * 80)
print(f"{Fore.CYAN}{Style.BRIGHT}GROWTH PROJECTION: $60 → 1 BTC ($95,000){Style.RESET_ALL}")
print("=" * 80)
print()

print(f"💰 Start: ${STARTING_BALANCE:.2f}")
print(f"🎯 Target: 1 BTC = ${TARGET_BTC_PRICE:,.0f}")
print(f"📈 Required Growth: {(TARGET_BALANCE/STARTING_BALANCE):.0f}x ({((TARGET_BALANCE/STARTING_BALANCE - 1) * 100):.0f}%)")
print()

print("⚙️  Trading Parameters:")
print(f"   Position Size: {POSITION_SIZE_PCT*100:.0f}% per trade")
print(f"   Take Profit: +{TAKE_PROFIT_PCT*100:.0f}%")
print(f"   Stop Loss: -{STOP_LOSS_PCT*100:.0f}%")
print(f"   Frequency: ~{TRADES_PER_WEEK} trades/week (after capital unlocks)")
print()

print("=" * 80)
print()

def simulate_growth(win_rate: float, name: str, color: str):
    """Simulate portfolio growth with compound effect"""

    balance = STARTING_BALANCE
    total_trades = 0
    weeks = 0

    milestones = [100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 95000]
    milestone_data = []

    # Track by week
    max_weeks = 520  # 10 years max (safety limit)

    while balance < TARGET_BALANCE and weeks < max_weeks:
        weeks += 1
        trades_this_week = TRADES_PER_WEEK

        for _ in range(trades_this_week):
            total_trades += 1

            # Position size (50% of balance)
            position_size = balance * POSITION_SIZE_PCT

            # Win or loss?
            import random
            random.seed(total_trades)  # Deterministic for same win_rate
            is_win = random.random() < win_rate

            if is_win:
                # Win: +35% on position
                profit = position_size * TAKE_PROFIT_PCT
                balance += profit
            else:
                # Loss: -25% on position
                loss = position_size * STOP_LOSS_PCT
                balance -= loss

            # Check milestones
            for milestone in milestones:
                if balance >= milestone and milestone not in [m[0] for m in milestone_data]:
                    milestone_data.append((milestone, weeks, total_trades))

            # Safety: stop if balance goes very low
            if balance < 10:
                break

        # Safety: stop if balance goes very low
        if balance < 10:
            break

    # Print results
    print(f"{color}{Style.BRIGHT}SCENARIO: {name}{Style.RESET_ALL}")
    print(f"Win Rate: {win_rate*100:.0f}% | Avg Trades/Week: {TRADES_PER_WEEK}")
    print()

    if balance >= TARGET_BALANCE:
        print(f"✅ {Fore.GREEN}TARGET REACHED!{Style.RESET_ALL}")
        print(f"   Final Balance: ${balance:,.2f}")
        print(f"   Time: {weeks} weeks ({weeks/4.3:.1f} months / {weeks/52:.1f} years)")
        print(f"   Total Trades: {total_trades}")
        print()

        print("📅 Milestones:")
        for amount, week, trades in milestone_data:
            months = week / 4.3
            date_reach = datetime.now() + timedelta(weeks=week)
            print(f"   ${amount:>6,} → Week {week:>3} ({months:>4.1f} months) - {date_reach.strftime('%b %Y')} - Trade #{trades}")

    else:
        print(f"❌ {Fore.RED}TARGET NOT REACHED{Style.RESET_ALL}")
        print(f"   Final Balance: ${balance:,.2f}")
        print(f"   Time: {weeks} weeks ({weeks/52:.1f} years)")
        print(f"   Reason: {'Balance too low' if balance < 10 else 'Time limit reached'}")

    print()
    print("-" * 80)
    print()

    return balance >= TARGET_BALANCE


# Run scenarios
print()

# Optimistic scenario
simulate_growth(0.60, "OPTIMISTIC (60% Win Rate)", Fore.GREEN)

# Realistic scenario
simulate_growth(0.50, "REALISTIC (50% Win Rate)", Fore.YELLOW)

# Conservative scenario
simulate_growth(0.45, "CONSERVATIVE (45% Win Rate)", Fore.CYAN)

# Pessimistic scenario
simulate_growth(0.40, "PESSIMISTIC (40% Win Rate)", Fore.RED)

print("=" * 80)
print()
print(f"{Fore.YELLOW}⚠️  DISCLAIMER:{Style.RESET_ALL}")
print("   - These are MATHEMATICAL PROJECTIONS, not guarantees")
print("   - Crypto markets are highly volatile and unpredictable")
print("   - Past performance does NOT indicate future results")
print("   - Win rates will vary based on market conditions")
print("   - Learning Engine will improve performance over time")
print("   - ONLY invest what you can afford to lose")
print()
print(f"{Fore.GREEN}💡 REALITY CHECK:{Style.RESET_ALL}")
print("   - First 10-20 trades = learning phase (lower win rate expected)")
print("   - After 30+ trades = optimized filters (higher win rate likely)")
print("   - Bear markets = harder (longer timeline)")
print("   - Bull markets = easier (shorter timeline)")
print("   - Your actual timeline will likely be between Realistic & Conservative")
print()
print("=" * 80)
