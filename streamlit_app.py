import streamlit as st
import pandas as pd
from urllib.parse import urlencode
import re
import gspread
from google.oauth2.service_account import Credentials

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Macfor UTM Builder 🍍",
    page_icon="🍍",
    layout="centered",
)

# =========================
# CONFIGURAR GOOGLE SHEETS
# =========================
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
SHEET_NAME = st.secrets["sheet_name"]
sheet = client.open(SHEET_NAME).worksheet("historico")

# =========================
# FUNÇÕES AUXILIARES
# =========================
def validar_url(url):
    pattern = re.compile(
        r'^(https?:\/\/)'
        r'([a-zA-Z0-9.-]+)'
        r'(\.[a-zA-Z]{2,})'
        r'(\/.*)?$'
    )
    return bool(pattern.match(url))

def limpar_texto(texto):
    texto = texto.strip().lower()
    texto = re.sub(r'[^a-z0-9_-]', '', texto)
    return texto

def carregar_historico():
    dados = sheet.get_all_records()
    return pd.DataFrame(dados)

def salvar_no_google_sheets(nova_linha):
    sheet.append_row(list(nova_linha.values()))

# =========================
# CABEÇALHO
# =========================
st.markdown("""
# 🍍 Macfor UTM Builder  
Crie, valide e salve seus links UTM com persistência no Google Sheets.
""")
st.divider()

# =========================
# CARREGAR HISTÓRICO
# =========================
if "history" not in st.session_state:
    st.session_state.history = carregar_historico()

# =========================
# FORMULÁRIO
# =========================
st.subheader("🔧 Parâmetros UTM")

col1, col2 = st.columns(2)
with col1:
    base_url = st.text_input("URL base*", placeholder="https://www.exemplo.com/")
    source = st.text_input("utm_source*", placeholder="google, newsletter...")
    medium = st.text_input("utm_medium*", placeholder="cpc, email...")
with col2:
    campaign = st.text_input("utm_campaign*", placeholder="promo_outubro, black_friday...")
    term = st.text_input("utm_term", placeholder="palavra-chave opcional")
    content = st.text_input("utm_content", placeholder="variação de anúncio opcional")

# =========================
# GERAR LINK
# =========================
if st.button("🚀 Gerar Link UTM"):
    if not base_url or not source or not medium or not campaign:
        st.error("⚠️ Preencha todos os campos obrigatórios (*).")
    elif not validar_url(base_url):
        st.error("❌ URL inválida. Ela deve começar com http:// ou https:// e ter um domínio válido.")
    else:
        if not base_url.endswith("/"):
            base_url += "/"

        source = limpar_texto(source)
        medium = limpar_texto(medium)
        campaign = limpar_texto(campaign)
        term = limpar_texto(term)
        content = limpar_texto(content)

        params = {
            "utm_source": source,
            "utm_medium": medium,
            "utm_campaign": campaign,
        }
        if term:
            params["utm_term"] = term
        if content:
            params["utm_content"] = content

        utm_link = f"{base_url}?{urlencode(params)}"

        novo_registro = {
            "Base URL": base_url,
            "UTM Source": source,
            "UTM Medium": medium,
            "UTM Campaign": campaign,
            "UTM Term": term,
            "UTM Content": content,
            "Link Gerado": utm_link
        }

        # Salvar no Google Sheets
        salvar_no_google_sheets(novo_registro)

        # Atualizar histórico em memória
        st.session_state.history = pd.concat(
            [st.session_state.history, pd.DataFrame([novo_registro])],
            ignore_index=True
        )

        st.success("✅ Link UTM gerado e salvo com sucesso no Google Sheets!")
        st.code(utm_link, language="markdown")

# =========================
# HISTÓRICO
# =========================
if not st.session_state.history.empty:
    st.divider()
    st.subheader("🕓 Histórico de links gerados")
    st.dataframe(st.session_state.history, use_container_width=True)

    csv = st.session_state.history.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="💾 Exportar histórico como CSV",
        data=csv,
        file_name="historico_macfor_utm.csv",
        mime="text/csv"
    )

# =========================
# RODAPÉ
# =========================
st.divider()
st.markdown(
    "<small style='color:gray;'>Feito com 🍍 por Guilherme — Macfor UTM Builder com Google Sheets</small>",
    unsafe_allow_html=True
)
