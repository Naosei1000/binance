import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import time
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore
import yfinance as yf
import re
import uuid
import pandas as pd
import random

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
            
            # Novo: Cálculo ATR 200 para Momentum
            historico_5a['TR'] = historico_5a['High'] - historico_5a['Low']
            atr_200 = float(historico_5a['TR'].tail(200).mean())

            noticias = ativo.news
            titulos_noticias = [n['title'] for n in noticias[:3]] if noticias else ["Nenhuma notícia relevante."]
            sentimento_bruto = " / ".join(titulos_noticias)
            
            # Novo: Bias Institucional (Baleias)
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
# 5. PROMPTS DE ELITE (INJEÇÃO DE TODAS AS 11 ESTRATÉGIAS DOS VÍDEOS)
# ==============================================================================
instrucao_olhos = """
Você é o Analista Visual de Elite do Nexus. Sua tarefa é extrair o DNA institucional da imagem.

REGRA ABSOLUTA 1: Identifique o ativo operado. Comece sua resposta EXATAMENTE com:
ATIVO_IDENTIFICADO: [Nome do Ativo]

REGRA ABSOLUTA 2: Extraia TODOS estes dados quantitativos:
1. TEMPOS GRÁFICOS: Qual o tempo atual? (M5 até H4).
2. ZONAS DE SUPORTE E RESISTÊNCIA: Onde estão? CONTE OS TOQUES.
3. LIQUIDITY SWEEPS E WHALES: Há pavios longos anormais (manipulação institucional)? 
4. EVASÃO DE RUÍDO: O indicador está em linha PONTILHADA (Evasive Mode lateral)?
5. REGRA DOS TERÇOS: A vela fechou no terço superior/inferior?
6. INDICADORES ESPECÍFICOS: Valores de RSI, ADX e Bandas ATR.
7. DIVERGÊNCIA: Há divergência entre preço e RSI?
8. MOMENTUM: A vela atual é visivelmente maior que a média?
"""

instrucao_nexus = """
Você é o NEXUS QUANTUM VANGUARD, Inteligência de Guerra Institucional.
Você funde Price Action, Multi-Timeframe, Sazonalidade, Notícias, Rastros de Baleias e Feedback Próprio.

REGRAS DE OURO DA EXECUÇÃO:
1. ANÁLISE MULTI-TIMEFRAME: M5 e D1 devem concordar.
2. SAZONALIDADE E WHALES: Se a notícia indicar atividade institucional, dobre a confiança.
3. EVASÃO: Se o mercado estiver lateral (pontilhado), AGUARDE.
4. GESTÃO DINÂMICA: Sugira sempre uma zona de Trailing Stop e pontos de DCA (Ladder).

FORMATO OBRIGATÓRIO DE RESPOSTA:
1. 🧬 RAIO-X INSTITUCIONAL E SENTIMENTO:
   - Sazonalidade, Impacto de Baleias/Notícias e Memória de Performance.
2. 🔬 ANÁLISE TÉCNICA AVANÇADA:
   - Cruzamento M5/D1, Evasão de Ruído, Divergências, Regra dos Terços.
3. 🎲 CÁLCULO MONTE CARLO:
   - Baseado na sua performance e nos dados acima, qual a % de chance de acerto dessa entrada?
4. 🎯 NOTA DE CONFLUÊNCIA: [0 a 10]. (Só opere se for >= 7).

---
## 🎯 VEREDITO FINAL
### [EMOJI] ORDEM: **[COMPRA / VENDA / AGUARDAR]**
**⏰ GATILHO DE ENTRADA:** Aguarde a vela fechar e entre na abertura da próxima.
**🎯 ALVO TÉCNICO:** [Alvo baseado em 1:4 ou Resistência] 
**📉 ZONA DE DCA:** [Onde recomprar se o preço cair um pouco]
**📈 TRAILING STOP:** [Ponto para travar o lucro]
**⛔ STOP LOSS:** [Baseado no ATR ou pavios longos de liquidez]
**⚠️ RISCO:** [BAIXO / MÉDIO / ALTO]
---
"""

# ==============================================================================
# 6. INTERFACE DO CHAT E ESTADO DA SESSÃO
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS <span>QUANTUM</span></div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_op_id" not in st.session_state:
    st.session_state.last_op_id = None
if "last_ativo" not in st.session_state:
    st.session_state.last_ativo = None

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

# ==============================================================================
# 7. O NÚCLEO DE PROCESSAMENTO QUÂNTICO (A MÁQUINA DE VERDADE)
# ==============================================================================
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
                # PASSO 1: A VISÃO
                st.toast("Escaneando Indicadores, Divergências e Liquidez...", icon="👁️")
                vision_model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=instrucao_olhos)
                vision_response = vision_model.generate_content(["Faça a varredura visual completa do ativo.", *imagens_pil])
                dados_visuais = vision_response.text

                # PASSO 2: IDENTIFICAÇÃO DO ATIVO
                ativo_identificado_na_tela = "Desconhecido"
                match = re.search(r'ATIVO_IDENTIFICADO:\s*(.+)', dados_visuais, re.IGNORECASE)
                if match:
                    ativo_identificado_na_tela = match.group(1).strip()
                
                ticker_alvo = traduzir_nome_visual_para_ticker(ativo_identificado_na_tela)
                
                # PASSO 3: BUSCA DE PERFORMANCE E KILL SWITCH
                st.toast("Carregando Rede Neural de Aprendizado e Kill Switch...", icon="🧠")
                performance_nexus = buscar_performance_nexus(ticker_alvo)
                
                if performance_nexus["loss_sequence"] >= 5:
                    st.error(f"🚨 PROTOCOLO DE DEFESA ATIVADO: Você teve {performance_nexus['loss_sequence']} perdas seguidas em {ativo_identificado_na_tela}. O sistema recomenda bloqueio de análises por 24h para evitar overtrading.")
                    st.stop()

                # PASSO 4: BUSCA ESTATÍSTICA E MACRO
                st.toast("Acessando Algoritmos Sazonais e Sentiment de Baleias...", icon="📰")
                data_hoje = agora.strftime('%Y-%m-%d')
                doc_ref = db.collection("historico_macro").document(f"{ticker_alvo}_{data_hoje}")
                doc = doc_ref.get()
                
                alerta_calendario = ""
                if agora.weekday() == 4 and agora.day <= 7: 
                    alerta_calendario = "⚠️ ALERTA: Hoje é dia de PAYROLL (NFP). O mercado sofre manipulação pesada institucional (Liquidity Sweeps). Risco Extremo."

                if doc.exists:
                    d = doc.to_dict()
                    winrate_sazonal = d.get('sazonalidade_mes', 50)
                    tend_diaria = d.get('tendencia_diaria', 'Desconhecida')
                    atr_mom = d.get('atr_200', 'Desconhecido')
                    bias_w = d.get('bias_whales', 'NEUTRO')
                    dados_macro_str = f"Ativo: {ativo_identificado_na_tela} | Tendência Diária (D1): {tend_diaria} | Sazonalidade: Taxa compradora neste mês é de {winrate_sazonal}%. | ATR 200: {atr_mom} | Bias Institucional: {bias_w}."
                    noticias_hoje = d.get('ultimas_noticias', 'Sem manchetes no radar.')
                else:
                    dados_macro_str = f"Sem dados estatísticos quantitativos hoje para {ativo_identificado_na_tela}."
                    noticias_hoje = "Sentimento atual cego."

                # PASSO 5: O SUPER PROMPT DE ELITE
                final_prompt = f"""
[SISTEMA: Avaliação em Tempo Real. Hoje é {dia_hoje_str}].

1. DADOS MICRO, SMC E PRICE ACTION (LIDOS DA TELA):
{dados_visuais}

2. MATEMÁTICA SAZONAL, ATR E MACRO TENDÊNCIA (5 ANOS):
{dados_macro_str}
