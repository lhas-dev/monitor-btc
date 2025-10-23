"""
BTC Backtest - Historical analysis of Buy the Dip strategy
Multiple drop detection methods with recovery analysis
"""

import pandas as pd
from typing import List, Dict
from btc_monitor.binance_api import BinanceClient
from btc_monitor.indicators import find_drops_advanced
from btc_monitor import settings


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
    if len(results) == 0:
        print("❌ No drops found in period")
        return

    df_results = pd.DataFrame(results)
    df_complete = df_results[df_results['max_gain_days'].notna()]

    print("="*80)
    print("📊 'BUY THE DIP' STRATEGY STATISTICS")
    print("="*80)

    print(f"\n📉 DROPS ANALYZED:")
    print(f"   Total drops: {len(df_results)}")
    print(f"   Average drop: {df_results['drop_percent'].mean():.2f}%")
    print(f"   Largest drop: {df_results['drop_percent'].min():.2f}%")

    # By type
    if 'tipo' in df_results.columns:
        print(f"\n📊 DROPS BY TYPE:")
        for tipo in df_results['tipo'].unique():
            count = len(df_results[df_results['tipo'] == tipo])
            print(f"   {tipo}: {count}")

    print(f"\n📈 RECOVERY:")
    recovered = df_results['recovered'].sum()
    recovery_rate = (recovered / len(df_results)) * 100
    print(f"   Recovery rate: {recovery_rate:.1f}% ({recovered}/{len(df_results)})")

    if recovered > 0:
        df_recovered = df_results[df_results['recovered'] == True]
        print(f"   Average time: {df_recovered['recovery_days'].mean():.1f} days")
        print(f"   Fastest: {df_recovered['recovery_days'].min():.0f} days")
        print(f"   Slowest: {df_recovered['recovery_days'].max():.0f} days")

    if len(df_complete) > 0:
        print(f"\n💰 POTENTIAL GAINS (7 days after):")
        print(f"   Average gain: {df_complete['max_gain_percent'].mean():.2f}%")
        print(f"   Largest gain: {df_complete['max_gain_percent'].max():.2f}%")
        print(f"   Smallest: {df_complete['max_gain_percent'].min():.2f}%")

        # Win rate by thresholds
        for threshold in [1.0, 2.0, 3.0]:
            winning = (df_complete['max_gain_percent'] >= threshold).sum()
            win_rate = (winning / len(df_complete)) * 100
            print(f"\n🎯 WIN RATE (profit ≥{threshold}%):")
            print(f"   {win_rate:.1f}% ({winning}/{len(df_complete)})")

    print("\n" + "="*80)
    return df_results


def print_recent_opportunities(results: List[Dict], n: int = 10):
    """Show recent detected drops"""
    if len(results) == 0:
        return

    print(f"\n📅 LAST {min(n, len(results))} DETECTED DROPS:")
    print("="*80)

    df_results = pd.DataFrame(results)
    recent = df_results.tail(n)

    for idx, row in recent.iterrows():
        print(f"\n📅 {row['date']} [{row.get('tipo', 'N/A')}]")
        print(f"   💸 Price: ${row['drop_price']:,.2f}")
        print(f"   📉 Drop: {row['drop_percent']:.2f}%")

        if row['recovered']:
            print(f"   ✅ Recovered in {row['recovery_days']:.0f} days")

        if pd.notna(row['max_gain_percent']):
            print(f"   📈 Max gain: {row['max_gain_percent']:.2f}% in {row['max_gain_days']:.0f} days")

    print("\n" + "="*80)


def run_backtest(days: int = 180, min_drop: float = None):
    """Execute complete backtest analysis"""
    if min_drop is None:
        min_drop = settings.MIN_DROP

    print("\n🚀 STARTING HISTORICAL ANALYSIS\n")
    print(f"Symbol: {settings.SYMBOL}")
    print(f"Period: {days} days")
    print(f"Min drop: {min_drop}%\n")

    # Initialize client
    client = BinanceClient(symbol=settings.SYMBOL, base_url="https://api.binance.com")

    # Fetch historical data
    print(f"📥 Downloading {days} days of historical data...")
    df = client.get_historical_with_retry(days)

    if df is None or len(df) == 0:
        print("\n❌ Unable to obtain data")
        print("💡 Possible causes:")
        print("   - Binance API temporarily unavailable")
        print("   - Request limit reached")
        print("   - Connection problems")
        return None, None

    print(f"✅ {len(df)} days downloaded\n")

    # Find drops
    drops = find_drops_advanced(df, min_drop)

    if len(drops) == 0:
        print(f"\n💡 No drops of {min_drop}%+ detected.")
        print(f"   Try lowering the threshold (e.g. 3% or 4%)")
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
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║      📊 BTC HISTORICAL ANALYSIS - BUY THE DIP STRATEGY    ║
    ║              Multiple Detection Methods                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

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
        print("\n✅ Analysis complete!")
        print("💡 Use these statistics to adjust your .env settings")


if __name__ == "__main__":
    main()
