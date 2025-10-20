"""
Monitor Automatizado BTC/BRL - Binance
Estratégia: Buy the Dip 5/3

Detecta quedas significativas e calcula alvos baseados em suportes/resistências históricos
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Tuple
import os

# Configurações
CONFIG = {
    'SYMBOL': 'BTCBRL',
    'QUEDA_MINIMA': 5.0,  # % mínima de queda para alertar
    'DISTANCIA_MA': 3.0,  # % de distância da média móvel para alertar
    'RSI_OVERSOLD': 30,   # RSI abaixo deste valor = sobrevendido
    'PERIODO_MA': 7,      # Dias para média móvel
    'STOP_LOSS': 3.0,     # % de stop loss sugerido
    'TAKE_PROFIT': 2.0,   # % mínimo de take profit
    'INTERVALO_CHECK': 300,  # Segundos entre cada verificação (5 min)
    'DIAS_HISTORICO': 90,  # Dias de histórico para análise
}

class BinanceMonitor:
    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.symbol = CONFIG['SYMBOL']
        self.last_alert_time = None
        self.price_history = []
        
    def get_current_price(self) -> float:
        """Busca o preço atual do BTC/BRL"""
        try:
            url = f"{self.base_url}/api/v3/ticker/price"
            params = {'symbol': self.symbol}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception as e:
            print(f"❌ Erro ao buscar preço: {e}")
            return None
    
    def get_24h_change(self) -> Dict:
        """Busca estatísticas das últimas 24h"""
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
            print(f"❌ Erro ao buscar dados 24h: {e}")
            return None
    
    def get_historical_klines(self, days: int = 90) -> pd.DataFrame:
        """Busca dados históricos (velas diárias)"""
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
            
            # Converter para DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Converter tipos
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        
        except Exception as e:
            print(f"❌ Erro ao buscar histórico: {e}")
            return None
    
    def calculate_support_resistance(self, df: pd.DataFrame, tolerance: float = 0.02) -> Tuple[List, List]:
        """
        Identifica suportes e resistências baseado em toques em níveis de preço
        tolerance: % de tolerância para agrupar níveis próximos
        """
        highs = df['high'].values
        lows = df['low'].values
        
        # Agrupar níveis próximos
        def cluster_levels(levels, tolerance):
            if len(levels) == 0:
                return []
            
            levels = sorted(levels)
            clusters = []
            current_cluster = [levels[0]]
            
            for level in levels[1:]:
                if abs(level - current_cluster[-1]) / current_cluster[-1] <= tolerance:
                    current_cluster.append(level)
                else:
                    clusters.append(np.mean(current_cluster))
                    current_cluster = [level]
            
            clusters.append(np.mean(current_cluster))
            return clusters
        
        # Contar toques em cada nível
        all_highs = cluster_levels(highs.tolist(), tolerance)
        all_lows = cluster_levels(lows.tolist(), tolerance)
        
        # Resistências (níveis altos tocados múltiplas vezes)
        resistances = sorted(all_highs, reverse=True)[:5]
        
        # Suportes (níveis baixos tocados múltiplas vezes)
        supports = sorted(all_lows, reverse=True)[:5]
        
        return supports, resistances
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calcula o RSI (Relative Strength Index)"""
        deltas = prices.diff()
        gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]
    
    def calculate_moving_average(self, df: pd.DataFrame, period: int) -> float:
        """Calcula média móvel simples"""
        return df['close'].tail(period).mean()
    
    def analyze_opportunity(self, current_price: float, stats_24h: Dict, df_historical: pd.DataFrame) -> Dict:
        """Analisa se há oportunidade de entrada"""
        
        analysis = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'price': current_price,
            'signals': [],
            'entry_signal': False,
            'target_price': None,
            'stop_loss': None,
            'score': 0
        }
        
        # 1. QUEDA DE 24H
        queda_24h = stats_24h['price_change_percent']
        if queda_24h <= -CONFIG['QUEDA_MINIMA']:
            analysis['signals'].append(f"🔴 QUEDA 24H: {queda_24h:.2f}% (mínimo: {-CONFIG['QUEDA_MINIMA']}%)")
            analysis['score'] += 3
        
        # 2. MÉDIA MÓVEL
        ma = self.calculate_moving_average(df_historical, CONFIG['PERIODO_MA'])
        distancia_ma = ((current_price - ma) / ma) * 100
        analysis['ma'] = ma
        analysis['distancia_ma'] = distancia_ma
        
        if distancia_ma <= -CONFIG['DISTANCIA_MA']:
            analysis['signals'].append(f"🔴 ABAIXO DA MA{CONFIG['PERIODO_MA']}: {distancia_ma:.2f}% (mínimo: {-CONFIG['DISTANCIA_MA']}%)")
            analysis['score'] += 2
        
        # 3. RSI
        rsi = self.calculate_rsi(df_historical['close'])
        analysis['rsi'] = rsi
        
        if rsi < CONFIG['RSI_OVERSOLD']:
            analysis['signals'].append(f"🔴 RSI OVERSOLD: {rsi:.1f} (limite: {CONFIG['RSI_OVERSOLD']})")
            analysis['score'] += 2
        
        # 4. SUPORTES E RESISTÊNCIAS
        supports, resistances = self.calculate_support_resistance(df_historical)
        analysis['supports'] = supports
        analysis['resistances'] = resistances
        
        # Verificar se está próximo de suporte
        for support in supports:
            diff_support = ((current_price - support) / support) * 100
            if -2 <= diff_support <= 2:  # Dentro de 2% do suporte
                analysis['signals'].append(f"🟡 PRÓXIMO DO SUPORTE: R$ {support:,.2f}")
                analysis['score'] += 1
                break
        
        # 5. CALCULAR ALVOS
        # Alvo = próxima resistência acima do preço atual
        target_resistance = None
        for resistance in sorted(resistances):
            if resistance > current_price:
                target_resistance = resistance
                break
        
        if target_resistance:
            profit_percent = ((target_resistance - current_price) / current_price) * 100
            if profit_percent >= CONFIG['TAKE_PROFIT']:
                analysis['target_price'] = target_resistance
                analysis['profit_percent'] = profit_percent
        
        # Se não achou resistência, usar % fixo
        if not analysis['target_price']:
            analysis['target_price'] = current_price * (1 + CONFIG['TAKE_PROFIT'] / 100)
            analysis['profit_percent'] = CONFIG['TAKE_PROFIT']
        
        # Stop loss
        # Usar próximo suporte abaixo ou % fixo
        stop_support = None
        for support in sorted(supports, reverse=True):
            if support < current_price:
                stop_support = support
                break
        
        if stop_support:
            stop_percent = ((current_price - stop_support) / current_price) * 100
            if stop_percent <= CONFIG['STOP_LOSS'] * 2:  # Se não for muito longe
                analysis['stop_loss'] = stop_support
                analysis['stop_percent'] = stop_percent
        
        if not analysis['stop_loss']:
            analysis['stop_loss'] = current_price * (1 - CONFIG['STOP_LOSS'] / 100)
            analysis['stop_percent'] = CONFIG['STOP_LOSS']
        
        # SINAL DE ENTRADA
        if analysis['score'] >= 3:  # Pelo menos 3 pontos de confirmação
            analysis['entry_signal'] = True
        
        return analysis
    
    def print_analysis(self, analysis: Dict):
        """Imprime análise formatada"""
        print("\n" + "="*80)
        print(f"⏰ {analysis['timestamp']}")
        print(f"💰 PREÇO ATUAL: R$ {analysis['price']:,.2f}")
        print("="*80)
        
        print(f"\n📊 INDICADORES:")
        print(f"   MA{CONFIG['PERIODO_MA']}: R$ {analysis['ma']:,.2f} ({analysis['distancia_ma']:+.2f}%)")
        print(f"   RSI(14): {analysis['rsi']:.1f}")
        
        if analysis['signals']:
            print(f"\n🚨 SINAIS DETECTADOS (Score: {analysis['score']}):")
            for signal in analysis['signals']:
                print(f"   {signal}")
        
        print(f"\n📍 NÍVEIS IMPORTANTES:")
        print(f"   Resistências: {', '.join([f'R$ {r:,.0f}' for r in analysis['resistances'][:3]])}")
        print(f"   Suportes: {', '.join([f'R$ {s:,.0f}' for s in analysis['supports'][:3]])}")
        
        if analysis['entry_signal']:
            print(f"\n{'🟢 OPORTUNIDADE DE ENTRADA DETECTADA! 🟢':^80}")
            print(f"\n💡 SUGESTÃO DE TRADE:")
            print(f"   🔹 ENTRADA: R$ {analysis['price']:,.2f}")
            print(f"   🎯 ALVO: R$ {analysis['target_price']:,.2f} (+{analysis['profit_percent']:.2f}%)")
            print(f"   🛑 STOP: R$ {analysis['stop_loss']:,.2f} (-{analysis['stop_percent']:.2f}%)")
            
            risk_reward = analysis['profit_percent'] / analysis['stop_percent']
            print(f"   📊 RISK/REWARD: 1:{risk_reward:.2f}")
        else:
            print(f"\n⚪ Nenhuma oportunidade clara no momento (Score: {analysis['score']}/7)")
        
        print("="*80 + "\n")
    
    def run_monitor(self):
        """Loop principal do monitor"""
        print("🤖 Monitor BTC/BRL Iniciado!")
        print(f"📡 Verificando a cada {CONFIG['INTERVALO_CHECK']} segundos...")
        print(f"⚙️  Configurações: Queda mínima {CONFIG['QUEDA_MINIMA']}%, RSI < {CONFIG['RSI_OVERSOLD']}\n")
        
        while True:
            try:
                # Buscar dados
                current_price = self.get_current_price()
                if not current_price:
                    time.sleep(30)
                    continue
                
                stats_24h = self.get_24h_change()
                if not stats_24h:
                    time.sleep(30)
                    continue
                
                # Buscar histórico (apenas de vez em quando para economizar requests)
                df_historical = self.get_historical_klines(CONFIG['DIAS_HISTORICO'])
                if df_historical is None or len(df_historical) == 0:
                    time.sleep(30)
                    continue
                
                # Analisar
                analysis = self.analyze_opportunity(current_price, stats_24h, df_historical)
                
                # Imprimir análise
                self.print_analysis(analysis)
                
                # Salvar log se houver sinal
                if analysis['entry_signal']:
                    self.save_signal_log(analysis)
                
                # Aguardar próxima verificação
                time.sleep(CONFIG['INTERVALO_CHECK'])
                
            except KeyboardInterrupt:
                print("\n👋 Monitor encerrado pelo usuário")
                break
            except Exception as e:
                print(f"❌ Erro no loop principal: {e}")
                time.sleep(60)
    
    def save_signal_log(self, analysis: Dict):
        """Salva sinais em arquivo de log"""
        log_file = 'signals_log.json'
        
        try:
            # Carregar logs existentes
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            # Adicionar novo sinal
            logs.append(analysis)
            
            # Salvar
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
            
            print(f"💾 Sinal salvo em {log_file}")
        
        except Exception as e:
            print(f"❌ Erro ao salvar log: {e}")

def main():
    monitor = BinanceMonitor()
    monitor.run_monitor()

if __name__ == "__main__":
    main()
