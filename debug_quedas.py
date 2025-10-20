"""
Debug - Análise de Quedas BTC/BRL
Verifica as maiores variações diárias para identificar o problema
"""

import requests
import pandas as pd
from datetime import datetime, timedelta

def get_historical_data(days: int = 180):
    """Busca dados históricos"""
    print(f"📥 Baixando {days} dias de dados...")
    
    base_url = "https://api.binance.com"
    symbol = "BTCBRL"
    
    url = f"{base_url}/api/v3/klines"
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    params = {
        'symbol': symbol,
        'interval': '1d',
        'startTime': start_time,
        'endTime': end_time,
        'limit': 1000
    }
    
    response = requests.get(url, params=params, timeout=10)
    
    # Debug: verificar resposta
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Erro na API: {response.text}")
        return None
    
    try:
        data = response.json()
    except Exception as e:
        print(f"Erro ao fazer parse JSON: {e}")
        print(f"Resposta: {response.text[:200]}")
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

def analyze_variations(df):
    """Analisa todos os tipos de variações"""
    
    print("="*80)
    print("🔍 ANÁLISE DE VARIAÇÕES")
    print("="*80)
    
    # 1. Variação de fechamento (close to close)
    df['change_close'] = df['close'].pct_change() * 100
    
    # 2. Variação intraday (high to low do mesmo dia)
    df['change_intraday'] = ((df['low'] - df['high']) / df['high']) * 100
    
    # 3. Variação de abertura para fechamento
    df['change_day'] = ((df['close'] - df['open']) / df['open']) * 100
    
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   Período: {df['date'].min()} até {df['date'].max()}")
    print(f"   Preço atual: R$ {df['close'].iloc[-1]:,.2f}")
    print(f"   Maior preço: R$ {df['high'].max():,.2f}")
    print(f"   Menor preço: R$ {df['low'].min():,.2f}")
    
    # Maiores quedas close-to-close
    print(f"\n📉 MAIORES QUEDAS (FECHAMENTO a FECHAMENTO):")
    quedas_close = df[['date', 'close', 'change_close']].sort_values('change_close').head(10)
    for idx, row in quedas_close.iterrows():
        print(f"   {row['date']}: {row['change_close']:+.2f}% (R$ {row['close']:,.2f})")
    
    # Maiores quedas intraday
    print(f"\n📉 MAIORES QUEDAS (ALTA → BAIXA DO DIA):")
    quedas_intra = df[['date', 'high', 'low', 'change_intraday']].sort_values('change_intraday').head(10)
    for idx, row in quedas_intra.iterrows():
        print(f"   {row['date']}: {row['change_intraday']:+.2f}% (R$ {row['high']:,.0f} → R$ {row['low']:,.0f})")
    
    # Maiores quedas no dia (abertura → fechamento)
    print(f"\n📉 MAIORES QUEDAS (ABERTURA → FECHAMENTO):")
    quedas_day = df[['date', 'open', 'close', 'change_day']].sort_values('change_day').head(10)
    for idx, row in quedas_day.iterrows():
        print(f"   {row['date']}: {row['change_day']:+.2f}% (R$ {row['open']:,.0f} → R$ {row['close']:,.0f})")
    
    # Contar quedas por tipo
    quedas_5_close = len(df[df['change_close'] <= -5.0])
    quedas_5_intra = len(df[df['change_intraday'] <= -5.0])
    quedas_5_day = len(df[df['change_day'] <= -5.0])
    
    print(f"\n🎯 QUANTIDADE DE QUEDAS ≥5%:")
    print(f"   Fechamento → Fechamento: {quedas_5_close}")
    print(f"   Alta → Baixa (intraday): {quedas_5_intra}")
    print(f"   Abertura → Fechamento: {quedas_5_day}")
    
    # Análise de quedas de 3% e 4%
    print(f"\n📊 QUEDAS POR MAGNITUDE (Fechamento → Fechamento):")
    for threshold in [3.0, 4.0, 5.0, 6.0, 7.0]:
        count = len(df[df['change_close'] <= -threshold])
        print(f"   ≥{threshold}%: {count} quedas")
    
    print("\n" + "="*80)
    
    # Análise de drawdowns (quedas de pico a vale)
    print("\n📉 ANALISANDO DRAWDOWNS (PICO → VALE)...")
    print("="*80)
    
    df['cummax'] = df['high'].cummax()
    df['drawdown'] = ((df['low'] - df['cummax']) / df['cummax']) * 100
    
    # Encontrar maiores drawdowns
    major_drawdowns = df[df['drawdown'] <= -5.0].copy()
    
    print(f"\n🔴 DRAWDOWNS ≥5% (de pico histórico até vale):")
    print(f"   Total: {len(major_drawdowns)} ocorrências")
    
    if len(major_drawdowns) > 0:
        print(f"\n   Maiores drawdowns:")
        for idx, row in major_drawdowns.nlargest(10, 'drawdown', keep='last').iterrows():
            print(f"   {row['date']}: {row['drawdown']:.2f}% (vale: R$ {row['low']:,.0f})")
    
    return df

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║              🔍 DEBUG - ANÁLISE DE QUEDAS BTC/BRL         ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    df = get_historical_data(180)
    df_analyzed = analyze_variations(df)
    
    print("\n💡 CONCLUSÃO:")
    print("   Se não aparecerem quedas de 5%+ no 'Fechamento → Fechamento',")
    print("   isso significa que o BTC não teve quedas tão bruscas de um dia para outro.")
    print("   Mas ele pode ter tido drawdowns maiores ao longo de vários dias!")
    print("\n   Vou atualizar o código para detectar ambos os tipos de queda.")

if __name__ == "__main__":
    main()
