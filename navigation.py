# navigation.py
import streamlit as st

def setup_navigation():
    # hide default nav (we already set in config)
    # Build a controlled sidebar by role
    st.sidebar.empty()
    role = st.session_state.get("role")

    if role is None:
        # show only login link (we keep app.py as entry)
        st.sidebar.markdown("**Login**")
    elif role == "user":
        st.sidebar.markdown("**Menu**")
        st.sidebar.button("Painel do Usuário", key="nav_user", on_click=lambda: st.experimental_set_query_params(page="user"))
        st.sidebar.button("Sair", key="nav_logout_user", on_click=_logout)
    elif role == "admin":
        st.sidebar.markdown("**Admin**")
        st.sidebar.button("Painel Admin", key="nav_admin", on_click=lambda: st.experimental_set_query_params(page="admin"))
        st.sidebar.button("Estatísticas", key="nav_stats", on_click=lambda: st.experimental_set_query_params(page="stats"))
        st.sidebar.button("Sair", key="nav_logout_admin", on_click=_logout)

def _logout():
    # clear session and go to main
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.experimental_rerun()
