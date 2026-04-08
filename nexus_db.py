import firebase_admin
from firebase_admin import credentials, firestore
import yfinance as yf
import pandas as pd
import streamlit as st

# ==========================================
# 1. CONFIGURAÇÃO E CONEXÃO DO NEXUS
# ==========================================
def conectar_firebase():
    """Estabelece a conexão do Nexus com o Firebase Firestore."""
    try:
        if not firebase_admin._apps:
            # Tenta pegar das Secrets (Se estiver rodando no Streamlit)
            if "firebase" in st.secrets:
                cred_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(cred_dict)
            else:
                # Se estiver no PC, usa o arquivo normal
                cred = credentials.Certificate("credenciais.json")
                
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()
        print("✅ Nexus conectado ao Firebase Firestore!")
        return db
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco: {e}")
        return None

# ==========================================
# 2. FUNÇÃO DE ALIMENTAÇÃO DO BANCO
# ==========================================
def salvar_historico_mercado(db, nome_colecao, id_documento, dados_mercado):
    """Salva uma linha de dados no Firestore."""
    try:
        doc_ref = db.collection(nome_colecao).document(id_documento)
        doc_ref.set(dados_mercado)
    except Exception as e:
        print(f"❌ Falha ao salvar os dados do doc {id_documento}: {e}")

# ==========================================
# 3. CAPTURANDO DADOS REAIS
# ==========================================
if __name__ == "__main__":
    banco_nexus = conectar_firebase()

    if banco_nexus:
        lista_de_moedas = ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "DOGE-USD"]
        
        print(f"\nBuscando 5 ANOS de dados para {len(lista_de_moedas)} moedas...")
        
        for ticker_symbol in lista_de_moedas:
            print(f"⏳ Baixando histórico de: {ticker_symbol}...")
            
            ativo = yf.Ticker(ticker_symbol)
            historico = ativo.history(period="5y")

            if not historico.empty:
                dias_salvos = 0
                for data_index, linha in historico.iterrows():
                    data_str = data_index.strftime('%Y-%m-%d')
                    id_unico = f"{ticker_symbol}_{data_str}"
                    
                    dados_reais = {
                        "ativo": ticker_symbol,
                        "data": data_str,
                        "abertura": float(linha["Open"]),
                        "fechamento": float(linha["Close"]),
                        "maxima": float(linha["High"]),
                        "minima": float(linha["Low"]),
                        "volume": int(linha["Volume"])
                    }
                    
                    salvar_historico_mercado(banco_nexus, "historico_cripto", id_unico, dados_reais)
                    dias_salvos += 1
                
                print(f"✅ {ticker_symbol}: {dias_salvos} dias salvos!")
            else:
                print(f"❌ Sem dados para {ticker_symbol}.")
                
        print("\n🚀 Operação Multi-Moedas Concluída!")