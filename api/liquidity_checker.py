#!/usr/bin/env python3
"""Liquidity Checker - Ensures sufficient liquidity before opening positions

Features:
- Validates 24h trading volume
- Checks bid-ask spread
- Ensures position can be exited without significant slippage
- Prevents entering illiquid positions
"""
from typing import Tuple


class LiquidityChecker:
    """
    Validates liquidity before opening positions

    Prevents scenarios where:
    - Volume is too low to exit without slippage
    - Bid-ask spread is too wide (illiquid market)
    - Position size is too large relative to daily volume
    """

    # Liquidity thresholds
    MIN_VOLUME_USDT = 500_000  # $500k minimum 24h volume
    MIN_VOLUME_POSITION_RATIO = 10  # Volume should be 10x position size
    MAX_SPREAD_PCT = 1.0  # Max 1% bid-ask spread

    def __init__(self, binance_client):
        """Initialize liquidity checker

        Args:
            binance_client: BinanceTradeClient instance
        """
        self.client = binance_client

    def check_liquidity(self, symbol: str, position_size_usdt: float) -> Tuple[bool, str]:
        """Check if symbol has sufficient liquidity

        Args:
            symbol: Trading pair (e.g., 'NEIROUSDC')
            position_size_usdt: Intended position size in USDT

        Returns:
            (has_liquidity, reason)

        Criteria:
        1. 24h volume > $500k (absolute minimum)
        2. Volume > 10x position size (can exit without slippage)
        3. Bid-ask spread < 1% (not too illiquid)
        """
        if self.client.dry_run:
            # In dry run, assume liquidity is sufficient
            return True, "OK (dry-run mode)"

        try:
            # Get 24h ticker stats
            ticker = self.client.client.get_ticker(symbol=symbol)
            volume_24h_usdt = float(ticker['quoteVolume'])

            # Check 1: Absolute volume
            if volume_24h_usdt < self.MIN_VOLUME_USDT:
                return False, f"Low 24h volume: ${volume_24h_usdt:,.0f} (need ${self.MIN_VOLUME_USDT:,.0f})"

            # Check 2: Relative to position size
            volume_ratio = volume_24h_usdt / position_size_usdt if position_size_usdt > 0 else 0
            if volume_ratio < self.MIN_VOLUME_POSITION_RATIO:
                return False, f"Volume too low vs position size (only {volume_ratio:.1f}x, need {self.MIN_VOLUME_POSITION_RATIO}x)"

            # Check 3: Bid-ask spread
            order_book = self.client.client.get_order_book(symbol=symbol, limit=5)

            if not order_book.get('bids') or not order_book.get('asks'):
                return False, "Order book is empty"

            best_bid = float(order_book['bids'][0][0])
            best_ask = float(order_book['asks'][0][0])

            if best_bid == 0:
                return False, "No bids in order book"

            spread_pct = (best_ask - best_bid) / best_bid * 100

            if spread_pct > self.MAX_SPREAD_PCT:
                return False, f"Spread too wide: {spread_pct:.2f}% (max {self.MAX_SPREAD_PCT}%)"

            return True, f"OK - Volume: ${volume_24h_usdt:,.0f}, Spread: {spread_pct:.3f}%"

        except Exception as e:
            print(f"Error checking liquidity for {symbol}: {e}")
            # On error, be conservative and reject
            return False, f"Error checking liquidity: {str(e)[:50]}"

    def get_order_book_depth(self, symbol: str, levels: int = 10) -> dict:
        """Get order book depth for analysis

        Args:
            symbol: Trading pair
            levels: Number of levels to analyze

        Returns:
            {
                'bid_depth_usdt': total USDT in bids,
                'ask_depth_usdt': total USDT in asks,
                'spread_pct': bid-ask spread percentage
            }
        """
        if self.client.dry_run:
            return {'bid_depth_usdt': 0, 'ask_depth_usdt': 0, 'spread_pct': 0}

        try:
            order_book = self.client.client.get_order_book(symbol=symbol, limit=levels)

            # Calculate depth
            bid_depth = sum(float(bid[0]) * float(bid[1]) for bid in order_book['bids'])
            ask_depth = sum(float(ask[0]) * float(ask[1]) for ask in order_book['asks'])

            best_bid = float(order_book['bids'][0][0]) if order_book['bids'] else 0
            best_ask = float(order_book['asks'][0][0]) if order_book['asks'] else 0

            spread_pct = (best_ask - best_bid) / best_bid * 100 if best_bid > 0 else 0

            return {
                'bid_depth_usdt': bid_depth,
                'ask_depth_usdt': ask_depth,
                'spread_pct': spread_pct
            }

        except Exception as e:
            print(f"Error getting order book depth for {symbol}: {e}")
            return {'bid_depth_usdt': 0, 'ask_depth_usdt': 0, 'spread_pct': 0}
