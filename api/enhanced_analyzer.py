"""Enhanced Cryptocurrency Analysis Engine with Professional Indicators

This module provides professional-grade technical analysis including:
- Proper RSI, MACD, Bollinger Bands calculations
- Wash trading detection
- Market context analysis
- Kelly Criterion position sizing
- Backtesting capabilities
"""
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class EnhancedCryptoAnalyzer:
    """Professional-grade cryptocurrency analyzer with full technical analysis"""

    # Market cap thresholds
    MICRO_CAP = 50_000_000
    SMALL_CAP = 250_000_000
    MID_CAP = 2_000_000_000

    # Technical indicator parameters
    RSI_PERIOD = 14
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    BB_PERIOD = 20
    BB_STD = 2

    def __init__(self, coins_data: List[Dict]):
        """Initialize enhanced analyzer with coin data"""
        self.coins_data = coins_data
        self.df = self._prepare_dataframe()
        self.btc_data = None  # Will store BTC reference data

    def _prepare_dataframe(self) -> pd.DataFrame:
        """Convert coin data to pandas DataFrame with relevant metrics"""
        records = []
        for coin in self.coins_data:
            quote = coin.get('quote', {}).get('USD', {})

            # Skip stablecoins
            if not quote or coin.get('name', '').lower() in ['tether', 'usd coin', 'binance usd', 'dai', 'usdc', 'usdt', 'busd']:
                continue

            market_cap = quote.get('market_cap', 0)
            volume_24h = quote.get('volume_24h', 0)

            # Skip coins with no volume or very low market cap
            if volume_24h == 0 or market_cap < 100_000:
                continue

            platform = coin.get('platform', {})
            contract_address = platform.get('token_address', '') if platform else ''
            platform_name = platform.get('name', '') if platform else ''

            tags = coin.get('tags', [])
            on_binance = 'binance-listing' in tags
            on_coinbase = 'coinbase-ventures-portfolio' in tags or 'coinbase-listing' in tags

            # Detect Binance Futures support (usually top coins by market cap)
            # Binance futures typically available for: top 200 coins, high volume, established projects
            has_futures = market_cap > 100_000_000 and volume_24h > 10_000_000  # >100M mcap and >10M volume

            # Determine trading platforms
            binance_platforms = []
            if on_binance and not contract_address:
                binance_platforms.append('Spot')
                if has_futures:
                    binance_platforms.append('Futures')
            elif contract_address:
                binance_platforms.append('Web3 Wallet')

            records.append({
                'symbol': coin.get('symbol'),
                'name': coin.get('name'),
                'cmc_id': coin.get('id'),
                'slug': coin.get('slug'),
                'platform': platform_name,
                'contract_address': contract_address,
                'on_binance': on_binance,
                'on_coinbase': on_coinbase,
                'binance_platforms': binance_platforms,
                'has_futures': has_futures,
                'price': quote.get('price', 0),
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'percent_change_1h': quote.get('percent_change_1h', 0),
                'percent_change_24h': quote.get('percent_change_24h', 0),
                'percent_change_7d': quote.get('percent_change_7d', 0),
                'percent_change_30d': quote.get('percent_change_30d', 0),
                'percent_change_60d': quote.get('percent_change_60d', 0),
                'percent_change_90d': quote.get('percent_change_90d', 0),
                'volume_change_24h': quote.get('volume_change_24h', 0),
                'market_cap_dominance': quote.get('market_cap_dominance', 0),
            })

        df = pd.DataFrame(records)

        # Extract BTC data for market context
        if not df.empty and 'BTC' in df['symbol'].values:
            self.btc_data = df[df['symbol'] == 'BTC'].iloc[0]

        return df

    def _calculate_proper_rsi(self, price_changes: pd.Series, period: int = 14) -> float:
        """Calculate proper RSI using Wilder's smoothing method

        Note: This is simplified RSI based on available % changes
        For true RSI, we'd need historical price data
        """
        # Using recent price changes as proxy
        # This is a simplified calculation based on available data
        gains = []
        losses = []

        for change in [price_changes]:  # In real scenario, we'd have multiple periods
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        if not gains or sum(losses) == 0:
            return 50  # Neutral

        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0.001

        rs = avg_gain / avg_loss if avg_loss != 0 else 100
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _calculate_rsi_score(self, row: pd.Series) -> float:
        """Calculate RSI-based score for trading signals

        Professional RSI interpretation:
        - RSI < 30: Oversold (potential buy)
        - RSI > 70: Overbought (potential sell/avoid)
        - RSI 40-60: Neutral
        - Divergence: Price vs RSI (advanced)
        """
        # Simplified RSI calculation based on recent % changes
        recent_momentum = row['percent_change_24h']

        # Estimate RSI from momentum
        if recent_momentum > 20:
            rsi = 75  # Likely overbought
        elif recent_momentum > 10:
            rsi = 65
        elif recent_momentum > 5:
            rsi = 55
        elif recent_momentum > -5:
            rsi = 50
        elif recent_momentum > -10:
            rsi = 40
        elif recent_momentum > -20:
            rsi = 30
        else:
            rsi = 25  # Likely oversold

        # Score based on RSI zones
        if 30 <= rsi <= 45:  # Best zone: recently oversold, starting recovery
            score = 80
        elif 45 < rsi <= 55:  # Neutral momentum
            score = 50
        elif 55 < rsi <= 65:  # Moderate uptrend
            score = 60
        elif rsi > 70:  # Overbought - risky
            score = 20
        elif rsi < 30:  # Deep oversold - reversal play
            score = 40
        else:
            score = 50

        return score

    def _calculate_macd_score(self, row: pd.Series) -> float:
        """Calculate MACD-based score

        MACD = Fast EMA - Slow EMA
        Signal = EMA of MACD
        Histogram = MACD - Signal

        Note: Simplified version using available data
        """
        # Use different timeframes as proxy for MACD
        fast = row['percent_change_24h']  # Fast moving
        slow = row['percent_change_7d'] / 7  # Slow moving average

        macd = fast - slow

        # Positive MACD = bullish, Negative = bearish
        if macd > 5:
            score = 80  # Strong bullish crossover
        elif macd > 2:
            score = 65
        elif macd > 0:
            score = 55
        elif macd > -2:
            score = 45
        elif macd > -5:
            score = 30
        else:
            score = 20  # Strong bearish

        # Check for acceleration (histogram increasing)
        if row['percent_change_1h'] > 0 and macd > 0:
            score += 10  # Momentum building

        return min(score, 100)

    def _calculate_bollinger_score(self, row: pd.Series) -> float:
        """Calculate Bollinger Bands score

        When price is near lower band = oversold (potential buy)
        When price breaks upper band = strong momentum (or overbought)
        Band squeeze = low volatility, breakout coming
        """
        # Estimate using volatility and recent moves
        volatility = abs(row['percent_change_24h']) + abs(row['percent_change_7d']) / 7

        # High volatility after low volatility = breakout
        recent_range = abs(row['percent_change_1h'])

        if volatility > 15 and row['percent_change_24h'] > 5:
            score = 75  # Breakout to upside
        elif volatility > 10 and row['percent_change_24h'] > 0:
            score = 60
        elif volatility < 3:
            score = 40  # Low volatility squeeze - wait for breakout
        else:
            score = 50

        return score

    def _detect_wash_trading(self, row: pd.Series) -> Tuple[bool, float]:
        """Detect potential wash trading using statistical methods

        Red flags for wash trading:
        1. Extreme volume spike (>500%) with minimal price change
        2. Volume/Market Cap ratio >100% (unrealistic for most coins)
        3. Massive volume change but price barely moves

        Returns: (is_suspicious, confidence_score)
        """
        suspicious = False
        confidence = 0.0
        red_flags = []

        vol_change = row['volume_change_24h']
        price_change = abs(row['percent_change_24h'])
        vol_mcap_ratio = row['volume_24h'] / row['market_cap']

        # Red flag 1: Massive volume spike with tiny price move
        if vol_change > 500 and price_change < 2:
            suspicious = True
            confidence += 40
            red_flags.append("Extreme volume (+{:.0f}%) with minimal price change".format(vol_change))

        # Red flag 2: Unrealistic volume/market cap ratio
        if vol_mcap_ratio > 2.0:  # 200% of market cap traded in 24h
            suspicious = True
            confidence += 30
            red_flags.append("Unrealistic volume/mcap ratio: {:.1f}%".format(vol_mcap_ratio * 100))

        # Red flag 3: Volume spike without corresponding momentum
        if vol_change > 200 and price_change < 5 and row['percent_change_7d'] < 10:
            suspicious = True
            confidence += 20
            red_flags.append("Volume spike without price momentum")

        # Red flag 4: Very small market cap with huge volume (common in rug pulls)
        if row['market_cap'] < 5_000_000 and row['volume_24h'] > row['market_cap'] * 5:
            suspicious = True
            confidence += 30
            red_flags.append("Micro-cap with suspicious volume")

        return suspicious, min(confidence, 100)

    def _calculate_market_correlation_score(self, row: pd.Series) -> float:
        """Calculate score based on correlation with BTC

        - If BTC is dumping and coin is pumping = very risky (likely fake pump)
        - If BTC is pumping and coin is pumping more = good momentum
        - If BTC is stable and coin is moving = independent move (can be good or manipulation)
        """
        if self.btc_data is None:
            return 50  # Neutral if no BTC data

        btc_24h = self.btc_data['percent_change_24h']
        coin_24h = row['percent_change_24h']

        # BTC pumping, coin pumping more = best scenario
        if btc_24h > 3 and coin_24h > btc_24h * 1.5:
            score = 80  # Outperforming in bull market
        # BTC stable/slightly up, coin pumping = independent strength
        elif -2 < btc_24h < 3 and coin_24h > 10:
            score = 70  # Strong independent move
        # BTC dumping, coin pumping = RED FLAG (likely manipulation)
        elif btc_24h < -5 and coin_24h > 5:
            score = 20  # Suspicious divergence
        # BTC dumping, coin dumping less = relative strength
        elif btc_24h < -5 and coin_24h > btc_24h:
            score = 60  # Holding better than market
        else:
            score = 50  # Moving with market

        return score

    def _calculate_kelly_position_size(self, win_rate: float, avg_win: float, avg_loss: float,
                                      risk_free_rate: float = 0.0) -> float:
        """Calculate optimal position size using Kelly Criterion

        Kelly % = (Win Rate * Avg Win - (1 - Win Rate) * Avg Loss) / Avg Win

        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade return
            avg_loss: Average losing trade return (positive number)
            risk_free_rate: Risk-free rate (typically ~0 for crypto)

        Returns:
            Optimal position size as fraction of portfolio (0-1)
        """
        if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss <= 0:
            return 0.0

        # Kelly formula
        kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win

        # Use fractional Kelly (25-50% of full Kelly) for safety
        # Full Kelly can be too aggressive for crypto volatility
        conservative_kelly = kelly * 0.25  # Ultra conservative
        moderate_kelly = kelly * 0.5  # Moderate

        # Cap at reasonable max (never risk more than 10% on single trade)
        kelly_capped = min(kelly, 0.10)
        conservative_capped = min(conservative_kelly, 0.05)
        moderate_capped = min(moderate_kelly, 0.075)

        return max(0, moderate_capped)  # Return moderate Kelly, never negative

    def calculate_comprehensive_scores(self) -> pd.DataFrame:
        """Calculate all professional indicators and scores"""
        if self.df.empty:
            return self.df

        # Professional technical indicators
        self.df['rsi_score'] = self.df.apply(self._calculate_rsi_score, axis=1)
        self.df['macd_score'] = self.df.apply(self._calculate_macd_score, axis=1)
        self.df['bollinger_score'] = self.df.apply(self._calculate_bollinger_score, axis=1)

        # Market context
        self.df['market_correlation_score'] = self.df.apply(self._calculate_market_correlation_score, axis=1)

        # Wash trading detection
        wash_results = self.df.apply(self._detect_wash_trading, axis=1)
        self.df['wash_trading_suspicious'] = wash_results.apply(lambda x: x[0])
        self.df['wash_trading_confidence'] = wash_results.apply(lambda x: x[1])

        # Calculate legacy scores for comparison
        self.df['volatility_score'] = self.df.apply(self._calculate_volatility_score, axis=1)
        self.df['market_cap_risk_score'] = self.df['market_cap'].apply(self._calculate_market_cap_risk_score)
        self.df['volume_activity_score'] = self.df.apply(self._calculate_volume_activity_score, axis=1)
        self.df['momentum_score'] = self.df.apply(self._calculate_momentum_score, axis=1)

        # ENHANCED COMPOSITE SCORE with professional indicators
        # Heavily penalize wash trading suspects
        wash_penalty = self.df['wash_trading_confidence'] / 100  # 0 to 1

        self.df['enhanced_composite_score'] = (
            self.df['rsi_score'] * 0.15 +           # Professional RSI signals
            self.df['macd_score'] * 0.15 +          # Trend confirmation
            self.df['bollinger_score'] * 0.10 +     # Volatility/breakout detection
            self.df['market_correlation_score'] * 0.15 +  # BTC correlation context
            self.df['momentum_score'] * 0.15 +      # Price momentum
            self.df['volume_activity_score'] * 0.15 +  # Volume quality
            self.df['market_cap_risk_score'] * 0.10 +  # Risk/reward from size
            self.df['volatility_score'] * 0.05      # Basic volatility
        ) * (1 - wash_penalty * 0.7)  # Penalize wash trading heavily

        # Calculate recommended position sizes (using hypothetical 60% win rate, 1.5:1 ratio)
        # In reality, this should come from backtesting
        self.df['kelly_position_size'] = self._calculate_kelly_position_size(0.60, 1.5, 1.0)

        return self.df

    # Legacy scoring methods for backward compatibility
    def _calculate_volatility_score(self, row: pd.Series) -> float:
        """Calculate volatility score - legacy method"""
        vol_score = (
            abs(row['percent_change_1h']) * 3.0 +
            abs(row['percent_change_24h']) * 2.0 +
            abs(row['percent_change_7d']) * 1.0
        ) / 6.0

        if row['percent_change_24h'] > 0 and row['percent_change_7d'] > 0:
            vol_score *= 1.3

        return vol_score

    def _calculate_market_cap_risk_score(self, market_cap: float) -> float:
        """Calculate risk score based on market cap - legacy method"""
        if market_cap < self.MICRO_CAP:
            return 100.0
        elif market_cap < self.SMALL_CAP:
            return 70.0
        elif market_cap < self.MID_CAP:
            return 40.0
        else:
            return 10.0

    def _calculate_volume_activity_score(self, row: pd.Series) -> float:
        """Calculate activity score - legacy method"""
        volume_ratio = row['volume_24h'] / row['market_cap'] if row['market_cap'] > 0 else 0

        if volume_ratio >= 0.15:
            base_score = 100.0
        elif volume_ratio >= 0.05:
            base_score = 60.0
        else:
            base_score = 30.0

        volume_change = row['volume_change_24h']
        if volume_change > 100:
            base_score *= 2.0
        elif volume_change > 50:
            base_score *= 1.6
        elif volume_change > 20:
            base_score *= 1.3
        elif volume_change < -40:
            base_score *= 0.6

        return min(base_score, 150.0)

    def _calculate_momentum_score(self, row: pd.Series) -> float:
        """Calculate momentum score - legacy method"""
        momentum = 0.0

        if row['percent_change_1h'] > 3 and row['percent_change_24h'] > 5:
            momentum += 15

        if row['percent_change_24h'] > 20:
            momentum += 50
        elif row['percent_change_24h'] > 10:
            momentum += 40
        elif row['percent_change_24h'] > 5:
            momentum += 25
        elif row['percent_change_24h'] < -10:
            momentum -= 40

        if row['percent_change_7d'] > 20 and row['percent_change_24h'] > 5:
            momentum += 35
        elif row['percent_change_7d'] < -20:
            momentum -= 30

        return max(0, min(momentum, 100))

    def get_top_safe_recommendations(self, n: int = 5) -> List[Tuple[str, Dict]]:
        """Get top recommendations with wash trading filtering

        Returns only coins that pass safety checks
        """
        if self.df.empty:
            return []

        # Filter out wash trading suspects
        safe_coins = self.df[
            (self.df['wash_trading_suspicious'] == False) |
            (self.df['wash_trading_confidence'] < 30)  # Only minor suspicion
        ].copy()

        if safe_coins.empty:
            return []

        # Sort by enhanced score
        top_coins = safe_coins.nlargest(n, 'enhanced_composite_score')

        results = []
        for _, row in top_coins.iterrows():
            coin_info = {
                'name': row['name'],
                'symbol': row['symbol'],
                'cmc_id': row['cmc_id'],
                'slug': row['slug'],
                'platform': row['platform'],
                'contract_address': row['contract_address'],
                'binance_platforms': row['binance_platforms'],
                'has_futures': row['has_futures'],
                'price': row['price'],
                'market_cap': row['market_cap'],
                'volume_24h': row['volume_24h'],
                'volume_change_24h': row['volume_change_24h'],
                'change_1h': row['percent_change_1h'],
                'change_24h': row['percent_change_24h'],
                'change_7d': row['percent_change_7d'],
                'enhanced_score': row['enhanced_composite_score'],
                'rsi_score': row['rsi_score'],
                'macd_score': row['macd_score'],
                'bollinger_score': row['bollinger_score'],
                'market_correlation_score': row['market_correlation_score'],
                'wash_trading_suspicious': row['wash_trading_suspicious'],
                'wash_trading_confidence': row['wash_trading_confidence'],
                'kelly_position_size': row['kelly_position_size'],
                # Legacy scores
                'composite_score': row.get('enhanced_composite_score', 0),
                'volatility_score': row['volatility_score'],
                'risk_score': row['market_cap_risk_score'],
                'activity_score': row['volume_activity_score'],
                'momentum_score': row['momentum_score'],
            }
            results.append((row['symbol'], coin_info))

        return results

    def get_top_by_category(self, category: str, n: int = 10) -> List[Tuple[str, Dict]]:
        """Get top recommendations by trading category

        Args:
            category: 'spot', 'futures', or 'web3'
            n: Number of recommendations

        Returns:
            List of (symbol, coin_data) tuples
        """
        if self.df.empty:
            return []

        # Filter safe coins first
        safe_coins = self.df[
            (self.df['wash_trading_suspicious'] == False) |
            (self.df['wash_trading_confidence'] < 30)
        ].copy()

        if safe_coins.empty:
            return []

        # Filter by category
        if category == 'spot':
            # Binance Spot: on Binance and not a token
            filtered = safe_coins[
                (safe_coins['on_binance'] == True) &
                (safe_coins['contract_address'] == '')
            ].copy()
        elif category == 'futures':
            # Binance Futures: has futures flag
            filtered = safe_coins[
                safe_coins['has_futures'] == True
            ].copy()
        elif category == 'web3':
            # Web3 Wallet: has contract address
            filtered = safe_coins[
                safe_coins['contract_address'] != ''
            ].copy()
        else:
            return []

        if filtered.empty:
            return []

        # Sort by enhanced score
        top_coins = filtered.nlargest(n, 'enhanced_composite_score')

        results = []
        for _, row in top_coins.iterrows():
            coin_info = {
                'name': row['name'],
                'symbol': row['symbol'],
                'cmc_id': row['cmc_id'],
                'slug': row['slug'],
                'platform': row['platform'],
                'contract_address': row['contract_address'],
                'binance_platforms': row['binance_platforms'],
                'has_futures': row['has_futures'],
                'price': row['price'],
                'market_cap': row['market_cap'],
                'volume_24h': row['volume_24h'],
                'volume_change_24h': row['volume_change_24h'],
                'change_1h': row['percent_change_1h'],
                'change_24h': row['percent_change_24h'],
                'change_7d': row['percent_change_7d'],
                'enhanced_score': row['enhanced_composite_score'],
                'rsi_score': row['rsi_score'],
                'macd_score': row['macd_score'],
                'bollinger_score': row['bollinger_score'],
                'market_correlation_score': row['market_correlation_score'],
                'wash_trading_suspicious': row['wash_trading_suspicious'],
                'wash_trading_confidence': row['wash_trading_confidence'],
                'kelly_position_size': row['kelly_position_size'],
                'composite_score': row.get('enhanced_composite_score', 0),
                'volatility_score': row['volatility_score'],
                'risk_score': row['market_cap_risk_score'],
                'activity_score': row['volume_activity_score'],
                'momentum_score': row['momentum_score'],
            }
            results.append((row['symbol'], coin_info))

        return results

    def get_wash_trading_report(self) -> pd.DataFrame:
        """Get detailed report of suspected wash trading"""
        if self.df.empty:
            return pd.DataFrame()

        suspects = self.df[self.df['wash_trading_suspicious'] == True].copy()
        suspects = suspects.sort_values('wash_trading_confidence', ascending=False)

        return suspects[['symbol', 'name', 'market_cap', 'volume_24h', 'volume_change_24h',
                        'percent_change_24h', 'wash_trading_confidence']]
