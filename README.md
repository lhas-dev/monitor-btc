# 🤖 Monitor Automatizado BTC/BRL - Binance

Sistema automatizado para identificar oportunidades de compra no Bitcoin (estratégia "Buy the Dip").

## 🎯 O que faz?

✅ Monitora o preço do BTC/BRL na Binance em tempo real  
✅ Detecta quedas significativas automaticamente  
✅ Calcula suportes e resistências baseados em histórico  
✅ Analisa indicadores técnicos (Média Móvel, RSI)  
✅ Sugere preço de entrada, alvo e stop loss  
✅ Sistema de pontuação para validar sinais  
✅ Salva alertas em arquivo JSON  

## 📋 Requisitos

- Python 3.7 ou superior
- Conexão com internet

## 🚀 Instalação

### 1. Instalar bibliotecas necessárias

Abra o terminal/prompt e execute:

```bash
pip install requests pandas numpy
```

### 2. Baixar os arquivos

Coloque os seguintes arquivos na mesma pasta:
- `monitor_btc.py` (arquivo principal)
- `config.py` (configurações)

## ⚙️ Configuração

Edite o arquivo `config.py` para ajustar sua estratégia:

```python
QUEDA_MINIMA = 5.0        # Alertar quando cair 5% em 24h
DISTANCIA_MA = 3.0        # Alertar quando ficar 3% abaixo da média
RSI_OVERSOLD = 30         # RSI abaixo de 30 = sobrevendido
PERIODO_MA = 7            # Média móvel de 7 dias
STOP_LOSS = 3.0           # Stop loss de 3%
TAKE_PROFIT = 2.0         # Alvo mínimo de 2%
INTERVALO_CHECK = 300     # Verificar a cada 5 minutos
```

## 🏃 Como Usar

### Executar o monitor:

```bash
python monitor_btc.py
```

### O que você verá:

```
🤖 Monitor BTC/BRL Iniciado!
📡 Verificando a cada 300 segundos...
⚙️  Configurações: Queda mínima 5.0%, RSI < 30

================================================================================
⏰ 2025-10-20 15:30:45
💰 PREÇO ATUAL: R$ 590.234,00
================================================================================

📊 INDICADORES:
   MA7: R$ 598.500,00 (-1.38%)
   RSI(14): 35.2

🚨 SINAIS DETECTADOS (Score: 5):
   🔴 QUEDA 24H: -5.80% (mínimo: -5.0%)
   🔴 ABAIXO DA MA7: -3.20% (mínimo: -3.0%)
   🟡 PRÓXIMO DO SUPORTE: R$ 588.000

📍 NÍVEIS IMPORTANTES:
   Resistências: R$ 605.000, R$ 600.000, R$ 595.000
   Suportes: R$ 590.000, R$ 585.000, R$ 580.000

                  🟢 OPORTUNIDADE DE ENTRADA DETECTADA! 🟢                  

💡 SUGESTÃO DE TRADE:
   🔹 ENTRADA: R$ 590.234,00
   🎯 ALVO: R$ 600.000,00 (+1.65%)
   🛑 STOP: R$ 572.527,00 (-3.00%)
   📊 RISK/REWARD: 1:0.55
================================================================================
```

### Parar o monitor:

Pressione `Ctrl + C` no terminal.

## 📊 Sistema de Pontuação

O monitor atribui pontos para cada sinal:

| Sinal | Pontos | Descrição |
|-------|--------|-----------|
| Queda 24h | 3 | Preço caiu mais que o mínimo configurado |
| Abaixo da MA | 2 | Preço está abaixo da média móvel |
| RSI Oversold | 2 | RSI indica sobrevendido |
| Próximo de Suporte | 1 | Preço está perto de suporte histórico |

**✅ SINAL DE ENTRADA:** Quando somar 3+ pontos

## 📁 Arquivos Gerados

### `signals_log.json`

Todos os sinais de entrada são salvos automaticamente neste arquivo:

```json
[
  {
    "timestamp": "2025-10-20 15:30:45",
    "price": 590234.0,
    "signals": [...],
    "entry_signal": true,
    "target_price": 600000.0,
    "stop_loss": 572527.0,
    "score": 5
  }
]
```

## 🎓 Dicas de Uso

### Personalização por Perfil

**Conservador:**
```python
QUEDA_MINIMA = 7.0
TAKE_PROFIT = 1.5
STOP_LOSS = 2.0
```

**Moderado (padrão):**
```python
QUEDA_MINIMA = 5.0
TAKE_PROFIT = 2.0
STOP_LOSS = 3.0
```

**Agressivo:**
```python
QUEDA_MINIMA = 3.0
TAKE_PROFIT = 3.0
STOP_LOSS = 4.0
```

### Horários Recomendados

- **Manhã (9h-12h):** Maior volatilidade, mais oportunidades
- **Tarde (14h-17h):** Movimentos mais calmos
- **Noite (20h-23h):** Influência do mercado americano

### Backtesting Manual

Você pode analisar o histórico editando a data no código:

```python
# No arquivo monitor_btc.py, linha ~200
# Altere para analisar uma data específica
```

## 🔧 Solução de Problemas

### Erro: "No module named 'requests'"
```bash
pip install requests
```

### Erro: "Connection timeout"
- Verifique sua conexão com internet
- A API da Binance pode estar temporariamente indisponível

### Muitos alertas falsos
- Aumente o `QUEDA_MINIMA` no config.py
- Aumente o score mínimo para entrada (editar linha 200 do código)

### Poucos alertas
- Diminua o `QUEDA_MINIMA`
- Diminua o `INTERVALO_CHECK` para verificar mais frequentemente

## 📈 Próximos Passos

Depois de usar o monitor por alguns dias:

1. **Analise o `signals_log.json`**
   - Veja quais sinais foram lucrativos
   - Ajuste os parâmetros com base nos resultados

2. **Adicione notificações**
   - Telegram: Use a biblioteca `python-telegram-bot`
   - Email: Use `smtplib`
   - Som: Use `winsound` (Windows) ou `playsound`

3. **Automatize ordens**
   - Integre com API da Binance para executar trades
   - ⚠️ **Use com EXTREMO CUIDADO!**

## ⚠️ Avisos Importantes

- Este é um **monitor educacional**, não um robô de trading
- **Sempre analise** os sinais antes de operar
- Mercado de cripto é **altamente volátil**
- **Nunca invista** mais do que pode perder
- Use **stop loss** em todas as operações
- Este código **NÃO executa trades automaticamente**

## 📞 Suporte

Dúvidas? Ajuste os parâmetros no `config.py` e teste!

---

**Desenvolvido para estratégia "Buy the Dip 5/3"**  
*Monitore quedas, compre no suporte, venda na resistência* 🚀
