"""
Binance API client - reusable wrapper for API calls
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
import time


class BinanceClient:
    """Simple Binance API client"""

    def __init__(self, symbol: str = 'BTCUSDT', base_url: str = "https://api.binance.us"):
        self.symbol = symbol
        self.base_url = base_url

    def get_current_price(self) -> Optional[float]:
        """Get current price for symbol"""
        try:
            url = f"{self.base_url}/api/v3/ticker/price"
            params = {'symbol': self.symbol}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception as e:
            print(f"❌ Error fetching price: {e}")
            return None

    def get_24h_stats(self) -> Optional[Dict]:
        """Get 24h statistics"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            params = {'symbol': self.symbol}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                'price_change': float(data['priceChange']),
                'price_change_percent': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice']),
                'volume': float(data['volume'])
            }
        except Exception as e:
            print(f"❌ Error fetching 24h data: {e}")
            return None

    def get_historical_klines(self, days: int = 90) -> Optional[pd.DataFrame]:
        """Get historical candlestick data"""
        try:
            url = f"{self.base_url}/api/v3/klines"
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

            params = {
                'symbol': self.symbol,
                'interval': '1d',
                'startTime': start_time,
                'endTime': end_time,
                'limit': 1000
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return None

    def get_historical_with_retry(self, days: int = 180, retries: int = 3) -> Optional[pd.DataFrame]:
        """Fetch historical data with retry logic (for backtest)"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for attempt in range(retries):
            try:
                url = f"{self.base_url}/api/v3/klines"
                end_time = int(datetime.now().timestamp() * 1000)
                start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

                params = {
                    'symbol': self.symbol,
                    'interval': '1d',
                    'startTime': start_time,
                    'endTime': end_time,
                    'limit': 1000
                }

                response = requests.get(url, params=params, headers=headers, timeout=15)

                if response.status_code == 200:
                    data = response.json()
                    if len(data) == 0:
                        return None

                    df = pd.DataFrame(data, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume',
                        'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                        'taker_buy_quote', 'ignore'
                    ])

                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df['date'] = df['timestamp'].dt.date
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = df[col].astype(float)

                    return df[['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
                else:
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff

            except Exception:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)

        return None
