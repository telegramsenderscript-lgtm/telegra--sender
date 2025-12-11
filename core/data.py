import json

USERS_FILE = "assets/users.json"
LOGS_FILE = "assets/logs.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_logs():
    try:
        with open(LOGS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_logs(data):
    with open(LOGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def add_log(user, action):
    logs = load_logs()
    logs.append({"user": user, "action": action})
    save_logs(logs)
