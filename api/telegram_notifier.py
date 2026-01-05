#!/usr/bin/env python3
"""Enhanced Telegram Notification System for Trading Bot

Features:
- Rich notifications with emojis and formatting
- Position exit alerts (TP/SL/PARTIAL)
- Trailing stop and profit-taking alerts
- Performance summaries
- Error notifications
"""
import os
import requests
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class TelegramNotifier:
    """Send trading notifications via Telegram with enhanced formatting"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)

        # Alert throttling to avoid spam
        self.last_alert_time = {}
        self.min_alert_interval = 300  # 5 minutes between duplicate alerts

        if not self.enabled:
            print("⚠️  Telegram notifications disabled (missing credentials)")

    def send_message(self, message: str, silent: bool = False) -> bool:
        """Send a message via Telegram

        Args:
            message: Message text (supports Markdown)
            silent: Send without notification sound

        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_notification': silent
            }
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}")
            return False

    def _should_send_alert(self, alert_key: str) -> bool:
        """Check if alert should be sent (throttle duplicates)"""
        last_time = self.last_alert_time.get(alert_key, 0)
        if time.time() - last_time < self.min_alert_interval:
            return False
        self.last_alert_time[alert_key] = time.time()
        return True

    def notify_new_position(self, symbol: str, quantity: float, price: float,
                           usdt_value: float, score: float, kelly: float,
                           stop_loss_pct: float = 0, take_profit_pct: float = 0):
        """Notify about new position opened"""
        tp_price = price * (1 + take_profit_pct) if take_profit_pct else 0
        sl_price = price * (1 - stop_loss_pct) if stop_loss_pct else 0

        message = f"""
🚀 *NEW POSITION OPENED*

💎 *{symbol}*
━━━━━━━━━━━━━━━
📊 *Entry Details:*
  • Price: `${price:.6f}`
  • Quantity: `{quantity:.4f}`
  • Size: `${usdt_value:.2f}`

📈 *Analysis:*
  • Score: `{score:.0f}/100`
  • Kelly: `{kelly*100:.1f}%`

🎯 *Protection Orders:*
  • TP: `${tp_price:.6f}` (+{take_profit_pct*100:.0f}%)
  • SL: `${sl_price:.6f}` (-{stop_loss_pct*100:.0f}%)

✅ OCO orders set automatically!
"""
        return self.send_message(message)

    def notify_position_exit(self, symbol: str, exit_type: str, quantity: float,
                            entry_price: float, exit_price: float, pnl_pct: float,
                            hold_time_hours: float, usdt_value: float):
        """Notify when position exits (TP/SL/PARTIAL/MANUAL)"""
        # Choose emoji based on exit type and profit/loss
        if exit_type == 'TP':
            emoji = "🎯"
            title = "TAKE PROFIT HIT"
        elif exit_type == 'SL':
            emoji = "🛑"
            title = "STOP LOSS HIT"
        elif exit_type == 'PARTIAL':
            emoji = "💰"
            title = "PARTIAL PROFIT TAKEN"
        elif exit_type == 'TRAILING':
            emoji = "🛡️"
            title = "TRAILING STOP HIT"
        else:
            emoji = "📤"
            title = "POSITION CLOSED"

        profit_emoji = "✅" if pnl_pct > 0 else "❌"

        message = f"""
{emoji} *{title}*

💎 *{symbol}*
━━━━━━━━━━━━━━━
📊 *Exit Details:*
  • Entry: `${entry_price:.6f}`
  • Exit: `${exit_price:.6f}`
  • Quantity: `{quantity:.4f}`

{profit_emoji} *Performance:*
  • P&L: `{pnl_pct:+.2f}%`
  • Value: `${usdt_value:.2f}`
  • Hold Time: `{hold_time_hours:.1f}h`

{'🎉 Profit locked in!' if pnl_pct > 0 else '⚠️ Loss contained by stop-loss'}
"""
        return self.send_message(message)

    def notify_trailing_stop_applied(self, symbol: str, profit_pct: float,
                                    new_stop_price: float, entry_price: float):
        """Notify when trailing stop is applied to breakeven"""
        message = f"""
🛡️ *TRAILING STOP ACTIVATED*

💎 *{symbol}*
━━━━━━━━━━━━━━━
📈 *Current Profit:* `+{profit_pct:.1f}%`

🔒 *Stop Moved to Breakeven:*
  • Entry Price: `${entry_price:.6f}`
  • New Stop: `${new_stop_price:.6f}`

✅ *Capital Protected!*
No more risk - profits are locked in!
"""
        return self.send_message(message, silent=True)

    def notify_partial_exit(self, symbol: str, profit_pct: float, quantity_sold: float,
                           exit_price: float, remaining_qty: float):
        """Notify when partial profit is taken"""
        message = f"""
💰 *PARTIAL PROFIT TAKEN*

💎 *{symbol}*
━━━━━━━━━━━━━━━
📊 *Profit Realized:*
  • Profit: `+{profit_pct:.1f}%`
  • Sold: `{quantity_sold:.4f}` (50%)
  • Price: `${exit_price:.6f}`

🎯 *Position Updated:*
  • Remaining: `{remaining_qty:.4f}` (50%)
  • Riding profits to full TP!

✅ Half of profits secured, letting winners run!
"""
        return self.send_message(message, silent=True)

    def notify_correlation_skip(self, symbol: str, correlated_with: str, correlation: float):
        """Notify when position skipped due to correlation"""
        if not self._should_send_alert(f"corr_{symbol}"):
            return False

        message = f"""
🚫 *POSITION SKIPPED - CORRELATION*

💎 *{symbol}*
━━━━━━━━━━━━━━━
⚠️ *Too Correlated With:*
  • {correlated_with}
  • Correlation: `{correlation:.2f}`

🛡️ *Risk Management:*
Avoiding concentration risk - diversifying portfolio instead!
"""
        return self.send_message(message, silent=True)

    def notify_liquidity_skip(self, symbol: str, reason: str):
        """Notify when position skipped due to low liquidity"""
        if not self._should_send_alert(f"liq_{symbol}"):
            return False

        message = f"""
🚫 *POSITION SKIPPED - LIQUIDITY*

💎 *{symbol}*
━━━━━━━━━━━━━━━
⚠️ *Issue:* {reason}

🛡️ *Risk Management:*
Avoiding illiquid market - protecting from slippage!
"""
        return self.send_message(message, silent=True)

    def notify_learning_insight(self, insight: str):
        """Notify about learning engine insights"""
        message = f"""
🧠 *LEARNING ENGINE UPDATE*

📊 *New Insight:*
{insight}

🤖 Bot is adapting strategy based on past performance!
"""
        return self.send_message(message, silent=True)

    def notify_trading_error(self, context: str, error: str):
        """Notify about trading errors"""
        message = f"""
⚠️ *TRADING ERROR*

🔴 *Context:* {context}
━━━━━━━━━━━━━━━
*Error:* {error}

Check logs for details.
Bot continues to run with safety checks.
"""
        return self.send_message(message)

    def notify_daily_summary(self, balance: float, pnl: float, pnl_pct: float,
                            positions: int, trades_today: int, win_rate: float = 0,
                            active_positions: list = None):
        """Send daily portfolio summary"""
        emoji = "📈" if pnl >= 0 else "📉"
        profit_emoji = "✅" if pnl >= 0 else "❌"

        # Format position list
        pos_text = ""
        if active_positions and len(active_positions) > 0:
            pos_text = "\n\n📊 *Active Positions:*\n"
            for pos in active_positions[:5]:  # Top 5
                pos_emoji = "🟢" if pos.get('pnl_pct', 0) > 0 else "🔴"
                pos_text += f"  {pos_emoji} {pos['symbol']}: `{pos.get('pnl_pct', 0):+.1f}%`\n"

        message = f"""
{emoji} *DAILY SUMMARY*

💰 *Portfolio:*
  • Balance: `${balance:.2f}`
  • Daily P&L: `{pnl:+.2f}` USDT ({pnl_pct:+.2f}%)

📊 *Trading Stats:*
  • Open Positions: `{positions}`
  • Trades Today: `{trades_today}`
  • Win Rate: `{win_rate*100:.1f}%`{pos_text}

🤖 Bot running 24/7 with active monitoring!
{profit_emoji} Keep compounding!
"""
        return self.send_message(message, silent=True)

    def notify_bot_startup(self, balance: float, positions: int, exposure_pct: float):
        """Notify when bot starts"""
        message = f"""
🤖 *BOT STARTED*

✅ *All Systems Online:*
━━━━━━━━━━━━━━━
💰 Balance: `${balance:.2f}`
📊 Positions: `{positions}`
📈 Exposure: `{exposure_pct:.1f}%`

🚀 *Features Active:*
  ✓ Position Monitoring
  ✓ Trailing Stops
  ✓ Partial Profits
  ✓ Correlation Filter
  ✓ Liquidity Checks
  ✓ Learning Engine

Ready to trade! 🎯
"""
        return self.send_message(message)

    def notify_bot_shutdown(self, reason: str = "Manual stop"):
        """Notify when bot stops"""
        message = f"""
🛑 *BOT STOPPED*

Reason: {reason}

All positions remain protected by OCO orders.
Restart when ready! 👋
"""
        return self.send_message(message)


# Global instance
notifier = TelegramNotifier()
