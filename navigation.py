# navigation.py
import streamlit as st

def setup_navigation():
    st.sidebar.empty()
    # We intentionally avoid listing pages here; pages handle protection.
    # You can add buttons if you want explicit links:
    if "user" in st.session_state:
        uid = st.session_state["user"]
        st.sidebar.write(f"Usuário: {uid}")
        st.sidebar.button("Sair", key="logout_sidebar", on_click=lambda: _do_logout())
    else:
        st.sidebar.write("Faça login na página principal")

def _do_logout():
    # simple reload approach; pages import core.auth.logout if needed
    import core.auth as a
    a.logout()
