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
**Crie, valide e salve seus links UTM com persistência no Google Sheets.**  
Mais automação, mais controle e 100% estilo Macfor.
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

def copiar_link_script():
    return """
    <script>
    function copiarLink(id) {
        const text = document.getElementById(id).innerText;
        navigator.clipboard.writeText(text);
        const btn = document.getElementById(id + "_btn");
        btn.innerText = "✅ Copiado!";
        setTimeout(() => { btn.innerText = "📋 Copiar"; }, 2000);
    }
    </script>
    """

# =========================
# FORMULÁRIO PRINCIPAL
# =========================
st.subheader("🔧 Parâmetros UTM")

col1, col2 = st.columns(2)
with col1:
    base_url = st.text_input("URL base*", placeholder="https://www.exemplo.com/")
    source = st.text_input("utm_source*", placeholder="google, newsletter...")
    medium = st.text_input("utm_medium*", placeholder="cpc, email...")
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
    elif "macfor" not in campaign.lower():
        st.warning("⚠️ A campanha deve conter 'macfor' no nome. Ajuste e tente novamente.")
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

        # Adiciona ao Google Sheets
        try:
            sheet.append_row([base_url, source, medium, campaign, term, content, utm_link])
            st.success("✅ Link salvo com sucesso no Google Sheets!")
        except Exception as e:
            st.error(f"⚠️ Erro ao salvar no Google Sheets: {e}")

        # Exibe o link com botão copiar
        st.markdown(copiar_link_script(), unsafe_allow_html=True)
        st.markdown(f"""
        <div style='display:flex; align-items:center; gap:10px;'>
            <code id="utm_link">{utm_link}</code>
            <button id="utm_link_btn" onclick="copiarLink('utm_link')" style="border:none; background-color:#4CAF50; color:white; padding:5px 10px; border-radius:6px; cursor:pointer;">📋 Copiar</button>
        </div>
        """, unsafe_allow_html=True)

# =========================
# VISUALIZAÇÃO DO HISTÓRICO
# =========================
st.divider()
st.subheader("🕓 Histórico de links gerados")

if st.button("🔄 Recarregar histórico"):
    st.experimental_rerun()

try:
    data = sheet.get_all_records()
    if data:
        df = pd.DataFrame(data).tail(100)  # mostra os últimos 100
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
    st.warning(f"⚠️ Não foi possível carregar o histórico da planilha. {e}")

# =========================
# RODAPÉ
# =========================
st.divider()
st.markdown(
    "<small style='color:gray;'>Feito com 🍍 por Guilherme — Macfor UTM Builder PRO v5</small>",
    unsafe_allow_html=True
)
