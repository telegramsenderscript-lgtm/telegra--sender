import streamlit as st
from core.data import load_users

def login_screen():
    st.title("Login – Painel Premium")

    users = load_users()

    uid = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if uid in users and users[uid]["password"] == pwd and users[uid]["active"]:
            st.session_state["logged"] = True
            st.session_state["role"] = users[uid]["role"]
            st.session_state["uid"] = uid
            st.experimental_rerun()
        else:
            st.error("Credenciais inválidas ou conta inativa.")

def is_logged_in():
    return st.session_state.get("logged", False)

def get_current_user():
    return st.session_state.get("uid", None)
