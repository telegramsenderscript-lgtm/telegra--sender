import os
import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

os.makedirs(SESSIONS_DIR, exist_ok=True)

def _safe(phone):
    return phone.replace("+", "").replace(" ", "")

def _session_file(phone):
    return os.path.join(SESSIONS_DIR, f"{_safe(phone)}.session")

def _hash_file(phone):
    return os.path.join(SESSIONS_DIR, f"{_safe(phone)}.hash")

def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# --------- SEND CODE ---------
def api_send_code(phone):
    async def run():
        session = StringSession()
        client = TelegramClient(session, API_ID, API_HASH)
        await client.connect()

        await client.send_code_request(phone)

        with open(_session_file(phone), "w") as f:
            f.write(session.save())

        with open(_hash_file(phone), "w") as f:
            f.write(client._phone_code_hash)

        await client.disconnect()
        return {"status": "ok"}

    try:
        return _run(run())
    except Exception as e:
        return {"status": "error", "error": str(e)}

# --------- CONFIRM CODE ---------
def api_confirm_code(phone, code):
    try:
        session_str = open(_session_file(phone)).read()
        phone_code_hash = open(_hash_file(phone)).read()
    except:
        return {"status": "error", "error": "session missing"}

    async def run():
        client = TelegramClient(
            StringSession(session_str),
            API_ID,
            API_HASH
        )
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

        with open(_session_file(phone), "w") as f:
            f.write(client.session.save())

        await client.disconnect()
        return {"status": "ok"}

    return _run(run())
