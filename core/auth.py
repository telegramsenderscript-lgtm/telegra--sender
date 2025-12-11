import streamlit as st
from core.data import load_users

def check_login(uid, pwd):
    users = load_users()

    if uid not in users:
        return False, "Usuário não encontrado."

    user = users[uid]

    if not user.get("active", False):
        return False, "Assinatura INATIVA."

    if user["password"] != pwd:
        return False, "Senha incorreta."

    return True, None


def login_screen():
    st.title("🔐 Login — Telegram Sender Premium")

    uid = st.text_input("Usuário")
    pwd = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        ok, msg = check_login(uid, pwd)

        if not ok:
            st.error(msg)
        else:
            st.success("Login realizado!")
            st.session_state.logged = True
            st.session_state.user_id = uid
            st.experimental_rerun()
