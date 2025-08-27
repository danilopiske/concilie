import streamlit as st
import pandas as pd
import json
import os
from conf.auth import carregar_usuarios, salvar_usuarios, hash_senha

CAMINHO_BANDEIRAS = "assets/parametros_bandeiras.json"

# Utilitários para bandeiras
def carregar_bandeiras():
    if os.path.exists(CAMINHO_BANDEIRAS):
        with open(CAMINHO_BANDEIRAS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_bandeiras(lista):
    with open(CAMINHO_BANDEIRAS, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2)

def interface():
    st.title("⚙️ Parâmetros do Sistema")

    aba1, aba2 = st.tabs(["👤 Usuários", "💳 Bandeiras"])

    # === ABA 1: Usuários ===
    with aba1:
        st.subheader("➕ Cadastro de Novo Usuário")

        usuario = st.text_input("Usuário").strip()
        senha = st.text_input("Senha", type="password")
        nome = st.text_input("Nome completo")
        empresa = st.text_input("Empresa")
        grupo = st.selectbox("Grupo", ["FINANCIAL", "ADMIN", "OPERACIONAL"])

        if st.button("Cadastrar Usuário"):
            if not usuario or not senha:
                st.warning("Usuário e senha são obrigatórios.")
                return

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
            st.success("✅ Usuário cadastrado com sucesso!")
            st.rerun()

        st.divider()
        st.subheader("📋 Usuários Cadastrados")
        usuarios = carregar_usuarios()
        if not usuarios:
            st.info("Nenhum usuário cadastrado.")
        else:
            df = pd.DataFrame([{
                "Usuário": u["usuario"],
                "Nome": u.get("nome", ""),
                "Empresa": u.get("empresa", ""),
                "Grupo": u.get("grupo", "")
            } for u in usuarios])
            st.dataframe(df, use_container_width=True)

    # === ABA 2: Bandeiras ===
    with aba2:
        st.subheader("💳 Cadastro de Bandeiras Disponíveis")

        nova_bandeira = st.text_input("Nome da nova bandeira").strip()
        padrao = st.checkbox("Marcar como padrão", value=False)

        if st.button("Adicionar Bandeira"):
            if nova_bandeira:
                lista = carregar_bandeiras()
                if any(b["nome"].lower() == nova_bandeira.lower() for b in lista):
                    st.warning("Bandeira já existe.")
                else:
                    lista.append({"nome": nova_bandeira, "padrao": padrao})
                    salvar_bandeiras(lista)
                    st.success("✅ Bandeira adicionada com sucesso!")
                    st.rerun()

        lista = carregar_bandeiras()
        st.divider()
        st.subheader("📋 Bandeiras Cadastradas")

        if not lista:
            st.info("Nenhuma bandeira cadastrada.")
        else:
            for b in lista:
                col1, col2, col3 = st.columns([0.6, 0.3, 0.1])
                with col1:
                    st.markdown(f"- **{b['nome']}**")
                with col2:
                    st.markdown(f"🔧 Padrão: {'✅' if b['padrao'] else '❌'}")
                with col3:
                    if st.button("🗑️", key=f"del_{b['nome']}"):
                        lista = [item for item in lista if item["nome"] != b["nome"]]
                        salvar_bandeiras(lista)
                        st.success(f"Bandeira '{b['nome']}' removida.")
                        st.rerun()
