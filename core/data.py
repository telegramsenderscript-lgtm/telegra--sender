import json
import streamlit as st

USERS_FILE = "assets/users.json"
LOG_FILE = "assets/logs.json"

# ---------------- USERS ----------------

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_user(uid):
    return load_users().get(uid)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---------------- LOGS ----------------

def add_log(entry):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    logs.append(entry)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4)

