# core/telegram_client.py
import asyncio
from telethon import TelegramClient
from telethon.sessions import MemorySession

# COLOQUE SEUS dados aqui (ou usar st.secrets)
API_ID = 32994616
API_HASH = "cf912432fa5bc84e7360944567697b08"

def _make_loop_and_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient(MemorySession(), API_ID, API_HASH, loop=loop)
    loop.run_until_complete(client.connect())
    return client, loop

def get_client():
    # armazenar em st.session_state is not available here (module-level),
    # so return a singleton stored in module globals
    global _CLIENT, _LOOP
    try:
        return _CLIENT, _LOOP
    except NameError:
        _CLIENT, _LOOP = _make_loop_and_client()
        return _CLIENT, _LOOP
