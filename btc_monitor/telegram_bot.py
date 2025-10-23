"""
Telegram notification handler
"""

from telegram import Bot
from telegram.error import TelegramError
from typing import Optional


class TelegramNotifier:
    """Simple Telegram bot for sending notifications"""

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram bot

        Args:
            bot_token: Bot token from @BotFather
            chat_id: Chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot: Optional[Bot] = None

        if bot_token and chat_id:
            try:
                self.bot = Bot(token=bot_token)
            except Exception as e:
                print(f"⚠️ Failed to initialize Telegram bot: {e}")

    def is_enabled(self) -> bool:
        """Check if Telegram is properly configured"""
        return self.bot is not None

    async def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Send a message via Telegram

        Args:
            message: Message text to send
            parse_mode: Message format (Markdown or HTML)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.bot:
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            print(f"❌ Telegram error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error sending notification: {e}")
            return False

    async def send_trade_signal(self, analysis: dict, symbol: str, ma_period: int) -> bool:
        """
        Send formatted trade signal notification

        Args:
            analysis: Analysis dictionary with signal data
            symbol: Trading symbol (e.g., BTCUSDT)
            ma_period: Moving average period used

        Returns:
            True if sent successfully
        """
        message = f"""
🚨 *{symbol} ENTRY SIGNAL DETECTED* 🚨

⏰ Time: {analysis['timestamp']}
💰 Current Price: USD {analysis['price']:,.2f}

📊 *INDICATORS:*
• MA{ma_period}: USD {analysis['ma']:,.2f} ({analysis['ma_distance']:+.2f}%)
• RSI(14): {analysis['rsi']:.1f}
• Score: {analysis['score']}/7

🔔 *DETECTED SIGNALS:*
"""
        for signal in analysis['signals']:
            message += f"• {signal}\n"

        message += f"""
💡 *TRADE SUGGESTION:*
🔹 ENTRY: USD {analysis['price']:,.2f}
🎯 TARGET: USD {analysis['target_price']:,.2f} (+{analysis['profit_percent']:.2f}%)
🛑 STOP LOSS: USD {analysis['stop_loss']:,.2f} (-{analysis['stop_percent']:.2f}%)

📊 Risk/Reward: 1:{analysis['profit_percent'] / analysis['stop_percent']:.2f}

📍 *KEY LEVELS:*
Resistances: {', '.join([f'USD {r:,.0f}' for r in analysis['resistances'][:3]])}
Supports: {', '.join([f'USD {s:,.0f}' for s in analysis['supports'][:3]])}
"""
        return await self.send_message(message)

    async def send_test_message(self) -> bool:
        """Send a test message to verify configuration"""
        message = """
🧪 *Telegram Test Message*

✅ Your BTC Monitor is successfully connected to Telegram!

This is what notifications will look like when a trading signal is detected.

*Configuration Status:*
• Bot Token: ✅ Valid
• Chat ID: ✅ Connected
• Notifications: ✅ Enabled

You're all set! 🚀
"""
        return await self.send_message(message)
