#!/usr/bin/env python3
"""Auto Trading Bot - Automated Crypto Trading with CADVI Signals

Features:
- Automatically trades top CADVI predictions
- Professional risk management with position sizing
- Real-time performance tracking
- Dry-run mode for safe testing
- Automatic stop-loss and take-profit orders

SAFETY FIRST:
- Start with dry_run=True to test without real money
- Review all settings before enabling live trading
- Never invest more than you can afford to lose
"""
import argparse
import time
from datetime import datetime
from colorama import Fore, Style, init

from api.cmc_client import CoinMarketCapClient
from api.enhanced_analyzer import EnhancedCryptoAnalyzer
from api.binance_client import load_binance_client
from api.telegram_notifier import notifier
from api.learning_engine import TradingLearningEngine
from api.dynamic_targets import calculate_dynamic_targets, explain_targets
from api.position_monitor import PositionMonitor
from api.correlation_analyzer import CorrelationAnalyzer
from api.liquidity_checker import LiquidityChecker

init(autoreset=True)


def print_header(dry_run: bool):
    """Print trading bot header"""
    mode = "DRY RUN MODE 🧪" if dry_run else "LIVE TRADING MODE 🔴"
    mode_color = Fore.YELLOW if dry_run else Fore.RED

    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}{Style.BRIGHT}CADVI AUTO TRADER{Style.RESET_ALL}")
    print(f"{mode_color}{Style.BRIGHT}{mode}{Style.RESET_ALL}")
    if not dry_run:
        print(f"{Fore.RED}⚠️  LIVE TRADING - REAL MONEY AT RISK ⚠️{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}⚠️  High Risk | Not Financial Advice | Trade at Your Own Risk{Style.RESET_ALL}")
    print("=" * 80 + "\n")


def print_portfolio_status(client):
    """Print current portfolio state"""
    summary = client.get_portfolio_summary()

    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}PORTFOLIO STATUS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

    # Balance
    balance = summary['total_balance_usdt']
    pnl = summary['pnl_usdt']
    pnl_pct = summary['pnl_pct']
    pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED

    print(f"Total Balance:     ${balance:.2f} USDT")
    print(f"Total P&L:         {pnl_color}{pnl:+.2f} USDT ({pnl_pct:+.2f}%){Style.RESET_ALL}")
    print(f"Daily P&L:         {pnl_color}{summary['daily_pnl']:+.2f} USDT{Style.RESET_ALL}")

    # PHOENIX PROTOCOL & VAULT METRICS (The Immortal Compounder)
    peak = summary['peak_balance_usdt']
    current_dd = summary['current_drawdown_pct']
    max_dd = summary['max_drawdown_pct']
    risk_mode = summary.get('risk_mode', 'NORMAL')
    risk_mult = summary.get('risk_multiplier', 1.0)
    vault_balance = summary.get('vault_balance_usdt', 0.0)
    tradable_balance = summary.get('tradable_balance_usdt', 0.0)

    # Color coding based on drawdown
    dd_color = Fore.GREEN if current_dd < 20 else Fore.YELLOW if current_dd < 30 else Fore.RED

    print(f"\n{Fore.CYAN}🦅 Phoenix Protocol (Auto-Recovery):{Style.RESET_ALL}")
    print(f"Mode:              {dd_color}{risk_mode}{Style.RESET_ALL} (Multiplier: {risk_mult:.2f}x)")
    print(f"Current Drawdown:  {dd_color}{current_dd:.1f}%{Style.RESET_ALL}")
    print(f"Max Drawdown:      {dd_color}{max_dd:.1f}%{Style.RESET_ALL} (worst ever)")
    print(f"Peak Balance:      ${peak:.2f} USDT")

    print(f"\n{Fore.CYAN}💰 Virtual Profit Vault (Immortality Engine):{Style.RESET_ALL}")
    print(f"Locked Profits:    {Fore.GREEN}${vault_balance:.2f} USDT{Style.RESET_ALL} ← Safe forever!")
    print(f"Tradable Capital:  ${tradable_balance:.2f} USDT ← Active trading")

    # Exposure
    exposure = summary['total_exposure_usdt']
    exposure_pct = summary['exposure_pct']
    print(f"\nTotal Exposure:    ${exposure:.2f} USDT ({exposure_pct:.1f}%)")

    # Positions
    print(f"Open Positions:    {summary['positions_count']}")

    if summary['positions']:
        print(f"\n{Fore.YELLOW}Open Positions:{Style.RESET_ALL}")
        for symbol, pos in summary['positions'].items():
            print(f"  {symbol:8s} {pos['amount']:.4f} @ ${pos['price']:.6f} = ${pos['usdt_value']:.2f}")

    # PROFIT WITHDRAWAL RECOMMENDATION (Manual Safety Net)
    withdrawal = summary.get('withdrawal_recommendation')
    if withdrawal:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}💰 PROFIT-TAKING ALERT!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Withdraw: ${withdrawal['amount_usdt']:.2f} USDT (Vault Balance){Style.RESET_ALL}")
        print(f"{Fore.GREEN}   Reason: {withdrawal['reason']}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}   New balance: ${withdrawal['new_balance']:.2f} USDT{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   ⚠️  Vault is virtual - real withdrawal is safer!{Style.RESET_ALL}")

    # Trading status
    if summary['trading_enabled']:
        print(f"\n{Fore.GREEN}✓ Trading Enabled{Style.RESET_ALL}")
    else:
        if summary['drawdown_kill_switch']:
            print(f"\n{Fore.RED}⛔ Trading DISABLED - Phoenix Protocol Failed (40% DD){Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⛔ Trading Disabled (Daily loss limit reached){Style.RESET_ALL}")

    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def print_trade_statistics(client):
    """Print trading performance statistics"""
    stats = client.get_trade_statistics()

    if stats['total_trades'] == 0:
        print(f"{Fore.YELLOW}No trades yet{Style.RESET_ALL}\n")
        return

    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}TRADING STATISTICS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

    win_rate = stats['win_rate'] * 100
    win_rate_color = Fore.GREEN if win_rate >= 50 else Fore.RED

    print(f"Total Trades:      {stats['total_trades']}")
    print(f"Closed Trades:     {stats['closed_trades']}")
    print(f"Wins / Losses:     {Fore.GREEN}{stats['wins']}{Style.RESET_ALL} / {Fore.RED}{stats['losses']}{Style.RESET_ALL}")
    print(f"Win Rate:          {win_rate_color}{win_rate:.1f}%{Style.RESET_ALL}")
    print(f"Avg Win:           {Fore.GREEN}+{stats['avg_win_pct']:.2f}%{Style.RESET_ALL}")
    print(f"Avg Loss:          {Fore.RED}-{stats['avg_loss_pct']:.2f}%{Style.RESET_ALL}")
    print(f"Profit Factor:     {stats['profit_factor']:.2f}")

    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")


def get_trading_opportunities(top_n: int = 5, min_score: int = 65, learning_engine: TradingLearningEngine = None, binance_client=None) -> list:
    """Scan market and get top trading opportunities

    Args:
        top_n: Number of opportunities to return
        min_score: Minimum score threshold
        learning_engine: Optional learning engine for adaptive filtering
        binance_client: Optional Binance client to verify symbol existence

    Returns:
        List of (symbol, coin_data) tuples
    """
    print(f"{Fore.YELLOW}Scanning market...{Style.RESET_ALL}", end=" ", flush=True)

    # Fetch CoinMarketCap data
    client = CoinMarketCapClient()
    coins_data = client.get_latest_listings(limit=1000)

    if not coins_data:
        print(f"{Fore.RED}Failed{Style.RESET_ALL}")
        return []

    print(f"{Fore.GREEN}✓{Style.RESET_ALL}")

    # Analyze (pass learning engine for adaptive scoring!)
    print(f"{Fore.YELLOW}Analyzing opportunities...{Style.RESET_ALL}", end=" ", flush=True)
    analyzer = EnhancedCryptoAnalyzer(coins_data, learning_engine=learning_engine)
    analyzer.calculate_comprehensive_scores()
    print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

    # Get recommendations with aggressive filtering
    all_spot = analyzer.get_top_by_category('spot', n=50)

    # Get adaptive filters from learning engine
    if learning_engine:
        adaptive_filters = learning_engine.get_adaptive_filters()
        min_score = max(min_score, adaptive_filters['min_score'])
        max_24h_change = adaptive_filters['max_24h_change']
        min_market_cap = adaptive_filters['min_market_cap']
        min_volume_change = adaptive_filters['min_volume_change']
        print(f"{Fore.CYAN}🧠 Using adaptive filters: Score≥{min_score}, 24h<{max_24h_change}%, MCap≥${min_market_cap/1e6:.0f}M{Style.RESET_ALL}")
    else:
        max_24h_change = 15
        min_market_cap = 30_000_000
        min_volume_change = 30

    # AGGRESSIVE FILTERING for high-probability targets (with learning!)
    filtered = []
    for symbol, coin in all_spot:
        # Check BEHAVIOR PATTERNS (not coin name!) - crucial for shitcoins!
        if learning_engine:
            should_trade, reason = learning_engine.should_trade_coin(coin)
            if not should_trade:
                print(f"{Fore.YELLOW}   Skipping {symbol}: {reason}{Style.RESET_ALL}")
                continue

        # Must meet ALL criteria:
        score_ok = coin['enhanced_score'] >= min_score
        not_overextended = coin['change_24h'] < max_24h_change  # Adaptive! (less important now)
        has_momentum = coin['volume_change_24h'] > min_volume_change  # Adaptive!
        wash_clean = coin['wash_trading_confidence'] < 40  # Low wash trading risk
        sufficient_liquidity = coin['market_cap'] > min_market_cap  # Adaptive!
        not_in_freefall = coin['change_24h'] > -15  # Avoid coins crashing hard

        # 24h change is now less strict - we handle it in dynamic TP/SL instead!
        # High pump = we just use tighter TP, not skip entirely
        if score_ok and has_momentum and wash_clean and sufficient_liquidity and not_in_freefall:
            # Only filter extreme pumps (>20%)
            if coin['change_24h'] < 20:
                filtered.append((symbol, coin))

    # Check for valid Binance pairs if client provided
    final_list = []
    if binance_client:
        print(f"{Fore.YELLOW}Verifying pairs on Binance...{Style.RESET_ALL}", end=" ", flush=True)
        verified_count = 0
        for symbol, coin in filtered:
            if len(final_list) >= top_n:
                break
            
            # Check if symbol exists with current quote currency (USDC)
            # We strictly enforce the configured quote currency to avoid 'Invalid Symbol' errors
            # and to respect regulatory restrictions (e.g. MiCA requiring USDC)
            target_pair = f"{symbol}{binance_client.quote_currency}"
            try:
                binance_client.client.get_symbol_ticker(symbol=target_pair)
                final_list.append((symbol, coin))
                verified_count += 1
            except:
                # Symbol not available in this pair (e.g. GOATUSDC doesn't exist)
                # Skip it silently
                pass
        print(f"{Fore.GREEN}✓ Found {verified_count} valid pairs{Style.RESET_ALL}\n")
        return final_list
    else:
        return filtered[:top_n]


def execute_trading_cycle(binance_client, opportunities: list, max_new_positions: int = 2,
                         position_monitor=None, correlation_analyzer=None, liquidity_checker=None):
    """Execute one trading cycle

    Args:
        binance_client: Binance trading client
        opportunities: List of trading opportunities
        max_new_positions: Max new positions to open per cycle
        position_monitor: PositionMonitor instance (optional)
        correlation_analyzer: CorrelationAnalyzer instance (optional)
        liquidity_checker: LiquidityChecker instance (optional)
    """
    if not opportunities:
        print(f"{Fore.YELLOW}No high-quality opportunities found{Style.RESET_ALL}\n")
        return

    print(f"{Fore.GREEN}{Style.BRIGHT}TOP OPPORTUNITIES:{Style.RESET_ALL}\n")

    positions_opened = 0
    current_positions = binance_client.positions.keys()

    for i, (symbol, coin) in enumerate(opportunities, 1):
        if positions_opened >= max_new_positions:
            print(f"\n{Fore.YELLOW}Max new positions limit reached ({max_new_positions}){Style.RESET_ALL}")
            break

        # Skip if already have a position
        if symbol in current_positions:
            print(f"{Fore.YELLOW}#{i} {symbol} - Already have an open position, skipping...{Style.RESET_ALL}")
            continue

        # Display opportunity
        price = coin['price']
        score = coin['enhanced_score']
        change_24h = coin['change_24h']
        kelly = coin['kelly_position_size']

        print(f"{Fore.CYAN}#{i} {symbol}{Style.RESET_ALL}")
        print(f"   Price: ${price:.6f} | Score: {score:.0f} | 24h: {change_24h:+.2f}%")
        print(f"   Kelly: {kelly*100:.1f}% | Market Cap: ${coin['market_cap']/1e6:.1f}M")

        # Calculate position size (use quote currency from client)
        quote = binance_client.quote_currency
        position_usdt = binance_client.calculate_position_size(f"{symbol}{quote}", kelly)

        if position_usdt == 0:
            print(f"   {Fore.RED}⊗ Skipped (position size too small or limits exceeded){Style.RESET_ALL}\n")
            continue

        # NEW: Check correlation with existing positions
        if correlation_analyzer:
            existing_positions = list(binance_client.positions.keys())
            should_trade, corr_reason = correlation_analyzer.check_portfolio_correlation(
                new_symbol=f"{symbol}{quote}",
                existing_positions=existing_positions,
                max_correlation=0.7
            )
            if not should_trade:
                print(f"   {Fore.YELLOW}⊗ Skipped (correlation): {corr_reason}{Style.RESET_ALL}\n")
                continue

        # NEW: Check liquidity
        if liquidity_checker:
            has_liquidity, liq_reason = liquidity_checker.check_liquidity(
                symbol=f"{symbol}{quote}",
                position_size_usdt=position_usdt
            )
            if not has_liquidity:
                print(f"   {Fore.YELLOW}⊗ Skipped (liquidity): {liq_reason}{Style.RESET_ALL}\n")
                continue

        # Calculate DYNAMIC targets based on coin characteristics!
        take_profit_pct, stop_loss_pct = calculate_dynamic_targets(coin)

        print(f"   {Fore.GREEN}→ Opening position: ${position_usdt:.2f} USDT{Style.RESET_ALL}")
        print(f"   🎯 TP: +{take_profit_pct*100:.1f}% | 🛑 SL: -{stop_loss_pct*100:.1f}% (Dynamic!)")

        # Execute trade (use quote currency from client)
        quote = binance_client.quote_currency
        result = binance_client.place_market_buy(
            symbol=f"{symbol}{quote}",
            position_size_usdt=position_usdt,
            stop_loss_pct=stop_loss_pct,  # Dynamic based on coin!
            take_profit_pct=take_profit_pct  # Dynamic based on coin!
        )

        if result:
            positions_opened += 1
            print(f"   {Fore.GREEN}✓ Position opened{Style.RESET_ALL}\n")

            # Store position metadata for monitoring (NEW!)
            if position_monitor and result.get('oco_order_list_id'):
                try:
                    position_monitor.store_position(
                        symbol=f"{symbol}{quote}",
                        entry_price=price,
                        quantity=float(result.get('executedQty', 0)),
                        stop_loss=result.get('stop_loss_price', price * (1 - stop_loss_pct)),
                        take_profit=result.get('take_profit_price', price * (1 + take_profit_pct)),
                        oco_order_list_id=result['oco_order_list_id'],
                        coin_data=coin  # Store coin metrics for later re-evaluation
                    )
                except Exception as e:
                    print(f"   ⚠️ Warning: Failed to store position metadata: {e}")

            # Send enhanced Telegram notification
            notifier.notify_new_position(
                symbol=symbol,
                quantity=result.get('executedQty', 0) if isinstance(result, dict) else 0,
                price=price,
                usdt_value=position_usdt,
                score=score,
                kelly=kelly,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct
            )
        else:
            print(f"   {Fore.RED}✗ Failed to open position{Style.RESET_ALL}\n")

    if positions_opened == 0:
        print(f"{Fore.YELLOW}No new positions opened this cycle{Style.RESET_ALL}\n")


def main():
    """Main auto-trader entry point"""
    parser = argparse.ArgumentParser(
        description='CADVI Auto Trader - Automated Crypto Trading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test without real trading (RECOMMENDED FIRST)
  python auto_trader.py --dry-run

  # Live trading with 3 positions max
  python auto_trader.py --live --max-positions 3

  # Continuous trading (checks every 30 min)
  python auto_trader.py --live --continuous --interval 30

Safety Notes:
  - Always test with --dry-run first
  - Start with small position sizes
  - Monitor regularly
  - Set strict daily loss limits in binance_client.py
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Simulate trades without executing (DEFAULT, RECOMMENDED)'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Enable LIVE TRADING with real money (CAREFUL!)'
    )
    parser.add_argument(
        '--max-positions',
        type=int,
        default=3,
        help='Max new positions per cycle (default: 3, SPRAY AND PRAY: Diversify quickly)'
    )
    parser.add_argument(
        '--min-score',
        type=int,
        default=65,
        help='Minimum score threshold (default: 65)'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuously (otherwise runs once)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Minutes between cycles in continuous mode (default: 30)'
    )
    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Auto-confirm (skip manual confirmation for background mode)'
    )

    args = parser.parse_args()

    # Determine dry-run mode
    dry_run = not args.live  # Live mode disables dry-run

    try:
        # Initialize
        print_header(dry_run)

        # Load Binance client
        print(f"{Fore.YELLOW}Connecting to Binance...{Style.RESET_ALL}", end=" ", flush=True)
        binance_client = load_binance_client(dry_run=dry_run)
        print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

        # Initialize Learning Engine
        print(f"{Fore.YELLOW}🧠 Initializing Learning Engine...{Style.RESET_ALL}", end=" ", flush=True)
        learning_engine = TradingLearningEngine()
        print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

        # Initialize Position Monitor (NEW!)
        print(f"{Fore.YELLOW}📊 Initializing Position Monitor...{Style.RESET_ALL}", end=" ", flush=True)
        position_monitor = PositionMonitor(
            binance_client=binance_client,
            learning_engine=learning_engine,
            telegram_notifier=notifier
        )
        print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

        # Initialize Risk Management Tools (NEW!)
        print(f"{Fore.YELLOW}🛡️ Initializing Risk Management...{Style.RESET_ALL}", end=" ", flush=True)
        correlation_analyzer = CorrelationAnalyzer(binance_client=binance_client)
        liquidity_checker = LiquidityChecker(binance_client=binance_client)
        print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

        # Show learning report
        print(learning_engine.generate_learning_report())

        # Show portfolio status
        print_portfolio_status(binance_client)

        # Show statistics
        print_trade_statistics(binance_client)

        # Confirmation for live trading
        if not dry_run and not args.confirm:
            print(f"{Fore.RED}{Style.BRIGHT}⚠️  LIVE TRADING MODE - REAL MONEY AT RISK ⚠️{Style.RESET_ALL}")
            confirm = input(f"{Fore.YELLOW}Type 'YES' to confirm live trading: {Style.RESET_ALL}")
            if confirm != 'YES':
                print(f"{Fore.RED}Live trading cancelled{Style.RESET_ALL}")
                return
            print()
        elif not dry_run and args.confirm:
            print(f"{Fore.GREEN}✓ Auto-confirmed (--confirm flag){Style.RESET_ALL}\n")

        # Trading loop
        cycle = 0
        last_daily_report = datetime.now()

        # Send startup notification
        if not dry_run:
            summary = binance_client.get_portfolio_summary()
            notifier.notify_bot_startup(
                balance=summary['total_balance_usdt'],
                positions=summary['positions_count'],
                exposure_pct=summary['exposure_pct']
            )

        while True:
            cycle += 1
            print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{Style.BRIGHT}TRADING CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")

            # STEP 1: Monitor existing positions (NEW - runs FIRST!)
            print(f"{Fore.YELLOW}📊 Monitoring open positions...{Style.RESET_ALL}", end=" ", flush=True)
            try:
                monitor_results = position_monitor.scan_positions()
                print(f"{Fore.GREEN}✓{Style.RESET_ALL}\n")

                # Handle triggered exits
                for exit_info in monitor_results['triggered_exits']:
                    exit_type = exit_info['exit_type']
                    pnl = exit_info['pnl_pct']
                    color = Fore.GREEN if pnl > 0 else Fore.RED
                    print(f"{color}💰 Position {exit_info['symbol']} exited via {exit_type}: {pnl:+.1f}%{Style.RESET_ALL}")

                    # Log the exit
                    position_monitor.log_triggered_exit(exit_info)

                    # Send enhanced notification
                    if notifier:
                        notifier.notify_position_exit(
                            symbol=exit_info['symbol'],
                            exit_type=exit_type,
                            quantity=exit_info['quantity'],
                            entry_price=exit_info['entry_price'],
                            exit_price=exit_info['exit_price'],
                            pnl_pct=pnl,
                            hold_time_hours=exit_info['hold_time_hours'],
                            usdt_value=exit_info['value']
                        )

                # Apply trailing stops and handle manual exits
                for adjustment in monitor_results['needs_adjustment']:
                    if adjustment['action'] == 'MANUAL_EXIT_SL':
                        # CRITICAL: Manual Stop-Loss exit (TP/SL reached without OCO)
                        success = position_monitor.execute_manual_exit(
                            symbol=adjustment['symbol'],
                            reason=adjustment['reason'],
                            exit_type='SL'
                        )
                        if success:
                            print(f"{Fore.RED}🚨 MANUAL STOP-LOSS: {adjustment['symbol']} at ${adjustment['current_price']:.6f} ({adjustment['profit_pct']:+.1f}%){Style.RESET_ALL}")

                    elif adjustment['action'] == 'MANUAL_EXIT_TP':
                        # CRITICAL: Manual Take-Profit exit (TP/SL reached without OCO)
                        success = position_monitor.execute_manual_exit(
                            symbol=adjustment['symbol'],
                            reason=adjustment['reason'],
                            exit_type='TP'
                        )
                        if success:
                            print(f"{Fore.GREEN}💰 MANUAL TAKE-PROFIT: {adjustment['symbol']} at ${adjustment['current_price']:.6f} (+{adjustment['profit_pct']:.1f}%){Style.RESET_ALL}")

                    elif adjustment['action'] == 'TRAILING_STOP':
                        success = position_monitor.apply_trailing_stop(
                            symbol=adjustment['symbol'],
                            current_profit_pct=adjustment['profit_pct']
                        )
                        if success:
                            print(f"{Fore.GREEN}🛡️ Trailing stop applied to {adjustment['symbol']} (+{adjustment['profit_pct']:.1f}%){Style.RESET_ALL}")
                            # Enhanced notification already sent by position_monitor

                    elif adjustment['action'] == 'PARTIAL_EXIT':
                        success = position_monitor.execute_partial_exit(
                            symbol=adjustment['symbol'],
                            current_profit_pct=adjustment['profit_pct']
                        )
                        if success:
                            print(f"{Fore.GREEN}💰 Partial profit taken on {adjustment['symbol']} (+{adjustment['profit_pct']:.1f}%){Style.RESET_ALL}")
                            # Enhanced notification already sent by position_monitor

                # Show active positions
                if monitor_results['active_positions']:
                    print(f"\n{Fore.CYAN}Active Positions:{Style.RESET_ALL}")
                    for pos in monitor_results['active_positions'][:5]:  # Show top 5
                        profit_color = Fore.GREEN if pos['profit_pct'] > 0 else Fore.RED
                        print(f"  {pos['symbol']}: {profit_color}{pos['profit_pct']:+.1f}%{Style.RESET_ALL} | Age: {pos['age_hours']:.1f}h")
                    print()

            except Exception as e:
                print(f"{Fore.RED}Error monitoring positions: {e}{Style.RESET_ALL}\n")

            # STEP 2: Get opportunities (with learning!)
            try:
                opportunities = get_trading_opportunities(top_n=10, min_score=args.min_score, learning_engine=learning_engine, binance_client=binance_client)

                # STEP 3: Execute trades (pass all risk management tools)
                execute_trading_cycle(
                    binance_client,
                    opportunities,
                    max_new_positions=args.max_positions,
                    position_monitor=position_monitor,
                    correlation_analyzer=correlation_analyzer,
                    liquidity_checker=liquidity_checker
                )
            except Exception as e:
                print(f"{Fore.RED}Error in trading cycle: {e}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Skipping this cycle and continuing...{Style.RESET_ALL}\n")
                import traceback
                traceback.print_exc()

            # Update portfolio status
            try:
                print_portfolio_status(binance_client)
            except Exception as e:
                print(f"{Fore.RED}Error updating portfolio status: {e}{Style.RESET_ALL}\n")

            # Show learning insights every 5 cycles
            if cycle % 5 == 0:
                print(f"\n{Fore.CYAN}🧠 LEARNING UPDATE (Cycle #{cycle}):{Style.RESET_ALL}")
                insights = learning_engine.get_pattern_insights()
                if insights['recommendations']:
                    for rec in insights['recommendations']:
                        print(f"   {rec}")
                print()

            # Send daily status report (every 24 hours)
            if not dry_run and (datetime.now() - last_daily_report).total_seconds() >= 86400:
                summary = binance_client.get_portfolio_summary()
                stats = binance_client.get_trade_statistics()

                # Get position details
                positions_text = ""
                for symbol, pos in summary['positions'].items():
                    if pos['usdt_value'] > 1:
                        positions_text += f"• {symbol}: ${pos['usdt_value']:.2f}\n"

                notifier.send_message(
                    f"📊 *DAILY STATUS UPDATE*\n\n"
                    f"💰 Balance: ${summary['total_balance_usdt']:.2f}\n"
                    f"📈 P&L: {summary['pnl_usdt']:+.2f} USDT ({summary['pnl_pct']:+.2f}%)\n"
                    f"📊 Exposure: {summary['exposure_pct']:.1f}%\n\n"
                    f"*Positions ({summary['positions_count']}):*\n{positions_text}\n"
                    f"*Trading Stats:*\n"
                    f"• Total Trades: {stats['total_trades']}\n"
                    f"• Win Rate: {stats['win_rate']*100:.1f}%\n\n"
                    f"🤖 Bot running smoothly! ✅",
                    silent=True
                )
                last_daily_report = datetime.now()

            if not args.continuous:
                break

            # Wait for next cycle
            wait_minutes = args.interval
            print(f"{Fore.YELLOW}Next cycle in {wait_minutes} minutes...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
            time.sleep(wait_minutes * 60)

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Trading stopped by user{Style.RESET_ALL}")
        if binance_client:
            print_portfolio_status(binance_client)
            print_trade_statistics(binance_client)

    except ValueError as e:
        print(f"{Fore.RED}Configuration error: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Make sure .env file has BINANCE_API_KEY and BINANCE_SECRET_KEY{Style.RESET_ALL}")
        raise  # Critical error - must exit

    except Exception as e:
        print(f"\n{Fore.RED}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.RED}UNEXPECTED ERROR IN BOT{Style.RESET_ALL}")
        print(f"{Fore.RED}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}\n")
        import traceback
        traceback.print_exc()
        print(f"\n{Fore.YELLOW}Bot encountered an unexpected error.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}The watchdog will restart it automatically.{Style.RESET_ALL}\n")
        # Don't raise - let watchdog restart us


if __name__ == "__main__":
    main()
