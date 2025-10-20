# 🚀 GUIA RÁPIDO - COMECE EM 3 MINUTOS

## 📦 Passo 1: Instalar Dependências

Abra o terminal/prompt de comando e cole:

```bash
pip install requests pandas numpy
```

Aguarde a instalação terminar.

---

## ⚙️ Passo 2: Configurar Estratégia

Abra o arquivo `config.py` e ajuste:

```python
QUEDA_MINIMA = 5.0      # Alertar quando cair 5% em 24h
INTERVALO_CHECK = 300   # Verificar a cada 5 minutos
```

**Pronto!** Os valores padrão já funcionam bem.

---

## ▶️ Passo 3: Rodar o Monitor

No terminal, execute:

```bash
python monitor_btc.py
```

Você verá algo assim:

```
🤖 Monitor BTC/BRL Iniciado!
📡 Verificando a cada 300 segundos...

💰 PREÇO ATUAL: R$ 590.234,00
📊 INDICADORES:
   MA7: R$ 598.500,00 (-1.38%)
   RSI(14): 35.2

⚪ Nenhuma oportunidade clara no momento (Score: 2/7)
```

O monitor vai **rodar continuamente** e avisar quando houver oportunidades!

---

## 🎯 Quando aparecer um sinal

```
🟢 OPORTUNIDADE DE ENTRADA DETECTADA! 🟢

💡 SUGESTÃO DE TRADE:
   🔹 ENTRADA: R$ 590.234,00
   🎯 ALVO: R$ 600.000,00 (+1.65%)
   🛑 STOP: R$ 572.527,00 (-3.00%)
```

**Analise** o sinal e decida se vai operar na Binance.

---

## 🛑 Parar o Monitor

Pressione `Ctrl + C` no terminal.

---

## 📊 EXTRA: Analisar Histórico

Para ver como a estratégia teria funcionado no passado:

```bash
python analise_historica.py
```

Isso mostra:
- Taxa de recuperação após quedas
- Tempo médio de recuperação
- Win rate da estratégia
- Últimas 10 oportunidades

---

## 🆘 Problemas?

### Erro: "No module named 'requests'"
```bash
pip install requests pandas numpy
```

### Monitor não detecta nada
- Espere alguns minutos
- O BTC precisa realmente cair 5%+ para alertar
- Ajuste `QUEDA_MINIMA` no config.py para valores menores

### Quer notificações sonoras?
Edite `monitor_btc.py` e adicione:
```python
import winsound  # Windows
winsound.Beep(1000, 1000)  # Após linha "OPORTUNIDADE DETECTADA"
```

---

## ✅ Checklist

- [ ] Instalei as dependências (`pip install...`)
- [ ] Configurei o `config.py`
- [ ] Rodei `python monitor_btc.py`
- [ ] Monitor está rodando continuamente
- [ ] Entendi que preciso **analisar** antes de operar

---

## 🎓 Próximos Passos

1. **Deixe rodar por 1 semana** - Observe os sinais
2. **Analise o histórico** - Execute `analise_historica.py`
3. **Ajuste parâmetros** - Melhore baseado nos resultados
4. **Opere com disciplina** - Use sempre stop loss

---

**🚀 Pronto! Seu monitor está funcionando!**

*Deixe o terminal aberto para o monitor continuar rodando.*
