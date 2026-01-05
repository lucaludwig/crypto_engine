#!/usr/bin/env python3
"""Position Monitor - Active monitoring and management of open positions

Features:
- Detects when OCO orders trigger (TP/SL hits)
- Logs all exits properly to trades_log.json
- Feeds exit data to learning engine
- Implements trailing stop to breakeven after +10% profit
- Implements partial profit taking (50% at 50% of TP target)
- Time-based exit review for stale positions (>48h)
"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from binance.exceptions import BinanceAPIException


class PositionMonitor:
    """
    Actively monitors open positions and manages dynamic adjustments

    This is the missing piece that enables the learning engine to work properly
    by ensuring ALL position exits are logged to trades_log.json
    """

    def __init__(self, binance_client, learning_engine=None, telegram_notifier=None):
        """Initialize position monitor

        Args:
            binance_client: BinanceTradeClient instance
            learning_engine: TradingLearningEngine instance (optional)
            telegram_notifier: TelegramNotifier instance (optional)
        """
        self.client = binance_client
        self.learning_engine = learning_engine
        self.notifier = telegram_notifier
        self.dry_run = binance_client.dry_run

        # Paths
        self.metadata_file = Path(__file__).parent.parent / "position_metadata.json"
        self.trades_file = Path(__file__).parent.parent / "trades_log.json"

        # Load existing metadata
        self.position_metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load position metadata from file"""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_metadata(self):
        """Save position metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.position_metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save position metadata: {e}")

    def store_position(self, symbol: str, entry_price: float, quantity: float,
                      stop_loss: float, take_profit: float, oco_order_list_id: int,
                      coin_data: Dict = None):
        """Store position metadata for monitoring

        Args:
            symbol: Trading pair (e.g., 'NEIROUSDC')
            entry_price: Entry price
            quantity: Position quantity
            stop_loss: Stop loss price
            take_profit: Take profit price
            oco_order_list_id: Binance OCO order list ID
            coin_data: Original coin metrics at entry
        """
        self.position_metadata[symbol] = {
            'entry_time': datetime.now().isoformat(),
            'entry_price': entry_price,
            'quantity': quantity,
            'quantity_remaining': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'oco_order_list_id': oco_order_list_id,
            'trailing_enabled': False,
            'partial_taken': False,
            'dca_count': 0,
            'coin_data': coin_data or {},
            'adjustments': []
        }
        self._save_metadata()

    def scan_positions(self) -> Dict:
        """Scan all open positions and detect exits/adjustments needed

        Returns:
            {
                'triggered_exits': [...],  # Positions that hit SL/TP
                'active_positions': [...],  # Still open
                'needs_adjustment': [...]  # Ready for trailing/partial
            }
        """
        results = {
            'triggered_exits': [],
            'active_positions': [],
            'needs_adjustment': []
        }

        try:
            # Sync current positions from Binance
            self.client._sync_account_state()
            current_positions = self.client.positions

            # Check each metadata entry
            for symbol, metadata in list(self.position_metadata.items()):
                try:
                    # Check if position still exists
                    base_asset = symbol.replace('USDC', '').replace('USDT', '').replace('BUSD', '')

                    if base_asset not in current_positions:
                        # Position closed - check if OCO triggered or manual close
                        exit_info = self._detect_triggered_order(symbol, metadata)
                        if exit_info:
                            results['triggered_exits'].append(exit_info)
                            # Remove from metadata
                            del self.position_metadata[symbol]
                            self._save_metadata()
                        continue

                    # Position still open - check current price and P&L
                    current_price = current_positions[base_asset]['price']
                    entry_price = metadata['entry_price']
                    profit_pct = ((current_price - entry_price) / entry_price) * 100

                    # Check for adjustments needed
                    adjustment = self._check_for_adjustments(
                        symbol, metadata, current_price, profit_pct
                    )

                    if adjustment:
                        results['needs_adjustment'].append(adjustment)

                    results['active_positions'].append({
                        'symbol': symbol,
                        'entry_price': entry_price,
                        'current_price': current_price,
                        'profit_pct': profit_pct,
                        'quantity': metadata['quantity_remaining'],
                        'age_hours': self._get_position_age_hours(metadata['entry_time'])
                    })

                except Exception as e:
                    print(f"Error checking position {symbol}: {e}")
                    continue

        except Exception as e:
            print(f"Error scanning positions: {e}")

        return results

    def _detect_triggered_order(self, symbol: str, metadata: Dict) -> Optional[Dict]:
        """Detect if OCO order triggered (TP or SL hit)

        Simplified approach: Check if any open orders exist for this symbol.
        If position closed and no orders remain, it was likely triggered.

        Args:
            symbol: Trading pair
            metadata: Position metadata

        Returns:
            Exit info dict if triggered, None otherwise
        """
        if self.dry_run:
            # In dry run, can't actually check OCO status
            return None

        try:
            # Check if there are any open orders for this symbol
            open_orders = self.client.client.get_open_orders(symbol=symbol)

            # If no open orders and position is gone, likely OCO triggered
            # But we can't determine exact exit price without order history
            # So we just acknowledge the exit happened
            if len(open_orders) == 0:
                # Get recent trades to find exit price
                try:
                    trades = self.client.client.get_my_trades(symbol=symbol, limit=5)

                    # Find most recent sell trade
                    entry_time = datetime.fromisoformat(metadata['entry_time'])
                    entry_timestamp = int(entry_time.timestamp() * 1000)

                    for trade in reversed(trades):  # Most recent first
                        if trade['isBuyer'] == False and trade['time'] > entry_timestamp:
                            # This is a sell after our entry
                            exit_price = float(trade['price'])
                            quantity = float(trade['qty'])
                            entry_price = metadata['entry_price']
                            pnl_pct = ((exit_price - entry_price) / entry_price) * 100

                            # Determine exit type based on price
                            stop_loss = metadata['stop_loss']
                            take_profit = metadata['take_profit']

                            if abs(exit_price - take_profit) < abs(exit_price - stop_loss):
                                exit_type = 'TP'
                            else:
                                exit_type = 'SL'

                            hold_time_hours = (datetime.now() - entry_time).total_seconds() / 3600

                            return {
                                'symbol': symbol,
                                'exit_type': exit_type,
                                'exit_price': exit_price,
                                'entry_price': entry_price,
                                'quantity': quantity,
                                'pnl_pct': pnl_pct,
                                'hold_time_hours': hold_time_hours,
                                'value': quantity * exit_price,
                                'metadata': metadata
                            }
                except Exception as trade_error:
                    # Can't get trade history, just skip
                    pass

            return None

        except BinanceAPIException as e:
            # Silently handle API errors
            return None
        except Exception as e:
            # Silently handle other errors - not critical
            return None

    def _check_for_adjustments(self, symbol: str, metadata: Dict,
                              current_price: float, profit_pct: float) -> Optional[Dict]:
        """Check if position needs trailing stop or partial exit

        Returns:
            Adjustment dict if needed, None otherwise
        """
        # CRITICAL: Check if manual exit needed (TP/SL reached without OCO)
        manual_exit = self._check_manual_exit_needed(symbol, metadata, current_price, profit_pct)
        if manual_exit:
            return manual_exit

        # Check for trailing stop (profit >= 10%)
        if profit_pct >= 10.0 and not metadata['trailing_enabled']:
            return {
                'action': 'TRAILING_STOP',
                'symbol': symbol,
                'profit_pct': profit_pct,
                'current_price': current_price,
                'entry_price': metadata['entry_price']
            }

        # Check for partial profit taking (profit >= 50% of TP target)
        if not metadata['partial_taken']:
            entry_price = metadata['entry_price']
            take_profit = metadata['take_profit']
            tp_target_pct = ((take_profit - entry_price) / entry_price) * 100
            partial_trigger_pct = tp_target_pct * 0.5  # 50% of TP target

            if profit_pct >= partial_trigger_pct and profit_pct >= 10.0:  # Min 10% profit
                return {
                    'action': 'PARTIAL_EXIT',
                    'symbol': symbol,
                    'profit_pct': profit_pct,
                    'current_price': current_price,
                    'tp_target_pct': tp_target_pct
                }

        # Check for time-based exit review (>48h with low profit/loss)
        age_hours = self._get_position_age_hours(metadata['entry_time'])
        if age_hours > 48 and abs(profit_pct) < 5.0:
            return {
                'action': 'TIME_REVIEW',
                'symbol': symbol,
                'profit_pct': profit_pct,
                'age_hours': age_hours,
                'metadata': metadata
            }

        return None

    def _check_manual_exit_needed(self, symbol: str, metadata: Dict,
                                   current_price: float, profit_pct: float) -> Optional[Dict]:
        """Check if manual exit needed (TP/SL reached without OCO)

        This is CRITICAL for positions without OCO protection!

        Returns:
            Manual exit dict if needed, None otherwise
        """
        entry_price = metadata['entry_price']
        stop_loss = metadata.get('stop_loss')
        take_profit = metadata.get('take_profit')

        # Check if Stop Loss hit (with 0.5% buffer for slippage)
        if stop_loss and current_price <= stop_loss * 1.005:
            return {
                'action': 'MANUAL_EXIT_SL',
                'symbol': symbol,
                'profit_pct': profit_pct,
                'current_price': current_price,
                'entry_price': entry_price,
                'trigger_price': stop_loss,
                'reason': f"Stop-Loss reached: ${stop_loss:.6f}"
            }

        # Check if Take Profit hit (with 0.5% buffer)
        if take_profit and current_price >= take_profit * 0.995:
            return {
                'action': 'MANUAL_EXIT_TP',
                'symbol': symbol,
                'profit_pct': profit_pct,
                'current_price': current_price,
                'entry_price': entry_price,
                'trigger_price': take_profit,
                'reason': f"Take-Profit reached: ${take_profit:.6f}"
            }

        return None

    def _get_position_age_hours(self, entry_time_str: str) -> float:
        """Calculate position age in hours"""
        entry_time = datetime.fromisoformat(entry_time_str)
        return (datetime.now() - entry_time).total_seconds() / 3600

    def execute_manual_exit(self, symbol: str, reason: str, exit_type: str) -> bool:
        """Execute manual exit (market sell) when TP/SL reached without OCO

        Args:
            symbol: Trading pair
            reason: Exit reason
            exit_type: 'TP' or 'SL'

        Returns:
            True if successful, False otherwise
        """
        metadata = self.position_metadata.get(symbol)
        if not metadata:
            print(f"No metadata found for {symbol}")
            return False

        quantity = metadata['quantity_remaining']

        if self.dry_run:
            print(f"[DRY RUN] Would execute manual exit on {symbol}: {reason}")
            # Clean up metadata
            del self.position_metadata[symbol]
            self._save_metadata()
            return True

        try:
            # Get symbol info for precision
            info = self.client.client.get_symbol_info(symbol)
            lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
            step_size = float(lot_filter['stepSize'])
            qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

            qty = round(quantity, qty_precision)
            qty_str = f"{qty:.{qty_precision}f}"

            # Execute MARKET SELL immediately
            sell_order = self.client.client.order_market_sell(
                symbol=symbol,
                quantity=qty_str
            )

            # Get execution price
            exec_price = float(sell_order.get('fills', [{}])[0].get('price', 0)) if sell_order.get('fills') else 0

            # Calculate P&L
            entry_price = metadata['entry_price']
            pnl_pct = ((exec_price - entry_price) / entry_price) * 100
            entry_time = datetime.fromisoformat(metadata['entry_time'])
            hold_time_hours = (datetime.now() - entry_time).total_seconds() / 3600

            print(f"✅ Manual exit executed: {symbol} at ${exec_price:.6f} ({pnl_pct:+.1f}%) - {reason}")

            # Log exit
            self._log_exit(
                symbol=symbol,
                exit_type=exit_type,
                exit_price=exec_price,
                quantity=qty,
                entry_price=entry_price,
                pnl_pct=pnl_pct,
                hold_time_hours=hold_time_hours,
                reason=reason,
                metadata=metadata
            )

            # Send notification
            if self.notifier:
                self.notifier.notify_position_exit(
                    symbol=symbol,
                    exit_type=exit_type,
                    quantity=qty,
                    entry_price=entry_price,
                    exit_price=exec_price,
                    pnl_pct=pnl_pct,
                    hold_time_hours=hold_time_hours,
                    usdt_value=qty * exec_price
                )

            # Cancel any remaining orders (if there's a fallback SL order)
            try:
                open_orders = self.client.client.get_open_orders(symbol=symbol)
                for order in open_orders:
                    self.client.client.cancel_order(symbol=symbol, orderId=order['orderId'])
                    print(f"   Cancelled remaining order: {order['orderId']}")
            except Exception as e:
                print(f"   Warning: Could not cancel remaining orders: {e}")

            # Clean up metadata
            del self.position_metadata[symbol]
            self._save_metadata()

            return True

        except Exception as e:
            print(f"Error executing manual exit for {symbol}: {e}")
            return False

    def apply_trailing_stop(self, symbol: str, current_profit_pct: float) -> bool:
        """Move stop-loss to breakeven after +10% profit

        Args:
            symbol: Trading pair
            current_profit_pct: Current profit percentage

        Returns:
            True if successful, False otherwise
        """
        metadata = self.position_metadata.get(symbol)
        if not metadata:
            print(f"No metadata found for {symbol}")
            return False

        if metadata['trailing_enabled']:
            print(f"Trailing already enabled for {symbol}")
            return False

        if self.dry_run:
            print(f"[DRY RUN] Would apply trailing stop to {symbol} at breakeven (entry: ${metadata['entry_price']:.6f})")
            metadata['trailing_enabled'] = True
            metadata['adjustments'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'TRAILING_STOP',
                'new_sl': metadata['entry_price'],
                'reason': f"Profit +{current_profit_pct:.1f}%, moved SL to breakeven"
            })
            self._save_metadata()
            return True

        try:
            # Cancel existing OCO order
            oco_id = metadata['oco_order_list_id']
            cancelled = self.client.cancel_oco_order(symbol, oco_id)

            if not cancelled:
                print(f"Failed to cancel OCO for {symbol}")
                return False

            # Place new OCO with SL at breakeven
            entry_price = metadata['entry_price']
            take_profit = metadata['take_profit']
            quantity_remaining = metadata['quantity_remaining']

            # Get symbol info for precision
            info = self.client.client.get_symbol_info(symbol)
            price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
            tick_size = float(price_filter['tickSize'])
            price_precision = len(str(tick_size).split('.')[-1].rstrip('0'))

            lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
            step_size = float(lot_filter['stepSize'])
            qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

            # Format prices and quantity
            sl_price = round(entry_price * 0.995, price_precision)  # Slightly below entry (0.5% slippage buffer)
            sl_limit_price = round(sl_price * 0.99, price_precision)
            tp_price = round(take_profit, price_precision)
            qty = round(quantity_remaining, qty_precision)

            tp_str = f"{tp_price:.{price_precision}f}"
            sl_str = f"{sl_price:.{price_precision}f}"
            sl_limit_str = f"{sl_limit_price:.{price_precision}f}"
            qty_str = f"{qty:.{qty_precision}f}"

            # Place new OCO
            new_oco = self.client.client.create_oco_order(
                symbol=symbol,
                side='SELL',
                quantity=qty_str,
                aboveType='LIMIT_MAKER',
                abovePrice=tp_str,
                belowType='STOP_LOSS_LIMIT',
                belowStopPrice=sl_str,
                belowPrice=sl_limit_str,
                belowTimeInForce='GTC'
            )

            # Update metadata
            metadata['oco_order_list_id'] = new_oco['orderListId']
            metadata['stop_loss'] = sl_price
            metadata['trailing_enabled'] = True
            metadata['adjustments'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'TRAILING_STOP',
                'new_sl': sl_price,
                'reason': f"Profit +{current_profit_pct:.1f}%, moved SL to breakeven"
            })
            self._save_metadata()

            print(f"✅ Trailing stop applied to {symbol}: SL moved to ${sl_price:.6f} (breakeven)")

            # Send enhanced notification
            if self.notifier:
                self.notifier.notify_trailing_stop_applied(
                    symbol=symbol,
                    profit_pct=current_profit_pct,
                    new_stop_price=sl_price,
                    entry_price=entry_price
                )

            return True

        except Exception as e:
            print(f"Error applying trailing stop to {symbol}: {e}")
            return False

    def execute_partial_exit(self, symbol: str, current_profit_pct: float) -> bool:
        """Take 50% profit at 50% of TP target

        Args:
            symbol: Trading pair
            current_profit_pct: Current profit percentage

        Returns:
            True if successful, False otherwise
        """
        metadata = self.position_metadata.get(symbol)
        if not metadata:
            print(f"No metadata found for {symbol}")
            return False

        if metadata['partial_taken']:
            print(f"Partial already taken for {symbol}")
            return False

        quantity_remaining = metadata['quantity_remaining']
        partial_qty = quantity_remaining * 0.5  # Sell 50%

        if self.dry_run:
            print(f"[DRY RUN] Would take partial profit on {symbol}: Sell {partial_qty:.4f} at +{current_profit_pct:.1f}%")
            metadata['partial_taken'] = True
            metadata['quantity_remaining'] = quantity_remaining - partial_qty
            metadata['adjustments'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'PARTIAL_EXIT',
                'quantity_sold': partial_qty,
                'profit_pct': current_profit_pct,
                'reason': f"Partial profit at +{current_profit_pct:.1f}%"
            })
            self._save_metadata()
            return True

        try:
            # Get symbol info for precision
            info = self.client.client.get_symbol_info(symbol)
            lot_filter = [f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
            step_size = float(lot_filter['stepSize'])
            qty_precision = len(str(step_size).split('.')[-1].rstrip('0'))

            partial_qty = round(partial_qty, qty_precision)
            qty_str = f"{partial_qty:.{qty_precision}f}"

            # Execute market sell for 50%
            sell_order = self.client.client.order_market_sell(
                symbol=symbol,
                quantity=qty_str
            )

            # Get execution price
            exec_price = float(sell_order.get('fills', [{}])[0].get('price', 0)) if sell_order.get('fills') else 0

            print(f"✅ Partial exit: Sold {partial_qty} {symbol} at ${exec_price:.6f} (+{current_profit_pct:.1f}%)")

            # Log partial exit
            entry_price = metadata['entry_price']
            pnl_pct = ((exec_price - entry_price) / entry_price) * 100
            entry_time = datetime.fromisoformat(metadata['entry_time'])
            hold_time_hours = (datetime.now() - entry_time).total_seconds() / 3600

            self._log_exit(
                symbol=symbol,
                exit_type='PARTIAL',
                exit_price=exec_price,
                quantity=partial_qty,
                entry_price=entry_price,
                pnl_pct=pnl_pct,
                hold_time_hours=hold_time_hours,
                reason=f"Partial profit at +{current_profit_pct:.1f}%",
                metadata=metadata
            )

            # Cancel old OCO and place new one on remaining 50%
            oco_id = metadata['oco_order_list_id']
            self.client.cancel_oco_order(symbol, oco_id)

            # Place new OCO on remaining quantity
            remaining_qty = quantity_remaining - partial_qty
            remaining_qty = round(remaining_qty, qty_precision)
            remaining_qty_str = f"{remaining_qty:.{qty_precision}f}"

            price_filter = [f for f in info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
            tick_size = float(price_filter['tickSize'])
            price_precision = len(str(tick_size).split('.')[-1].rstrip('0'))

            stop_loss = metadata['stop_loss']
            take_profit = metadata['take_profit']

            tp_str = f"{take_profit:.{price_precision}f}"
            sl_str = f"{stop_loss:.{price_precision}f}"
            sl_limit_str = f"{(stop_loss * 0.99):.{price_precision}f}"

            new_oco = self.client.client.create_oco_order(
                symbol=symbol,
                side='SELL',
                quantity=remaining_qty_str,
                aboveType='LIMIT_MAKER',
                abovePrice=tp_str,
                belowType='STOP_LOSS_LIMIT',
                belowStopPrice=sl_str,
                belowPrice=sl_limit_str,
                belowTimeInForce='GTC'
            )

            # Update metadata
            metadata['oco_order_list_id'] = new_oco['orderListId']
            metadata['quantity_remaining'] = remaining_qty
            metadata['partial_taken'] = True
            metadata['adjustments'].append({
                'timestamp': datetime.now().isoformat(),
                'action': 'PARTIAL_EXIT',
                'quantity_sold': partial_qty,
                'exec_price': exec_price,
                'profit_pct': pnl_pct,
                'reason': f"Partial profit at +{current_profit_pct:.1f}%"
            })
            self._save_metadata()

            # Send enhanced notification
            if self.notifier:
                self.notifier.notify_partial_exit(
                    symbol=symbol,
                    profit_pct=pnl_pct,
                    quantity_sold=partial_qty,
                    exit_price=exec_price,
                    remaining_qty=remaining_qty
                )

            return True

        except Exception as e:
            print(f"Error executing partial exit for {symbol}: {e}")
            return False

    def _log_exit(self, symbol: str, exit_type: str, exit_price: float,
                  quantity: float, entry_price: float, pnl_pct: float,
                  hold_time_hours: float, reason: str, metadata: Dict):
        """Log position exit to trades_log.json

        This is CRITICAL - without this, learning engine has no data!
        """
        trade_log = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'side': 'SELL',
            'quantity': quantity,
            'price': exit_price,
            'entry_price': entry_price,
            'order_id': 0,  # We don't have order ID for OCO triggers
            'status': 'FILLED',
            'exit_type': exit_type,
            'pnl_pct': pnl_pct,
            'hold_time_hours': hold_time_hours,
            'stop_loss_pct': 0,
            'take_profit_pct': 0,
            'reason': reason,
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

            print(f"📝 Exit logged: {symbol} {exit_type} +{pnl_pct:.1f}%")

            # Feed to learning engine
            if self.learning_engine:
                coin_data = metadata.get('coin_data', {})
                self.learning_engine.analyze_trade_outcome(
                    symbol=symbol,
                    buy_price=entry_price,
                    sell_price=exit_price,
                    coin_data=coin_data
                )

        except Exception as e:
            print(f"Warning: Failed to log exit for {symbol}: {e}")

    def log_triggered_exit(self, exit_info: Dict):
        """Log a triggered exit (TP/SL hit) to trades_log and learning engine"""
        self._log_exit(
            symbol=exit_info['symbol'],
            exit_type=exit_info['exit_type'],
            exit_price=exit_info['exit_price'],
            quantity=exit_info['quantity'],
            entry_price=exit_info['entry_price'],
            pnl_pct=exit_info['pnl_pct'],
            hold_time_hours=exit_info['hold_time_hours'],
            reason=f"OCO {exit_info['exit_type']} triggered",
            metadata=exit_info['metadata']
        )
