"""
Technical indicators and analysis functions
RSI, Moving Average, Support/Resistance detection
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Tuple, List


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate RSI (Relative Strength Index) using pandas_ta"""
    rsi = ta.rsi(prices, length=period)
    return rsi.iloc[-1]


def calculate_moving_average(df: pd.DataFrame, period: int) -> float:
    """Calculate simple moving average using pandas_ta"""
    sma = ta.sma(df['close'], length=period)
    return sma.iloc[-1]


def calculate_support_resistance(df: pd.DataFrame, tolerance: float = 0.02) -> Tuple[List[float], List[float]]:
    """
    Identify support and resistance levels based on price touches

    Args:
        df: DataFrame with OHLC data
        tolerance: Percentage tolerance to group nearby levels (default 2%)

    Returns:
        Tuple of (supports, resistances) as lists
    """
    highs = df['high'].values
    lows = df['low'].values

    def cluster_levels(levels, tolerance):
        """Group nearby price levels"""
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

    # Cluster high and low levels
    all_highs = cluster_levels(highs.tolist(), tolerance)
    all_lows = cluster_levels(lows.tolist(), tolerance)

    # Get top 5 resistance and support levels
    resistances = sorted(all_highs, reverse=True)[:5]
    supports = sorted(all_lows, reverse=True)[:5]

    return supports, resistances


def find_drops_advanced(df: pd.DataFrame, min_drop: float = 5.0) -> pd.DataFrame:
    """
    Detect price drops using multiple methods:
    1. Close-to-close (daily change)
    2. Peak-to-valley (drawdown from recent high)
    3. Intraday (high to low same day)

    Args:
        df: DataFrame with OHLC data
        min_drop: Minimum drop percentage to detect

    Returns:
        DataFrame with detected drops
    """
    # Method 1: Close to close
    df['change_close'] = df['close'].pct_change() * 100
    drops_close = df[df['change_close'] <= -min_drop].copy()
    drops_close['tipo'] = 'Close-to-Close'

    # Method 2: Drawdown from peak
    df['rolling_max'] = df['high'].rolling(window=30, min_periods=1).max()
    df['drawdown'] = ((df['low'] - df['rolling_max']) / df['rolling_max']) * 100
    drops_drawdown = df[df['drawdown'] <= -min_drop].copy()
    drops_drawdown['tipo'] = 'Peak-to-Valley'
    drops_drawdown['change_close'] = drops_drawdown['drawdown']

    # Method 3: Intraday
    df['change_intraday'] = ((df['low'] - df['high']) / df['high']) * 100
    drops_intraday = df[df['change_intraday'] <= -min_drop].copy()
    drops_intraday['tipo'] = 'Intraday'
    drops_intraday['change_close'] = drops_intraday['change_intraday']

    # Combine and remove duplicates by date
    all_drops = pd.concat([drops_close, drops_drawdown, drops_intraday])

    if len(all_drops) > 0:
        all_drops = all_drops.sort_values('change_close').groupby('date').first().reset_index()

    return all_drops


def analyze_opportunity(current_price: float, stats_24h: dict, df_historical: pd.DataFrame,
                       min_drop: float, ma_distance: float, rsi_oversold: int,
                       ma_period: int, stop_loss: float, take_profit: float,
                       max_take_profit: float = 5.0, resistance_factor: float = 0.6) -> dict:
    """
    Analyze if there's a trading opportunity based on indicators

    Returns:
        Dictionary with analysis results and signals
    """
    analysis = {
        'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'price': current_price,
        'signals': [],
        'entry_signal': False,
        'target_price': None,
        'stop_loss': None,
        'score': 0
    }

    # 1. Check 24h drop
    drop_24h = stats_24h['price_change_percent']
    if drop_24h <= -min_drop:
        analysis['signals'].append(f"🔴 24H DROP: {drop_24h:.2f}% (minimum: {-min_drop}%)")
        analysis['score'] += 3

    # 2. Check moving average
    ma = calculate_moving_average(df_historical, ma_period)
    ma_dist = ((current_price - ma) / ma) * 100
    analysis['ma'] = ma
    analysis['ma_distance'] = ma_dist

    if ma_dist <= -ma_distance:
        analysis['signals'].append(f"🔴 BELOW MA{ma_period}: {ma_dist:.2f}% (minimum: {-ma_distance}%)")
        analysis['score'] += 2

    # 3. Check RSI
    rsi = calculate_rsi(df_historical['close'])
    analysis['rsi'] = rsi

    if rsi < rsi_oversold:
        analysis['signals'].append(f"🔴 RSI OVERSOLD: {rsi:.1f} (limit: {rsi_oversold})")
        analysis['score'] += 2

    # 4. Support and Resistance levels
    supports, resistances = calculate_support_resistance(df_historical)
    analysis['supports'] = supports
    analysis['resistances'] = resistances

    # Check if near support
    for support in supports:
        diff_support = ((current_price - support) / support) * 100
        if -2 <= diff_support <= 2:  # Within 2% of support
            analysis['signals'].append(f"🟡 NEAR SUPPORT: USD {support:,.2f}")
            analysis['score'] += 1
            break

    # 5. Calculate target price (hybrid approach: partial resistance + cap)
    target_resistance = None
    for resistance in sorted(resistances):
        if resistance > current_price:
            target_resistance = resistance
            break

    if target_resistance:
        # Calculate distance to resistance
        distance_to_resistance = target_resistance - current_price

        # Use partial distance (default 60%)
        partial_target = current_price + (distance_to_resistance * resistance_factor)

        # Apply maximum profit cap
        max_target = current_price * (1 + max_take_profit / 100)
        final_target = min(partial_target, max_target)
        final_profit = ((final_target - current_price) / current_price) * 100

        # Only use if meets minimum threshold
        if final_profit >= take_profit:
            analysis['target_price'] = final_target
            analysis['profit_percent'] = final_profit

    # If no resistance found or target too low, use capped percentage
    if not analysis['target_price']:
        # Use minimum of (TAKE_PROFIT or MAX_TAKE_PROFIT)
        target_percent = min(take_profit, max_take_profit)
        analysis['target_price'] = current_price * (1 + target_percent / 100)
        analysis['profit_percent'] = target_percent

    # 6. Calculate stop loss (next support or fixed %)
    stop_support = None
    for support in sorted(supports, reverse=True):
        if support < current_price:
            stop_support = support
            break

    if stop_support:
        stop_percent = ((current_price - stop_support) / current_price) * 100
        if stop_percent <= stop_loss * 2:
            analysis['stop_loss'] = stop_support
            analysis['stop_percent'] = stop_percent

    if not analysis['stop_loss']:
        analysis['stop_loss'] = current_price * (1 - stop_loss / 100)
        analysis['stop_percent'] = stop_loss

    # Entry signal if score >= 3
    if analysis['score'] >= 3:
        analysis['entry_signal'] = True

    return analysis
