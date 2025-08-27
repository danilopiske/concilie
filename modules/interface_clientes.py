import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
from proc.funcoesbd import (inserir_cliente, buscar_cliente_por_id, adicionar_ec, remover_ec, buscar_ecs_por_cliente,
carregar_clientes, atualizar_cliente,buscar_taxas_por_ec, adicionar_taxa, editar_taxa, excluir_taxa, excluir_todas_taxas_ec,
buscar_termos_filtraveis, adicionar_termo_filtravel, excluir_termo_filtravel,buscar_bandeiras_por_ec,salvar_bandeiras_por_ec)   


CAMINHO_TAXAS = "assets/parametros_taxas.json"
CAMINHO_TERMOS = "assets/parametros_filtraveis.json"
CAMINHO_BANDEIRAS = "assets/parametros_bandeiras_clients.json"
BANDEIRAS_PADRAO = ["Elo", "Mastercard", "Visa"]


# === Funções auxiliares ===

def carregar_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validar_cnpj(cnpj):
    numeros = ''.join(filter(str.isdigit, cnpj))
    return len(numeros) == 14

def validar_parcelas(pini, pfim):
    try:
        return int(pini) <= int(pfim)
    except:
        return False

def validar_datas(dini, dfim):
    try:
        dini_dt = datetime.strptime(dini, "%d/%m/%Y")
        dfim_dt = datetime.strptime(dfim, "%d/%m/%Y")
        return dini_dt <= dfim_dt
    except:
        return False

# === Interface principal ===

def interface():
    st.title("🏢 Clientes e Parâmetros")

    clientes = carregar_clientes()


    if not clientes:
        st.warning("Nenhum cliente cadastrado ainda.")
        st.stop()

    # Exibir cliente_id - nome_fantasia - cnpj
    opcoes_clientes = [f"{c['cliente_id']} - {c['nome_fantasia']} - {c['cnpj']}" for c in clientes]
    cliente_map = {f"{c['cliente_id']} - {c['nome_fantasia']} - {c['cnpj']}": c for c in clientes}

    cliente_label = st.selectbox("🔎 Selecione o cliente para trabalhar", opcoes_clientes)
    cliente = cliente_map[cliente_label]
    cliente_selecionado = cliente["cliente_id"]
    ecs = buscar_ecs_por_cliente(cliente["cliente_id"])
    if not ecs:
        st.warning("Este cliente não possui ECs cadastrados.")
        st.stop()
    ec_selecionado = st.selectbox("🔢 Escolha o EC para trabalhar", ecs)

    abas = st.tabs([
        "📇 Cadastro de Clientes",
        "💰 Taxas",
        "🔍 Termos Filtráveis",
        "🎴 Bandeiras"
    ])


    # === Aba 1: Cadastro ===
    with abas[0]:
        st.subheader("📇 Cadastro / Edição de Cliente")

        cliente_info = buscar_cliente_por_id(int(cliente_selecionado))

        # Pré-preencher variáveis
        c_id = cliente_info["cliente_id"] if cliente_info else ""
        nome = cliente_info["nome_fantasia"] if cliente_info else ""
        razao = cliente_info["razao_social"] if cliente_info else ""
        cnpj = cliente_info["cnpj"] if cliente_info else ""

        endereco = cliente_info.get("endereco", {}) if cliente_info else {}
        logradouro = endereco.get("logradouro", "")
        numero = endereco.get("numero", "")
        complemento = endereco.get("complemento", "")
        bairro = endereco.get("bairro", "")
        cidade = endereco.get("cidade", "")
        uf = endereco.get("uf", "")

        contatos = cliente_info.get("contatos", {}) if cliente_info else {}
        telefone1 = contatos.get("telefone1", "")
        telefone2 = contatos.get("telefone2", "")
        telefone3 = contatos.get("telefone3", "")
        email1 = contatos.get("email1", "")
        email2 = contatos.get("email2", "")

        bancario = cliente_info.get("bancario", {}) if cliente_info else {}
        banco = bancario.get("banco", "")
        agencia = bancario.get("agencia", "")
        conta = bancario.get("conta", "")

        st.text_input("Código do Cliente", value=c_id, key="cliente_id", disabled=True)
        nome = st.text_input("Nome Fantasia", value=nome)
        razao = st.text_input("Razão Social", value=razao)
        cnpj = st.text_input("CNPJ", value=cnpj)

        st.markdown("### 📍 Endereço")
        logradouro = st.text_input("Logradouro", value=logradouro)
        numero = st.text_input("Número", value=numero)
        complemento = st.text_input("Complemento", value=complemento)
        bairro = st.text_input("Bairro", value=bairro)
        cidade = st.text_input("Cidade", value=cidade)
        uf = st.text_input("UF", value=uf, max_chars=2)

        st.markdown("### ☎️ Contatos")
        telefone1 = st.text_input("Telefone 1", value=telefone1)
        telefone2 = st.text_input("Telefone 2", value=telefone2)
        telefone3 = st.text_input("Telefone 3", value=telefone3)
        email1 = st.text_input("E-mail 1", value=email1)
        email2 = st.text_input("E-mail 2", value=email2)

        st.markdown("### 🏦 Dados Bancários")
        banco = st.text_input("Banco", value=banco)
        agencia = st.text_input("Agência", value=agencia)
        conta = st.text_input("Conta", value=conta)

        if st.button("💾 Salvar"):
            if not cnpj or not nome:
                st.warning("CNPJ e Nome Fantasia são obrigatórios.")
                st.stop()
            if not validar_cnpj(cnpj):
                st.error("❌ CNPJ inválido.")
                st.stop()

            dados = {
                "cliente_id": int(c_id) if c_id else int(''.join(filter(str.isdigit, cnpj))[:8] + "0001"),
                "nome_fantasia": nome,
                "razao_social": razao,
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

            try:
                if cliente_info:
                    atualizar_cliente(dados)
                    st.success("Cliente atualizado com sucesso.")
                else:
                    inserir_cliente({**dados, "ecs": []})
                    st.success("Cliente cadastrado com sucesso.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar cliente: {e}")
                
        st.markdown("---")
        st.markdown("### 🔁 Gerenciar ECs vinculados")

        ecs_atuais = cliente_info.get("ecs", []) if cliente_info else []

        if ecs_atuais:
            st.write("**ECs vinculados:**")
            for ec in ecs_atuais:
                col1, col2 = st.columns([3, 1])
                col1.write(ec)
                if col2.button("🗑️ Remover", key=f"del_{ec}"):
                    try:
                        remover_ec(dados["cliente_id"], ec)
                        st.success(f"EC {ec} removido.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao remover EC: {e}")
        else:
            st.info("Nenhum EC vinculado ao cliente.")

        # Campo para adicionar novo EC
        novo_ec = st.text_input("➕ Novo EC", key="novo_ec_input")
        if st.button("Adicionar EC"):
            if not novo_ec.strip():
                st.warning("Informe um EC para adicionar.")
            else:
                try:
                    adicionar_ec(dados["cliente_id"], novo_ec.strip())
                    st.success(f"EC {novo_ec} adicionado com sucesso.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao adicionar EC: {e}")
    
        # === Aba 3: Taxas ===
    with abas[1]:
        st.subheader("📑 Taxas cadastradas")
        st.markdown(f"**Cliente:** {cliente['nome_fantasia']}  \n**CNPJ:** {cliente['cnpj']}")

        try:
            taxas = buscar_taxas_por_ec(ec_selecionado)
            if taxas:
                df_taxas = pd.DataFrame(taxas)
                st.dataframe(df_taxas.drop(columns=["id"]), use_container_width=True)

                st.markdown("### 🗑️ Excluir taxas individualmente")
                for i, linha in enumerate(taxas):
                    with st.expander(f"{linha['bandeira']} / {linha['forma_pagamento']} - {linha['parcelas_ini']}x a {linha['parcelas_fim']}x"):
                        st.write(f"**Taxa:** {linha['taxa']}%")
                        col1, col2 = st.columns([1, 4])
                        if col1.button("🗑️ Excluir", key=f"excluir_taxa_{linha['id']}"):
                            try:
                                excluir_taxa(linha["id"])
                                st.success("Taxa excluída com sucesso.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir taxa: {e}")
            else:
                st.info("Nenhuma taxa cadastrada para este EC.")
        except Exception as e:
            st.error(f"Erro ao buscar taxas: {e}")
            st.stop()

        st.markdown("### ➕ Inserir novas taxas")
        df_novo = pd.DataFrame([{
            "Bandeira": "", "Forma de pagamento": "", "Parcelado": "",
            "Parcelas Ini": "", "Parcelas Fim": "", "Data ini": "",
            "Data fim": "", "Taxa": ""
        }])
        df_editado = st.data_editor(df_novo, num_rows="dynamic", use_container_width=True)

        if st.button("Salvar novas taxas"):
            df_limpo = df_editado.dropna(how="all")
            if df_limpo.empty:
                st.warning("Nenhuma taxa informada.")
                st.stop()

            sucesso = 0
            for linha in df_limpo.to_dict(orient="records"):
                if not validar_parcelas(linha["Parcelas Ini"], linha["Parcelas Fim"]):
                    st.error("Erro: Parcelas inválidas.")
                    st.stop()
                if not validar_datas(linha["Data ini"], linha["Data fim"]):
                    st.error("Erro: Datas inválidas.")
                    st.stop()

                taxa_dict = {
                    "ec": ec_selecionado,
                    "bandeira": linha["Bandeira"].strip(),
                    "forma_pagamento": linha["Forma de pagamento"].replace("\n", " ").strip(),
                    "parcelado": linha["Parcelado"].strip(),
                    "parcelas_ini": int(linha["Parcelas Ini"]),
                    "parcelas_fim": int(linha["Parcelas Fim"]),
                    "data_ini": datetime.strptime(linha["Data ini"].strip(), "%d/%m/%Y").date(),
                    "data_fim": datetime.strptime(linha["Data fim"].strip(), "%d/%m/%Y").date(),
                    "taxa": float(linha["Taxa"].replace(",", "."))
                }

                if adicionar_taxa(taxa_dict):
                    sucesso += 1

            st.success(f"{sucesso} taxa(s) adicionada(s) com sucesso.")
            st.rerun()

    # === Aba 4: Termos filtráveis ===
    with abas[2]:
        st.subheader("🔍 Termos filtráveis")
        st.markdown(f"**Cliente:** {cliente['nome_fantasia']}  \n**CNPJ:** {cliente['cnpj']}")

        try:
            termos = buscar_termos_filtraveis(ec_selecionado)
        except Exception as e:
            st.error(f"Erro ao buscar termos: {e}")
            st.stop()

        st.markdown("### ➖ Remover termos existentes")
        if termos:
            for termo in termos:
                col1, col2 = st.columns([5, 1])
                col1.write(termo)
                if col2.button("🗑️ Remover", key=f"remover_{termo}"):
                    if excluir_termo_filtravel(ec_selecionado, termo):
                        st.success(f"Termo '{termo}' removido.")
                        st.rerun()
                    else:
                        st.error(f"Erro ao remover termo '{termo}'.")
        else:
            st.info("Nenhum termo filtrável cadastrado.")

        st.markdown("### ➕ Adicionar novo termo")
        novo_termo = st.text_input("Novo termo", key="novo_termo")
        if st.button("Adicionar termo"):
            if not novo_termo.strip():
                st.warning("Informe um termo.")
            elif adicionar_termo_filtravel(ec_selecionado, novo_termo):
                st.success(f"Termo '{novo_termo}' adicionado com sucesso.")
                st.rerun()
            else:
                st.error(f"Erro ao adicionar termo '{novo_termo}'.")

            
        # === Aba 5: Bandeiras Selecionadas ===
    with abas[3]:
        if not cliente_selecionado:
            st.info("Selecione um cliente para configurar as bandeiras.")
        else:
            st.subheader(f"🎴 Bandeiras Selecionadas para {cliente_selecionado}")

            try:
                with open("assets/parametros_bandeiras.json", "r", encoding="utf-8") as f:
                    lista_bandeiras = json.load(f)
            except Exception as e:
                st.error("Erro ao carregar as bandeiras disponíveis.")
                st.stop()

            nomes_bandeiras = [b["nome"] for b in lista_bandeiras]
            padrao_dict = {b["nome"]: int(b.get("padrao", False)) for b in lista_bandeiras}

            try:
                config_cliente = buscar_bandeiras_por_ec(ec_selecionado)
            except Exception as e:
                st.error(f"Erro ao buscar configurações: {e}")
                st.stop()

            # Se não houver config ainda, usar padrão
            if not config_cliente:
                config_cliente = padrao_dict.copy()

            colunas = st.columns(len(nomes_bandeiras))
            for i, b in enumerate(nomes_bandeiras):
                config_cliente[b] = 1 if colunas[i].checkbox(b, value=config_cliente.get(b, 0), key=f"ck_{b}") else 0

            if st.button("Salvar bandeiras"):
                if salvar_bandeiras_por_ec(ec_selecionado, config_cliente):
                    st.success("Bandeiras atualizadas com sucesso.")
                else:
                    st.error("Erro ao salvar as bandeiras.")
