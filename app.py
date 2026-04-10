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

# ==============================================================================
# 1. CONFIGURAÇÃO VISUAL E LUXUOSA DO SITE (Foco Mobile)
# ==============================================================================
st.set_page_config(page_title="NEXUS SUPREMO - FINAL", page_icon="💠", layout="centered")

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
        background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: pulse 2.5s infinite;
        text-shadow: 0px 0px 15px rgba(0, 242, 254, 0.2);
    }
    .nexus-logo span {
        font-size: 1.2rem; letter-spacing: 3px; color: #e2e8f0;
        -webkit-text-fill-color: #e2e8f0; vertical-align: middle; margin-left: 5px;
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
        padding: 1.2rem !important; margin-bottom: 1rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    .stButton > button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white; border: 1px solid rgba(0, 242, 254, 0.3) !important;
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
# 3. AUTO-ATUALIZAÇÃO DE DADOS MACRO E NOTÍCIAS
# ==============================================================================
@st.cache_data(ttl=43200) 
def atualizar_memoria_nexus_background():
    try:
        moedas_macro = ["BTC-USD", "ETH-USD", "EURUSD=X", "GC=F", "^AXJO"] 
        for ticker in moedas_macro:
            ativo = yf.Ticker(ticker)
            historico = ativo.history(period="1mo") 
            
            noticias = ativo.news
            titulos_noticias = [n['title'] for n in noticias[:3]] if noticias else ["Nenhuma notícia relevante."]
            sentimento_bruto = " / ".join(titulos_noticias)
            
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
                    "minima": float(linha["Low"]),
                    "ultimas_noticias": sentimento_bruto 
                }
                db.collection("historico_macro").document(id_unico).set(dados_macro)
        return True
    except Exception as e:
        return False

atualizar_memoria_nexus_background()

# ==============================================================================
# 4. FUNÇÕES DE APRENDIZADO DO NEXUS (MEMÓRIA DE RESULTADOS)
# ==============================================================================
def buscar_performance_nexus(ativo):
    """Busca o histórico de acertos do Nexus para este ativo."""
    try:
        docs = db.collection("resultados_nexus").where("ativo", "==", ativo).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).get()
        if not docs: 
            return "Sem histórico de operações recentes para este ativo."
        
        wins = sum(1 for d in docs if d.to_dict().get("resultado") == "WIN")
        total = len(docs)
        taxa = (wins / total) * 100
        return f"Nas últimas {total} operações de {ativo}, você teve {wins} WINs. (Taxa de acerto: {taxa:.0f}%)."
    except Exception as e:
        return "Erro ao carregar memória de performance."

def salvar_resultado(id_op, ativo, resultado):
    """Salva se a operação deu WIN ou LOSS."""
    db.collection("resultados_nexus").document(id_op).set({
        "ativo": ativo, 
        "resultado": resultado, 
        "timestamp": firestore.SERVER_TIMESTAMP
    })

# ==============================================================================
# 5. PERSONAS E REGRAS DE OURO
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
"""

instrucao_nexus = """
Você é o NEXUS SUPREMO, a IA de trading com consciência de aprendizado.
Sua análise cruza 4 pilares: MICRO (Imagem), MACRO (Banco), SENTIMENTO (Notícias) e sua PERFORMANCE (Seu histórico de acertos).

REGRAS DE OURO:
1. Se as NOTÍCIAS indicarem turbulência global, o risco é ALTO.
2. Se a sua PERFORMANCE recente neste ativo for muito ruim (Muitos LOSS), você deve ser extremamente cauteloso ou ordenar AGUARDAR.

FORMATO OBRIGATÓRIO DE RESPOSTA:
1. Comece com "🧠 CONSCIÊNCIA NEXUS:" e comente sobre seu histórico de acertos e o impacto das notícias do dia.
2. Faça sua análise técnica rápida cruzando Micro e Macro.
3. Finalize OBRIGATORIAMENTE com o bloco abaixo:

---
## 🎯 VEREDITO FINAL

### [EMOJI] ORDEM: **[AÇÃO]**
**⏰ GATILHO DE ENTRADA:** Aguarde o cronômetro chegar a 00:00 e entre na virada da vela.
**🎯 TAXA ALVO:** [Valor do Preço]
**⚠️ RISCO:** [BAIXO / MÉDIO / ALTO]

INSTRUÇÕES:
- COMPRA: 🟢 em negrito.
- VENDA: 🔴 em negrito.
- AGUARDAR: 🟡 em negrito.
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
# 6. INTERFACE DO CHAT E ESTADO DA SESSÃO
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS <span>SUPREMO</span></div>', unsafe_allow_html=True)

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

with st.popover("🖼️ Anexar Print"):
    uploaded_files = st.file_uploader("Fotos", type=["png", "jpg", "jpeg"], accept_multiple_files=True, label_visibility="collapsed")

if uploaded_files:
    st.markdown("<div style='font-size: 0.85rem; color: #00f2fe; margin-bottom: 5px;'>✔️ Print Carregado pelo Comandante.</div>", unsafe_allow_html=True)

col_texto, col_btn = st.columns([8, 2], vertical_alignment="bottom")
with col_texto:
    prompt = st.text_input("", placeholder="Clique em Analisar...", label_visibility="collapsed")
with col_btn:
    enviar = st.button("ANALISAR")

# ==============================================================================
# 7. O CÉREBRO: O PROCESSAMENTO COMPLETO
# ==============================================================================
if enviar and uploaded_files:
    comando_usuario = prompt if prompt else "Cruze os dados da imagem com as notícias e seu histórico de acertos."
    start_time = time.time()
    fuso_br = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_br)
    
    imagens_pil = [Image.open(f) for f in uploaded_files]

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f"**Comando:** {comando_usuario}")
        st.image(imagens_pil[0], width=200)

    with st.chat_message("assistant", avatar="💠"):
        with st.spinner("NEXUS lendo Imagem, Banco de Dados, Notícias e Memória..."):
            try:
                # PASSO 1: A VISÃO
                st.toast("Escaneando Print...", icon="👁️")
                vision_model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=instrucao_olhos)
                vision_response = vision_model.generate_content(["Extraia tudo.", *imagens_pil])
                dados_visuais = vision_response.text

                # PASSO 2: IDENTIFICAÇÃO DO ATIVO
                ativo_identificado_na_tela = "Desconhecido"
                match = re.search(r'ATIVO_IDENTIFICADO:\s*(.+)', dados_visuais, re.IGNORECASE)
                if match:
                    ativo_identificado_na_tela = match.group(1).strip()
                
                ticker_alvo = traduzir_nome_visual_para_ticker(ativo_identificado_na_tela)
                
                # PASSO 3: BUSCA DE MACRO, NOTÍCIAS E CALENDÁRIO
                st.toast("Acessando Banco e Sentimento...", icon="📰")
                data_hoje = agora.strftime('%Y-%m-%d')
                doc_ref = db.collection("historico_macro").document(f"{ticker_alvo}_{data_hoje}")
                doc = doc_ref.get()
                
                dia_semana = agora.weekday()
                alerta_calendario = ""
                if dia_semana == 4 and agora.day <= 7: 
                    alerta_calendario = "ALERTA DE CALENDÁRIO: Hoje é dia de PAYROLL (NFP). Volatilidade extrema."

                if doc.exists:
                    d = doc.to_dict()
                    dados_macro_str = f"Ativo: {ativo_identificado_na_tela} | Tendência Macro (D1): {d.get('tendencia_diaria')}."
                    noticias_hoje = d.get('ultimas_noticias', 'Sem notícias no radar.')
                else:
                    dados_macro_str = f"Sem dados Macro hoje para {ativo_identificado_na_tela}."
                    noticias_hoje = "Sem leitura de sentimento atual."

                # PASSO 4: BUSCA DE PERFORMANCE (MEMÓRIA DO NEXUS)
                st.toast("Consultando Histórico de Acertos...", icon="🧠")
                performance_nexus = buscar_performance_nexus(ticker_alvo)

                # PASSO 5: O SUPER PROMPT DE ELITE
                final_prompt = f"""
[SISTEMA: Análise em tempo real].

1. DADOS MICRO (EXTRAÍDOS DA IMAGEM DO COMANDANTE):
{dados_visuais}

2. DADOS MACRO (BANCO DE DADOS NEXUS):
{dados_macro_str}

3. SENTIMENTO DE MERCADO E NOTÍCIAS:
Manchetes atuais: "{noticias_hoje}"
{alerta_calendario}

4. MEMÓRIA DE PERFORMANCE DO NEXUS:
{performance_nexus}

COMANDO: {comando_usuario}
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

                st.markdown(f"<div style='color: #00f2fe; font-size: 0.8rem; margin-bottom: 15px;'><i>🧠 Análise Global processada em <b>{tempo_pensamento}s</b>.</i></div>", unsafe_allow_html=True)
                st.markdown(resposta_nexus)
                
                st.session_state.messages.append({"role": "user", "content": f"Print enviado. {comando_usuario}"})
                st.session_state.messages.append({"role": "assistant", "content": resposta_nexus})
                
                # REGISTRA A OPERAÇÃO PARA RECEBER O FEEDBACK DEPOIS
                st.session_state.last_op_id = str(uuid.uuid4())
                st.session_state.last_ativo = ticker_alvo

            except Exception as e:
                mensagem_erro = str(e).lower()
                if "429" in mensagem_erro or "quota" in mensagem_erro:
                     st.error("⏳ ALERTA DE VELOCIDADE: O Google Gemini (Visão) pediu para você esperar cerca de 1 minuto antes do próximo print. O plano gratuito protege contra muitas fotos seguidas. Beba uma água e aperte Analisar de novo!")
                else:
                     st.error(f"🚨 ALERTA: {e}")
                st.stop()
    st.rerun()

elif enviar and not uploaded_files:
    st.warning("⚠️ Comandante, anexe um print da tela para o Nexus analisar.")

# ==============================================================================
# 8. MÓDULO DE FEEDBACK (O NEXUS APRENDE AQUI)
# ==============================================================================
if st.session_state.last_op_id:
    st.markdown("---")
    st.markdown("<h4 style='text-align: center; color: #e2e8f0;'>Qual foi o resultado da operação?</h4>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 DEU WIN!", key="btn_win"):
            salvar_resultado(st.session_state.last_op_id, st.session_state.last_ativo, "WIN")
            st.toast("✅ Boa, Comandante! O Nexus salvou esse cenário como vitorioso.", icon="🟢")
            st.session_state.last_op_id = None
            time.sleep(2)
            st.rerun()
    with col2:
        if st.button("🔴 DEU LOSS", key="btn_loss"):
            salvar_resultado(st.session_state.last_op_id, st.session_state.last_ativo, "LOSS")
            st.toast("❌ Entendido. O Nexus será mais cauteloso nesse ativo na próxima vez.", icon="🔴")
            st.session_state.last_op_id = None
            time.sleep(2)
            st.rerun()