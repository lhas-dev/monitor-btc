"""
Enhanced Historical Analysis - BTC/USDT
With robust API handling and multiple drop detection methods
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import time

class ImprovedBacktestAnalyzer:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.symbol = "BTCUSDT"
        
    def get_historical_data(self, days: int = 180, retries: int = 3) -> pd.DataFrame:
        """Fetch historical data with retry and appropriate headers"""
        print(f"📥 Downloading {days} days of historical data...")
        
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
                        print(f"⚠️  No data returned")
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

                    print(f"✅ {len(df)} days downloaded\n")
                    return df[['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]

                else:
                    print(f"⚠️  Attempt {attempt + 1}/{retries} - Status: {response.status_code}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        
            except Exception as e:
                print(f"⚠️  Attempt {attempt + 1}/{retries} - Error: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)

        print("❌ Unable to download data from API after multiple attempts")
        print("💡 TIP: Try again in a few minutes or check your connection")
        return None
    
    def find_drops_advanced(self, df: pd.DataFrame, min_drop: float = 5.0) -> pd.DataFrame:
        """
        Detect drops using MULTIPLE methods:
        1. Close-to-close (previous day to next day)
        2. Peak-to-valley (from high to low over any period)
        3. Intraday (high to low on same day)
        """

        # Method 1: Close to close (original)
        df['change_close'] = df['close'].pct_change() * 100
        drops_close = df[df['change_close'] <= -min_drop].copy()
        drops_close['tipo'] = 'Close-to-Close'

        # Method 2: Drawdown (from recent peak to valley)
        # Calculate maximum of last 30 days
        df['rolling_max'] = df['high'].rolling(window=30, min_periods=1).max()
        df['drawdown'] = ((df['low'] - df['rolling_max']) / df['rolling_max']) * 100
        drops_drawdown = df[df['drawdown'] <= -min_drop].copy()
        drops_drawdown['tipo'] = 'Peak-to-Valley'
        drops_drawdown['change_close'] = drops_drawdown['drawdown']

        # Method 3: Intraday (high to low on same day)
        df['change_intraday'] = ((df['low'] - df['high']) / df['high']) * 100
        drops_intraday = df[df['change_intraday'] <= -min_drop].copy()
        drops_intraday['tipo'] = 'Intraday'
        drops_intraday['change_close'] = drops_intraday['change_intraday']

        # Combine all types and remove duplicates by date
        all_drops = pd.concat([drops_close, drops_drawdown, drops_intraday])

        # Group by date and get the largest drop
        if len(all_drops) > 0:
            all_drops = all_drops.sort_values('change_close').groupby('date').first().reset_index()
        
        print(f"🔍 Found {len(all_drops)} drops of {min_drop}%+ (using multiple methods)")
        if len(all_drops) > 0:
            print(f"   - Close-to-Close: {len(drops_close)}")
            print(f"   - Peak-to-Valley: {len(drops_drawdown)}")
            print(f"   - Intraday: {len(drops_intraday)}")

        return all_drops
    
    def analyze_recovery(self, df: pd.DataFrame, drops: pd.DataFrame, days_ahead: int = 7) -> List[Dict]:
        """Analyze recovery after drops"""
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
    
    def print_statistics(self, results: List[Dict]):
        """Print enhanced statistics"""
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
    
    def print_recent_opportunities(self, results: List[Dict], n: int = 10):
        """Show recent opportunities"""
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
    
    def run_analysis(self, days: int = 180, min_drop: float = 5.0):
        """Execute complete analysis"""
        print("\n🚀 STARTING ENHANCED HISTORICAL ANALYSIS\n")

        df = self.get_historical_data(days)

        if df is None or len(df) == 0:
            print("\n❌ Unable to obtain data")
            print("💡 Possible causes:")
            print("   - Binance API temporarily unavailable")
            print("   - Request limit reached")
            print("   - Connection problems")
            print("\n🔧 Solutions:")
            print("   - Wait a few minutes and try again")
            print("   - Check your internet connection")
            print("   - Try decreasing the analysis period")
            return None, None

        # Find drops (enhanced method)
        drops = self.find_drops_advanced(df, min_drop)

        if len(drops) == 0:
            print(f"\n💡 TIP: No drops of {min_drop}%+ detected.")
            print(f"   Try lowering the threshold (e.g. 3% or 4%) to see more opportunities.")
            return df, None

        # Analyze recovery
        print(f"\n⏳ Analyzing drop recovery...\n")
        results = self.analyze_recovery(df, drops)

        # Statistics
        df_results = self.print_statistics(results)

        # Recent opportunities
        self.print_recent_opportunities(results)

        return df, df_results

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║      📊 BTC/USDT HISTORICAL ANALYSIS - ENHANCED VERSION   ║
    ║              Multiple Detection Methods                   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    analyzer = ImprovedBacktestAnalyzer()

    # Try with 5%, if nothing found, try with 3%
    df, results = analyzer.run_analysis(days=180, min_drop=5.0)

    if results is None and df is not None:
        print("\n🔄 Trying again with 3% threshold...")
        drops = analyzer.find_drops_advanced(df, min_drop=3.0)
        if len(drops) > 0:
            results_list = analyzer.analyze_recovery(df, drops)
            analyzer.print_statistics(results_list)
            analyzer.print_recent_opportunities(results_list)

    if df is not None:
        print("\n✅ Analysis complete!")
        print("💡 Use these statistics to adjust config.py")

if __name__ == "__main__":
    main()
