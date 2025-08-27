import streamlit as st
from conf.auth import autenticar

def exibir_login():
    st.title("🔐 Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = autenticar(usuario, senha)
        if user:
            st.session_state.user = user["usuario"]
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")