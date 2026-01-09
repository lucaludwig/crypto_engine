"""Volatility Compression Detector

HYBRID NUMBERS (Balanced - Not Too Strict):
- Bollinger Bands: Period=20, StdDev=2.0, Width < 0.045 (4.5%)
- ATR(14): Must be in lower 22% percentile of last 300 candles
- Keltner Channels: Period=20, Multiplier=1.5
- Price must be inside BOTH BB and KC simultaneously

This module identifies when a market is "loaded" and ready to explode.
"""
import numpy as np
from typing import Dict, List, Tuple, Optional


class CompressionDetector:
    """Detects volatility compression patterns

    A coin is tradeable ONLY when ALL conditions are met:
    1. BB Width < 3% (dead market)
    2. ATR in lower 15% (historically low volatility)
    3. Price inside both BB and Keltner Channels (squeeze)
    """

    # AGGRESSIVE GROWTH MODE - More opportunities
    BB_PERIOD = 20
    BB_STD_DEV = 2.0
    BB_WIDTH_THRESHOLD = 0.08  # 8% (was 4.5%)

    ATR_PERIOD = 14
    ATR_LOOKBACK = 300  # 300 candles for percentile calculation
    ATR_PERCENTILE_MAX = 22  # Must be in lower 22% (was 15%)

    KC_PERIOD = 20
    KC_MULTIPLIER = 1.5

    def __init__(self):
        """Initialize compression detector with hard-coded parameters"""
        pass

    def calculate_bollinger_bands(self, closes: np.ndarray) -> Dict[str, float]:
        """Calculate Bollinger Bands

        Args:
            closes: Array of closing prices (at least BB_PERIOD length)

        Returns:
            Dict with 'upper', 'middle', 'lower', 'width' (as % of price)
        """
        if len(closes) < self.BB_PERIOD:
            return None

        sma = np.mean(closes[-self.BB_PERIOD:])
        std = np.std(closes[-self.BB_PERIOD:], ddof=1)

        upper = sma + (self.BB_STD_DEV * std)
        lower = sma - (self.BB_STD_DEV * std)
        width = (upper - lower) / sma  # Relative width

        return {
            'upper': upper,
            'middle': sma,
            'lower': lower,
            'width': width,
            'current_price': closes[-1]
        }

    def calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
        """Calculate Average True Range (ATR)

        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of closing prices

        Returns:
            Current ATR value
        """
        if len(closes) < self.ATR_PERIOD + 1:
            return None

        # True Range calculation
        tr_list = []
        for i in range(1, len(closes)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr = max(hl, hc, lc)
            tr_list.append(tr)

        tr_array = np.array(tr_list)
        if len(tr_array) < self.ATR_PERIOD:
            return None

        # Simple moving average of TR
        atr = np.mean(tr_array[-self.ATR_PERIOD:])
        return atr

    def calculate_atr_percentile(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
        """Calculate current ATR percentile rank over lookback period

        Args:
            highs, lows, closes: Price arrays (need ATR_LOOKBACK length)

        Returns:
            Percentile rank (0-100) of current ATR
        """
        if len(closes) < self.ATR_LOOKBACK:
            return None

        # Calculate rolling ATR values
        atr_values = []
        for i in range(self.ATR_PERIOD, len(closes)):
            atr = self.calculate_atr(
                highs[i-self.ATR_PERIOD:i+1],
                lows[i-self.ATR_PERIOD:i+1],
                closes[i-self.ATR_PERIOD:i+1]
            )
            if atr is not None:
                atr_values.append(atr)

        if not atr_values:
            return None

        current_atr = atr_values[-1]
        percentile = (np.sum(np.array(atr_values) < current_atr) / len(atr_values)) * 100

        return percentile

    def calculate_keltner_channels(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Dict[str, float]:
        """Calculate Keltner Channels

        Args:
            highs, lows, closes: Price arrays

        Returns:
            Dict with 'upper', 'middle', 'lower'
        """
        if len(closes) < self.KC_PERIOD:
            return None

        ema = closes[-self.KC_PERIOD:].mean()  # Using SMA for simplicity
        atr = self.calculate_atr(highs, lows, closes)

        if atr is None:
            return None

        upper = ema + (self.KC_MULTIPLIER * atr)
        lower = ema - (self.KC_MULTIPLIER * atr)

        return {
            'upper': upper,
            'middle': ema,
            'lower': lower
        }

    def is_compressed(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> Tuple[bool, Dict]:
        """Check if market is in compression (ready to explode)

        ALL conditions must be TRUE:
        1. BB Width < 3%
        2. ATR in lower 15% percentile
        3. Price inside both BB and KC

        Args:
            highs, lows, closes: Price data (need ATR_LOOKBACK candles)

        Returns:
            (is_compressed: bool, details: dict)
        """
        details = {
            'bb_compressed': False,
            'atr_low': False,
            'inside_squeeze': False,
            'bb_width': None,
            'atr_percentile': None
        }

        # 1. Check Bollinger Band Width
        bb = self.calculate_bollinger_bands(closes)
        if bb is None:
            return False, details

        details['bb_width'] = bb['width']
        details['bb_compressed'] = bb['width'] < self.BB_WIDTH_THRESHOLD

        # 2. Check ATR Percentile
        atr_percentile = self.calculate_atr_percentile(highs, lows, closes)
        if atr_percentile is None:
            return False, details

        details['atr_percentile'] = atr_percentile
        details['atr_low'] = atr_percentile < self.ATR_PERCENTILE_MAX

        # 3. Check Keltner Squeeze
        kc = self.calculate_keltner_channels(highs, lows, closes)
        if kc is None:
            return False, details

        current_price = closes[-1]
        inside_bb = bb['lower'] < current_price < bb['upper']
        inside_kc = kc['lower'] < current_price < kc['upper']
        details['inside_squeeze'] = inside_bb and inside_kc

        # ALL must be true
        is_compressed = (
            details['bb_compressed'] and
            details['atr_low'] and
            details['inside_squeeze']
        )

        return is_compressed, details

    def get_compression_score(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> float:
        """Get compression strength score (0-100)

        Higher score = tighter compression = higher explosion potential

        Returns:
            Score 0-100 (only returns score if is_compressed=True, else 0)
        """
        is_compressed, details = self.is_compressed(highs, lows, closes)

        if not is_compressed:
            return 0.0

        # Score based on how tight the compression is
        bb_score = max(0, 100 * (1 - details['bb_width'] / self.BB_WIDTH_THRESHOLD))
        atr_score = max(0, 100 * (1 - details['atr_percentile'] / self.ATR_PERCENTILE_MAX))

        # Average the two scores
        score = (bb_score + atr_score) / 2

        return min(100, score)
