import streamlit as st
from core.auth import is_logged_in, login_screen, get_current_user


st.set_page_config(
    page_title="Telegram Sender",
    page_icon="🚀",
    initial_sidebar_state="collapsed"
)

# Oculta o menu lateral global da multipage
hide_menu = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)


# -----------------------------------
# VERIFICA LOGIN
# -----------------------------------
if not is_logged_in():
    login_screen()
    st.stop()

# -----------------------------------
# APÓS LOGIN → REDIRECIONAMENTO
# -----------------------------------
user = get_current_user()

if user is None:
    st.error("Erro interno: usuário não carregado.")
    st.stop()

role = user.get("role", "user")

# Se for admin → manda para /Admin
if role == "admin":
    st.switch_page("pages/1_Admin.py")

# Se for cliente → manda para painel
else:
    st.switch_page("pages/2_Painel_Usuario.py")
