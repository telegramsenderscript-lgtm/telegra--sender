# pages/2_Painel_Usuario.py
import streamlit as st
import asyncio, time
from core.auth import is_logged_in, get_current_user, logout
from core.data import append_user_log, now_iso
from core.telegram_client import start_client_for_user, confirm_code_for_user

# Proteção
if not is_logged_in():
    st.error("Faça login primeiro.")
    st.stop()

uid = st.session_state.user
user = get_current_user()

st.title("📡 Painel do Usuário")

# ============================
# INFORMAÇÕES BÁSICAS
# ============================
st.markdown(f"**Usuário:** {uid}")
st.markdown(f"**Seu número cadastrado:** `{user.get('phone', '(não cadastrado)')}`")

assinatura_ativa = user.get("active", False)

if assinatura_ativa:
    st.success("Assinatura: ATIVA")
else:
    st.error("Assinatura: INATIVA")
    st.warning("Renove sua assinatura para continuar.")
    st.stop()

st.markdown("---")

# ============================
# BOTÃO — ENVIAR CÓDIGO
# ============================

if st.button("📩 Enviar código para o Telegram"):
    phone = user.get("phone")
    if not phone:
        st.error("Telefone não cadastrado.")
    else:
        async def _start():
            return await start_client_for_user(uid, phone)

        try:
            result = asyncio.new_event_loop().run_until_complete(_start())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_start())

        if result.get("status") == "code_sent":
            st.success("Código enviado! Verifique o Telegram no celular.")
            st.session_state.phone_hash = result.get("phone_code_hash")

        elif result.get("status") == "authorized":
            st.info("Sessão já autorizada.")

        else:
            st.error(result)

# ============================
# CONFIRMAR CÓDIGO
# ============================

code = st.text_input("Digite o código recebido no Telegram:")

if st.button("✔ Confirmar código"):
    phone = user.get("phone")

    async def _confirm():
        return await confirm_code_for_user(
            uid, phone, code, st.session_state.get("phone_hash")
        )

    try:
        try:
            c = asyncio.get_event_loop().run_until_complete(_confirm())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            c = loop.run_until_complete(_confirm())

        if c.get("status") == "authorized":
            st.success("Autorizado com sucesso!")
            append_user_log(uid, {"action": "telegram_authorized", "ts": now_iso()})

        elif c.get("status") == "2fa_required":
            st.error("Sua conta tem 2FA — precisa inserir a senha.")

        else:
            st.error(c)

    except Exception as e:
        st.error(f"Erro: {e}")

st.markdown("---")
st.subheader("Envio simples para grupo")

group_id = st.text_input("Group ID")
msg = st.text_area("Mensagem")

if st.button("Enviar mensagem"):
    if not group_id or not msg:
        st.error("Preencha grupo e mensagem.")
    else:
        st.info("Função reduzida aqui — e
