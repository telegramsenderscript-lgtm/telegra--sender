import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
USERS_FILE = os.path.join(ASSETS_DIR, "users.json")
LOGS_FILE = os.path.join(ASSETS_DIR, "logs.json")

def ensure_dirs_and_files():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
    if not os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

def now_iso():
    return datetime.utcnow().isoformat()

def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---- Users ----
def load_users():
    ensure_dirs_and_files()
    return read_json(USERS_FILE, {})

def save_users(users: dict):
    ensure_dirs_and_files()
    write_json(USERS_FILE, users)

def add_user(uid, password, role="user", active=True, phone=""):
    users = load_users()
    if uid in users:
        raise ValueError("Usuário já existe")
    users[uid] = {
        "password": password,
        "role": role,
        "active": bool(active),
        "phone": phone
    }
    save_users(users)

def edit_user(old_uid, password=None, active=None, phone=None):
    users = load_users()
    if old_uid not in users:
        raise ValueError("Usuário não existe")
    if password is not None and password != "":
        users[old_uid]["password"] = password
    if active is not None:
        users[old_uid]["active"] = bool(active)
    if phone is not None:
        users[old_uid]["phone"] = phone
    save_users(users)

def delete_user(uid):
    users = load_users()
    if uid in users:
        del users[uid]
        save_users(users)
    # remove logs for that user
    logs = load_logs()
    logs = [l for l in logs if l.get("uid") != uid]
    write_json(LOGS_FILE, logs)

def toggle_active(uid, state: bool):
    users = load_users()
    if uid not in users:
        raise ValueError("Usuário não existe")
    users[uid]["active"] = bool(state)
    save_users(users)


# ---- Logs ----
def load_logs():
    ensure_dirs_and_files()
    return read_json(LOGS_FILE, [])

def save_logs(logs: list):
    ensure_dirs_and_files()
    write_json(LOGS_FILE, logs)

def append_user_log(user, entry: dict):
    # entry is a dict like {"action":"...", ...}
    logs = load_logs()
    entry = entry.copy()
    # if provided user is a uid, put into uid, else if user is special, use 'actor'
    if isinstance(user, str):
        entry["actor"] = user
    entry.setdefault("ts", now_iso())
    logs.append(entry)
    save_logs(logs)

def clear_logs():
    write_json(LOGS_FILE, [])
