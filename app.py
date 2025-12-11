# app.py
import streamlit as st
from core.auth import login_screen, is_logged_in, get_current_user
from core.data import load_users

st.set_page_config(page_title="Telegram Sender", layout="centered")

# Hide default Streamlit menu
hide_menu = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_menu, unsafe_allow_html=True)

# If not logged -> show login
if not is_logged_in():
    login_screen()
    st.stop()

# Logged -> get user and redirect to proper page
user = get_current_user()
if user is None:
    st.error("Erro interno: usuário não encontrado na sessão.")
    st.stop()

role = user.get("role","user")
if role == "admin":
    st.experimental_set_query_params(page="admin")
    st.write("Redirecionando para painel admin...")
    st.stop()
else:
    st.experimental_set_query_params(page="user")
    st.write("Redirecionando para painel usuário...")
    st.stop()
