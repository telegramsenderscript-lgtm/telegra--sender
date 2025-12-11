# pages/1_Admin.py
import streamlit as st
from core.auth import is_logged_in, get_current_user, logout
from core.data import load_users, save_users, add_user, edit_user, delete_user, append_user_log, load_user_logs, remove_session, now_iso

# protect
if not is_logged_in():
    st.error("Faça login (admin).")
    st.stop()

current = get_current_user()
if current.get("role") != "admin":
    st.error("Acesso restrito ao admin.")
    st.stop()

st.title("🔧 Painel Admin (CRUD)")

users = load_users()

st.subheader("Usuários (clique para editar)")
for uid, u in users.items():
    cols = st.columns([3,1,1,1,1])
    cols[0].write(f"**{uid}** — {u.get('phone','')}")
    cols[1].write("Ativo" if u.get("active", False) else "Inativo")
    cols[2].write(u.get("role","user"))
    if cols[3].button("Editar", key=f"edit_{uid}"):
        st.session_state.edit_uid = uid
        st.experimental_rerun()
    if cols[4].button("Deletar", key=f"del_{uid}"):
        delete_user(uid)
        append_user_log(uid, {"action":"deleted_by_admin","ts": now_iso()})
        st.success("Usuário removido.")
        st.experimental_rerun()

st.markdown("---")
st.subheader("Criar novo usuário")
with st.form("create"):
    new_id = st.text_input("ID (novo)")
    new_pwd = st.text_input("Senha")
    new_phone = st.text_input("Telefone (+55...)")
    new_active = st.checkbox("Ativo?", value=True)
    new_role = st.selectbox("Role", ["user","admin"])
    if st.form_submit_button("Criar"):
        try:
            add_user(new_id, new_pwd, role=new_role, active=new_active, phone=new_phone)
            append_user_log(new_id, {"action":"created_by_admin","ts": now_iso()})
            st.success("Usuário criado.")
            st.experimental_rerun()
        except Exception as e:
            st.error(str(e))

# Edit flow
if "edit_uid" in st.session_state:
    uid = st.session_state.edit_uid
    st.subheader(f"Editar usuário: {uid}")
    u = users.get(uid, {})
    with st.form("edit_form"):
        new_uid = st.text_input("Novo ID (deixe igual para não mudar)", value=uid)
        pwd = st.text_input("Senha", value=u.get("password",""))
        phone = st.text_input("Telefone", value=u.get("phone",""))
        active = st.checkbox("Ativo?", value=u.get("active", False))
        role = st.selectbox("Role", ["user","admin"], index=0 if u.get("role","user")=="user" else 1)
        if st.form_submit_button("Salvar"):
            try:
                edit_user(old_uid=uid, new_uid=new_uid, password=pwd, role=role, active=active, phone=phone)
                append_user_log(new_uid, {"action":"edited_by_admin","ts": now_iso()})
                st.success("Salvo.")
                del st.session_state.edit_uid
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))
    if st.button("Cancelar edição"):
        del st.session_state.edit_uid
        st.experimental_rerun()

st.markdown("---")
st.subheader("Ações administrativas")
sel = st.selectbox("Escolha usuário para ações:", list(users.keys()))
if st.button("Resetar sessão Telegram (apaga .session)"):
    removed = remove_session(sel)
    append_user_log(sel, {"action":"session_reset_by_admin","removed": removed, "ts": now_iso()})
    st.success(f"Arquivos removidos: {removed}")

if st.button("Ver logs do usuário selecionado"):
    logs = load_user_logs(sel)
    st.write(logs)
    st.download_button("Baixar logs deste usuário (JSON)", data=str(logs), file_name=f"{sel}_logs.json")
