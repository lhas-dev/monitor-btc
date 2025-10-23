"""
Backtest report formatting

Contains all backtest analysis report formatting functions.
"""

import pandas as pd
from typing import List, Dict


def format_header() -> str:
    """
    Format backtest header banner

    Returns:
        Formatted header string
    """
    return """
    ╔═══════════════════════════════════════════════════════════╗
    ║      📊 BTC HISTORICAL ANALYSIS - BUY THE DIP STRATEGY    ║
    ║              Multiple Detection Methods                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """


def format_backtest_startup_info(symbol: str, days: int, min_drop: float) -> str:
    """
    Format backtest startup information

    Args:
        symbol: Trading symbol
        days: Number of days to analyze
        min_drop: Minimum drop percentage

    Returns:
        Formatted startup information
    """
    output = "\n🚀 STARTING HISTORICAL ANALYSIS\n\n"
    output += f"Symbol: {symbol}\n"
    output += f"Period: {days} days\n"
    output += f"Min drop: {min_drop}%\n"
    return output


def format_statistics(results: List[Dict]) -> str:
    """
    Format comprehensive backtest statistics

    Args:
        results: List of drop analysis results

    Returns:
        Formatted statistics string
    """
    if len(results) == 0:
        return "❌ No drops found in period"

    df_results = pd.DataFrame(results)
    df_complete = df_results[df_results['max_gain_days'].notna()]

    output = "="*80 + "\n"
    output += "📊 'BUY THE DIP' STRATEGY STATISTICS\n"
    output += "="*80 + "\n"

    output += f"\n📉 DROPS ANALYZED:\n"
    output += f"   Total drops: {len(df_results)}\n"
    output += f"   Average drop: {df_results['drop_percent'].mean():.2f}%\n"
    output += f"   Largest drop: {df_results['drop_percent'].min():.2f}%\n"

    # By type
    if 'tipo' in df_results.columns:
        output += f"\n📊 DROPS BY TYPE:\n"
        for tipo in df_results['tipo'].unique():
            count = len(df_results[df_results['tipo'] == tipo])
            output += f"   {tipo}: {count}\n"

    output += f"\n📈 RECOVERY:\n"
    recovered = df_results['recovered'].sum()
    recovery_rate = (recovered / len(df_results)) * 100
    output += f"   Recovery rate: {recovery_rate:.1f}% ({recovered}/{len(df_results)})\n"

    if recovered > 0:
        df_recovered = df_results[df_results['recovered'] == True]
        output += f"   Average time: {df_recovered['recovery_days'].mean():.1f} days\n"
        output += f"   Fastest: {df_recovered['recovery_days'].min():.0f} days\n"
        output += f"   Slowest: {df_recovered['recovery_days'].max():.0f} days\n"

    if len(df_complete) > 0:
        output += f"\n💰 POTENTIAL GAINS (7 days after):\n"
        output += f"   Average gain: {df_complete['max_gain_percent'].mean():.2f}%\n"
        output += f"   Largest gain: {df_complete['max_gain_percent'].max():.2f}%\n"
        output += f"   Smallest: {df_complete['max_gain_percent'].min():.2f}%\n"

        # Win rate by thresholds
        for threshold in [1.0, 2.0, 3.0]:
            winning = (df_complete['max_gain_percent'] >= threshold).sum()
            win_rate = (winning / len(df_complete)) * 100
            output += f"\n🎯 WIN RATE (profit ≥{threshold}%):\n"
            output += f"   {win_rate:.1f}% ({winning}/{len(df_complete)})\n"

    output += "\n" + "="*80 + "\n"
    return output


def format_recent_opportunities(results: List[Dict], n: int = 10) -> str:
    """
    Format recent detected drops

    Args:
        results: List of drop analysis results
        n: Number of recent opportunities to show

    Returns:
        Formatted recent opportunities string
    """
    if len(results) == 0:
        return ""

    df_results = pd.DataFrame(results)
    recent = df_results.tail(n)

    output = f"\n📅 LAST {min(n, len(results))} DETECTED DROPS:\n"
    output += "="*80 + "\n"

    for idx, row in recent.iterrows():
        output += f"\n📅 {row['date']} [{row.get('tipo', 'N/A')}]\n"
        output += f"   💸 Price: ${row['drop_price']:,.2f}\n"
        output += f"   📉 Drop: {row['drop_percent']:.2f}%\n"

        if row['recovered']:
            output += f"   ✅ Recovered in {row['recovery_days']:.0f} days\n"

        if pd.notna(row['max_gain_percent']):
            output += f"   📈 Max gain: {row['max_gain_percent']:.2f}% in {row['max_gain_days']:.0f} days\n"

    output += "\n" + "="*80 + "\n"
    return output


def format_error_no_data() -> str:
    """
    Format error message for when no data is available

    Returns:
        Formatted error message
    """
    output = "\n❌ Unable to obtain data\n"
    output += "💡 Possible causes:\n"
    output += "   - Binance API temporarily unavailable\n"
    output += "   - Request limit reached\n"
    output += "   - Connection problems\n"
    return output


def format_no_drops_found(min_drop: float) -> str:
    """
    Format message when no drops are found

    Args:
        min_drop: Minimum drop percentage threshold

    Returns:
        Formatted message
    """
    output = f"\n💡 No drops of {min_drop}%+ detected.\n"
    output += f"   Try lowering the threshold (e.g. 3% or 4%)\n"
    return output


def format_completion_message() -> str:
    """
    Format backtest completion message

    Returns:
        Formatted completion message
    """
    output = "\n✅ Analysis complete!\n"
    output += "💡 Use these statistics to adjust your .env settings\n"
    return output
