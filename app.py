# app.py
import streamlit as st
from core.auth import login_screen, is_logged_in, get_current_user

st.set_page_config(page_title="Telegram Sender", layout="centered")
# hide menu & footer
hide_menu = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)

if not is_logged_in():
    login_screen()
    st.stop()

user = get_current_user()
if user is None:
    st.error("Erro interno: usuário não encontrado.")
    st.stop()

role = user.get("role", "user")
# redirect via query param (Streamlit multipage will load appropriate page)
if role == "admin":
    st.success("Entrando no painel admin...")
    st.experimental_set_query_params(page="admin")
else:
    st.success("Entrando no painel usuário...")
    st.experimental_set_query_params(page="user")
st.stop()
