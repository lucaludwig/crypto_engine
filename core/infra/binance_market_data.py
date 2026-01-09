"""Binance Market Data Client

Fetches OHLCV data for compression/breakout detection.

Optimized for:
- Top 50-100 USDT Perpetuals by 30-day volume
- 5-minute and 15-minute timeframes
- Efficient batch fetching
- Retry logic with exponential backoff
"""
from binance.client import Client
from binance.exceptions import BinanceAPIException
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time


def retry_on_failure(max_retries: int = 3, base_delay: float = 0.5):
    """Decorator for retrying API calls with exponential backoff"""
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
                        time.sleep(delay)
            # CRITICAL FIX: Log failure after max retries
            if last_exception:
                print(f"  ⚠️ {func.__name__}() failed after {max_retries + 1} attempts: {last_exception}")
            # Return None instead of raising for market data (non-critical)
            return None
        return wrapper
    return decorator


class BinanceMarketData:
    """Fetches and processes market data from Binance

    Focus on USDT Perpetual Futures for:
    - Higher leverage
    - Better liquidity
    - Lower fees
    """

    # Supported timeframes
    TIMEFRAME_5M = "5m"
    TIMEFRAME_15M = "15m"
    TIMEFRAME_1H = "1h"

    # STABLECOIN & FIAT FILTER (CRITICAL!)
    # These are NOT tradeable - they have no volatility
    STABLECOINS = [
        'USDT', 'USDC', 'BUSD', 'TUSD', 'USDD', 'FDUSD', 'USDP',
        'DAI', 'FRAX', 'GUSD', 'PAX', 'PAXG', 'LUSD', 'SUSD',
        'USDN', 'UST', 'USTC', 'ALUSD', 'MIM', 'CUSD', 'USDJ'
    ]

    FIAT_CURRENCIES = [
        'USD', 'EUR', 'GBP', 'AUD', 'BRL', 'TRY', 'RUB', 'UAH',
        'NGN', 'PLN', 'ARS', 'BIDR', 'ZAR', 'VAI'
    ]

    def __init__(self, api_key: str = None, api_secret: str = None):
        """Initialize Binance client

        Args:
            api_key: Binance API key (optional for market data)
            api_secret: Binance API secret (optional for market data)
        """
        self.client = Client(api_key, api_secret)

    def is_stablecoin_or_fiat_pair(self, symbol: str, quote_asset: str = "USDT") -> bool:
        """Check if symbol is a stablecoin or fiat pair (MUST BE FILTERED!)

        Args:
            symbol: Trading symbol (e.g., 'FDUSDUSDT', 'EURUSDT')
            quote_asset: Quote asset (e.g., 'USDT')

        Returns:
            True if this is a stablecoin/fiat pair (should NOT be traded)
        """
        # Extract base asset (everything before quote asset)
        if not symbol.endswith(quote_asset):
            return False

        base_asset = symbol[:-len(quote_asset)]

        # Check if base asset is a stablecoin
        if base_asset in self.STABLECOINS:
            return True

        # Check if base asset contains fiat currency
        for fiat in self.FIAT_CURRENCIES:
            if fiat in base_asset:
                return True

        return False

    def get_top_symbols_by_volume(self, limit: int = 100, quote_asset: str = "USDC") -> List[str]:
        """Get top symbols by 24h volume

        CRITICAL: Filters out stablecoins and fiat pairs!

        Args:
            limit: Number of symbols to return
            quote_asset: Quote asset (default: USDC)

        Returns:
            List of symbols sorted by volume descending (NO STABLECOINS!)
        """
        try:
            # Get 24h ticker for all symbols
            tickers = self.client.get_ticker()

            # Filter for USDT pairs and sort by volume
            usdt_pairs = []
            filtered_count = 0
            for ticker in tickers:
                symbol = ticker['symbol']

                # Must end with quote asset
                if not symbol.endswith(quote_asset):
                    continue

                # CRITICAL: Filter stablecoins and fiat pairs
                if self.is_stablecoin_or_fiat_pair(symbol, quote_asset):
                    filtered_count += 1
                    continue

                try:
                    volume_usdt = float(ticker['quoteVolume'])
                    usdt_pairs.append((symbol, volume_usdt))
                except (KeyError, ValueError):
                    continue

            # Sort by volume descending
            usdt_pairs.sort(key=lambda x: x[1], reverse=True)

            # Return top N symbols
            top_symbols = [symbol for symbol, volume in usdt_pairs[:limit]]

            print(f"  Filtered {filtered_count} stablecoin/fiat pairs")
            return top_symbols

        except BinanceAPIException as e:
            print(f"Error fetching top symbols: {e}")
            return []

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: Optional[int] = None
    ) -> Optional[Dict]:
        """Fetch kline/candlestick data

        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Timeframe ('5m', '15m', '1h')
            limit: Number of candles (max 1000)
            start_time: Start timestamp in ms (optional)

        Returns:
            Dict with 'opens', 'highs', 'lows', 'closes', 'volumes' as numpy arrays
        """
        # Fetch klines (retry decorator handles exceptions)
        klines = self.client.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            startTime=start_time
        )

        if not klines:
            return None

        # Parse klines into arrays
        opens = np.array([float(k[1]) for k in klines])
        highs = np.array([float(k[2]) for k in klines])
        lows = np.array([float(k[3]) for k in klines])
        closes = np.array([float(k[4]) for k in klines])
        volumes = np.array([float(k[5]) for k in klines])
        timestamps = np.array([int(k[0]) for k in klines])

        return {
            'symbol': symbol,
            'interval': interval,
            'timestamps': timestamps,
            'opens': opens,
            'highs': highs,
            'lows': lows,
            'closes': closes,
            'volumes': volumes,
            'count': len(opens)
        }

    @retry_on_failure(max_retries=3, base_delay=0.5)
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price

        Args:
            symbol: Trading symbol

        Returns:
            Current price or None
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])

    def get_24h_stats(self, symbol: str) -> Optional[Dict]:
        """Get 24h statistics

        Args:
            symbol: Trading symbol

        Returns:
            Dict with 24h stats
        """
        try:
            ticker = self.client.get_ticker(symbol=symbol)

            return {
                'symbol': symbol,
                'price_change_pct': float(ticker['priceChangePercent']),
                'volume': float(ticker['volume']),
                'quote_volume': float(ticker['quoteVolume']),
                'high': float(ticker['highPrice']),
                'low': float(ticker['lowPrice']),
                'last_price': float(ticker['lastPrice'])
            }

        except BinanceAPIException as e:
            print(f"Error fetching 24h stats for {symbol}: {e}")
            return None

    def batch_get_klines(
        self,
        symbols: List[str],
        interval: str,
        limit: int = 500,
        delay_ms: int = 100
    ) -> Dict[str, Dict]:
        """Fetch klines for multiple symbols

        Args:
            symbols: List of trading symbols
            interval: Timeframe
            limit: Number of candles per symbol
            delay_ms: Delay between requests in ms

        Returns:
            Dict mapping symbol to klines data
        """
        results = {}

        for i, symbol in enumerate(symbols):
            klines = self.get_klines(symbol, interval, limit)
            if klines:
                results[symbol] = klines

            # Rate limiting
            if i < len(symbols) - 1:
                time.sleep(delay_ms / 1000)

        return results

    def get_market_snapshot(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get quick market snapshot for multiple symbols

        Args:
            symbols: List of trading symbols

        Returns:
            Dict mapping symbol to current stats
        """
        snapshot = {}

        try:
            # Batch fetch tickers (more efficient)
            tickers = self.client.get_ticker()
            ticker_map = {t['symbol']: t for t in tickers}

            for symbol in symbols:
                if symbol in ticker_map:
                    ticker = ticker_map[symbol]
                    snapshot[symbol] = {
                        'price': float(ticker['lastPrice']),
                        'volume_24h': float(ticker['quoteVolume']),
                        'change_24h_pct': float(ticker['priceChangePercent']),
                        'high_24h': float(ticker['highPrice']),
                        'low_24h': float(ticker['lowPrice'])
                    }

        except BinanceAPIException as e:
            print(f"Error fetching market snapshot: {e}")

        return snapshot

    def calculate_lookback_timestamp(self, interval: str, candles: int) -> int:
        """Calculate start timestamp for fetching N candles

        Args:
            interval: Timeframe ('5m', '15m', '1h')
            candles: Number of candles to lookback

        Returns:
            Timestamp in milliseconds
        """
        # Map interval to minutes
        interval_minutes = {
            '1m': 1,
            '5m': 5,
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '1d': 1440
        }

        if interval not in interval_minutes:
            raise ValueError(f"Unsupported interval: {interval}")

        minutes = interval_minutes[interval]
        lookback_minutes = minutes * candles

        start_time = datetime.now() - timedelta(minutes=lookback_minutes)
        return int(start_time.timestamp() * 1000)
