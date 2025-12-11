import os
import json
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

_clients = {}           # uid -> TelegramClient
_client_locks = {}      # uid -> asyncio.Lock()


def _session_file(uid):
    return os.path.join(SESSIONS_DIR, f"{uid}.session")


async def _get_client(uid):
    if uid not in _client_locks:
        _client_locks[uid] = asyncio.Lock()

    async with _client_locks[uid]:
        if uid in _clients:
            return _clients[uid]

        path = _session_file(uid)
        session = StringSession(open(path).read()) if os.path.exists(path) else StringSession()

        client = TelegramClient(session, API_ID, API_HASH)
        await client.connect()

        _clients[uid] = client
        return client


async def start_client_for_user(uid, phone):
    client = await _get_client(uid)

    if await client.is_user_authorized():
        return {"status": "authorized"}

    res = await client.send_code_request(phone)
    return {"status": "code_sent", "phone_code_hash": res.phone_code_hash}


async def confirm_code_for_user(uid, phone, code, phone_code_hash):
    client = await _get_client(uid)

    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    except Exception as e:
        if "2FA" in str(e):
            return {"status": "2fa_required"}
        return {"status": "error", "error": str(e)}

    open(_session_file(uid), "w").write(client.session.save())
    return {"status": "authorized"}


async def list_dialogs_for_user(uid):
    client = await _get_client(uid)
    dialogs = await client.get_dialogs()

    return {
        "status": "ok",
        "groups": [
            {"name": d.name, "id": d.id}
            for d in dialogs
        ]
    }


async def send_message_for_user(uid, chat_id, msg):
    client = await _get_client(uid)

    try:
        await client.send_message(int(chat_id), msg)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
