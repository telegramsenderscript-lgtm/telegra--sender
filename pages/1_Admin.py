# pages/1_Admin.py
import streamlit as st
import json, os
from core.auth import is_logged_in, get_current_user, logout
from core.data import load_users, save_users, load_logs

# navigation
from navigation import setup_navigation
setup_navigation()

# protect
user = get_current_user()
if not user or user.get("role") != "admin":
    st.error("Acesso negado. Login admin necessário.")
    st.stop()

st.title("🔧 Painel Admin")

users = load_users()

st.subheader("Usuários")
for uid, u in users.items():
    cols = st.columns([2,1,1,1])
    cols[0].write(f"**{uid}** — {u.get('phone','')}")
    cols[1].write("Ativo" if u.get("active", False) else "Inativo")
    cols[2].write(u.get("role", "user"))
    if cols[3].button("Editar", key=f"edit_{uid}"):
        st.session_state.edit_uid = uid

st.markdown("---")

# Create / Edit form
if "edit_uid" in st.session_state:
    uid = st.session_state.edit_uid
    st.subheader(f"Editar usuário: {uid}")
    u = users.get(uid, {})
    with st.form("edit_form"):
        pwd = st.text_input("Senha", value=u.get("password",""))
        phone = st.text_input("Telefone", value=u.get("phone",""))
        active = st.checkbox("Ativo?", value=u.get("active", False))
        role = st.selectbox("Role", ["user","admin"], index=0 if u.get("role","user")=="user" else 1)
        if st.form_submit_button("Salvar"):
            users[uid]["password"] = pwd
            users[uid]["phone"] = phone
            users[uid]["active"] = active
            users[uid]["role"] = role
            save_users(users)
            st.success("Salvo.")
            del st.session_state.edit_uid
            st.experimental_rerun()
    if st.button("Cancelar edição"):
        del st.session_state.edit_uid
        st.experimental_rerun()
else:
    st.subheader("Criar novo usuário")
    with st.form("create_form"):
        new_id = st.text_input("ID (ex: cliente123)")
        new_pwd = st.text_input("Senha")
        new_phone = st.text_input("Telefone (+55...)")
        new_active = st.checkbox("Ativo?", value=True)
        new_role = st.selectbox("Role", ["user","admin"])
        if st.form_submit_button("Criar usuário"):
            if new_id in users:
                st.error("Usuário já existe.")
            else:
                users[new_id] = {
                    "password": new_pwd,
                    "phone": new_phone,
                    "active": new_active,
                    "role": new_role
                }
                save_users(users)
                st.success("Usuário criado.")
                st.experimental_rerun()

st.markdown("---")
st.subheader("Logs do sistema")
logs = load_logs()
st.write(f"Total logs: {len(logs)}")
if logs:
    st.download_button("Baixar logs (JSON)", data=json.dumps(logs, indent=2, ensure_ascii=False), file_name="logs.json")
    st.dataframe(logs)
