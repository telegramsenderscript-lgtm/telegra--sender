import streamlit as st
from core.auth import login_user, is_logged_in, get_current_user
from core.data import load_users
import json

st.set_page_config(page_title="Painel Premium", layout="centered")

if "user" not in st.session_state:
    st.session_state.user = None

st.title("Painel de Controle Premium")

# Se já está logado → mostra painel
if is_logged_in():
    user = get_current_user()
    st.success(f"Logado como: **{user['username']}**")

    st.page_link("pages/2_Painel_Usuario.py", label="Painel do Usuário", icon="✨")
    st.page_link("pages/1_Admin.py", label="Painel de Admin", icon="🛠️")
    st.page_link("pages/3_Estatisticas.py", label="Estatísticas", icon="📊")

    if st.button("Sair da Conta"):
        st.session_state.user = None
        st.rerun()
    st.stop()

# ---- LOGIN ----

st.header("Login")
username = st.text_input("Usuário")
password = st.text_input("Senha", type="password")

if st.button("Entrar"):
    if login_user(username, password):
        st.success("Login realizado!")
        st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")
