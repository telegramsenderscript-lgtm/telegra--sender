# pages/2_Painel_Usuario.py
import streamlit as st
import io, time, asyncio
from core.auth import is_logged_in, get_current_user, logout
from core.data import append_user_log, now_iso, load_users
from core.telegram_client import start_client_for_user, confirm_code_for_user, send_message, logout_user, get_client
from core.telegram_client import get_client as gc  # in case of local fallback

# protect
if not is_logged_in():
    st.error("Faça login primeiro.")
    st.stop()

user = get_current_user()
uid = st.session_state.user

st.title("📡 Painel do Usuário")
st.write(f"Usuário: **{uid}**")
st.write(f"Telefone autorizado: **{user.get('phone','(não cadastrado)')}**")
st.write(f"Assinatura: **{'ATIVA' if user.get('active', False) else 'INATIVA'}**")

if not user.get("active", False):
    st.error("Sua assinatura está inativa. Contate o administrador.")
    st.stop()

# get client + loop
from core.telegram_client import _make_client as _make_client_dummy  # not used; keep import safe
client, loop = None, None
try:
    from core.telegram_client import _make_client as _mm
except:
    pass

# SEND CODE (starts client or sends code)
if st.button("Enviar código SMS para o telefone cadastrado"):
    phone = user.get("phone")
    if not phone:
        st.error("Telefone não cadastrado. Peça ao admin.")
    else:
        async def run_start():
            from core.telegram_client import start_client_for_user
            return await start_client_for_user(uid, phone)
        try:
            res = asyncio.get_event_loop().run_until_complete(run_start())
        except RuntimeError:
            # fallback: create new loop
            res = asyncio.new_event_loop().run_until_complete(run_start())
        if isinstance(res, dict) and res.get("status") == "code_sent":
            st.success("Código enviado! Verifique o Telegram do número.")
            st.session_state.phone_hash = res.get("phone_code_hash")
        elif isinstance(res, dict) and res.get("status") == "authorized":
            st.success("Sessão já autorizada.")
        else:
            st.error(f"Erro: {res}")

code = st.text_input("Código recebido")
if st.button("Confirmar código"):
    phone = user.get("phone")
    try:
        async def run_confirm():
            return await confirm_code_for_user(uid, phone, code, st.session_state.get("phone_hash"))
        try:
            cres = asyncio.get_event_loop().run_until_complete(run_confirm())
        except RuntimeError:
            cres = asyncio.new_event_loop().run_until_complete(run_confirm())

        if cres.get("status") == "authorized":
            st.success("Conta autorizada com sucesso!")
            append_user_log(uid, {"action":"telegram_authorized","ts": now_iso()})
        elif cres.get("status") == "2fa_required":
            st.warning("Conta exige 2FA (senha). Use o campo 2FA abaixo.")
            st.session_state.need_2fa = True
        else:
            st.error(str(cres))
    except Exception as e:
        st.error(f"Erro: {e}")

if st.session_state.get("need_2fa"):
    pwd2 = st.text_input("Senha 2FA", type="password")
    if st.button("Confirmar 2FA"):
        async def run_2fa():
            from core.telegram_client import _make_client as make_client
            client = make_client(uid)
            return await client.sign_in(password=pwd2)
        st.error("2FA manual não implementada via UI. Faça pelo Telegram se preciso.")  # keep simple

# list groups
if st.button("Listar grupos/canais"):
    try:
        client = _make_client_dummy(uid)  # create client instance
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.connect())
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
    labels = [f"{t} (ID:{gid})" for gid,t,_ in groups]
    sel = st.selectbox("Selecione grupo/canal", labels)
    idx = labels.index(sel)
    gid, title, dialog = groups[idx]

    col1, col2 = st.columns([1,3])
    with col1:
        try:
            bio = io.BytesIO()
            loop.run_until_complete(dialog.download_profile_photo(file=bio))
            bio.seek(0)
            st.image(bio.read(), caption=title, use_column_width=True)
        except Exception:
            st.write("(sem foto)")
    with col2:
        st.markdown(f"**{title}**")
        st.markdown(f"ID: `{gid}`")

    msg = st.text_area("Mensagem (sem ping):", height=120)

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
                client = _make_client_dummy(uid)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(client.connect())
                while True:
                    if st.session_state.stop_flood:
                        return None
                    try:
                        st.session_state.attempts += 1
                        attempts_pl.info(f"Tentativas: {st.session_state.attempts}")
                        t0 = time.perf_counter()
                        loop.run_until_complete(client.send_message(int(gid), msg))
                        ping_ms = (time.perf_counter() - t0) * 1000
                        return ping_ms
                    except Exception:
                        status_pl.warning("Grupo fechado — tentando...")
                        await asyncio.sleep(0.03)

            try:
                ping = asyncio.new_event_loop().run_until_complete(flood_loop())
                if ping is None:
                    status_pl.info("Envio cancelado.")
                else:
                    status_pl.success("Mensagem enviada!")
                    ping_pl.info(f"⏱️ Ping: {ping:.2f} ms")
                    append_user_log(uid, {"action":"sent_message","group_id":gid,"group_title":title,"attempts":st.session_state.attempts,"ping_ms":round(ping,2),"ts": now_iso()})
            except Exception as e:
                status_pl.error(f"Erro durante envio: {e}")
else:
    st.info("Nenhum grupo carregado. Clique em 'Listar grupos/canais'.")

if st.button("Sair"):
    logout()
