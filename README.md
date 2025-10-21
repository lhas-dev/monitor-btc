# 🤖 Automated BTC/BRL Monitor - Binance

Automated system to identify Bitcoin buying opportunities (Buy the Dip strategy).

## 🎯 What does it do?

✅ Monitors BTC/BRL price on Binance in real-time
✅ Automatically detects significant drops
✅ Calculates support and resistance based on historical data
✅ Analyzes technical indicators (Moving Average, RSI)
✅ Suggests entry price, target, and stop loss
✅ Scoring system to validate signals
✅ Saves alerts to JSON file
✅ **Sends notifications via Telegram when signals are detected**

## 📋 Requirements

- Python 3.7 or higher
- Internet connection
- Telegram account (for notifications)

## 🚀 Installation

### Option 1: Docker (Recommended for Production)

The easiest way to run the monitor is using Docker:

#### Prerequisites
- Docker and Docker Compose installed ([Get Docker](https://docs.docker.com/get-docker/))

#### Quick Start
1. **Configure your settings:**
   ```bash
   # Edit config.py and add your Telegram credentials
   nano config.py
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f btc-monitor
   ```

4. **Stop the monitor:**
   ```bash
   docker-compose down
   ```

#### Docker Commands

```bash
# Build the image
docker-compose build

# Start the monitor (detached mode)
docker-compose up -d

# View logs in real-time
docker-compose logs -f

# Restart the monitor
docker-compose restart

# Stop the monitor
docker-compose stop

# Remove container and volumes
docker-compose down -v
```

### Option 2: Manual Python Installation

#### 1. Install required libraries

Open terminal/command prompt and run:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install requests pandas numpy python-telegram-bot
```

#### 2. Download files

Place the following files in the same folder:
- `monitor_btc.py` (main file)
- `config.py` (configuration)
- `requirements.txt` (dependencies)

## ⚙️ Configuration

### Basic Configuration

Edit `config.py` file to adjust your strategy:

```python
MIN_DROP = 5.0              # Alert when price drops 5% in 24h
MA_DISTANCE = 3.0           # Alert when price is 3% below average
RSI_OVERSOLD = 30           # RSI below 30 = oversold
MA_PERIOD = 7               # 7-day moving average
STOP_LOSS = 3.0             # 3% stop loss
TAKE_PROFIT = 2.0           # Minimum 2% target
CHECK_INTERVAL = 300        # Check every 5 minutes
```

### Telegram Setup (Optional but Recommended)

To receive notifications on your phone:

1. **Create a Telegram Bot:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow instructions and choose a name for your bot
   - Save the **bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get your Chat ID:**
   - Send a message to your bot
   - Open this URL in your browser (replace TOKEN with your bot token):
     ```
     https://api.telegram.org/botTOKEN/getUpdates
     ```
   - Look for `"chat":{"id":123456789}` in the response
   - Save this **chat ID** number

3. **Configure in config.py:**
   ```python
   TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
   TELEGRAM_CHAT_ID = "123456789"
   TELEGRAM_ENABLED = True
   ```

## 🏃 How to Use

### Run the monitor:

```bash
python monitor_btc.py
```

### What you'll see:

```
🤖 BTC/BRL Monitor Started!
📡 Checking every 300 seconds...
⚙️  Settings: Min drop 5.0%, RSI < 30
✅ Telegram notifications enabled

================================================================================
⏰ 2025-10-20 15:30:45
💰 CURRENT PRICE: R$ 590,234.00
================================================================================

📊 INDICATORS:
   MA7: R$ 598,500.00 (-1.38%)
   RSI(14): 35.2

🚨 DETECTED SIGNALS (Score: 5):
   🔴 24H DROP: -5.80% (minimum: -5.0%)
   🔴 BELOW MA7: -3.20% (minimum: -3.0%)
   🟡 NEAR SUPPORT: R$ 588,000

📍 KEY LEVELS:
   Resistances: R$ 605,000, R$ 600,000, R$ 595,000
   Supports: R$ 590,000, R$ 585,000, R$ 580,000

                  🟢 ENTRY OPPORTUNITY DETECTED! 🟢

💡 TRADE SUGGESTION:
   🔹 ENTRY: R$ 590,234.00
   🎯 TARGET: R$ 600,000.00 (+1.65%)
   🛑 STOP: R$ 572,527.00 (-3.00%)
   📊 RISK/REWARD: 1:0.55

✅ Telegram notification sent successfully
💾 Signal saved to signals_log.json
================================================================================
```

### Stop the monitor:

Press `Ctrl + C` in the terminal.

## 📊 Scoring System

The monitor assigns points for each signal:

| Signal | Points | Description |
|--------|--------|-------------|
| 24h Drop | 3 | Price dropped more than configured minimum |
| Below MA | 2 | Price is below moving average |
| RSI Oversold | 2 | RSI indicates oversold |
| Near Support | 1 | Price is close to historical support |

**✅ ENTRY SIGNAL:** When score reaches 3+ points

## 📁 Generated Files

### `signals_log.json`

All entry signals are automatically saved to this file:

```json
[
  {
    "timestamp": "2025-10-20 15:30:45",
    "price": 590234.0,
    "signals": [...],
    "entry_signal": true,
    "target_price": 600000.0,
    "stop_loss": 572527.0,
    "score": 5
  }
]
```

## 🎓 Usage Tips

### Customization by Profile

**Conservative:**
```python
MIN_DROP = 7.0
TAKE_PROFIT = 1.5
STOP_LOSS = 2.0
```

**Moderate (default):**
```python
MIN_DROP = 5.0
TAKE_PROFIT = 2.0
STOP_LOSS = 3.0
```

**Aggressive:**
```python
MIN_DROP = 3.0
TAKE_PROFIT = 3.0
STOP_LOSS = 4.0
```

### Recommended Time Windows

- **Morning (9am-12pm):** Higher volatility, more opportunities
- **Afternoon (2pm-5pm):** Calmer movements
- **Night (8pm-11pm):** US market influence

### Manual Backtesting

You can analyze historical data by editing the date in the code:

```python
# In monitor_btc.py file, around line 200
# Change to analyze a specific date
```

## 🔧 Troubleshooting

### Error: "No module named 'requests'"
```bash
pip install requests
```

### Error: "No module named 'telegram'"
```bash
pip install python-telegram-bot
```

### Error: "Connection timeout"
- Check your internet connection
- Binance API might be temporarily unavailable

### Telegram notifications not working
- Verify bot token is correct
- Check chat ID is correct
- Ensure you sent at least one message to your bot
- Verify `TELEGRAM_ENABLED = True` in config.py

### Too many false alerts
- Increase `MIN_DROP` in config.py
- Increase minimum score for entry (edit line 277 in the code)

### Too few alerts
- Decrease `MIN_DROP`
- Decrease `CHECK_INTERVAL` to check more frequently

### Docker Issues

**Container not starting:**
```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs btc-monitor
```

**Config changes not taking effect:**
```bash
# Restart the container after editing config.py
docker-compose restart
```

**Container keeps restarting:**
```bash
# Check if config.py has valid Telegram credentials
# View logs for error messages
docker-compose logs -f btc-monitor
```

**Update the application:**
```bash
# Rebuild the Docker image
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📱 Telegram Notification Features

When an entry signal is detected, you'll receive a formatted message on Telegram with:

- ⏰ Timestamp
- 💰 Current price
- 📊 Technical indicators (MA, RSI, Score)
- 🔔 All detected signals
- 💡 Trade suggestion (entry, target, stop loss)
- 📊 Risk/Reward ratio
- 📍 Key support and resistance levels

## 📈 Next Steps

After using the monitor for a few days:

1. **Analyze `signals_log.json`**
   - See which signals were profitable
   - Adjust parameters based on results

2. **Fine-tune Telegram notifications**
   - Monitor on your phone
   - React quickly to opportunities
   - Keep track of market movements

3. **Automate orders (Advanced)**
   - Integrate with Binance API to execute trades
   - ⚠️ **USE WITH EXTREME CAUTION!**

## ⚠️ Important Warnings

- This is an **educational monitor**, not a trading bot
- **Always analyze** signals before trading
- Crypto market is **highly volatile**
- **Never invest** more than you can afford to lose
- Use **stop loss** in all operations
- This code **DOES NOT execute trades automatically**
- Trading cryptocurrencies involves substantial risk

## 📞 Support

Questions? Adjust parameters in `config.py` and test!

---

**Developed for "Buy the Dip 5/3" strategy**
*Monitor drops, buy at support, sell at resistance* 🚀
