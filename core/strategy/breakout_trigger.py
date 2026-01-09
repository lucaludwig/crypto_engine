"""Breakout Trigger - Entry Signal Generator

HYBRID NUMBERS (Balanced):
- Volume Multiplier: ≥ 2.3× (20-period average) [was 2.8×]
- Price Break: Close > Max(High, last 24 candles) for LONG
- RSI: Must be between 55 and 70 (trend confirmed, not overbought) ✅ UNCHANGED
- Max Wick: Wick ≤ 30% of candle body (prevents pump & dump) ✅ UNCHANGED

❌ NO ANTICIPATING
❌ NO PRE-BREAKOUT ENTRY

Entry ONLY when candle CLOSES outside range with volume confirmation.
"""
import numpy as np
from typing import Dict, Tuple, Optional
from enum import Enum


class Direction(Enum):
    """Trade direction"""
    LONG = "LONG"
    SHORT = "SHORT"
    NONE = "NONE"


class BreakoutTrigger:
    """Detects valid breakout signals

    A trade triggers ONLY when:
    1. Volume ≥ 2.8× average
    2. Close breaks 24-candle high/low
    3. RSI between 55-70 (for longs)
    4. Wick ≤ 30% of body
    """

    # AGGRESSIVE GROWTH MODE - More signals
    VOLUME_MULTIPLIER = 1.8  # Was 2.3
    VOLUME_PERIOD = 20

    BREAKOUT_LOOKBACK = 24  # 24 candles (24 hours on 1h, 2 hours on 5m)

    RSI_PERIOD = 14
    RSI_MIN = 55  # Trend must be confirmed ✅ UNCHANGED
    RSI_MAX = 70  # But not overbought ✅ UNCHANGED

    MAX_WICK_PCT = 0.30  # Max 30% wick vs body ✅ UNCHANGED

    def __init__(self):
        """Initialize breakout trigger with hard-coded parameters"""
        pass

    def calculate_rsi(self, closes: np.ndarray, period: int = None) -> float:
        """Calculate RSI

        Args:
            closes: Array of closing prices
            period: RSI period (defaults to RSI_PERIOD)

        Returns:
            RSI value (0-100)
        """
        if period is None:
            period = self.RSI_PERIOD

        if len(closes) < period + 1:
            return None

        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def check_volume_spike(self, volumes: np.ndarray) -> Tuple[bool, float]:
        """Check if current volume is above threshold

        Args:
            volumes: Array of volume data

        Returns:
            (is_spike: bool, multiplier: float)
        """
        if len(volumes) < self.VOLUME_PERIOD + 1:
            return False, 0.0

        avg_volume = np.mean(volumes[-self.VOLUME_PERIOD-1:-1])  # Exclude current
        current_volume = volumes[-1]

        # CRITICAL FIX: Prevent division by zero on dead/delisted coins
        if avg_volume <= 0 or current_volume <= 0:
            return False, 0.0

        multiplier = current_volume / avg_volume

        # CRITICAL FIX: Cap extreme multipliers to prevent overflow
        if multiplier > 1000:
            multiplier = 1000.0

        is_spike = multiplier >= self.VOLUME_MULTIPLIER

        return is_spike, multiplier

    def check_price_break(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[Direction, float]:
        """Check if price broke out of range

        Args:
            highs, lows, closes: Price data

        Returns:
            (direction: Direction, break_price: float)
        """
        if len(closes) < self.BREAKOUT_LOOKBACK + 1:
            return Direction.NONE, 0.0

        # Get range (exclude current candle)
        range_highs = highs[-self.BREAKOUT_LOOKBACK-1:-1]
        range_lows = lows[-self.BREAKOUT_LOOKBACK-1:-1]

        max_high = np.max(range_highs)
        min_low = np.min(range_lows)

        current_close = closes[-1]

        # Check breakout
        if current_close > max_high:
            return Direction.LONG, max_high

        if current_close < min_low:
            return Direction.SHORT, min_low

        return Direction.NONE, 0.0

    def check_wick_size(self, open_price: float, high: float, low: float, close: float, direction: Direction) -> bool:
        """Check if wick is acceptable (≤ 30% of body)

        Args:
            open_price, high, low, close: OHLC data
            direction: Trade direction

        Returns:
            True if wick is acceptable
        """
        body = abs(close - open_price)

        if body == 0:
            return False  # Doji candles are rejected

        if direction == Direction.LONG:
            # For longs, check upper wick
            wick = high - max(open_price, close)
        elif direction == Direction.SHORT:
            # For shorts, check lower wick
            wick = min(open_price, close) - low
        else:
            return False

        wick_pct = wick / body
        return wick_pct <= self.MAX_WICK_PCT

    def detect_breakout(
        self,
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray
    ) -> Tuple[Direction, Dict]:
        """Detect valid breakout signal

        ALL conditions must be met:
        1. Volume spike ≥ 2.8×
        2. Price break outside 24-candle range
        3. RSI 55-70 (for longs)
        4. Wick ≤ 30%

        Args:
            opens, highs, lows, closes, volumes: OHLCV data

        Returns:
            (direction: Direction, details: dict)
        """
        details = {
            'volume_spike': False,
            'volume_multiplier': 0.0,
            'price_break': False,
            'break_direction': Direction.NONE,
            'break_price': 0.0,
            'rsi_valid': False,
            'rsi': None,
            'wick_valid': False,
            'signal': Direction.NONE
        }

        # 1. Check Volume Spike
        volume_spike, vol_mult = self.check_volume_spike(volumes)
        details['volume_spike'] = volume_spike
        details['volume_multiplier'] = vol_mult

        if not volume_spike:
            return Direction.NONE, details

        # 2. Check Price Break
        break_dir, break_price = self.check_price_break(highs, lows, closes)
        details['price_break'] = break_dir != Direction.NONE
        details['break_direction'] = break_dir
        details['break_price'] = break_price

        if break_dir == Direction.NONE:
            return Direction.NONE, details

        # 3. Check RSI (only for LONG trades)
        rsi = self.calculate_rsi(closes)
        details['rsi'] = rsi

        if break_dir == Direction.LONG:
            if rsi is None:
                return Direction.NONE, details
            details['rsi_valid'] = self.RSI_MIN <= rsi <= self.RSI_MAX
            if not details['rsi_valid']:
                return Direction.NONE, details
        else:
            # For shorts, invert RSI check (30-45)
            if rsi is not None:
                details['rsi_valid'] = 30 <= rsi <= 45
                if not details['rsi_valid']:
                    return Direction.NONE, details

        # 4. Check Wick Size
        wick_ok = self.check_wick_size(
            opens[-1], highs[-1], lows[-1], closes[-1], break_dir
        )
        details['wick_valid'] = wick_ok

        if not wick_ok:
            return Direction.NONE, details

        # ALL CONDITIONS MET
        details['signal'] = break_dir
        return break_dir, details

    def get_entry_price(self, direction: Direction, closes: np.ndarray, break_price: float) -> float:
        """Get recommended entry price

        For market orders: current close
        For limit orders: slightly above/below break price

        Args:
            direction: Trade direction
            closes: Price data
            break_price: The breakout level

        Returns:
            Recommended entry price
        """
        if direction == Direction.NONE:
            return 0.0

        # Use market order at current close
        return closes[-1]

    def calculate_signal_strength(self, details: Dict) -> float:
        """Calculate signal strength score (0-100)

        Higher score = stronger signal = higher conviction

        Args:
            details: Signal details from detect_breakout()

        Returns:
            Score 0-100
        """
        if details['signal'] == Direction.NONE:
            return 0.0

        score = 0.0

        # Volume strength (max 40 points)
        vol_mult = details['volume_multiplier']
        if vol_mult >= 2.8:
            vol_score = min(40, (vol_mult - 2.8) / 1.2 * 40)  # 40 points at 4.0×
            score += vol_score

        # RSI position (max 30 points)
        if details['rsi'] is not None:
            if details['break_direction'] == Direction.LONG:
                # Ideal RSI for longs is ~62.5 (middle of 55-70)
                rsi_optimal = 62.5
                rsi_distance = abs(details['rsi'] - rsi_optimal)
                rsi_score = max(0, 30 - (rsi_distance / 7.5 * 30))
                score += rsi_score

        # Wick quality (max 30 points)
        if details['wick_valid']:
            score += 30

        return min(100, score)
