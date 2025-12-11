import streamlit as st

def setup_navigation():
    role = st.session_state.get("role", None)

    # Limpa sidebar
    st.sidebar.empty()

    # Só cria menu se estiver logado
    if role == "user":
        st.sidebar.page_link("pages/2_Painel_Usuario.py", label="Painel do Usuário")
        st.sidebar.page_link("app.py", label="Sair")

    elif role == "admin":
        st.sidebar.page_link("pages/1_Admin.py", label="Painel Admin")
        st.sidebar.page_link("pages/3_Estatisticas.py", label="Estatísticas")
        st.sidebar.page_link("app.py", label="Sair")
