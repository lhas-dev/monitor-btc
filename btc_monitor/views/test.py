"""
Test script message formatting

Contains all message formatting for the Telegram test script.
"""


def format_test_start(bot_token: str, chat_id: str, enabled: bool) -> str:
    """
    Format test start information

    Args:
        bot_token: Bot token (will be truncated for security)
        chat_id: Chat ID
        enabled: Whether Telegram is enabled

    Returns:
        Formatted test start message
    """
    output = "🧪 Testing Telegram Configuration...\n\n"
    output += f"Bot Token: {bot_token[:20]}... (hidden for security)\n"
    output += f"Chat ID: {chat_id}\n"
    output += f"Enabled: {enabled}\n"
    output += "-" * 50 + "\n"
    return output


def format_telegram_disabled() -> str:
    """
    Format message when Telegram is disabled

    Returns:
        Formatted disabled message
    """
    output = "\n⚠️ Telegram is disabled in .env\n"
    output += "   Set TELEGRAM_ENABLED=true in your .env file\n"
    return output


def format_credentials_missing() -> str:
    """
    Format message when Telegram credentials are missing

    Returns:
        Formatted credentials missing message
    """
    output = "\n⚠️ Telegram credentials missing\n"
    output += "   Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to your .env file\n"
    return output


def format_init_bot() -> str:
    """
    Format message for bot initialization step

    Returns:
        Formatted initialization message
    """
    return "\n1️⃣ Initializing Telegram bot..."


def format_bot_init_failed() -> str:
    """
    Format message when bot initialization fails

    Returns:
        Formatted failure message with troubleshooting
    """
    output = "   ❌ Failed to initialize bot\n"
    output += "\n🔧 Troubleshooting:\n"
    output += "   1. Verify your bot token is correct\n"
    output += "   2. Check that your chat ID is correct\n"
    return output


def format_bot_init_success() -> str:
    """
    Format message when bot initialization succeeds

    Returns:
        Formatted success message
    """
    return "   ✅ Bot initialized successfully"


def format_sending_test() -> str:
    """
    Format message for sending test step

    Returns:
        Formatted sending message
    """
    return "\n2️⃣ Sending test message..."


def format_success_message() -> str:
    """
    Format comprehensive success message

    Returns:
        Formatted success message
    """
    output = "   ✅ Test message sent successfully!\n"
    output += "\n" + "=" * 50 + "\n"
    output += "✅ SUCCESS! Check your Telegram app now.\n"
    output += "=" * 50 + "\n"
    output += "\nYou should see a test message from your bot.\n"
    output += "If you received it, your configuration is correct! 🎉\n"
    return output


def format_error_message(error_type: str = "send") -> str:
    """
    Format error message with troubleshooting

    Args:
        error_type: Type of error ("send" or "init")

    Returns:
        Formatted error message with troubleshooting steps
    """
    output = "   ❌ Failed to send test message\n"
    output += "\n🔧 Troubleshooting:\n"
    output += "   1. Verify your bot token is correct\n"
    output += "   2. Make sure you sent at least one message to your bot\n"
    output += "   3. Check that your chat ID is correct\n"
    output += "   4. Ensure you have internet connection\n"
    return output
