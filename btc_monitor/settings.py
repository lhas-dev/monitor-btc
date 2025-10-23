"""
Configuration management - loads from .env file
All settings with sensible defaults
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def get_env(key: str, default=None, value_type=str):
    """Get environment variable with type conversion"""
    value = os.getenv(key)
    if value is None:
        return default

    try:
        if value_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif value_type == float:
            return float(value)
        elif value_type == int:
            return int(value)
        return value
    except (ValueError, AttributeError):
        return default


# === TRADING SYMBOL ===
# Parse comma-separated symbols into a list
_symbol_str = get_env('SYMBOL', 'BTCUSDT')
SYMBOLS = [s.strip().upper() for s in _symbol_str.split(',') if s.strip()]

# Keep SYMBOL for backward compatibility (first symbol in list)
SYMBOL = SYMBOLS[0] if SYMBOLS else 'BTCUSDT'

# === DETECTION PARAMETERS ===
MIN_DROP = get_env('MIN_DROP', 5.0, float)
MA_DISTANCE = get_env('MA_DISTANCE', 3.0, float)
RSI_OVERSOLD = get_env('RSI_OVERSOLD', 30, int)
MA_PERIOD = get_env('MA_PERIOD', 7, int)

# === RISK MANAGEMENT ===
STOP_LOSS = get_env('STOP_LOSS', 3.0, float)
TAKE_PROFIT = get_env('TAKE_PROFIT', 2.0, float)  # Minimum profit threshold
MAX_TAKE_PROFIT = get_env('MAX_TAKE_PROFIT', 5.0, float)  # Maximum profit target cap
RESISTANCE_FACTOR = get_env('RESISTANCE_FACTOR', 0.6, float)  # Partial distance to resistance (0.5-0.7)

# === MONITORING ===
CHECK_INTERVAL = get_env('CHECK_INTERVAL', 300, int)
HISTORICAL_DAYS = get_env('HISTORICAL_DAYS', 90, int)

# === TELEGRAM NOTIFICATION ===
TELEGRAM_ENABLED = get_env('TELEGRAM_ENABLED', False, bool)
TELEGRAM_BOT_TOKEN = get_env('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = get_env('TELEGRAM_CHAT_ID', '')
