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
from btc_monitor.views.console import format_analysis, format_startup_info, format_telegram_status


def print_analysis(analysis: dict):
    """Print formatted analysis to console"""
    output = format_analysis(analysis, settings.MA_PERIOD)
    print(output, end="")


def run_monitor():
    """Main monitoring loop"""
    # Print startup info
    startup_info = format_startup_info(
        settings.SYMBOL,
        settings.CHECK_INTERVAL,
        settings.MIN_DROP,
        settings.RSI_OVERSOLD
    )
    print(startup_info)

    # Initialize components
    client = BinanceClient(symbol=settings.SYMBOL)
    storage = SignalStorage()
    telegram = None

    if settings.TELEGRAM_ENABLED:
        telegram = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
        telegram_status = format_telegram_status(telegram.is_enabled() if telegram else False)
        print(telegram_status)
        if not telegram.is_enabled():
            telegram = None
    else:
        print(format_telegram_status(False))

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
