import streamlit as st
from modules.tela_login import exibir_login
from modules.interface_parametros import interface as exibir_parametros
from modules.interface_clientes import interface as exibir_clientes
from modules.vendas import interface as vendas_interface
from modules.lancamentos import interface as lanc_interface
from modules.interface_processamentos import exibir_processamentos
from modules.interface_processamento import processamento
from modules.resultados_calculos import exibir_resultados_calculos

st.set_page_config(page_title="Conciliê", layout="wide")

if "user" not in st.session_state:
    exibir_login()
else:
    st.sidebar.title(f"👤 Usuário: {st.session_state.user}")
    menu = st.sidebar.radio("Menu", [
        "🏠 Início", "👥 Parametros",
        "Gerenciamento Clientes",
        "Gerenciar Processamentos",
        "💰 Processar Vendas", "📂 Processar Lançamentos", "Processamentos", "Resultados Calculos",
        "🚪 Sair"
    ])

    if menu == "🏠 Início":
        st.title("Bem-vindo ao Conciliê")
    elif menu == "👥 Parametros":
        exibir_parametros()
    elif menu == "Gerenciamento Clientes":
        exibir_clientes()
    elif menu == "Gerenciar Processamentos":
        exibir_processamentos()
    elif menu == "💰 Processar Vendas":
        vendas_interface()
    elif menu == "📂 Processar Lançamentos":
        lanc_interface()
    elif menu == "Processamentos":
        processamento()
    elif menu == "Resultados Calculos":
        exibir_resultados_calculos()
    elif menu == "🚪 Sair":
        st.session_state.clear()
        st.rerun()