import streamlit as st
from core.storage import load_json


def login_screen():
    users = load_json("data/users.json")

    st.header("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username in users and users[username]["password"] == password:
            st.session_state.user = users[username]
            st.session_state.username = username
            st.success("Login bem-sucedido!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


def logout_button():
    if st.button("Sair da Conta"):
        st.session_state.clear()
        st.rerun()


def check_session():
    return "user" in st.session_state
