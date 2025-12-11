import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

# Cache global de clientes
_clients = {}           # uid -> TelegramClient
_client_locks = {}      # uid -> asyncio.Lock()


def _session_path(uid: str):
    return os.path.join(SESSIONS_DIR, f"{uid}.session")


# -----------------------------------------------------------------------------
# Obtém OU cria cliente sem recriar o event loop
# -----------------------------------------------------------------------------
async def _get_client(uid: str):
    if uid not in _client_locks:
        _client_locks[uid] = asyncio.Lock()

    async with _client_locks[uid]:
        # Já inicializado?
        if uid in _clients:
            client = _clients[uid]
            if not client.is_connected():
                try:
                    await client.connect()
                except:
                    pass
            return client

        # Criar sessão do usuário
        path = _session_path(uid)
        if os.path.exists(path):
            try:
                session = StringSession(open(path).read())
            except:
                session = StringSession()
        else:
            session = StringSession()

        # Criar cliente
        client = TelegramClient(session, API_ID, API_HASH)

        # Conectar
        await client.connect()

        _clients[uid] = client
        return client


# -----------------------------------------------------------------------------
# Solicita código de login
# -----------------------------------------------------------------------------
async def start_client_for_user(uid, phone):
    client = await _get_client(uid)

    # Já logado
    if await client.is_user_authorized():
        return {"status": "authorized"}

    # Enviar código
    try:
        res = await client.send_code_request(phone)
        return {"status": "code_sent", "phone_code_hash": res.phone_code_hash}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# -----------------------------------------------------------------------------
# Confirma o código e salva a sessão
# -----------------------------------------------------------------------------
async def confirm_code_for_user(uid, phone, code, phone_code_hash):
    client = await _get_client(uid)

    try:
        await client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=phone_code_hash
        )
    except Exception as e:
        if "2FA" in str(e):
            return {"status": "2fa_required"}
        return {"status": "error", "error": str(e)}

    # Salvar sessão permanente
    try:
        open(_session_path(uid), "w").write(client.session.save())
    except:
        pass

    return {"status": "authorized"}


# -----------------------------------------------------------------------------
# Lista chats/grupos
# -----------------------------------------------------------------------------
async def list_dialogs_for_user(uid):
    client = await _get_client(uid)

    try:
        dialogs = await client.get_dialogs()

        return {
            "status": "ok",
            "groups": [
                {
                    "name": d.name or "(sem nome)",
                    "id": d.id
                }
                for d in dialogs
            ]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# -----------------------------------------------------------------------------
# Envia mensagem (usado no loop de ataque)
# -----------------------------------------------------------------------------
async def send_message_for_user(uid, chat_id, msg):
    client = await _get_client(uid)

    try:
        await client.send_message(int(chat_id), msg)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# -----------------------------------------------------------------------------
# Logout direto no Telegram (se quiser usar alguma vez)
# -----------------------------------------------------------------------------
async def logout_user_for_user(uid):
    client = await _get_client(uid)

    try:
        await client.log_out()
    except:
        pass

    # Remove sessão gravada
    path = _session_path(uid)
    if os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass

    # Remove do cache
    _clients.pop(uid, None)

    return {"status": "logged_out"}
