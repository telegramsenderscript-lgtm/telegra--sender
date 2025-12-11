import streamlit as st
from core.auth import check_session
from core.access_control import has_active_subscription

if not check_session():
    st.error("Faça login primeiro.")
    st.stop()

user = st.session_state.user

st.title("Seu Painel")

st.info(f"Status da assinatura: **{'Ativa' if user['active'] else 'Inativa'}**")

if not has_active_subscription(user):
    st.warning("Você precisa de assinatura ativa para continuar.")
    st.stop()

st.success("Acesso Premium liberado!")

st.text_area("Sua mensagem:")
st.button("Enviar")
