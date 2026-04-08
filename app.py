import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image

# 1. CONFIGURAÇÃO VISUAL E LUXUOSA DO SITE
# ==============================================================================
st.set_page_config(page_title="NEXUS SUPREMO", page_icon="💠", layout="centered")

st.markdown("""
<style>
    /* Fundo Escuro, Frio e Elegante */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', 'Helvetica Neue', sans-serif;
    }
    
    /* Esconder elementos inúteis do Streamlit (cabeçalho e rodapé) */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Animação suave de entrada */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(15px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    /* Estilo do Título Minimalista e Luxuoso */
    .nexus-logo {
        text-align: center;
        font-size: 2.2rem;
        font-weight: 300;
        letter-spacing: 8px;
        color: #ffffff;
        margin-top: 1rem;
        margin-bottom: 3rem;
        animation: fadeIn 1s ease-out;
    }
    .nexus-logo span {
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Ocultar barra de ferramentas de imagens nativa para ficar mais limpo */
    [data-testid="StyledFullScreenButton"] {display: none;}
    
    /* Melhorar visual do botão de envio */
    .stButton > button {
        background: linear-gradient(90deg, #3a7bd5 0%, #00d2ff 100%);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
        height: 100%;
        width: 100%;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
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
Você é o Nexus Supremo, o Comandante de Execução de operações financeiras. 
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

# 4. TÍTULO NA TELA (SUBSTITUINDO O ANTIGO)
# ==============================================================================
st.markdown('<div class="nexus-logo">NEXUS <span>SUPREMO</span></div>', unsafe_allow_html=True)

# 5. GERENCIAMENTO DE ESTADO DO CHAT
# ==============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe o histórico de mensagens na tela
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Se tiver imagens guardadas na mensagem, exibe elas bonitinhas
            if "images" in message and message["images"]:
                cols = st.columns(len(message["images"]))
                for i, img in enumerate(message["images"]):
                    cols[i].image(img, use_container_width=True)

# 6. BARRA DE INPUT ESTILO GEMINI/CHATGPT (BOTÃO ANEXO + CAMPO DE TEXTO)
# ==============================================================================
st.write("") # Espaçador
col_anexo, col_texto, col_btn = st.columns([1, 8, 1.5], vertical_alignment="bottom")

with col_anexo:
    # Popover: O clipe de papel que abre a janelinha de envio de fotos
    with st.popover("📎"):
        st.markdown("**Anexos (M15 e M5)**")
        uploaded_files = st.file_uploader(
            "Selecione as imagens", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True, 
            label_visibility="collapsed"
        )

with col_texto:
    # Campo de texto limpo e direto
    prompt = st.text_input("", placeholder="Solicitar análise de operação...", label_visibility="collapsed")

with col_btn:
    # Botão de envio
    enviar = st.button("Analisar")


# 7. PROCESSAMENTO PRINCIPAL (O MOTOR DA MÁQUINA)
# ==============================================================================
if enviar and prompt:
    # Abre as imagens (se houver) para exibir no chat e mandar pro Gemini
    imagens_pil = []
    if uploaded_files:
        imagens_pil = [Image.open(f) for f in uploaded_files]

    # 1. Mostra a mensagem do usuário na tela
    with st.chat_message("user"):
        st.markdown(prompt)
        if imagens_pil:
            cols = st.columns(len(imagens_pil))
            for i, img in enumerate(imagens_pil):
                cols[i].image(img, use_container_width=True)

    # Salva no histórico a ação do usuário (texto puro e imagens separadas)
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "images": imagens_pil
    })

    # 2. Resposta da Inteligência Artificial
    with st.chat_message("assistant"):
        with st.spinner("Nexus calculando probabilidade de execução..."):
            try:
                final_prompt = prompt
                
                # Passo 1: Visão Computacional (Gemini)
                if uploaded_files:
                    st.toast("Olhos ativados: Lendo estrutura de mercado...", icon="👁️")
                    # Nota: Mantive a versão 'gemini-2.5-flash' como estava no seu código. 
                    # Se der erro, mude para 'gemini-1.5-flash'
                    vision_model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=instrucao_olhos)
                    vision_response = vision_model.generate_content(["Extraia os dados técnicos destes gráficos.", *imagens_pil])
                    dados_visuais = vision_response.text
                    final_prompt = f"DADOS VISUAIS (M15 e M5): {dados_visuais}\n\nPERGUNTA DO USUÁRIO: {prompt}"

                # Passo 2: Cérebro Llama (Groq)
                historico_para_groq = [{"role": "system", "content": instrucao_nexus}]
                
                # Pega as últimas mensagens do histórico, mas manda SÓ o texto para a Groq (sem as imagens PIL para não quebrar)
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
                
                # Passo 3: Sistema de Cores Visual no Streamlit
                if "🟢" in resposta_nexus or "COMPRA" in resposta_nexus.upper():
                    st.success("✅ OPERAÇÃO AUTORIZADA: PREPARE-SE PARA COMPRAR NA PRÓXIMA VELA")
                elif "🔴" in resposta_nexus or "VENDA" in resposta_nexus.upper():
                    st.error("🚨 OPERAÇÃO AUTORIZADA: PREPARE-SE PARA VENDER NA PRÓXIMA VELA")
                elif "🟡" in resposta_nexus or "AGUARDAR" in resposta_nexus.upper():
                    st.warning("⚠️ OPERAÇÃO ABORTADA: PERMANEÇA DE FORA")

                # Exibe o texto completo
                st.markdown(resposta_nexus)
                
                # Salva a resposta do assistente no histórico
                st.session_state.messages.append({"role": "assistant", "content": resposta_nexus})

            except Exception as e:
                st.error(f"Falha de sistema: {e}")
                
    # Recarrega a tela para limpar o campo de texto
    st.rerun()