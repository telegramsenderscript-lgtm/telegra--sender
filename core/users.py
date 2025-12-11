from core.storage import load_json, save_json

def get_users():
    return load_json("data/users.json")

def save_users(data):
    save_json("data/users.json", data)

def create_user(username, password, active=False):
    users = get_users()
    users[username] = {
        "password": password,
        "active": active,
        "role": "user"
    }
    save_users(users)

def set_active(username, status: bool):
    users = get_users()
    if username in users:
        users[username]["active"] = status
        save_users(users)
