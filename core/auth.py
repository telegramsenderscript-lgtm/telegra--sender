# core/auth.py
import streamlit as st
from core.data import load_users, append_user_log, now_iso

def is_logged_in():
    return "user" in st.session_state and st.session_state.user is not None

def get_current_user():
    if not is_logged_in():
        return None
    users = load_users()
    uid = st.session_state.user
    return users.get(uid)

def login_screen():
    st.title("Telegram Sender")
    st.subheader("🔐 Login — Painel Premium")

    uid = st.text_input("Usuário")
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
        # login ok, set session
        st.session_state.user = uid
        append_user_log(uid, {"action": "login", "ts": now_iso()})
        st.experimental_rerun()
        return True
    return False

def logout():
    uid = st.session_state.get("user")
    if uid:
        append_user_log(uid, {"action": "logout", "ts": now_iso()})
    # clear keys we used
    keys = list(st.session_state.keys())
    for k in keys:
        del st.session_state[k]
    st.experimental_rerun()
