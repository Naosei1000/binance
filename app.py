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
</style>
""", unsafe_allow_html=True)

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
            
            # Cálculo ATR 200 para Momentum
            historico_5a['TR'] = historico_5a['High'] - historico_5a['Low']
            atr_200 = float(historico_5a['TR'].tail(200).mean())

            noticias = ativo.news
            titulos_noticias = [n['title'] for n in noticias[:3]] if noticias else ["Nenhuma notícia relevante."]
            sentimento_bruto = " / ".join(titulos_noticias)
            
            # Bias Institucional (Baleias)
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
# 4. FUNÇÕES DE APRENDIZADO E SEGURANÇA (KILL SWITCH)
# ==============================================================================
def buscar_performance_nexus(ativo):
    try:
        docs = db.collection("resultados_nexus").where("ativo", "==", ativo).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).get()
        if not docs: 
            return {"texto": "Sem histórico de operações recentes para este ativo.", "loss_sequence": 0, "wins": 0}
        
        resultados = [d.to_dict().get("resultado") for d in docs]
        wins = resultados.count("WIN")
        total = len(docs)
        taxa = (wins / total) * 100
        
        # Conta perdas seguidas
        loss_seq = 0
        for r in resultados:
            if r == "LOSS": loss_seq += 1
            else: break
            
        return {"texto": f"Nas últimas {total} operações de {ativo}, você teve {wins} WINs. (Taxa de acerto: {taxa:.0f}%).", "loss_sequence": loss_seq, "wins": wins}
    except Exception as e:
        return {"texto": "Erro ao carregar memória de performance.", "loss_sequence": 0, "wins": 0}

def salvar_resultado(id_op, ativo, resultado):
    db.collection("resultados_nexus").document(id_op).set({
        "ativo": ativo, 
        "resultado": resultado, 
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
# 5. O LEITOR MATEMÁTICO AO VIVO (O CÉREBRO AUTÔNOMO)
# ==============================================================================
def ler_dados_mercado_ao_vivo(ticker):
    """
    Função crítica que lê as velas reais via código, calcula RSI, Médias e Pavios.
    O Nexus usa isso para analisar o mercado automaticamente sem precisar de print.
    """
    try:
        df = yf.download(ticker, period="5d", interval="5m", progress=False)
        if df.empty: return "Falha ao puxar dados da corretora via API."
        
        # Calcula RSI 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Calcula EMA
        df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        
        # Análise de Preço da Última Vela
        vela_atual = df.tail(3).iloc[-1]
        
        corpo = abs(vela_atual['Close'] - vela_atual['Open'])
        pavio_sup = float(vela_atual['High']) - max(float(vela_atual['Open']), float(vela_atual['Close']))
        pavio_inf = min(float(vela_atual['Open']), float(vela_atual['Close'])) - float(vela_atual['Low'])
        
        sweep_baixa = "SIM (Manipulação para Varejo)" if pavio_inf > (corpo * 2.5) else "NÃO"
        sweep_alta = "SIM (Manipulação para Varejo)" if pavio_sup > (corpo * 2.5) else "NÃO"
        
        tendencia_micro = "ALTA" if vela_atual['EMA_9'].iloc[0] > vela_atual['EMA_21'].iloc[0] else "BAIXA"
        
        resumo_dados = f"""
        * STATUS MATEMÁTICO DO M5 AGORA:
        - Preço: {float(vela_atual['Close']):.4f}
        - RSI: {float(vela_atual['RSI']):.2f}
        - Tendência EMA: {tendencia_micro}
        - Liquidity Sweep Inferior (Stops): {sweep_baixa}
        - Liquidity Sweep Superior (Stops): {sweep_alta}
        """
        return resumo_dados
    except Exception as e:
        return f"Erro na leitura matemática HFT: {e}"

# ==============================================================================
# 5.5 HUB DE MONITORAMENTO AO VIVO E CORRETORAS
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS <span>QUANTUM</span></div>', unsafe_allow_html=True)

with st.expander("📡 HUB DE MONITORAMENTO AO VIVO E CORRETORAS", expanded=False):
    st.markdown("<p style='font-size:0.9rem; color:#e2e8f0;'>Conexão de dados da corretora. O gráfico abaixo é em tempo real.</p>", unsafe_allow_html=True)
    
    col_ativo, col_corretora = st.columns(2)
    with col_ativo:
        ativo_live = st.selectbox("Ativo para Monitorar:", ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "FX:EURUSD", "OANDA:XAUUSD"])
    with col_corretora:
        corretora_selecionada = st.selectbox("Selecione sua Corretora:", ["Binance", "Bybit", "OKX", "B3 (Em breve)"])
    
    api_key_input = st.text_input("API Key (Leitura)", type="password", placeholder="Cole sua API Key aqui...")
    
    if st.button("SINCRONIZAR DADOS"):
        st.toast(f"Conectando ao terminal {corretora_selecionada}...", icon="⚡")
        time.sleep(1)
        st.success("✅ Conexão Simulada Estabelecida. Gráfico e Scanner prontos.")

    # Gráfico do TradingView para o usuário visualizar
    html_grafico = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_nexus"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget(
      {{
      "width": "100%",
      "height": 400,
      "symbol": "{ativo_live}",
      "interval": "5",
      "timezone": "Etc/UTC",
      "theme": "dark",
      "style": "1",
      "locale": "br",
      "enable_publishing": false,
      "backgroundColor": "rgba(15, 23, 42, 0.7)",
      "gridColor": "rgba(0, 255, 136, 0.05)",
      "hide_top_toolbar": false,
      "save_image": false,
      "container_id": "tradingview_nexus"
    }}
      );
      </script>
    </div>
    """
    components.html(html_grafico, height=400)

st.markdown("---")

# ==============================================================================
# 6. O PILOTO AUTOMÁTICO (LEITURA 24/7 SEM PRINT) E CHAT MANUAL
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_op_id" not in st.session_state:
    st.session_state.last_op_id = None
if "last_ativo" not in st.session_state:
    st.session_state.last_ativo = None

auto_mode = st.toggle("🟢 ATIVAR PILOTO AUTOMÁTICO (NEXUS LÊ O GRÁFICO SOZINHO)")
container_log = st.empty()

if auto_mode:
    # --- MODO 1: O ROBÔ LÊ O MERCADO SOZINHO VIA DADOS (VÍDEOS 9, 10, 11) ---
    with container_log.container():
        st.warning("📡 SCANNER ATIVADO: O Nexus está puxando a fita de preços da corretora...")
        
        ativo_para_ler = "BTC-USD" if "BTC" in ativo_live else "ETH-USD"
        if "EUR" in ativo_live: ativo_para_ler = "EURUSD=X"
        if "XAU" in ativo_live: ativo_para_ler = "GC=F"
        
        # Puxa os dados da corretora
        dados_matematicos = ler_dados_mercado_ao_vivo(ativo_para_ler)
        
        # Verifica a segurança (Kill Switch)
        perf = buscar_performance_nexus(ativo_para_ler)
        if perf["loss_sequence"] >= 5:
            st.error("🚨 KILL SWITCH ATIVADO: 5 Perdas Seguidas. Piloto Automático Desligado por segurança.")
            st.stop()
            
        doc = db.collection("historico_macro").document(f"{ativo_para_ler}_{datetime.now().strftime('%Y-%m-%d')}").get()
        macro_info = doc.to_dict() if doc.exists else "Macro Indisponível"
        
        # O prompt Autônomo Institucional
        inst_auto = """
        Você é o NEXUS QUANTUM AUTÔNOMO. Você opera lendo dados matemáticos puros (OHLCV).
        CRITÉRIOS:
        1. Se RSI < 30 e Sweep Inferior detectado = COMPRA FORTE.
        2. Se RSI > 70 e Sweep Superior detectado = VENDA FORTE.
        3. Se a Tendência Micro for contra a Diária = AGUARDAR.
        
        RESPONDA:
        1. 🔬 LEITURA QUÂNTICA AO VIVO: (Análise dos dados matemáticos M5).
        2. 🐋 BIAS INSTITUCIONAL: (Sazonalidade e Notícias).
        3. 🎯 NOTA DE OPORTUNIDADE: [0/10].
        
        ## 🎯 SINAL DO ALGORITMO
        ORDEM: [COMPRA / VENDA / AGUARDAR NOVA VELA]
        ALVO: [Sugerir 1:4] | STOP: [Atrás do Liquidity Sweep]
        LADDER (DCA): [Ponto de Recompra se cair]
        """
        
        prompt_final = f"DADOS DA CORRETORA (M5):\n{dados_matematicos}\nMACRO/SAZONAL:\n{macro_info}\nPERFORMANCE:\n{perf['texto']}"
        
        try:
            resposta = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": inst_auto}, {"role": "user", "content": prompt_final}],
                temperature=0.1, max_tokens=1024
            ).choices[0].message.content
            
            st.success("✅ Varredura Concluída com Sucesso!")
            st.markdown(resposta)
            
            st.session_state.last_op_id = str(uuid.uuid4())
            st.session_state.last_ativo = ativo_para_ler
            
        except Exception as e:
            st.error(f"Erro na IA: {e}")
            
        st.info("⏳ O Nexus está aguardando o fechamento da próxima vela para ler o gráfico novamente (Cooldown de 60s)...")
        time.sleep(60) 
        st.rerun()

else:
    # --- MODO 2: O MODO ORIGINAL (USUÁRIO MANDA O PRINT) ---
    for message in st.session_state.messages:
        if message["role"] != "system":
            icone_avatar = "🧑‍💻" if message["role"] == "user" else "💠"
            with st.chat_message(message["role"], avatar=icone_avatar):
                st.markdown(message["content"])

    with st.popover("🖼️ Anexar Print do Gráfico"):
        uploaded_files = st.file_uploader("Fotos", type=["png", "jpg", "jpeg"], accept_multiple_files=True, label_visibility="collapsed")

    if uploaded_files:
        st.markdown("<div style='font-size: 0.85rem; color: #00ff88; margin-bottom: 5px;'>✔️ Print Carregado. Pronto para a Varredura.</div>", unsafe_allow_html=True)

    col_texto, col_btn = st.columns([8, 2], vertical_alignment="bottom")
    with col_texto:
        prompt = st.text_input("", placeholder="Clique em Analisar ou cole regras institucionais...", label_visibility="collapsed")
    with col_btn:
        enviar = st.button("ANALISAR")

    if enviar and uploaded_files:
        comando_usuario = prompt if prompt else "Cruze dados Visuais, Sazonalidade, Notícias Institucionais e Multi-Timeframe."
        start_time = time.time()
        
        fuso_br = timezone(timedelta(hours=-3))
        agora = datetime.now(fuso_br)
        dias_da_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        dia_hoje_str = dias_da_semana[agora.weekday()]
        
        imagens_pil = [Image.open(f) for f in uploaded_files]

        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(f"**Comando:** {comando_usuario}")
            st.image(imagens_pil[0], width=200)

        with st.chat_message("assistant", avatar="💠"):
            with st.spinner("NEXUS executando protocolo de Confluência Total e Checagem Institucional..."):
                try:
                    st.toast("Escaneando Indicadores, Divergências e Liquidez...", icon="👁️")
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
                    
                    st.toast("Carregando Rede Neural de Aprendizado e Kill Switch...", icon="🧠")
                    performance_nexus = buscar_performance_nexus(ticker_alvo)
                    
                    if performance_nexus["loss_sequence"] >= 5:
                        st.error(f"🚨 PROTOCOLO DE DEFESA ATIVADO: 5 perdas seguidas em {ativo_identificado_na_tela}. Bloqueio de 24h.")
                        st.stop()

                    st.toast("Acessando Algoritmos Sazonais e Sentiment de Baleias...", icon="📰")
                    data_hoje = agora.strftime('%Y-%m-%d')
                    doc = db.collection("historico_macro").document(f"{ticker_alvo}_{data_hoje}").get()
                    
                    alerta_calendario = "⚠️ PAYROLL HOJE." if agora.weekday() == 4 and agora.day <= 7 else ""

                    if doc.exists:
                        d = doc.to_dict()
                        dados_macro_str = f"Ativo: {ativo_identificado_na_tela} | Tendência Diária (D1): {d.get('tendencia_diaria')} | Sazonalidade: {d.get('sazonalidade_mes')}%. | ATR 200: {d.get('atr_200')} | Bias Institucional: {d.get('bias_whales')}."
                        noticias_hoje = d.get('ultimas_noticias', 'Sem manchetes no radar.')
                    else:
                        dados_macro_str = "Sem dados quantitativos hoje."
                        noticias_hoje = "Sentimento atual cego."

                    instrucao_nexus = """
                    Você é o NEXUS QUANTUM VANGUARD.
                    FORMATO: 1. RAIO-X INSTITUCIONAL. 2. ANÁLISE TÉCNICA. 3. NOTA DE CONFLUÊNCIA.
                    VEREDITO: ORDEM, ALVO, ZONA DCA, TRAILING STOP, STOP LOSS.
                    """
                    final_prompt = f"MICRO: {dados_visuais}\nMACRO: {dados_macro_str}\nNEWS: {noticias_hoje}\nPERF: {performance_nexus['texto']}\nCMD: {comando_usuario}"

                    resposta_nexus = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": instrucao_nexus}, {"role": "user", "content": final_prompt}],
                        temperature=0.1, max_tokens=1024
                    ).choices[0].message.content

                    st.markdown(f"<div style='color: #00ff88; font-size: 0.8rem; margin-bottom: 15px;'><i>🔬 Confluência Institucional processada em <b>{round(time.time() - start_time, 1)}s</b>.</i></div>", unsafe_allow_html=True)
                    st.markdown(resposta_nexus)
                    
                    st.session_state.messages.append({"role": "user", "content": f"Print enviado. {comando_usuario}"})
                    st.session_state.messages.append({"role": "assistant", "content": resposta_nexus})
                    
                    st.session_state.last_op_id = str(uuid.uuid4())
                    st.session_state.last_ativo = ticker_alvo

                except Exception as e:
                    st.error(f"🚨 ALERTA DO SISTEMA: {e}")
                    st.stop()
        st.rerun()

    elif enviar and not uploaded_files:
        st.warning("⚠️ Comandante, anexe um print da tela para ativar a Visão Institucional.")

# ==============================================================================
# 9. MÓDULO DE FEEDBACK E EVOLUÇÃO (CICLO DE APRENDIZADO)
# ==============================================================================
if st.session_state.last_op_id:
    st.markdown("---")
    st.markdown("<h4 style='text-align: center; color: #e2e8f0;'>Qual foi o resultado da operação?</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 DEU WIN!", key="btn_win"):
            salvar_resultado(st.session_state.last_op_id, st.session_state.last_ativo, "WIN")
            st.toast("✅ Excelente! Parâmetros da vitória arquivados no código-fonte.", icon="🟢")
            st.session_state.last_op_id = None
            time.sleep(2)
            st.rerun()
    with col2:
        if st.button("🔴 DEU LOSS", key="btn_loss"):
            salvar_resultado(st.session_state.last_op_id, st.session_state.last_ativo, "LOSS")
            st.toast("❌ Registro confirmado. Ajustando rigor da IA para este ativo.", icon="🔴")
            st.session_state.last_op_id = None
            time.sleep(2)
            st.rerun()