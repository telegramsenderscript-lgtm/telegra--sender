import json
import streamlit as st
from core.data import load_users

def login_user(username, password):
    users = load_users()

    for u in users:
        if u["username"] == username and u["password"] == password:
            st.session_state.user = u
            return True
    return False

def is_logged_in():
    return st.session_state.get("user") is not None

def get_current_user():
    return st.session_state.get("user", None)

def is_admin():
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "admin"

def has_active_subscription():
    user = get_current_user()
    if not user:
        return False
    return user.get("active", False)
