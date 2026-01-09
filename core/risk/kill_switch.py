"""Kill Switch - Hard Stop Mechanisms

GOLDEN NUMBERS (Hard-Coded):
- Daily Loss Limit: -5% → Trading OFF
- Drawdown Limit: 20% → Position size halved
- Drawdown Kill Switch: 40% → Trading OFF (permanent)
- Consecutive Failures: 2 → Coin blacklisted for 7 days

These are NON-NEGOTIABLE safety mechanisms.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
import os


class KillSwitch:
    """Manages hard stop mechanisms and safety limits

    Responsibilities:
    1. Track daily P&L and enforce -5% limit
    2. Track drawdown and enforce 20% / 40% limits
    3. Manage coin blacklist (2 failures → 7 day ban)
    """

    # GOLDEN NUMBERS - DO NOT MODIFY
    DAILY_LOSS_LIMIT_PCT = -5.0  # -5% daily loss → stop trading
    DRAWDOWN_REDUCE_PCT = 20.0  # 20% DD → reduce position size
    DRAWDOWN_KILL_PCT = 40.0  # 40% DD → stop all trading
    CONSECUTIVE_FAILS_LIMIT = 2  # 2 failures → blacklist
    BLACKLIST_DAYS = 7  # Blacklist duration

    def __init__(self, state_file: str = "kill_switch_state.json"):
        """Initialize kill switch

        Args:
            state_file: Path to state persistence file
        """
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError) as e:
                print(f"Warning: Could not load kill switch state: {e}")

        # Default state
        return {
            'peak_balance': 0.0,
            'daily_start_balance': 0.0,
            'daily_start_date': None,
            'blacklist': {},  # {symbol: ban_until_timestamp}
            'coin_failures': {},  # {symbol: consecutive_failures}
            'trading_enabled': True,
            'position_size_multiplier': 1.0
        }

    def _save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save kill switch state: {e}")

    def update_peak_balance(self, current_balance: float):
        """Update peak balance for drawdown calculation

        Args:
            current_balance: Current account balance
        """
        if current_balance > self.state['peak_balance']:
            self.state['peak_balance'] = current_balance
            self._save_state()

    def get_current_drawdown_pct(self, current_balance: float) -> float:
        """Calculate current drawdown from peak

        Args:
            current_balance: Current account balance

        Returns:
            Drawdown percentage (positive number)
        """
        if self.state['peak_balance'] == 0:
            return 0.0

        drawdown = ((self.state['peak_balance'] - current_balance) / self.state['peak_balance']) * 100
        return max(0, drawdown)

    def check_drawdown_limits(self, current_balance: float) -> Dict:
        """Check if drawdown limits are exceeded

        Args:
            current_balance: Current account balance

        Returns:
            Dict with 'trading_enabled', 'position_multiplier', 'drawdown_pct', 'reason'
        """
        self.update_peak_balance(current_balance)
        drawdown_pct = self.get_current_drawdown_pct(current_balance)

        result = {
            'trading_enabled': True,
            'position_multiplier': 1.0,
            'drawdown_pct': drawdown_pct,
            'reason': 'OK'
        }

        # Check 40% kill switch
        if drawdown_pct >= self.DRAWDOWN_KILL_PCT:
            result['trading_enabled'] = False
            result['position_multiplier'] = 0.0
            result['reason'] = f'KILL SWITCH: {drawdown_pct:.1f}% drawdown >= {self.DRAWDOWN_KILL_PCT}%'
            self.state['trading_enabled'] = False
            self.state['position_size_multiplier'] = 0.0
            self._save_state()
            return result

        # Check 20% reduction
        if drawdown_pct >= self.DRAWDOWN_REDUCE_PCT:
            result['position_multiplier'] = 0.5  # Halve position sizes
            result['reason'] = f'REDUCED: {drawdown_pct:.1f}% drawdown >= {self.DRAWDOWN_REDUCE_PCT}%'
            self.state['position_size_multiplier'] = 0.5
            self._save_state()
            return result

        # Normal operation
        self.state['position_size_multiplier'] = 1.0
        self._save_state()
        return result

    def check_daily_loss_limit(self, current_balance: float) -> Dict:
        """Check if daily loss limit is exceeded

        Args:
            current_balance: Current account balance

        Returns:
            Dict with 'trading_enabled', 'daily_pnl_pct', 'reason'
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # Reset daily tracking if new day
        if self.state['daily_start_date'] != today:
            self.state['daily_start_date'] = today
            self.state['daily_start_balance'] = current_balance
            self._save_state()

        # Calculate daily P&L
        if self.state['daily_start_balance'] == 0:
            daily_pnl_pct = 0.0
        else:
            daily_pnl_pct = ((current_balance - self.state['daily_start_balance']) / self.state['daily_start_balance']) * 100

        result = {
            'trading_enabled': True,
            'daily_pnl_pct': daily_pnl_pct,
            'reason': 'OK'
        }

        # Check limit
        if daily_pnl_pct <= self.DAILY_LOSS_LIMIT_PCT:
            result['trading_enabled'] = False
            result['reason'] = f'DAILY LIMIT: {daily_pnl_pct:.1f}% loss >= {self.DAILY_LOSS_LIMIT_PCT}%'
            return result

        return result

    def record_trade_result(self, symbol: str, is_win: bool):
        """Record trade result for blacklist management

        Args:
            symbol: Trading symbol
            is_win: True if trade was profitable
        """
        if symbol not in self.state['coin_failures']:
            self.state['coin_failures'][symbol] = 0

        if is_win:
            # Reset failure count on win
            self.state['coin_failures'][symbol] = 0
        else:
            # Increment failure count
            self.state['coin_failures'][symbol] += 1

            # Check if should blacklist
            if self.state['coin_failures'][symbol] >= self.CONSECUTIVE_FAILS_LIMIT:
                self._blacklist_coin(symbol)
                self.state['coin_failures'][symbol] = 0  # Reset counter

        self._save_state()

    def _blacklist_coin(self, symbol: str):
        """Add coin to blacklist

        Args:
            symbol: Trading symbol to blacklist
        """
        ban_until = datetime.now() + timedelta(days=self.BLACKLIST_DAYS)
        self.state['blacklist'][symbol] = ban_until.timestamp()
        self._save_state()
        print(f"⛔ {symbol} BLACKLISTED until {ban_until.strftime('%Y-%m-%d %H:%M')} ({self.BLACKLIST_DAYS} days)")

    def is_coin_blacklisted(self, symbol: str) -> bool:
        """Check if coin is currently blacklisted

        Args:
            symbol: Trading symbol

        Returns:
            True if blacklisted
        """
        if symbol not in self.state['blacklist']:
            return False

        ban_until_ts = self.state['blacklist'][symbol]
        ban_until = datetime.fromtimestamp(ban_until_ts)

        # Check if ban expired
        if datetime.now() > ban_until:
            del self.state['blacklist'][symbol]
            self._save_state()
            return False

        return True

    def get_blacklisted_coins(self) -> List[str]:
        """Get list of currently blacklisted coins

        Returns:
            List of blacklisted symbols
        """
        blacklisted = []
        for symbol, ban_until_ts in list(self.state['blacklist'].items()):
            ban_until = datetime.fromtimestamp(ban_until_ts)
            if datetime.now() <= ban_until:
                blacklisted.append(symbol)
            else:
                # Expired, remove
                del self.state['blacklist'][symbol]

        self._save_state()
        return blacklisted

    def is_trading_allowed(self, current_balance: float, symbol: Optional[str] = None) -> Dict:
        """Master check: is trading allowed?

        Args:
            current_balance: Current account balance
            symbol: Optional symbol to check (for blacklist)

        Returns:
            Dict with 'allowed', 'reason', 'position_multiplier'
        """
        result = {
            'allowed': True,
            'reason': 'OK',
            'position_multiplier': 1.0
        }

        # 1. Check coin blacklist
        if symbol and self.is_coin_blacklisted(symbol):
            result['allowed'] = False
            result['reason'] = f'{symbol} is blacklisted'
            return result

        # 2. Check daily loss limit
        daily_check = self.check_daily_loss_limit(current_balance)
        if not daily_check['trading_enabled']:
            result['allowed'] = False
            result['reason'] = daily_check['reason']
            return result

        # 3. Check drawdown limits
        dd_check = self.check_drawdown_limits(current_balance)
        if not dd_check['trading_enabled']:
            result['allowed'] = False
            result['reason'] = dd_check['reason']
            return result

        # Apply position multiplier from drawdown
        result['position_multiplier'] = dd_check['position_multiplier']

        return result

    def get_status(self, current_balance: float) -> Dict:
        """Get complete kill switch status

        Args:
            current_balance: Current account balance

        Returns:
            Complete status dict
        """
        drawdown_pct = self.get_current_drawdown_pct(current_balance)
        daily_check = self.check_daily_loss_limit(current_balance)
        blacklisted = self.get_blacklisted_coins()

        return {
            'peak_balance': self.state['peak_balance'],
            'current_balance': current_balance,
            'drawdown_pct': drawdown_pct,
            'daily_pnl_pct': daily_check['daily_pnl_pct'],
            'trading_enabled': self.state['trading_enabled'],
            'position_size_multiplier': self.state['position_size_multiplier'],
            'blacklisted_coins': blacklisted,
            'blacklist_count': len(blacklisted)
        }
