# core/auth.py
import streamlit as st
from core.data import load_users, save_users, now_iso, append_log

def login_screen():
    st.title("Telegram Sender")
    st.subheader("🔐 Login — Painel Premium")
    uid = st.text_input("ID do cliente")
    pwd = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        users = load_users()
        user = users.get(uid)
        if not user:
            st.error("Usuário não encontrado.")
            return False
        if user.get("password") != pwd:
            st.error("Senha incorreta.")
            return False
        if not user.get("active", False):
            st.error("Assinatura inativa. Contate o administrador.")
            return False

        # success
        st.session_state.role = user.get("role", "user")
        st.session_state.user_id = uid
        st.session_state.username = uid
        append_log({"user": uid, "action": "login", "ts": now_iso()})
        st.experimental_rerun()
        return True
    return False

def logout():
    user = st.session_state.get("user_id")
    if user:
        append_log({"user": user, "action": "logout", "ts": now_iso()})
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()

def is_logged_in():
    return "user_id" in st.session_state

def get_current_user():
    if not is_logged_in():
        return None
    users = load_users()
    return users.get(st.session_state.user_id)
