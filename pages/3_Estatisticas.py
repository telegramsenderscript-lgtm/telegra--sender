import streamlit as st
from core.auth import check_session
from core.storage import load_json

if not check_session() or st.session_state.user["role"] != "admin":
    st.error("Acesso negado.")
    st.stop()

st.title("Estatísticas de Uso")
logs = load_json("data/logs.json")

st.json(logs)
