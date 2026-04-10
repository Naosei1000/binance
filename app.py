import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import time
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore
import yfinance as yf
import streamlit.components.v1 as components  
import re
import uuid
import pandas as pd
import random
import numpy as np
import requests

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E LUXUOSA DO SITE (Foco Mobile)
# ==============================================================================
st.set_page_config(page_title="NEXUS QUANTUM", page_icon="💠", layout="centered")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(-45deg, #070b14, #0f172a, #070b14, #000000);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="StyledFullScreenButton"] {display: none;}
    
    .nexus-logo {
        text-align: center; font-size: 2.8rem; font-weight: 800; letter-spacing: 8px;
        margin-top: -3rem; margin-bottom: 1rem;
        background: linear-gradient(to right, #4facfe 0%, #00ff88 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: pulse 2.5s infinite;
        text-shadow: 0px 0px 15px rgba(0, 255, 136, 0.2);
    }
    .nexus-logo span {
        font-size: 1.2rem; letter-spacing: 3px; color: #e2e8f0;
        -webkit-text-fill-color: #e2e8f0; vertical-align: middle; margin-left: 5px;
    }
    @keyframes pulse {
        0% { opacity: 0.8; text-shadow: 0px 0px 15px rgba(0, 255, 136, 0.2); }
        50% { opacity: 1; text-shadow: 0px 0px 25px rgba(0, 255, 136, 0.6); }
        100% { opacity: 0.8; text-shadow: 0px 0px 15px rgba(0, 255, 136, 0.2); }
    }
    [data-testid="stChatMessage"] {
        background-color: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(0, 255, 136, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important; margin-bottom: 1rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    .stButton > button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white; border: 1px solid rgba(0, 255, 136, 0.3) !important;
        border-radius: 8px !important; height: 100%; width: 100%;
        font-weight: 700; transition: all 0.3s ease;
    }
    .stToggle { margin-bottom: 1rem; }
    
    /* Barra de progresso do cronômetro mais visível */
    .stProgress > div > div > div > div {
        background-color: #00ff88;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SESSÃO DO USUÁRIO E VARIÁVEIS GLOBAIS
# ==============================================================================
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4()) # Isolamento por aba/usuário
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_op_id" not in st.session_state:
    st.session_state.last_op_id = None
if "last_ativo" not in st.session_state:
    st.session_state.last_ativo = None
if "next_auto_run" not in st.session_state:
    st.session_state.next_auto_run = 0

# ==============================================================================
# 2. CONFIGURAÇÃO DAS APIS E BANCO DE DADOS
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    
    genai.configure(api_key=GOOGLE_API_KEY)
    groq_client = Groq(api_key=GROQ_API_KEY)

    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()

except Exception as e:
    st.error(f"🚨 Falha na ignição: Configure as variáveis no Secrets. Detalhe: {e}")
    st.stop()

# ==============================================================================
# 3. AUTO-ATUALIZAÇÃO QUÂNTICA (MACRO, SAZONALIDADE 5 ANOS, ATR E NOTÍCIAS)
# ==============================================================================
@st.cache_data(ttl=43200) 
def atualizar_memoria_nexus_background():
    try:
        moedas_macro = ["BTC-USD", "ETH-USD", "EURUSD=X", "GC=F", "^AXJO"] 
        mes_atual = datetime.now().month
        
        for ticker in moedas_macro:
            ativo = yf.Ticker(ticker)
            historico_5a = ativo.history(period="5y") 
            
            if historico_5a.empty:
                continue
                
            hist_mes = historico_5a[historico_5a.index.month == mes_atual]
            dias_green = sum(1 for _, row in hist_mes.iterrows() if row['Close'] > row['Open'])
            total_dias = len(hist_mes)
            winrate_sazonal = (dias_green / total_dias * 100) if total_dias > 0 else 50
            
            historico_5a['TR'] = historico_5a['High'] - historico_5a['Low']
            atr_200 = float(historico_5a['TR'].tail(200).mean())

            noticias = ativo.news
            titulos_noticias = [n['title'] for n in noticias[:3]] if noticias else ["Nenhuma notícia relevante."]
            sentimento_bruto = " / ".join(titulos_noticias)
            
            bias_institucional = "ALTA" if any(x in sentimento_bruto.upper() for x in ["ETF", "SEC", "WHALE", "GOVERNMENT", "FED"]) else "NEUTRO"

            linha_hoje = historico_5a.iloc[-1]
            data_str = datetime.now().strftime('%Y-%m-%d')
            tendencia = "ALTA" if linha_hoje["Close"] > linha_hoje["Open"] else "BAIXA"
            
            dados_macro = {
                "ativo": ticker,
                "data": data_str,
                "tendencia_diaria": tendencia,
                "sazonalidade_mes": round(winrate_sazonal, 1),
                "atr_200": atr_200,
                "bias_whales": bias_institucional,
                "abertura": float(linha_hoje["Open"]),
                "fechamento": float(linha_hoje["Close"]),
                "ultimas_noticias": sentimento_bruto 
            }
            db.collection("historico_macro").document(f"{ticker}_{data_str}").set(dados_macro)
        return True
    except Exception as e:
        return False

atualizar_memoria_nexus_background()

# ==============================================================================
# 4. FUNÇÕES DE APRENDIZADO, SEGURANÇA E CRONÔMETRO DIÁRIO
# ==============================================================================

def exibir_cronometro_cota_diaria(mensagem_erro):
    """Exibe um cronômetro visual em JavaScript até a meia-noite UTC (Reset de Cota)"""
    agora = datetime.now(timezone.utc)
    amanha = agora + timedelta(days=1)
    meia_noite = datetime(amanha.year, amanha.month, amanha.day, tzinfo=timezone.utc)
    segundos_restantes = int((meia_noite - agora).total_seconds())

    st.error(mensagem_erro)
    
    html_cronometro = f"""
    <div style="background-color: rgba(15, 23, 42, 0.9); border: 1px solid #ff4b4b; border-radius: 12px; padding: 25px; text-align: center; color: white; font-family: 'Inter', sans-serif;">
        <h4 style="margin-top: 0; color: #ff4b4b; font-size: 1.1rem; text-transform: uppercase;">⏳ Reset do Limite Diário (UTC):</h4>
        <h1 id="timer_diario" style="font-family: monospace; letter-spacing: 5px; color: #00ff88; font-size: 3.5rem; margin: 15px 0; text-shadow: 0px 0px 10px rgba(0, 255, 136, 0.4);">00:00:00</h1>
        <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 0;">Você pode deixar esta página aberta. O sistema avisará quando recarregar.</p>
        <script>
            var timeLeft = {segundos_restantes};
            var timerEl = document.getElementById('timer_diario');
            var countdown = setInterval(function() {{
                if(timeLeft <= 0) {{ 
                    timerEl.innerHTML = "RECARREGADO!"; 
                    timerEl.style.color = "#00ff88";
                    clearInterval(countdown);
                    return; 
                }}
                timeLeft--;
                var h = Math.floor(timeLeft / 3600);
                var m = Math.floor((timeLeft % 3600) / 60);
                var s = timeLeft % 60;
                timerEl.innerHTML = (h < 10 ? "0" + h : h) + ":" + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
            }}, 1000);
        </script>
    </div>
    """
    components.html(html_cronometro, height=250)
    st.stop()


def buscar_performance_nexus(ativo):
    try:
        # Consulta amarrada ao ID do usuário
        docs = db.collection("resultados_nexus").where("ativo", "==", ativo).where("user_id", "==", st.session_state.user_id).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).get()
        if not docs: 
            return {"texto": "Sem histórico de operações recente.", "loss_sequence": 0, "wins": 0}
        
        resultados = [d.to_dict().get("resultado") for d in docs]
        wins = resultados.count("WIN")
        total = len(docs)
        taxa = (wins / total) * 100
        
        loss_seq = 0
        for r in resultados:
            if r == "LOSS": loss_seq += 1
            else: break
            
        return {"texto": f"Últimas {total} ops: {wins} WINs (Taxa: {taxa:.0f}%).", "loss_sequence": loss_seq, "wins": wins}
    except Exception as e:
        return {"texto": "Erro ao carregar memória.", "loss_sequence": 0, "wins": 0}

def salvar_resultado(id_op, ativo, resultado):
    db.collection("resultados_nexus").document(id_op).set({
        "ativo": ativo, 
        "resultado": resultado, 
        "user_id": st.session_state.user_id, # Registra quem fez a operação
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def traduzir_nome_visual_para_ticker(nome_visual):
    nome = nome_visual.upper()
    if "EUR" in nome and "USD" in nome: return "EURUSD=X"
    if "OURO" in nome or "GOLD" in nome: return "GC=F"
    if "AUS 200" in nome or "AUS" in nome: return "^AXJO"
    if "BTC" in nome or "BITCOIN" in nome: return "BTC-USD"
    if "ETH" in nome or "ETHEREUM" in nome: return "ETH-USD"
    return "BTC-USD"

# ==============================================================================
# 5. MÓDULO HFT DA BINANCE E O CÉREBRO MATEMÁTICO
# ==============================================================================
def puxar_grafico_binance(simbolo="BTCUSDT", intervalo="5m", limite=100):
    url = "https://api.binance.us/api/v3/klines"
    parametros = {"symbol": simbolo, "interval": intervalo, "limit": limite}
    
    try:
        resposta = requests.get(url, params=parametros, timeout=5)
        
        if resposta.status_code != 200:
            st.error(f"Erro API Binance: Código {resposta.status_code} - Detalhe: {resposta.text}") 
            return pd.DataFrame()
            
        dados = resposta.json()
        colunas = ['Tempo_Abertura', 'Open', 'High', 'Low', 'Close', 'Volume_Cripto',
                   'Tempo_Fechamento', 'Volume_Financeiro', 'Numero_Trades',
                   'Compra_Agressiva_Cripto', 'Compra_Agressiva_Financeiro', 'Ignorar']
        
        df = pd.DataFrame(dados, columns=colunas)
        colunas_numericas = ['Open', 'High', 'Low', 'Close', 'Volume_Financeiro']
        df[colunas_numericas] = df[colunas_numericas].astype(float)
        
        return df[['Open', 'High', 'Low', 'Close', 'Volume_Financeiro']]
    except Exception as e:
        st.error(f"Erro Técnico no Nexus (Requests falhou): {e}")
        return pd.DataFrame()

def processar_timeframe(df, usa_volume_binance=False):
    c = df['Close'].to_numpy()
    o = df['Open'].to_numpy()
    h = df['High'].to_numpy()
    l = df['Low'].to_numpy()

    # TRAVA DE SEGURANÇA MATEMÁTICA
    if len(c) < 21:
        preco_atual = float(c[-1]) if len(c) > 0 else 0
        return preco_atual, 50.0, "NEUTRA (Falta de Dados)", "NÃO", "NÃO"

    delta = np.diff(c)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    if len(gain) > 14:
        avg_gain = np.convolve(gain, np.ones(14)/14, mode='valid')[-1]
        avg_loss = np.convolve(loss, np.ones(14)/14, mode='valid')[-1]
        rsi_atual = 100 - (100 / (1 + (avg_gain / avg_loss))) if avg_loss != 0 else 100.0
    else:
        rsi_atual = 50.0

    ema_9_atual = np.mean(c[-9:])
    ema_21_atual = np.mean(c[-21:])

    preco_atual = float(c[-1])
    tendencia = "ALTA" if ema_9_atual > ema_21_atual else "BAIXA"

    corpo = abs(float(c[-1]) - float(o[-1]))
    p_sup = float(h[-1]) - max(float(o[-1]), float(c[-1]))
    p_inf = min(float(o[-1]), float(c[-1])) - float(l[-1])

    if usa_volume_binance and 'Volume_Financeiro' in df.columns:
        v = df['Volume_Financeiro'].to_numpy()
        vol_atual = v[-1]
        avg_vol = np.mean(v[-20:]) if len(v) >= 20 else vol_atual

        if p_sup > (corpo * 2.5) and vol_atual > (avg_vol * 1.2):
            sweep_alta = "SIM (ALTA LIQUIDEZ / ABSORÇÃO)"
        elif p_sup > (corpo * 2.5):
            sweep_alta = "SIM (Volume Normal)"
        else:
            sweep_alta = "NÃO"

        if p_inf > (corpo * 2.5) and vol_atual > (avg_vol * 1.2):
            sweep_baixa = "SIM (ALTA LIQUIDEZ / ABSORÇÃO)"
        elif p_inf > (corpo * 2.5):
            sweep_baixa = "SIM (Volume Normal)"
        else:
            sweep_baixa = "NÃO"
    else:
        sweep_alta = "SIM" if p_sup > (corpo * 2.5) else "NÃO"
        sweep_baixa = "SIM" if p_inf > (corpo * 2.5) else "NÃO"

    return preco_atual, rsi_atual, tendencia, sweep_alta, sweep_baixa

def ler_dados_mercado_ao_vivo_multi_tf(ticker):
    try:
        if "BTC" in ticker or "ETH" in ticker:
            simbolo_binance = ticker.replace("-USD", "USDT")
            
            df_m5 = puxar_grafico_binance(simbolo_binance, "5m", 100)
            df_m30 = puxar_grafico_binance(simbolo_binance, "30m", 100)
            df_h1 = puxar_grafico_binance(simbolo_binance, "1h", 100)
            df_d1 = puxar_grafico_binance(simbolo_binance, "1d", 60)
            
            if df_m5.empty or df_m30.empty or df_h1.empty or df_d1.empty:
                return "FALHA_DE_DADOS"

            p_m5, rsi_m5, t_m5, sa_m5, sb_m5 = processar_timeframe(df_m5, usa_volume_binance=True)
            _, rsi_m30, t_m30, _, _ = processar_timeframe(df_m30, usa_volume_binance=True)
            _, rsi_h1, t_h1, _, _ = processar_timeframe(df_h1, usa_volume_binance=True)
            _, rsi_d1, t_d1, _, _ = processar_timeframe(df_d1, usa_volume_binance=True)
            
            origem_dados = "BINANCE API (HFT)"

        else:
            ativo = yf.Ticker(ticker)
            df_m5 = ativo.history(period="3d", interval="5m")
            time.sleep(0.5)
            df_m30 = ativo.history(period="10d", interval="30m")
            time.sleep(0.5)
            df_h1 = ativo.history(period="20d", interval="1h")
            time.sleep(0.5)
            df_d1 = ativo.history(period="2mo", interval="1d")

            if df_m5.empty or df_m30.empty or df_h1.empty or df_d1.empty: 
                return "FALHA_DE_DADOS"

            p_m5, rsi_m5, t_m5, sa_m5, sb_m5 = processar_timeframe(df_m5, usa_volume_binance=False)
            _, rsi_m30, t_m30, _, _ = processar_timeframe(df_m30, usa_volume_binance=False)
            _, rsi_h1, t_h1, _, _ = processar_timeframe(df_h1, usa_volume_binance=False)
            _, rsi_d1, t_d1, _, _ = processar_timeframe(df_d1, usa_volume_binance=False)
            
            origem_dados = "YAHOO FINANCE"

        resumo_dados = f"""
        * LEITURA MULTI-TIMEFRAME ({origem_dados}):
        - Preço Atual: {p_m5:.4f}
        
        - TENDÊNCIA MACRO (D1): {t_d1} | RSI: {rsi_d1:.1f}
        - TENDÊNCIA MÉDIA (H1): {t_h1} | RSI: {rsi_h1:.1f}
        - TENDÊNCIA CURTA (M30): {t_m30} | RSI: {rsi_m30:.1f}
        - TENDÊNCIA MICRO (M5): {t_m5} | RSI: {rsi_m5:.1f}
        
        - Manipulação Detectada no M5 (Sweep Baixa): {sb_m5}
        - Manipulação Detectada no M5 (Sweep Alta): {sa_m5}
        """
        return resumo_dados
    except Exception as e:
        return "FALHA_DE_DADOS"

# ==============================================================================
# 5.5 HUB DE CORRETORAS E GRÁFICO AO VIVO CENTRAL (SEMPRE VISÍVEL)
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS <span>QUANTUM</span></div>', unsafe_allow_html=True)

st.markdown("### 📡 RADAR DE OPERAÇÕES E CORRETORA")

col_ativo, col_corretora = st.columns(2)
with col_ativo:
    ativo_live = st.selectbox("Ativo para Monitorar:", ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "FX:EURUSD", "OANDA:XAUUSD"])
with col_corretora:
    corretora_selecionada = st.selectbox("Conectar Corretora Real (Via API):", ["Yahoo Finance (Padrão/Gratuito)", "Binance", "Bybit", "OKX", "IQ Option"])

api_key_input = st.text_input("Sua Chave API (Opcional - Requerido para operações reais futuras)", type="password", placeholder="Insira a API Key da sua corretora...")

if st.button("SINCRONIZAR DADOS"):
    st.toast(f"Conectando ao terminal {corretora_selecionada}...", icon="⚡")
    time.sleep(1)
    st.success("✅ Conexão Simulada Estabelecida. Gráfico e Scanner prontos para leitura.")

simbolo_tv = ativo_live
html_grafico = f"""
<div class="tradingview-widget-container">
  <div id="tradingview_nexus"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {{
  "width": "100%", "height": 450, "symbol": "{simbolo_tv}", "interval": "5", "timezone": "Etc/UTC",
  "theme": "dark", "style": "1", "locale": "br", "enable_publishing": false,
  "backgroundColor": "rgba(15, 23, 42, 0.7)", "gridColor": "rgba(0, 255, 136, 0.05)",
  "hide_top_toolbar": false, "save_image": false, "container_id": "tradingview_nexus"
  }}
  );
  </script>
</div>
"""
components.html(html_grafico, height=450)
st.markdown("---")

# ==============================================================================
# 6. O PILOTO AUTOMÁTICO E CHAT MANUAL
# ==============================================================================

# O HISTÓRICO DE MENSAGENS AGORA FICA AQUI EM CIMA PARA APARECER EM TODOS OS MODOS
for message in st.session_state.messages:
    if message["role"] != "system":
        icone_avatar = "🧑‍💻" if message["role"] == "user" else "💠"
        with st.chat_message(message["role"], avatar=icone_avatar):
            st.markdown(message["content"])

auto_mode = st.toggle("🟢 ATIVAR PILOTO AUTOMÁTICO (VARREDURA MULTI-TIMEFRAME CONSTANTE)")

if auto_mode:
    # --- MODO 1: O ROBÔ LÊ O MERCADO SOZINHO VIA DADOS (HFT MULTI-TIMEFRAME) ---
    tempo_agora = time.time()
    
    if tempo_agora >= st.session_state.next_auto_run:
        with st.spinner("📡 SCANNER ATIVADO: Puxando histórico Multi-Timeframe da corretora..."):
            
            ativo_para_ler = "BTC-USD" if "BTC" in ativo_live else "ETH-USD"
            if "EUR" in ativo_live: ativo_para_ler = "EURUSD=X"
            if "XAU" in ativo_live: ativo_para_ler = "GC=F"
            
            fuso_br = timezone(timedelta(hours=-3))
            hora_atual = datetime.now(fuso_br).strftime('%H:%M:%S')

            dados_matematicos = ler_dados_mercado_ao_vivo_multi_tf(ativo_para_ler)
            perf = buscar_performance_nexus(ativo_para_ler)
            
            if perf["loss_sequence"] >= 5:
                st.error("🚨 KILL SWITCH ATIVADO: 5 Perdas Seguidas. Piloto Automático Desligado.")
                st.stop()
                
            if "FALHA_DE_DADOS" in dados_matematicos:
                 st.error("⚠️ O servidor limitou as requisições (Anti-Spam). O Nexus aguardará o próximo ciclo para tentar novamente.")
            else:
                doc = db.collection("historico_macro").document(f"{ativo_para_ler}_{datetime.now().strftime('%Y-%m-%d')}").get()
                macro_info = doc.to_dict() if doc.exists else "Macro Indisponível"
                
                # =========================================================
                # ATUALIZAÇÃO 1: PROMPT DO MODO AUTOMÁTICO BEM MASTIGADO
                # =========================================================
                inst_auto = """
                Você é o Algoritmo Nexus.
                Sua missão é dar o sinal de forma EXTREMAMENTE FÁCIL, MASTIGADA E DIRETA, como se estivesse guiando um iniciante absoluto passo a passo. 
                Nada de jargões confusos. Diga exatamente onde clicar e quando fechar.
                
                REGRAS DE SINAL:
                1. Só recomende COMPRA se H1 e M30 estiverem em ALTA, e o M5 tiver RSI baixo ou Sweep.
                2. Só recomende VENDA se H1 e M30 estiverem em BAIXA, e o M5 tiver RSI alto ou Sweep.
                3. Se não houver alinhamento H1/M30/M5, a ordem é AGUARDAR.

                FORMATO OBRIGATÓRIO (Siga exatamente este formato):
                
                ### [🟢 APERTE COMPRAR (Verde) / 🔴 APERTE VENDER (Vermelho) / 🟡 FIQUE DE FORA]
                **🪙 Moeda/Ativo:** [Nome da Moeda, ex: BTC/USD]
                **⏱️ Tempo Gráfico:** Coloque no M5 (Velas de 5 minutos)
                **🎯 O Que Fazer Agora:** [Ex: Vá na sua corretora AGORA e clique no botão de COMPRAR / VENDER]
                **🛑 Quando Fechar a Operação:** [Ex: Feche a operação manualmente assim que estiver no lucro no Alvo X, ou saia IMEDIATAMENTE se o preço for contra e bater no Stop Loss Y para proteger seu dinheiro.]
                
                *Por que entrar?* [Explique em 1 frase muito simples e fácil de entender o porquê da operação]
                """
                
                prompt_final = f"MOEDA: {ativo_para_ler}\nDADOS:\n{dados_matematicos}\nMACRO:\n{macro_info}\nPERF:\n{perf['texto']}\nHORARIO ATUAL: {hora_atual}"
                
                try:
                    resposta = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": inst_auto}, {"role": "user", "content": prompt_final}],
                        temperature=0.1, max_tokens=350
                    ).choices[0].message.content
                    
                    # SALVANDO A RESPOSTA NO HISTÓRICO ANTES DE ATUALIZAR A PÁGINA
                    st.session_state.messages.append({"role": "assistant", "content": f"**[🤖 MODO AUTOMÁTICO - {hora_atual}]**\n\n{resposta}"})
                    
                    st.session_state.last_op_id = str(uuid.uuid4())
                    st.session_state.last_ativo = ativo_para_ler
                    
                    # Define próxima execução
                    st.session_state.next_auto_run = time.time() + 60
                    st.rerun()
                    
                except Exception as e:
                    erro_str = str(e)
                    # VERIFICAÇÃO INTELIGENTE DE COTA NO MODO AUTOMÁTICO ORIGINAL
                    if "429" in erro_str or "Quota exceeded" in erro_str:
                        delay_match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)\s*\}', erro_str)
                        wait_seconds = int(delay_match.group(1)) if delay_match else None
                        
                        if wait_seconds and wait_seconds < 300: # Cota de Minuto
                            st.warning(f"⚠️ Limite por minuto da IA atingido. Resfriando por {wait_seconds}s...")
                            cooldown_ph = st.empty()
                            cbar = st.progress(0.0)
                            for sec in range(wait_seconds, 0, -1):
                                cooldown_ph.info(f"⏳ Recarregando API para evitar sobrecarga: **{sec}s**")
                                cbar.progress((wait_seconds - sec) / wait_seconds)
                                time.sleep(1)
                            cooldown_ph.empty()
                            cbar.empty()
                            st.rerun()
                        else: # Cota Diária
                            exibir_cronometro_cota_diaria("🚨 COTA DIÁRIA DO PILOTO AUTOMÁTICO ESGOTADA! Você usou todos os créditos para hoje.")
                    else:
                        st.error(f"Erro no Processador Quântico IA: {e}")
                        st.stop()
                        
    else:
        # LOOP DESBLOQUEADO MANTENDO SUAS MENSAGENS VISUAIS
        st.markdown("---")
        segundos_restantes = int(st.session_state.next_auto_run - tempo_agora)
        progresso = max(0.0, min(1.0, (60 - segundos_restantes) / 60.0))
        
        status_text = st.empty()
        progress_bar = st.progress(0.0)
        
        status_text.info(f"⏳ Aguardando fechamento da vela. Próxima leitura em: **{segundos_restantes} segundos**")
        progress_bar.progress(progresso)
        
        time.sleep(1)
        st.rerun()

else:
    # --- MODO 2: O MODO ORIGINAL (USUÁRIO MANDA O PRINT) ---
    with st.popover("🖼️ Anexar Print do Gráfico (Análise Manual)"):
        uploaded_files = st.file_uploader("Fotos", type=["png", "jpg", "jpeg"], accept_multiple_files=True, label_visibility="collapsed")

    col_texto, col_btn = st.columns([8, 2], vertical_alignment="bottom")
    with col_texto:
        prompt = st.text_input("", placeholder="Clique em Analisar ou cole regras institucionais...", label_visibility="collapsed")
    with col_btn:
        enviar = st.button("ANALISAR")

    if enviar and uploaded_files:
        comando_usuario = prompt if prompt else "Cruze dados Visuais, Sazonalidade, Notícias Institucionais e Multi-Timeframe. Diga o melhor horário de entrada."
        start_time = time.time()
        
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br)
        dias_da_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        dia_hoje_str = dias_da_semana[agora.weekday()]
        
        # OTIMIZAÇÃO APLICADA AQUI: Reduzindo o peso do print para não estourar a cota do Gemini!
        imagens_pil = []
        for f in uploaded_files:
            img = Image.open(f)
            img.thumbnail((1024, 1024)) # Compressor Quântico: diminui a resolução da imagem enviada
            imagens_pil.append(img)

        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(f"**Comando:** {comando_usuario}")
            st.image(imagens_pil[0], width=200)

        with st.chat_message("assistant", avatar="💠"):
            with st.spinner("NEXUS executando protocolo de Confluência Total..."):
                try:
                    st.toast("Escaneando Indicadores Visuais...", icon="👁️")
                    instrucao_olhos = """
                    Você é o Analista Visual de Elite do Nexus.
                    REGRA 1: Identifique ATIVO_IDENTIFICADO: [Nome do Ativo].
                    REGRA 2: Extraia Liquidity Sweeps, Regra dos Terços, Suportes e RSI.
                    """
                    vision_model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=instrucao_olhos)
                    dados_visuais = vision_model.generate_content(["Faça a varredura visual completa do ativo.", *imagens_pil]).text

                    match = re.search(r'ATIVO_IDENTIFICADO:\s*(.+)', dados_visuais, re.IGNORECASE)
                    ativo_identificado_na_tela = match.group(1).strip() if match else "Desconhecido"
                    ticker_alvo = traduzir_nome_visual_para_ticker(ativo_identificado_na_tela)
                    
                    st.toast("Carregando Kill Switch...", icon="🧠")
                    performance_nexus = buscar_performance_nexus(ticker_alvo)
                    
                    if performance_nexus["loss_sequence"] >= 5:
                        st.error(f"🚨 PROTOCOLO DE DEFESA ATIVADO: 5 perdas seguidas em {ativo_identificado_na_tela}. Bloqueio de 24h.")
                        st.stop()

                    data_hoje = agora.strftime('%Y-%m-%d')
                    doc = db.collection("historico_macro").document(f"{ticker_alvo}_{data_hoje}").get()

                    if doc.exists:
                        d = doc.to_dict()
                        dados_macro_str = f"Ativo: {ativo_identificado_na_tela} | Tendência Diária (D1): {d.get('tendencia_diaria')} | Sazonalidade: {d.get('sazonalidade_mes')}%. | ATR 200: {d.get('atr_200')} | Bias Institucional: {d.get('bias_whales')}."
                        noticias_hoje = d.get('ultimas_noticias', 'Sem manchetes no radar.')
                    else:
                        dados_macro_str = "Sem dados quantitativos hoje."
                        noticias_hoje = "Sentimento atual cego."

                    # =========================================================
                    # ATUALIZAÇÃO 2: PROMPT DO MODO MANUAL BEM MASTIGADO
                    # =========================================================
                    instrucao_nexus_manual = """
                    Você é o Algoritmo Nexus.
                    Sua missão é dar o sinal de forma EXTREMAMENTE FÁCIL, MASTIGADA E DIRETA, como se estivesse guiando um iniciante absoluto passo a passo. 
                    Nada de jargões confusos. Diga exatamente onde clicar e quando fechar baseando-se na imagem.
                    
                    FORMATO OBRIGATÓRIO (Siga exatamente este formato):
                    
                    ### [🟢 APERTE COMPRAR (Verde) / 🔴 APERTE VENDER (Vermelho) / 🟡 FIQUE DE FORA]
                    **🪙 Moeda/Ativo:** [Nome da Moeda lida na imagem]
                    **⏱️ Tempo Gráfico:** Coloque no M5 (Velas de 5 minutos)
                    **🎯 O Que Fazer Agora:** [Ex: Vá na sua corretora AGORA e clique no botão de COMPRAR / VENDER]
                    **🛑 Quando Fechar a Operação:** [Ex: Feche a operação manualmente assim que estiver no lucro no Alvo X, ou saia IMEDIATAMENTE se o preço for contra e bater no Stop Loss Y para proteger seu dinheiro.]
                    
                    *Por que entrar?* [Explique em 1 frase muito simples e fácil de entender o porquê da operação baseada na imagem]
                    """
                    final_prompt = f"MICRO VISUAL: {dados_visuais}\nMACRO: {dados_macro_str}\nNEWS: {noticias_hoje}\nPERF: {performance_nexus['texto']}\nCMD: {comando_usuario}"

                    resposta_nexus = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": instrucao_nexus_manual}, {"role": "user", "content": final_prompt}],
                        temperature=0.1, max_tokens=350
                    ).choices[0].message.content

                    st.markdown(f"<div style='color: #00ff88; font-size: 0.8rem; margin-bottom: 15px;'><i>🔬 Processado em <b>{round(time.time() - start_time, 1)}s</b>.</i></div>", unsafe_allow_html=True)
                    st.markdown(resposta_nexus)
                    
                    st.session_state.messages.append({"role": "user", "content": f"Print enviado. {comando_usuario}"})
                    st.session_state.messages.append({"role": "assistant", "content": resposta_nexus})
                    
                    st.session_state.last_op_id = str(uuid.uuid4())
                    st.session_state.last_ativo = ticker_alvo

                except Exception as e:
                    erro_str = str(e)
                    # VERIFICAÇÃO INTELIGENTE DE COTA NO MODO MANUAL ORIGINAL MANTIDA
                    if "429" in erro_str or "Quota exceeded" in erro_str:
                        delay_match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)\s*\}', erro_str)
                        wait_seconds = int(delay_match.group(1)) if delay_match else None
                        
                        if wait_seconds and wait_seconds < 300: # Cota de Minuto (Resfriamento curto)
                            st.warning(f"⚠️ Limite de imagens por minuto atingido. Ativando protocolo de resfriamento ({wait_seconds}s)...")
                            cooldown_ph = st.empty()
                            cbar = st.progress(0.0)
                            for sec in range(wait_seconds, 0, -1):
                                cooldown_ph.info(f"⏳ Recarregando conexão com o servidor. Liberação em: **{sec} segundos**")
                                cbar.progress((wait_seconds - sec) / wait_seconds)
                                time.sleep(1)
                            cooldown_ph.success("✅ Cota recarregada! O sistema tentará processar a imagem novamente no próximo clique.")
                            cbar.empty()
                            st.rerun()
                        else: # Cota Diária
                            exibir_cronometro_cota_diaria("🚨 COTA DIÁRIA VISUAL (GEMINI) ESGOTADA! Você usou todos os créditos gratuitos para hoje.")
                    else:
                        st.error(f"🚨 ALERTA DO SISTEMA: {e}")
                        st.stop()
        
        st.rerun()

    elif enviar and not uploaded_files:
        st.warning("⚠️ Comandante, anexe um print da tela para análise.")

# ==============================================================================
# 9. MÓDULO DE FEEDBACK E EVOLUÇÃO (CICLO DE APRENDIZADO)
# ==============================================================================
if st.session_state.last_op_id:
    st.markdown("---")
    st.markdown("<h4 style='text-align: center; color: #e2e8f0;'>Resultado da operação?</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 DEU WIN!", key="btn_win"):
            salvar_resultado(st.session_state.last_op_id, st.session_state.last_ativo, "WIN")
            st.toast("✅ Excelente! Parâmetros da vitória arquivados.", icon="🟢")
            st.session_state.last_op_id = None
            time.sleep(2)
            st.rerun()
    with col2:
        if st.button("🔴 DEU LOSS", key="btn_loss"):
            salvar_resultado(st.session_state.last_op_id, st.session_state.last_ativo, "LOSS")
            st.toast("❌ Registro confirmado.", icon="🔴")
            st.session_state.last_op_id = None
            time.sleep(2)
            st.rerun()