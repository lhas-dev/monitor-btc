# 🤖 Automated BTC Monitor - Binance

Automated system to identify Bitcoin buying opportunities using **Buy the Dip strategy** combined with technical indicators (Moving Average, RSI, Support/Resistance levels).

## 🎯 Overview

This monitor analyzes Bitcoin price movements on Binance and detects optimal entry points by:

- Monitoring significant price drops (Buy the Dip)
- Analyzing moving averages and RSI indicators
- Calculating support and resistance levels from historical data
- Using a scoring system to validate signals
- Sending Telegram notifications when opportunities are detected

## 📋 Requirements

- Docker and Docker Compose ([Get Docker](https://docs.docker.com/get-docker/))
- Telegram account (for notifications)
- Internet connection

## 🚀 Installation

1. **Clone or download this repository**

2. **Configure environment variables:**

   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Build and start the monitor:**

   ```bash
   docker-compose up -d
   ```

4. **Check logs:**
   ```bash
   docker-compose logs -f btc-monitor
   ```

## ⚙️ Configuration

All configuration is done via the `.env` file. Edit the `.env` file to customize your strategy and credentials:

### Strategy Parameters

```bash
SYMBOL=BTCUSDT            # Trading pair to monitor
MIN_DROP=5.0              # Alert when price drops 5% in 24h
MA_DISTANCE=3.0           # Alert when price is 3% below moving average
RSI_OVERSOLD=30           # RSI below 30 = oversold
MA_PERIOD=7               # 7-day moving average
STOP_LOSS=3.0             # 3% stop loss
TAKE_PROFIT=2.0           # Minimum 2% profit target (threshold)
MAX_TAKE_PROFIT=5.0       # Maximum 5% profit target cap (conservative)
RESISTANCE_FACTOR=0.6     # Use 60% distance to resistance (0.5-0.7)
CHECK_INTERVAL=300        # Check every 5 minutes (in seconds)
HISTORICAL_DAYS=90        # Days of historical data to analyze
```

#### 🎯 Conservative Target Calculation

The system uses a **hybrid approach** for calculating profit targets:

1. **Finds next resistance level** above current price
2. **Uses partial distance** (60% by default via `RESISTANCE_FACTOR`)
3. **Applies maximum cap** (5% by default via `MAX_TAKE_PROFIT`)

**Example:**
- Current Price: $100,000
- Next Resistance: $108,000 (+8%)
- Partial Target (60%): $100,000 + ($8,000 × 0.6) = $104,800 (+4.8%) ✅
- Max Cap Check: 4.8% < 5% → Target: $104,800

This approach provides **realistic, conservative targets** instead of aggressive resistance levels.

**Tuning:**
- `RESISTANCE_FACTOR=0.5-0.7` → Lower = more conservative
- `MAX_TAKE_PROFIT=3-7` → Adjust based on market volatility

### Telegram Configuration

All parameters are configured via `.env` file:

1. **Create a Telegram Bot:**

   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command and follow instructions
   - Save the bot token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get your Chat ID:**

   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find `"chat":{"id":123456789}` in the response

3. **Add credentials to `.env`:**
   ```bash
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

## 🏃 Usage

### Run the Monitor

```bash
docker-compose up -d
```

### Run Backtest

Test the strategy with historical data:

```bash
docker-compose run btc-monitor python backtest.py
```

### Test Telegram Integration

Verify your Telegram configuration is working:

```bash
docker-compose run btc-monitor python test_telegram.py
```

You should receive a test message on Telegram. If not, check your bot token and chat ID in `.env`.

### Stop the Monitor

```bash
docker-compose down
```

## 📊 Scoring System

The monitor assigns points for each detected signal:

| Signal       | Points | Description                                |
| ------------ | ------ | ------------------------------------------ |
| 24h Drop     | 3      | Price dropped more than configured minimum |
| Below MA     | 2      | Price is below moving average              |
| RSI Oversold | 2      | RSI indicates oversold condition           |
| Near Support | 1      | Price is close to historical support level |

**✅ ENTRY SIGNAL:** Generated when score reaches 3+ points

## 📅 Recommended Time Windows

Best times to monitor based on market activity:

- **Morning (9am-12pm):** Higher volatility, more opportunities
- **Afternoon (2pm-5pm):** Calmer movements
- **Night (8pm-11pm):** US market influence

## ⚠️ Important Warnings

- This is an **educational monitor**, not a trading bot
- **Always analyze** signals before making any trades
- Cryptocurrency market is **highly volatile and risky**
- **Never invest** more than you can afford to lose
- Always use **stop loss** to protect your capital
- This system **DOES NOT execute trades automatically**
- Trading cryptocurrencies involves substantial financial risk
- Past performance does not guarantee future results

---

**Strategy:** Buy the Dip combined with Technical Analysis
**Approach:** Monitor drops → Validate with indicators → Enter at support → Exit at resistance 🚀
