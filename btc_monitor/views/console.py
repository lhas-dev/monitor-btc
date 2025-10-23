"""
Console output formatting

Contains all console/terminal output formatting for the monitor script.
"""


def format_analysis(analysis: dict, ma_period: int) -> str:
    """
    Format analysis output for console display

    Args:
        analysis: Analysis dictionary with signal data
        ma_period: Moving average period used

    Returns:
        Formatted analysis string for console output
    """
    output = "\n" + "="*80 + "\n"
    output += f"⏰ {analysis['timestamp']}\n"
    output += f"💰 CURRENT PRICE: USD {analysis['price']:,.2f}\n"
    output += "="*80

    output += f"\n\n📊 INDICATORS:\n"
    output += f"   MA{ma_period}: USD {analysis['ma']:,.2f} ({analysis['ma_distance']:+.2f}%)\n"
    output += f"   RSI(14): {analysis['rsi']:.1f}\n"

    if analysis['signals']:
        output += f"\n🚨 DETECTED SIGNALS (Score: {analysis['score']}):\n"
        for signal in analysis['signals']:
            output += f"   {signal}\n"

    output += f"\n📍 KEY LEVELS:\n"
    output += f"   Resistances: {', '.join([f'USD {r:,.0f}' for r in analysis['resistances'][:3]])}\n"
    output += f"   Supports: {', '.join([f'USD {s:,.0f}' for s in analysis['supports'][:3]])}\n"

    if analysis['entry_signal']:
        output += f"\n{'🟢 ENTRY OPPORTUNITY DETECTED! 🟢':^80}\n"
        output += f"\n💡 TRADE SUGGESTION:\n"
        output += f"   🔹 ENTRY: USD {analysis['price']:,.2f}\n"
        output += f"   🎯 TARGET: USD {analysis['target_price']:,.2f} (+{analysis['profit_percent']:.2f}%)\n"
        output += f"   🛑 STOP: USD {analysis['stop_loss']:,.2f} (-{analysis['stop_percent']:.2f}%)\n"

        risk_reward = analysis['profit_percent'] / analysis['stop_percent']
        output += f"   📊 RISK/REWARD: 1:{risk_reward:.2f}\n"
    else:
        output += f"\n⚪ No clear opportunity at the moment (Score: {analysis['score']}/7)\n"

    output += "\n" + "="*80 + "\n"
    return output


def format_startup_info(symbol: str, check_interval: int, min_drop: float, rsi_oversold: int) -> str:
    """
    Format startup information for console display

    Args:
        symbol: Trading symbol
        check_interval: Check interval in seconds
        min_drop: Minimum drop percentage
        rsi_oversold: RSI oversold threshold

    Returns:
        Formatted startup information string
    """
    output = "🤖 BTC Monitor Started!\n"
    output += f"📡 Symbol: {symbol}\n"
    output += f"📡 Checking every {check_interval} seconds...\n"
    output += f"⚙️  Settings: Min drop {min_drop}%, RSI < {rsi_oversold}\n"
    return output


def format_telegram_status(telegram_enabled: bool) -> str:
    """
    Format Telegram status message

    Args:
        telegram_enabled: Whether Telegram is enabled

    Returns:
        Formatted status message
    """
    if telegram_enabled:
        return "✅ Telegram notifications enabled"
    else:
        return "⚠️ Telegram not configured properly"
