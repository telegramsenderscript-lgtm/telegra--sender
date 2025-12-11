import streamlit as st
from core.auth import check_session
from core.users import get_users, create_user, set_active


if not check_session() or st.session_state.user["role"] != "admin":
    st.error("Acesso negado.")
    st.stop()

st.title("Painel Administrativo")

users = get_users()
st.subheader("Criar Novo Usuário")

new_user = st.text_input("Novo usuário")
new_pass = st.text_input("Senha", type="password")

if st.button("Criar Usuário"):
    create_user(new_user, new_pass, active=False)
    st.success("Usuário criado!")
    st.rerun()

st.subheader("Gerenciar Usuários")

for u, data in users.items():
    col1, col2 = st.columns([3, 1])
    col1.write(f"{u} — Assinatura: {'Ativa' if data['active'] else 'Inativa'}")

    if col2.button("Alternar", key=u):
        set_active(u, not data["active"])
        st.rerun()
