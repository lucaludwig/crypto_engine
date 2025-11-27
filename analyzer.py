"""Cryptocurrency Analysis and Scoring Engine"""
from typing import List, Dict, Tuple
import pandas as pd


class CryptoAnalyzer:
    """Analyzes cryptocurrencies for high-risk, high-return potential"""

    # Market cap thresholds for risk categories (in USD)
    MICRO_CAP = 50_000_000  # < 50M = very high risk
    SMALL_CAP = 250_000_000  # < 250M = high risk
    MID_CAP = 2_000_000_000  # < 2B = medium risk

    # Volume/Market Cap ratio thresholds
    HIGH_VOLUME_RATIO = 0.15  # 15%+ volume/mcap = high activity
    MEDIUM_VOLUME_RATIO = 0.05  # 5%+ volume/mcap = medium activity

    def __init__(self, coins_data: List[Dict]):
        """Initialize analyzer with coin data from CoinMarketCap

        Args:
            coins_data: List of cryptocurrency data from CMC API
        """
        self.coins_data = coins_data
        self.df = self._prepare_dataframe()

    def _prepare_dataframe(self) -> pd.DataFrame:
        """Convert coin data to pandas DataFrame with relevant metrics"""
        records = []
        for coin in self.coins_data:
            quote = coin.get('quote', {}).get('USD', {})

            # Skip stablecoins and coins without sufficient data
            if not quote or coin.get('name', '').lower() in ['tether', 'usd coin', 'binance usd', 'dai']:
                continue

            market_cap = quote.get('market_cap', 0)
            volume_24h = quote.get('volume_24h', 0)

            # Skip coins with no volume or very low market cap
            if volume_24h == 0 or market_cap < 100_000:
                continue

            # Get platform info for token identification
            platform = coin.get('platform', {})
            contract_address = platform.get('token_address', '') if platform else ''
            platform_name = platform.get('name', '') if platform else ''

            # Check exchange listings via tags
            tags = coin.get('tags', [])
            on_binance = 'binance-listing' in tags
            on_coinbase = 'coinbase-ventures-portfolio' in tags or 'coinbase-listing' in tags

            records.append({
                'symbol': coin.get('symbol'),
                'name': coin.get('name'),
                'cmc_id': coin.get('id'),
                'slug': coin.get('slug'),
                'platform': platform_name,
                'contract_address': contract_address,
                'on_binance': on_binance,
                'on_coinbase': on_coinbase,
                'price': quote.get('price', 0),
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'percent_change_1h': quote.get('percent_change_1h', 0),
                'percent_change_24h': quote.get('percent_change_24h', 0),
                'percent_change_7d': quote.get('percent_change_7d', 0),
                'volume_change_24h': quote.get('volume_change_24h', 0),
                'market_cap_dominance': quote.get('market_cap_dominance', 0),
            })

        return pd.DataFrame(records)

    def _calculate_volatility_score(self, row: pd.Series) -> float:
        """Calculate volatility score (higher = more volatile = higher potential)

        Considers recent price changes and their magnitude
        """
        # Weight recent changes more heavily
        vol_score = (
            abs(row['percent_change_1h']) * 3.0 +  # Most recent, highest weight
            abs(row['percent_change_24h']) * 2.0 +
            abs(row['percent_change_7d']) * 1.0
        ) / 6.0

        # Bonus for positive momentum
        if row['percent_change_24h'] > 0 and row['percent_change_7d'] > 0:
            vol_score *= 1.3

        return vol_score

    def _calculate_market_cap_risk_score(self, market_cap: float) -> float:
        """Calculate risk score based on market cap (lower cap = higher risk/reward)"""
        if market_cap < self.MICRO_CAP:
            return 100.0  # Highest risk/reward
        elif market_cap < self.SMALL_CAP:
            return 70.0
        elif market_cap < self.MID_CAP:
            return 40.0
        else:
            return 10.0  # Large caps = lower risk/reward

    def _calculate_unusual_volume_score(self, row: pd.Series) -> float:
        """Detect unusual volume spikes - PRO TRADER VERSION

        Volume spikes MUST be accompanied by price action!
        Pro traders: "Volume confirms price" - volume alone means nothing
        """
        score = 0.0
        volume_change = row['volume_change_24h']
        price_change = row['percent_change_24h']

        # RULE: Volume spike WITH price increase = bullish confirmation
        if volume_change > 200 and price_change > 10:
            score += 100  # Strong buy signal
        elif volume_change > 200 and price_change > 0:
            score += 60  # Volume spike but weak price = caution
        elif volume_change > 200 and price_change < 0:
            score += 20  # High volume + dump = distribution (very risky!)

        # Moderate volume increase with strong price
        elif volume_change > 100 and price_change > 10:
            score += 80
        elif volume_change > 50 and price_change > 10:
            score += 60
        elif volume_change > 50 and price_change > 5:
            score += 50

        # Steady volume with good price action (sustainable)
        elif volume_change > 10 and price_change > 10:
            score += 40

        # WARNING: Declining volume = trend exhaustion
        if volume_change < -30 and price_change > 0:
            score -= 30  # Price up but volume dying = trap!
        elif volume_change < -50:
            score -= 50  # Dying interest

        return max(0, min(score, 100))

    def _calculate_volume_activity_score(self, row: pd.Series) -> float:
        """Calculate activity score based on volume metrics - IMPROVED VERSION"""
        volume_ratio = row['volume_24h'] / row['market_cap'] if row['market_cap'] > 0 else 0

        # Base score from volume/mcap ratio
        if volume_ratio >= self.HIGH_VOLUME_RATIO:
            base_score = 100.0
        elif volume_ratio >= self.MEDIUM_VOLUME_RATIO:
            base_score = 60.0
        else:
            base_score = 30.0

        # Strong boost for volume increase (more important than I had before)
        volume_change = row['volume_change_24h']
        if volume_change > 100:
            base_score *= 2.0  # Doubled activity = major interest
        elif volume_change > 50:
            base_score *= 1.6
        elif volume_change > 20:
            base_score *= 1.3
        elif volume_change > 10:
            base_score *= 1.15
        elif volume_change < -40:
            base_score *= 0.6  # Dying interest

        return min(base_score, 150.0)  # Allow going over 100 for exceptional cases

    def _calculate_rsi_like_score(self, row: pd.Series) -> float:
        """Calculate RSI-like oversold/overbought score

        RSI logic: We want oversold coins that are starting to bounce back
        """
        score = 0.0

        # Check if coin was recently oversold and is bouncing
        # Strong negative 7d but positive 24h = potential reversal
        if row['percent_change_7d'] < -15 and row['percent_change_24h'] > 5:
            score += 50  # Strong reversal signal
        elif row['percent_change_7d'] < -10 and row['percent_change_24h'] > 0:
            score += 30

        # Moderate pullback with recent strength
        if row['percent_change_7d'] < 0 and row['percent_change_24h'] > 10:
            score += 20

        # Avoid extremely overbought (too late to enter)
        if row['percent_change_24h'] > 50 or row['percent_change_7d'] > 100:
            score -= 30  # Likely too late, correction coming

        return max(0, min(score, 100))

    def _calculate_trend_strength_score(self, row: pd.Series) -> float:
        """Calculate trend strength - PRO TRADER VERSION

        Focus: Multi-timeframe confirmation (hours + days align)
        Pro traders look for trends that hold across ALL timeframes
        """
        score = 0.0

        # GOLD STANDARD: All timeframes positive (most reliable setup)
        if row['percent_change_24h'] > 0 and row['percent_change_7d'] > 0:
            score += 50  # Base score for aligned trend

            # Higher highs = acceleration (very bullish)
            daily_rate = row['percent_change_24h']
            weekly_rate = row['percent_change_7d'] / 7
            if daily_rate > weekly_rate * 1.5:
                score += 30  # Accelerating upward
            elif daily_rate > weekly_rate:
                score += 20  # Steady acceleration

        # WARNING: Divergence between timeframes (risky!)
        elif row['percent_change_24h'] > 10 and row['percent_change_7d'] < 0:
            score += 10  # Possible reversal but unconfirmed (low score)

        # AVOID: Downtrend on both timeframes
        elif row['percent_change_24h'] < 0 and row['percent_change_7d'] < 0:
            score = 0  # Clear downtrend

        # Strength of 24h move
        if row['percent_change_24h'] > 15:
            score += 15
        elif row['percent_change_24h'] > 8:
            score += 10

        return min(score, 100)

    def _calculate_momentum_score(self, row: pd.Series) -> float:
        """Calculate momentum score - PRO TRADER VERSION

        Focus: Sustained trends over hours/days, not minute-by-minute noise
        """
        momentum = 0.0

        # 1h change: Only for confirmation, LOW weight (reduce noise)
        if row['percent_change_1h'] > 3 and row['percent_change_24h'] > 5:
            momentum += 15  # Reduced from 50! Only counts if 24h confirms
        elif row['percent_change_1h'] < -3 and row['percent_change_24h'] > 10:
            # Slight dip but strong 24h = buying opportunity
            momentum += 10

        # 24h trend: PRIMARY SIGNAL (most stable timeframe for day trading)
        if row['percent_change_24h'] > 20:
            momentum += 50
        elif row['percent_change_24h'] > 10:
            momentum += 40
        elif row['percent_change_24h'] > 5:
            momentum += 25
        elif row['percent_change_24h'] > 2:
            momentum += 10
        elif row['percent_change_24h'] < -10:
            momentum -= 40  # Strong downtrend = avoid

        # 7d trend: Context and confirmation (filters out pumps that will dump)
        if row['percent_change_7d'] > 20 and row['percent_change_24h'] > 5:
            momentum += 35  # Sustained uptrend = high confidence
        elif row['percent_change_7d'] > 0 and row['percent_change_24h'] > 10:
            momentum += 20  # Building momentum
        elif row['percent_change_7d'] < -20:
            momentum -= 30  # Long-term downtrend = risky

        return max(0, min(momentum, 100))

    def calculate_scores(self) -> pd.DataFrame:
        """Calculate comprehensive risk/reward scores for all coins - IMPROVED ALGORITHM"""
        if self.df.empty:
            return self.df

        # Calculate individual score components
        self.df['volatility_score'] = self.df.apply(self._calculate_volatility_score, axis=1)
        self.df['market_cap_risk_score'] = self.df['market_cap'].apply(self._calculate_market_cap_risk_score)
        self.df['volume_activity_score'] = self.df.apply(self._calculate_volume_activity_score, axis=1)
        self.df['unusual_volume_score'] = self.df.apply(self._calculate_unusual_volume_score, axis=1)
        self.df['momentum_score'] = self.df.apply(self._calculate_momentum_score, axis=1)
        self.df['trend_strength_score'] = self.df.apply(self._calculate_trend_strength_score, axis=1)
        self.df['rsi_like_score'] = self.df.apply(self._calculate_rsi_like_score, axis=1)

        # Composite score (IMPROVED WEIGHTING based on pro trader research)
        # Key findings from research:
        # - Volume spikes are THE most important signal for pumps
        # - Momentum + Trend Strength together are critical
        # - Market Cap risk still matters for high-risk coins
        # - Volatility is less important than actual price movement
        self.df['composite_score'] = (
            self.df['unusual_volume_score'] * 0.25 +      # NEW: Volume spikes = whale activity
            self.df['momentum_score'] * 0.20 +            # Price momentum (improved)
            self.df['trend_strength_score'] * 0.15 +      # NEW: Consistent trend
            self.df['volume_activity_score'] * 0.15 +     # Base volume activity
            self.df['market_cap_risk_score'] * 0.15 +     # Reduced from 30% - still important
            self.df['volatility_score'] * 0.05 +          # Reduced from 25% - less predictive
            self.df['rsi_like_score'] * 0.05              # NEW: Reversal signals
        )

        return self.df

    def get_top_high_risk_coins(self, n: int = 5) -> List[Tuple[str, Dict]]:
        """Get top N coins with highest risk/reward potential

        Args:
            n: Number of top coins to return

        Returns:
            List of tuples (symbol, coin_data_dict)
        """
        if self.df.empty:
            return []

        # Sort by composite score
        top_coins = self.df.nlargest(n, 'composite_score')

        results = []
        for _, row in top_coins.iterrows():
            coin_info = {
                'name': row['name'],
                'symbol': row['symbol'],
                'cmc_id': row['cmc_id'],
                'slug': row['slug'],
                'platform': row['platform'],
                'contract_address': row['contract_address'],
                'on_binance': row['on_binance'],
                'on_coinbase': row['on_coinbase'],
                'price': row['price'],
                'market_cap': row['market_cap'],
                'volume_24h': row['volume_24h'],
                'volume_change_24h': row['volume_change_24h'],
                'change_1h': row['percent_change_1h'],
                'change_24h': row['percent_change_24h'],
                'change_7d': row['percent_change_7d'],
                'composite_score': row['composite_score'],
                'volatility_score': row['volatility_score'],
                'risk_score': row['market_cap_risk_score'],
                'activity_score': row['volume_activity_score'],
                'unusual_volume_score': row['unusual_volume_score'],
                'momentum_score': row['momentum_score'],
                'trend_strength_score': row['trend_strength_score'],
                'rsi_like_score': row['rsi_like_score'],
            }
            results.append((row['symbol'], coin_info))

        return results

    def get_top_binance_spot_coins(self, n: int = 5) -> List[Tuple[str, Dict]]:
        """Get top N coins for BINANCE SPOT TRADING (direct trading on exchange)

        Args:
            n: Number of top coins to return

        Returns:
            List of tuples (symbol, coin_data_dict)
        """
        if self.df.empty:
            return []

        # Filter: Must be on Binance (for direct spot trading)
        binance_coins = self.df[self.df['on_binance'] == True].copy()

        if binance_coins.empty:
            return []

        # Sort by composite score
        top_coins = binance_coins.nlargest(n, 'composite_score')

        results = []
        for _, row in top_coins.iterrows():
            coin_info = {
                'name': row['name'],
                'symbol': row['symbol'],
                'cmc_id': row['cmc_id'],
                'slug': row['slug'],
                'platform': row['platform'],
                'contract_address': row['contract_address'],
                'on_binance': row['on_binance'],
                'on_coinbase': row['on_coinbase'],
                'price': row['price'],
                'market_cap': row['market_cap'],
                'volume_24h': row['volume_24h'],
                'volume_change_24h': row['volume_change_24h'],
                'change_1h': row['percent_change_1h'],
                'change_24h': row['percent_change_24h'],
                'change_7d': row['percent_change_7d'],
                'composite_score': row['composite_score'],
                'volatility_score': row['volatility_score'],
                'risk_score': row['market_cap_risk_score'],
                'activity_score': row['volume_activity_score'],
                'unusual_volume_score': row['unusual_volume_score'],
                'momentum_score': row['momentum_score'],
                'trend_strength_score': row['trend_strength_score'],
                'rsi_like_score': row['rsi_like_score'],
            }
            results.append((row['symbol'], coin_info))

        return results

    def get_top_binance_wallet_coins(self, n: int = 5) -> List[Tuple[str, Dict]]:
        """Get top N tokens for BINANCE WEB3 WALLET (tokens NOT on Binance exchange)

        These are tokens you need to trade via Binance Wallet, not on Binance exchange

        Args:
            n: Number of top coins to return

        Returns:
            List of tuples (symbol, coin_data_dict)
        """
        if self.df.empty:
            return []

        # Filter: Tokens (has contract) that are NOT on Binance exchange
        # These need Binance Wallet or other DEX
        wallet_coins = self.df[
            (self.df['contract_address'] != '') &
            (self.df['on_binance'] == False)
        ].copy()

        if wallet_coins.empty:
            return []

        # Sort by composite score
        top_coins = wallet_coins.nlargest(n, 'composite_score')

        results = []
        for _, row in top_coins.iterrows():
            coin_info = {
                'name': row['name'],
                'symbol': row['symbol'],
                'cmc_id': row['cmc_id'],
                'slug': row['slug'],
                'platform': row['platform'],
                'contract_address': row['contract_address'],
                'on_binance': row['on_binance'],
                'on_coinbase': row['on_coinbase'],
                'price': row['price'],
                'market_cap': row['market_cap'],
                'volume_24h': row['volume_24h'],
                'volume_change_24h': row['volume_change_24h'],
                'change_1h': row['percent_change_1h'],
                'change_24h': row['percent_change_24h'],
                'change_7d': row['percent_change_7d'],
                'composite_score': row['composite_score'],
                'volatility_score': row['volatility_score'],
                'risk_score': row['market_cap_risk_score'],
                'activity_score': row['volume_activity_score'],
                'unusual_volume_score': row['unusual_volume_score'],
                'momentum_score': row['momentum_score'],
                'trend_strength_score': row['trend_strength_score'],
                'rsi_like_score': row['rsi_like_score'],
            }
            results.append((row['symbol'], coin_info))

        return results
