"""
Análise Histórica - BTC/BRL
Analisa o desempenho passado da estratégia "Buy the Dip"
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict

class BacktestAnalyzer:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.symbol = "BTCBRL"
    
    def get_historical_data(self, days: int = 180) -> pd.DataFrame:
        """Busca dados históricos"""
        print(f"📥 Baixando {days} dias de dados históricos...")
        
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
        
        print(f"✅ {len(df)} dias baixados\n")
        return df[['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    def calculate_daily_changes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula variações diárias"""
        df['change'] = df['close'].pct_change() * 100
        df['change_abs'] = df['close'].diff()
        return df
    
    def find_drops(self, df: pd.DataFrame, min_drop: float = 5.0) -> pd.DataFrame:
        """Encontra todas as quedas significativas"""
        drops = df[df['change'] <= -min_drop].copy()
        print(f"🔍 Encontradas {len(drops)} quedas de {min_drop}%+ nos últimos {len(df)} dias")
        return drops
    
    def analyze_recovery(self, df: pd.DataFrame, drops: pd.DataFrame, days_ahead: int = 7) -> List[Dict]:
        """Analisa quanto tempo e % o BTC levou para recuperar após cada queda"""
        results = []
        
        for idx, drop_row in drops.iterrows():
            drop_date = drop_row['date']
            drop_price = drop_row['close']
            drop_change = drop_row['change']
            
            # Pegar dias seguintes
            future_data = df[df['date'] > drop_date].head(days_ahead)
            
            if len(future_data) == 0:
                continue
            
            # Encontrar recuperação
            recovery_day = None
            recovery_price = None
            max_gain = 0
            max_gain_day = None
            
            for future_idx, future_row in future_data.iterrows():
                days_passed = (future_row['date'] - drop_date).days
                current_price = future_row['close']
                gain = ((current_price - drop_price) / drop_price) * 100
                
                # Primeira recuperação acima do drop
                if recovery_day is None and current_price > drop_price:
                    recovery_day = days_passed
                    recovery_price = current_price
                
                # Máximo ganho alcançado
                if gain > max_gain:
                    max_gain = gain
                    max_gain_day = days_passed
            
            results.append({
                'date': drop_date,
                'drop_percent': drop_change,
                'drop_price': drop_price,
                'recovery_days': recovery_day,
                'recovery_price': recovery_price,
                'max_gain_percent': max_gain,
                'max_gain_days': max_gain_day,
                'recovered': recovery_day is not None
            })
        
        return results
    
    def calculate_support_resistance_levels(self, df: pd.DataFrame) -> Dict:
        """Identifica principais níveis de suporte e resistência"""
        prices = pd.concat([df['high'], df['low']]).values
        
        # Dividir em bins e encontrar mais frequentes
        hist, bins = np.histogram(prices, bins=50)
        
        # Top 10 níveis mais tocados
        top_indices = hist.argsort()[-10:][::-1]
        top_levels = [(bins[i] + bins[i+1]) / 2 for i in top_indices]
        
        return {
            'levels': sorted(top_levels, reverse=True),
            'current_price': df['close'].iloc[-1]
        }
    
    def print_statistics(self, results: List[Dict]):
        """Imprime estatísticas da análise"""
        if len(results) == 0:
            print("❌ Nenhuma queda encontrada no período")
            return
        
        df_results = pd.DataFrame(results)
        
        # Filtrar apenas quedas que temos dados completos
        df_complete = df_results[df_results['max_gain_days'].notna()]
        
        print("="*80)
        print("📊 ESTATÍSTICAS DA ESTRATÉGIA 'BUY THE DIP'")
        print("="*80)
        
        print(f"\n📉 QUEDAS ANALISADAS:")
        print(f"   Total de quedas: {len(df_results)}")
        print(f"   Queda média: {df_results['drop_percent'].mean():.2f}%")
        print(f"   Maior queda: {df_results['drop_percent'].min():.2f}%")
        
        print(f"\n📈 RECUPERAÇÃO:")
        recovered = df_results['recovered'].sum()
        recovery_rate = (recovered / len(df_results)) * 100
        print(f"   Taxa de recuperação: {recovery_rate:.1f}% ({recovered}/{len(df_results)})")
        
        if recovered > 0:
            df_recovered = df_results[df_results['recovered'] == True]
            print(f"   Tempo médio de recuperação: {df_recovered['recovery_days'].mean():.1f} dias")
            print(f"   Recuperação mais rápida: {df_recovered['recovery_days'].min():.0f} dias")
            print(f"   Recuperação mais lenta: {df_recovered['recovery_days'].max():.0f} dias")
        
        print(f"\n💰 GANHOS POTENCIAIS (7 dias após queda):")
        print(f"   Ganho médio: {df_complete['max_gain_percent'].mean():.2f}%")
        print(f"   Maior ganho: {df_complete['max_gain_percent'].max():.2f}%")
        print(f"   Menor ganho: {df_complete['max_gain_percent'].min():.2f}%")
        print(f"   Ganhos positivos: {(df_complete['max_gain_percent'] > 0).sum()}/{len(df_complete)}")
        
        # Win rate
        winning_trades = (df_complete['max_gain_percent'] >= 2.0).sum()  # 2% de lucro mínimo
        win_rate = (winning_trades / len(df_complete)) * 100
        print(f"\n🎯 WIN RATE (lucro ≥2%):")
        print(f"   {win_rate:.1f}% ({winning_trades}/{len(df_complete)})")
        
        print("\n" + "="*80)
        
        return df_results
    
    def print_recent_opportunities(self, results: List[Dict], n: int = 10):
        """Mostra as últimas oportunidades"""
        print(f"\n📅 ÚLTIMAS {n} QUEDAS DETECTADAS:")
        print("="*80)
        
        df_results = pd.DataFrame(results)
        recent = df_results.tail(n)
        
        for idx, row in recent.iterrows():
            print(f"\n📅 {row['date']}")
            print(f"   💸 Preço na queda: R$ {row['drop_price']:,.2f}")
            print(f"   📉 Queda: {row['drop_percent']:.2f}%")
            
            if row['recovered']:
                print(f"   ✅ Recuperou em {row['recovery_days']:.0f} dias (R$ {row['recovery_price']:,.2f})")
            else:
                print(f"   ⏳ Ainda não recuperou totalmente")
            
            if pd.notna(row['max_gain_percent']):
                print(f"   📈 Ganho máximo: {row['max_gain_percent']:.2f}% em {row['max_gain_days']:.0f} dias")
        
        print("\n" + "="*80)
    
    def run_analysis(self, days: int = 180, min_drop: float = 5.0):
        """Executa análise completa"""
        print("\n🚀 INICIANDO ANÁLISE HISTÓRICA\n")
        
        # Baixar dados
        df = self.get_historical_data(days)
        df = self.calculate_daily_changes(df)
        
        # Encontrar quedas
        drops = self.find_drops(df, min_drop)
        
        # Analisar recuperação
        print(f"\n⏳ Analisando recuperação das quedas...\n")
        results = self.analyze_recovery(df, drops)
        
        # Estatísticas
        df_results = self.print_statistics(results)
        
        # Últimas oportunidades
        self.print_recent_opportunities(results)
        
        # Níveis atuais
        levels = self.calculate_support_resistance_levels(df)
        print(f"\n📍 NÍVEIS IMPORTANTES ATUAIS:")
        print(f"   Preço atual: R$ {levels['current_price']:,.2f}")
        print(f"   Principais níveis: {', '.join([f'R$ {level:,.0f}' for level in levels['levels'][:5]])}")
        
        return df, df_results

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║           📊 ANÁLISE HISTÓRICA BTC/BRL - BINANCE          ║
    ║              Estratégia: Buy the Dip 5/3                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    analyzer = BacktestAnalyzer()
    
    # Configurações
    DAYS = 180  # Analisar últimos 6 meses
    MIN_DROP = 5.0  # Quedas de 5%+
    
    df, results = analyzer.run_analysis(days=DAYS, min_drop=MIN_DROP)
    
    print("\n✅ Análise concluída!")
    print("\n💡 DICA: Ajuste os parâmetros no monitor_btc.py com base nessas estatísticas")

if __name__ == "__main__":
    main()
