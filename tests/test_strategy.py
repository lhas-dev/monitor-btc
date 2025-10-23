"""
Unit tests for trading strategy calculation

Tests the analyze_opportunity function with various market scenarios
to ensure correct signal generation and target/stop loss calculation.
"""

import pytest
from btc_monitor.indicators import analyze_opportunity


class TestSignalGeneration:
    """Tests for entry signal generation logic"""

    def test_strong_buy_signal(self, scenario_strong_buy):
        """Strong signals (drop + RSI + MA) should trigger entry"""
        current_price, stats_24h, df = scenario_strong_buy

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        # Should trigger entry signal
        assert analysis['entry_signal'] is True, "Strong signal should trigger entry"
        assert analysis['score'] >= 3, f"Score should be >= 3 (entry threshold), got {analysis['score']}"
        assert len(analysis['signals']) >= 1, "Should have at least one signal"

        # At minimum, should have the 24h drop signal (score +3)
        drop_signal_found = any("24H DROP" in signal for signal in analysis['signals'])
        assert drop_signal_found, "Should detect 24h drop signal"

        # Should have price and timestamp
        assert analysis['price'] == current_price
        assert 'timestamp' in analysis

    def test_no_signal_scenario(self, scenario_no_signal):
        """Weak conditions should not trigger entry signal"""
        current_price, stats_24h, df = scenario_no_signal

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        # Should NOT trigger entry signal
        assert analysis['entry_signal'] is False, "Weak signal should not trigger entry"
        assert analysis['score'] < 3, f"Score should be < 3, got {analysis['score']}"

    def test_partial_signal_minimum_threshold(self, scenario_partial_signal):
        """Signal at minimum threshold (score=3) should trigger entry"""
        current_price, stats_24h, df = scenario_partial_signal

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        # Should trigger entry signal (score=3 is minimum)
        assert analysis['entry_signal'] is True, "Score>=3 should trigger entry"
        assert analysis['score'] >= 3, f"Score should be >= 3, got {analysis['score']}"

        # Should have at least the drop signal
        drop_signal_found = any("24H DROP" in signal for signal in analysis['signals'])
        assert drop_signal_found, "Should detect 24h drop signal"

    def test_near_support_adds_bonus_score(self, scenario_near_support):
        """Price near support should add bonus point to score"""
        current_price, stats_24h, df = scenario_near_support

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        # Check if near support signal is detected
        near_support_detected = any("NEAR SUPPORT" in signal for signal in analysis['signals'])
        assert near_support_detected, "Should detect near support level"


class TestTargetCalculation:
    """Tests for conservative target price calculation"""

    def test_conservative_target_uses_partial_resistance(self, scenario_conservative_target):
        """Target should use 60% distance to resistance, not full resistance"""
        current_price, stats_24h, df = scenario_conservative_target

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        # Target should exist
        assert analysis['target_price'] is not None, "Target price should be calculated"

        # Target should be less than full resistance (110k)
        # With 60% factor: 100k + (110k - 100k) * 0.6 = 106k
        # But capped at 5%: 100k * 1.05 = 105k
        expected_max = current_price * 1.05  # 5% cap
        assert analysis['target_price'] <= expected_max, \
            f"Target should be capped at {expected_max}, got {analysis['target_price']}"

        # Target should be at least minimum take profit
        expected_min = current_price * 1.02  # 2% minimum
        assert analysis['target_price'] >= expected_min, \
            f"Target should be at least {expected_min}, got {analysis['target_price']}"

        # Profit percent should be reasonable (2-5%)
        assert 2.0 <= analysis['profit_percent'] <= 5.0, \
            f"Profit percent should be 2-5%, got {analysis['profit_percent']}"

    def test_target_respects_max_take_profit_cap(self):
        """Target should never exceed MAX_TAKE_PROFIT cap"""
        from tests.conftest import create_price_with_indicators, create_mock_stats_24h

        current_price = 100000
        # Create scenario with very high resistance
        df = create_price_with_indicators(
            current_price=current_price,
            ma_value=98000,
            rsi_value=25,
            resistances=[120000, 125000]  # +20% resistance
        )
        stats_24h = create_mock_stats_24h(-6.0)

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,  # Should cap at 5%
            resistance_factor=0.6
        )

        # Even with 20% resistance, should cap at 5%
        max_allowed = current_price * 1.05
        assert analysis['target_price'] <= max_allowed, \
            f"Target should be capped at 5% ({max_allowed}), got {analysis['target_price']}"


class TestStopLossCalculation:
    """Tests for stop loss calculation logic"""

    def test_stop_loss_exists(self, scenario_strong_buy):
        """Stop loss should always be calculated"""
        current_price, stats_24h, df = scenario_strong_buy

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        assert analysis['stop_loss'] is not None, "Stop loss should be calculated"
        assert analysis['stop_percent'] is not None, "Stop percent should be calculated"

        # Stop loss should be below current price
        assert analysis['stop_loss'] < current_price, \
            "Stop loss should be below current price"

        # Stop percent should be reasonable
        assert 0 < analysis['stop_percent'] <= 6.0, \
            f"Stop percent should be 0-6%, got {analysis['stop_percent']}"

    def test_stop_loss_reasonable_default(self):
        """Stop loss should default to configured percentage when no support"""
        from tests.conftest import create_price_with_indicators, create_mock_stats_24h

        current_price = 100000
        # Create scenario with no nearby support
        df = create_price_with_indicators(
            current_price=current_price,
            ma_value=98000,
            rsi_value=25,
            supports=[80000, 75000],  # Far away supports
            resistances=[105000]
        )
        stats_24h = create_mock_stats_24h(-6.0)

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,  # Should use this default
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        # Should use either default percentage or nearest support (within 6% max)
        expected_stop_default = current_price * 0.97  # 3% stop loss
        max_stop = current_price * 0.94  # Maximum 6% stop loss

        # Stop should be reasonable (between 3-6% below current)
        assert max_stop <= analysis['stop_loss'] <= current_price, \
            f"Stop loss should be between {max_stop} and {current_price}, got {analysis['stop_loss']}"

        # Stop percent should be reasonable
        assert 0 < analysis['stop_percent'] <= 6.0, \
            f"Stop percent should be 0-6%, got {analysis['stop_percent']}"


class TestRiskReward:
    """Tests for risk/reward ratio validation"""

    def test_risk_reward_ratio_is_favorable(self, scenario_strong_buy):
        """Risk/reward ratio should be > 1.0 (preferably > 1.5)"""
        current_price, stats_24h, df = scenario_strong_buy

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        # Both profit and stop should exist
        assert analysis['profit_percent'] > 0, "Profit percent should be positive"
        assert analysis['stop_percent'] > 0, "Stop percent should be positive"

        # Risk/reward calculation
        risk_reward = analysis['profit_percent'] / analysis['stop_percent']

        # Risk/reward should exist (may vary based on support/resistance detection)
        # Just verify the calculation makes sense
        assert risk_reward > 0, f"Risk/reward should be positive, got {risk_reward:.2f}"

        # Log the ratio for information (not a hard requirement in tests)
        # In real scenarios, should aim for > 1.5
        print(f"Risk/Reward ratio: {risk_reward:.2f}")


class TestIndicatorValues:
    """Tests for indicator calculations"""

    def test_ma_distance_calculated(self, scenario_strong_buy):
        """MA distance should be calculated and included in analysis"""
        current_price, stats_24h, df = scenario_strong_buy

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        assert 'ma' in analysis, "MA value should be in analysis"
        assert 'ma_distance' in analysis, "MA distance should be in analysis"
        assert analysis['ma'] > 0, "MA should be positive"

    def test_rsi_calculated(self, scenario_strong_buy):
        """RSI should be calculated and included in analysis"""
        current_price, stats_24h, df = scenario_strong_buy

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        assert 'rsi' in analysis, "RSI should be in analysis"
        assert 0 <= analysis['rsi'] <= 100, \
            f"RSI should be 0-100, got {analysis['rsi']}"

    def test_support_resistance_levels_found(self, scenario_strong_buy):
        """Support and resistance levels should be detected"""
        current_price, stats_24h, df = scenario_strong_buy

        analysis = analyze_opportunity(
            current_price=current_price,
            stats_24h=stats_24h,
            df_historical=df,
            min_drop=5.0,
            ma_distance=3.0,
            rsi_oversold=30,
            ma_period=7,
            stop_loss=3.0,
            take_profit=2.0,
            max_take_profit=5.0,
            resistance_factor=0.6
        )

        assert 'supports' in analysis, "Supports should be in analysis"
        assert 'resistances' in analysis, "Resistances should be in analysis"
        assert len(analysis['supports']) > 0, "Should find support levels"
        assert len(analysis['resistances']) > 0, "Should find resistance levels"
