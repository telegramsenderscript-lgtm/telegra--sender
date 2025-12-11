import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Salvamos as sessões diretamente dentro da pasta "assets"
SESSIONS_DIR = "assets"  # Não criar subpasta, evita erro no Streamlit Cloud


def session_file(user_id: str):
    """Retorna o caminho do arquivo de sessão do usuário."""
    return os.path.join(SESSIONS_DIR, f"{user_id}_session.txt")


def save_session(user_id: str, session_string: str):
    """Salva a sessão do usuário."""
    with open(session_file(user_id), "w") as f:
        f.write(session_string)


def load_session(user_id: str):
    """Carrega a sessão do usuário, se existir."""
    path = session_file(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return None


def delete_session(user_id: str):
    """Remove a sessão do usuário."""
    path = session_file(user_id)
    if os.path.exists(path):
        os.remove(path)


def get_client(user_id: str, api_id: str, api_hash: str):
    """Carrega o cliente Telegram com a sessão salva ou cria uma nova."""
    session = load_session(user_id)
    if session:
        return TelegramClient(StringSession(session), api_id, api_hash)
    else:
        return TelegramClient(StringSession(), api_id, api_hash)


async def start_client_for_user(user_id: str, api_id: str, api_hash: str):
    """Inicia o cliente, envia código e retorna o cliente ativo."""
    client = get_client(user_id, api_id, api_hash)

    if not client.is_connected():
        await client.connect()

    return client


async def confirm_code_for_user(user_id: str, api_id: str, api_hash: str, phone: str, code: str):
    """Finaliza login com código enviado ao Telegram."""
    client = get_client(user_id, api_id, api_hash)

    await client.connect()

    try:
        await client.sign_in(phone=phone, code=code)
    except Exception as e:
        return False, f"Erro ao validar código: {e}"

    # Após logar, salvar sessão
    session_string = client.session.save()
    save_session(user_id, session_string)

    return True, "Autenticado com sucesso!"


async def send_message(user_id: str, api_id: str, api_hash: str, target: str, message: str):
    """Envia mensagem usando sessão salva."""
    client = get_client(user_id, api_id, api_hash)

    await client.connect()

    try:
        await client.send_message(target, message)
        return True, "Mensagem enviada!"
    except Exception as e:
        return False, str(e)


def logout_user(user_id: str):
    """Remove sessão salva."""
    delete_session(user_id)
