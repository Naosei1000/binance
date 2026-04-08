import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image

# 1. CONFIGURAÇÃO VISUAL E LUXUOSA DO SITE
# ==============================================================================
st.set_page_config(page_title="NEXUS", page_icon="💠", layout="centered")

# INJEÇÃO DE CSS (DESIGN DE ELITE, LEVE PARA CELULAR E DESTAQUE NO VEREDITO)
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

    /* Esconder elementos inúteis do Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="StyledFullScreenButton"] {display: none;}
    
    /* Logo Animada do NEXUS */
    .nexus-logo {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: 15px;
        margin-top: 0rem;
        margin-bottom: 2rem;
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
        background-color: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(0, 242, 254, 0.1) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    /* 🎯 DESTAQUE MÁXIMO PARA O VEREDITO FINAL 🎯 */
    [data-testid="stChatMessage"] h2 {
        background: linear-gradient(90deg, rgba(0, 242, 254, 0.05) 0%, rgba(0, 242, 254, 0.2) 50%, rgba(0, 242, 254, 0.05) 100%);
        border-top: 1px solid #00f2fe;
        border-bottom: 1px solid #00f2fe;
        padding: 12px;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #ffffff;
        border-radius: 8px;
        margin-top: 25px;
        margin-bottom: 25px;
        font-size: 1.4rem;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.1);
    }

    /* Linhas divisórias (---) mais discretas */
    hr {
        border-color: rgba(0, 242, 254, 0.2) !important;
    }

    /* Botão de Envio */
    .stButton > button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border: 1px solid rgba(0, 242, 254, 0.3);
        border-radius: 8px;
        transition: all 0.3s ease;
        height: 100%;
        width: 100%;
        font-weight: 600;
        letter-spacing: 1px;
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
    st.error("🚨 Chaves de API não encontradas! Configure a área de 'Secrets' no painel do Streamlit.")
    st.stop()

# 3. PERSONAS E REGRAS DE OURO
# ==============================================================================
instrucao_nexus = """
Você é o Nexus, o Comandante de Execução de operações financeiras. 
Sua análise é implacável, técnica, fria e focada no tempo gráfico de M5 (5 minutos).

REGRAS DE OURO:
1. Você sempre buscará a confluência entre o gráfico maior (M15) e o gráfico de entrada (M5).
2. Se a análise estiver confusa ou o risco for alto demais, ordene AGUARDAR.
3. Não use jargões desnecessários, vá direto ao ponto.

FORMATO OBRIGATÓRIO DE RESPOSTA (NUNCA MUDE ISSO):
Primeiro, faça uma análise técnica rápida e direta (máximo 2 parágrafos) justificando o movimento.
Depois, finalize OBRIGATORIAMENTE com o bloco abaixo, exatamente neste formato:

---
## 🎯 VEREDITO FINAL

### [EMOJI] ORDEM: **[AÇÃO]**
**⏰ GATILHO DE ENTRADA:** Aguarde o cronômetro da vela atual na corretora chegar a 00:00. Entre no exato milissegundo em que a PRÓXIMA vela nascer.
**📉 TAXA ALVO DO PREÇO:** [Valor do Preço em que a análise foi baseada]
**⚠️ RISCO:** [BAIXO / MÉDIO / ALTO]

---
INSTRUÇÕES DE CORES E AÇÃO:
- Se for COMPRA: Use o emoji 🟢 e escreva COMPRA em negrito.
- Se for VENDA: Use o emoji 🔴 e escreva VENDA em negrito.
- Se for AGUARDAR: Use o emoji 🟡 e escreva AGUARDAR em negrito.
"""

instrucao_olhos = """
Você é um analista visual de múltiplos tempos gráficos. 
Sua tarefa é extrair os dados puros das imagens: Tendência macro, suportes, resistências, valor atual do preço e padrões de vela (engolfo, martelo, doji).
Seja extremamente detalhista com os números que aparecem no gráfico.
"""

# 4. TÍTULO NA TELA 
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS</div>', unsafe_allow_html=True)

# 5. GERENCIAMENTO DE ESTADO DO CHAT (Com Avatares Customizados)
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico de mensagens
for message in st.session_state.messages:
    if message["role"] != "system":
        # Avatares elegantes: Usuário (🧑‍💻) e Nexus (💠)
        icone_avatar = "🧑‍💻" if message["role"] == "user" else "💠"
        
        with st.chat_message(message["role"], avatar=icone_avatar):
            st.markdown(message["content"])
            if "images" in message and message["images"]:
                cols = st.columns(len(message["images"]))
                for i, img in enumerate(message["images"]):
                    cols[i].image(img, use_container_width=True)

# 6. BARRA DE INPUT E ANEXO OTIMIZADA
# ==============================================================================
st.write("") 
col_anexo, col_texto, col_btn = st.columns([1, 8, 1.5], vertical_alignment="bottom")

with col_anexo:
    with st.popover("📎"):
        st.markdown("**Imagens da Operação**")
        uploaded_files = st.file_uploader(
            "Selecione", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True, 
            label_visibility="collapsed"
        )

with col_texto:
    prompt = st.text_input("", placeholder="Solicitar análise tática ao Nexus...", label_visibility="collapsed")

with col_btn:
    enviar = st.button("ANALISAR")


# 7. PROCESSAMENTO PRINCIPAL (MOTOR INTACTO)
# ==============================================================================
if enviar and prompt:
    imagens_pil = []
    if uploaded_files:
        imagens_pil = [Image.open(f) for f in uploaded_files]

    # Painel do Usuário
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(f"**Parâmetros de Entrada:** {prompt}")
        if imagens_pil:
            cols = st.columns(len(imagens_pil))
            for i, img in enumerate(imagens_pil):
                cols[i].image(img, use_container_width=True)

    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "images": imagens_pil
    })

    # Painel do Nexus
    with st.chat_message("assistant", avatar="💠"):
        with st.spinner("NEXUS executando cálculos de probabilidade..."):
            try:
                final_prompt = prompt
                
                if uploaded_files:
                    st.toast("Óptica Ativada: Escaneando estrutura gráfica...", icon="💠")
                    vision_model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=instrucao_olhos)
                    vision_response = vision_model.generate_content(["Extraia os dados técnicos destes gráficos.", *imagens_pil])
                    dados_visuais = vision_response.text
                    final_prompt = f"DADOS VISUAIS (M15 e M5): {dados_visuais}\n\nPERGUNTA DO USUÁRIO: {prompt}"

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
                
                # Exibe o relatório de forma organizada com o CSS aplicado
                st.markdown(resposta_nexus)
                
                # Sistema de Alertas Visuais extra no Streamlit
                if "🟢" in resposta_nexus or "COMPRA" in resposta_nexus.upper():
                    st.success("✅ SINAL CONFIRMADO: PREPARE-SE PARA EXECUÇÃO DE COMPRA")
                elif "🔴" in resposta_nexus or "VENDA" in resposta_nexus.upper():
                    st.error("🚨 SINAL CONFIRMADO: PREPARE-SE PARA EXECUÇÃO DE VENDA")
                elif "🟡" in resposta_nexus or "AGUARDAR" in resposta_nexus.upper():
                    st.warning("⚠️ EXECUÇÃO ABORTADA: PERMANEÇA POSICIONADO E AGUARDE")

                st.session_state.messages.append({"role": "assistant", "content": resposta_nexus})

            except Exception as e:
                st.error(f"Falha de processamento tático: {e}")
                
    st.rerun()