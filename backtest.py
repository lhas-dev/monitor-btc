"""
BTC Backtest - Historical analysis of Buy the Dip strategy
Multiple drop detection methods with recovery analysis
"""

import pandas as pd
from typing import List, Dict
from btc_monitor.binance_api import BinanceClient
from btc_monitor.indicators import find_drops_advanced
from btc_monitor import settings
from btc_monitor.views.backtest import (
    format_header,
    format_backtest_startup_info,
    format_statistics,
    format_recent_opportunities,
    format_error_no_data,
    format_no_drops_found,
    format_completion_message
)


def analyze_recovery(df: pd.DataFrame, drops: pd.DataFrame, days_ahead: int = 7) -> List[Dict]:
    """Analyze price recovery after drops"""
    results = []

    for idx, drop_row in drops.iterrows():
        drop_date = drop_row['date']
        drop_price = drop_row['close']
        drop_change = drop_row['change_close']
        drop_tipo = drop_row.get('tipo', 'Unknown')

        # Get following days
        future_data = df[df['date'] > drop_date].head(days_ahead)

        if len(future_data) == 0:
            continue

        # Find recovery
        recovery_day = None
        recovery_price = None
        max_gain = 0
        max_gain_day = None

        for future_idx, future_row in future_data.iterrows():
            days_passed = (future_row['date'] - drop_date).days
            current_price = future_row['close']
            gain = ((current_price - drop_price) / drop_price) * 100

            if recovery_day is None and current_price > drop_price:
                recovery_day = days_passed
                recovery_price = current_price

            if gain > max_gain:
                max_gain = gain
                max_gain_day = days_passed

        results.append({
            'date': drop_date,
            'tipo': drop_tipo,
            'drop_percent': drop_change,
            'drop_price': drop_price,
            'recovery_days': recovery_day,
            'recovery_price': recovery_price,
            'max_gain_percent': max_gain,
            'max_gain_days': max_gain_day,
            'recovered': recovery_day is not None
        })

    return results


def print_statistics(results: List[Dict]):
    """Print comprehensive statistics"""
    output = format_statistics(results)
    print(output, end="")

    if len(results) > 0:
        return pd.DataFrame(results)
    return None


def print_recent_opportunities(results: List[Dict], n: int = 10):
    """Show recent detected drops"""
    output = format_recent_opportunities(results, n)
    print(output, end="")


def run_backtest(days: int = 180, min_drop: float = None):
    """Execute complete backtest analysis"""
    if min_drop is None:
        min_drop = settings.MIN_DROP

    # Print startup info
    startup_info = format_backtest_startup_info(settings.SYMBOL, days, min_drop)
    print(startup_info)

    # Initialize client
    client = BinanceClient(symbol=settings.SYMBOL, base_url="https://api.binance.com")

    # Fetch historical data
    print(f"📥 Downloading {days} days of historical data...")
    df = client.get_historical_with_retry(days)

    if df is None or len(df) == 0:
        print(format_error_no_data())
        return None, None

    print(f"✅ {len(df)} days downloaded\n")

    # Find drops
    drops = find_drops_advanced(df, min_drop)

    if len(drops) == 0:
        print(format_no_drops_found(min_drop))
        return df, None

    print(f"🔍 Found {len(drops)} drops of {min_drop}%+ using multiple methods\n")

    # Analyze recovery
    print(f"⏳ Analyzing drop recovery...\n")
    results = analyze_recovery(df, drops)

    # Print statistics
    df_results = print_statistics(results)

    # Recent opportunities
    print_recent_opportunities(results)

    return df, df_results


def main():
    # Print header
    print(format_header())

    # Try with configured threshold
    df, results = run_backtest(days=180)

    # If no results, try with 3%
    if results is None and df is not None:
        print("\n🔄 Trying again with 3% threshold...\n")
        drops = find_drops_advanced(df, min_drop=3.0)
        if len(drops) > 0:
            results_list = analyze_recovery(df, drops)
            print_statistics(results_list)
            print_recent_opportunities(results_list)

    if df is not None:
        print(format_completion_message())


if __name__ == "__main__":
    main()
