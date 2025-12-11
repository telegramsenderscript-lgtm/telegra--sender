# core/data.py
import json
import os
import shutil
from datetime import datetime

USERS_FILE = "assets/users.json"
GLOBAL_LOG = "assets/logs.json"
LOGS_DIR = "data/logs"
SESSIONS_DIR = "sessions"

def ensure_dirs():
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(GLOBAL_LOG), exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(SESSIONS_DIR, exist_ok=True)

def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Users functions
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
    """
    Edits user. If new_uid provided and different, rename the user key (move data + logs + session).
    """
    users = load_users()
    if old_uid not in users:
        raise ValueError("Usuário não existe")

    # get old data
    u = users[old_uid].copy()

    # apply changes
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
        # create new key and remove old key
        users[target_uid] = u
        del users[old_uid]
        save_users(users)
        # move logs and session
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
    # remove logs and session
    _remove_user_artifacts(uid)

# logs
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

def load_user_logs(uid):
    ensure_dirs()
    path = os.path.join(LOGS_DIR, f"{uid}.json")
    return read_json(path, [])

def save_user_logs(uid, lst):
    ensure_dirs()
    path = os.path.join(LOGS_DIR, f"{uid}.json")
    write_json(path, lst)

def append_user_log(uid, entry: dict):
    logs = load_user_logs(uid)
    logs.append(entry)
    save_user_logs(uid, logs)
    # also global log
    append_global_log({"user": uid, **entry})

# session helpers (for Telethon .session files)
def get_session_path(uid):
    ensure_dirs()
    return os.path.join(SESSIONS_DIR, f"{uid}.session")

def remove_session(uid):
    path = get_session_path(uid)
    # Telethon may produce multiple files like uid.session, uid.session-journal, etc.
    base = os.path.splitext(path)[0]
    removed = []
    for fname in os.listdir(SESSIONS_DIR):
        if fname.startswith(os.path.basename(base)):
            try:
                os.remove(os.path.join(SESSIONS_DIR, fname))
                removed.append(fname)
            except:
                pass
    return removed

def _move_user_artifacts(old_uid, new_uid):
    # move logs file
    old_log = os.path.join(LOGS_DIR, f"{old_uid}.json")
    new_log = os.path.join(LOGS_DIR, f"{new_uid}.json")
    try:
        if os.path.exists(old_log):
            shutil.move(old_log, new_log)
    except Exception:
        pass
    # move session files (any files starting with old_uid)
    try:
        for fname in os.listdir(SESSIONS_DIR):
            if fname.startswith(old_uid):
                src = os.path.join(SESSIONS_DIR, fname)
                dst = os.path.join(SESSIONS_DIR, fname.replace(old_uid, new_uid, 1))
                shutil.move(src, dst)
    except Exception:
        pass

def _remove_user_artifacts(uid):
    # remove logs
    try:
        p = os.path.join(LOGS_DIR, f"{uid}.json")
        if os.path.exists(p):
            os.remove(p)
    except:
        pass
    # remove sessions
    remove_session(uid)

def now_iso():
    return datetime.utcnow().isoformat()
