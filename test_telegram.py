"""
Test Telegram Notification
Simple script to test if your Telegram bot is configured correctly
"""

import asyncio
from btc_monitor.telegram_bot import TelegramNotifier
from btc_monitor import settings


async def test_telegram():
    """Test sending a message via Telegram"""

    print("🧪 Testing Telegram Configuration...\n")
    print(f"Bot Token: {settings.TELEGRAM_BOT_TOKEN[:20]}... (hidden for security)")
    print(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")
    print(f"Enabled: {settings.TELEGRAM_ENABLED}")
    print("-" * 50)

    if not settings.TELEGRAM_ENABLED:
        print("\n⚠️ Telegram is disabled in .env")
        print("   Set TELEGRAM_ENABLED=true in your .env file")
        return

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("\n⚠️ Telegram credentials missing")
        print("   Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to your .env file")
        return

    print("\n1️⃣ Initializing Telegram bot...")
    notifier = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)

    if not notifier.is_enabled():
        print("   ❌ Failed to initialize bot")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify your bot token is correct")
        print("   2. Check that your chat ID is correct")
        return

    print("   ✅ Bot initialized successfully")

    print("\n2️⃣ Sending test message...")
    success = await notifier.send_test_message()

    if success:
        print("   ✅ Test message sent successfully!")
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Check your Telegram app now.")
        print("=" * 50)
        print("\nYou should see a test message from your bot.")
        print("If you received it, your configuration is correct! 🎉")
    else:
        print("   ❌ Failed to send test message")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify your bot token is correct")
        print("   2. Make sure you sent at least one message to your bot")
        print("   3. Check that your chat ID is correct")
        print("   4. Ensure you have internet connection")


def main():
    asyncio.run(test_telegram())


if __name__ == "__main__":
    main()
