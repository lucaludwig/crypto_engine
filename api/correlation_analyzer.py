#!/usr/bin/env python3
"""Correlation Analyzer - Prevents concentrated portfolio risk

Features:
- Calculates price correlation between trading pairs
- Checks new positions against existing portfolio
- Rejects correlated positions to prevent concentrated risk
- Caches correlations to reduce API calls
"""
import time
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import statistics


class CorrelationAnalyzer:
    """
    Analyzes price correlation between coins to avoid concentrated risk

    Example:
        If XVG and LUNC both dump together (high correlation),
        don't hold both at the same time
    """

    def __init__(self, binance_client):
        """Initialize correlation analyzer

        Args:
            binance_client: BinanceTradeClient instance
        """
        self.client = binance_client
        self.correlation_cache = {}  # (symbol1, symbol2) -> {'corr': float, 'valid_until': timestamp}
        self.cache_duration_seconds = 3600  # 1 hour

    def get_price_correlation(self, symbol1: str, symbol2: str,
                             timeframe: str = '1h', periods: int = 24) -> float:
        """Calculate correlation between two symbols

        Args:
            symbol1: First trading pair (e.g., 'NEIROUSDC')
            symbol2: Second trading pair (e.g., 'LUNCUSDC')
            timeframe: Candle timeframe ('1h', '4h', '1d')
            periods: Number of periods to analyze (default 24 = last 24 hours with 1h candles)

        Returns:
            Correlation coefficient (-1 to 1)
            > 0.7: Strong positive correlation (AVOID - will dump together)
            < 0.3: Low correlation (OK - diversified)
        """
        # Check cache first
        cache_key = tuple(sorted([symbol1, symbol2]))
        if cache_key in self.correlation_cache:
            cached = self.correlation_cache[cache_key]
            if cached['valid_until'] > time.time():
                return cached['corr']

        if self.client.dry_run:
            # In dry run, return random correlation
            import random
            return random.uniform(0.2, 0.6)

        try:
            # Fetch historical candles for both symbols
            klines1 = self.client.client.get_klines(
                symbol=symbol1,
                interval=timeframe,
                limit=periods
            )

            klines2 = self.client.client.get_klines(
                symbol=symbol2,
                interval=timeframe,
                limit=periods
            )

            if not klines1 or not klines2 or len(klines1) < 10 or len(klines2) < 10:
                # Not enough data, assume low correlation
                return 0.0

            # Extract close prices
            prices1 = [float(k[4]) for k in klines1]  # Close price is index 4
            prices2 = [float(k[4]) for k in klines2]

            # Calculate returns (percent change)
            returns1 = [(prices1[i] - prices1[i-1]) / prices1[i-1] * 100
                       for i in range(1, len(prices1))]
            returns2 = [(prices2[i] - prices2[i-1]) / prices2[i-1] * 100
                       for i in range(1, len(prices2))]

            # Calculate Pearson correlation coefficient
            corr = self._calculate_pearson_correlation(returns1, returns2)

            # Cache result
            self.correlation_cache[cache_key] = {
                'corr': corr,
                'valid_until': time.time() + self.cache_duration_seconds
            }

            return corr

        except Exception as e:
            print(f"Error calculating correlation between {symbol1} and {symbol2}: {e}")
            return 0.0  # Assume no correlation on error

    def _calculate_pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient

        Formula: r = Σ((x - x_mean)(y - y_mean)) / sqrt(Σ(x - x_mean)² * Σ(y - y_mean)²)

        Returns:
            Correlation coefficient between -1 and 1
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = min(len(x), len(y))
        x = x[:n]
        y = y[:n]

        try:
            # Calculate means
            x_mean = statistics.mean(x)
            y_mean = statistics.mean(y)

            # Calculate covariance and standard deviations
            covariance = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            x_variance = sum((x[i] - x_mean) ** 2 for i in range(n))
            y_variance = sum((y[i] - y_mean) ** 2 for i in range(n))

            if x_variance == 0 or y_variance == 0:
                return 0.0

            correlation = covariance / ((x_variance * y_variance) ** 0.5)

            # Clamp to [-1, 1] range
            return max(-1.0, min(1.0, correlation))

        except Exception as e:
            print(f"Error in correlation calculation: {e}")
            return 0.0

    def check_portfolio_correlation(self, new_symbol: str,
                                   existing_positions: List[str],
                                   max_correlation: float = 0.7) -> Tuple[bool, str]:
        """Check if new symbol is too correlated with existing portfolio

        Args:
            new_symbol: New symbol to check (e.g., 'NEIROUSDC')
            existing_positions: List of existing position symbols (base assets, e.g., ['XVG', 'LUNC'])
            max_correlation: Maximum allowed correlation (default 0.7)

        Returns:
            (should_trade, reason)

        Example:
            (False, "Too correlated with XVG (0.85)")
            (True, "OK - Max correlation 0.42 with LUNC")
        """
        if not existing_positions:
            return True, "No existing positions to correlate with"

        correlations = []
        max_corr_symbol = None
        max_corr_value = 0.0

        for existing_symbol in existing_positions:
            # Build full symbol pairs
            quote = self.client.quote_currency

            # Existing symbol might be base asset or full pair
            if not existing_symbol.endswith(('USDC', 'USDT', 'BUSD')):
                existing_pair = f"{existing_symbol}{quote}"
            else:
                existing_pair = existing_symbol

            # Calculate correlation
            corr = abs(self.get_price_correlation(new_symbol, existing_pair))
            correlations.append(corr)

            if corr > max_corr_value:
                max_corr_value = corr
                max_corr_symbol = existing_symbol.replace('USDC', '').replace('USDT', '').replace('BUSD', '')

        # Check if any correlation exceeds threshold
        if max_corr_value > max_correlation:
            return False, f"Too correlated with {max_corr_symbol} ({max_corr_value:.2f})"

        return True, f"OK - Max correlation {max_corr_value:.2f} with {max_corr_symbol}"

    def get_correlation_matrix(self, symbols: List[str]) -> dict:
        """Generate correlation matrix for portfolio visualization

        Args:
            symbols: List of trading pair symbols

        Returns:
            Dict mapping (symbol1, symbol2) -> correlation

        Useful for understanding portfolio risk concentration
        """
        matrix = {}

        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                corr = self.get_price_correlation(sym1, sym2)
                matrix[(sym1, sym2)] = corr

        return matrix

    def clear_cache(self):
        """Clear correlation cache (e.g., after market regime change)"""
        self.correlation_cache = {}
