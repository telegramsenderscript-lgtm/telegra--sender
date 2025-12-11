import asyncio
from telethon import TelegramClient
from telethon.sessions import MemorySession

api_id = 32994616
api_hash = "cf912432fa5bc84e7360944567697b08"

# manter vivo
if "loop" not in asyncio.__dict__:
    pass

def get_client():
    if "client" not in asyncio.__dict__:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        asyncio.client = TelegramClient(
            MemorySession(),
            api_id,
            api_hash,
            loop=loop
        )
        loop.run_until_complete(asyncio.client.connect())

    return asyncio.client, asyncio.get_event_loop()
