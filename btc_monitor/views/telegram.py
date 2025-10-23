"""
Telegram message formatting

Contains all Telegram-specific message templates and formatting logic.
Messages use Markdown formatting for Telegram's parse_mode.
"""


def format_trade_signal(analysis: dict, symbol: str, ma_period: int) -> str:
    """
    Format a trade signal notification for Telegram

    Args:
        analysis: Analysis dictionary with signal data
        symbol: Trading symbol (e.g., BTCUSDT)
        ma_period: Moving average period used

    Returns:
        Formatted message string with Markdown formatting
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
    return message


def format_test_message() -> str:
    """
    Format a test message to verify Telegram configuration

    Returns:
        Formatted test message string with Markdown formatting
    """
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
    return message
