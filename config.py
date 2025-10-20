# ⚙️ CONFIGURAÇÕES DO MONITOR BTC/BRL
# Edite os valores abaixo conforme sua estratégia

# === PARÂMETROS DE DETECÇÃO ===

# Queda mínima em 24h para gerar alerta (%)
QUEDA_MINIMA = 5.0

# Distância da média móvel para alertar (%)
# Ex: 3.0 = alertar quando preço estiver 3% abaixo da média
DISTANCIA_MA = 3.0

# RSI abaixo deste valor indica sobrevendido
RSI_OVERSOLD = 30

# Período da média móvel (dias)
PERIODO_MA = 7


# === GESTÃO DE RISCO ===

# Stop loss sugerido (%)
STOP_LOSS = 3.0

# Take profit mínimo para considerar trade válido (%)
TAKE_PROFIT = 2.0


# === MONITORAMENTO ===

# Intervalo entre verificações (segundos)
# 300 = 5 minutos
# 60 = 1 minuto
# 3600 = 1 hora
INTERVALO_CHECK = 300

# Dias de histórico para análise
DIAS_HISTORICO = 90


# === SISTEMA DE PONTUAÇÃO ===
# O monitor soma pontos para cada sinal detectado:
# - Queda 24h: 3 pontos
# - Abaixo da MA: 2 pontos
# - RSI oversold: 2 pontos
# - Próximo de suporte: 1 ponto
# 
# ENTRADA SUGERIDA: 3+ pontos
