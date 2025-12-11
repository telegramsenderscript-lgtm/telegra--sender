import streamlit as st
from core.auth import login_screen, logout_button, check_session


st.set_page_config(
    page_title="Painel Premium",
    page_icon="🔥",
    layout="centered"
)

# Sidebar
with st.sidebar:
    if check_session():
        st.success(f"Logado como: {st.session_state.user['username']}")
        logout_button()
    else:
        st.info("Você não está logado.")

# Página inicial
st.title("Painel de Controle Premium")

if not check_session():
    login_screen()
else:
    st.write("Selecione uma página no menu à esquerda.")
