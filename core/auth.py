import streamlit as st
from core.data import load_users

# -------------------------
# LOGIN CHECK
# -------------------------
def is_logged_in():
    return "user" in st.session_state and st.session_state.user is not None


# -------------------------
# GET CURRENT USER
# -------------------------
def get_current_user():
    if not is_logged_in():
        return None
    users = load_users()
    return users.get(st.session_state.user)


# -------------------------
# LOGOUT
# -------------------------
def logout():
    if "user" in st.session_state:
        del st.session_state["user"]
    st.session_state.clear()
    st.experimental_rerun()


# -------------------------
# LOGIN SCREEN
# -------------------------
def login_screen():
    st.title("🔐 Login — Telegram Sender")

    user_input = st.text_input("Usuário")
    pwd_input = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        users = load_users()

        if user_input not in users:
            st.error("Usuário não encontrado.")
            return

        user = users[user_input]

        if not user.get("active", False):
            st.error("Conta inativa.")
            return

        if user.get("password") != pwd_input:
            st.error("Senha incorreta.")
            return

        st.session_state.user = user_input
        st.success("Login realizado!")
        st.experimental_rerun()
