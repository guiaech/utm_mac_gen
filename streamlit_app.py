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
    initial_sidebar_state="collapsed"
)

st.markdown("""
# 🍍 Macfor UTM Builder PRO  
**Crie, valide e salve seus links UTM.**
""")
st.divider()

# =========================
# VALIDAÇÃO DE SECRETS
# =========================
required_sections = ["gcp_service_account", "sheets"]
missing = [s for s in required_sections if s not in st.secrets]
if missing:
    st.error(f"❌ Segredos ausentes: {', '.join(missing)}. Configure-os em Settings → Secrets.")
    st.stop()

SHEET_NAME = st.secrets["sheets"]["sheet_name"]

# =========================
# CONEXÃO COM GOOGLE SHEETS
# =========================
try:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).worksheet("historico")
except Exception as e:
    st.error(f"⚠️ Falha ao conectar ao Google Sheets: {e}")
    st.stop()

# =========================
# FUNÇÕES DE VALIDAÇÃO
# =========================
def validar_url(url):
    pattern = re.compile(r'^(https?:\/\/)([a-zA-Z0-9.-]+)(\.[a-zA-Z]{2,})(\/.*)?$')
    return bool(pattern.match(url))

def limpar_texto(texto):
    """
    Limpa o texto e substitui caracteres inválidos por '-'.
    Mantém apenas letras, números, hífens e underscores.
    """
    texto = texto.strip().lower()
    # Substitui espaços e caracteres especiais por '-'
    texto = re.sub(r'[^a-z0-9_-]+', '-', texto)
    # Remove múltiplos '-' seguidos
    texto = re.sub(r'-{2,}', '-', texto)
    # Remove hífen do início e fim (se houver)
    texto = texto.strip('-')
    return texto

# =========================
# LISTAS PADRONIZADAS
# =========================
plataformas = [
    "adsplay", "google", "linkedin", "meta", "tiktok",
    "twitter", "audio", "facebook", "instagram"
]

midias = [
    "cpa", "cpc", "cpi", "cpm", "cpr", "lc", "mva",
    "mvao", "mvo", "mxcon", "pimp", "roas", "uni",
    "cpe", "cpv", "social", "offline"
]

# =========================
# FORMULÁRIO PRINCIPAL
# =========================
st.subheader("🔧 Parâmetros UTM")

col1, col2 = st.columns(2)
with col1:
    base_url = st.text_input("URL base*", placeholder="https://www.exemplo.com/")
    source = st.selectbox("utm_source*", plataformas, index=None, placeholder="Selecione a plataforma")
    medium = st.selectbox("utm_medium*", midias, index=None, placeholder="Selecione a mídia")

with col2:
    campaign = st.text_input("utm_campaign*", placeholder="macfor_campanha_exemplo")
    term = st.text_input("utm_term", placeholder="palavra-chave opcional")
    content = st.text_input("utm_content", placeholder="variação de anúncio opcional")

# =========================
# BOTÃO DE GERAÇÃO
# =========================
if st.button("🚀 Gerar Link UTM"):
    if not base_url or not source or not medium or not campaign:
        st.error("⚠️ Preencha todos os campos obrigatórios (*).")
    elif not validar_url(base_url):
        st.error("❌ URL inválida. Deve começar com http:// ou https:// e conter um domínio válido.")
    else:
        if not base_url.endswith("/"):
            base_url += "/"

        source = limpar_texto(source)
        medium = limpar_texto(medium)
        campaign = limpar_texto(campaign)
        term = limpar_texto(term)
        content = limpar_texto(content)

        # Garante que 'macfor' esteja no nome da campanha
        if "macfor" not in campaign:
            campaign = f"macfor_{campaign}"

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

        # Adiciona ao Google Sheets
        try:
            sheet.append_row([base_url, source, medium, campaign, term, content, utm_link])
            st.success("✅ Link salvo com sucesso no Google Sheets!")
        except Exception as e:
            st.error(f"⚠️ Erro ao salvar no Google Sheets: {e}")

        # Exibe o link com instrução de cópia
        st.markdown("### 🔗 Seu link UTM — selecione e **copie** ←")
        st.code(utm_link, language="markdown")
        st.caption("Dica: clique no código acima e use ⌘/Ctrl + C para copiar.")

# =========================
# HISTÓRICO
# =========================
st.divider()
st.subheader("🕓 Histórico de links gerados")

if st.button("🔄 Recarregar histórico"):
    st.session_state["refresh"] = not st.session_state.get("refresh", False)
    st.rerun()

try:
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data).tail(100)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Exportar histórico como CSV",
            data=csv,
            file_name="historico_macfor_utm.csv",
            mime="text/csv"
        )
    else:
        st.info("Nenhum link gerado ainda.")
except Exception as e:
    st.warning(f"⚠️ Não foi possível carregar o histórico. {e}")

# =========================
# RODAPÉ
# =========================
st.divider()
st.markdown(
    "<small style='color:gray;'>Feito com 🍍 Macfor UTM Builder PRO v9</small>",
    unsafe_allow_html=True
)
