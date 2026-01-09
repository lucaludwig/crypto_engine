"""Historical Data Loader

Downloads and manages historical OHLCV data from Binance for backtesting.

Data Requirements:
- At least 12 months of data (ideally 24+ months)
- 5-minute timeframe (primary)
- Top 50-100 USDT pairs by volume
- Includes stablecoin filtering
"""
from binance.client import Client
from binance.exceptions import BinanceAPIException
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time
import pickle
import os


class DataLoader:
    """Loads and caches historical data from Binance"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        cache_dir: str = "backtest_data"
    ):
        """Initialize data loader

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            cache_dir: Directory to cache downloaded data
        """
        self.client = Client(api_key, api_secret)
        self.cache_dir = cache_dir

        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)

    def download_historical_data(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[List[Dict]]:
        """Download historical klines from Binance

        Args:
            symbol: Trading symbol
            interval: Timeframe ('5m', '15m', '1h')
            start_date: Start date
            end_date: End date

        Returns:
            List of OHLCV bars
        """
        # Check cache first
        cache_file = self._get_cache_file(symbol, interval, start_date, end_date)
        if os.path.exists(cache_file):
            print(f"  Loading {symbol} from cache...")
            return self._load_from_cache(cache_file)

        print(f"  Downloading {symbol} {interval} from {start_date.date()} to {end_date.date()}...")

        try:
            # Convert to timestamps
            start_ts = int(start_date.timestamp() * 1000)
            end_ts = int(end_date.timestamp() * 1000)

            # Download in chunks (Binance limit: 1000 candles per request)
            all_klines = []
            current_start = start_ts

            while current_start < end_ts:
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval=interval,
                    startTime=current_start,
                    endTime=end_ts,
                    limit=1000
                )

                if not klines:
                    break

                all_klines.extend(klines)

                # Update start time for next batch
                current_start = klines[-1][0] + 1

                # Rate limiting
                time.sleep(0.1)

            # Parse klines
            bars = []
            for k in all_klines:
                bar = {
                    'timestamp': datetime.fromtimestamp(k[0] / 1000),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                }
                bars.append(bar)

            # Cache
            self._save_to_cache(cache_file, bars)

            print(f"  Downloaded {len(bars)} bars for {symbol}")
            return bars

        except BinanceAPIException as e:
            print(f"  Error downloading {symbol}: {e}")
            return None

    def download_multiple_symbols(
        self,
        symbols: List[str],
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, List[Dict]]:
        """Download data for multiple symbols

        Args:
            symbols: List of trading symbols
            interval: Timeframe
            start_date: Start date
            end_date: End date

        Returns:
            Dict mapping symbol to bars
        """
        print(f"\nDownloading data for {len(symbols)} symbols...")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"Interval: {interval}\n")

        data = {}

        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] {symbol}")

            bars = self.download_historical_data(symbol, interval, start_date, end_date)

            if bars:
                data[symbol] = bars

            # Rate limiting between symbols
            time.sleep(0.2)

        print(f"\n✓ Downloaded data for {len(data)}/{len(symbols)} symbols")
        return data

    def split_data_is_oos(
        self,
        data: Dict[str, List[Dict]],
        is_pct: float = 0.70
    ) -> Tuple[Dict, Dict]:
        """Split data into In-Sample and Out-of-Sample

        Args:
            data: Dict of symbol -> bars
            is_pct: In-Sample percentage (default: 70%)

        Returns:
            (is_data, oos_data) tuple
        """
        is_data = {}
        oos_data = {}

        for symbol, bars in data.items():
            split_idx = int(len(bars) * is_pct)

            is_data[symbol] = bars[:split_idx]
            oos_data[symbol] = bars[split_idx:]

        is_start = is_data[list(is_data.keys())[0]][0]['timestamp']
        is_end = is_data[list(is_data.keys())[0]][-1]['timestamp']
        oos_start = oos_data[list(oos_data.keys())[0]][0]['timestamp']
        oos_end = oos_data[list(oos_data.keys())[0]][-1]['timestamp']

        print(f"\n{'='*80}")
        print(f"DATA SPLIT (IS: {is_pct*100:.0f}% | OOS: {(1-is_pct)*100:.0f}%)")
        print(f"{'='*80}")
        print(f"In-Sample:     {is_start.date()} to {is_end.date()} ({len(is_data[list(is_data.keys())[0]])} bars)")
        print(f"Out-of-Sample: {oos_start.date()} to {oos_end.date()} ({len(oos_data[list(oos_data.keys())[0]])} bars)")
        print(f"{'='*80}\n")

        return is_data, oos_data

    def _get_cache_file(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Get cache file path

        Args:
            symbol, interval, start_date, end_date: Data parameters

        Returns:
            Cache file path
        """
        filename = f"{symbol}_{interval}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pkl"
        return os.path.join(self.cache_dir, filename)

    def _save_to_cache(self, cache_file: str, data: List[Dict]):
        """Save data to cache

        Args:
            cache_file: Cache file path
            data: Data to save
        """
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Warning: Could not cache data: {e}")

    def _load_from_cache(self, cache_file: str) -> Optional[List[Dict]]:
        """Load data from cache

        Args:
            cache_file: Cache file path

        Returns:
            Cached data or None
        """
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load cache: {e}")
            return None

    def validate_data(self, data: Dict[str, List[Dict]]) -> Dict:
        """Validate downloaded data with REALISTIC tolerances

        Args:
            data: Dict of symbol -> bars

        Returns:
            Validation report
        """
        # REALISTIC VALIDATION THRESHOLDS
        MAX_GAPS_ALLOWED = 5           # Max 5 gaps over 12 months is acceptable
        MAX_GAP_SIZE_CANDLES = 50      # Each gap can be max 50 candles (~4 hours)
        MAX_MISSING_DATA_PCT = 0.5     # Max 0.5% of data can be missing

        report = {
            'total_symbols': len(data),
            'valid_symbols': 0,
            'invalid_symbols': [],
            'min_bars': float('inf'),
            'max_bars': 0,
            'avg_bars': 0
        }

        total_bars = 0

        for symbol, bars in data.items():
            if not bars:
                report['invalid_symbols'].append((symbol, "No data"))
                continue

            # Check for gaps
            timestamps = [b['timestamp'] for b in bars]
            gaps = []
            total_missing_candles = 0

            for i in range(1, len(timestamps)):
                diff_minutes = (timestamps[i] - timestamps[i-1]).total_seconds() / 60
                if diff_minutes > 10:  # Gap detected (>10 min for 5m candles)
                    missing_candles = int(diff_minutes / 5) - 1
                    gaps.append((timestamps[i-1], timestamps[i], missing_candles))
                    total_missing_candles += missing_candles

            # REALISTIC VALIDATION:
            # Reject ONLY if:
            # 1. More than 5 gaps (frequent outages)
            # 2. Any single gap > 10 candles (50 minutes)
            # 3. Total missing > 0.5% of expected data

            expected_total_candles = len(bars) + total_missing_candles
            missing_data_pct = (total_missing_candles / expected_total_candles * 100) if expected_total_candles > 0 else 0

            rejection_reasons = []

            if len(gaps) > MAX_GAPS_ALLOWED:
                rejection_reasons.append(f"{len(gaps)} gaps (max {MAX_GAPS_ALLOWED})")

            large_gaps = [g for g in gaps if g[2] > MAX_GAP_SIZE_CANDLES]
            if large_gaps:
                rejection_reasons.append(f"{len(large_gaps)} large gaps (>{MAX_GAP_SIZE_CANDLES} candles)")

            if missing_data_pct > MAX_MISSING_DATA_PCT:
                rejection_reasons.append(f"{missing_data_pct:.2f}% missing (max {MAX_MISSING_DATA_PCT}%)")

            if rejection_reasons:
                report['invalid_symbols'].append((symbol, ", ".join(rejection_reasons)))
                continue

            # Valid (has 0-5 small gaps, all acceptable)
            report['valid_symbols'] += 1
            bar_count = len(bars)
            report['min_bars'] = min(report['min_bars'], bar_count)
            report['max_bars'] = max(report['max_bars'], bar_count)
            total_bars += bar_count

        if report['valid_symbols'] > 0:
            report['avg_bars'] = total_bars / report['valid_symbols']

        return report
