import json, os
from datetime import datetime

USERS_FILE = "data/users.json"
LOG_DIR = "data/logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf8") as f:
        return json.load(f)


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, indent=4)


def append_user_log(uid, log):
    path = os.path.join(LOG_DIR, f"{uid}.log")
    with open(path, "a", encoding="utf8") as f:
        f.write(json.dumps(log) + "\n")


def now_iso():
    return datetime.now().isoformat()
