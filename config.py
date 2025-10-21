# ⚙️ BTC/BRL MONITOR CONFIGURATION
# Edit the values below according to your strategy

# === DETECTION PARAMETERS ===

# Minimum 24h drop to trigger alert (%)
MIN_DROP = 5.0

# Distance from moving average to trigger alert (%)
# Example: 3.0 = alert when price is 3% below average
MA_DISTANCE = 3.0

# RSI below this value indicates oversold condition
RSI_OVERSOLD = 30

# Moving average period (days)
MA_PERIOD = 7


# === RISK MANAGEMENT ===

# Suggested stop loss (%)
STOP_LOSS = 3.0

# Minimum take profit to consider valid trade (%)
TAKE_PROFIT = 2.0


# === MONITORING ===

# Interval between checks (seconds)
# 300 = 5 minutes
# 60 = 1 minute
# 3600 = 1 hour
CHECK_INTERVAL = 300

# Days of historical data for analysis
HISTORICAL_DAYS = 90


# === TELEGRAM NOTIFICATION ===
# Get your bot token from @BotFather on Telegram
# Get your chat ID by messaging your bot and checking https://api.telegram.org/bot<TOKEN>/getUpdates
TELEGRAM_BOT_TOKEN = ""  # Add your bot token here
TELEGRAM_CHAT_ID = ""     # Add your chat ID here
TELEGRAM_ENABLED = True  # Set to True to enable notifications


# === SCORING SYSTEM ===
# The monitor adds points for each detected signal:
# - 24h drop: 3 points
# - Below MA: 2 points
# - RSI oversold: 2 points
# - Near support: 1 point
#
# SUGGESTED ENTRY: 3+ points
