"""Binance Order Executor

Executes trades on Binance Spot market.

Safety features:
- Validates slippage before execution
- Dry-run mode for testing
- Order confirmation
- Position tracking
- Retry logic with exponential backoff
"""
from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Dict, Optional, List
from datetime import datetime
import json
import os
import time


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors that should stop trading"""
    pass


def retry_on_failure(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying API calls with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except BinanceAPIException as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        print(f"  ⚠️ API error (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        print(f"  ❌ API failed after {max_retries + 1} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


class BinanceExecutor:
    """Executes and manages orders on Binance

    Supports:
    - Market orders (primary)
    - Stop-loss orders
    - Position tracking
    - Dry-run mode
    """

    def __init__(self, api_key: str, api_secret: str, dry_run: bool = True):
        """Initialize executor

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            dry_run: If True, simulates orders without executing
        """
        self.client = Client(api_key, api_secret)
        self.dry_run = dry_run
        self.positions_file = "positions.json"
        self.positions = self._load_positions()

    def _load_positions(self) -> Dict:
        """Load active positions from file"""
        if os.path.exists(self.positions_file):
            try:
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load positions file: {e}")
        return {}

    def _save_positions(self):
        """Save positions to file"""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.positions, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save positions: {e}")

    @retry_on_failure(max_retries=3, base_delay=1.0)
    def get_account_balance(self) -> float:
        """Get USDT or USDC balance (whichever is higher)

        Returns:
            Available USDT/USDC balance

        Raises:
            BinanceAPIError: If balance cannot be fetched after retries
        """
        if self.dry_run:
            return 1000.0  # Simulated balance

        account = self.client.get_account()
        usdt_balance = 0.0
        usdc_balance = 0.0

        for balance in account['balances']:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
            elif balance['asset'] == 'USDC':
                usdc_balance = float(balance['free'])

        # Return whichever is higher (user may use USDT or USDC)
        result = max(usdt_balance, usdc_balance)

        if result == 0.0:
            print("  ⚠️ Warning: Account balance is $0.00")

        return result

    def execute_market_buy(
        self,
        symbol: str,
        quantity: float,
        expected_price: float,
        max_slippage_pct: float = 0.3
    ) -> Optional[Dict]:
        """Execute market buy order

        Args:
            symbol: Trading symbol
            quantity: Quantity to buy (in coins)
            expected_price: Expected fill price
            max_slippage_pct: Maximum allowed slippage

        Returns:
            Order result dict or None if failed
        """
        try:
            if self.dry_run:
                # Simulate order
                avg_price = expected_price * 1.001  # Simulate small slippage
                total_cost = avg_price * quantity

                return {
                    'symbol': symbol,
                    'orderId': f"DRY_RUN_{datetime.now().timestamp()}",
                    'status': 'FILLED',
                    'executedQty': quantity,
                    'cummulativeQuoteQty': total_cost,
                    'avgPrice': avg_price,
                    'dry_run': True
                }

            # Get current price to check slippage
            current_price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
            slippage_pct = abs((current_price - expected_price) / expected_price) * 100

            if slippage_pct > max_slippage_pct:
                print(f"❌ Slippage too high: {slippage_pct:.2f}% > {max_slippage_pct}%")
                return None

            # Execute market order
            order = self.client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )

            return {
                'symbol': order['symbol'],
                'orderId': order['orderId'],
                'status': order['status'],
                'executedQty': float(order['executedQty']),
                'cummulativeQuoteQty': float(order['cummulativeQuoteQty']),
                'avgPrice': float(order['cummulativeQuoteQty']) / float(order['executedQty']) if float(order['executedQty']) > 0 else 0,
                'dry_run': False
            }

        except BinanceAPIException as e:
            print(f"Error executing buy order for {symbol}: {e}")
            return None

    def execute_market_sell(
        self,
        symbol: str,
        quantity: float
    ) -> Optional[Dict]:
        """Execute market sell order

        Args:
            symbol: Trading symbol
            quantity: Quantity to sell

        Returns:
            Order result dict or None if failed
        """
        try:
            if self.dry_run:
                # Simulate order
                price = 1.0  # Placeholder
                total_value = price * quantity

                return {
                    'symbol': symbol,
                    'orderId': f"DRY_RUN_{datetime.now().timestamp()}",
                    'status': 'FILLED',
                    'executedQty': quantity,
                    'cummulativeQuoteQty': total_value,
                    'dry_run': True
                }

            # Execute market order
            order = self.client.order_market_sell(
                symbol=symbol,
                quantity=quantity
            )

            return {
                'symbol': order['symbol'],
                'orderId': order['orderId'],
                'status': order['status'],
                'executedQty': float(order['executedQty']),
                'cummulativeQuoteQty': float(order['cummulativeQuoteQty']),
                'avgPrice': float(order['cummulativeQuoteQty']) / float(order['executedQty']) if float(order['executedQty']) > 0 else 0,
                'dry_run': False
            }

        except BinanceAPIException as e:
            print(f"Error executing sell order for {symbol}: {e}")
            return None

    def place_stop_loss(
        self,
        symbol: str,
        quantity: float,
        stop_price: float
    ) -> Optional[str]:
        """Place stop-loss order

        Args:
            symbol: Trading symbol
            quantity: Quantity to sell
            stop_price: Stop price

        Returns:
            Order ID or None
        """
        try:
            if self.dry_run:
                return f"DRY_RUN_STOP_{datetime.now().timestamp()}"

            order = self.client.create_order(
                symbol=symbol,
                side='SELL',
                type='STOP_LOSS_LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                stopPrice=stop_price,
                price=stop_price * 0.99  # Limit price slightly below stop
            )

            return order['orderId']

        except BinanceAPIException as e:
            print(f"Error placing stop-loss for {symbol}: {e}")
            return None

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order

        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel

        Returns:
            True if successful
        """
        try:
            if self.dry_run:
                return True

            self.client.cancel_order(symbol=symbol, orderId=order_id)
            return True

        except BinanceAPIException as e:
            print(f"Error canceling order {order_id}: {e}")
            return False

    def add_position(
        self,
        symbol: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        entry_time: datetime = None
    ):
        """Add position to tracking

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            quantity: Position size in coins
            stop_loss: Initial stop loss price
            entry_time: Entry timestamp
        """
        if entry_time is None:
            entry_time = datetime.now()

        self.positions[symbol] = {
            'symbol': symbol,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'peak_price': entry_price,
            'entry_time': entry_time.isoformat(),
            'stop_order_id': None
        }

        self._save_positions()

    def update_position_stop(self, symbol: str, new_stop: float, stop_order_id: str = None):
        """Update stop loss for position

        Args:
            symbol: Trading symbol
            new_stop: New stop price
            stop_order_id: Stop order ID (if applicable)
        """
        if symbol in self.positions:
            self.positions[symbol]['stop_loss'] = new_stop
            if stop_order_id:
                self.positions[symbol]['stop_order_id'] = stop_order_id
            self._save_positions()

    def update_position_peak(self, symbol: str, peak_price: float):
        """Update peak price for trailing stop

        Args:
            symbol: Trading symbol
            peak_price: New peak price
        """
        if symbol in self.positions:
            self.positions[symbol]['peak_price'] = peak_price
            self._save_positions()

    def remove_position(self, symbol: str):
        """Remove position from tracking

        Args:
            symbol: Trading symbol
        """
        if symbol in self.positions:
            del self.positions[symbol]
            self._save_positions()

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position data

        Args:
            symbol: Trading symbol

        Returns:
            Position dict or None
        """
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict:
        """Get all active positions

        Returns:
            Dict of all positions
        """
        return self.positions.copy()

    def get_total_exposure_pct(self, account_balance: float) -> float:
        """Calculate total exposure percentage

        Args:
            account_balance: Total account balance

        Returns:
            Exposure percentage
        """
        if account_balance == 0:
            return 0.0

        total_exposure = 0.0
        for symbol, position in self.positions.items():
            # Use current value (approximate with entry price)
            position_value = position['entry_price'] * position['quantity']
            total_exposure += position_value

        return (total_exposure / account_balance) * 100
