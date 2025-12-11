import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_FILE = os.path.join(BASE_DIR, "..", "users.json")
LOGS_FILE = os.path.join(BASE_DIR, "..", "logs.json")


# =============================== TEMPO =====================================

def now_iso():
    return datetime.utcnow().isoformat()


# =============================== USERS =====================================

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def update_user(uid, data: dict):
    users = load_users()
    if uid not in users:
        return False
    users[uid].update(data)
    save_users(users)
    return True


def delete_user(uid):
    users = load_users()
    if uid in users:
        del users[uid]
        save_users(users)
        return True
    return False


# =============================== LOGS =======================================

def load_logs():
    if not os.path.exists(LOGS_FILE):
        return []
    with open(LOGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_logs(logs: list):
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def append_user_log(uid, entry: dict):
    logs = load_logs()
    entry["uid"] = uid
    entry["ts"] = now_iso()
    logs.append(entry)
    save_logs(logs)
    return True


def get_user_logs(uid):
    logs = load_logs()
    return [l for l in logs if l.get("uid") == uid]


def clear_user_logs(uid):
    logs = load_logs()
    logs = [l for l in logs if l.get("uid") != uid]
    save_logs(logs)
    return True
