import streamlit as st
from datetime import datetime
import pandas as pd
from proc.funcoesbd import registrar_calculo_vendas, buscar_processamentos_disponiveis

def processamento():
    st.title("🛠️ Processamento de Vendas – Atualização de Taxas")

    processamentos = buscar_processamentos_disponiveis()
    processamentoid = st.selectbox("Selecione o Processamento", processamentos)

    col1, col2 = st.columns(2)
    data_ini = col1.date_input("Data Inicial", value=datetime.now().replace(day=1))
    data_fim = col2.date_input("Data Final", value=datetime.now())

    id_calculo = st.text_input("ID do Cálculo", value=f"CALC_{datetime.now().strftime('%Y%m%d%H%M%S')}")

    modo_log = st.radio(
        "Modo de Cálculo Log:",
        options=[
            "log mes min", "log mes med",
            "log tri min", "log tri med",
            "log sem min", "log sem med"
        ],
        index=0
    )

    if st.button("▶️ Registrar Cálculo"):
        sucesso, logs = registrar_calculo_vendas(
            processamentoid=processamentoid,
            data_ini=pd.to_datetime(data_ini),
            data_fim=pd.to_datetime(data_fim),
            calc_id=id_calculo,
            calc_usuario=st.session_state.get("usuario", "usuário_teste"),
            modo_log=modo_log
        )
        
        for linha in logs:
            st.text(linha)

        if sucesso:
            st.success("Cálculo registrado com sucesso.")
        else:
            st.error("Erro ao registrar cálculo.")
