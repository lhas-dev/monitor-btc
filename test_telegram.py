"""
Test Telegram Notification
Simple script to test if your Telegram bot is configured correctly
"""

import asyncio
from btc_monitor.telegram_bot import TelegramNotifier
from btc_monitor import settings
from btc_monitor.views.test import (
    format_test_start,
    format_telegram_disabled,
    format_credentials_missing,
    format_init_bot,
    format_bot_init_failed,
    format_bot_init_success,
    format_sending_test,
    format_success_message,
    format_error_message
)


async def test_telegram():
    """Test sending a message via Telegram"""

    # Print test start info
    print(format_test_start(
        settings.TELEGRAM_BOT_TOKEN,
        settings.TELEGRAM_CHAT_ID,
        settings.TELEGRAM_ENABLED
    ))

    if not settings.TELEGRAM_ENABLED:
        print(format_telegram_disabled())
        return

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print(format_credentials_missing())
        return

    print(format_init_bot())
    notifier = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)

    if not notifier.is_enabled():
        print(format_bot_init_failed())
        return

    print(format_bot_init_success())

    print(format_sending_test())
    success = await notifier.send_test_message()

    if success:
        print(format_success_message())
    else:
        print(format_error_message())


def main():
    asyncio.run(test_telegram())


if __name__ == "__main__":
    main()
