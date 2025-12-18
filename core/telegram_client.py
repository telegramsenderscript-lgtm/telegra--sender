import os
import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID") or 0)
API_HASH = os.environ.get("API_HASH") or ""

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

# garante que sessions seja pasta
if os.path.exists(SESSIONS_DIR) and not os.path.isdir(SESSIONS_DIR):
    os.remove(SESSIONS_DIR)
os.makedirs(SESSIONS_DIR, exist_ok=True)


def _safe(phone):
    return phone.replace("+", "").replace(" ", "")

def _pending_session(phone):
    return os.path.join(SESSIONS_DIR, f"{_safe(phone)}.pending")

def _final_session(phone):
    return os.path.join(SESSIONS_DIR, f"{_safe(phone)}.session")


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

            # salva session pendente
            with open(_pending_session(phone), "w") as f:
                f.write(session.save())

            await client.disconnect()
            return {"status": "ok"}

        return loop.run_until_complete(run())

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ================== CONFIRMAR CÓDIGO ==================
def api_confirm_code(phone, code):
    try:
        pending = _pending_session(phone)

        if not os.path.exists(pending):
            return {"status": "error", "error": "no pending session"}

        session_str = open(pending).read()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run():
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await client.connect()

            try:
                await client.sign_in(phone=phone, code=code)
            except errors.SessionPasswordNeededError:
                return {"status": "2fa_required"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

            # salva session final
            with open(_final_session(phone), "w") as f:
                f.write(client.session.save())

            os.remove(pending)
            await client.disconnect()
            return {"status": "ok"}

        return loop.run_until_complete(run())

    except Exception as e:
        return {"status": "error", "error": str(e)}
