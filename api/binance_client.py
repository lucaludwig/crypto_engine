"""Binance Trading Client with Professional Risk Management

Features:
- Safe position sizing with hard limits
- Daily loss tracking and auto-shutdown
- Dry-run mode for testing
- Comprehensive trade logging
- Real-time balance tracking
"""
import os
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import json
from pathlib import Path


class BinanceTradeClient:
    """Professional Binance trading client with safety limits"""

    # SAFETY LIMITS - THE IMMORTAL COMPOUNDER 🦅
    MAX_POSITION_SIZE_PCT = 0.20  # Max 20% per trade
    MAX_TOTAL_EXPOSURE_PCT = 0.95  # Max 95% total exposure
    DAILY_LOSS_LIMIT_PCT = 0.25  # Auto-stop if -25% for the day
    MIN_ORDER_VALUE_USDT = 11.0  # Binance minimum (~$10)

    # PHOENIX PROTOCOL LIGHT (Auto-Recovery, Less Aggressive)
    DRAWDOWN_CAUTIOUS_PCT = 0.20   # At 20% DD -> 75% size
    DRAWDOWN_SURVIVAL_PCT = 0.30   # At 30% DD -> 50% size
    DRAWDOWN_KILLSWITCH_PCT = 0.40 # At 40% DD -> Kill (last defense)

    # VIRTUAL PROFIT VAULT (Immortality Engine)
    VAULT_LOCK_RATE = 0.50  # Lock 50% of every new All-Time High profit

    # PROFIT WITHDRAWAL WARNINGS (Manual Safety Net)
    PROFIT_WARNING_THRESHOLD = 0.20  # Warn user after +20% total gain

    def __init__(self, api_key: str, api_secret: str, dry_run: bool = True, quote_currency: str = 'USDT'):
        """Initialize Binance client

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            dry_run: If True, simulate trades without executing (RECOMMENDED for first run)
            quote_currency: Quote currency to use (USDT or USDC)
        """
        self.client = Client(api_key, api_secret)
        self.dry_run = dry_run
        self.quote_currency = quote_currency  # Support both USDT and USDC

        # Trading state
        self.starting_balance_usdt = 0.0
        self.current_balance_usdt = 0.0
        self.daily_pnl = 0.0
        self.today = datetime.now().date()

        # DRAWDOWN TRACKING
        self.peak_balance_usdt = 0.0  # All-time high balance
        self.max_drawdown_pct = 0.0  # Maximum drawdown from peak (%)
        self.current_drawdown_pct = 0.0  # Current drawdown from peak (%)
        self.drawdown_kill_switch_triggered = False  # Emergency stop flag

        # VIRTUAL PROFIT VAULT (Immortality Engine)
        self.vault_balance_usdt = 0.0  # Locked profits (safe from trading)
        self.high_water_mark_usdt = 0.0  # Highest balance ever (for vault calculations)

        # Position tracking
        self.positions: Dict[str, Dict] = {}  # symbol -> position info
        self.oco_orders: Dict[str, int] = {}  # symbol -> orderListId

        # Trade history
        self.trades_file = Path(__file__).parent.parent / "trades_log.json"
        self.load_trade_history()

        # Initialize
        self._sync_account_state()

    def _sync_account_state(self):
        """Sync account balance and positions"""
        try:
            account = self.client.get_account()

            # Calculate total balance in quote currency (USDT or USDC)
            total_usdt = 0.0
            positions = {}

            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked

                if total > 0:
                    if asset in [self.quote_currency, 'USDT', 'USDC', 'BUSD']:
                        # Stablecoins treated as 1:1
                        total_usdt += total
                    else:
                        # Convert to quote currency value
                        try:
                            # Try quote currency pair first
                            ticker = self.client.get_symbol_ticker(symbol=f"{asset}{self.quote_currency}")
                            price = float(ticker['price'])
                            usdt_value = total * price
                            total_usdt += usdt_value

                            # Track as position
                            positions[asset] = {
                                'amount': total,
                                'usdt_value': usdt_value,
                                'price': price
                            }
                        except:
                            # Try USDT as fallback
                            try:
                                ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                                price = float(ticker['price'])
                                usdt_value = total * price
                                total_usdt += usdt_value

                                positions[asset] = {
                                    'amount': total,
                                    'usdt_value': usdt_value,
                                    'price': price
                                }
                            except:
                                # Asset not traded or error
                                pass

            self.current_balance_usdt = total_usdt
            if self.starting_balance_usdt == 0:
                self.starting_balance_usdt = total_usdt
                self.high_water_mark_usdt = total_usdt  # Initialize high water mark

            self.positions = positions

            # UPDATE VIRTUAL VAULT (Lock profits on new ATH)
            if self.current_balance_usdt > self.high_water_mark_usdt:
                new_profit = self.current_balance_usdt - self.high_water_mark_usdt
                # Lock 50% of the NEW profit into vault
                vault_deposit = new_profit * self.VAULT_LOCK_RATE
                self.vault_balance_usdt += vault_deposit
                self.high_water_mark_usdt = self.current_balance_usdt

                if vault_deposit > 0.01:  # Only print if meaningful
                    print(f"💰 Vault: Locked ${vault_deposit:.2f} (Total: ${self.vault_balance_usdt:.2f})")

            # UPDATE PEAK BALANCE AND DRAWDOWN
            if self.current_balance_usdt > self.peak_balance_usdt:
                self.peak_balance_usdt = self.current_balance_usdt
                self.current_drawdown_pct = 0.0
            else:
                if self.peak_balance_usdt > 0:
                    self.current_drawdown_pct = ((self.peak_balance_usdt - self.current_balance_usdt) / self.peak_balance_usdt) * 100
                    if self.current_drawdown_pct > self.max_drawdown_pct:
                        self.max_drawdown_pct = self.current_drawdown_pct

            return True

        except BinanceAPIException as e:
            print(f"Error syncing account: {e}")
            return False

    def get_phoenix_multiplier(self) -> float:
        """Calculate Phoenix Protocol risk multiplier based on drawdown

        PHOENIX PROTOCOL LIGHT - Less aggressive than original
        - Allows recovery with meaningful position sizes
        - Doesn't kill bot completely until 40% DD

        Returns:
            Float 0.5-1.0 (1.0 = normal, 0.5 = survival)
        """
        if self.current_drawdown_pct >= self.DRAWDOWN_SURVIVAL_PCT * 100:
            return 0.50  # Survival Mode (50% size) - Still tradeable!
        elif self.current_drawdown_pct >= self.DRAWDOWN_CAUTIOUS_PCT * 100:
            return 0.75  # Cautious Mode (75% size)
        else:
            return 1.00  # Normal Mode

    def get_tradable_balance(self) -> float:
        """Get balance available for trading (Total - Vault)

        Returns:
            USDT balance that can be used for trading
        """
        return max(0.0, self.current_balance_usdt - self.vault_balance_usdt)

    def get_risk_mode_name(self) -> str:
        """Get human-readable risk mode name"""
        multiplier = self.get_phoenix_multiplier()
        if multiplier == 0.50:
            return "SURVIVAL 🦅"
        elif multiplier == 0.75:
            return "CAUTIOUS ⚠️"
        else:
            return "NORMAL ✓"

    def check_profit_withdrawal(self) -> Optional[Dict]:
        """Check if profits should be withdrawn (Manual Safety Net)

        Vault protects automatically, but user should still manually withdraw!

        Returns:
            Dict with withdrawal recommendation or None
        """
        if self.dry_run:
            return None

        total_pnl = self.current_balance_usdt - self.starting_balance_usdt
        total_pnl_pct = (total_pnl / self.starting_balance_usdt) if self.starting_balance_usdt > 0 else 0

        # Warn at +20% total gain
        if total_pnl_pct >= self.PROFIT_WARNING_THRESHOLD:
            # Suggest withdrawing vault balance (the locked profits)
            withdrawal_amount = self.vault_balance_usdt

            return {
                'should_withdraw': True,
                'amount_usdt': withdrawal_amount,
                'reason': f"Profit +{total_pnl_pct*100:.1f}% (Vault: ${self.vault_balance_usdt:.2f})",
                'new_balance': self.current_balance_usdt - withdrawal_amount,
                'total_pnl': total_pnl,
                'total_pnl_pct': total_pnl_pct
            }

        return None

    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio state"""
        self._sync_account_state()

        # Check if profits should be withdrawn
        withdrawal_recommendation = self.check_profit_withdrawal()

        total_exposure = sum(pos['usdt_value'] for pos in self.positions.values())
        exposure_pct = (total_exposure / self.current_balance_usdt * 100) if self.current_balance_usdt > 0 else 0

        pnl = self.current_balance_usdt - self.starting_balance_usdt
        pnl_pct = (pnl / self.starting_balance_usdt * 100) if self.starting_balance_usdt > 0 else 0

        return {
            'total_balance_usdt': self.current_balance_usdt,
            'tradable_balance_usdt': self.get_tradable_balance(),
            'vault_balance_usdt': self.vault_balance_usdt,
            'starting_balance_usdt': self.starting_balance_usdt,
            'pnl_usdt': pnl,
            'pnl_pct': pnl_pct,
            'total_exposure_usdt': total_exposure,
            'exposure_pct': exposure_pct,
            'positions_count': len(self.positions),
            'positions': self.positions,
            'daily_pnl': self.daily_pnl,
            'trading_enabled': self._is_trading_enabled(),
            # DRAWDOWN & PHOENIX PROTOCOL
            'peak_balance_usdt': self.peak_balance_usdt,
            'current_drawdown_pct': self.current_drawdown_pct,
            'max_drawdown_pct': self.max_drawdown_pct,
            'risk_multiplier': self.get_phoenix_multiplier(),
            'risk_mode': self.get_risk_mode_name(),
            'drawdown_kill_switch': self.drawdown_kill_switch_triggered,
            # PROFIT WARNINGS
            'withdrawal_recommendation': withdrawal_recommendation
        }

    def _is_trading_enabled(self) -> bool:
        """Check if trading should continue based on safety limits"""
        # PHOENIX PROTOCOL: Kill switch at 40% DD (last defense!)
        if self.current_drawdown_pct >= self.DRAWDOWN_KILLSWITCH_PCT * 100:
            if not self.drawdown_kill_switch_triggered:
                print(f"🚨 KILL SWITCH: {self.current_drawdown_pct:.1f}% drawdown from peak!")
                print(f"🚨 Peak: ${self.peak_balance_usdt:.2f}, Now: ${self.current_balance_usdt:.2f}")
                print(f"🚨 Phoenix Protocol failed. Manual intervention required.")
                self.drawdown_kill_switch_triggered = True
            return False

        if self.drawdown_kill_switch_triggered:
            return False

        # Check if new day - reset daily tracking
        if datetime.now().date() != self.today:
            self.today = datetime.now().date()
            self.daily_pnl = 0.0
            self.starting_balance_usdt = self.current_balance_usdt

        # Calculate daily PnL
        self.daily_pnl = self.current_balance_usdt - self.starting_balance_usdt
        daily_pnl_pct = (self.daily_pnl / self.starting_balance_usdt) if self.starting_balance_usdt > 0 else 0

        # Stop trading if daily loss limit exceeded
        if daily_pnl_pct <= -self.DAILY_LOSS_LIMIT_PCT:
            print(f"⛔ Daily loss limit reached: {daily_pnl_pct*100:.2f}%. Trading disabled until tomorrow.")
            return False

        return True

    def calculate_position_size(self, symbol: str, kelly_fraction: float = 0.05) -> float:
        """Calculate safe position size with PHOENIX PROTOCOL and VAULT

        THE IMMORTAL COMPOUNDER:
        1. Uses only tradable balance (excludes vault)
        2. Applies Phoenix multiplier based on drawdown
        3. Respects all safety limits

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            kelly_fraction: Suggested Kelly position size (0-1)

        Returns:
            Position size in USDT (capped by safety limits)
        """
        if not self._is_trading_enabled():
            return 0.0

        self._sync_account_state()

        # 1. Use TRADABLE balance (excluding vault)
        tradable_balance = self.get_tradable_balance()

        # 2. Get Phoenix Protocol multiplier
        phoenix_multiplier = self.get_phoenix_multiplier()

        # 3. Calculate max position with Phoenix scaling
        max_position_usdt = tradable_balance * self.MAX_POSITION_SIZE_PCT * phoenix_multiplier

        # 4. Check total exposure limit (based on tradable balance)
        current_exposure = sum(pos['usdt_value'] for pos in self.positions.values())
        available_exposure = tradable_balance * self.MAX_TOTAL_EXPOSURE_PCT - current_exposure

        if available_exposure <= 0:
            return 0.0

        # 5. Kelly calculation with Phoenix scaling
        kelly_position_usdt = tradable_balance * kelly_fraction * phoenix_multiplier
        safe_position_usdt = min(kelly_position_usdt, max_position_usdt, available_exposure)

        # 6. Ensure minimum order size
        if safe_position_usdt > 0 and safe_position_usdt < self.MIN_ORDER_VALUE_USDT:
            # Only boost to minimum if in Normal/Cautious mode (not Survival)
            if phoenix_multiplier >= 0.75:
                if self.MIN_ORDER_VALUE_USDT <= available_exposure:
                    safe_position_usdt = self.MIN_ORDER_VALUE_USDT
                else:
                    return 0.0
            else:
                # In Survival mode, don't force trades below natural size
                return 0.0

        return safe_position_usdt

    def _find_valid_symbol(self, base_asset: str) -> Optional[str]:
        """Find valid trading pair, trying quote currency first, then fallback

        Args:
            base_asset: Base asset (e.g., 'BTC', 'ETH')

        Returns:
            Valid symbol or None
        """
        pairs_to_try = [
            f"{base_asset}{self.quote_currency}",  # Try preferred quote currency
            f"{base_asset}USDT",  # Fallback to USDT
            f"{base_asset}USDC",  # Fallback to USDC
        ]

        for symbol in pairs_to_try:
            try:
                self.client.get_symbol_ticker(symbol=symbol)
                return symbol
            except:
                continue

        return None

    def place_market_buy(self, symbol: str, position_size_usdt: float,
                        stop_loss_pct: float = 0.25, take_profit_pct: float = 0.35) -> Optional[Dict]:
        """Place market buy order with automatic stop-loss and take-profit

        Args:
            symbol: Trading pair (e.g., 'RENDERUSDT') or base asset (e.g., 'RENDER')
            position_size_usdt: Position size in USDT
            stop_loss_pct: Stop loss percentage (default 25% - MORE BREATHING ROOM)
            take_profit_pct: Take profit percentage (default 35% - COMPOUND TURBO)

        Returns:
            Order details or None if failed
        """
        if position_size_usdt < self.MIN_ORDER_VALUE_USDT:
            print(f"❌ Position size too small: ${position_size_usdt:.2f} (min ${self.MIN_ORDER_VALUE_USDT})")
            return None

        if not self._is_trading_enabled():
            print("❌ Trading disabled (daily loss limit or other safety trigger)")
            return None

        # Find valid symbol if needed
        if not symbol.endswith(('USDT', 'USDC', 'BUSD')):
            symbol = self._find_valid_symbol(symbol)
            if not symbol:
                print(f"❌ Cannot find valid trading pair for {symbol}")
                return None

        try:
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])

            # Calculate quantity
            quantity = position_size_usdt / current_price

            # Get symbol info for precision
            info = self.client.get_symbol_info(symbol)
            step_size = None
            min_qty = None

            for filter in info['filters']:
                if filter['filterType'] == 'LOT_SIZE':
                    step_size = float(filter['stepSize'])
                    min_qty = float(filter['minQty'])

            # Round quantity to valid precision
            if step_size:
                precision = len(str(step_size).split('.')[-1].rstrip('0'))
                quantity = round(quantity, precision)

            if min_qty and quantity < min_qty:
                print(f"❌ Quantity {quantity} below minimum {min_qty} for {symbol}")
                return None

            if self.dry_run:
                print(f"\n🧪 DRY RUN - Would execute:")
                print(f"   BUY {quantity} {symbol} at ~${current_price:.6f}")
                print(f"   Total: ${position_size_usdt:.2f} USDT")
                print(f"   Stop Loss: ${current_price * (1 - stop_loss_pct):.6f} (-{stop_loss_pct*100:.0f}%)")
                print(f"   Take Profit: ${current_price * (1 + take_profit_pct):.6f} (+{take_profit_pct*100:.0f}%)")

                order_result = {
                    'symbol': symbol,
                    'orderId': f"DRY_RUN_{datetime.now().timestamp()}",
                    'status': 'DRY_RUN',
                    'executedQty': quantity,
                    'price': current_price,
                    'type': 'MARKET',
                    'side': 'BUY',
                    'transactTime': int(datetime.now().timestamp() * 1000)
                }
            else:
                # Execute market buy
                order_result = self.client.order_market_buy(
                    symbol=symbol,
                    quantity=quantity
                )

                print(f"✅ BUY executed: {quantity} {symbol} at ~${current_price:.6f}")

                # Calculate stop-loss and take-profit prices
                stop_price = current_price * (1 - stop_loss_pct)
                stop_limit_price = stop_price * 0.99  # Slightly below stop
                take_profit_price = current_price * (1 + take_profit_pct)

                # Get price precision from symbol info
                price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
                tick_size = float(price_filter['tickSize'])
                price_precision = len(str(tick_size).split('.')[-1].rstrip('0'))

                # Get quantity precision
                lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
                step_size = float(lot_filter['stepSize'])
                qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

                # Round prices to valid precision
                stop_price = round(stop_price, price_precision)
                stop_limit_price = round(stop_limit_price, price_precision)
                take_profit_price = round(take_profit_price, price_precision)

                # Format as strings without scientific notation
                import math
                quantity_adjusted = math.floor(quantity / step_size) * step_size
                quantity = round(quantity_adjusted, qty_precision)

                tp_str = f"{take_profit_price:.{price_precision}f}"
                sl_str = f"{stop_price:.{price_precision}f}"
                sl_limit_str = f"{stop_limit_price:.{price_precision}f}"
                qty_str = f"{quantity:.{qty_precision}f}"

                # Place OCO Order (One-Cancels-Other) - Proper protection!
                try:
                    oco_order = self.client.create_oco_order(
                        symbol=symbol,
                        side='SELL',
                        quantity=qty_str,
                        aboveType='LIMIT_MAKER',  # Take-profit
                        abovePrice=tp_str,
                        belowType='STOP_LOSS_LIMIT',  # Stop-loss
                        belowStopPrice=sl_str,
                        belowPrice=sl_limit_str,
                        belowTimeInForce='GTC'
                    )
                    print(f"   ✅ OCO Order set:")
                    print(f"      🎯 TP: ${take_profit_price:.6f} (+{take_profit_pct*100:.1f}%)")
                    print(f"      🛑 SL: ${stop_price:.6f} (-{stop_loss_pct*100:.1f}%)")
                    print(f"      (One-Cancels-Other - Proper protection!)")

                    # Store OCO order list ID for monitoring
                    base_asset = symbol.replace('USDC', '').replace('USDT', '').replace('BUSD', '')
                    self.oco_orders[base_asset] = oco_order['orderListId']

                    # Store order list ID in order result for position monitor
                    order_result['oco_order_list_id'] = oco_order['orderListId']
                    order_result['stop_loss_price'] = stop_price
                    order_result['take_profit_price'] = take_profit_price
                except BinanceAPIException as e:
                    print(f"   ⚠️  OCO Order failed: {e}")
                    print(f"   Trying separate Stop-Loss as fallback...")

                    # CRITICAL FALLBACK: Set at least a Stop-Loss order!
                    try:
                        sl_order = self.client.create_order(
                            symbol=symbol,
                            side='SELL',
                            type='STOP_LOSS_LIMIT',
                            quantity=qty_str,
                            stopPrice=sl_str,
                            price=sl_limit_str,
                            timeInForce='GTC'
                        )
                        print(f"   ✅ Fallback Stop-Loss set: ${stop_price:.6f} (-{stop_loss_pct*100:.1f}%)")
                        print(f"   ⚠️  NO Take-Profit! Position Monitor will handle TP.")

                        order_result['oco_order_list_id'] = None
                        order_result['fallback_sl_order_id'] = sl_order['orderId']
                        order_result['stop_loss_price'] = stop_price
                        order_result['take_profit_price'] = take_profit_price

                        # Send Telegram warning
                        from api.telegram_notifier import notifier
                        notifier.send_message(
                            f"⚠️ *OCO FAILED - FALLBACK SL SET*\n\n"
                            f"Symbol: {symbol}\n"
                            f"Stop-Loss: ${stop_price:.6f}\n"
                            f"Take-Profit: Manual monitoring active\n\n"
                            f"Position Monitor will sell at TP target.",
                            silent=False
                        )
                    except Exception as fallback_error:
                        print(f"   ❌ CRITICAL: Fallback Stop-Loss FAILED: {fallback_error}")
                        print(f"   🚨 POSITION IS UNPROTECTED! Position Monitor will handle manually.")
                        order_result['oco_order_list_id'] = None
                        order_result['fallback_sl_order_id'] = None
                        order_result['stop_loss_price'] = stop_price
                        order_result['take_profit_price'] = take_profit_price

                        # Send critical Telegram alert
                        from api.telegram_notifier import notifier
                        notifier.send_message(
                            f"🚨 *CRITICAL: NO PROTECTION SET*\n\n"
                            f"Symbol: {symbol}\n"
                            f"OCO Failed: {e}\n"
                            f"Fallback SL Failed: {fallback_error}\n\n"
                            f"Position Monitor will actively manage this position!",
                            silent=False
                        )

            # Log trade
            self._log_trade(order_result, 'BUY', stop_loss_pct, take_profit_pct)

            # Update positions
            self._sync_account_state()

            return order_result

        except BinanceAPIException as e:
            print(f"❌ Order failed: {e}")
            return None

    def close_position(self, symbol: str, reason: str = "Manual close") -> Optional[Dict]:
        """Close an open position

        Args:
            symbol: Asset symbol (e.g., 'RENDER')
            reason: Reason for closing

        Returns:
            Order details or None
        """
        # Remove quote currency suffix if present
        asset = symbol.replace('USDT', '').replace('USDC', '').replace('BUSD', '')

        if asset not in self.positions:
            print(f"❌ No position found for {asset}")
            return None

        position = self.positions[asset]
        quantity = position['amount']
        symbol_pair = f"{asset}{self.quote_currency}"

        try:
            if self.dry_run:
                current_price = position['price']
                print(f"\n🧪 DRY RUN - Would close:")
                print(f"   SELL {quantity} {asset} at ~${current_price:.6f}")
                print(f"   Reason: {reason}")

                order_result = {
                    'symbol': symbol_pair,
                    'orderId': f"DRY_RUN_CLOSE_{datetime.now().timestamp()}",
                    'status': 'DRY_RUN',
                    'executedQty': quantity,
                    'price': current_price,
                    'type': 'MARKET',
                    'side': 'SELL',
                    'transactTime': int(datetime.now().timestamp() * 1000)
                }
            else:
                order_result = self.client.order_market_sell(
                    symbol=symbol_pair,
                    quantity=quantity
                )
                print(f"✅ SELL executed: {quantity} {asset}")

            self._log_trade(order_result, 'SELL', 0, 0, reason)
            self._sync_account_state()

            return order_result

        except BinanceAPIException as e:
            print(f"❌ Close failed: {e}")
            return None

    def _log_trade(self, order: Dict, side: str, sl_pct: float, tp_pct: float,
                   reason: str = "", exit_type: str = "", pnl_pct: float = 0,
                   hold_time_hours: float = 0):
        """Log trade to file (enhanced with exit data)"""
        trade_log = {
            'timestamp': datetime.now().isoformat(),
            'symbol': order['symbol'],
            'side': side,
            'quantity': order.get('executedQty', 0),
            'price': order.get('price', 0),
            'order_id': order.get('orderId', ''),
            'status': order.get('status', ''),
            'stop_loss_pct': sl_pct,
            'take_profit_pct': tp_pct,
            'reason': reason,
            'exit_type': exit_type,  # NEW: 'TP', 'SL', 'PARTIAL', 'TIME_EXIT', 'MANUAL', ''
            'pnl_pct': pnl_pct,  # NEW: Profit/loss percentage
            'hold_time_hours': hold_time_hours,  # NEW: How long position was held
            'dry_run': self.dry_run
        }

        try:
            if self.trades_file.exists():
                with open(self.trades_file, 'r') as f:
                    trades = json.load(f)
            else:
                trades = []

            trades.append(trade_log)

            with open(self.trades_file, 'w') as f:
                json.dump(trades, f, indent=2)

        except Exception as e:
            print(f"Warning: Failed to log trade: {e}")

    def load_trade_history(self) -> List[Dict]:
        """Load trade history from file"""
        if not self.trades_file.exists():
            return []

        try:
            with open(self.trades_file, 'r') as f:
                return json.load(f)
        except:
            return []

    def get_trade_statistics(self) -> Dict:
        """Calculate trading statistics from history"""
        trades = self.load_trade_history()

        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0
            }

        # Match buy/sell pairs to calculate wins/losses
        # This is simplified - in production you'd want more sophisticated matching
        buys = [t for t in trades if t['side'] == 'BUY']
        sells = [t for t in trades if t['side'] == 'SELL']

        wins = 0
        losses = 0
        total_win_pct = 0
        total_loss_pct = 0

        for sell in sells:
            symbol = sell['symbol']
            sell_price = float(sell['price'])

            # Find corresponding buy
            matching_buys = [b for b in buys if b['symbol'] == symbol and b['timestamp'] < sell['timestamp']]
            if matching_buys:
                buy = matching_buys[-1]  # Most recent buy
                buy_price = float(buy['price'])

                pnl_pct = ((sell_price - buy_price) / buy_price) * 100

                if pnl_pct > 0:
                    wins += 1
                    total_win_pct += pnl_pct
                else:
                    losses += 1
                    total_loss_pct += abs(pnl_pct)

        total_closed = wins + losses
        win_rate = (wins / total_closed) if total_closed > 0 else 0
        avg_win = (total_win_pct / wins) if wins > 0 else 0
        avg_loss = (total_loss_pct / losses) if losses > 0 else 0
        profit_factor = (total_win_pct / total_loss_pct) if total_loss_pct > 0 else 0

        return {
            'total_trades': len(trades),
            'closed_trades': total_closed,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'profit_factor': profit_factor
        }

    def get_oco_order_status(self, order_list_id: int) -> Optional[Dict]:
        """Query Binance for OCO order status

        Args:
            order_list_id: The OCO order list ID from create_oco_order

        Returns:
            Order status dict or None if error
        """
        if self.dry_run:
            return None  # Can't query OCO in dry-run mode

        try:
            return self.client.get_order_list(orderListId=order_list_id)
        except BinanceAPIException as e:
            print(f"Error querying OCO order {order_list_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error querying OCO: {e}")
            return None

    def cancel_oco_order(self, symbol: str, order_list_id: int) -> bool:
        """Cancel existing OCO order (for trailing stops / partial exits)

        Args:
            symbol: Trading pair (e.g., 'NEIROUSDC')
            order_list_id: The OCO order list ID to cancel

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"[DRY RUN] Would cancel OCO order {order_list_id} for {symbol}")
            return True

        try:
            self.client.cancel_order_list(symbol=symbol, orderListId=order_list_id)
            print(f"✅ Cancelled OCO order {order_list_id} for {symbol}")
            return True
        except BinanceAPIException as e:
            print(f"Failed to cancel OCO order {order_list_id}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error cancelling OCO: {e}")
            return False


def load_binance_client(dry_run: bool = True, quote_currency: str = 'USDC') -> BinanceTradeClient:
    """Load Binance client from environment variables

    Args:
        dry_run: If True, simulate trades without executing
        quote_currency: Quote currency to use (USDT or USDC, default: USDC)

    Returns:
        Initialized BinanceTradeClient
    """
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET_KEY')

    if not api_key or not api_secret:
        raise ValueError("BINANCE_API_KEY and BINANCE_SECRET_KEY must be set in .env")

    return BinanceTradeClient(api_key, api_secret, dry_run=dry_run, quote_currency=quote_currency)
