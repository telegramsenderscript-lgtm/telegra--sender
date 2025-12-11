# pages/2_Painel_Usuario.py
import streamlit as st
import io, time, asyncio
from core.auth import is_logged_in, get_current_user, logout
from core.data import append_user_log, now_iso, load_users
from core.telegram_client import start_client_for_user, confirm_code_for_user, send_message, logout_user

# protection
if not is_logged_in():
    st.error("Faça login primeiro.")
    st.stop()

uid = st.session_state.user
user = get_current_user()
st.title("📡 Painel do Usuário")
st.write(f"Usuário: **{uid}**")
st.write(f"Telefone autorizado: **{user.get('phone','(não cadastrado)')}**")
st.write(f"Assinatura: **{'ATIVA' if user.get('active', False) else 'INATIVA'}**")
if not user.get("active", False):
    st.error("Sua assinatura está inativa. Contate o administrador.")
    st.stop()

# send code
if st.button("Enviar código SMS para o telefone cadastrado"):
    phone = user.get("phone")
    if not phone:
        st.error("Telefone não cadastrado.")
    else:
        async def run_start():
            return await start_client_for_user(uid, phone)
        try:
            res = asyncio.get_event_loop().run_until_complete(run_start())
        except RuntimeError:
            res = asyncio.new_event_loop().run_until_complete(run_start())
        if isinstance(res, dict):
            if res.get("status") == "code_sent":
                st.success("Código enviado! Verifique o Telegram no telefone.")
                st.session_state.phone_hash = res.get("phone_code_hash")
            elif res.get("status") == "authorized":
                st.success("Sessão já autorizada.")
            else:
                st.error(str(res))

code = st.text_input("Código recebido")
if st.button("Confirmar código"):
    phone = user.get("phone")
    async def run_confirm():
        return await confirm_code_for_user(uid, phone, code, st.session_state.get("phone_hash"))
    try:
        try:
            cres = asyncio.get_event_loop().run_until_complete(run_confirm())
        except RuntimeError:
            cres = asyncio.new_event_loop().run_until_complete(run_confirm())
        if cres.get("status") == "authorized":
            st.success("Conta autorizada com sucesso!")
            append_user_log(uid, {"action":"telegram_authorized","ts": now_iso()})
        elif cres.get("status") == "2fa_required":
            st.warning("Conta exige 2FA (senha).")
            st.session_state.need_2fa = True
        else:
            st.error(str(cres))
    except Exception as e:
        st.error(f"Erro: {e}")

# list groups (sync approach)
if st.button("Listar grupos/canais"):
    try:
        # create a local client and request dialogs
        client = asyncio.new_event_loop().run_until_complete(start_client_for_user(uid, user.get("phone")))
        # if returns dict -> handle
        if isinstance(client, dict):
            if client.get("status") == "code_sent":
                st.info("Código enviado. Confirme-o primeiro.")
            elif client.get("status") == "authorized":
                st.success("Sessão autorizada.")
            else:
                st.error(client)
        else:
            # client is a Telethon client object — but our start_client returns dict usually.
            st.info("Sessão ativa.")
    except Exception as e:
        st.error(f"Erro ao listar grupos: {e}")

# The actual listing + sending is handled in the more manual way below using new client creation
# For brevity, provide a manual flow: ask group id and send

st.markdown("---")
st.subheader("Envio manual por Group ID")
group_id = st.text_input("Group ID (ex: -1001234567890)")
message = st.text_area("Mensagem (sem ping):", height=120)

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
    status_pl.warning("Envio cancelado.")

if st.button("🚀 ENVIAR EM LOOP ATÉ ABRIR"):
    if not message or not group_id:
        st.error("Preencha Group ID e mensagem.")
    else:
        st.session_state.stop_flood = False
        st.session_state.attempts = 0

        async def flood_loop():
            # create client instance from saved session
            ok, result = await confirm_code_for_user(uid, user.get("phone"), "", None) if False else (None, None)
            # We'll instantiate client using get_client logic inside telegram_client
            from core.telegram_client import _client_from_uid as _dummy  # not used directly
            # create client instance
            client = asyncio.get_event_loop().run_until_complete(start_client_for_user(uid, user.get("phone")))
            # if returned dict, not authorized
            if isinstance(client, dict):
                return {"status":"not_ready","msg":"Sessão não autorizada"}
            # client is actual Telethon client object? Our function returns dicts; to do safe send below we will create a temp client:
            from telethon import TelegramClient
            from telethon.sessions import StringSession
            session_string = load_session = None
            try:
                session_string = None
                p = f"assets/{uid}_session.txt"
                if os.path.exists(p):
                    with open(p,"r") as f:
                        session_string = f.read()
                if session_string:
                    tel = TelegramClient(StringSession(session_string), int(st.secrets["api_id"]), st.secrets["api_hash"])
                else:
                    tel = TelegramClient(StringSession(), int(st.secrets["api_id"]), st.secrets["api_hash"])
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(tel.connect())
            except Exception as e:
                return {"status":"error","error":str(e)}

            while True:
                if st.session_state.stop_flood:
                    return {"status":"cancelled"}
                try:
                    st.session_state.attempts += 1
                    attempts_pl.info(f"Tentativas: {st.session_state.attempts}")
                    t0 = time.perf_counter()
                    loop.run_until_complete(tel.send_message(int(group_id), message))
                    ping_ms = (time.perf_counter() - t0) * 1000
                    return {"status":"ok","ping":ping_ms}
                except Exception:
                    status_pl.warning("Grupo fechado — tentando...")
                    await asyncio.sleep(0.03)

        try:
            res = asyncio.new_event_loop().run_until_complete(flood_loop())
            if res.get("status") == "ok":
                status_pl.success("Mensagem enviada!")
                ping_pl.info(f"⏱️ Ping: {res.get('ping'):.2f} ms")
                append_user_log(uid, {"action":"sent_message","group_id":group_id,"attempts":st.session_state.attempts,"ping_ms":round(res.get("ping"),2),"ts": now_iso()})
            elif res.get("status") == "cancelled":
                status_pl.info("Envio cancelado.")
            else:
                status_pl.error(str(res))
        except Exception as e:
            status_pl.error(f"Erro: {e}")

if st.button("Sair"):
    logout()
