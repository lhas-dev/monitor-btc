"""
BTC Monitor - Main monitoring script
Buy the Dip strategy with technical indicators
"""

import time
import asyncio
from btc_monitor.binance_api import BinanceClient
from btc_monitor.indicators import analyze_opportunity
from btc_monitor.telegram_bot import TelegramNotifier
from btc_monitor.storage import SignalStorage
from btc_monitor import settings


def print_analysis(analysis: dict):
    """Print formatted analysis to console"""
    print("\n" + "="*80)
    print(f"⏰ {analysis['timestamp']}")
    print(f"💰 CURRENT PRICE: USD {analysis['price']:,.2f}")
    print("="*80)

    print(f"\n📊 INDICATORS:")
    print(f"   MA{settings.MA_PERIOD}: USD {analysis['ma']:,.2f} ({analysis['ma_distance']:+.2f}%)")
    print(f"   RSI(14): {analysis['rsi']:.1f}")

    if analysis['signals']:
        print(f"\n🚨 DETECTED SIGNALS (Score: {analysis['score']}):")
        for signal in analysis['signals']:
            print(f"   {signal}")

    print(f"\n📍 KEY LEVELS:")
    print(f"   Resistances: {', '.join([f'USD {r:,.0f}' for r in analysis['resistances'][:3]])}")
    print(f"   Supports: {', '.join([f'USD {s:,.0f}' for s in analysis['supports'][:3]])}")

    if analysis['entry_signal']:
        print(f"\n{'🟢 ENTRY OPPORTUNITY DETECTED! 🟢':^80}")
        print(f"\n💡 TRADE SUGGESTION:")
        print(f"   🔹 ENTRY: USD {analysis['price']:,.2f}")
        print(f"   🎯 TARGET: USD {analysis['target_price']:,.2f} (+{analysis['profit_percent']:.2f}%)")
        print(f"   🛑 STOP: USD {analysis['stop_loss']:,.2f} (-{analysis['stop_percent']:.2f}%)")

        risk_reward = analysis['profit_percent'] / analysis['stop_percent']
        print(f"   📊 RISK/REWARD: 1:{risk_reward:.2f}")
    else:
        print(f"\n⚪ No clear opportunity at the moment (Score: {analysis['score']}/7)")

    print("="*80 + "\n")


def run_monitor():
    """Main monitoring loop"""
    print("🤖 BTC Monitor Started!")
    print(f"📡 Symbol: {settings.SYMBOL}")
    print(f"📡 Checking every {settings.CHECK_INTERVAL} seconds...")
    print(f"⚙️  Settings: Min drop {settings.MIN_DROP}%, RSI < {settings.RSI_OVERSOLD}")

    # Initialize components
    client = BinanceClient(symbol=settings.SYMBOL)
    storage = SignalStorage()
    telegram = None

    if settings.TELEGRAM_ENABLED:
        telegram = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
        if telegram.is_enabled():
            print("✅ Telegram notifications enabled")
        else:
            print("⚠️ Telegram not configured properly")
            telegram = None

    print()

    while True:
        try:
            # Fetch current data
            current_price = client.get_current_price()
            if not current_price:
                time.sleep(30)
                continue

            stats_24h = client.get_24h_stats()
            if not stats_24h:
                time.sleep(30)
                continue

            # Fetch historical data
            df_historical = client.get_historical_klines(settings.HISTORICAL_DAYS)
            if df_historical is None or len(df_historical) == 0:
                time.sleep(30)
                continue

            # Analyze opportunity
            analysis = analyze_opportunity(
                current_price=current_price,
                stats_24h=stats_24h,
                df_historical=df_historical,
                min_drop=settings.MIN_DROP,
                ma_distance=settings.MA_DISTANCE,
                rsi_oversold=settings.RSI_OVERSOLD,
                ma_period=settings.MA_PERIOD,
                stop_loss=settings.STOP_LOSS,
                take_profit=settings.TAKE_PROFIT
            )

            # Print analysis
            print_analysis(analysis)

            # Save and notify if signal detected
            if analysis['entry_signal']:
                storage.save_signal(analysis)

                if telegram:
                    asyncio.run(telegram.send_trade_signal(
                        analysis,
                        settings.SYMBOL,
                        settings.MA_PERIOD
                    ))
                    print("✅ Telegram notification sent")

            # Wait for next check
            time.sleep(settings.CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n👋 Monitor stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(60)


if __name__ == "__main__":
    run_monitor()
