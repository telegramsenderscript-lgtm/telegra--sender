import os
import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID") or 0)
API_HASH = os.environ.get("API_HASH") or ""

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)

def _safe(phone):
    return phone.replace("+", "").replace(" ", "")

def _session_path(phone):
    return os.path.join(SESSIONS_DIR, f"{_safe(phone)}.session")

def _hash_path(phone):
    return os.path.join(SESSIONS_DIR, f"{_safe(phone)}.hash")


# ================== ENVIAR CÓDIGO ==================
def api_send_code(phone):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run():
            session = StringSession()
            client = TelegramClient(session, API_ID, API_HASH)
            await client.connect()

            await client.send_code_request(phone)

            with open(_session_path(phone), "w") as f:
                f.write(session.save())

            with open(_hash_path(phone), "w") as f:
                f.write(client._phone_code_hash)

            await client.disconnect()
            return {"status": "ok"}

        return loop.run_until_complete(run())

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ================== CONFIRMAR CÓDIGO ==================
def api_confirm_code(phone, code):
    try:
        sp = _session_path(phone)
        hp = _hash_path(phone)

        if not os.path.exists(sp) or not os.path.exists(hp):
            return {"status": "error", "error": "session missing"}

        session_str = open(sp).read()
        phone_code_hash = open(hp).read().strip()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run():
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await client.connect()

            try:
                await client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=phone_code_hash
                )
            except errors.SessionPasswordNeededError:
                return {"status": "2fa_required"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

            with open(sp, "w") as f:
                f.write(client.session.save())

            await client.disconnect()
            return {"status": "ok"}

        return loop.run_until_complete(run())

    except Exception as e:
        return {"status": "error", "error": str(e)}
