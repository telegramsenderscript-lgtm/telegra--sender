import streamlit as st
from core.auth import is_logged_in, login_screen, logout, get_current_user

# Verifica login
if not is_logged_in():
    login_screen()
    st.stop()

# Pega dados do usuário logado
user = get_current_user()

st.title("Painel do Usuário 🔐")

st.write(f"Usuário logado: **{st.session_state.user}**")
st.write(f"Telefone autorizado: **{user.get('phone', '(não cadastrado)')}**")

st.divider()

st.subheader("Enviar Código Telegram")
st.info("⚠️ Esta parte você vai integrar com seu cliente Telegram depois.")

if st.button("Sair"):
    logout()
    st.rerun()
