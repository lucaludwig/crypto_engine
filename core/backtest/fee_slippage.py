"""Fee & Slippage Model - Realistic Trade Costs

CRITICAL: Backtests MUST include realistic costs!

Binance Spot Trading Fees (Tier 0):
- Maker: 0.1%
- Taker: 0.1%
- We use market orders (taker) for entries and exits

Slippage:
- Market orders suffer slippage on illiquid coins
- Conservative estimate: 0.05% - 0.1% per trade
- We use 0.075% (middle estimate)

Total Cost Per Trade (Round-Trip):
- Entry: 0.1% (fee) + 0.075% (slippage) = 0.175%
- Exit:  0.1% (fee) + 0.075% (slippage) = 0.175%
- Total: 0.35% per round-trip trade

This is NON-NEGOTIABLE for realistic backtesting.
"""
from typing import Dict


class FeeSlippageModel:
    """Models realistic trading costs for backtesting

    Binance Spot Tier 0 Fees + Conservative Slippage
    """

    # BINANCE SPOT TIER 0 (VIP 0)
    MAKER_FEE_PCT = 0.10  # 0.1% maker fee
    TAKER_FEE_PCT = 0.10  # 0.1% taker fee (we use market orders)

    # SLIPPAGE (Conservative)
    SLIPPAGE_PCT = 0.075  # 0.075% slippage per trade

    # TOTAL COST
    ENTRY_COST_PCT = TAKER_FEE_PCT + SLIPPAGE_PCT  # 0.175%
    EXIT_COST_PCT = TAKER_FEE_PCT + SLIPPAGE_PCT   # 0.175%
    ROUND_TRIP_COST_PCT = ENTRY_COST_PCT + EXIT_COST_PCT  # 0.35%

    def __init__(self):
        """Initialize fee model with Binance Tier 0 rates"""
        pass

    def calculate_entry_cost(self, entry_price: float, quantity: float) -> Dict:
        """Calculate entry cost (fee + slippage)

        Args:
            entry_price: Intended entry price
            quantity: Position size in coins

        Returns:
            Dict with cost breakdown
        """
        position_value = entry_price * quantity

        # Slippage (pay slightly more than expected)
        slippage_amount = position_value * (self.SLIPPAGE_PCT / 100)
        actual_entry_price = entry_price * (1 + self.SLIPPAGE_PCT / 100)

        # Fee (on actual filled value)
        actual_position_value = actual_entry_price * quantity
        fee_amount = actual_position_value * (self.TAKER_FEE_PCT / 100)

        total_cost = slippage_amount + fee_amount
        total_cost_pct = (total_cost / position_value) * 100

        return {
            'intended_price': entry_price,
            'actual_price': actual_entry_price,
            'slippage_amount': slippage_amount,
            'fee_amount': fee_amount,
            'total_cost': total_cost,
            'total_cost_pct': total_cost_pct,
            'position_value': actual_position_value
        }

    def calculate_exit_cost(self, exit_price: float, quantity: float) -> Dict:
        """Calculate exit cost (fee + slippage)

        Args:
            exit_price: Intended exit price
            quantity: Position size in coins

        Returns:
            Dict with cost breakdown
        """
        position_value = exit_price * quantity

        # Slippage (receive slightly less than expected)
        slippage_amount = position_value * (self.SLIPPAGE_PCT / 100)
        actual_exit_price = exit_price * (1 - self.SLIPPAGE_PCT / 100)

        # Fee (on actual filled value)
        actual_position_value = actual_exit_price * quantity
        fee_amount = actual_position_value * (self.TAKER_FEE_PCT / 100)

        total_cost = slippage_amount + fee_amount
        total_cost_pct = (total_cost / position_value) * 100

        return {
            'intended_price': exit_price,
            'actual_price': actual_exit_price,
            'slippage_amount': slippage_amount,
            'fee_amount': fee_amount,
            'total_cost': total_cost,
            'total_cost_pct': total_cost_pct,
            'position_value': actual_position_value
        }

    def calculate_round_trip_cost(self, entry_price: float, exit_price: float, quantity: float) -> Dict:
        """Calculate total round-trip cost

        Args:
            entry_price: Entry price
            exit_price: Exit price
            quantity: Position size

        Returns:
            Complete cost breakdown
        """
        entry_cost = self.calculate_entry_cost(entry_price, quantity)
        exit_cost = self.calculate_exit_cost(exit_price, quantity)

        # Calculate gross P&L (before costs)
        gross_pnl = (exit_price - entry_price) * quantity
        gross_pnl_pct = ((exit_price - entry_price) / entry_price) * 100

        # Calculate net P&L (after costs)
        total_costs = entry_cost['total_cost'] + exit_cost['total_cost']
        net_pnl = gross_pnl - total_costs
        net_pnl_pct = (net_pnl / (entry_price * quantity)) * 100

        # Cost impact
        cost_impact_pct = ((gross_pnl - net_pnl) / abs(gross_pnl)) * 100 if gross_pnl != 0 else 0

        return {
            'entry': entry_cost,
            'exit': exit_cost,
            'gross_pnl': gross_pnl,
            'gross_pnl_pct': gross_pnl_pct,
            'net_pnl': net_pnl,
            'net_pnl_pct': net_pnl_pct,
            'total_costs': total_costs,
            'cost_impact_pct': cost_impact_pct,
            'effective_entry': entry_cost['actual_price'],
            'effective_exit': exit_cost['actual_price']
        }

    def get_cost_summary(self) -> Dict:
        """Get summary of fee model

        Returns:
            Fee model configuration
        """
        return {
            'maker_fee_pct': self.MAKER_FEE_PCT,
            'taker_fee_pct': self.TAKER_FEE_PCT,
            'slippage_pct': self.SLIPPAGE_PCT,
            'entry_cost_pct': self.ENTRY_COST_PCT,
            'exit_cost_pct': self.EXIT_COST_PCT,
            'round_trip_cost_pct': self.ROUND_TRIP_COST_PCT,
            'description': 'Binance Spot Tier 0 + 0.075% Slippage'
        }

    def minimum_profitable_move(self) -> float:
        """Calculate minimum price move needed to break even

        Returns:
            Minimum profit % needed to cover costs
        """
        return self.ROUND_TRIP_COST_PCT
