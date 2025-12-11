import streamlit as st
import json

st.title("📊 Estatísticas de Uso")

try:
    logs = json.load(open("assets/logs.json", "r", encoding="utf-8"))
except:
    logs = []

if not logs:
    st.info("Nenhum envio registrado.")
else:
    for l in logs:
        st.write(l)
        st.write("---")
