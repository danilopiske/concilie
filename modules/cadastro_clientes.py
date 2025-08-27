import streamlit as st
import json
import os
import pandas as pd

ARQUIVO_CLIENTES = os.path.join("assets", "clientes.json")

def carregar_clientes():
    if os.path.exists(ARQUIVO_CLIENTES):
        try:
            with open(ARQUIVO_CLIENTES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar clientes: {e}")
    return []

def salvar_clientes(lista):
    try:
        with open(ARQUIVO_CLIENTES, "w", encoding="utf-8") as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar clientes: {e}")
        return False

def interface():
    st.title("👥 Cadastro de Clientes")

    aba1, aba2 = st.tabs(["➕ Cadastrar Cliente", "📋 Clientes Cadastrados"])

    # === ABA 1: Formulário de Cadastro ===
    with aba1:
        st.subheader("📄 Dados do Cliente")

        cliente_id = st.text_input("Código do Cliente / Grupo (cliente_id)").strip().upper()
        nome_fantasia = st.text_input("Nome Fantasia").strip()
        razao_social = st.text_input("Razão Social").strip()
        cnpj = st.text_input("CNPJ").strip()

        st.markdown("### 📍 Endereço")
        logradouro = st.text_input("Logradouro")
        numero = st.text_input("Número")
        complemento = st.text_input("Complemento")
        bairro = st.text_input("Bairro")
        cidade = st.text_input("Cidade")
        uf = st.text_input("UF", max_chars=2)

        st.markdown("### ☎️ Contatos")
        telefone1 = st.text_input("Telefone 1")
        telefone2 = st.text_input("Telefone 2")
        telefone3 = st.text_input("Telefone 3")
        email1 = st.text_input("E-mail 1")
        email2 = st.text_input("E-mail 2")

        st.markdown("### 🏦 Dados Bancários")
        banco = st.text_input("Banco")
        agencia = st.text_input("Agência")
        conta = st.text_input("Conta")

        if st.button("💾 Salvar Cliente"):
            if not cliente_id or not nome_fantasia or not cnpj:
                st.warning("Campos obrigatórios: Código do Cliente, Nome Fantasia e CNPJ.")
                return

            novo_cliente = {
                "cliente_id": cliente_id,
                "nome_fantasia": nome_fantasia,
                "razao_social": razao_social,
                "cnpj": cnpj,
                "endereco": {
                    "logradouro": logradouro,
                    "numero": numero,
                    "complemento": complemento,
                    "bairro": bairro,
                    "cidade": cidade,
                    "uf": uf.upper()
                },
                "contatos": {
                    "telefone1": telefone1,
                    "telefone2": telefone2,
                    "telefone3": telefone3,
                    "email1": email1,
                    "email2": email2
                },
                "bancario": {
                    "banco": banco,
                    "agencia": agencia,
                    "conta": conta
                }
            }

            clientes = carregar_clientes()

            # Verifica se já existe cliente_id
            if any(c["cliente_id"] == cliente_id for c in clientes):
                st.error(f"Cliente com ID '{cliente_id}' já existe.")
                return

            clientes.append(novo_cliente)

            if salvar_clientes(clientes):
                st.success(f"Cliente '{nome_fantasia}' cadastrado com sucesso!")
                st.rerun()

    # === ABA 2: Visualização ===
    with aba2:
        clientes = carregar_clientes()
        if not clientes:
            st.info("Nenhum cliente cadastrado ainda.")
            return

        df = pd.DataFrame([{
            "Código": c["cliente_id"],
            "Nome Fantasia": c["nome_fantasia"],
            "Razão Social": c["razao_social"],
            "CNPJ": c["cnpj"],
            "Cidade": c["endereco"].get("cidade", ""),
            "UF": c["endereco"].get("uf", "")
        } for c in clientes])

        st.dataframe(df, use_container_width=True)
