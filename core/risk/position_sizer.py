"""Position Sizer - Fixed Risk Per Trade

GOLDEN NUMBERS (Hard-Coded):
- Risk Per Trade: 1.25% of account
- Max Total Exposure: 60% of account
- Max Slippage Tolerance: 0.3%

Position Size = (Account × Risk%) / Stop Distance

❌ NO KELLY CRITERION
❌ NO DYNAMIC SIZING
✅ FIXED RISK ONLY
"""
from typing import Dict, Optional


class PositionSizer:
    """Calculates position sizes based on fixed risk

    Formula:
    Position Size = (Account Balance × Risk%) / Stop Distance

    Where:
    - Risk% = 1.25% (hard-coded)
    - Stop Distance = Entry Price - Stop Loss Price
    """

    # AGGRESSIVE GROWTH MODE - Survivable but faster
    RISK_PER_TRADE_PCT = 3.0  # 3% per trade (was 1.25%)
    MAX_TOTAL_EXPOSURE_PCT = 60.0  # Max 60% of account in positions
    MAX_SLIPPAGE_PCT = 0.3  # 0.3% max slippage tolerance
    MIN_POSITION_SIZE_USDT = 11.0  # Binance minimum order value

    def __init__(self):
        """Initialize position sizer with hard-coded parameters"""
        pass

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        current_exposure_pct: float = 0.0
    ) -> Dict:
        """Calculate position size based on fixed risk

        Args:
            account_balance: Total account balance in USDT
            entry_price: Planned entry price
            stop_loss_price: Planned stop loss price
            current_exposure_pct: Current portfolio exposure %

        Returns:
            Dict with 'position_size_usdt', 'position_size_coins', 'risk_amount', 'valid'
        """
        result = {
            'position_size_usdt': 0.0,
            'position_size_coins': 0.0,
            'risk_amount_usdt': 0.0,
            'valid': False,
            'reason': ''
        }

        # CRITICAL FIX: Check for zero balance to prevent division by zero
        if account_balance <= 0:
            result['reason'] = "Account balance is zero or negative"
            return result

        # Check if we're at max exposure
        if current_exposure_pct >= self.MAX_TOTAL_EXPOSURE_PCT:
            result['reason'] = f"Max exposure reached ({current_exposure_pct:.1f}% >= {self.MAX_TOTAL_EXPOSURE_PCT}%)"
            return result

        # Calculate risk amount
        risk_amount = account_balance * (self.RISK_PER_TRADE_PCT / 100)

        # Calculate stop distance
        if entry_price <= 0 or stop_loss_price <= 0:
            result['reason'] = "Invalid entry or stop loss price"
            return result

        stop_distance = abs(entry_price - stop_loss_price)
        if stop_distance == 0:
            result['reason'] = "Stop loss too close to entry"
            return result

        stop_distance_pct = (stop_distance / entry_price) * 100

        # Calculate position size in USDT
        # Position Size = Risk Amount / Stop Distance %
        position_size_usdt = (risk_amount / stop_distance_pct) * 100

        # Check if this would exceed max exposure
        new_exposure_pct = current_exposure_pct + (position_size_usdt / account_balance * 100)
        if new_exposure_pct > self.MAX_TOTAL_EXPOSURE_PCT:
            # Scale down position to fit within max exposure
            available_exposure_pct = self.MAX_TOTAL_EXPOSURE_PCT - current_exposure_pct
            position_size_usdt = (available_exposure_pct / 100) * account_balance
            result['reason'] = f"Position scaled down to fit max exposure ({self.MAX_TOTAL_EXPOSURE_PCT}%)"

        # Calculate position size in coins
        position_size_coins = position_size_usdt / entry_price

        # CRITICAL FIX: Check minimum position size (Binance requires $11+)
        if position_size_usdt < self.MIN_POSITION_SIZE_USDT:
            result['reason'] = f"Position size ${position_size_usdt:.2f} below Binance minimum ${self.MIN_POSITION_SIZE_USDT}"
            result['position_size_usdt'] = position_size_usdt  # Still set for debugging
            return result

        result['position_size_usdt'] = position_size_usdt
        result['position_size_coins'] = position_size_coins
        result['risk_amount_usdt'] = risk_amount
        result['stop_distance_pct'] = stop_distance_pct
        result['valid'] = position_size_usdt >= self.MIN_POSITION_SIZE_USDT

        if result['valid'] and not result['reason']:
            result['reason'] = 'OK'

        return result

    def validate_slippage(self, expected_price: float, actual_price: float) -> bool:
        """Check if slippage is within tolerance

        Args:
            expected_price: Expected entry price
            actual_price: Actual filled price

        Returns:
            True if slippage is acceptable
        """
        if expected_price == 0:
            return False

        slippage_pct = abs((actual_price - expected_price) / expected_price) * 100

        return slippage_pct <= self.MAX_SLIPPAGE_PCT

    def calculate_max_positions(self, account_balance: float, avg_position_size_usdt: float) -> int:
        """Calculate maximum number of positions based on exposure limit

        Args:
            account_balance: Total account balance
            avg_position_size_usdt: Average position size in USDT

        Returns:
            Max number of simultaneous positions
        """
        if avg_position_size_usdt == 0:
            return 0

        max_exposure_usdt = account_balance * (self.MAX_TOTAL_EXPOSURE_PCT / 100)
        max_positions = int(max_exposure_usdt / avg_position_size_usdt)

        return max(1, max_positions)

    def get_risk_metrics(self, account_balance: float, position_size_usdt: float, stop_distance_pct: float) -> Dict:
        """Get risk metrics for a position

        Args:
            account_balance: Account balance
            position_size_usdt: Position size in USDT
            stop_distance_pct: Stop loss distance as %

        Returns:
            Dict with risk metrics
        """
        risk_amount = position_size_usdt * (stop_distance_pct / 100)
        risk_pct = (risk_amount / account_balance) * 100
        exposure_pct = (position_size_usdt / account_balance) * 100

        return {
            'risk_amount_usdt': risk_amount,
            'risk_pct': risk_pct,
            'exposure_pct': exposure_pct,
            'position_size_usdt': position_size_usdt,
            'stop_distance_pct': stop_distance_pct,
            'target_risk_pct': self.RISK_PER_TRADE_PCT
        }
