#!/usr/bin/env python3
"""Volatility Compression → Expansion Breakout Bot

STRATEGY:
1. Scan Top 50-100 USDT coins by volume
2. Detect compression (BB Width < 3%, ATR < 15th percentile, Keltner squeeze)
3. Wait for breakout (Volume 2.8×, Price break, RSI 55-70, Wick < 30%)
4. Enter with fixed 1.25% risk
5. Trail stops: 15% profit → 5% trail, 30% profit → 3% trail

GOLDEN NUMBERS - HARD-CODED:
- Risk per trade: 1.25%
- Max exposure: 60%
- Daily loss limit: -5%
- Drawdown limit: 20% (reduce size), 40% (stop trading)
- Consecutive failures: 2 → 7-day blacklist

NO MODIFICATIONS ALLOWED TO CORE PARAMETERS.
"""
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Import core modules
from core.strategy.compression_detector import CompressionDetector
from core.strategy.breakout_trigger import BreakoutTrigger, Direction
from core.risk.position_sizer import PositionSizer
from core.risk.kill_switch import KillSwitch
from core.execution.stop_manager import StopManager
from core.execution.trailing_logic import TrailingLogic
from core.learning.coin_ranker import CoinRanker
from core.infra.binance_market_data import BinanceMarketData
from core.infra.binance_executor import BinanceExecutor

init(autoreset=True)
load_dotenv()


class VolatilityBot:
    """Main trading bot orchestrating the entire strategy"""

    def __init__(self, dry_run: bool = True, interval_minutes: int = 5):
        """Initialize bot

        Args:
            dry_run: If True, simulates trades without executing
            interval_minutes: Scan interval in minutes
        """
        # Load API keys (support both BINANCE_API_SECRET and BINANCE_SECRET_KEY)
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET') or os.getenv('BINANCE_SECRET_KEY')

        if not api_key or not api_secret:
            raise ValueError("BINANCE_API_KEY and BINANCE_API_SECRET/BINANCE_SECRET_KEY must be set in .env")

        # Initialize components
        self.dry_run = dry_run
        self.interval_minutes = interval_minutes

        # Strategy
        self.compression_detector = CompressionDetector()
        self.breakout_trigger = BreakoutTrigger()

        # Risk
        self.position_sizer = PositionSizer()
        self.kill_switch = KillSwitch()

        # Execution
        self.stop_manager = StopManager()
        self.trailing_logic = TrailingLogic()

        # Learning
        self.coin_ranker = CoinRanker()

        # Infrastructure
        self.market_data = BinanceMarketData(api_key, api_secret)
        self.executor = BinanceExecutor(api_key, api_secret, dry_run=dry_run)

        # State
        self.watchlist = []  # Coins in compression
        self.last_scan_time = None

        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}VOLATILITY BREAKOUT BOT v2.0{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"Mode: {Fore.YELLOW if dry_run else Fore.RED}{'DRY RUN' if dry_run else 'LIVE TRADING'}{Style.RESET_ALL}")
        print(f"Scan Interval: {interval_minutes} minutes")
        print(f"Strategy: Volatility Compression → Expansion Breakout")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

    def scan_market_for_compression(self, top_n: int = 100) -> list:
        """Scan market for coins in compression

        Args:
            top_n: Number of top coins to scan

        Returns:
            List of (symbol, compression_score) tuples
        """
        print(f"\n{Fore.YELLOW}Scanning market for compression...{Style.RESET_ALL}")

        # Get top coins by volume (Default to USDC for MiCA compliance)
        symbols = self.market_data.get_top_symbols_by_volume(limit=top_n, quote_asset="USDC")
        print(f"Scanning {len(symbols)} top USDC coins by 24h volume...")

        compressed_coins = []

        for i, symbol in enumerate(symbols):
            # Rate limiting display
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{len(symbols)}...")

            # Fetch 5m klines (need 300+ for ATR percentile)
            klines = self.market_data.get_klines(symbol, self.market_data.TIMEFRAME_5M, limit=500)

            if not klines:
                continue

            # Check compression
            is_compressed, details = self.compression_detector.is_compressed(
                klines['highs'],
                klines['lows'],
                klines['closes']
            )

            if is_compressed:
                score = self.compression_detector.get_compression_score(
                    klines['highs'],
                    klines['lows'],
                    klines['closes']
                )
                compressed_coins.append((symbol, score, details))

        # Rank using learning engine if available
        if self.coin_ranker.is_learning_active() and compressed_coins:
            coin_symbols = [c[0] for c in compressed_coins]
            ranked = self.coin_ranker.rank_coins(coin_symbols)
            ranked_map = {symbol: score for symbol, score in ranked}

            # Re-sort by learning score
            compressed_coins.sort(key=lambda x: ranked_map.get(x[0], 50), reverse=True)

        print(f"\n{Fore.GREEN}✓ Found {len(compressed_coins)} coins in compression{Style.RESET_ALL}")

        if compressed_coins:
            print(f"\n{Fore.CYAN}Top Compressed Coins:{Style.RESET_ALL}")
            for symbol, score, details in compressed_coins[:10]:
                print(f"  {symbol:12s} Score: {score:5.1f} | BB: {details['bb_width']:.4f} | ATR Pctl: {details['atr_percentile']:.1f}%")

        return compressed_coins

    def check_for_breakouts(self, compressed_coins: list) -> list:
        """Check compressed coins for breakout signals

        Args:
            compressed_coins: List of compressed coins from scan

        Returns:
            List of breakout signals
        """
        if not compressed_coins:
            return []

        print(f"\n{Fore.YELLOW}Checking for breakouts...{Style.RESET_ALL}")

        breakouts = []

        for symbol, comp_score, comp_details in compressed_coins:
            # Fetch fresh data
            klines = self.market_data.get_klines(symbol, self.market_data.TIMEFRAME_5M, limit=100)

            if not klines:
                continue

            # Check for breakout
            direction, details = self.breakout_trigger.detect_breakout(
                klines['opens'],
                klines['highs'],
                klines['lows'],
                klines['closes'],
                klines['volumes']
            )

            # ONLY ALLOW LONG TRADES FOR SPOT
            if direction == Direction.LONG:
                signal_strength = self.breakout_trigger.calculate_signal_strength(details)
                breakouts.append({
                    'symbol': symbol,
                    'direction': direction,
                    'signal_strength': signal_strength,
                    'details': details,
                    'compression_score': comp_score,
                    'current_price': klines['closes'][-1],
                    'klines': klines
                })
            elif direction == Direction.SHORT:
                print(f"  {Fore.BLACK}{Style.BRIGHT}Skipping SHORT signal for {symbol} (Spot account restriction){Style.RESET_ALL}")

        if breakouts:
            # Sort by signal strength
            breakouts.sort(key=lambda x: x['signal_strength'], reverse=True)

            print(f"\n{Fore.GREEN}🔥 {len(breakouts)} BREAKOUT SIGNAL(S) DETECTED! 🔥{Style.RESET_ALL}")
            for signal in breakouts:
                # CRITICAL FIX: Handle None values in signal details
                vol_mult = signal['details'].get('volume_multiplier', 0)
                rsi = signal['details'].get('rsi')
                rsi_str = f"{rsi:.1f}" if rsi is not None else "N/A"
                print(f"  {signal['symbol']:12s} {signal['direction'].value:5s} | Strength: {signal['signal_strength']:5.1f} | Vol: {vol_mult:.2f}× | RSI: {rsi_str}")

        return breakouts

    def execute_trade(self, signal: dict) -> bool:
        """Execute trade from breakout signal

        Args:
            signal: Breakout signal dict

        Returns:
            True if trade executed successfully
        """
        symbol = signal['symbol']
        direction = signal['direction']
        klines = signal['klines']

        # SAFETY CHECK: Only LONG allowed on Spot
        if direction != Direction.LONG:
            print(f"{Fore.RED}❌ Trade blocked: Spot accounts cannot execute {direction.value} signals{Style.RESET_ALL}")
            return False

        print(f"\n{Fore.YELLOW}Executing trade: {symbol} {direction.value}{Style.RESET_ALL}")

        # CRITICAL FIX: Fetch FRESH price before execution (not stale signal price)
        current_price = self.market_data.get_current_price(symbol)
        if not current_price:
            print(f"{Fore.RED}❌ Trade blocked: Could not fetch fresh price for {symbol}{Style.RESET_ALL}")
            return False

        signal_price = signal['current_price']
        # CRITICAL FIX: Guard against division by zero
        if signal_price > 0:
            price_diff_pct = abs((current_price - signal_price) / signal_price) * 100
            if price_diff_pct > 1.0:
                print(f"{Fore.YELLOW}⚠️ Price moved {price_diff_pct:.2f}% since signal (${signal_price:.6f} → ${current_price:.6f}){Style.RESET_ALL}")

        # 1. Check kill switches
        try:
            account_balance = self.executor.get_account_balance()
        except Exception as e:
            print(f"{Fore.RED}❌ Trade blocked: Could not fetch account balance: {e}{Style.RESET_ALL}")
            return False

        kill_check = self.kill_switch.is_trading_allowed(account_balance, symbol)

        if not kill_check['allowed']:
            print(f"{Fore.RED}❌ Trade blocked: {kill_check['reason']}{Style.RESET_ALL}")
            return False

        # 2. Calculate stop loss
        atr = self.compression_detector.calculate_atr(klines['highs'], klines['lows'], klines['closes'])
        breakout_low = signal['details']['break_price']  # This is the breakout level

        stop_data = self.stop_manager.calculate_initial_stop_loss(
            current_price,
            atr,
            breakout_low,
            direction.value
        )

        print(f"  Entry: ${current_price:.6f}")
        print(f"  Stop Loss: ${stop_data['stop_price']:.6f} ({stop_data['method']}, {stop_data['stop_distance_pct']:.2f}%)")

        # 3. Calculate position size
        current_exposure = self.executor.get_total_exposure_pct(account_balance)
        position_multiplier = kill_check['position_multiplier']

        size_data = self.position_sizer.calculate_position_size(
            account_balance * position_multiplier,  # Apply drawdown reduction
            current_price,
            stop_data['stop_price'],
            current_exposure
        )

        if not size_data['valid']:
            print(f"{Fore.RED}❌ Invalid position size: {size_data['reason']}{Style.RESET_ALL}")
            return False

        print(f"  Position Size: ${size_data['position_size_usdt']:.2f} USDT ({size_data['position_size_coins']:.6f} coins)")
        print(f"  Risk: ${size_data['risk_amount_usdt']:.2f} ({self.position_sizer.RISK_PER_TRADE_PCT}%)")
        print(f"  Exposure: {current_exposure:.1f}% → {current_exposure + (size_data['position_size_usdt']/account_balance*100):.1f}%")

        # 4. Execute order
        order_result = self.executor.execute_market_buy(
            symbol,
            size_data['position_size_coins'],
            current_price,
            max_slippage_pct=self.position_sizer.MAX_SLIPPAGE_PCT
        )

        if not order_result:
            print(f"{Fore.RED}❌ Order execution failed{Style.RESET_ALL}")
            return False

        # CRITICAL FIX: Validate order result has required fields
        required_fields = ['avgPrice', 'executedQty', 'orderId']
        for field in required_fields:
            if field not in order_result:
                print(f"{Fore.RED}❌ Order result missing '{field}' field. Order may be orphaned!{Style.RESET_ALL}")
                print(f"  Full result: {order_result}")
                return False

        # Validate values are not zero/empty
        if order_result['executedQty'] <= 0:
            print(f"{Fore.RED}❌ Order executed 0 quantity. No position created.{Style.RESET_ALL}")
            return False

        if order_result['avgPrice'] <= 0:
            print(f"{Fore.RED}❌ Order has invalid avg price. Using current price as fallback.{Style.RESET_ALL}")
            order_result['avgPrice'] = current_price

        # 5. Track position
        self.executor.add_position(
            symbol,
            order_result['avgPrice'],
            order_result['executedQty'],
            stop_data['stop_price']
        )

        print(f"{Fore.GREEN}✓ Trade executed successfully!{Style.RESET_ALL}")
        print(f"  Order ID: {order_result['orderId']}")
        print(f"  Filled: {order_result['executedQty']:.6f} @ ${order_result['avgPrice']:.6f}")

        return True

    def manage_positions(self):
        """Manage open positions (stops, trailing, exits)"""
        positions = self.executor.get_all_positions()

        if not positions:
            return

        print(f"\n{Fore.CYAN}Managing {len(positions)} position(s)...{Style.RESET_ALL}")

        for symbol, position in list(positions.items()):
            # Get current price
            current_price = self.market_data.get_current_price(symbol)
            if not current_price:
                continue

            entry_price = position['entry_price']
            entry_time = datetime.fromisoformat(position['entry_time'])
            current_stop = position['stop_loss']
            peak_price = position['peak_price']

            # CRITICAL FIX: Guard against division by zero (corrupted position data)
            if entry_price <= 0:
                print(f"  {Fore.RED}⚠️ Invalid entry_price for {symbol}, skipping{Style.RESET_ALL}")
                continue

            # Calculate profit
            profit_pct = ((current_price - entry_price) / entry_price) * 100

            print(f"\n  {symbol}: ${current_price:.6f} ({profit_pct:+.2f}%)")

            # Update peak
            new_peak = max(peak_price, current_price)
            if new_peak > peak_price:
                self.executor.update_position_peak(symbol, new_peak)
                peak_price = new_peak

            # Check time exit
            time_check = self.stop_manager.check_time_exit(
                entry_time,
                datetime.now(),
                entry_price,
                current_price
            )

            if time_check['should_exit']:
                print(f"  {Fore.YELLOW}⏰ Time exit triggered: {time_check['reason']}{Style.RESET_ALL}")
                self._close_position(symbol, position, current_price, "Time Exit")
                continue

            # Check stop hit
            if self.trailing_logic.check_stop_hit(current_price, current_stop):
                print(f"  {Fore.RED}🛑 Stop loss hit at ${current_price:.6f}{Style.RESET_ALL}")
                self._close_position(symbol, position, current_price, "Stop Loss")
                continue

            # Update trailing stop
            trailing_update = self.trailing_logic.update_trailing_stop(
                entry_price,
                current_price,
                peak_price,
                current_stop
            )

            if trailing_update['updated']:
                print(f"  {Fore.GREEN}📈 Trailing stop updated: ${current_stop:.6f} → ${trailing_update['new_stop']:.6f}{Style.RESET_ALL}")
                print(f"     {trailing_update['reason']}")
                self.executor.update_position_stop(symbol, trailing_update['new_stop'])
            else:
                # Check breakeven move
                initial_stop = current_stop  # Simplified; should track separately
                be_check = self.stop_manager.should_move_to_breakeven(
                    entry_price,
                    current_price,
                    initial_stop
                )

                if be_check['should_move'] and be_check['new_stop'] > current_stop:
                    print(f"  {Fore.CYAN}🎯 Moving to breakeven: ${be_check['new_stop']:.6f}{Style.RESET_ALL}")
                    self.executor.update_position_stop(symbol, be_check['new_stop'])

    def _close_position(self, symbol: str, position: dict, exit_price: float, reason: str):
        """Close a position

        Args:
            symbol: Trading symbol
            position: Position data
            exit_price: Exit price
            reason: Exit reason
        """
        quantity = position['quantity']
        entry_price = position['entry_price']

        # Execute sell
        order = self.executor.execute_market_sell(symbol, quantity)

        if order:
            # CRITICAL FIX: Guard against division by zero
            if entry_price <= 0:
                profit_pct = 0.0
            else:
                profit_pct = ((exit_price - entry_price) / entry_price) * 100
            is_win = profit_pct > 0

            # Record for learning
            self.coin_ranker.record_trade(symbol, profit_pct)
            self.kill_switch.record_trade_result(symbol, is_win)

            # Remove position
            self.executor.remove_position(symbol)

            # Display result
            color = Fore.GREEN if is_win else Fore.RED
            print(f"\n  {color}{'✓ WIN' if is_win else '✗ LOSS'}: {symbol} closed at ${exit_price:.6f} ({profit_pct:+.2f}%){Style.RESET_ALL}")
            print(f"  Reason: {reason}")

    def run(self, max_positions: int = 4):
        """Main bot loop

        Args:
            max_positions: Maximum simultaneous positions
        """
        print(f"{Fore.GREEN}Bot started. Press Ctrl+C to stop.{Style.RESET_ALL}\n")

        try:
            while True:
                print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")

                # 1. Manage existing positions
                self.manage_positions()

                # 2. Check if we can open new positions
                open_positions = len(self.executor.get_all_positions())
                can_trade = open_positions < max_positions

                if can_trade:
                    # 3. Scan for compression (every interval)
                    compressed = self.scan_market_for_compression(top_n=100)

                    # 4. Check for breakouts
                    breakouts = self.check_for_breakouts(compressed)

                    # 5. Execute trades (limit to available slots)
                    available_slots = max_positions - open_positions
                    for signal in breakouts[:available_slots]:
                        success = self.execute_trade(signal)
                        if success:
                            open_positions += 1
                            if open_positions >= max_positions:
                                break
                else:
                    print(f"\n{Fore.YELLOW}Max positions ({max_positions}) reached. Waiting...{Style.RESET_ALL}")

                # 6. Display status
                self._print_status()

                # 7. Sleep until next scan
                sleep_seconds = self.interval_minutes * 60
                print(f"\n{Fore.CYAN}Next scan in {self.interval_minutes} minutes...{Style.RESET_ALL}")
                time.sleep(sleep_seconds)

        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Bot stopped by user.{Style.RESET_ALL}")
            self._print_final_summary()

    def _print_status(self):
        """Print bot status"""
        try:
            account_balance = self.executor.get_account_balance()
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Could not fetch balance for status: {e}{Style.RESET_ALL}")
            account_balance = 0.0

        positions = self.executor.get_all_positions()
        kill_status = self.kill_switch.get_status(account_balance)

        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}STATUS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"Balance: ${account_balance:.2f} USDT")
        print(f"Peak: ${kill_status['peak_balance']:.2f} USDT")
        print(f"Drawdown: {kill_status['drawdown_pct']:.1f}%")
        print(f"Daily P&L: {kill_status['daily_pnl_pct']:+.2f}%")
        print(f"Open Positions: {len(positions)}")
        print(f"Position Multiplier: {kill_status['position_size_multiplier']:.2f}×")
        print(f"Blacklisted: {kill_status['blacklist_count']} coins")

    def _print_final_summary(self):
        """Print final summary on exit"""
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}FINAL SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

        # Learning summary
        summary = self.coin_ranker.get_performance_summary()
        print(f"Total Trades: {summary['total_trades']}")
        print(f"Coins Tracked: {summary['coins_tracked']}")
        print(f"Learning Active: {'Yes' if summary['learning_active'] else 'No'}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Volatility Compression Breakout Bot")
    parser.add_argument('--live', action='store_true', help='Enable live trading (default: dry run)')
    parser.add_argument('--interval', type=int, default=5, help='Scan interval in minutes (default: 5)')
    parser.add_argument('--max-positions', type=int, default=4, help='Max simultaneous positions (default: 4)')
    parser.add_argument('--confirm', action='store_true', help='Auto-confirm live trading (for background/daemon mode)')

    args = parser.parse_args()

    # Confirm live mode
    if args.live and not args.confirm:
        print(f"\n{Fore.RED}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.RED}{Style.BRIGHT}⚠️  LIVE TRADING MODE - REAL MONEY AT RISK ⚠️{Style.RESET_ALL}")
        print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}\n")
        response = input("Type 'YES' to confirm live trading: ")
        if response != 'YES':
            print("Live trading not confirmed. Exiting.")
            sys.exit(0)

    # Initialize and run bot
    bot = VolatilityBot(dry_run=not args.live, interval_minutes=args.interval)
    bot.run(max_positions=args.max_positions)


if __name__ == '__main__':
    main()
