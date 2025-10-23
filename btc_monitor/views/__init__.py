"""
Views module - Centralized message formatting and presentation logic

This module contains all user-facing message templates and formatting functions
for different output channels (Telegram, console, backtest reports, etc.)
"""

from btc_monitor.views.telegram import format_trade_signal, format_test_message
from btc_monitor.views.console import format_analysis, format_startup_info, format_telegram_status
from btc_monitor.views.backtest import (
    format_statistics,
    format_recent_opportunities,
    format_header,
    format_backtest_startup_info
)
from btc_monitor.views.test import (
    format_test_start,
    format_success_message,
    format_error_message
)

__all__ = [
    # Telegram views
    'format_trade_signal',
    'format_test_message',

    # Console views
    'format_analysis',
    'format_startup_info',
    'format_telegram_status',

    # Backtest views
    'format_statistics',
    'format_recent_opportunities',
    'format_header',
    'format_backtest_startup_info',

    # Test views
    'format_test_start',
    'format_success_message',
    'format_error_message',
]
