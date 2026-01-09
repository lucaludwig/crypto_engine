"""Backtest Module - Walk-Forward Validation

MANDATORY BEFORE LIVE TRADING:
- In-Sample (IS): 70% of data for validation
- Out-of-Sample (OOS): 30% of data for blind test
- Realistic fees & slippage
- NO PARAMETER TWEAKING in OOS
- Target metrics:
  - Expectancy per Trade > 0
  - Profit Factor > 1.8
  - Max Drawdown < 25%
  - Sharpe Ratio > 1.5
  - OOS drop < 30% vs IS
"""

__all__ = [
    'EventEngine',
    'FeeSlippageModel',
    'MetricsCalculator',
    'WalkForwardTest',
    'DataLoader'
]
