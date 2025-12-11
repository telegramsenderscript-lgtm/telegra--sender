# core/telegram_client.py
import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.errors import PhoneCodeInvalidError, PhoneCodeExpiredError

try:
    from streamlit import secrets
    API_ID = int(secrets["api_id"])
    API_HASH = secrets["api_hash"]
except Exception:
    # fallback values (you must set real ones in secrets)
    API_ID = 0
    API_HASH = ""

SESSIONS_DIR = "assets/sessions"

if not os.path.exists(SESSIONS_DIR):
    try:
        os.makedirs(SESSIONS_DIR, exist_ok=True)
    except Exception:
        pass  # evita erro no Streamlit Cloud


# keep active clients in-memory per Python process
_active = {}

def _session_file(uid):
    return os.path.join(SESSIONS_DIR, f"{uid}.session")

def _make_client(uid):
    session = _session_file(uid)
    client = TelegramClient(session, API_ID, API_HASH)
    return client

async def _ensure_connect(client):
    if not client.is_connected():
        await client.connect()

async def start_client_for_user(uid, phone):
    """
    Creates client and tries to connect. If not authorized, returns "code" state.
    """
    client = _make_client(uid)
    await _ensure_connect(client)

    if not await client.is_user_authorized():
        # request code
        try:
            sent = await client.send_code_request(phone)
            # keep client instance in _active for later confirmation
            _active[uid] = client
            return {"status": "code_sent", "phone_code_hash": getattr(sent, "phone_code_hash", None)}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        _active[uid] = client
        return {"status": "authorized"}

async def confirm_code_for_user(uid, phone, code, phone_code_hash=None):
    """
    Uses Telethon sign_in to complete login. Returns status.
    """
    # create client from session file (or existing)
    client = _active.get(uid) or _make_client(uid)
    await _ensure_connect(client)
    try:
        if phone_code_hash:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        else:
            await client.sign_in(phone, code)
    except SessionPasswordNeededError:
        return {"status": "2fa_required"}
    except PhoneCodeInvalidError:
        return {"status": "invalid_code"}
    except PhoneCodeExpiredError:
        return {"status": "code_expired"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

    _active[uid] = client
    return {"status": "authorized"}

async def send_message(uid, target, message):
    """
    Sends message using the user's session client.
    """
    client = _active.get(uid)
    if not client:
        # try instantiate from session file
        client = _make_client(uid)
        await _ensure_connect(client)
        if not await client.is_user_authorized():
            return {"status": "not_authorized"}
        _active[uid] = client

    try:
        await client.send_message(target, message)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def logout_user(uid):
    client = _active.get(uid)
    if client:
        try:
            await client.disconnect()
        except:
            pass
        if uid in _active:
            del _active[uid]
    # remove session files
    from core.data import remove_session
    removed = remove_session(uid)
    return {"status": "logged_out", "removed_files": removed}
