import streamlit as st
import google.generativeai as genai
from groq import Groq
from PIL import Image

# 1. Configuração Visual do Site
st.set_page_config(page_title="NEXUS SUPREMO - Comandante", layout="wide")
st.title("🎯 NEXUS SUPREMO (Operacional M5)")
st.markdown("---")

# 2. Configuração das APIs (Segurança: Lendo das Secrets do Streamlit)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    
    genai.configure(api_key=GOOGLE_API_KEY)
    groq_client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    st.error("🚨 Chaves de API não encontradas! Configure a área de 'Secrets' no painel do Streamlit.")
    st.stop()

# 3. Personas e Regras de Ouro
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

# 4. Interface Lateral
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Entrada de Dados (Prints)")
    uploaded_files = st.file_uploader("Envie os prints (Ex: M15 e M5)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if uploaded_files:
        for idx, file in enumerate(uploaded_files):
            st.image(file, caption=f"Gráfico {idx+1}", use_container_width=True)

# 5. Exibição do Chat
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 6. Processamento Principal
if prompt := st.chat_input("Solicitar análise de operação..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Nexus calculando probabilidade de execução..."):
            try:
                final_prompt = prompt
                
                # Passo 1: Visão Computacional (Gemini)
                if uploaded_files:
                    st.toast("Olhos ativados: Lendo estrutura de mercado...", icon="👁️")
                    vision_model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=instrucao_olhos)
                    
                    imagens_pil = [Image.open(f) for f in uploaded_files]
                    vision_response = vision_model.generate_content(["Extraia os dados técnicos destes gráficos.", *imagens_pil])
                    dados_visuais = vision_response.text
                    
                    final_prompt = f"DADOS VISUAIS (M15 e M5): {dados_visuais}\n\nPERGUNTA DO USUÁRIO: {prompt}"

                # Passo 2: Cérebro Llama (Groq)
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
                
                # Passo 3: Sistema de Cores Visual no Streamlit
                if "🟢" in resposta_nexus or "COMPRA" in resposta_nexus.upper():
                    st.success("✅ OPERAÇÃO AUTORIZADA: PREPARE-SE PARA COMPRAR NA PRÓXIMA VELA")
                elif "🔴" in resposta_nexus or "VENDA" in resposta_nexus.upper():
                    st.error("🚨 OPERAÇÃO AUTORIZADA: PREPARE-SE PARA VENDER NA PRÓXIMA VELA")
                elif "🟡" in resposta_nexus or "AGUARDAR" in resposta_nexus.upper():
                    st.warning("⚠️ OPERAÇÃO ABORTADA: PERMANEÇA DE FORA")

                # Exibe o texto completo
                st.markdown(resposta_nexus)
                st.session_state.messages.append({"role": "assistant", "content": resposta_nexus})

            except Exception as e:
                st.error(f"Falha de sistema: {e}")