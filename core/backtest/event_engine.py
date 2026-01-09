"""Event-Driven Backtesting Engine

Event-driven architecture ensures the backtest uses the SAME logic as live trading.

Events:
- MarketDataEvent: New candle data available
- SignalEvent: Strategy generated a signal
- OrderEvent: Order to be executed
- FillEvent: Order was filled

This prevents look-ahead bias and ensures realistic simulation.
"""
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from enum import Enum

from core.strategy.compression_detector import CompressionDetector
from core.strategy.breakout_trigger import BreakoutTrigger, Direction
from core.risk.position_sizer import PositionSizer
from core.execution.stop_manager import StopManager
from core.execution.trailing_logic import TrailingLogic
from core.backtest.fee_slippage import FeeSlippageModel


class EventType(Enum):
    """Event types"""
    MARKET_DATA = "MARKET_DATA"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"


class Position:
    """Represents an open position"""

    def __init__(
        self,
        symbol: str,
        entry_price: float,
        quantity: float,
        stop_loss: float,
        entry_time: datetime
    ):
        self.symbol = symbol
        self.entry_price = entry_price
        self.quantity = quantity
        self.stop_loss = stop_loss
        self.initial_stop = stop_loss
        self.entry_time = entry_time
        self.peak_price = entry_price
        self.direction = "LONG"  # Simplified: only longs for now


class BacktestEngine:
    """Event-driven backtesting engine

    Uses the SAME strategy modules as live trading:
    - CompressionDetector
    - BreakoutTrigger
    - PositionSizer
    - StopManager
    - TrailingLogic
    """

    def __init__(
        self,
        initial_capital: float,
        max_positions: int = 4,
        data_lookback: int = 500
    ):
        """Initialize backtest engine

        Args:
            initial_capital: Starting capital
            max_positions: Max simultaneous positions
            data_lookback: Candles to keep in memory for indicators
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.max_positions = max_positions
        self.data_lookback = data_lookback

        # Initialize strategy components (SAME as live bot!)
        self.compression_detector = CompressionDetector()
        self.breakout_trigger = BreakoutTrigger()
        self.position_sizer = PositionSizer()
        self.stop_manager = StopManager()
        self.trailing_logic = TrailingLogic()
        self.fee_model = FeeSlippageModel()

        # State
        self.positions: Dict[str, Position] = {}
        self.equity_curve = [initial_capital]
        self.trades: List[Dict] = []
        self.current_time = None

        # Data buffers (symbol -> {opens, highs, lows, closes, volumes, timestamps})
        self.data_buffers: Dict[str, Dict] = {}

    def add_market_data(self, symbol: str, bar: Dict):
        """Add new market data bar

        Args:
            symbol: Trading symbol
            bar: OHLCV bar dict
        """
        if symbol not in self.data_buffers:
            self.data_buffers[symbol] = {
                'opens': [],
                'highs': [],
                'lows': [],
                'closes': [],
                'volumes': [],
                'timestamps': []
            }

        # Append to buffer
        buffer = self.data_buffers[symbol]
        buffer['opens'].append(bar['open'])
        buffer['highs'].append(bar['high'])
        buffer['lows'].append(bar['low'])
        buffer['closes'].append(bar['close'])
        buffer['volumes'].append(bar['volume'])
        buffer['timestamps'].append(bar['timestamp'])

        # Trim to lookback
        if len(buffer['opens']) > self.data_lookback:
            for key in buffer:
                buffer[key] = buffer[key][-self.data_lookback:]

        self.current_time = bar['timestamp']

    def check_for_signals(self, symbol: str) -> Optional[Dict]:
        """Check if compression + breakout conditions met

        Args:
            symbol: Trading symbol

        Returns:
            Signal dict or None
        """
        if symbol not in self.data_buffers:
            return None

        buffer = self.data_buffers[symbol]

        # Need enough data
        if len(buffer['closes']) < 300:
            return None

        # Convert to numpy
        opens = np.array(buffer['opens'])
        highs = np.array(buffer['highs'])
        lows = np.array(buffer['lows'])
        closes = np.array(buffer['closes'])
        volumes = np.array(buffer['volumes'])

        # 1. Check compression
        is_compressed, comp_details = self.compression_detector.is_compressed(
            highs, lows, closes
        )

        if not is_compressed:
            return None

        # 2. Check breakout
        direction, break_details = self.breakout_trigger.detect_breakout(
            opens, highs, lows, closes, volumes
        )

        if direction == Direction.NONE:
            return None

        # Signal found!
        signal_strength = self.breakout_trigger.calculate_signal_strength(break_details)

        return {
            'symbol': symbol,
            'direction': direction,
            'signal_strength': signal_strength,
            'current_price': closes[-1],
            'breakout_level': break_details['break_price'],
            'compression_score': self.compression_detector.get_compression_score(highs, lows, closes),
            'details': break_details
        }

    def execute_signal(self, signal: Dict):
        """Execute a signal (open position)

        Args:
            signal: Signal dict
        """
        symbol = signal['symbol']

        # Check if already in position
        if symbol in self.positions:
            return

        # Check if we're at max positions
        if len(self.positions) >= self.max_positions:
            return

        # Get data for stop calculation
        buffer = self.data_buffers[symbol]
        highs = np.array(buffer['highs'])
        lows = np.array(buffer['lows'])
        closes = np.array(buffer['closes'])

        entry_price = signal['current_price']

        # Calculate stop loss
        atr = self.compression_detector.calculate_atr(highs, lows, closes)
        stop_data = self.stop_manager.calculate_initial_stop_loss(
            entry_price,
            atr,
            signal['breakout_level'],
            signal['direction'].value
        )

        # Calculate position size
        current_exposure = self._calculate_current_exposure()
        size_data = self.position_sizer.calculate_position_size(
            self.capital,
            entry_price,
            stop_data['stop_price'],
            current_exposure
        )

        if not size_data['valid']:
            return

        # Apply fees & slippage
        entry_cost = self.fee_model.calculate_entry_cost(
            entry_price,
            size_data['position_size_coins']
        )

        # Deduct FULL position cost from capital (not just fees!)
        # position_value includes the actual price paid (entry_price + slippage + fees)
        self.capital -= entry_cost['position_value']

        # Open position
        position = Position(
            symbol=symbol,
            entry_price=entry_cost['actual_price'],
            quantity=size_data['position_size_coins'],
            stop_loss=stop_data['stop_price'],
            entry_time=self.current_time
        )

        self.positions[symbol] = position

    def manage_positions(self):
        """Manage open positions (check stops, update trailing)"""
        for symbol, position in list(self.positions.items()):
            if symbol not in self.data_buffers:
                continue

            buffer = self.data_buffers[symbol]
            current_price = buffer['closes'][-1]

            # Update peak
            position.peak_price = max(position.peak_price, current_price)

            # Check stop hit
            if self.trailing_logic.check_stop_hit(current_price, position.stop_loss):
                self._close_position(symbol, current_price, "Stop Loss")
                continue

            # Check time exit (8 hours)
            hours_held = (self.current_time - position.entry_time).total_seconds() / 3600
            profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100

            if hours_held >= 8 and profit_pct < 2.0:
                self._close_position(symbol, current_price, "Time Exit")
                continue

            # Update trailing stop
            trailing_update = self.trailing_logic.update_trailing_stop(
                position.entry_price,
                current_price,
                position.peak_price,
                position.stop_loss
            )

            if trailing_update['updated']:
                position.stop_loss = trailing_update['new_stop']
            else:
                # Check breakeven move
                be_check = self.stop_manager.should_move_to_breakeven(
                    position.entry_price,
                    current_price,
                    position.initial_stop
                )

                if be_check['should_move'] and be_check['new_stop'] > position.stop_loss:
                    position.stop_loss = be_check['new_stop']

    def _close_position(self, symbol: str, exit_price: float, reason: str):
        """Close a position

        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Exit reason
        """
        if symbol not in self.positions:
            return

        position = self.positions[symbol]

        # Calculate exit cost
        exit_cost = self.fee_model.calculate_exit_cost(
            exit_price,
            position.quantity
        )

        # Calculate P&L
        round_trip = self.fee_model.calculate_round_trip_cost(
            position.entry_price,
            exit_price,
            position.quantity
        )

        # Add proceeds to capital
        # position_value already includes slippage (actual_price * quantity)
        # Only deduct fees, not total_cost (which double-counts slippage)
        proceeds = exit_cost['position_value'] - exit_cost['fee_amount']
        self.capital += proceeds

        # Record trade
        trade = {
            'symbol': symbol,
            'entry_time': position.entry_time,
            'exit_time': self.current_time,
            'entry_price': position.entry_price,
            'exit_price': exit_cost['actual_price'],
            'quantity': position.quantity,
            'pnl': round_trip['net_pnl'],
            'pnl_pct': round_trip['net_pnl_pct'],
            'gross_pnl': round_trip['gross_pnl'],
            'costs': round_trip['total_costs'],
            'reason': reason,
            'duration_hours': (self.current_time - position.entry_time).total_seconds() / 3600
        }

        self.trades.append(trade)

        # Remove position
        del self.positions[symbol]

    def _calculate_current_exposure(self) -> float:
        """Calculate current exposure percentage

        Returns:
            Exposure as percentage of capital
        """
        if not self.positions:
            return 0.0

        total_exposure = 0.0
        for position in self.positions.values():
            exposure = position.entry_price * position.quantity
            total_exposure += exposure

        return (total_exposure / self.capital) * 100

    def update_equity(self):
        """Update equity curve"""
        # Calculate unrealized P&L
        unrealized_pnl = 0.0
        for symbol, position in self.positions.items():
            if symbol in self.data_buffers:
                current_price = self.data_buffers[symbol]['closes'][-1]
                pnl = (current_price - position.entry_price) * position.quantity
                unrealized_pnl += pnl

        equity = self.capital + unrealized_pnl
        self.equity_curve.append(equity)

    def get_results(self) -> Dict:
        """Get backtest results

        Returns:
            Results dict with trades, equity curve, metrics
        """
        return {
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'total_pnl': self.capital - self.initial_capital,
            'total_return_pct': ((self.capital - self.initial_capital) / self.initial_capital) * 100,
            'total_trades': len(self.trades)
        }
