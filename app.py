import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image
import time
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO VISUAL E LUXUOSA DO SITE
# ==============================================================================
st.set_page_config(page_title="NEXUS", page_icon="💠", layout="centered")

st.markdown("""
<style>
    /* Fundo Animado Leve (Otimizado para Celular) */
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
    
    /* Logo Animada do NEXUS */
    .nexus-logo {
        text-align: center;
        font-size: 3.2rem;
        font-weight: 800;
        letter-spacing: 12px;
        margin-top: -2rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: pulse 2.5s infinite;
        text-shadow: 0px 0px 15px rgba(0, 242, 254, 0.2);
    }

    @keyframes pulse {
        0% { opacity: 0.8; text-shadow: 0px 0px 15px rgba(0, 242, 254, 0.2); }
        50% { opacity: 1; text-shadow: 0px 0px 25px rgba(0, 242, 254, 0.6); }
        100% { opacity: 0.8; text-shadow: 0px 0px 15px rgba(0, 242, 254, 0.2); }
    }

    /* Estilo das Mensagens (Fundo translúcido elegante) */
    [data-testid="stChatMessage"] {
        background-color: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(0, 242, 254, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }

    /* 🎯 DESTAQUE MÁXIMO PARA O VEREDITO FINAL 🎯 */
    [data-testid="stChatMessage"] h2 {
        background: transparent;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #ffffff;
        font-size: 1.3rem;
        margin-bottom: 5px;
    }

    /* 🚨 CAIXA DE DESTAQUE NEON PARA A "ORDEM" 🚨 */
    [data-testid="stChatMessage"] h3 {
        background: rgba(0, 242, 254, 0.1);
        border-left: 5px solid #00f2fe;
        border-right: 5px solid #00f2fe;
        padding: 15px;
        text-align: center;
        border-radius: 8px;
        font-size: 1.5rem !important;
        color: #ffffff;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.15);
    }

    /* ========================================================= */
    /* BARRA DE INPUT ESTILO PROFISSIONAL E ALINHADA           */
    /* ========================================================= */
    
    div[data-testid="stPopover"] > button {
        background-color: transparent !important;
        border: none !important;
        font-size: 1.5rem !important;
        padding: 0 !important;
        color: #a0aec0 !important;
        transition: color 0.3s ease;
    }
    div[data-testid="stPopover"] > button:hover {
        color: #00f2fe !important;
    }

    div[data-testid="stTextInput"] div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.9) !important;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        border-radius: 12px !important;
        padding-left: 10px;
    }
    div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
        border-color: #00f2fe !important;
    }

    /* Botão ANALISAR (Perfeito e sem quebrar palavra) */
    .stButton > button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: 1px solid rgba(0, 242, 254, 0.3) !important;
        border-radius: 8px !important; 
        height: 100%;
        width: 100%;
        font-weight: 700;
        letter-spacing: 1px;
        font-size: 0.9rem !important;
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    .stButton > button:hover {
        border-color: #00f2fe !important;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.4) !important;
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# 2. CONFIGURAÇÃO DAS APIS (SECRETS)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    
    genai.configure(api_key=GOOGLE_API_KEY)
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("🚨 Chaves de API não encontradas! Configure a área de 'Secrets'.")
    st.stop()

# 3. PERSONAS E REGRAS DE OURO (COM FOCO NO HORÁRIO M5)
# ==============================================================================
instrucao_nexus = """
Você é o Nexus, o Comandante de Execução de operações financeiras. 
Sua análise é implacável, técnica, fria e focada no tempo gráfico de M5 (5 minutos).

REGRAS DE OURO:
1. Você receberá os dados de tempo real. Se o tempo da próxima vela estiver muito perto e a operação for arriscada por falta de tempo de análise, ordene AGUARDAR.
2. Você sempre buscará a confluência entre o gráfico maior (M15) e o gráfico de entrada (M5).
3. Não use jargões desnecessários, vá direto ao ponto.

FORMATO OBRIGATÓRIO DE RESPOSTA (NUNCA MUDE ISSO):
Primeiro, faça uma análise técnica rápida e direta.
Depois, finalize OBRIGATORIAMENTE com o bloco abaixo, exatamente neste formato:

---
## 🎯 VEREDITO FINAL

### [EMOJI] ORDEM: **[AÇÃO]**
**⏰ GATILHO DE ENTRADA:** O tempo ideal para entrar nesta operação é EXATAMENTE às **[HORÁRIO DA PRÓXIMA VELA]** (quando o cronômetro da corretora virar 00:00).
**📉 TAXA ALVO DO PREÇO:** [Valor do Preço]
**⚠️ RISCO:** [BAIXO / MÉDIO / ALTO]

---
INSTRUÇÕES DE CORES E AÇÃO:
- Se for COMPRA: Use 🟢 e escreva COMPRA em negrito.
- Se for VENDA: Use 🔴 e escreva VENDA em negrito.
- Se for AGUARDAR: Use 🟡 e escreva AGUARDAR em negrito.
"""

instrucao_olhos = """
Sua tarefa é extrair os dados puros das imagens: Tendência macro, suportes, resistências, valor atual do preço e padrões de vela. Seja detalhista com os números.
"""

# 4. TÍTULO E ESTADO DO CHAT
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"] != "system":
        icone_avatar = "🧑‍💻" if message["role"] == "user" else "💠"
        with st.chat_message(message["role"], avatar=icone_avatar):
            st.markdown(message["content"])

# 5. BARRA DE INPUT ESTILO PROFISSIONAL
# ==============================================================================
st.write("") 

# ---> MINIATURA DISCRETA DAS FOTOS (SÓ PRA TER CERTEZA) <---
with st.popover("🖼️"):
    uploaded_files = st.file_uploader(
        "Selecione as fotos", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True, 
        label_visibility="collapsed"
    )

if uploaded_files:
    # Mostra só os ícones minúsculos das imagens antes de enviar
    st.markdown("<div style='font-size: 0.8rem; color: #00f2fe; margin-bottom: 2px; margin-left: 55px;'>✔️ Imagem pronta no gatilho:</div>", unsafe_allow_html=True)
    cols_thumb = st.columns([0.1]*len(uploaded_files) + [1])
    for i, file in enumerate(uploaded_files):
        img_thumb = Image.open(file)
        # Força um tamanho bem pequenininho só pra constar na tela
        cols_thumb[i].image(img_thumb, width=40)

# Proporção ajustada da barra para caber o botão "ANALISAR" perfeitamente
col_anexo, col_texto, col_btn = st.columns([1, 7.5, 2.5], vertical_alignment="bottom")

with col_texto:
    prompt = st.text_input("", placeholder="Aguardando comando de análise...", label_visibility="collapsed")

with col_btn:
    enviar = st.button("ANALISAR")


# 6. PROCESSAMENTO COM TEMPO DE RESPOSTA E LÓGICA DE HORÁRIO
# ==============================================================================
if enviar and prompt:
    # MARCA O TEMPO ZERO DO CRONÔMETRO
    start_time = time.time()
    
    # PEGA O HORÁRIO EXATO DE BRASÍLIA
    fuso_br = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_br)
    hora_atual_str = agora.strftime("%H:%M:%S")
    
    # CALCULA A HORA DA PRÓXIMA VELA M5
    minutos_restantes = 5 - (agora.minute % 5)
    if minutos_restantes == 5 and agora.second == 0: 
        minutos_restantes = 0 # Caso o cara mande exatamente cravado
    proxima_vela = agora + timedelta(minutes=minutos_restantes)
    proxima_vela = proxima_vela.replace(second=0, microsecond=0)
    hora_proxima_vela_str = proxima_vela.strftime("%H:%M:00")

    imagens_pil = []
    if uploaded_files:
        imagens_pil = [Image.open(f) for f in uploaded_files]

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f"**Comando de Entrada:** {prompt}")

    st.session_state.messages.append({
        "role": "user", 
        "content": prompt
    })

    with st.chat_message("assistant", avatar="💠"):
        with st.spinner("NEXUS escaneando o mercado e calculando timing..."):
            try:
                # INJETA O TEMPO NO CÉREBRO DO NEXUS
                contexto_tempo = f"[SISTEMA: A solicitação foi recebida às {hora_atual_str}. A próxima vela de M5 nasce às {hora_proxima_vela_str}. Confirme a viabilidade de entrada neste horário.]"
                
                final_prompt = f"{contexto_tempo}\n\n"
                
                if uploaded_files:
                    st.toast("Lendo estrutura dos gráficos...", icon="💠")
                    vision_model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=instrucao_olhos)
                    vision_response = vision_model.generate_content(["Extraia dados técnicos", *imagens_pil])
                    dados_visuais = vision_response.text
                    final_prompt += f"DADOS VISUAIS (M15 e M5): {dados_visuais}\n\n"
                
                final_prompt += f"PERGUNTA DO USUÁRIO: {prompt}"

                historico_para_groq = [{"role": "system", "content": instrucao_nexus}]
                for msg in st.session_state.messages[-5:-1]:
                    historico_para_groq.append({"role": msg["role"], "content": msg["content"]})
                
                historico_para_groq.append({"role": "user", "content": final_prompt})

                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=historico_para_groq,
                    temperature=0.1, 
                    max_tokens=1024
                )

                resposta_nexus = completion.choices[0].message.content
                
                # FINALIZA O CRONÔMETRO
                end_time = time.time()
                tempo_pensamento = round(end_time - start_time, 1)

                # RENDERIZA O TEMPO DE PENSAMENTO PRIMEIRO (Super Elegante)
                st.markdown(f"<div style='color: #00f2fe; font-size: 0.9rem; margin-bottom: 15px;'><i>🧠 Nexus processou os dados gráficos e lógicos em <b>{tempo_pensamento} segundos</b>.</i></div>", unsafe_allow_html=True)
                
                # RENDERIZA A RESPOSTA COMPLETA
                st.markdown(resposta_nexus)
                
                # Sistema de Alertas Rápidos
                if "🟢" in resposta_nexus or "COMPRA" in resposta_nexus.upper():
                    st.success(f"✅ SINAL DE COMPRA PARA ÀS {hora_proxima_vela_str}")
                elif "🔴" in resposta_nexus or "VENDA" in resposta_nexus.upper():
                    st.error(f"🚨 SINAL DE VENDA PARA ÀS {hora_proxima_vela_str}")
                elif "🟡" in resposta_nexus or "AGUARDAR" in resposta_nexus.upper():
                    st.warning("⚠️ EXECUÇÃO ABORTADA: AGUARDE")

                # Salva a resposta no histórico (incluindo a nota de pensamento)
                resposta_salva = f"<i>🧠 Nexus pensou por {tempo_pensamento} segundos.</i>\n\n{resposta_nexus}"
                st.session_state.messages.append({"role": "assistant", "content": resposta_salva})

            except Exception as e:
                st.error(f"Falha de processamento tático: {e}")
                
    st.rerun()