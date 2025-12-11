import streamlit as st
from core.data import load_users, save_users

st.title("🔧 Painel ADMIN")

if st.session_state.user_id != "admin":
    st.error("Você não é admin.")
    st.stop()

users = load_users()

st.subheader("Usuários cadastrados")

for uid, data in users.items():
    st.write(f"### {uid}")
    st.write(data)
    st.write("---")

st.subheader("Adicionar novo usuário")

new_uid = st.text_input("Novo usuário")
new_pwd = st.text_input("Senha")
new_phone = st.text_input("Telefone (+55...)")

if st.button("Criar"):
    users[new_uid] = {
        "password": new_pwd,
        "active": True,
        "phone": new_phone,
        "expires": None
    }

    save_users(users)
    st.success("Usuário criado com sucesso!")
    st.experimental_rerun()
