"""
Análise Histórica MELHORADA - BTC/BRL
Com tratamento robusto de API e múltiplas formas de detectar quedas
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
        self.symbol = "BTCBRL"
        
    def get_historical_data(self, days: int = 180, retries: int = 3) -> pd.DataFrame:
        """Busca dados históricos com retry e headers apropriados"""
        print(f"📥 Baixando {days} dias de dados históricos...")
        
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
                        print(f"⚠️  Nenhum dado retornado")
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
                    
                    print(f"✅ {len(df)} dias baixados\n")
                    return df[['date', 'timestamp', 'open', 'high', 'low', 'close', 'volume']]
                
                else:
                    print(f"⚠️  Tentativa {attempt + 1}/{retries} - Status: {response.status_code}")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        
            except Exception as e:
                print(f"⚠️  Tentativa {attempt + 1}/{retries} - Erro: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        
        print("❌ Não foi possível baixar dados da API após várias tentativas")
        print("💡 DICA: Tente novamente em alguns minutos ou verifique sua conexão")
        return None
    
    def find_drops_advanced(self, df: pd.DataFrame, min_drop: float = 5.0) -> pd.DataFrame:
        """
        Detecta quedas usando MÚLTIPLOS métodos:
        1. Close-to-close (dia anterior para dia seguinte)
        2. Peak-to-valley (de máxima para mínima em qualquer período)
        3. Intraday (alta para baixa no mesmo dia)
        """
        
        # Método 1: Close to close (original)
        df['change_close'] = df['close'].pct_change() * 100
        drops_close = df[df['change_close'] <= -min_drop].copy()
        drops_close['tipo'] = 'Close-to-Close'
        
        # Método 2: Drawdown (de pico recente para vale)
        # Calcula a máxima dos últimos 30 dias
        df['rolling_max'] = df['high'].rolling(window=30, min_periods=1).max()
        df['drawdown'] = ((df['low'] - df['rolling_max']) / df['rolling_max']) * 100
        drops_drawdown = df[df['drawdown'] <= -min_drop].copy()
        drops_drawdown['tipo'] = 'Peak-to-Valley'
        drops_drawdown['change_close'] = drops_drawdown['drawdown']
        
        # Método 3: Intraday (alta para baixa no mesmo dia)
        df['change_intraday'] = ((df['low'] - df['high']) / df['high']) * 100
        drops_intraday = df[df['change_intraday'] <= -min_drop].copy()
        drops_intraday['tipo'] = 'Intraday'
        drops_intraday['change_close'] = drops_intraday['change_intraday']
        
        # Combinar todos os tipos e remover duplicatas por data
        all_drops = pd.concat([drops_close, drops_drawdown, drops_intraday])
        
        # Agrupar por data e pegar a maior queda
        if len(all_drops) > 0:
            all_drops = all_drops.sort_values('change_close').groupby('date').first().reset_index()
        
        print(f"🔍 Encontradas {len(all_drops)} quedas de {min_drop}%+ (usando múltiplos métodos)")
        if len(all_drops) > 0:
            print(f"   - Close-to-Close: {len(drops_close)}")
            print(f"   - Peak-to-Valley: {len(drops_drawdown)}")
            print(f"   - Intraday: {len(drops_intraday)}")
        
        return all_drops
    
    def analyze_recovery(self, df: pd.DataFrame, drops: pd.DataFrame, days_ahead: int = 7) -> List[Dict]:
        """Analisa recuperação após quedas"""
        results = []
        
        for idx, drop_row in drops.iterrows():
            drop_date = drop_row['date']
            drop_price = drop_row['close']
            drop_change = drop_row['change_close']
            drop_tipo = drop_row.get('tipo', 'Unknown')
            
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
        """Imprime estatísticas melhoradas"""
        if len(results) == 0:
            print("❌ Nenhuma queda encontrada no período")
            return
        
        df_results = pd.DataFrame(results)
        df_complete = df_results[df_results['max_gain_days'].notna()]
        
        print("="*80)
        print("📊 ESTATÍSTICAS DA ESTRATÉGIA 'BUY THE DIP'")
        print("="*80)
        
        print(f"\n📉 QUEDAS ANALISADAS:")
        print(f"   Total de quedas: {len(df_results)}")
        print(f"   Queda média: {df_results['drop_percent'].mean():.2f}%")
        print(f"   Maior queda: {df_results['drop_percent'].min():.2f}%")
        
        # Por tipo
        if 'tipo' in df_results.columns:
            print(f"\n📊 QUEDAS POR TIPO:")
            for tipo in df_results['tipo'].unique():
                count = len(df_results[df_results['tipo'] == tipo])
                print(f"   {tipo}: {count}")
        
        print(f"\n📈 RECUPERAÇÃO:")
        recovered = df_results['recovered'].sum()
        recovery_rate = (recovered / len(df_results)) * 100
        print(f"   Taxa de recuperação: {recovery_rate:.1f}% ({recovered}/{len(df_results)})")
        
        if recovered > 0:
            df_recovered = df_results[df_results['recovered'] == True]
            print(f"   Tempo médio: {df_recovered['recovery_days'].mean():.1f} dias")
            print(f"   Mais rápida: {df_recovered['recovery_days'].min():.0f} dias")
            print(f"   Mais lenta: {df_recovered['recovery_days'].max():.0f} dias")
        
        if len(df_complete) > 0:
            print(f"\n💰 GANHOS POTENCIAIS (7 dias após):")
            print(f"   Ganho médio: {df_complete['max_gain_percent'].mean():.2f}%")
            print(f"   Maior ganho: {df_complete['max_gain_percent'].max():.2f}%")
            print(f"   Menor: {df_complete['max_gain_percent'].min():.2f}%")
            
            # Win rate por thresholds
            for threshold in [1.0, 2.0, 3.0]:
                winning = (df_complete['max_gain_percent'] >= threshold).sum()
                win_rate = (winning / len(df_complete)) * 100
                print(f"\n🎯 WIN RATE (lucro ≥{threshold}%):")
                print(f"   {win_rate:.1f}% ({winning}/{len(df_complete)})")
        
        print("\n" + "="*80)
        
        return df_results
    
    def print_recent_opportunities(self, results: List[Dict], n: int = 10):
        """Mostra últimas oportunidades"""
        if len(results) == 0:
            return
            
        print(f"\n📅 ÚLTIMAS {min(n, len(results))} QUEDAS DETECTADAS:")
        print("="*80)
        
        df_results = pd.DataFrame(results)
        recent = df_results.tail(n)
        
        for idx, row in recent.iterrows():
            print(f"\n📅 {row['date']} [{row.get('tipo', 'N/A')}]")
            print(f"   💸 Preço: R$ {row['drop_price']:,.2f}")
            print(f"   📉 Queda: {row['drop_percent']:.2f}%")
            
            if row['recovered']:
                print(f"   ✅ Recuperou em {row['recovery_days']:.0f} dias")
            
            if pd.notna(row['max_gain_percent']):
                print(f"   📈 Ganho máx: {row['max_gain_percent']:.2f}% em {row['max_gain_days']:.0f} dias")
        
        print("\n" + "="*80)
    
    def run_analysis(self, days: int = 180, min_drop: float = 5.0):
        """Executa análise completa"""
        print("\n🚀 INICIANDO ANÁLISE HISTÓRICA MELHORADA\n")
        
        df = self.get_historical_data(days)
        
        if df is None or len(df) == 0:
            print("\n❌ Não foi possível obter dados")
            print("💡 Possíveis causas:")
            print("   - API da Binance temporariamente indisponível")
            print("   - Limite de requisições atingido")
            print("   - Problemas de conexão")
            print("\n🔧 Soluções:")
            print("   - Aguarde alguns minutos e tente novamente")
            print("   - Verifique sua conexão com internet")
            print("   - Tente diminuir o período de análise")
            return None, None
        
        # Encontrar quedas (método melhorado)
        drops = self.find_drops_advanced(df, min_drop)
        
        if len(drops) == 0:
            print(f"\n💡 DICA: Nenhuma queda de {min_drop}%+ detectada.")
            print(f"   Tente diminuir o threshold (ex: 3% ou 4%) para ver mais oportunidades.")
            return df, None
        
        # Analisar recuperação
        print(f"\n⏳ Analisando recuperação das quedas...\n")
        results = self.analyze_recovery(df, drops)
        
        # Estatísticas
        df_results = self.print_statistics(results)
        
        # Últimas oportunidades
        self.print_recent_opportunities(results)
        
        return df, df_results

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║      📊 ANÁLISE HISTÓRICA BTC/BRL - VERSÃO MELHORADA      ║
    ║              Múltiplos Métodos de Detecção                ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    analyzer = ImprovedBacktestAnalyzer()
    
    # Tentar com 5%, se não achar nada, tentar com 3%
    df, results = analyzer.run_analysis(days=180, min_drop=5.0)
    
    if results is None and df is not None:
        print("\n🔄 Tentando novamente com threshold de 3%...")
        drops = analyzer.find_drops_advanced(df, min_drop=3.0)
        if len(drops) > 0:
            results_list = analyzer.analyze_recovery(df, drops)
            analyzer.print_statistics(results_list)
            analyzer.print_recent_opportunities(results_list)
    
    if df is not None:
        print("\n✅ Análise concluída!")
        print("💡 Use essas estatísticas para ajustar config.py")

if __name__ == "__main__":
    main()
