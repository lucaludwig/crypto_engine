"""Trailing Stop Logic - Maximize Winners

GOLDEN NUMBERS (Hard-Coded):
- 15% Profit → Activate trailing stop with 5% distance
- 30% Profit → Tighten trailing stop to 3% distance

❌ NO FIXED TAKE-PROFIT
✅ RIDE WINNERS with trailing stops

Goal: Capture fat-tail gains while protecting profits.
"""
from typing import Dict, Optional


class TrailingLogic:
    """Manages trailing stop logic for profit maximization

    Trailing Stop Activation:
    - Inactive until +15% profit
    - 15-30% profit: Trail by 5%
    - 30%+ profit: Trail by 3%

    The stop NEVER moves down (for longs), only up.
    """

    # AGGRESSIVE GROWTH MODE - Capture mid-range pumps
    TRAILING_ACTIVATION_PCT = 5.0  # Activate at +5% profit (was 15%)
    TRAILING_DISTANCE_WIDE_PCT = 5.0  # 5% trail distance (15-30% profit)
    TRAILING_DISTANCE_TIGHT_PCT = 3.0  # 3% trail distance (30%+ profit)
    TRAILING_TIGHTEN_PCT = 30.0  # Tighten at +30% profit

    def __init__(self):
        """Initialize trailing logic"""
        pass

    def calculate_profit_pct(self, entry_price: float, current_price: float, direction: str = "LONG") -> float:
        """Calculate current profit percentage

        Args:
            entry_price: Entry price
            current_price: Current price
            direction: Trade direction

        Returns:
            Profit percentage
        """
        if direction == "LONG":
            profit_pct = ((current_price - entry_price) / entry_price) * 100
        else:  # SHORT
            profit_pct = ((entry_price - current_price) / entry_price) * 100

        return profit_pct

    def is_trailing_active(self, profit_pct: float) -> bool:
        """Check if trailing stop should be active

        Args:
            profit_pct: Current profit percentage

        Returns:
            True if trailing should be active
        """
        return profit_pct >= self.TRAILING_ACTIVATION_PCT

    def get_trailing_distance(self, profit_pct: float) -> float:
        """Get current trailing distance based on profit level

        Args:
            profit_pct: Current profit percentage

        Returns:
            Trailing distance in percent
        """
        if profit_pct >= self.TRAILING_TIGHTEN_PCT:
            return self.TRAILING_DISTANCE_TIGHT_PCT
        elif profit_pct >= self.TRAILING_ACTIVATION_PCT:
            return self.TRAILING_DISTANCE_WIDE_PCT
        else:
            return 0.0  # Not active yet

    def calculate_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        peak_price: float,
        direction: str = "LONG"
    ) -> Dict:
        """Calculate trailing stop level

        Args:
            entry_price: Entry price
            current_price: Current market price
            peak_price: Peak price since entry (high water mark)
            direction: Trade direction

        Returns:
            Dict with 'trailing_active', 'stop_price', 'distance_pct', 'profit_pct'
        """
        profit_pct = self.calculate_profit_pct(entry_price, current_price, direction)
        is_active = self.is_trailing_active(profit_pct)

        result = {
            'trailing_active': is_active,
            'stop_price': None,
            'distance_pct': 0.0,
            'profit_pct': profit_pct,
            'peak_price': peak_price,
            'mode': 'INACTIVE'
        }

        if not is_active:
            return result

        # Get trailing distance
        distance_pct = self.get_trailing_distance(profit_pct)
        result['distance_pct'] = distance_pct

        # Calculate stop based on peak price
        if direction == "LONG":
            stop_price = peak_price * (1 - distance_pct / 100)
            result['mode'] = 'TIGHT' if distance_pct == self.TRAILING_DISTANCE_TIGHT_PCT else 'WIDE'
        else:  # SHORT
            stop_price = peak_price * (1 + distance_pct / 100)
            result['mode'] = 'TIGHT' if distance_pct == self.TRAILING_DISTANCE_TIGHT_PCT else 'WIDE'

        result['stop_price'] = stop_price

        return result

    def update_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        current_peak: float,
        current_stop: float,
        direction: str = "LONG"
    ) -> Dict:
        """Update trailing stop (only moves in favorable direction)

        Args:
            entry_price: Entry price
            current_price: Current price
            current_peak: Current peak price
            current_stop: Current stop loss
            direction: Trade direction

        Returns:
            Dict with 'updated', 'new_stop', 'reason'
        """
        # Update peak if necessary
        new_peak = current_peak
        if direction == "LONG":
            new_peak = max(current_peak, current_price)
        else:  # SHORT
            new_peak = min(current_peak, current_price)

        # Calculate what trailing stop should be
        trailing = self.calculate_trailing_stop(entry_price, current_price, new_peak, direction)

        result = {
            'updated': False,
            'new_stop': current_stop,
            'new_peak': new_peak,
            'trailing_mode': trailing['mode'],
            'reason': ''
        }

        if not trailing['trailing_active']:
            result['reason'] = f"Trailing not active yet (need {self.TRAILING_ACTIVATION_PCT}% profit)"
            return result

        new_stop = trailing['stop_price']

        # Only move stop in favorable direction
        if direction == "LONG":
            if new_stop > current_stop:
                result['updated'] = True
                result['new_stop'] = new_stop
                result['reason'] = f"Trailing up to {trailing['distance_pct']}% below peak ({trailing['mode']} mode)"
        else:  # SHORT
            if new_stop < current_stop:
                result['updated'] = True
                result['new_stop'] = new_stop
                result['reason'] = f"Trailing down to {trailing['distance_pct']}% above peak ({trailing['mode']} mode)"

        if not result['updated']:
            result['reason'] = f"No update: trailing stop ({new_stop:.6f}) not better than current ({current_stop:.6f})"

        return result

    def check_stop_hit(self, current_price: float, stop_price: float, direction: str = "LONG") -> bool:
        """Check if stop was hit

        Args:
            current_price: Current price
            stop_price: Stop loss price
            direction: Trade direction

        Returns:
            True if stop was hit
        """
        if direction == "LONG":
            return current_price <= stop_price
        else:  # SHORT
            return current_price >= stop_price

    def get_exit_summary(
        self,
        entry_price: float,
        exit_price: float,
        peak_price: float,
        direction: str = "LONG"
    ) -> Dict:
        """Get summary of exit performance

        Args:
            entry_price: Entry price
            exit_price: Exit price
            peak_price: Peak price reached
            direction: Trade direction

        Returns:
            Dict with performance metrics
        """
        profit_pct = self.calculate_profit_pct(entry_price, exit_price, direction)
        peak_profit_pct = self.calculate_profit_pct(entry_price, peak_price, direction)

        # Calculate how much profit we gave back from peak
        if direction == "LONG":
            giveback = ((peak_price - exit_price) / entry_price) * 100
        else:  # SHORT
            giveback = ((exit_price - peak_price) / entry_price) * 100

        capture_ratio = (profit_pct / peak_profit_pct * 100) if peak_profit_pct != 0 else 0

        return {
            'final_profit_pct': profit_pct,
            'peak_profit_pct': peak_profit_pct,
            'giveback_pct': giveback,
            'capture_ratio': capture_ratio,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'peak_price': peak_price
        }
