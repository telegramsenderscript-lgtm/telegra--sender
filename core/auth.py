# app.py
import streamlit as st
from core.auth import login_screen, is_logged_in, get_current_user
from navigation import setup_navigation

st.set_page_config(page_title="Telegram Sender", layout="centered")
setup_navigation()

# If logged, redirect user by role:
if is_logged_in():
    user = get_current_user()
    role = user.get("role", "user")
    if role == "admin":
        st.experimental_set_query_params(page="admin")
    else:
        st.experimental_set_query_params(page="user")
    # show minimal message
    st.success(f"Você já está logado como {st.session_state.get('user_id')}. Use o menu.")
    st.stop()

# Not logged => show login screen
login_screen()
