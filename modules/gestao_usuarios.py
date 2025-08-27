import streamlit as st
from conf.auth import carregar_usuarios, salvar_usuarios

def exibir_gestao():
    st.title("👥 Gestão de Usuários")
    usuarios = carregar_usuarios()
    for i, u in enumerate(usuarios):
        with st.expander(f"{u['usuario']} ({u['grupo']})"):
            u['nome'] = st.text_input("Nome", u["nome"], key=f"nome_{i}")
            u['empresa'] = st.text_input("Empresa", u["empresa"], key=f"empresa_{i}")
            u['grupo'] = st.selectbox("Grupo", ["FINANCIAL", "ADMIN", "OPERACIONAL"], index=["FINANCIAL", "ADMIN", "OPERACIONAL"].index(u["grupo"]), key=f"grupo_{i}")
            if st.button("Salvar", key=f"salvar_{i}"):
                salvar_usuarios(usuarios)
                st.success("Atualizado.")