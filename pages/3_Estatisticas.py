# pages/3_Estatisticas.py
import streamlit as st
from core.auth import is_logged_in, get_current_user
from core.data import load_global_logs

if not is_logged_in():
    st.error("Faça login")
    st.stop()

user = get_current_user()
if user.get("role") != "admin":
    st.error("Acesso restrito a admin")
    st.stop()

st.title("📊 Estatísticas / Logs")
logs = load_global_logs()
st.write(f"Total de eventos: {len(logs)}")
if logs:
    st.dataframe(logs)
    st.download_button("Baixar logs JSON", data=str(logs), file_name="logs.json")
