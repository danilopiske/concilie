import os
import sys
import time
import numpy as np
import pandas as pd
import streamlit as st
from openpyxl import load_workbook
from datetime import datetime

from proc.utils import (
    remover_acentos,
    normalizar_forma_pagamento,
    normalizar_bandeira
)

from proc.funcoesbd import (
    buscar_ecs_por_cliente,
    buscar_termos_filtraveis,
    buscar_bandeiras_por_ec,
    carregar_clientes,
    listar_processamentos_existentes,
    gerar_novo_id_processamento,
    inserir_vendas_processadas,
    inserir_vendas_filtradas,
    salvar_processamento,
    remover_vendas_duplicadas
)


def interface():
    st.title("📂 Processador de Lançamentos Cielo")

    lista_clientes = carregar_clientes()
    if not lista_clientes:
        st.warning("Nenhum cliente encontrado.")
        st.stop()

    opcoes_clientes = {
        f"{c['cliente_id']} - {c['nome_fantasia']} - {c['cnpj']}": c['cliente_id']
        for c in lista_clientes
    }

    cliente_label = st.selectbox("👤 Selecione o cliente", list(opcoes_clientes))
    cliente_id = opcoes_clientes[cliente_label]

    ecs = buscar_ecs_por_cliente(cliente_id)
    if not ecs:
        st.warning("Este cliente não possui ECs vinculados.")
        st.stop()

    ec_selecionado = st.selectbox("🏦 Escolha o EC", ecs)

    modo = st.radio("Modo de processamento", ["📦 Processamento novo", "🔄 Continuar existente"])
    descricao = ""
    id_processamento = ""
    data_proc = None

    if modo == "📦 Processamento novo":
        id_processamento, data_proc = gerar_novo_id_processamento(ec_selecionado)
        descricao = st.text_input(
            "Descrição do processamento",
            f"Processamento {data_proc.strftime('%d/%m/%Y %H:%M')}"
        )
    else:
        ids_existentes = listar_processamentos_existentes(ec_selecionado)
        if not ids_existentes:
            st.warning("Nenhum processamento existente encontrado para esse EC.")
            st.stop()
        id_processamento = st.selectbox("Selecione o processamento existente", ids_existentes)

    uploaded_files = st.file_uploader(
        "📂 Envie arquivos Excel para processar", accept_multiple_files=True, type=["xlsx"]
    )

    if uploaded_files:
        st.session_state.arquivos_lancamentos = uploaded_files

    arquivos = st.session_state.get("arquivos_lancamentos", [])

    if arquivos and st.button("📊 Processar Lançamentos"):
        resultado = processar_lancamentos(arquivos, cliente_id, ec_selecionado, id_processamento)

        if resultado:
            for msg in resultado:
                st.success(msg)
            if modo == "📦 Processamento novo":
                salvar_processamento(ec_selecionado, cliente_id, id_processamento, descricao, data_proc)
        else:
            st.error("❌ Nenhum arquivo foi processado.")
