import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
USERS_FILE = os.path.join(ASSETS_DIR, "users.json")
GLOBAL_LOG = os.path.join(ASSETS_DIR, "logs.json")

LOGS_DIR = os.path.join(BASE_DIR, "data", "logs")


def ensure_dirs():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f, indent=2)


def read_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---------------- USERS ----------------

def load_users():
    ensure_dirs()
    return read_json(USERS_FILE, {})


def save_users(users):
    write_json(USERS_FILE, users)


def add_user(uid, password, role="user", active=True, phone=""):
    users = load_users()
    if uid in users:
        raise ValueError("Usuário já existe")

    users[uid] = {
        "password": password,
        "role": role,
        "active": active,
        "phone": phone
    }
    save_users(users)


def edit_user(old_uid, password=None, active=None, phone=None):
    users = load_users()
    if old_uid not in users:
        raise ValueError("Usuário não existe")

    u = users[old_uid]
    if password:
        u["password"] = password
    if active is not None:
        u["active"] = active
    if phone is not None:
        u["phone"] = phone

    save_users(users)


def delete_user(uid):
    users = load_users()
    if uid in users:
        del users[uid]
        save_users(users)

    # remove logs
    log_path = os.path.join(LOGS_DIR, f"{uid}.json")
    if os.path.exists(log_path):
        os.remove(log_path)


def toggle_active(uid, state):
    users = load_users()
    if uid not in users:
        raise ValueError("Usuário não existe")

    users[uid]["active"] = state
    save_users(users)
