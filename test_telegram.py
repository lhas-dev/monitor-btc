"""
Test Telegram Notification
Simple script to test if your Telegram bot is configured correctly
"""

import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

async def test_telegram():
    """Test sending a message via Telegram"""

    print("🧪 Testing Telegram Configuration...\n")
    print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:20]}... (hidden for security)")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    print("-" * 50)

    try:
        # Initialize bot
        print("\n1️⃣ Initializing Telegram bot...")
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        print("   ✅ Bot initialized successfully")

        # Send test message
        print("\n2️⃣ Sending test message...")
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

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )

        print("   ✅ Test message sent successfully!")
        print("\n" + "=" * 50)
        print("✅ SUCCESS! Check your Telegram app now.")
        print("=" * 50)
        print("\nYou should see a test message from your bot.")
        print("If you received it, your configuration is correct! 🎉")

    except TelegramError as e:
        print(f"\n❌ Telegram Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify your bot token is correct")
        print("   2. Make sure you sent at least one message to your bot")
        print("   3. Check that your chat ID is correct")
        print("   4. Ensure you have internet connection")

    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("\n🔧 Make sure you have installed python-telegram-bot:")
        print("   pip install python-telegram-bot")

def main():
    asyncio.run(test_telegram())

if __name__ == "__main__":
    main()
