"""
Análise Histórica - BTC/BRL (Multi-API)
Tenta Binance primeiro, depois CoinGecko como fallback
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import time

class MultiAPIAnalyzer:
    def __init__(self):
        self.binance_url = "https://api.binance.com"
        self.coingecko_url = "https://api.coingecko.com/api/v3"
        
    def try_binance(self, days: int) -> Tuple[pd.DataFrame, str]:
        """Tenta buscar dados da Binance"""
        try:
            print("📡 Tentando API da Binance...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = f"{self.binance_url}/api/v3/klines"
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            params = {
                'symbol': 'BTCBRL',
                'interval': '1d',
                'startTime': start_time,
                'endTime': end_time,
                'limit': 1000
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                    'taker_buy_quote', 'ignore'
                ])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['date'] = df['timestamp'].dt.date
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = df[col].astype(float)
                
                print(f"   ✅ Binance: {len(df)} dias")
                return df[['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']], "Binance"
            else:
                print(f"   ❌ Binance retornou status {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"   ❌ Erro na Binance: {e}")
            return None, None
    
    def try_coingecko(self, days: int) -> Tuple[pd.DataFrame, str]:
        """Tenta buscar dados do CoinGecko"""
        try:
            print("📡 Tentando API do CoinGecko...")
            
            url = f"{self.coingecko_url}/coins/bitcoin/market_chart"
            params = {
                'vs_currency': 'brl',
                'days': days,
                'interval': 'daily'
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # CoinGecko retorna listas de [timestamp, valor]
                prices = data['prices']
                
                df = pd.DataFrame(prices, columns=['timestamp', 'close'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['date'] = df['timestamp'].dt.date
                
                # CoinGecko não tem OHLC em API gratuita, então aproximamos
                df['open'] = df['close']
                df['high'] = df['close'] * 1.01  # Aprox +1%
                df['low'] = df['close'] * 0.99   # Aprox -1%
                df['volume'] = 0.0
                
                print(f"   ✅ CoinGecko: {len(df)} dias")
                print(f"   ⚠️  Nota: CoinGecko API gratuita não tem OHLC completo")
                return df[['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']], "CoinGecko"
            else:
                print(f"   ❌ CoinGecko retornou status {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"   ❌ Erro no CoinGecko: {e}")
            return None, None
    
    def get_historical_data(self, days: int = 180) -> Tuple[pd.DataFrame, str]:
        """Tenta múltiplas APIs"""
        print(f"\n📥 Buscando {days} dias de dados históricos...\n")
        
        # Tentar Binance primeiro
        df, source = self.try_binance(days)
        if df is not None:
            return df, source
        
        print()
        
        # Fallback para CoinGecko
        df, source = self.try_coingecko(days)
        if df is not None:
            return df, source
        
        print("\n❌ Todas as APIs falharam")
        return None, None
    
    def find_drops_multi_method(self, df: pd.DataFrame, min_drop: float = 5.0) -> pd.DataFrame:
        """Detecta quedas usando múltiplos métodos"""
        
        all_drops = []
        
        # Método 1: Close-to-Close
        df['change_close'] = df['close'].pct_change() * 100
        drops_close = df[df['change_close'] <= -min_drop].copy()
        if len(drops_close) > 0:
            drops_close['tipo'] = 'Close-to-Close'
            drops_close['drop_percent'] = drops_close['change_close']
            all_drops.append(drops_close[['date', 'close', 'drop_percent', 'tipo']])
        
        # Método 2: Drawdown (pico para vale)
        df['rolling_max_7d'] = df['high'].rolling(window=7, min_periods=1).max()
        df['rolling_max_30d'] = df['high'].rolling(window=30, min_periods=1).max()
        df['drawdown_7d'] = ((df['low'] - df['rolling_max_7d']) / df['rolling_max_7d']) * 100
        df['drawdown_30d'] = ((df['low'] - df['rolling_max_30d']) / df['rolling_max_30d']) * 100
        
        drops_dd_7d = df[df['drawdown_7d'] <= -min_drop].copy()
        if len(drops_dd_7d) > 0:
            drops_dd_7d['tipo'] = 'Drawdown-7d'
            drops_dd_7d['drop_percent'] = drops_dd_7d['drawdown_7d']
            all_drops.append(drops_dd_7d[['date', 'close', 'drop_percent', 'tipo']])
        
        drops_dd_30d = df[df['drawdown_30d'] <= -min_drop].copy()
        if len(drops_dd_30d) > 0:
            drops_dd_30d['tipo'] = 'Drawdown-30d'
            drops_dd_30d['drop_percent'] = drops_dd_30d['drawdown_30d']
            all_drops.append(drops_dd_30d[['date', 'close', 'drop_percent', 'tipo']])
        
        # Método 3: Intraday
        df['change_intraday'] = ((df['low'] - df['high']) / df['high']) * 100
        drops_intra = df[df['change_intraday'] <= -min_drop].copy()
        if len(drops_intra) > 0:
            drops_intra['tipo'] = 'Intraday'
            drops_intra['drop_percent'] = drops_intra['change_intraday']
            all_drops.append(drops_intra[['date', 'close', 'drop_percent', 'tipo']])
        
        # Combinar e remover duplicatas
        if len(all_drops) == 0:
            return pd.DataFrame()
        
        combined = pd.concat(all_drops)
        
        # Para cada data, pegar apenas a maior queda
        result = combined.sort_values('drop_percent').groupby('date').first().reset_index()
        
        print(f"\n🔍 QUEDAS DETECTADAS (≥{min_drop}%):")
        print(f"   Total: {len(result)} oportunidades")
        for tipo in combined['tipo'].unique():
            count = len(combined[combined['tipo'] == tipo])
            print(f"   - {tipo}: {count}")
        
        return result
    
    def analyze_recovery(self, df: pd.DataFrame, drops: pd.DataFrame, days_ahead: int = 7) -> List[Dict]:
        """Analisa recuperação"""
        results = []
        
        for idx, drop_row in drops.iterrows():
            drop_date = drop_row['date']
            drop_price = drop_row['close']
            drop_change = drop_row['drop_percent']
            drop_tipo = drop_row['tipo']
            
            future_data = df[df['date'] > drop_date].head(days_ahead)
            
            if len(future_data) == 0:
                continue
            
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
                'max_gain_percent': max_gain,
                'max_gain_days': max_gain_day,
                'recovered': recovery_day is not None
            })
        
        return results
    
    def print_analysis(self, results: List[Dict], source: str):
        """Imprime análise"""
        if len(results) == 0:
            return
        
        df = pd.DataFrame(results)
        
        print("\n" + "="*80)
        print(f"📊 ANÁLISE COMPLETA (Fonte: {source})")
        print("="*80)
        
        print(f"\n📉 QUEDAS:")
        print(f"   Total: {len(df)}")
        print(f"   Queda média: {df['drop_percent'].mean():.2f}%")
        print(f"   Maior queda: {df['drop_percent'].min():.2f}%")
        
        print(f"\n📈 RECUPERAÇÃO:")
        recovered = df['recovered'].sum()
        print(f"   Taxa: {(recovered/len(df)*100):.1f}% ({recovered}/{len(df)})")
        
        if recovered > 0:
            df_rec = df[df['recovered'] == True]
            print(f"   Tempo médio: {df_rec['recovery_days'].mean():.1f} dias")
        
        df_complete = df[df['max_gain_days'].notna()]
        if len(df_complete) > 0:
            print(f"\n💰 GANHOS (7 dias após):")
            print(f"   Médio: {df_complete['max_gain_percent'].mean():.2f}%")
            print(f"   Máximo: {df_complete['max_gain_percent'].max():.2f}%")
            
            for threshold in [2.0, 3.0]:
                wins = (df_complete['max_gain_percent'] >= threshold).sum()
                rate = (wins / len(df_complete)) * 100
                print(f"\n   Win Rate (≥{threshold}%): {rate:.1f}%")
        
        print("\n" + "="*80)
        
        # Mostrar últimas quedas
        print("\n📅 ÚLTIMAS 5 QUEDAS:")
        print("="*80)
        for idx, row in df.tail(5).iterrows():
            print(f"\n{row['date']} - {row['tipo']}")
            print(f"   Queda: {row['drop_percent']:.2f}% (R$ {row['drop_price']:,.0f})")
            if row['recovered']:
                print(f"   ✅ Recuperou em {row['recovery_days']:.0f} dias")
            if pd.notna(row['max_gain_percent']):
                print(f"   📈 Ganho máx: {row['max_gain_percent']:.2f}%")
        
        print("\n" + "="*80)
    
    def run(self, days: int = 180, min_drop: float = 5.0):
        """Executa análise completa"""
        print("""
╔═══════════════════════════════════════════════════════════╗
║      📊 ANÁLISE HISTÓRICA BTC/BRL (Multi-API)             ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        df, source = self.get_historical_data(days)
        
        if df is None:
            print("\n❌ Não foi possível obter dados de nenhuma API")
            print("\n💡 DICA: Execute este script no SEU COMPUTADOR")
            print("   Provavelmente vai funcionar! A API está bloqueando")
            print("   apenas este servidor específico.")
            return
        
        print(f"\n✅ Dados obtidos com sucesso!\n")
        
        drops = self.find_drops_multi_method(df, min_drop)
        
        if len(drops) == 0:
            print(f"\n⚠️  Nenhuma queda de {min_drop}%+ encontrada")
            print(f"💡 Tentando com {min_drop-2}%...")
            drops = self.find_drops_multi_method(df, min_drop-2)
        
        if len(drops) > 0:
            print(f"\n⏳ Analisando recuperação...")
            results = self.analyze_recovery(df, drops)
            self.print_analysis(results, source)
        else:
            print("\n⚠️  Nenhuma queda significativa detectada no período")
        
        print("\n✅ Análise concluída!")

def main():
    analyzer = MultiAPIAnalyzer()
    analyzer.run(days=180, min_drop=5.0)

if __name__ == "__main__":
    main()
