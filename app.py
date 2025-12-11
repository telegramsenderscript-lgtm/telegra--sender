import streamlit as st
import json
from navigation import setup_navigation

st.set_page_config(page_title="Telegram Sender — Premium Login", layout="centered")

# --- Carrega DB de usuários ---
def load_users():
    try:
        with open("assets/users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

users_db = load_users()

# --- Reset se clicou Sair ---
if "logout" in st.session_state:
    st.session_state.clear()

# --- Setup Navigation ---
setup_navigation()

# Se já logado, redireciona
role = st.session_state.get("role")
if role == "user":
    st.switch_page("pages/2_Painel_Usuario.py")
elif role == "admin":
    st.switch_page("pages/1_Admin.py")

# --- Tela de Login ---
st.title("Telegram Sender")
st.subheader("🔐 Login – Painel Premium")

uid = st.text_input("ID do cliente")
pwd = st.text_input("Senha", type="password")

if st.button("Entrar"):
    user = users_db.get(uid)

    if user and user.get("password") == pwd and user.get("active", True):
        st.session_state.role = "admin" if user.get("admin", False) else "user"
        st.session_state.user_id = uid

        if st.session_state.role == "admin":
            st.switch_page("pages/1_Admin.py")
        else:
            st.switch_page("pages/2_Painel_Usuario.py")
    else:
        st.error("Credenciais inválidas ou conta inativa.")
