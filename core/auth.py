# core/auth.py
from flask import session, redirect, url_for
from core.data import load_users, append_user_log, now_iso

def is_logged_in():
    return "user" in session and session["user"] is not None

def get_current_user():
    if not is_logged_in():
        return None
    users = load_users()
    uid = session["user"]
    return users.get(uid)

def login_user(uid):
    """Grava login do usuário e registra log."""
    session["user"] = uid
    append_user_log(uid, {"action": "login", "ts": now_iso()})

def logout_user():
    """Remove o usuário da sessão e registra log."""
    uid = session.get("user")
    if uid:
        append_user_log(uid, {"action": "logout", "ts": now_iso()})
    session.clear()
