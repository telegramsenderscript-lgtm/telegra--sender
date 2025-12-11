# pages/2_Painel_Usuario.py
import streamlit as st
import io, time, asyncio
from navigation import setup_navigation
from core.auth import is_logged_in, get_current_user, logout
from core.data import append_log, now_iso
from core.telegram_client import get_client

setup_navigation()

# protect
if not is_logged_in():
    st.error("Acesso negado. Faça login primeiro.")
    st.stop()

user = get_current_user()
st.title("📡 Painel do Usuário")
st.write(f"Usuário: **{st.session_state.user_id}** — Telefone autorizado: {user.get('phone','(não cadastrado)')}")

if not user.get("phone"):
    st.warning("Telefone não cadastrado. Peça ao admin para adicionar.")
    st.stop()

# client
client, loop = get_client()

# send code
if st.button("Enviar código SMS"):
    try:
        res = loop.run_until_complete(client.send_code_request(user["phone"]))
        st.session_state.phone_hash = res.phone_code_hash
        st.success("Código enviado. Verifique o Telegram.")
    except Exception as e:
        st.error(f"Erro ao enviar código: {e}")

code = st.text_input("Código recebido")
if st.button("Confirmar código"):
    try:
        loop.run_until_complete(client.sign_in(user["phone"], code, phone_code_hash=st.session_state.get("phone_hash")))
        st.success("Logado no Telegram!")
    except Exception as e:
        txt = str(e).lower()
        if "password" in txt:
            st.warning("Conta com 2FA: digite a senha abaixo.")
            st.session_state.need_2fa = True
        else:
            st.error(f"Erro: {e}")

if st.session_state.get("need_2fa"):
    pwd2 = st.text_input("Senha 2FA", type="password")
    if st.button("Confirmar 2FA"):
        try:
            loop.run_until_complete(client.sign_in(password=pwd2))
            st.success("2FA aceita.")
            st.session_state.need_2fa = False
        except Exception as e:
            st.error(f"Erro 2FA: {e}")

# list groups
if st.button("Listar grupos/canais"):
    try:
        dialogs = loop.run_until_complete(client.get_dialogs())
        choices = []
        for d in dialogs:
            if getattr(d, "is_group", False) or getattr(d, "is_channel", False):
                title = getattr(d.entity, "title", "") or str(d.id)
                choices.append((d.entity.id, title, d))
        st.session_state.groups = choices
        st.success(f"{len(choices)} grupos/canais carregados.")
    except Exception as e:
        st.error(f"Erro listando: {e}")

groups = st.session_state.get("groups") or []
if groups:
    opt_labels = [f"{t} (ID: {gid})" for gid, t, _ in groups]
    sel = st.selectbox("Selecione o grupo/canal", opt_labels)
    idx = opt_labels.index(sel)
    gid, title, dialog_obj = groups[idx]

    col1, col2 = st.columns([1,3])
    with col1:
        try:
            bio = io.BytesIO()
            loop.run_until_complete(client.download_profile_photo(dialog_obj.entity, file=bio))
            bio.seek(0)
            st.image(bio.read(), caption=title, use_column_width=True)
        except:
            st.write("(sem foto)")
    with col2:
        st.markdown(f"**{title}**")
        st.markdown(f"ID: `{gid}`")

    msg = st.text_area("Mensagem (sem ping):", height=120)

    # control state
    if "stop_flood" not in st.session_state:
        st.session_state.stop_flood = False
    if "attempts" not in st.session_state:
        st.session_state.attempts = 0

    attempts_pl = st.empty()
    status_pl = st.empty()
    ping_pl = st.empty()
    attempts_pl.info(f"Tentativas: {st.session_state.attempts}")

    if st.button("❌ Cancelar envio"):
        st.session_state.stop_flood = True
        status_pl.warning("Envio cancelado pelo usuário.")

    if st.button("🚀 ENVIAR EM LOOP ATÉ ABRIR"):
        if not msg:
            st.error("Digite a mensagem.")
        else:
            st.session_state.stop_flood = False
            st.session_state.attempts = 0

            async def flood_loop():
                while True:
                    if st.session_state.stop_flood:
                        return None
                    try:
                        st.session_state.attempts += 1
                        attempts_pl.info(f"Tentativas: {st.session_state.attempts}")
                        t0 = time.perf_counter()
                        await client.send_message(int(gid), msg)
                        ping_ms = (time.perf_counter() - t0) * 1000
                        return ping_ms
                    except Exception:
                        status_pl.warning("Grupo fechado — tentando novamente...")
                        await asyncio.sleep(0.03)

            try:
                ping = loop.run_until_complete(flood_loop())
                if ping is None:
                    status_pl.info("Envio cancelado.")
                else:
                    status_pl.success("Mensagem enviada com sucesso!")
                    ping_pl.info(f"⏱️ Ping: {ping:.2f} ms")
                    append_log = None
                    from core.data import append_log, now_iso
                    append_log({
                        "user": st.session_state.user_id,
                        "action": "sent_message",
                        "group_id": gid,
                        "group_title": title,
                        "attempts": st.session_state.attempts,
                        "ping_ms": round(ping,2),
                        "ts": now_iso()
                    })
            except Exception as e:
                status_pl.error(f"Erro durante envio: {e}")
else:
    st.info("Nenhum grupo carregado. Clique em 'Listar grupos/canais'.")

# logout
if st.button("Sair"):
    logout()
