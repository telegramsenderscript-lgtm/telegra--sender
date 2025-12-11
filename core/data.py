# core/data.py
import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
USERS_FILE = os.path.join(ASSETS_DIR, "users.json")
GLOBAL_LOG = os.path.join(ASSETS_DIR, "logs.json")

LOGS_DIR = os.path.join(BASE_DIR, "data", "logs")  # per-user logs stored here

SESSIONS_DIR = ASSETS_DIR  # session files saved as assets/<uid>_session.txt

def ensure_dirs():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    # ensure files exist
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
    if not os.path.exists(GLOBAL_LOG):
        with open(GLOBAL_LOG, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)

def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------------- Users ----------------
def load_users():
    ensure_dirs()
    return read_json(USERS_FILE, {})

def save_users(users: dict):
    ensure_dirs()
    write_json(USERS_FILE, users)

def add_user(uid, password, role="user", active=True, phone=""):
    users = load_users()
    if uid in users:
        raise ValueError("Usuário já existe")
    users[uid] = {"password": password, "role": role, "active": active, "phone": phone}
    save_users(users)
    return users[uid]

def edit_user(old_uid, new_uid=None, password=None, role=None, active=None, phone=None):
    users = load_users()
    if old_uid not in users:
        raise ValueError("Usuário não existe")
    u = users[old_uid].copy()
    if password is not None:
        u["password"] = password
    if role is not None:
        u["role"] = role
    if active is not None:
        u["active"] = active
    if phone is not None:
        u["phone"] = phone
    target_uid = new_uid or old_uid
    if target_uid != old_uid:
        if target_uid in users:
            raise ValueError("Novo ID já existe")
        users[target_uid] = u
        del users[old_uid]
        save_users(users)
        _move_user_artifacts(old_uid, target_uid)
    else:
        users[old_uid] = u
        save_users(users)
    return users

def delete_user(uid):
    users = load_users()
    if uid in users:
        del users[uid]
        save_users(users)
    _remove_user_artifacts(uid)

# ---------------- Logs ----------------
def load_global_logs():
    ensure_dirs()
    return read_json(GLOBAL_LOG, [])

def save_global_logs(lst):
    ensure_dirs()
    write_json(GLOBAL_LOG, lst)

def append_global_log(entry: dict):
    logs = load_global_logs()
    logs.append(entry)
    save_global_logs(logs)

def user_log_path(uid):
    ensure_dirs()
    return os.path.join(LOGS_DIR, f"{uid}.json")

def load_user_logs(uid):
    return read_json(user_log_path(uid), [])

def save_user_logs(uid, lst):
    write_json(user_log_path(uid), lst)

def append_user_log(uid, entry: dict):
    logs = load_user_logs(uid)
    logs.append(entry)
    save_user_logs(uid, logs)
    append_global_log({"user": uid, **entry})

def now_iso():
    return datetime.utcnow().isoformat()

# ---------------- Sessions (files in assets) ----------------
def session_file(uid):
    return os.path.join(SESSIONS_DIR, f"{uid}_session.txt")

def save_session(uid, session_string):
    path = session_file(uid)
    with open(path, "w", encoding="utf-8") as f:
        f.write(session_string)

def load_session(uid):
    p = session_file(uid)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    return None

def remove_session(uid):
    removed = []
    p = session_file(uid)
    try:
        if os.path.exists(p):
            os.remove(p)
            removed.append(os.path.basename(p))
    except:
        pass
    return removed

def _move_user_artifacts(old_uid, new_uid):
    # move per-user logs
    old_log = user_log_path(old_uid)
    new_log = user_log_path(new_uid)
    try:
        if os.path.exists(old_log):
            shutil.move(old_log, new_log)
    except:
        pass
    # move session file if exists
    old_s = session_file(old_uid)
    new_s = session_file(new_uid)
    try:
        if os.path.exists(old_s):
            shutil.move(old_s, new_s)
    except:
        pass

def _remove_user_artifacts(uid):
    # remove logs and session
    p = user_log_path(uid)
    try:
        if os.path.exists(p):
            os.remove(p)
    except:
        pass
    remove_session(uid)
