import streamlit as st
from conf.auth import carregar_usuarios, salvar_usuarios, hash_senha

def exibir_cadastro():
    st.title("📝 Cadastro de Usuário")
    usuario = st.text_input("Novo Usuário")
    senha = st.text_input("Senha", type="password")
    nome = st.text_input("Nome completo")
    empresa = st.text_input("Empresa")
    grupo = st.selectbox("Grupo", ["FINANCIAL", "ADMIN", "OPERACIONAL"])

    if st.button("Cadastrar"):
        usuarios = carregar_usuarios()
        if any(u["usuario"] == usuario for u in usuarios):
            st.error("Usuário já existe.")
            return
        usuarios.append({
            "usuario": usuario,
            "senha": hash_senha(senha),
            "nome": nome,
            "empresa": empresa,
            "grupo": grupo
        })
        salvar_usuarios(usuarios)
        st.success("Usuário cadastrado com sucesso.")