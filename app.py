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

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E LUXUOSA DO SITE (Foco Mobile)
# ==============================================================================
st.set_page_config(page_title="NEXUS SUPREMO", page_icon="💠", layout="centered")

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
        text-align: center;
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: 8px;
        margin-top: -3rem;
        margin-bottom: 1rem;
        background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: pulse 2.5s infinite;
        text-shadow: 0px 0px 15px rgba(0, 242, 254, 0.2);
    }
    .nexus-logo span {
        font-size: 1.2rem;
        letter-spacing: 3px;
        color: #e2e8f0;
        -webkit-text-fill-color: #e2e8f0;
        vertical-align: middle;
        margin-left: 5px;
    }
    @keyframes pulse {
        0% { opacity: 0.8; text-shadow: 0px 0px 15px rgba(0, 242, 254, 0.2); }
        50% { opacity: 1; text-shadow: 0px 0px 25px rgba(0, 242, 254, 0.6); }
        100% { opacity: 0.8; text-shadow: 0px 0px 15px rgba(0, 242, 254, 0.2); }
    }
    [data-testid="stChatMessage"] {
        background-color: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(0, 242, 254, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.2rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    .stButton > button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        border-radius: 8px !important; 
        height: 100%;
        width: 100%;
        font-weight: 700;
        transition: all 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONFIGURAÇÃO DAS APIS E BANCO DE DADOS (Nuem via Secrets)
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
    st.error(f"🚨 Falha na ignição: Configure as variáveis no Secrets do Streamlit. Detalhe: {e}")
    st.stop()

# ==============================================================================
# 3. A SOLUÇÃO NINJA: AUTO-ATUALIZAÇÃO DE DADOS
# ==============================================================================
@st.cache_data(ttl=43200) # Roda apenas 1 vez a cada 12 horas para economizar recursos
def atualizar_memoria_nexus_background():
    """Baixa silenciosamente os dados atualizados das principais paridades."""
    try:
        moedas_macro = ["BTC-USD", "ETH-USD", "EURUSD=X", "GC=F", "^AXJO"] 
        for ticker in moedas_macro:
            ativo = yf.Ticker(ticker)
            historico = ativo.history(period="1mo") 
            
            for data_index, linha in historico.iterrows():
                data_str = data_index.strftime('%Y-%m-%d')
                id_unico = f"{ticker}_{data_str}"
                tendencia = "ALTA" if linha["Close"] > linha["Open"] else "BAIXA"
                
                dados_macro = {
                    "ativo": ticker,
                    "data": data_str,
                    "tendencia_diaria": tendencia,
                    "abertura": float(linha["Open"]),
                    "fechamento": float(linha["Close"]),
                    "maxima": float(linha["High"]),
                    "minima": float(linha["Low"])
                }
                db.collection("historico_macro").document(id_unico).set(dados_macro)
        return True
    except Exception as e:
        return False

# Dispara a atualização silenciosa assim que o app abre
atualizar_memoria_nexus_background()

# ==============================================================================
# 4. PERSONAS E REGRAS DE OURO (Com auto-identificação)
# ==============================================================================
instrucao_olhos = """
Você é o Analista Visual de Elite do Nexus.
Sua tarefa é analisar a imagem de trading (corretora) de forma OBCECADA por detalhes.

REGRA ABSOLUTA NÚMERO 1:
Identifique qual é o ativo principal sendo operado. Olhe as abas superiores, veja qual está iluminada/selecionada.
Sua resposta DEVE começar OBRIGATORIAMENTE com esta linha exata:
ATIVO_IDENTIFICADO: [Nome do Ativo] (Exemplos: EUR/USD, Ouro, AUS 200, BTC).

REGRA NÚMERO 2:
Após identificar o ativo, descreva ABSOLUTAMENTE TUDO:
- Tempo gráfico selecionado (ex: 5m, 1m).
- Valor do preço atual.
- Tendência micro (o que está acontecendo nas últimas velas).
- Padrões de vela visíveis (Martelo, Engolfo, Doji).
- Zonas de Suporte e Resistência visíveis.
- Valores máximos e mínimos marcados na tela.
Entregue o máximo de informações técnicas possível.
"""

instrucao_nexus = """
Você é o Nexus, o Comandante de Execução de operações. 
Sua análise é implacável. Você cruza a leitura VISUAL detalhada da imagem com o HISTÓRICO MACRO (D1) do banco de dados.

REGRAS DE OURO:
1. Se a Imagem aponta Compra, mas o Macro aponta Baixa forte, o risco é ALTO. Considere ordenar AGUARDAR.
2. Analise tudo e seja direto.

FORMATO OBRIGATÓRIO DE RESPOSTA (NUNCA MUDE ISSO):
Primeiro, faça uma análise técnica rápida e direta justificando o movimento com base no que você viu e no banco de dados.
Depois, finalize OBRIGATORIAMENTE com o bloco abaixo:

---
## 🎯 VEREDITO FINAL

### [EMOJI] ORDEM: **[AÇÃO]**
**⏰ GATILHO DE ENTRADA:** Aguarde o cronômetro da vela atual chegar a 00:00. Entre no exato milissegundo em que a próxima vela nascer.
**🎯 TAXA ALVO:** [Valor do Preço em que a análise foi baseada]
**⚠️ RISCO:** [BAIXO / MÉDIO / ALTO]

INSTRUÇÕES DE CORES E AÇÃO:
- Se for COMPRA: Use o emoji 🟢 e escreva COMPRA em negrito.
- Se for VENDA: Use o emoji 🔴 e escreva VENDA em negrito.
- Se for AGUARDAR: Use o emoji 🟡 e escreva AGUARDAR em negrito.
---
"""

def traduzir_nome_visual_para_ticker(nome_visual):
    nome = nome_visual.upper()
    if "EUR" in nome and "USD" in nome: return "EURUSD=X"
    if "OURO" in nome or "GOLD" in nome: return "GC=F"
    if "AUS 200" in nome or "AUS" in nome: return "^AXJO"
    if "BTC" in nome or "BITCOIN" in nome: return "BTC-USD"
    if "ETH" in nome or "ETHEREUM" in nome: return "ETH-USD"
    return "BTC-USD"

# ==============================================================================
# 5. TÍTULO E INTERFACE DO CHAT (MOBILE FRIENDLY)
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS <span>SUPREMO</span></div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"] != "system":
        icone_avatar = "🧑‍💻" if message["role"] == "user" else "💠"
        with st.chat_message(message["role"], avatar=icone_avatar):
            st.markdown(message["content"])

# ==============================================================================
# 6. BARRA DE INPUT
# ==============================================================================
with st.popover("🖼️ Anexar Print"):
    uploaded_files = st.file_uploader("Fotos", type=["png", "jpg", "jpeg"], accept_multiple_files=True, label_visibility="collapsed")

if uploaded_files:
    st.markdown("<div style='font-size: 0.85rem; color: #00f2fe; margin-bottom: 5px;'>✔️ Print Carregado pelo Comandante.</div>", unsafe_allow_html=True)

col_texto, col_btn = st.columns([8, 2], vertical_alignment="bottom")

with col_texto:
    prompt = st.text_input("", placeholder="Clique em Analisar ou digite algo...", label_visibility="collapsed")

with col_btn:
    enviar = st.button("ANALISAR")

# ==============================================================================
# 7. O CÉREBRO: PROCESSAMENTO E FUSÃO (VISÃO + BANCO)
# ==============================================================================
if enviar and uploaded_files:
    comando_usuario = prompt if prompt else "Analise a imagem anexada e decida a melhor operação."
    
    start_time = time.time()
    fuso_br = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_br)
    
    imagens_pil = [Image.open(f) for f in uploaded_files]

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f"**Comando:** {comando_usuario}")
        st.image(imagens_pil[0], width=200)

    with st.chat_message("assistant", avatar="💠"):
        with st.spinner("NEXUS lendo a imagem e cruzando dados..."):
            try:
                # ---------------------------------------------------------
                # PASSO 1: A VISÃO OLHA A IMAGEM
                # ---------------------------------------------------------
                st.toast("Escaneando Print da Tela...", icon="👁️")
                vision_model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=instrucao_olhos)
                vision_response = vision_model.generate_content(["Extraia tudo desta imagem.", *imagens_pil])
                dados_visuais = vision_response.text

                # ---------------------------------------------------------
                # PASSO 2: IDENTIFICAÇÃO AUTOMÁTICA DA MOEDA
                # ---------------------------------------------------------
                ativo_identificado_na_tela = "Desconhecido"
                match = re.search(r'ATIVO_IDENTIFICADO:\s*(.+)', dados_visuais, re.IGNORECASE)
                if match:
                    ativo_identificado_na_tela = match.group(1).strip()
                
                ticker_alvo = traduzir_nome_visual_para_ticker(ativo_identificado_na_tela)

                # ---------------------------------------------------------
                # PASSO 3: BUSCA O CONTEXTO MACRO NO BANCO
                # ---------------------------------------------------------
                st.toast(f"Buscando histórico macro de {ativo_identificado_na_tela}...", icon="🗄️")
                data_hoje = agora.strftime('%Y-%m-%d')
                doc_ref = db.collection("historico_macro").document(f"{ticker_alvo}_{data_hoje}")
                doc = doc_ref.get()
                
                if doc.exists:
                    d = doc.to_dict()
                    dados_macro_str = f"Ativo: {ativo_identificado_na_tela} | Tendência Macro (D1): {d.get('tendencia_diaria')}. Máxima do dia: {d.get('maxima'):.2f}, Mínima: {d.get('minima'):.2f}."
                else:
                    dados_macro_str = f"Sem dados Macro hoje para {ativo_identificado_na_tela}. Opere apenas com base na imagem."

                # ---------------------------------------------------------
                # PASSO 4: O SUPER PROMPT DE DECISÃO FINAL (GROQ)
                # ---------------------------------------------------------
                final_prompt = f"""
[SISTEMA: Análise em tempo real].

1. DADOS MICRO (EXTRAÍDOS DA IMAGEM DO COMANDANTE):
O Ativo identificado na tela foi: {ativo_identificado_na_tela}.
Aqui estão os detalhes técnicos puros da foto:
{dados_visuais}

2. DADOS MACRO (EXTRAÍDOS DO SEU BANCO DE DADOS):
{dados_macro_str}

COMANDO DO COMANDANTE: {comando_usuario}
Cruze os dados Macro e Micro agora e dê o veredito.
"""
                
                historico_para_groq = [{"role": "system", "content": instrucao_nexus}]
                historico_para_groq.append({"role": "user", "content": final_prompt})

                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=historico_para_groq,
                    temperature=0.1, 
                    max_tokens=1024
                )

                resposta_nexus = completion.choices[0].message.content
                tempo_pensamento = round(time.time() - start_time, 1)

                st.markdown(f"<div style='color: #00f2fe; font-size: 0.8rem; margin-bottom: 15px;'><i>🧠 Ativo detectado: {ativo_identificado_na_tela} | Processado em <b>{tempo_pensamento}s</b>.</i></div>", unsafe_allow_html=True)
                st.markdown(resposta_nexus)
                
                # Salva Histórico
                st.session_state.messages.append({"role": "user", "content": f"Print enviado. {comando_usuario}"})
                st.session_state.messages.append({"role": "assistant", "content": resposta_nexus})

            except Exception as e:
                st.error(f"🚨 ALERTA: {e}")
                st.stop()
    st.rerun()

elif enviar and not uploaded_files:
    st.warning("⚠️ Comandante, anexe um print da tela para o Nexus analisar.")