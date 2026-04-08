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
    [data-testid="stChatMessage"] {
        background-color: rgba(15, 23, 42, 0.7) !important;
        border: 1px solid rgba(0, 242, 254, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    [data-testid="stChatMessage"] h2 {
        background: transparent;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #ffffff;
        font-size: 1.3rem;
        margin-bottom: 5px;
    }
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

# 3. PERSONAS E REGRAS DE OURO (COM PASSO A PASSO DIDÁTICO)
# ==============================================================================
instrucao_nexus = """
Você é o Nexus, o Comandante de Execução de operações financeiras. 
Sua análise é implacável, técnica, fria e focada no tempo gráfico de M5 (5 minutos) de tempo fixo.

REGRAS DE OURO:
1. Você receberá os dados de tempo real. Se a análise estiver confusa, ordene AGUARDAR.
2. Não use jargões difíceis. O usuário precisa de um passo a passo extremamente simples.

FORMATO OBRIGATÓRIO DE RESPOSTA (NUNCA MUDE ISSO):
Primeiro, faça uma análise técnica rápida e justifique.
Depois, finalize OBRIGATORIAMENTE com o bloco abaixo:

---
## 🎯 VEREDITO FINAL

### [EMOJI] ORDEM: **[COMPRA ou VENDA ou AGUARDAR]**
**⏰ HORÁRIO DA ENTRADA:** O momento exato para agir é às **[HORÁRIO DA PRÓXIMA VELA]**.

### 🛠️ PASSO A PASSO DA EXECUÇÃO:
1. **Prepare o relógio:** Na sua corretora, altere o "Tempo de Expiração" para 5 minutos (M5).
2. **Ação:** Quando o relógio bater EXATAMENTE o horário de entrada, clique no botão de **[AÇÃO DA ORDEM]**.
3. **Saída:** Solte o mouse. Você NÃO precisa fechar a operação. A corretora encerrará automaticamente após os 5 minutos.
---
"""

instrucao_olhos = """
Sua tarefa é extrair os dados puros das imagens: Tendência macro, suportes, resistências, valor atual do preço e padrões de vela.
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

# 5. BARRA DE INPUT
# ==============================================================================
st.write("") 

with st.popover("🖼️"):
    uploaded_files = st.file_uploader(
        "Selecione as fotos", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True, 
        label_visibility="collapsed"
    )

if uploaded_files:
    st.markdown("<div style='font-size: 0.85rem; color: #00f2fe; margin-bottom: 5px; margin-left: 10px;'>✔️ Imagem pronta para análise:</div>", unsafe_allow_html=True)
    for file in uploaded_files:
        img_thumb = Image.open(file)
        st.image(img_thumb, width=60) 

col_anexo, col_texto, col_btn = st.columns([1, 7.5, 2.5], vertical_alignment="bottom")

with col_texto:
    prompt = st.text_input("", placeholder="Aguardando comando de análise...", label_visibility="collapsed")

with col_btn:
    enviar = st.button("ANALISAR")

# 6. PROCESSAMENTO, TRATAMENTO DE ERRO DE CRÉDITOS E CRONÔMETRO
# ==============================================================================
if enviar and prompt:
    start_time = time.time()
    
    fuso_br = timezone(timedelta(hours=-3))
    agora = datetime.now(fuso_br)
    hora_atual_str = agora.strftime("%H:%M:%S")
    
    minutos_restantes = 5 - (agora.minute % 5)
    if minutos_restantes == 5 and agora.second == 0: 
        minutos_restantes = 0
    proxima_vela = agora + timedelta(minutes=minutos_restantes)
    proxima_vela = proxima_vela.replace(second=0, microsecond=0)
    hora_proxima_vela_str = proxima_vela.strftime("%H:%M:00")

    imagens_pil = []
    if uploaded_files:
        imagens_pil = [Image.open(f) for f in uploaded_files]

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f"**Comando de Entrada:** {prompt}")

    with st.chat_message("assistant", avatar="💠"):
        with st.spinner("NEXUS escaneando o mercado..."):
            try:
                contexto_tempo = f"[SISTEMA: A solicitação foi recebida às {hora_atual_str}. A próxima vela de M5 nasce às {hora_proxima_vela_str}. Coloque este horário no passo a passo.]"
                
                final_prompt = f"{contexto_tempo}\n\n"
                
                if uploaded_files:
                    st.toast("Lendo estrutura dos gráficos...", icon="💠")
                    # USANDO O MODELO OFICIAL QUE FUNCIONA PARA NÃO TRAVAR
                    vision_model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=instrucao_olhos)
                    vision_response = vision_model.generate_content(["Extraia dados técnicos", *imagens_pil])
                    dados_visuais = vision_response.text
                    final_prompt += f"DADOS VISUAIS: {dados_visuais}\n\n"
                
                final_prompt += f"PERGUNTA: {prompt}"

                historico_para_groq = [{"role": "system", "content": instrucao_nexus}]
                
                for msg in st.session_state.messages[-4:]:
                    historico_para_groq.append({"role": msg["role"], "content": msg["content"]})
                
                historico_para_groq.append({"role": "user", "content": final_prompt})

                completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=historico_para_groq,
                    temperature=0.1, 
                    max_tokens=1024
                )

                resposta_nexus = completion.choices[0].message.content
                
                end_time = time.time()
                tempo_pensamento = round(end_time - start_time, 1)

                st.markdown(f"<div style='color: #00f2fe; font-size: 0.9rem; margin-bottom: 15px;'><i>🧠 Nexus processou os dados em <b>{tempo_pensamento} segundos</b>.</i></div>", unsafe_allow_html=True)
                st.markdown(resposta_nexus)
                
                st.session_state.messages.append({"role": "user", "content": prompt})
                resposta_salva = f"<i>🧠 Nexus pensou por {tempo_pensamento} segundos.</i>\n\n{resposta_nexus}"
                st.session_state.messages.append({"role": "assistant", "content": resposta_salva})

            except Exception as e:
                # SE ACABAR OS CRÉDITOS OU DER ERRO, A TELA AVISA!
                mensagem_erro = str(e).lower()
                if "quota" in mensagem_erro or "429" in mensagem_erro or "rate limit" in mensagem_erro:
                    st.error("🚨 ERRO DE SISTEMA: O limite de requisições ou créditos da API (Google ou Groq) foi esgotado. Verifique os painéis das APIs.")
                elif "not found" in mensagem_erro or "model" in mensagem_erro:
                    st.error("🚨 ERRO DE SISTEMA: Nome do modelo de Inteligência Artificial inválido. Mantenha as versões oficiais (ex: gemini-2.0-flash).")
                else:
                    st.error(f"🚨 ALERTA CRÍTICO DO NEXUS: Falha de comunicação. Detalhes: {e}")
                
                st.stop() # Interrompe tudo para você poder ler o erro

    st.rerun()