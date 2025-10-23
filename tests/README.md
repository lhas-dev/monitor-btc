# BTC Monitor - Unit Tests

Simple unit tests for the trading strategy calculation logic.

## Overview

These tests focus on validating the **strategy calculation** without external dependencies:

- ✅ Signal generation (entry signal detection)
- ✅ Conservative target calculation (hybrid approach)
- ✅ Stop loss calculation
- ✅ Risk/reward ratios
- ✅ Indicator calculations (RSI, MA, Support/Resistance)

**What's NOT tested** (by design):

- ❌ Binance API integration
- ❌ Telegram notifications
- ❌ Storage/file operations
- ❌ Docker configuration

## Installation

```bash
# Install test dependencies
pip install -r requirements-dev.txt
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_strategy.py

# Run specific test
pytest tests/test_strategy.py::TestTargetCalculation::test_conservative_target_uses_partial_resistance

# Run with coverage report
pytest --cov=btc_monitor tests/
```

## Test Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py           # Fixtures and mock data helpers
├── test_strategy.py      # Strategy calculation tests
└── README.md             # This file
```

## Test Categories

### 1. Signal Generation (`TestSignalGeneration`)

Tests that the strategy correctly identifies entry signals based on market conditions:

- **Strong Buy Signal**: Multiple indicators trigger (drop + RSI + MA)
- **No Signal**: Weak conditions don't trigger entry
- **Partial Signal**: Minimum threshold (score=3) triggers entry
- **Near Support**: Bonus points when price near support level

### 2. Target Calculation (`TestTargetCalculation`)

Tests the conservative hybrid target calculation:

- **Partial Resistance**: Uses 60% distance to resistance, not full
- **Max Cap**: Respects MAX_TAKE_PROFIT cap (5% default)
- **Minimum Threshold**: Targets meet TAKE_PROFIT minimum

### 3. Stop Loss (`TestStopLossCalculation`)

Tests stop loss calculation logic:

- **Always Calculated**: Stop loss exists for every signal
- **Support Levels**: Uses nearest support when available
- **Default Percentage**: Falls back to default % when no support

### 4. Risk/Reward (`TestRiskReward`)

Tests risk/reward ratio validation:

- **Positive Ratio**: Profit and stop percentages are valid
- **Favorable Ratio**: Ideally > 1.5 for conservative strategy

### 5. Indicator Values (`TestIndicatorValues`)

Tests that indicators are properly calculated:

- **MA Distance**: Moving average and distance calculated
- **RSI**: RSI value in valid range (0-100)
- **Support/Resistance**: Levels detected from historical data

## Mock Data

The `conftest.py` file provides helper functions to create realistic market scenarios:

### Helper Functions

```python
# Create historical OHLC data
create_mock_historical_data(
    days=90,
    base_price=100000,
    trend="neutral"  # up, down, neutral, volatile
)

# Create 24h statistics
create_mock_stats_24h(
    price_change_percent=-5.0
)

# Create data with specific indicators
create_price_with_indicators(
    current_price=100000,
    ma_value=98000,
    rsi_value=25,
    supports=[96000, 93000],
    resistances=[105000, 110000]
)
```

### Fixtures

Pre-configured market scenarios:

- `scenario_strong_buy` - Strong buy signal (drop + RSI + MA)
- `scenario_no_signal` - No signal scenario
- `scenario_partial_signal` - Minimum threshold scenario
- `scenario_conservative_target` - Target calculation test
- `scenario_near_support` - Price near support level

## Adding New Tests

### 1. Create a new test function

```python
def test_my_new_scenario():
    """Description of what this tests"""
    # Create mock data
    current_price = 100000
    df = create_mock_historical_data()
    stats_24h = create_mock_stats_24h(-5.0)

    # Run analysis
    analysis = analyze_opportunity(...)

    # Assertions
    assert analysis['entry_signal'] is True
    assert analysis['score'] >= 3
```

### 2. Or create a new fixture in conftest.py

```python
@pytest.fixture
def scenario_my_case():
    """My custom scenario"""
    current_price = 100000
    df = create_price_with_indicators(...)
    stats_24h = create_mock_stats_24h(...)
    return current_price, stats_24h, df
```

## Test Results

All tests should pass:

```
======================== 12 passed in 0.41s =========================
tests/test_strategy.py::TestSignalGeneration::test_strong_buy_signal PASSED
tests/test_strategy.py::TestSignalGeneration::test_no_signal_scenario PASSED
tests/test_strategy.py::TestSignalGeneration::test_partial_signal_minimum_threshold PASSED
tests/test_strategy.py::TestSignalGeneration::test_near_support_adds_bonus_score PASSED
tests/test_strategy.py::TestTargetCalculation::test_conservative_target_uses_partial_resistance PASSED
tests/test_strategy.py::TestTargetCalculation::test_target_respects_max_take_profit_cap PASSED
tests/test_strategy.py::TestStopLossCalculation::test_stop_loss_exists PASSED
tests/test_strategy.py::TestStopLossCalculation::test_stop_loss_reasonable_default PASSED
tests/test_strategy.py::TestRiskReward::test_risk_reward_ratio_is_favorable PASSED
tests/test_strategy.py::TestIndicatorValues::test_ma_distance_calculated PASSED
tests/test_strategy.py::TestIndicatorValues::test_rsi_calculated PASSED
tests/test_strategy.py::TestIndicatorValues::test_support_resistance_levels_found PASSED
```

## Philosophy

These tests follow the principle of **simplicity over complexity**:

- ✅ Test business logic, not infrastructure
- ✅ Use simple fixtures, avoid heavy mocking frameworks
- ✅ Focus on key scenarios that matter
- ✅ Fast execution (< 1 second)
- ✅ Easy to understand and maintain

**Not overengineered** - Just what you need to validate the strategy works correctly.
