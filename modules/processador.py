import streamlit as st

# Configuração da página
st.set_page_config(page_title="Análise EC Cielo", layout="wide")


from modules.vendas import processar_vendas
from modules.lancamentos import processar_lancamentos
from modules.unir import processar_arquivos
from modules.interface_clientes import cadastrar_taxas
from modules.calcular_contratos import main as calcular_contratos_main
import os


# ---------- MENU LATERAL ----------
st.sidebar.title("📊 Análise EC Cielo")
opcao = st.sidebar.radio(
    "Selecione a opção:",
    [
        "Início",
        "Processar Lançamentos",
        "Processar Vendas",
        "Unir Resultados",
        "Cadastro de Taxas",
        "Calcular Contratos",
    ],
)

# ---------- TELA INICIAL ----------
if opcao == "Início":
    st.title("Bem-vindo à Análise EC Cielo! 🎯")
    st.markdown(
        """
        **Fluxo sugerido**

        1. **Processar Lançamentos**  
        2. **Processar Vendas**  
        3. **Unir Resultados**  
        4. **Cadastro de Taxas** (se necessário)  
        5. **Calcular Contratos**

        Use o menu lateral para navegar entre as etapas.
        """
    )

# ---------- PROCESSAR LANÇAMENTOS ----------
elif opcao == "Processar Lançamentos":
    st.title("📂 Processar Lançamentos")
    arquivos_lanc = st.file_uploader(
        "Selecione os arquivos de lançamentos",
        accept_multiple_files=True,
        type=["xlsx"],
        key="lanc",
    )

    if st.button("Processar Lançamentos"):
        if arquivos_lanc:
            caminho = processar_lancamentos(arquivos_lanc)
            if caminho:
                st.success(f"✅ Processado! Arquivo salvo em: {caminho}")
            else:
                st.error("❌ Falha no processamento.")
        else:
            st.warning("Selecione ao menos um arquivo.")

# ---------- PROCESSAR VENDAS ----------
elif opcao == "Processar Vendas":
    st.title("🛒 Processar Vendas")
    arquivos_vend = st.file_uploader(
        "Selecione os arquivos de vendas",
        accept_multiple_files=True,
        type=["xlsx"],
        key="vend",
    )

    if st.button("Processar Vendas"):
        if arquivos_vend:
            caminho = processar_vendas(arquivos_vend)
            if caminho:
                st.success(f"✅ Processado! Arquivo salvo em: {caminho}")
            else:
                st.error("❌ Falha no processamento.")
        else:
            st.warning("Selecione ao menos um arquivo.")

# ---------- UNIR RESULTADOS ----------
elif opcao == "Unir Resultados":
    st.title("🔗 Unir Resultados")

    usar_anteriores = st.checkbox(
        "Usar arquivos gerados anteriormente (padrão)", value=True
    )

    vendas_default = os.path.join("venda_planilhas", "vendas_consolidada.xlsx")
    lanc_default = os.path.join("lancamento_planilhas", "lancamento_consolidada.xlsx")

    if usar_anteriores and os.path.exists(vendas_default) and os.path.exists(lanc_default):
        st.info("Arquivos padrão encontrados e serão utilizados.")
        vendas_file = vendas_default
        lanc_file = lanc_default
    else:
        st.warning("Faça upload se desejar outros arquivos.")
        vendas_file = st.file_uploader("Arquivo de Vendas Consolidada", type=["xlsx"], key="vend_unir")
        lanc_file = st.file_uploader("Arquivo de Lançamento Consolidado", type=["xlsx"], key="lanc_unir")

    if st.button("Unir Arquivos"):
        if vendas_file and lanc_file:
            processar_arquivos(vendas_file, lanc_file)
        else:
            st.warning("Selecione (ou garanta a existência de) ambos os arquivos.")

# ---------- CADASTRO DE TAXAS ----------
elif opcao == "Cadastro de Taxas":
    st.title("💰 Cadastro de Taxas")
    cadastrar_taxas()

# ---------- CALCULAR CONTRATOS ----------
elif opcao == "Calcular Contratos":
    st.title("📑 Calcular Contratos")
    # Chama diretamente a função main do módulo; ela já possui a UI interna
    calcular_contratos_main()

# (não há necessidade de 'else', pois cobrimos todas as opções)