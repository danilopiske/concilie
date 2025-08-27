import streamlit as st
from proc.funcoesbd import buscar_resumo_processamentos, deletar_processamento

def exibir_processamentos():
        
    st.title("📦 Interface de Processamentos")

    df = buscar_resumo_processamentos()

    if df.empty:
        st.info("Nenhum processamento encontrado.")
        st.stop()

    for idx, row in df.iterrows():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 1])
            col1.markdown(f"**🧾 Processamento:** `{row['id_processamento']}`")
            col2.markdown(f"**🗓️ Data:** `{row['data_processamento']}`")
            col3.markdown(f"**📍 EC:** `{row['ec_id']}`")
            col4.markdown(f"**Total Venda:** `{row['total_valor_venda']}`")
            

            col5.markdown(f"**📊 Nº:** {int(row['num_transacoes'])}")

            with st.expander("⚙️ Opções"):
                if st.button("❌ Deletar este processamento", key=f"del_{idx}"):
                    deletar_processamento(row['id_processamento'])
                    st.success(f"Processamento `{row['id_processamento']}` deletado com sucesso.")
                    st.rerun()

