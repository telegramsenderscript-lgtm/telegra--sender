# core/telegram_client.py
import os, asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from core.data import load_session, save_session, remove_session

API_ID = int(os.environ.get("API_ID") or 0)
API_HASH = os.environ.get("API_HASH") or None

_active_clients = {}

def _session_string_to_client(session_string):
    return TelegramClient(StringSession(session_string), API_ID, API_HASH)

def _client_from_uid(uid):
    if uid in _active_clients:
        return _active_clients[uid]
    session_string = load_session(uid)
    if session_string:
        client = _session_string_to_client(session_string)
    else:
        client = TelegramClient(StringSession(), API_ID, API_HASH)
    _active_clients[uid] = client
    return client

async def start_client_for_user(uid: str, phone: str):
    if not API_ID or not API_HASH:
        return {"status":"error","error":"API_ID/API_HASH not configured"}
    client = _client_from_uid(uid)
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        try:
            sent = await client.send_code_request(phone)
            _active_clients[uid] = client
            return {"status":"code_sent", "phone_code_hash": getattr(sent, "phone_code_hash", None)}
        except Exception as e:
            return {"status":"error","error": str(e)}
    else:
        _active_clients[uid] = client
        return {"status":"authorized"}

async def confirm_code_for_user(uid: str, phone: str, code: str, phone_code_hash=None):
    if not API_ID or not API_HASH:
        return {"status":"error","error":"API_ID/API_HASH not configured"}
    client = _client_from_uid(uid)
    if not client.is_connected():
        await client.connect()
    try:
        if phone_code_hash:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        else:
            await client.sign_in(phone, code)
    except SessionPasswordNeededError:
        return {"status":"2fa_required"}
    except PhoneCodeInvalidError:
        return {"status":"invalid_code"}
    except PhoneCodeExpiredError:
        return {"status":"code_expired"}
    except Exception as e:
        return {"status":"error","error":str(e)}
    try:
        ss = client.session.save()
        save_session(uid, ss)
    except:
        pass
    _active_clients[uid] = client
    return {"status":"authorized"}

async def list_dialogs_for_user(uid: str):
    if not API_ID or not API_HASH:
        return {"status":"error","error":"API_ID/API_HASH not configured"}
    client = _client_from_uid(uid)
    if not client.is_connected():
        await client.connect()
    if not await client.is_user_authorized():
        return {"status":"error","error":"not_authorized"}
    dialogs = []
    async for d in client.iter_dialogs():
        title = getattr(d.entity, "title", getattr(d.entity, "first_name", None))
        dialogs.append({"id": d.id, "title": title})
    return {"status":"ok","dialogs": dialogs}

async def send_message_for_user(uid: str, target, message: str):
    client = _client_from_uid(uid)
    if not client.is_connected():
        await client.connect()
    try:
        await client.send_message(int(target), message)
        return {"status":"ok"}
    except Exception as e:
        return {"status":"error","error": str(e)}

async def logout_user_for_user(uid: str):
    client = _active_clients.get(uid)
    if client:
        try:
            await client.disconnect()
        except:
            pass
        _active_clients.pop(uid, None)
    removed = remove_session(uid)
    return {"status":"logged_out", "removed": removed}
