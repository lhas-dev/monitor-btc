"""
Telegram notification handler
"""

from telegram import Bot
from telegram.error import TelegramError
from typing import Optional
from btc_monitor.views.telegram import format_trade_signal, format_test_message


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
        message = format_trade_signal(analysis, symbol, ma_period)
        return await self.send_message(message)

    async def send_test_message(self) -> bool:
        """Send a test message to verify configuration"""
        message = format_test_message()
        return await self.send_message(message)
