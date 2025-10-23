"""
Pytest fixtures and helper functions for strategy tests

Provides mock market data and scenarios without external dependencies.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def create_mock_historical_data(
    days: int = 90,
    base_price: float = 100000,
    trend: str = "neutral",
    volatility: float = 0.02
) -> pd.DataFrame:
    """
    Create mock historical OHLC data for testing

    Args:
        days: Number of days of data
        base_price: Starting price
        trend: "up", "down", "neutral", "volatile"
        volatility: Daily price variation (0.02 = 2%)

    Returns:
        DataFrame with date, open, high, low, close, volume
    """
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # Generate price trend
    if trend == "up":
        trend_component = np.linspace(0, 0.2, days)  # +20% over period
    elif trend == "down":
        trend_component = np.linspace(0, -0.2, days)  # -20% over period
    elif trend == "volatile":
        trend_component = np.sin(np.linspace(0, 4 * np.pi, days)) * 0.1
    else:  # neutral
        trend_component = np.zeros(days)

    # Generate random price movements
    np.random.seed(42)  # Reproducible tests
    random_moves = np.random.randn(days) * volatility

    # Calculate prices
    price_multipliers = 1 + trend_component + random_moves
    prices = base_price * np.cumprod(price_multipliers)

    # Generate OHLC data
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        # Generate realistic OHLC
        daily_range = close * volatility
        high = close + abs(np.random.randn() * daily_range)
        low = close - abs(np.random.randn() * daily_range)
        open_price = close + np.random.randn() * daily_range * 0.5
        volume = np.random.uniform(1000, 5000)

        data.append({
            'date': date,
            'open': open_price,
            'high': max(high, close, open_price),
            'low': min(low, close, open_price),
            'close': close,
            'volume': volume
        })

    return pd.DataFrame(data)


def create_mock_stats_24h(price_change_percent: float = -5.0) -> dict:
    """
    Create mock 24h statistics

    Args:
        price_change_percent: 24h price change percentage

    Returns:
        Dictionary with 24h stats
    """
    return {
        'price_change_percent': price_change_percent,
        'high': 105000,
        'low': 95000,
        'volume': 50000
    }


def create_price_with_indicators(
    current_price: float,
    ma_value: float,
    rsi_value: float,
    supports: list = None,
    resistances: list = None
) -> pd.DataFrame:
    """
    Create historical data that will produce specific indicator values

    Args:
        current_price: Current price
        ma_value: Desired moving average value
        rsi_value: Desired RSI value (0-100)
        supports: List of support levels
        resistances: List of resistance levels

    Returns:
        DataFrame configured to produce desired indicators
    """
    days = 90

    # Create prices that will result in desired MA
    # Recent prices oscillate around MA target
    prices = []
    for i in range(days - 7):
        prices.append(ma_value * (1 + np.random.randn() * 0.01))

    # Last 7 days adjust to hit target MA
    # MA = average of last 7 days
    sum_needed = ma_value * 7
    sum_so_far = sum(prices[-6:]) if len(prices) >= 6 else 0
    prices.append(sum_needed - sum_so_far)

    # Adjust for RSI (simplified - last price determines RSI trend)
    if rsi_value < 30:  # Oversold - recent downtrend
        for i in range(len(prices) - 14, len(prices)):
            prices[i] *= (1 - 0.02)  # Gradual decline
    elif rsi_value > 70:  # Overbought - recent uptrend
        for i in range(len(prices) - 14, len(prices)):
            prices[i] *= (1 + 0.02)  # Gradual increase

    # Set last price to current price
    prices[-1] = current_price

    # Build DataFrame
    dates = pd.date_range(end=datetime.now(), periods=len(prices), freq='D')
    data = []

    for date, close in zip(dates, prices):
        daily_range = close * 0.01
        data.append({
            'date': date,
            'open': close,
            'high': close + abs(np.random.randn() * daily_range),
            'low': close - abs(np.random.randn() * daily_range),
            'close': close,
            'volume': 1000
        })

    # Add support/resistance levels to the data
    if supports:
        for support in supports:
            # Add historical touches at support
            idx = np.random.randint(0, len(data) - 20)
            data[idx]['low'] = support
            data[idx]['close'] = support * 1.002

    if resistances:
        for resistance in resistances:
            # Add historical touches at resistance
            idx = np.random.randint(0, len(data) - 20)
            data[idx]['high'] = resistance
            data[idx]['close'] = resistance * 0.998

    return pd.DataFrame(data)


# Pytest Fixtures

@pytest.fixture
def scenario_strong_buy():
    """
    Strong buy signal scenario:
    - Price drop -6% (triggers)
    - RSI 25 (triggers)
    - Below MA by -4% (triggers)
    """
    current_price = 100000
    ma_value = 104166.67  # 4% above current

    df = create_price_with_indicators(
        current_price=current_price,
        ma_value=ma_value,
        rsi_value=25,
        supports=[96000, 93000, 90000],
        resistances=[108000, 112000, 115000]
    )

    stats_24h = create_mock_stats_24h(price_change_percent=-6.0)

    return current_price, stats_24h, df


@pytest.fixture
def scenario_no_signal():
    """
    No signal scenario:
    - Price drop -2% (doesn't trigger)
    - RSI 50 (neutral)
    - Near MA (doesn't trigger)
    """
    current_price = 100000
    ma_value = 100500  # Only 0.5% difference

    df = create_price_with_indicators(
        current_price=current_price,
        ma_value=ma_value,
        rsi_value=50,
        supports=[96000],
        resistances=[104000]
    )

    stats_24h = create_mock_stats_24h(price_change_percent=-2.0)

    return current_price, stats_24h, df


@pytest.fixture
def scenario_partial_signal():
    """
    Partial signal scenario:
    - Price drop -5.5% (triggers, score=3)
    - RSI 40 (doesn't trigger)
    - Below MA by -2% (doesn't trigger)
    """
    current_price = 100000
    ma_value = 102040  # 2% above current

    df = create_price_with_indicators(
        current_price=current_price,
        ma_value=ma_value,
        rsi_value=40,
        supports=[97000],
        resistances=[105000]
    )

    stats_24h = create_mock_stats_24h(price_change_percent=-5.5)

    return current_price, stats_24h, df


@pytest.fixture
def scenario_conservative_target():
    """
    Scenario to test conservative target calculation:
    - Current: $100,000
    - Next resistance: $110,000 (+10%)
    - Expected target: ~$106,000 (60% distance) or $105,000 (5% cap)
    """
    current_price = 100000
    ma_value = 99000

    df = create_price_with_indicators(
        current_price=current_price,
        ma_value=ma_value,
        rsi_value=28,
        supports=[96000, 92000],
        resistances=[110000, 115000, 120000]
    )

    stats_24h = create_mock_stats_24h(price_change_percent=-5.5)

    return current_price, stats_24h, df


@pytest.fixture
def scenario_near_support():
    """
    Scenario where price is near support level:
    - Current: $100,000
    - Support at $99,000 (1% below)
    - Should trigger "NEAR SUPPORT" signal
    """
    current_price = 100000
    ma_value = 102000

    df = create_price_with_indicators(
        current_price=current_price,
        ma_value=ma_value,
        rsi_value=32,
        supports=[99000, 95000, 91000],  # First support at 1% below
        resistances=[105000, 110000]
    )

    stats_24h = create_mock_stats_24h(price_change_percent=-3.0)

    return current_price, stats_24h, df
