"""
Automated BTC/BRL Monitor - Binance
Strategy: Buy the Dip 5/3

Detects significant drops and calculates targets based on historical support/resistance levels
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Tuple
import os
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file (priority)
load_dotenv()

# Import config.py for fallback values
try:
    import config as config_module
except ImportError:
    config_module = None

# Helper function to get config values: .env first, then config.py, then default
def get_config(env_key: str, config_attr: str = None, default=None, value_type=str):
    """Get configuration value from .env first, then config.py, then default"""
    # Try environment variable first
    env_value = os.getenv(env_key)
    if env_value is not None:
        try:
            if value_type == bool:
                return env_value.lower() in ('true', '1', 'yes', 'on')
            elif value_type == float:
                return float(env_value)
            elif value_type == int:
                return int(env_value)
            return env_value
        except (ValueError, AttributeError):
            pass

    # Try config.py
    if config_module and config_attr and hasattr(config_module, config_attr):
        return getattr(config_module, config_attr)

    # Return default
    return default

# Load all configuration values (priority: .env > config.py > defaults)
MIN_DROP = get_config('MIN_DROP', 'MIN_DROP', 5.0, float)
MA_DISTANCE = get_config('MA_DISTANCE', 'MA_DISTANCE', 3.0, float)
RSI_OVERSOLD = get_config('RSI_OVERSOLD', 'RSI_OVERSOLD', 30, int)
MA_PERIOD = get_config('MA_PERIOD', 'MA_PERIOD', 7, int)
STOP_LOSS = get_config('STOP_LOSS', 'STOP_LOSS', 3.0, float)
TAKE_PROFIT = get_config('TAKE_PROFIT', 'TAKE_PROFIT', 2.0, float)
CHECK_INTERVAL = get_config('CHECK_INTERVAL', 'CHECK_INTERVAL', 300, int)
HISTORICAL_DAYS = get_config('HISTORICAL_DAYS', 'HISTORICAL_DAYS', 90, int)
TELEGRAM_BOT_TOKEN = get_config('TELEGRAM_BOT_TOKEN', 'TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = get_config('TELEGRAM_CHAT_ID', 'TELEGRAM_CHAT_ID', '')
TELEGRAM_ENABLED = get_config('TELEGRAM_ENABLED', 'TELEGRAM_ENABLED', False, bool)

# Legacy compatibility - map old config names to new ones
CONFIG = {
    'SYMBOL': 'BTCBRL',
    'QUEDA_MINIMA': MIN_DROP,
    'DISTANCIA_MA': MA_DISTANCE,
    'RSI_OVERSOLD': RSI_OVERSOLD,
    'PERIODO_MA': MA_PERIOD,
    'STOP_LOSS': STOP_LOSS,
    'TAKE_PROFIT': TAKE_PROFIT,
    'INTERVALO_CHECK': CHECK_INTERVAL,
    'DIAS_HISTORICO': HISTORICAL_DAYS,
}

class BinanceMonitor:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.symbol = CONFIG['SYMBOL']
        self.last_alert_time = None
        self.price_history = []

        # Initialize Telegram bot if enabled
        self.telegram_bot = None
        if TELEGRAM_ENABLED and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                self.telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
                print("✅ Telegram notifications enabled")
            except Exception as e:
                print(f"⚠️ Failed to initialize Telegram bot: {e}")

    def get_current_price(self) -> float:
        """Get current BTC/BRL price"""
        try:
            url = f"{self.base_url}/api/v3/ticker/price"
            params = {'symbol': self.symbol}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception as e:
            print(f"❌ Error fetching price: {e}")
            return None

    def get_24h_change(self) -> Dict:
        """Get 24h statistics"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            params = {'symbol': self.symbol}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                'price_change': float(data['priceChange']),
                'price_change_percent': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
        except Exception as e:
            print(f"❌ Error fetching 24h data: {e}")
            return None

    def get_historical_klines(self, days: int = 90) -> pd.DataFrame:
        """Get historical data (daily candles)"""
        try:
            url = f"{self.base_url}/api/v3/klines"
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            params = {
                'symbol': self.symbol,
                'interval': '1d',
                'startTime': start_time,
                'endTime': end_time,
                'limit': 1000
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return None

    def calculate_support_resistance(self, df: pd.DataFrame, tolerance: float = 0.02) -> Tuple[List, List]:
        """
        Identify supports and resistances based on price level touches
        tolerance: % tolerance to group nearby levels
        """
        highs = df['high'].values
        lows = df['low'].values

        # Group nearby levels
        def cluster_levels(levels, tolerance):
            if len(levels) == 0:
                return []

            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]

            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                    current_cluster.append(level)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [level]

            clusters.append(np.mean(current_cluster))
            return clusters

        # Count touches at each level
        all_highs = cluster_levels(highs.tolist(), tolerance)
        all_lows = cluster_levels(lows.tolist(), tolerance)

        # Resistances (high levels touched multiple times)
        resistances = sorted(all_highs, reverse=True)[:5]

        # Supports (low levels touched multiple times)
        supports = sorted(all_lows, reverse=True)[:5]

        return supports, resistances

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        deltas = prices.diff()
        gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def calculate_moving_average(self, df: pd.DataFrame, period: int) -> float:
        """Calculate simple moving average"""
        return df['close'].tail(period).mean()

    def analyze_opportunity(self, current_price: float, stats_24h: Dict, df_historical: pd.DataFrame) -> Dict:
        """Analyze if there's an entry opportunity"""

        analysis = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': current_price,
            'signals': [],
            'entry_signal': False,
            'target_price': None,
            'stop_loss': None,
            'score': 0
        }

        # 1. 24H DROP
        drop_24h = stats_24h['price_change_percent']
        if drop_24h <= -CONFIG['QUEDA_MINIMA']:
            analysis['signals'].append(f"🔴 24H DROP: {drop_24h:.2f}% (minimum: {-CONFIG['QUEDA_MINIMA']}%)")
            analysis['score'] += 3

        # 2. MOVING AVERAGE
        ma = self.calculate_moving_average(df_historical, CONFIG['PERIODO_MA'])
        ma_distance = ((current_price - ma) / ma) * 100
        analysis['ma'] = ma
        analysis['ma_distance'] = ma_distance

        if ma_distance <= -CONFIG['DISTANCIA_MA']:
            analysis['signals'].append(f"🔴 BELOW MA{CONFIG['PERIODO_MA']}: {ma_distance:.2f}% (minimum: {-CONFIG['DISTANCIA_MA']}%)")
            analysis['score'] += 2

        # 3. RSI
        rsi = self.calculate_rsi(df_historical['close'])
        analysis['rsi'] = rsi

        if rsi < CONFIG['RSI_OVERSOLD']:
            analysis['signals'].append(f"🔴 RSI OVERSOLD: {rsi:.1f} (limit: {CONFIG['RSI_OVERSOLD']})")
            analysis['score'] += 2

        # 4. SUPPORTS AND RESISTANCES
        supports, resistances = self.calculate_support_resistance(df_historical)
        analysis['supports'] = supports
        analysis['resistances'] = resistances

        # Check if near support
        for support in supports:
            diff_support = ((current_price - support) / support) * 100
            if -2 <= diff_support <= 2:  # Within 2% of support
                analysis['signals'].append(f"🟡 NEAR SUPPORT: R$ {support:,.2f}")
                analysis['score'] += 1
                break

        # 5. CALCULATE TARGETS
        # Target = next resistance above current price
        target_resistance = None
        for resistance in sorted(resistances):
            if resistance > current_price:
                target_resistance = resistance
                break

        if target_resistance:
            profit_percent = ((target_resistance - current_price) / current_price) * 100
            if profit_percent >= CONFIG['TAKE_PROFIT']:
                analysis['target_price'] = target_resistance
                analysis['profit_percent'] = profit_percent

        # If no resistance found, use fixed %
        if not analysis['target_price']:
            analysis['target_price'] = current_price * (1 + CONFIG['TAKE_PROFIT'] / 100)
            analysis['profit_percent'] = CONFIG['TAKE_PROFIT']

        # Stop loss
        # Use next support below or fixed %
        stop_support = None
        for support in sorted(supports, reverse=True):
            if support < current_price:
                stop_support = support
                break

        if stop_support:
            stop_percent = ((current_price - stop_support) / current_price) * 100
            if stop_percent <= CONFIG['STOP_LOSS'] * 2:  # If not too far
                analysis['stop_loss'] = stop_support
                analysis['stop_percent'] = stop_percent

        if not analysis['stop_loss']:
            analysis['stop_loss'] = current_price * (1 - CONFIG['STOP_LOSS'] / 100)
            analysis['stop_percent'] = CONFIG['STOP_LOSS']

        # ENTRY SIGNAL
        if analysis['score'] >= 3:  # At least 3 confirmation points
            analysis['entry_signal'] = True

        return analysis

    async def send_telegram_notification(self, analysis: Dict):
        """Send notification via Telegram"""
        if not self.telegram_bot or not TELEGRAM_CHAT_ID:
            return

        try:
            # Format message
            message = f"""
🚨 *BTC/BRL ENTRY SIGNAL DETECTED* 🚨

⏰ Time: {analysis['timestamp']}
💰 Current Price: R$ {analysis['price']:,.2f}

📊 *INDICATORS:*
• MA{CONFIG['PERIODO_MA']}: R$ {analysis['ma']:,.2f} ({analysis['ma_distance']:+.2f}%)
• RSI(14): {analysis['rsi']:.1f}
• Score: {analysis['score']}/7

🔔 *DETECTED SIGNALS:*
"""
            for signal in analysis['signals']:
                message += f"• {signal}\n"

            message += f"""
💡 *TRADE SUGGESTION:*
🔹 ENTRY: R$ {analysis['price']:,.2f}
🎯 TARGET: R$ {analysis['target_price']:,.2f} (+{analysis['profit_percent']:.2f}%)
🛑 STOP LOSS: R$ {analysis['stop_loss']:,.2f} (-{analysis['stop_percent']:.2f}%)

📊 Risk/Reward: 1:{analysis['profit_percent'] / analysis['stop_percent']:.2f}

📍 *KEY LEVELS:*
Resistances: {', '.join([f'R$ {r:,.0f}' for r in analysis['resistances'][:3]])}
Supports: {', '.join([f'R$ {s:,.0f}' for s in analysis['supports'][:3]])}
"""

            # Send message
            await self.telegram_bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            print("✅ Telegram notification sent successfully")

        except TelegramError as e:
            print(f"❌ Error sending Telegram notification: {e}")
        except Exception as e:
            print(f"❌ Unexpected error sending notification: {e}")

    def print_analysis(self, analysis: Dict):
        """Print formatted analysis"""
        print("\n" + "="*80)
        print(f"⏰ {analysis['timestamp']}")
        print(f"💰 CURRENT PRICE: R$ {analysis['price']:,.2f}")
        print("="*80)

        print(f"\n📊 INDICATORS:")
        print(f"   MA{CONFIG['PERIODO_MA']}: R$ {analysis['ma']:,.2f} ({analysis['ma_distance']:+.2f}%)")
        print(f"   RSI(14): {analysis['rsi']:.1f}")

        if analysis['signals']:
            print(f"\n🚨 DETECTED SIGNALS (Score: {analysis['score']}):")
            for signal in analysis['signals']:
                print(f"   {signal}")

        print(f"\n📍 KEY LEVELS:")
        print(f"   Resistances: {', '.join([f'R$ {r:,.0f}' for r in analysis['resistances'][:3]])}")
        print(f"   Supports: {', '.join([f'R$ {s:,.0f}' for s in analysis['supports'][:3]])}")

        if analysis['entry_signal']:
            print(f"\n{'🟢 ENTRY OPPORTUNITY DETECTED! 🟢':^80}")
            print(f"\n💡 TRADE SUGGESTION:")
            print(f"   🔹 ENTRY: R$ {analysis['price']:,.2f}")
            print(f"   🎯 TARGET: R$ {analysis['target_price']:,.2f} (+{analysis['profit_percent']:.2f}%)")
            print(f"   🛑 STOP: R$ {analysis['stop_loss']:,.2f} (-{analysis['stop_percent']:.2f}%)")

            risk_reward = analysis['profit_percent'] / analysis['stop_percent']
            print(f"   📊 RISK/REWARD: 1:{risk_reward:.2f}")
        else:
            print(f"\n⚪ No clear opportunity at the moment (Score: {analysis['score']}/7)")

        print("="*80 + "\n")

    def run_monitor(self):
        """Main monitoring loop"""
        print("🤖 BTC/BRL Monitor Started!")
        print(f"📡 Checking every {CONFIG['INTERVALO_CHECK']} seconds...")
        print(f"⚙️  Settings: Min drop {CONFIG['QUEDA_MINIMA']}%, RSI < {CONFIG['RSI_OVERSOLD']}\n")

        while True:
            try:
                # Fetch data
                current_price = self.get_current_price()
                if not current_price:
                    time.sleep(30)
                    continue

                stats_24h = self.get_24h_change()
                if not stats_24h:
                    time.sleep(30)
                    continue

                # Fetch historical data (only occasionally to save requests)
                df_historical = self.get_historical_klines(CONFIG['DIAS_HISTORICO'])
                if df_historical is None or len(df_historical) == 0:
                    time.sleep(30)
                    continue

                # Analyze
                analysis = self.analyze_opportunity(current_price, stats_24h, df_historical)

                # Print analysis
                self.print_analysis(analysis)

                # Save log and send notification if signal detected
                if analysis['entry_signal']:
                    self.save_signal_log(analysis)

                    # Send Telegram notification
                    if TELEGRAM_ENABLED and self.telegram_bot:
                        asyncio.run(self.send_telegram_notification(analysis))

                # Wait for next check
                time.sleep(CONFIG['INTERVALO_CHECK'])

            except KeyboardInterrupt:
                print("\n👋 Monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                time.sleep(60)

    def save_signal_log(self, analysis: Dict):
        """Save signals to log file"""
        log_file = 'signals_log.json'

        try:
            # Load existing logs
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []

            # Add new signal
            logs.append(analysis)

            # Save
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)

            print(f"💾 Signal saved to {log_file}")

        except Exception as e:
            print(f"❌ Error saving log: {e}")

def main():
    monitor = BinanceMonitor()
    monitor.run_monitor()

if __name__ == "__main__":
    main()
