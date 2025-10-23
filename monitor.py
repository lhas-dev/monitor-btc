"""
BTC Monitor - Main monitoring script
Buy the Dip strategy with technical indicators
Supports multiple symbols in parallel
"""

import asyncio
from btc_monitor.binance_api import BinanceClient
from btc_monitor.indicators import analyze_opportunity
from btc_monitor.telegram_bot import TelegramNotifier
from btc_monitor.storage import SignalStorage
from btc_monitor import settings
from btc_monitor.views.console import format_analysis, format_startup_info, format_telegram_status


def print_analysis(analysis: dict, symbol: str):
    """Print formatted analysis to console"""
    output = format_analysis(analysis, settings.MA_PERIOD)
    # Prefix with symbol for multi-symbol monitoring
    print(f"[{symbol}] ", end="")
    print(output, end="")


async def monitor_symbol(symbol: str, telegram: TelegramNotifier = None):
    """
    Monitor a single symbol continuously

    Args:
        symbol: Trading symbol to monitor (e.g., BTCUSDT)
        telegram: Shared TelegramNotifier instance
    """
    print(f"\n🚀 Starting monitor for {symbol}")

    # Initialize components for this symbol
    client = BinanceClient(symbol=symbol)
    storage = SignalStorage(symbol=symbol)

    while True:
        try:
            # Fetch current data
            current_price = client.get_current_price()
            if not current_price:
                await asyncio.sleep(30)
                continue

            stats_24h = client.get_24h_stats()
            if not stats_24h:
                await asyncio.sleep(30)
                continue

            # Fetch historical data
            df_historical = client.get_historical_klines(settings.HISTORICAL_DAYS)
            if df_historical is None or len(df_historical) == 0:
                await asyncio.sleep(30)
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
                take_profit=settings.TAKE_PROFIT,
                max_take_profit=settings.MAX_TAKE_PROFIT,
                resistance_factor=settings.RESISTANCE_FACTOR
            )

            # Print analysis
            print_analysis(analysis, symbol)

            # Save and notify if signal detected
            if analysis['entry_signal']:
                storage.save_signal(analysis)

                if telegram:
                    await telegram.send_trade_signal(
                        analysis,
                        symbol,
                        settings.MA_PERIOD
                    )
                    print(f"[{symbol}] ✅ Telegram notification sent")

            # Wait for next check
            await asyncio.sleep(settings.CHECK_INTERVAL)

        except asyncio.CancelledError:
            print(f"\n[{symbol}] 👋 Monitor stopped")
            break
        except Exception as e:
            print(f"[{symbol}] ❌ Error in monitoring loop: {e}")
            await asyncio.sleep(60)


async def run_monitor_async():
    """Main monitoring coordinator for all symbols"""
    # Print startup info
    symbols_str = ", ".join(settings.SYMBOLS)
    print(f"\n{'='*60}")
    print(f"🤖 Multi-Symbol Crypto Monitor")
    print(f"{'='*60}")
    print(f"📊 Monitoring symbols: {symbols_str}")
    print(f"⏱️  Check interval: {settings.CHECK_INTERVAL}s")
    print(f"📉 Min drop threshold: {settings.MIN_DROP}%")
    print(f"📈 RSI oversold: {settings.RSI_OVERSOLD}")
    print(f"{'='*60}")

    # Initialize telegram (shared across all symbols)
    telegram = None
    if settings.TELEGRAM_ENABLED:
        telegram = TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
        telegram_status = format_telegram_status(telegram.is_enabled() if telegram else False)
        print(telegram_status)
        if not telegram.is_enabled():
            telegram = None
    else:
        print(format_telegram_status(False))

    # Create monitoring tasks for each symbol
    tasks = []
    for symbol in settings.SYMBOLS:
        task = asyncio.create_task(monitor_symbol(symbol, telegram))
        tasks.append(task)

    # Run all tasks concurrently
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down all monitors...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def run_monitor():
    """Entry point - runs the async monitor"""
    try:
        asyncio.run(run_monitor_async())
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")


if __name__ == "__main__":
    run_monitor()
