import streamlit as st
import time
import asyncio
from core.data import load_user, add_log
from core.telegram_client import get_client

st.title("📨 Envio Automático")

user = load_user(st.session_state.user_id)

if not user["active"]:
    st.error("Sua assinatura está INATIVA.")
    st.stop()

client, loop = get_client()

st.info(f"Número autorizado: **{user['phone']}**")

msg = st.text_area("Mensagem (sem ping):")

if st.button("ENVIAR AUTOMÁTICO"):

    if not msg:
        st.error("Escreva uma mensagem antes!")
        st.stop()

    placeholder = st.empty()
    attempts = 0

    async def send_loop():
        nonlocal attempts
        while True:
            attempts += 1
            placeholder.info(f"Tentando enviar... tentativa **{attempts}**")

            try:
                await client.send_message("me", msg)  # Mude depois
                return attempts
            except:
                await asyncio.sleep(0.05)

    try:
        total = loop.run_until_complete(send_loop())
        st.success(f"Mensagem enviada! Tentativas: {total}")

        add_log({
            "user": st.session_state.user_id,
            "timestamp": time.time(),
            "attempts": total
        })

    except Exception as e:
        st.error(f"Erro: {e}")
