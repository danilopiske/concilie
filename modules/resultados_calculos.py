import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
from conf.conf_bd import get_engine  # ajuste conforme seu projeto
import io

def exibir_resultados_calculos():
    st.title("📊 Resultados de Cálculos – Vendas Processadas + Cálculos")
    engine = get_engine()
    with engine.connect() as conn:
        # Lista de processamentoid disponíveis
        proc_ids = pd.read_sql("SELECT DISTINCT processamentoid FROM vendas_processadas ORDER BY 1 DESC", conn)
        processamentoid = st.selectbox("🔢 Processamento ID", proc_ids['processamentoid'].tolist())

        # Lista de cálculos disponíveis
        calc_ids = pd.read_sql("SELECT DISTINCT calc_id FROM vendas_calculos ORDER BY calc_id DESC", conn)
        calc_id = st.selectbox("🧾 Cálculo ID", calc_ids['calc_id'].tolist())

    col1, col2 = st.columns(2)
    data_ini = col1.date_input("📅 Data Inicial", value=datetime(2024, 1, 1))
    data_fim = col2.date_input("📅 Data Final", value=datetime.now())

    if st.button("🔍 Buscar Resultados"):
        with st.spinner("Carregando dados..."):
            with engine.connect() as conn:
                query = text("""
                    SELECT 
                        v.id AS id_venda,
                        v.processamentoid,
                        v.Data_da_venda,
                        v.Bandeira,
                        v.Forma_de_pagamento,
                        v.Taxas_Perc,
                        v.Valor_da_venda,
                        v.Valor_Descontado,
                        v.Valor_líquido_da_venda,
                        c.calc_id,
                        c.tx_cad, c.desc_cad, c.vl_liq_cad,
                        c.tx_log, c.desc_log, c.vl_liq_log,
                        c.calc_usuario, c.calc_data
                    FROM vendas_processadas v
                    LEFT JOIN vendas_calculos c ON v.id = c.id_venda
                    WHERE v.processamentoid = :proc_id
                      AND c.calc_id = :calc_id
                      AND v.Data_da_venda BETWEEN :data_ini AND :data_fim
                """)
                df = pd.read_sql_query(query, conn, params={
                    "proc_id": processamentoid,
                    "calc_id": calc_id,
                    "data_ini": data_ini,
                    "data_fim": data_fim
                })

        if df.empty:
            st.warning("⚠️ Nenhum resultado encontrado.")
        else:
            st.success(f"✅ {len(df)} registros encontrados.")
            st.dataframe(df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="Resultados")

            output.seek(0)
            st.download_button(
                label="⬇️ Baixar Excel",
                data=output,
                file_name=f"resultados_{calc_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

