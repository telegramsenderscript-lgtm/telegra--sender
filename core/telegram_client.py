import os
import asyncio
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

API_ID = int(os.environ.get("API_ID") or 0)
API_HASH = os.environ.get("API_HASH") or ""

# --- Ajuste para garantir que sessions seja um diretório ---
SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sessions")
if os.path.exists(SESSIONS_DIR) and not os.path.isdir(SESSIONS_DIR):
    os.remove(SESSIONS_DIR)
os.makedirs(SESSIONS_DIR, exist_ok=True)

def _session_path_for(phone):
    safe = phone.replace("+","").replace(" ","")
    return os.path.join(SESSIONS_DIR, f"{safe}.session")

# --- sync wrappers used by Flask ---
def api_send_code(phone):
    if not phone:
        return {"status":"error","error":"phone missing"}
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def _send():
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            res = await client.send_code_request(phone)
            await client.disconnect()
            return {"status":"ok","phone_code_hash": getattr(res,"phone_code_hash", None)}
        return loop.run_until_complete(_send())
    except Exception as e:
        return {"status":"error","error": str(e)}

def api_confirm_code(phone, code, phone_code_hash=None):
    if not phone:
        return {"status":"error","error":"phone missing"}
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def _confirm():
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            try:
                await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            except errors.SessionPasswordNeededError:
                return {"status":"2fa_required"}
            except Exception as e:
                return {"status":"error","error": str(e)}
            ss = client.session.save()
            p = _session_path_for(phone)
            with open(p, "w", encoding="utf-8") as f:
                f.write(ss)
            await client.disconnect()
            return {"status":"ok"}
        return loop.run_until_complete(_confirm())
    except Exception as e:
        return {"status":"error","error": str(e)}

def api_get_dialogs(phone):
    p = _session_path_for(phone)
    if not os.path.exists(p):
        return {"status":"error","error":"session not found"}
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def _dlg():
            session_str = open(p,"r",encoding="utf-8").read()
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await client.connect()
            dialogs = []
            async for d in client.get_dialogs():
                dialogs.append({"id": d.id, "name": getattr(d, "title", None)})
            await client.disconnect()
            return {"status":"ok","dialogs": dialogs}
        return loop.run_until_complete(_dlg())
    except Exception as e:
        return {"status":"error","error": str(e)}

def api_send_message_loop(phone, peer_id, message):
    p = _session_path_for(phone)
    if not os.path.exists(p):
        return {"status":"error","error":"session not found"}
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def _loop_send():
            session_str = open(p,"r",encoding="utf-8").read()
            client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await client.connect()
            if not await client.is_user_authorized():
                await client.disconnect()
                return {"status":"error","error":"not authorized"}
            while True:
                try:
                    await client.send_message(int(peer_id), message)
                    await client.disconnect()
                    return {"status":"ok"}
                except errors.ChatWriteForbiddenError:
                    await asyncio.sleep(0.2)
                except Exception as e:
                    await client.disconnect()
                    return {"status":"error","error": str(e)}
        return loop.run_until_complete(_loop_send())
    except Exception as e:
        return {"status":"error","error": str(e)}
