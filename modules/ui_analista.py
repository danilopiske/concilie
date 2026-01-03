# modules/ui_analista.py
import os
import tempfile
import base64
from typing import Optional, Dict, List, Any
from datetime import datetime
import pandas as pd
import panel as pn
from sqlalchemy.engine import Engine

from conf.funcoesbd import (
    analise_criar,
    analise_listar,
    analise_buscar_por_id,
    analise_atualizar,
    analise_deletar,
    analise_adicionar_arquivo,
    analise_salvar_bandeiras,
    analise_salvar_formas_pagamento,
    analise_salvar_tipos_recebiveis,
    analise_salvar_periodos,
    analise_obter_resultados,
    contextos_listar,
    fetch_all,
    listar_processamentoids,
    listar_processamentos_detalhado_por_id,
    agregar_bandeiras_db,
    agregar_formas_pagamento_db,
    agregar_formas_pagamento_por_ano_db,
    agregar_periodos_db,
    agregar_periodos_bandeira_forma_db,
    agregar_semestral_db,
    agregar_trimestral_db,
    agregar_anual_db,
    agregar_recebiveis_db,
    obter_total_registros_processamento,
)
from proc.proc_importacao import (
    preparar_dataframe_de_arquivo,
    safe_read_file,
    is_multisheet_rede_file,
    safe_read_multisheet_file,
)


def _notify(kind: str, msg: str):
    n = getattr(pn.state, "notifications", None)
    if n:
        if hasattr(n, kind):
            getattr(n, kind)(msg)


def _extrair_bandeiras(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extrai bandeiras únicas do DataFrame com estatísticas detalhadas."""
    if df.empty:
        return []

    colunas_bandeira = ["Bandeira", "bandeira", "BANDEIRA", "Bandeira do Cartão"]
    coluna_bandeira = None
    for col in colunas_bandeira:
        if col in df.columns:
            coluna_bandeira = col
            break

    if not coluna_bandeira:
        return []

    colunas_valor = ["Valor_da_venda", "Valor da Transação", "Valor", "vl_venda"]
    coluna_valor = None
    for col in colunas_valor:
        if col in df.columns:
            coluna_valor = col
            break

    # Procurar colunas de taxa
    colunas_taxa_perc = ["Taxas_Perc", "Taxa_Percentual", "Taxa %", "Percentual"]
    coluna_taxa_perc = None
    for col in colunas_taxa_perc:
        if col in df.columns:
            coluna_taxa_perc = col
            break

    colunas_taxa_valor = ["Valor_descontado", "Taxa_Valor", "Valor Taxa", "Desconto"]
    coluna_taxa_valor = None
    for col in colunas_taxa_valor:
        if col in df.columns:
            coluna_taxa_valor = col
            break

    if coluna_valor:
        agg_dict = {coluna_valor: ["count", "sum", "mean", "min", "max"]}
        if coluna_taxa_perc:
            agg_dict[coluna_taxa_perc] = ["mean", "min", "max"]
        if coluna_taxa_valor:
            agg_dict[coluna_taxa_valor] = ["sum", "mean", "min", "max"]

        df_agg = df.groupby(coluna_bandeira).agg(agg_dict).reset_index()

        # Renomear colunas
        new_columns = ["bandeira"]
        if coluna_valor:
            new_columns.extend(
                ["quantidade", "valor_total", "valor_medio", "valor_min", "valor_max"]
            )
        if coluna_taxa_perc:
            new_columns.extend(["taxa_perc_media", "taxa_perc_min", "taxa_perc_max"])
        if coluna_taxa_valor:
            new_columns.extend(
                [
                    "taxa_valor_total",
                    "taxa_valor_media",
                    "taxa_valor_min",
                    "taxa_valor_max",
                ]
            )

        df_agg.columns = new_columns
    else:
        df_agg = df[coluna_bandeira].value_counts().reset_index()
        df_agg.columns = ["bandeira", "quantidade"]
        df_agg["valor_total"] = 0

    return df_agg.to_dict("records")


def _extrair_formas_pagamento(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extrai formas de pagamento únicas do DataFrame com estatísticas detalhadas."""
    if df.empty:
        return []

    colunas_forma = [
        "Forma_de_pagamento",
        "Forma de Pagamento",
        "Forma Pagamento",
        "Tipo",
    ]
    coluna_forma = None
    for col in colunas_forma:
        if col in df.columns:
            coluna_forma = col
            break

    if not coluna_forma:
        return []

    colunas_valor = ["Valor_da_venda", "Valor da Transação", "Valor", "vl_venda"]
    coluna_valor = None
    for col in colunas_valor:
        if col in df.columns:
            coluna_valor = col
            break

    # Procurar colunas de taxa
    colunas_taxa_perc = ["Taxas_Perc", "Taxa_Percentual", "Taxa %", "Percentual"]
    coluna_taxa_perc = None
    for col in colunas_taxa_perc:
        if col in df.columns:
            coluna_taxa_perc = col
            break

    colunas_taxa_valor = ["Valor_descontado", "Taxa_Valor", "Valor Taxa", "Desconto"]
    coluna_taxa_valor = None
    for col in colunas_taxa_valor:
        if col in df.columns:
            coluna_taxa_valor = col
            break

    if coluna_valor:
        agg_dict = {coluna_valor: ["count", "sum", "mean", "min", "max"]}
        if coluna_taxa_perc:
            agg_dict[coluna_taxa_perc] = ["mean", "min", "max"]
        if coluna_taxa_valor:
            agg_dict[coluna_taxa_valor] = ["sum", "mean", "min", "max"]

        df_agg = df.groupby(coluna_forma).agg(agg_dict).reset_index()

        # Renomear colunas
        new_columns = ["forma_pagamento"]
        if coluna_valor:
            new_columns.extend(
                ["quantidade", "valor_total", "valor_medio", "valor_min", "valor_max"]
            )
        if coluna_taxa_perc:
            new_columns.extend(["taxa_perc_media", "taxa_perc_min", "taxa_perc_max"])
        if coluna_taxa_valor:
            new_columns.extend(
                [
                    "taxa_valor_total",
                    "taxa_valor_media",
                    "taxa_valor_min",
                    "taxa_valor_max",
                ]
            )

        df_agg.columns = new_columns
    else:
        df_agg = df[coluna_forma].value_counts().reset_index()
        df_agg.columns = ["forma_pagamento", "quantidade"]
        df_agg["valor_total"] = 0

    return df_agg.to_dict("records")


def _extrair_tipos_recebiveis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extrai tipos de recebíveis do DataFrame."""
    if df.empty:
        return []

    # Procurar colunas que possam indicar tipo de recebível
    colunas_tipo = ["Tipo", "Tipo de Recebível", "Status", "Situação"]
    coluna_tipo = None
    for col in colunas_tipo:
        if col in df.columns:
            coluna_tipo = col
            break

    if not coluna_tipo:
        return []

    colunas_valor = ["Valor", "Valor do Recebível", "Valor a Receber"]
    coluna_valor = None
    for col in colunas_valor:
        if col in df.columns:
            coluna_valor = col
            break

    if coluna_valor:
        df_agg = (
            df.groupby(coluna_tipo).agg({coluna_valor: ["count", "sum"]}).reset_index()
        )
        df_agg.columns = ["tipo_recebivel", "quantidade", "valor_total"]
    else:
        df_agg = df[coluna_tipo].value_counts().reset_index()
        df_agg.columns = ["tipo_recebivel", "quantidade"]
        df_agg["valor_total"] = 0

    return df_agg.to_dict("records")


def _extrair_periodos(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extrai agregações por mês, trimestre, semestre e ano."""
    if df.empty:
        return []

    # Procurar coluna de data
    colunas_data = [
        "Data_da_venda",
        "Data da Transação",
        "Data",
        "data_venda",
        "Data_da_Transacao",
    ]
    coluna_data = None
    for col in colunas_data:
        if col in df.columns:
            coluna_data = col
            break

    if not coluna_data:
        return []

    # Procurar coluna de valor
    colunas_valor = ["Valor_da_venda", "Valor da Transação", "Valor", "vl_venda"]
    coluna_valor = None
    for col in colunas_valor:
        if col in df.columns:
            coluna_valor = col
            break

    # Converter data
    df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce")
    df = df[df[coluna_data].notna()].copy()

    if df.empty:
        return []

    periodos = []

    # Por mês
    df["mes"] = df[coluna_data].dt.to_period("M").astype(str)
    if coluna_valor:
        df_mes = (
            df.groupby("mes")
            .agg({coluna_valor: ["count", "sum", "mean", "min", "max"]})
            .reset_index()
        )
        df_mes.columns = [
            "periodo",
            "quantidade",
            "valor_total",
            "valor_medio",
            "valor_min",
            "valor_max",
        ]
    else:
        df_mes = df.groupby("mes").size().reset_index()
        df_mes.columns = ["periodo", "quantidade"]
        df_mes["valor_total"] = 0
        df_mes["valor_medio"] = 0
        df_mes["valor_min"] = 0
        df_mes["valor_max"] = 0

    for _, row in df_mes.iterrows():
        periodos.append(
            {
                "tipo_periodo": "mes",
                "periodo": row["periodo"],
                "quantidade": int(row["quantidade"]),
                "valor_total": float(row.get("valor_total", 0)),
                "valor_medio": float(row.get("valor_medio", 0)),
                "valor_min": float(row.get("valor_min", 0)),
                "valor_max": float(row.get("valor_max", 0)),
            }
        )

    # Por trimestre
    df["trimestre"] = df[coluna_data].dt.to_period("Q").astype(str)
    if coluna_valor:
        df_trim = (
            df.groupby("trimestre")
            .agg({coluna_valor: ["count", "sum", "mean", "min", "max"]})
            .reset_index()
        )
        df_trim.columns = [
            "periodo",
            "quantidade",
            "valor_total",
            "valor_medio",
            "valor_min",
            "valor_max",
        ]
    else:
        df_trim = df.groupby("trimestre").size().reset_index()
        df_trim.columns = ["periodo", "quantidade"]
        df_trim["valor_total"] = 0
        df_trim["valor_medio"] = 0
        df_trim["valor_min"] = 0
        df_trim["valor_max"] = 0

    for _, row in df_trim.iterrows():
        periodos.append(
            {
                "tipo_periodo": "trimestre",
                "periodo": row["periodo"],
                "quantidade": int(row["quantidade"]),
                "valor_total": float(row.get("valor_total", 0)),
                "valor_medio": float(row.get("valor_medio", 0)),
                "valor_min": float(row.get("valor_min", 0)),
                "valor_max": float(row.get("valor_max", 0)),
            }
        )

    # Por semestre
    df["semestre"] = (
        df[coluna_data].dt.year.astype(str)
        + "-S"
        + ((df[coluna_data].dt.month - 1) // 6 + 1).astype(str)
    )
    if coluna_valor:
        df_sem = (
            df.groupby("semestre")
            .agg({coluna_valor: ["count", "sum", "mean", "min", "max"]})
            .reset_index()
        )
        df_sem.columns = [
            "periodo",
            "quantidade",
            "valor_total",
            "valor_medio",
            "valor_min",
            "valor_max",
        ]
    else:
        df_sem = df.groupby("semestre").size().reset_index()
        df_sem.columns = ["periodo", "quantidade"]
        df_sem["valor_total"] = 0
        df_sem["valor_medio"] = 0
        df_sem["valor_min"] = 0
        df_sem["valor_max"] = 0

    for _, row in df_sem.iterrows():
        periodos.append(
            {
                "tipo_periodo": "semestre",
                "periodo": row["periodo"],
                "quantidade": int(row["quantidade"]),
                "valor_total": float(row.get("valor_total", 0)),
                "valor_medio": float(row.get("valor_medio", 0)),
                "valor_min": float(row.get("valor_min", 0)),
                "valor_max": float(row.get("valor_max", 0)),
            }
        )

    # Por ano
    df["ano"] = df[coluna_data].dt.year.astype(str)
    if coluna_valor:
        df_ano = (
            df.groupby("ano")
            .agg({coluna_valor: ["count", "sum", "mean", "min", "max"]})
            .reset_index()
        )
        df_ano.columns = [
            "periodo",
            "quantidade",
            "valor_total",
            "valor_medio",
            "valor_min",
            "valor_max",
        ]
    else:
        df_ano = df.groupby("ano").size().reset_index()
        df_ano.columns = ["periodo", "quantidade"]
        df_ano["valor_total"] = 0
        df_ano["valor_medio"] = 0
        df_ano["valor_min"] = 0
        df_ano["valor_max"] = 0

    for _, row in df_ano.iterrows():
        periodos.append(
            {
                "tipo_periodo": "ano",
                "periodo": row["periodo"],
                "quantidade": int(row["quantidade"]),
                "valor_total": float(row.get("valor_total", 0)),
                "valor_medio": float(row.get("valor_medio", 0)),
                "valor_min": float(row.get("valor_min", 0)),
                "valor_max": float(row.get("valor_max", 0)),
            }
        )

    return periodos


def make_analista_view(
    engine: Engine, usuario_logado: Optional[str]
) -> pn.viewable.Viewable:
    """Interface principal do Analista"""

    # Estado da análise atual
    analise_atual = {"id": None, "nome": None}

    # Novo: Seleção de processamento já realizado
    try:
        processamentoids = listar_processamentoids(engine)
    except Exception:
        processamentoids = []
    processamentoid_select = pn.widgets.Select(
        name="Processamento Importado",
        options=["Nenhum"] + processamentoids,
        value="Nenhum",
    )
    btn_carregar_processamento = pn.widgets.Button(
        name="Carregar Processamento", button_type="primary"
    )

    # Widgets principais
    nome_analise_input = pn.widgets.TextInput(
        name="Nome da Análise", placeholder="Ex: Análise Vendas 2024"
    )
    descricao_input = pn.widgets.TextAreaInput(
        name="Descrição", placeholder="Descrição opcional da análise", height=80
    )
    contexto_select = pn.widgets.Select(
        name="Contexto", options=["padrao"], value="padrao"
    )
    tipo_arquivo_select = pn.widgets.Select(
        name="Tipo de Arquivo",
        options={"Venda": "V", "Lançamento": "L", "Recebíveis": "R"},
        value="V",
    )

    # Carregar contextos
    try:
        contextos = contextos_listar(engine)
        contexto_select.options = ["padrao"] + [
            c["nome"] for c in contextos if c["nome"] != "padrao"
        ]
    except:
        pass

    # Seleção de análise existente
    analises_select = pn.widgets.Select(
        name="Análises Existentes", options=[], value=None, width=400
    )
    btn_carregar_analise = pn.widgets.Button(
        name="Carregar Análise", button_type="primary"
    )

    # Upload de arquivos
    file_input = pn.widgets.FileInput(accept=".xlsx,.xls,.csv", multiple=True)
    btn_processar_arquivos = pn.widgets.Button(
        name="📊 Processar Arquivos", button_type="primary", disabled=True
    )

    # Lista de arquivos processados
    arquivos_tabulator = pn.widgets.Tabulator(
        pd.DataFrame(columns=["#", "Arquivo", "Registros", "Status"]),
        height=200,
        sizing_mode="stretch_width",
        selectable="checkbox",
        pagination="local",
        page_size=10,
    )

    # Resultados - Tabulators individuais
    tabulator_bandeiras = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=300,
        sizing_mode="stretch_width",
        name="Bandeiras",
    )
    tabulator_formas = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=300,
        sizing_mode="stretch_width",
        name="Formas de Pagamento",
    )
    tabulator_recebiveis = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=300,
        sizing_mode="stretch_width",
        name="Tipos de Recebíveis",
    )
    tabulator_periodos_mes = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=300,
        sizing_mode="stretch_width",
        name="Períodos - Mês",
    )
    tabulator_periodos_trimestre = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=300,
        sizing_mode="stretch_width",
        name="Períodos - Trimestre",
    )
    tabulator_periodos_semestre = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=300,
        sizing_mode="stretch_width",
        name="Períodos - Semestre",
    )
    tabulator_periodos_ano = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=300,
        sizing_mode="stretch_width",
        name="Períodos - Ano",
    )
    tabulator_formas_por_ano = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=400,
        sizing_mode="stretch_width",
        name="Formas de Pagamento por Ano",
    )

    # Tabulators de períodos detalhados (período + bandeira + forma)
    tabulator_completo = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=400,
        sizing_mode="stretch_width",
        name="Visão Completa",
    )
    tabulator_anual = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=400,
        sizing_mode="stretch_width",
        name="Análise Anual",
    )
    tabulator_semestral = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=400,
        sizing_mode="stretch_width",
        name="Análise Semestral",
    )
    tabulator_trimestral = pn.widgets.Tabulator(
        pd.DataFrame(),
        height=400,
        sizing_mode="stretch_width",
        name="Análise Trimestral",
    )

    status_pane = pn.pane.Markdown("", sizing_mode="stretch_width")

    # Estado interno
    arquivos_processados = []
    resultados_atuais = {
        "bandeiras": [],
        "formas_pagamento": [],
        "tipos_recebiveis": [],
        "periodos": [],
    }

    def atualizar_lista_analises():
        """Atualiza a lista de análises disponíveis"""
        try:
            analises = analise_listar(engine, usuario_logado)
            opts = {
                f"{a['id']} - {a['nome_analise']} ({a['status']})": a["id"]
                for a in analises
            }
            analises_select.options = list(opts.keys())
        except Exception as e:
            _notify("error", f"Erro ao carregar análises: {e}")

    def criar_nova_analise():
        """Cria uma nova análise"""
        nome = nome_analise_input.value.strip()
        if not nome:
            return _notify("warning", "Informe um nome para a análise.")

        try:
            analise_id = analise_criar(
                engine,
                nome,
                descricao_input.value.strip() if descricao_input.value else None,
                usuario_logado,
            )
            analise_atual["id"] = analise_id
            analise_atual["nome"] = nome

            btn_processar_arquivos.disabled = False
            status_pane.object = f"✅ **Análise criada:** {nome} (ID: {analise_id})"
            _notify("success", f"Análise '{nome}' criada com sucesso!")
            atualizar_lista_analises()
        except Exception as e:
            _notify("error", f"Erro ao criar análise: {e}")

    def carregar_analise():
        """Carrega uma análise existente"""
        if not analises_select.value:
            return _notify("warning", "Selecione uma análise para carregar.")

        try:
            analise_id = int(analises_select.value.split(" - ")[0])
            analise = analise_buscar_por_id(engine, analise_id)
            if not analise:
                return _notify("error", "Análise não encontrada.")

            analise_atual["id"] = analise_id
            analise_atual["nome"] = analise["nome_analise"]
            nome_analise_input.value = analise["nome_analise"]
            descricao_input.value = analise.get("descricao", "") or ""

            # Carregar resultados salvos
            resultados = analise_obter_resultados(engine, analise_id)
            resultados_atuais.update(resultados)

            # Atualizar tabs
            if resultados["bandeiras"]:
                tabulator_bandeiras.value = pd.DataFrame(resultados["bandeiras"])
            else:
                tabulator_bandeiras.value = pd.DataFrame()
            if resultados["formas_pagamento"]:
                tabulator_formas.value = pd.DataFrame(resultados["formas_pagamento"])
            else:
                tabulator_formas.value = pd.DataFrame()
            if resultados["tipos_recebiveis"]:
                tabulator_recebiveis.value = pd.DataFrame(
                    resultados["tipos_recebiveis"]
                )
            else:
                tabulator_recebiveis.value = pd.DataFrame()
            if resultados["periodos"]:
                tabulator_periodos_mes.value = pd.DataFrame(resultados["periodos"])
            else:
                tabulator_periodos_mes.value = pd.DataFrame()

            # Carregar arquivos
            if resultados["arquivos"]:
                df_arquivos = pd.DataFrame(resultados["arquivos"])
                arquivos_tabulator.value = pd.DataFrame(
                    {
                        "#": range(1, len(df_arquivos) + 1),
                        "Arquivo": df_arquivos["nome_arquivo"],
                        "Registros": df_arquivos["total_registros"],
                        "Status": "Processado",
                    }
                )

            status_pane.object = f"✅ **Análise carregada:** {analise['nome_analise']} (ID: {analise_id})"
            _notify("success", f"Análise '{analise['nome_analise']}' carregada!")
        except Exception as e:
            _notify("error", f"Erro ao carregar análise: {e}")

    def carregar_processamento_existente():
        """Carrega arquivos já processados pelo importador usando agregações do banco (OTIMIZADO)"""
        pid = processamentoid_select.value
        print(f"\n[DEBUG] Iniciando carregamento do processamento: {pid}")

        if not pid or pid == "Nenhum":
            print(f"[DEBUG] Processamento inválido: {pid}")
            return _notify("warning", "Selecione um processamento válido.")

        status_pane.object = (
            "🔄 **Carregando processamento... (agregando no banco de dados)**"
        )
        btn_carregar_processamento.disabled = True

        try:
            # OTIMIZAÇÃO: Usar agregações diretas no banco em vez de carregar tudo para Pandas
            # Isso é MUITO mais rápido (segundos vs minutos)

            # 1. Obter total de registros (rápido)
            print(f"[DEBUG] Buscando total de registros para processamento {pid}...")
            total_registros = obter_total_registros_processamento(engine, pid)
            print(f"[DEBUG] Total de registros encontrados: {total_registros:,}")

            if total_registros == 0:
                print(f"[DEBUG] Nenhum registro encontrado para processamento {pid}")
                status_pane.object = (
                    f"⚠️ **Nenhum dado encontrado para o processamento {pid}.**"
                )
                return _notify(
                    "warning", f"Nenhum dado encontrado para o processamento {pid}."
                )

            # 2. Agregar dados diretamente no banco (muito mais rápido)
            print(f"[DEBUG] Agregando bandeiras...")
            bandeiras = agregar_bandeiras_db(engine, pid)
            print(f"[DEBUG] Bandeiras agregadas: {len(bandeiras)} registros")
            print(
                f"[DEBUG] Primeiras 2 bandeiras: {bandeiras[:2] if bandeiras else 'vazio'}"
            )

            print(f"[DEBUG] Agregando formas de pagamento...")
            formas = agregar_formas_pagamento_db(engine, pid)
            print(f"[DEBUG] Formas agregadas: {len(formas)} registros")
            print(f"[DEBUG] Primeiras 2 formas: {formas[:2] if formas else 'vazio'}")

            print(f"[DEBUG] Agregando períodos...")
            periodos = agregar_periodos_db(engine, pid)
            print(f"[DEBUG] Períodos agregados: {len(periodos)} registros")
            print(
                f"[DEBUG] Primeiros 2 períodos: {periodos[:2] if periodos else 'vazio'}"
            )

            print(f"[DEBUG] Agregando tipos de recebíveis...")
            recebiveis = agregar_recebiveis_db(engine, pid)
            print(f"[DEBUG] Recebíveis agregados: {len(recebiveis)} registros")
            print(
                f"[DEBUG] Primeiros 2 recebíveis: {recebiveis[:2] if recebiveis else 'vazio'}"
            )

            # Converter None para 0 nas agregações
            print(f"[DEBUG] Convertendo valores None para 0 nas bandeiras...")
            for b in bandeiras:
                for k in [
                    "quantidade",
                    "valor_total",
                    "valor_medio",
                    "valor_min",
                    "valor_max",
                    "taxa_perc_media",
                    "taxa_perc_min",
                    "taxa_perc_max",
                    "taxa_valor_total",
                    "taxa_valor_media",
                    "taxa_valor_min",
                    "taxa_valor_max",
                ]:
                    if k in b and b[k] is None:
                        b[k] = 0

            for f in formas:
                for k in [
                    "quantidade",
                    "valor_total",
                    "valor_medio",
                    "valor_min",
                    "valor_max",
                    "taxa_perc_media",
                    "taxa_perc_min",
                    "taxa_perc_max",
                    "taxa_valor_total",
                    "taxa_valor_media",
                    "taxa_valor_min",
                    "taxa_valor_max",
                ]:
                    if k in f and f[k] is None:
                        f[k] = 0

            for p in periodos:
                for k in [
                    "quantidade",
                    "valor_total",
                    "valor_medio",
                    "valor_min",
                    "valor_max",
                ]:
                    if k in p and p[k] is None:
                        p[k] = 0

            # Atualizar interface
            print(f"[DEBUG] Atualizando interface - criando DataFrame de arquivos...")
            arquivos_df = pd.DataFrame(
                {
                    "#": [1],
                    "Arquivo": [f"Processamento {pid}"],
                    "Registros": [total_registros],
                    "Status": ["Importado"],
                }
            )
            arquivos_tabulator.value = arquivos_df
            print(f"[DEBUG] Tabela de arquivos atualizada")

            # Atualizar tabs com resultados
            print(f"[DEBUG] Atualizando tab de bandeiras...")
            if bandeiras:
                df_bandeiras = pd.DataFrame(bandeiras)
                print(
                    f"[DEBUG] DataFrame bandeiras: {len(df_bandeiras)} linhas x {len(df_bandeiras.columns)} colunas"
                )
                print(f"[DEBUG] Colunas bandeiras: {list(df_bandeiras.columns)}")
                print(f"[DEBUG] Tipo df_bandeiras: {type(df_bandeiras)}")
                print(f"[DEBUG] Primeiras 2 linhas:\n{df_bandeiras.head(2)}")
                tabulator_bandeiras.value = df_bandeiras.reset_index(drop=True)
                print(f"[DEBUG] Tabulator bandeiras atualizado!")
            else:
                print(f"[DEBUG] Nenhuma bandeira")
                tabulator_bandeiras.value = pd.DataFrame()

            print(f"[DEBUG] Atualizando tab de formas...")
            if formas:
                df_formas = pd.DataFrame(formas)
                print(f"[DEBUG] DataFrame formas: {len(df_formas)} linhas")
                print(f"[DEBUG] Colunas formas: {list(df_formas.columns)}")
                tabulator_formas.value = df_formas.reset_index(drop=True)
                print(f"[DEBUG] Tabulator formas atualizado!")
            else:
                print(f"[DEBUG] Nenhuma forma")
                tabulator_formas.value = pd.DataFrame()

            # Tab de tipos de recebíveis
            print(f"[DEBUG] Atualizando tab de tipos de recebíveis...")
            if recebiveis:
                df_recebiveis = pd.DataFrame(recebiveis)
                print(f"[DEBUG] DataFrame recebíveis: {len(df_recebiveis)} linhas")
                tabulator_recebiveis.value = df_recebiveis.reset_index(drop=True)
            else:
                print(f"[DEBUG] Nenhum recebível")
                tabulator_recebiveis.value = pd.DataFrame()

            print(f"[DEBUG] Atualizando tabs de períodos...")
            if periodos:
                df_periodos = pd.DataFrame(periodos)
                print(f"[DEBUG] DataFrame períodos: {len(df_periodos)} linhas")

                # Separar por tipo de período
                df_mes = df_periodos[df_periodos["tipo_periodo"] == "mes"].copy()
                df_trimestre = df_periodos[
                    df_periodos["tipo_periodo"] == "trimestre"
                ].copy()
                df_semestre = df_periodos[
                    df_periodos["tipo_periodo"] == "semestre"
                ].copy()
                df_ano = df_periodos[df_periodos["tipo_periodo"] == "ano"].copy()

                print(f"[DEBUG] Períodos mensais filtrados: {len(df_mes)} linhas")
                print(
                    f"[DEBUG] Colunas períodos mensais: {list(df_mes.columns) if not df_mes.empty else 'vazio'}"
                )

                # Atualizar tabulators básicos
                if not df_mes.empty:
                    tabulator_periodos_mes.value = df_mes.reset_index(drop=True)
                    print(
                        f"[DEBUG] Tabulator períodos mensais atualizado com {len(df_mes)} linhas"
                    )
                else:
                    tabulator_periodos_mes.value = pd.DataFrame()

                if not df_trimestre.empty:
                    tabulator_periodos_trimestre.value = df_trimestre.reset_index(
                        drop=True
                    )
                    print(
                        f"[DEBUG] Tabulator períodos trimestrais atualizado com {len(df_trimestre)} linhas"
                    )
                else:
                    tabulator_periodos_trimestre.value = pd.DataFrame()

                if not df_semestre.empty:
                    tabulator_periodos_semestre.value = df_semestre.reset_index(
                        drop=True
                    )
                    print(
                        f"[DEBUG] Tabulator períodos semestrais atualizado com {len(df_semestre)} linhas"
                    )
                else:
                    tabulator_periodos_semestre.value = pd.DataFrame()

                if not df_ano.empty:
                    tabulator_periodos_ano.value = df_ano.reset_index(drop=True)
                    print(
                        f"[DEBUG] Tabulator períodos anuais atualizado com {len(df_ano)} linhas"
                    )
                else:
                    tabulator_periodos_ano.value = pd.DataFrame()
            else:
                print(f"[DEBUG] Nenhum período")
                tabulator_periodos_mes.value = pd.DataFrame()
                tabulator_periodos_trimestre.value = pd.DataFrame()
                tabulator_periodos_semestre.value = pd.DataFrame()
                tabulator_periodos_ano.value = pd.DataFrame()

            # Carregar agregações detalhadas por período
            print(f"[DEBUG] Carregando agregações por trimestre...")
            periodos_trimestral = agregar_trimestral_db(engine, pid)
            if periodos_trimestral:
                df_trim = pd.DataFrame(periodos_trimestral)
                print(f"[DEBUG] Trimestral: {len(df_trim)} linhas")
                print(f"[DEBUG] Colunas trimestral: {list(df_trim.columns)}")
                df_trim_reset = df_trim.reset_index(drop=True)
                print(
                    f"[DEBUG] Trimestral após reset: shape={df_trim_reset.shape}, columns={list(df_trim_reset.columns)}"
                )
                print(
                    f"[DEBUG] Primeiras 2 linhas trimestral:\n{df_trim_reset.head(2)}"
                )
                tabulator_trimestral.value = df_trim_reset
                print(f"[DEBUG] Tabulator trimestral atualizado!")
            else:
                tabulator_trimestral.value = pd.DataFrame()

            print(f"[DEBUG] Carregando agregações por semestre...")
            periodos_semestral = agregar_semestral_db(engine, pid)
            if periodos_semestral:
                df_sem = pd.DataFrame(periodos_semestral)
                print(f"[DEBUG] Semestral: {len(df_sem)} linhas")
                print(f"[DEBUG] Colunas semestral: {list(df_sem.columns)}")
                df_sem_reset = df_sem.reset_index(drop=True)
                print(
                    f"[DEBUG] Semestral após reset: shape={df_sem_reset.shape}, columns={list(df_sem_reset.columns)}"
                )
                print(f"[DEBUG] Primeiras 2 linhas semestral:\n{df_sem_reset.head(2)}")
                tabulator_semestral.value = df_sem_reset
                print(f"[DEBUG] Tabulator semestral atualizado!")
            else:
                tabulator_semestral.value = pd.DataFrame()

            print(f"[DEBUG] Carregando agregações por ano...")
            periodos_anual = agregar_anual_db(engine, pid)
            if periodos_anual:
                df_ano = pd.DataFrame(periodos_anual)
                print(f"[DEBUG] Anual: {len(df_ano)} linhas")
                print(f"[DEBUG] Colunas anual: {list(df_ano.columns)}")
                df_ano_reset = df_ano.reset_index(drop=True)
                print(
                    f"[DEBUG] Anual após reset: shape={df_ano_reset.shape}, columns={list(df_ano_reset.columns)}"
                )
                print(f"[DEBUG] Primeiras 2 linhas anual:\n{df_ano_reset.head(2)}")
                tabulator_anual.value = df_ano_reset
                print(f"[DEBUG] Tabulator anual atualizado!")
            else:
                tabulator_anual.value = pd.DataFrame()

            print(f"[DEBUG] Carregando formas de pagamento por ano...")
            formas_por_ano = agregar_formas_pagamento_por_ano_db(engine, pid)
            if formas_por_ano:
                df_formas_ano = pd.DataFrame(formas_por_ano)
                print(f"[DEBUG] Formas por ano: {len(df_formas_ano)} linhas")
                print(f"[DEBUG] Colunas formas por ano: {list(df_formas_ano.columns)}")
                tabulator_formas_por_ano.value = df_formas_ano.reset_index(drop=True)
                print(f"[DEBUG] Tabulator formas por ano atualizado!")
            else:
                tabulator_formas_por_ano.value = pd.DataFrame()

            # Carregar visão completa (todas as agregações combinadas)
            print(f"[DEBUG] Criando visão completa...")
            df_completo_list = []

            if periodos_trimestral:
                df_t = pd.DataFrame(periodos_trimestral)
                df_t["tipo_agregacao"] = "Trimestral"
                # Renomear coluna específica para "periodo"
                df_t = df_t.rename(columns={"trimestre": "periodo"})
                df_completo_list.append(df_t)

            if periodos_semestral:
                df_s = pd.DataFrame(periodos_semestral)
                df_s["tipo_agregacao"] = "Semestral"
                # Renomear coluna específica para "periodo"
                df_s = df_s.rename(columns={"semestre": "periodo"})
                df_completo_list.append(df_s)

            if periodos_anual:
                df_a = pd.DataFrame(periodos_anual)
                df_a["tipo_agregacao"] = "Anual"
                # Renomear coluna específica para "periodo"
                df_a = df_a.rename(columns={"ano": "periodo"})
                df_completo_list.append(df_a)

            if df_completo_list:
                df_completo = pd.concat(df_completo_list, ignore_index=True)
                # Reordenar colunas: tipo_agregacao, periodo, bandeira, forma_pagamento, valores...
                cols_order = [
                    "tipo_agregacao",
                    "periodo",
                    "bandeira",
                    "forma_pagamento",
                    "valor_total",
                    "quantidade",
                    "taxa_perc_minima",
                ]
                # Usar apenas colunas que existem
                cols = [c for c in cols_order if c in df_completo.columns]
                df_completo = df_completo[cols]
                print(f"[DEBUG] Visão completa: {len(df_completo)} linhas")
                print(f"[DEBUG] Colunas visão completa: {list(df_completo.columns)}")
                tabulator_completo.value = df_completo.reset_index(drop=True)
                print(f"[DEBUG] Tabulator completo atualizado!")
            else:
                tabulator_completo.value = pd.DataFrame()

            print(f"[DEBUG] Todos os tabulators atualizados!")

            # Contar períodos por tipo
            n_mes = (
                len([p for p in periodos if p.get("tipo_periodo") == "mes"])
                if periodos
                else 0
            )
            n_trim = len(periodos_trimestral) if periodos_trimestral else 0
            n_sem = len(periodos_semestral) if periodos_semestral else 0
            n_ano = len(periodos_anual) if periodos_anual else 0

            status_pane.object = f"""✅ **Processamento {pid} carregado!** 
            
📊 **Resumo:**
- Total de registros: {total_registros:,}
- Bandeiras: {len(bandeiras)}
- Formas de pagamento: {len(formas)}
- Tipos de recebíveis: {len(recebiveis)}
- Períodos: {n_mes} meses | {n_trim} trimestres | {n_sem} semestres | {n_ano} anos
"""
            _notify(
                "success",
                f"Processamento {pid} carregado! {total_registros:,} registros",
            )

        except Exception as e:
            print(f"[ERROR] Erro ao carregar processamento: {e}")
            import traceback

            traceback.print_exc()
            status_pane.object = f"❌ **Erro ao carregar processamento:** {e}"
            _notify("error", f"Erro ao carregar processamento: {e}")
        finally:
            btn_carregar_processamento.disabled = False

    btn_carregar_processamento.on_click(lambda e: carregar_processamento_existente())

    def processar_arquivos():
        """Processa os arquivos carregados"""
        if not analise_atual["id"]:
            return _notify("warning", "Crie ou carregue uma análise primeiro.")
        if not file_input.value:
            return _notify("warning", "Selecione um ou mais arquivos para processar.")
        files = (
            file_input.value
            if isinstance(file_input.value, list)
            else [file_input.value]
        )
        filenames = (
            file_input.filename
            if isinstance(file_input.filename, list)
            else [file_input.filename]
        )
        status_pane.object = "🔄 **Processando arquivos...**"
        btn_processar_arquivos.disabled = True
        try:
            total_registros = 0
            novos_arquivos = []

            for file_bytes, fname in zip(files, filenames):
                if file_bytes is None:
                    continue

                ext = os.path.splitext(fname)[-1] if fname else ".tmp"
                if ext.lower() not in [".xlsx", ".xls", ".csv"]:
                    ext = ".tmp"

                if isinstance(file_bytes, str):
                    try:
                        file_bytes = base64.b64decode(file_bytes)
                    except:
                        pass

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=ext, mode="wb"
                ) as tmp:
                    tmp.write(file_bytes)
                    path = tmp.name

                try:
                    # Ler arquivo
                    if is_multisheet_rede_file(path):
                        multisheet_data = safe_read_multisheet_file(
                            path, tipo_arquivo_select.value
                        )
                        df = pd.DataFrame()
                        for sheet_name, sheet_info in multisheet_data.items():
                            df_sheet = sheet_info["df"]
                            df = pd.concat([df, df_sheet], ignore_index=True)
                    else:
                        df, _, _ = safe_read_file(path)

                    if df.empty:
                        continue

                    # Processar com de-para se necessário
                    try:
                        df_mapeado, _, _ = preparar_dataframe_de_arquivo(
                            path=path,
                            engine=engine,
                            contexto=contexto_select.value,
                            tipo_origem=tipo_arquivo_select.value,
                        )
                    except:
                        df_mapeado = df

                    # Extrair dados
                    bandeiras = _extrair_bandeiras(df_mapeado)
                    formas = _extrair_formas_pagamento(df_mapeado)
                    tipos = _extrair_tipos_recebiveis(df_mapeado)
                    periodos = _extrair_periodos(df_mapeado)

                    # Adicionar à análise
                    arquivo_id = analise_adicionar_arquivo(
                        engine,
                        analise_atual["id"],
                        fname,
                        None,
                        tipo_arquivo_select.value,
                        contexto_select.value,
                        len(df_mapeado),
                    )

                    total_registros += len(df_mapeado)
                    novos_arquivos.append(
                        {
                            "arquivo": fname,
                            "registros": len(df_mapeado),
                            "bandeiras": bandeiras,
                            "formas": formas,
                            "tipos": tipos,
                            "periodos": periodos,
                        }
                    )

                finally:
                    if os.path.exists(path):
                        try:
                            os.unlink(path)
                        except:
                            pass

            # Carregar resultados existentes
            resultados_existentes = analise_obter_resultados(
                engine, analise_atual["id"]
            )

            # Consolidar resultados (incluindo existentes)
            todas_bandeiras = {}
            todas_formas = {}
            todos_tipos = {}
            todos_periodos = {}

            # Adicionar resultados existentes
            for b in resultados_existentes.get("bandeiras", []):
                nome = b["bandeira"]
                todas_bandeiras[nome] = {
                    "bandeira": nome,
                    "quantidade": b.get("quantidade", 0),
                    "valor_total": float(b.get("valor_total", 0.0)),
                }

            for f in resultados_existentes.get("formas_pagamento", []):
                nome = f["forma_pagamento"]
                todas_formas[nome] = {
                    "forma_pagamento": nome,
                    "quantidade": f.get("quantidade", 0),
                    "valor_total": float(f.get("valor_total", 0.0)),
                }

            for t in resultados_existentes.get("tipos_recebiveis", []):
                nome = t["tipo_recebivel"]
                todos_tipos[nome] = {
                    "tipo_recebivel": nome,
                    "quantidade": t.get("quantidade", 0),
                    "valor_total": float(t.get("valor_total", 0.0)),
                }

            for p in resultados_existentes.get("periodos", []):
                key = f"{p['tipo_periodo']}_{p['periodo']}"
                todos_periodos[key] = p.copy()

            # Adicionar novos resultados
            for arq in novos_arquivos:
                for b in arq["bandeiras"]:
                    nome = b["bandeira"]
                    if nome not in todas_bandeiras:
                        todas_bandeiras[nome] = {
                            "bandeira": nome,
                            "quantidade": 0,
                            "valor_total": 0.0,
                        }
                    todas_bandeiras[nome]["quantidade"] += b.get("quantidade", 0)
                    todas_bandeiras[nome]["valor_total"] += b.get("valor_total", 0.0)

                for f in arq["formas"]:
                    nome = f["forma_pagamento"]
                    if nome not in todas_formas:
                        todas_formas[nome] = {
                            "forma_pagamento": nome,
                            "quantidade": 0,
                            "valor_total": 0.0,
                        }
                    todas_formas[nome]["quantidade"] += f.get("quantidade", 0)
                    todas_formas[nome]["valor_total"] += f.get("valor_total", 0.0)

                for t in arq["tipos"]:
                    nome = t["tipo_recebivel"]
                    if nome not in todos_tipos:
                        todos_tipos[nome] = {
                            "tipo_recebivel": nome,
                            "quantidade": 0,
                            "valor_total": 0.0,
                        }
                    todos_tipos[nome]["quantidade"] += t.get("quantidade", 0)
                    todos_tipos[nome]["valor_total"] += t.get("valor_total", 0.0)

                for p in arq["periodos"]:
                    key = f"{p['tipo_periodo']}_{p['periodo']}"
                    if key not in todos_periodos:
                        todos_periodos[key] = p.copy()
                    else:
                        todos_periodos[key]["quantidade"] += p.get("quantidade", 0)
                        todos_periodos[key]["valor_total"] += p.get("valor_total", 0.0)

            # Salvar no banco
            analise_salvar_bandeiras(
                engine, analise_atual["id"], list(todas_bandeiras.values())
            )
            analise_salvar_formas_pagamento(
                engine, analise_atual["id"], list(todas_formas.values())
            )
            analise_salvar_tipos_recebiveis(
                engine, analise_atual["id"], list(todos_tipos.values())
            )
            analise_salvar_periodos(
                engine, analise_atual["id"], list(todos_periodos.values())
            )

            # Atualizar análise
            analise_atualizar(
                engine,
                analise_atual["id"],
                total_arquivos=len(novos_arquivos),
                total_registros=total_registros,
            )

            # Atualizar interface
            if todas_bandeiras:
                tabulator_bandeiras.value = pd.DataFrame(list(todas_bandeiras.values()))
            if todas_formas:
                tabulator_formas.value = pd.DataFrame(list(todas_formas.values()))
            if todos_tipos:
                tabulator_recebiveis.value = pd.DataFrame(list(todos_tipos.values()))
            if todos_periodos:
                tabulator_periodos_mes.value = pd.DataFrame(
                    list(todos_periodos.values())
                )

            # Atualizar lista de arquivos
            arquivos_df = pd.DataFrame(
                {
                    "#": range(1, len(novos_arquivos) + 1),
                    "Arquivo": [a["arquivo"] for a in novos_arquivos],
                    "Registros": [a["registros"] for a in novos_arquivos],
                    "Status": "Processado",
                }
            )
            if not arquivos_tabulator.value.empty:
                arquivos_df = pd.concat(
                    [arquivos_tabulator.value, arquivos_df], ignore_index=True
                )
                arquivos_df["#"] = range(1, len(arquivos_df) + 1)
            arquivos_tabulator.value = arquivos_df

            status_pane.object = f"✅ **{len(novos_arquivos)} arquivo(s) processado(s)!** Total: {total_registros:,} registros"
            _notify(
                "success",
                f"{len(novos_arquivos)} arquivo(s) processado(s) com sucesso!",
            )

        except Exception as e:
            status_pane.object = f"❌ **Erro ao processar:** {e}"
            _notify("error", f"Erro ao processar arquivos: {e}")
        finally:
            btn_processar_arquivos.disabled = False

    def salvar_analise():
        """Salva a análise atual"""
        if not analise_atual["id"]:
            return _notify("warning", "Nenhuma análise ativa.")

        try:
            analise_atualizar(
                engine,
                analise_atual["id"],
                nome_analise=(
                    nome_analise_input.value.strip()
                    if nome_analise_input.value
                    else None
                ),
                descricao=(
                    descricao_input.value.strip() if descricao_input.value else None
                ),
            )
            _notify("success", "Análise salva com sucesso!")
            atualizar_lista_analises()
        except Exception as e:
            _notify("error", f"Erro ao salvar análise: {e}")

    def finalizar_analise():
        """Finaliza a análise"""
        if not analise_atual["id"]:
            return _notify("warning", "Nenhuma análise ativa.")

        try:
            analise_atualizar(engine, analise_atual["id"], status="finalizada")
            btn_processar_arquivos.disabled = True
            status_pane.object = f"✅ **Análise finalizada:** {analise_atual['nome']}"
            _notify("success", "Análise finalizada com sucesso!")
            atualizar_lista_analises()
        except Exception as e:
            _notify("error", f"Erro ao finalizar análise: {e}")

    # Eventos
    btn_processar_arquivos.on_click(lambda e: processar_arquivos())
    btn_carregar_processamento.on_click(lambda e: carregar_processamento_existente())
    btn_carregar_analise.on_click(lambda e: carregar_analise())

    # Carregar lista inicial (com try/except para evitar erro se não houver análises)
    try:
        atualizar_lista_analises()
    except Exception as e:
        print(f"Aviso: Não foi possível carregar lista de análises: {e}")

    return pn.Column(
        pn.pane.Markdown("## 📊 Analista de Arquivos"),
        pn.Card(
            pn.Column(
                pn.pane.Markdown("### 💾 Análises Salvas"),
                pn.Row(
                    analises_select,
                    btn_carregar_analise,
                    sizing_mode="stretch_width",
                ),
                pn.layout.Divider(),
                pn.pane.Markdown("### 📁 Upload de Arquivos"),
                pn.Row(file_input, btn_processar_arquivos, sizing_mode="stretch_width"),
                pn.pane.Markdown("### 📦 Ou carregar processamento já importado"),
                pn.Row(
                    processamentoid_select,
                    btn_carregar_processamento,
                    sizing_mode="stretch_width",
                ),
                pn.pane.Markdown("### 📋 Arquivos Processados"),
                arquivos_tabulator,
            ),
            title="Processar Arquivos",
            sizing_mode="stretch_width",
        ),
        status_pane,
        pn.pane.Markdown("### 📈 Resultados da Análise"),
        pn.pane.Markdown("#### Agregações Básicas"),
        pn.Card(
            tabulator_bandeiras,
            title="Bandeiras",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_formas,
            title="Formas de Pagamento",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_formas_por_ano,
            title="Formas de Pagamento por Ano",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_recebiveis,
            title="Tipos de Recebíveis",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_periodos_mes,
            title="Períodos Mensais",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_periodos_trimestre,
            title="Períodos Trimestrais",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_periodos_semestre,
            title="Períodos Semestrais",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_periodos_ano,
            title="Períodos Anuais",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.pane.Markdown("#### Análises por Período (Bandeira + Forma de Pagamento)"),
        pn.Card(
            tabulator_anual,
            title="📅 Análise Anual",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_semestral,
            title="📆 Análise Semestral",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        pn.Card(
            tabulator_trimestral,
            title="📊 Análise Trimestral",
            collapsed=False,
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
    )
