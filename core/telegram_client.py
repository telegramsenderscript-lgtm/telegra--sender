# core/telegram_client.py

import os
import asyncio
from telethon import TelegramClient, errors
from core.data import save_session, load_session

API_ID = 28942
API_HASH = "e3db99f0980c6175f3a0f6370676d280"

SESSIONS_DIR = "sessions"

# ---------- Correção para o Render (não crasha se existir arquivo chamado 'sessions') ----------
if not os.path.isdir(SESSIONS_DIR):
    try:
        os.makedirs(SESSIONS_DIR, exist_ok=True)
    except FileExistsError:
        pass
# -----------------------------------------------------------------------------------------------


def get_session_path(phone):
    """Retorna caminho da sessão do usuário."""
    safe = phone.replace("+", "")
    return os.path.join(SESSIONS_DIR, f"{safe}.session")


# -------------- SISTEMA DE EVENT LOOP (CORREÇÃO DO SEU ERRO ATUAL) -----------------

def get_event_loop():
    """Garante que o loop não mude — correção do erro no Render."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError()
        return loop
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

# ---------------------------------------------------------------------------


async def send_code(phone):
    """Envia código de login para o Telegram."""
    session_path = get_session_path(phone)
    client = TelegramClient(session_path, API_ID, API_HASH)

    await client.connect()
    try:
        sent = await client.send_code_request(phone)
        return {"status": "ok", "phone_code_hash": sent.phone_code_hash}
    except errors.PhoneNumberInvalidError:
        return {"status": "error", "error": "Telefone inválido."}
    finally:
        await client.disconnect()


async def confirm_code(phone, code, phone_hash):
    """Confirma código enviado ao Telegram."""
    session_path = get_session_path(phone)
    client = TelegramClient(session_path, API_ID, API_HASH)

    await client.connect()
    try:
        await client.sign_in(phone, code, phone_code_hash=phone_hash)
        return {"status": "ok"}
    except errors.SessionPasswordNeededError:
        return {"status": "2fa"}
    except errors.PhoneCodeInvalidError:
        return {"status": "error", "error": "Código inválido."}
    finally:
        await client.disconnect()


async def get_dialogs(phone):
    """Retorna grupos disponíveis para selecionar no dropdown."""
    session_path = get_session_path(phone)
    client = TelegramClient(session_path, API_ID, API_HASH)

    await client.connect()

    if not await client.is_user_authorized():
        return {"status": "error", "error": "Não autorizado."}

    dialogs = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            dialogs.append({
                "id": dialog.id,
                "title": dialog.title
            })

    await client.disconnect()
    return {"status": "ok", "dialogs": dialogs}


async def send_message_loop(phone, peer_id, message):
    """
    LOOP DE ENVIO:
    - Fica tentando enviar SEM PARAR
    - Envia instantaneamente quando o grupo abrir
    """

    session_path = get_session_path(phone)
    client = TelegramClient(session_path, API_ID, API_HASH)

    await client.connect()

    if not await client.is_user_authorized():
        return {"status": "error", "error": "Sessão expirada."}

    while True:
        try:
            await client.send_message(peer_id, message)
            return {"status": "ok", "sent": True}
        except errors.ChatWriteForbiddenError:
            # Grupo fechado — continua tentando
            await asyncio.sleep(0.5)
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ---------- Funções de interface síncrona (para chamadas Flask) -------------

def async_run(coro):
    """Executa qualquer função async mantendo o loop estável."""
    loop = get_event_loop()
    return loop.run_until_complete(coro)


def api_send_code(phone):
    return async_run(send_code(phone))


def api_confirm_code(phone, code, phone_hash):
    return async_run(confirm_code(phone, code, phone_hash))


def api_get_dialogs(phone):
    return async_run(get_dialogs(phone))


def api_send_message_loop(phone, peer_id, message):
    return async_run(send_message_loop(phone, peer_id, message))
