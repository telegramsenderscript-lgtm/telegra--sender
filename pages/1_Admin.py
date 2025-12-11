# pages/1_Admin.py
import streamlit as st
import json
import os
from core.auth import is_logged_in, get_current_user
from core.data import (
    load_users,
    save_users,
    add_user,
    edit_user,
    delete_user,
    append_user_log,
    load_user_logs,
    remove_session,
    now_iso,
    session_file,
)

# Proteção
if not is_logged_in():
    st.error("Faça login (admin).")
    st.stop()

cur = get_current_user()
if cur.get("role") != "admin":
    st.error("Acesso restrito ao admin.")
    st.stop()

st.title("🔧 Painel Admin — Gestão de Usuários")

users = load_users()

st.markdown("### 👥 Usuários cadastrados")
if not users:
    st.info("Ainda não há usuários cadastrados.")
else:
    for uid, u in users.items():
        c0, c1, c2, c3, c4 = st.columns([3,1,1,1,1])
        display_name = u.get("display_name") or uid
        c0.markdown(f"**{display_name}**  \n`{uid}`  \n📞 {u.get('phone','(não cadastrado)')}")
        c1.write("🟢 Ativo" if u.get("active", False) else "🔴 Inativo")
        c2.write(u.get("role","user"))
        if c3.button("Editar", key=f"e_{uid}"):
            st.session_state.edit_uid = uid
            st.experimental_rerun()
        if c4.button("Deletar", key=f"d_{uid}"):
            delete_user(uid)
            append_user_log(uid, {"action":"deleted_by_admin","ts": now_iso(), "by": cur.get("role")})
            st.success("Usuário removido.")
            st.experimental_rerun()

st.markdown("---")
st.markdown("### ➕ Criar novo usuário")
with st.form("create_user", clear_on_submit=True):
    new_id = st.text_input("ID (ex: cliente123)")
    new_display = st.text_input("Nome de exibição (opcional)")
    new_pwd = st.text_input("Senha", type="password")
    new_phone = st.text_input("Telefone (+55...)")
    new_active = st.checkbox("Ativo?", value=True)
    new_role = st.selectbox("Role", ["user","admin"])
    if st.form_submit_button("Criar"):
        try:
            add_user(new_id, new_pwd, role=new_role, active=new_active, phone=new_phone)
            # add display_name if provided
            if new_display:
                us = load_users()
                us[new_id]["display_name"] = new_display
                save_users(us)
            append_user_log(new_id, {"action":"created_by_admin","ts": now_iso(), "by": cur.get("role")})
            st.success("Usuário criado.")
            st.experimental_rerun()
        except Exception as e:
            st.error(str(e))

# Edit flow
if "edit_uid" in st.session_state:
    uid = st.session_state.edit_uid
    st.markdown("---")
    st.subheader(f"✏️ Editar usuário: {uid}")
    u = users.get(uid, {})
    with st.form("edit_user_form"):
        new_uid = st.text_input("Novo ID (deixe igual para não alterar)", value=uid)
        display_name = st.text_input("Nome de exibição", value=u.get("display_name",""))
        pwd = st.text_input("Senha (deixe em branco para manter)", type="password")
        phone = st.text_input("Telefone", value=u.get("phone",""))
        active = st.checkbox("Ativo?", value=u.get("active", False))
        role = st.selectbox("Role", ["user","admin"], index=0 if u.get("role","user")=="user" else 1)
        if st.form_submit_button("Salvar alterações"):
            try:
                edit_user(old_uid=uid,
                          new_uid=new_uid or uid,
                          password=pwd if pwd!="" else None,
                          role=role,
                          active=active,
                          phone=phone)
                # save display name
                us = load_users()
                if display_name:
                    us[new_uid or uid]["display_name"] = display_name
                    save_users(us)
                append_user_log(new_uid or uid, {"action":"edited_by_admin","ts": now_iso(), "by": cur.get("role")})
                st.success("Usuário salvo.")
                del st.session_state.edit_uid
                st.experimental_rerun()
            except Exception as e:
                st.error(str(e))
    if st.button("Cancelar edição"):
        del st.session_state.edit_uid
        st.experimental_rerun()

st.markdown("---")
st.subheader("⚙️ Ações administrativas rápidas")
col1, col2 = st.columns([2,2])
sel = col1.selectbox("Escolha usuário:", list(users.keys()) if users else [])
if sel:
    u = users.get(sel, {})
    col1.write(f"📛 {u.get('display_name') or sel}")
    col1.write(f"📞 {u.get('phone','(não cadastrado)')}")
    col1.write(f"Status: {'ATIVO' if u.get('active',False) else 'INATIVO'}")
    # session file info
    sf = session_file(sel)
    has_session = os.path.exists(sf)
    col2.write(f"Session: {'✅' if has_session else '❌'}")
    if col2.button("Resetar sessão Telegram (apaga arquivo)", key=f"reset_{sel}"):
        removed = remove_session(sel)
        append_user_log(sel, {"action":"session_reset_by_admin","removed": removed, "ts": now_iso(), "by": cur.get("role")})
        st.success(f"Arquivos removidos: {removed}")

    if col2.button("Forçar ativar assinatura", key=f"act_{sel}"):
        try:
            us = load_users()
            us[sel]["active"] = True
            save_users(us)
            append_user_log(sel, {"action":"activated_by_admin","ts": now_iso(), "by": cur.get("role")})
            st.success("Ativado.")
            st.experimental_rerun()
        except Exception as e:
            st.error(str(e))

    if col2.button("Forçar desativar assinatura", key=f"deact_{sel}"):
        try:
            us = load_users()
            us[sel]["active"] = False
            save_users(us)
            append_user_log(sel, {"action":"deactivated_by_admin","ts": now_iso(), "by": cur.get("role")})
            st.success("Desativado.")
            st.experimental_rerun()
        except Exception as e:
            st.error(str(e))

st.markdown("---")
st.subheader("📁 Logs do usuário / download")
if sel:
    logs = load_user_logs(sel)
    st.write(logs or "Sem logs")
    if logs:
        st.download_button("Baixar logs (JSON)", data=json.dumps(logs, ensure_ascii=False, indent=2), file_name=f"{sel}_logs.json")

st.markdown("---")
st.subheader("🗑️ Remover usuário")
if sel:
    if st.button("Deletar usuário selecionado"):
        delete_user(sel)
        append_user_log(sel, {"action":"deleted_by_admin","ts": now_iso(), "by": cur.get("role")})
        st.success("Usuário removido.")
        st.experimental_rerun()

st.markdown("---")
st.subheader("📥 Import / Export usuários (JSON)")
col_a, col_b = st.columns(2)
with col_a:
    uploaded = st.file_uploader("Importar users.json", type=["json"])
    if uploaded:
        try:
            data = json.load(uploaded)
            if isinstance(data, dict):
                save_users(data)
                st.success("Arquivo importado.")
                st.experimental_rerun()
            else:
                st.error("Formato inválido.")
        except Exception as e:
            st.error(str(e))
with col_b:
    if st.button("Exportar users.json"):
        st.download_button("Baixar users.json", data=json.dumps(load_users(), ensure_ascii=False, indent=2), file_name="users.json")

st.markdown("---")
st.subheader("📜 Logs globais")
from core.data import load_global_logs
glogs = load_global_logs()
st.write(f"Eventos totais: {len(glogs)}")
if glogs:
    st.dataframe(glogs)
    st.download_button("Baixar logs globais", data=json.dumps(glogs, ensure_ascii=False, indent=2), file_name="global_logs.json")
