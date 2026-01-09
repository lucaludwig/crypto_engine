"""Stop Loss Manager

GOLDEN NUMBERS (Hard-Coded):
- Initial Stop Loss: 1.5× ATR(14) OR below breakout candle low (whichever is closer)
- Breakeven Trigger: Profit = 1.5× Risk
- Time Exit: 8 hours with <2% profit → Market Exit

No guessing, no hoping. Hard stops ONLY.
"""
import numpy as np
from typing import Dict, Optional
from datetime import datetime, timedelta


class StopManager:
    """Manages stop loss levels and breakeven moves

    Stop Loss Progression:
    1. Entry: 1.5× ATR or below breakout low
    2. At +1.5R profit: Move to breakeven (entry + fees)
    3. Trailing stop takes over (see trailing_logic.py)
    """

    # GOLDEN NUMBERS - DO NOT MODIFY
    INITIAL_STOP_ATR_MULTIPLIER = 1.5  # 1.5× ATR
    BREAKEVEN_TRIGGER_R = 1.5  # Move to BE at 1.5R profit
    FEE_ESTIMATE_PCT = 0.15  # 0.15% total fees (maker + taker)
    TIME_EXIT_HOURS = 8  # Exit if <2% profit after 8 hours
    TIME_EXIT_MIN_PROFIT_PCT = 2.0  # 2% minimum

    def __init__(self):
        """Initialize stop manager"""
        pass

    def calculate_initial_stop_loss(
        self,
        entry_price: float,
        atr: float,
        breakout_low: float,
        direction: str = "LONG"
    ) -> Dict:
        """Calculate initial stop loss level

        Uses CLOSER of:
        1. Entry - (1.5× ATR)
        2. Breakout candle low

        Args:
            entry_price: Entry price
            atr: ATR(14) value
            breakout_low: Low of breakout candle
            direction: "LONG" or "SHORT"

        Returns:
            Dict with 'stop_price', 'stop_distance_pct', 'method'
        """
        if direction == "LONG":
            # Calculate both options
            atr_stop = entry_price - (self.INITIAL_STOP_ATR_MULTIPLIER * atr)
            candle_stop = breakout_low

            # Use whichever is CLOSER (higher price for longs)
            stop_price = max(atr_stop, candle_stop)
            method = "ATR" if stop_price == atr_stop else "Breakout Low"

        else:  # SHORT
            # For shorts (inverse logic)
            atr_stop = entry_price + (self.INITIAL_STOP_ATR_MULTIPLIER * atr)
            candle_stop = breakout_low  # Would be breakout HIGH for shorts

            # Use whichever is CLOSER (lower price for shorts)
            stop_price = min(atr_stop, candle_stop)
            method = "ATR" if stop_price == atr_stop else "Breakout High"

        stop_distance = abs(entry_price - stop_price)
        stop_distance_pct = (stop_distance / entry_price) * 100

        return {
            'stop_price': stop_price,
            'stop_distance': stop_distance,
            'stop_distance_pct': stop_distance_pct,
            'method': method,
            'atr_stop': atr_stop if direction == "LONG" else atr_stop,
            'candle_stop': candle_stop
        }

    def calculate_breakeven_level(self, entry_price: float, direction: str = "LONG") -> float:
        """Calculate breakeven price (entry + fees)

        Args:
            entry_price: Original entry price
            direction: Trade direction

        Returns:
            Breakeven price
        """
        fee_offset = entry_price * (self.FEE_ESTIMATE_PCT / 100)

        if direction == "LONG":
            breakeven = entry_price + fee_offset
        else:  # SHORT
            breakeven = entry_price - fee_offset

        return breakeven

    def should_move_to_breakeven(
        self,
        entry_price: float,
        current_price: float,
        initial_stop_price: float,
        direction: str = "LONG"
    ) -> Dict:
        """Check if stop should be moved to breakeven

        Trigger: Profit = 1.5× Risk

        Args:
            entry_price: Entry price
            current_price: Current market price
            initial_stop_price: Initial stop loss price
            direction: Trade direction

        Returns:
            Dict with 'should_move', 'new_stop', 'profit_r'
        """
        # Calculate current profit
        if direction == "LONG":
            profit = current_price - entry_price
        else:  # SHORT
            profit = entry_price - current_price

        # Calculate risk (distance to stop)
        risk = abs(entry_price - initial_stop_price)

        if risk == 0:
            return {'should_move': False, 'new_stop': initial_stop_price, 'profit_r': 0.0}

        # Calculate R multiple
        profit_r = profit / risk

        # Check trigger
        should_move = profit_r >= self.BREAKEVEN_TRIGGER_R

        new_stop = initial_stop_price
        if should_move:
            new_stop = self.calculate_breakeven_level(entry_price, direction)

        return {
            'should_move': should_move,
            'new_stop': new_stop,
            'profit_r': profit_r,
            'trigger_r': self.BREAKEVEN_TRIGGER_R
        }

    def check_time_exit(
        self,
        entry_time: datetime,
        current_time: datetime,
        entry_price: float,
        current_price: float,
        direction: str = "LONG"
    ) -> Dict:
        """Check if position should be exited due to time

        Time Exit Rule: If >8 hours and profit <2% → Exit

        Args:
            entry_time: Position entry time
            current_time: Current time
            entry_price: Entry price
            current_price: Current price
            direction: Trade direction

        Returns:
            Dict with 'should_exit', 'reason', 'hours_held', 'profit_pct'
        """
        hours_held = (current_time - entry_time).total_seconds() / 3600

        # Calculate profit %
        if direction == "LONG":
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100

        should_exit = (
            hours_held >= self.TIME_EXIT_HOURS and
            profit_pct < self.TIME_EXIT_MIN_PROFIT_PCT
        )

        reason = ""
        if should_exit:
            reason = f"Time exit: {hours_held:.1f}h held with only {profit_pct:.2f}% profit"

        return {
            'should_exit': should_exit,
            'reason': reason,
            'hours_held': hours_held,
            'profit_pct': profit_pct,
            'trigger_hours': self.TIME_EXIT_HOURS,
            'min_profit_pct': self.TIME_EXIT_MIN_PROFIT_PCT
        }

    def get_stop_update(
        self,
        entry_price: float,
        entry_time: datetime,
        current_price: float,
        current_time: datetime,
        current_stop: float,
        initial_stop: float,
        direction: str = "LONG"
    ) -> Dict:
        """Get complete stop loss update recommendation

        Args:
            entry_price: Entry price
            entry_time: Entry time
            current_price: Current price
            current_time: Current time
            current_stop: Current stop loss
            initial_stop: Initial stop loss
            direction: Trade direction

        Returns:
            Dict with action recommendations
        """
        result = {
            'action': 'HOLD',  # HOLD | MOVE_TO_BREAKEVEN | TIME_EXIT
            'new_stop': current_stop,
            'reason': ''
        }

        # 1. Check time exit first (highest priority)
        time_check = self.check_time_exit(entry_time, current_time, entry_price, current_price, direction)
        if time_check['should_exit']:
            result['action'] = 'TIME_EXIT'
            result['reason'] = time_check['reason']
            return result

        # 2. Check breakeven move (only if not already at BE)
        be_price = self.calculate_breakeven_level(entry_price, direction)
        if current_stop < be_price if direction == "LONG" else current_stop > be_price:
            be_check = self.should_move_to_breakeven(entry_price, current_price, initial_stop, direction)
            if be_check['should_move']:
                result['action'] = 'MOVE_TO_BREAKEVEN'
                result['new_stop'] = be_check['new_stop']
                result['reason'] = f"Profit = {be_check['profit_r']:.2f}R (trigger: {self.BREAKEVEN_TRIGGER_R}R)"
                return result

        # 3. No action needed
        result['reason'] = 'No stop update needed'
        return result
