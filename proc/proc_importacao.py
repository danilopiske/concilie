from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Protocol, Optional
import pandas as pd
import numpy as np
import unicodedata
import re
import os
from datetime import datetime
from pathlib import Path
from sqlalchemy.engine import Engine
from proc.importers.factory import ImporterFactory
from proc.importers.utils import log_to_debug_file

from conf.funcoesbd import (
    depara_carregar_mapa_completo,
    processamento_gerar_novo_id,
    processamento_salvar,
    bandeiras_por_ec,
    termos_listar,
    vendas_processadas_bulk_insert,
    vendas_filtradas_bulk_insert,
    vendas_diversas_bulk_insert,
    vendas_remover_duplicadas,
    recebiveis_processados_bulk_insert,
    recebiveis_filtrados_bulk_insert,
    recebiveis_remover_duplicadas,
)
from conf.debug_utils import PerformanceTimer


# Função para processar, filtrar e gravar recebíveis
def classificar_e_gravar_recebiveis(
    engine: Engine,
    df: pd.DataFrame,
    *,
    cliente_id: int,
    ec_id: str,
    contexto: str,
    usuario: str,
    arquivo_origem: str = "",
    processamentoid: int | str = None,
    progress_callback = None
) -> dict:
    """
    Processa, filtra e grava recebíveis nas tabelas corretas, com metadados e deduplicação.
    """
    with PerformanceTimer("RECORD", "Gravação Recebíveis (Bulk Insert)", {"rows": len(df), "contexto": contexto}):
        # Termo filtrável removido - deve ser configurado manualmente se necessário
    
        was_fresh = processamentoid is None
    
        if not df.empty:
    
            # Deduplicação preventiva em memória (Python) antes de gravar
            # Identificar colunas base para unicidade (todas exceto metadados de processamento)
            cols_ignorar = {"id", "data_processamento", "usuario_processamento", "arquivo_origem", "processamentoid"}
            cols_dedup = [c for c in df.columns if c not in cols_ignorar]
            
            if cols_dedup:
                len_antes = len(df)
                df = df.drop_duplicates(subset=cols_dedup).copy()
                len_depois = len(df)
                if len_antes > len_depois:
                    print(f"[DEBUG][DEDUP] Removidas {len_antes - len_depois} duplicadas em memória antes da gravação.")
    
            # Se já tem coluna 'Filtrado', refaz a filtragem com os termos atuais do banco
            if "Filtrado" in df.columns:
                # Refaz a filtragem: sobrescreve a coluna 'Filtrado' com base nos termos atuais
                # Detecta coluna de lançamento (PRIORIZA 'lancamento' sobre 'descricao')
                lancamento_col = None
    
                # Primeira passada: buscar especificamente por 'lancamento'
                for c in df.columns:
                    if str(c).strip().lower() in [
                        "lancamento",
                        "lançamento",
                        "tipo de lancamento",
                        "tipo de lançamento",
                    ]:
                        lancamento_col = c
                        break
    
                # Segunda passada: se não encontrou 'lancamento', buscar por 'descricao'
                if not lancamento_col:
                    for c in df.columns:
                        if str(c).strip().lower() in ["descricao", "descrição"]:
                            lancamento_col = c
                            break
    
                if not lancamento_col:
                    lancamento_col = df.columns[0] if len(df.columns) > 0 else None
    
                def norm(s):
                    import unicodedata
    
                    return (
                        unicodedata.normalize("NFKD", str(s or ""))
                        .encode("ASCII", "ignore")
                        .decode("ASCII")
                        .upper()
                        .strip()
                    )
    
                termos_raw = termos_listar(engine, str(ec_id), contexto, tipo="r")
                termos = [
                    norm(t["termo"]) if isinstance(t, dict) and "termo" in t else norm(t)
                    for t in termos_raw
                ]
    
                if termos:
                    padrao_termos = re.compile(
                        "|".join(map(re.escape, termos)), flags=re.IGNORECASE
                    )
                else:
                    padrao_termos = None
    
                mask_vazio = df[lancamento_col].isnull() | (
                    df[lancamento_col].astype(str).str.strip() == ""
                )
    
                if padrao_termos:
                    def check_match(x):
                        x_norm = norm(x)
                        match = padrao_termos.search(x_norm)
                        return bool(match)
    
                    mask_termo = df[lancamento_col].astype(str).apply(check_match)
                else:
                    mask_termo = pd.Series([False] * len(df), index=df.index)
    
                # Linhas processadas: não vazias e não termo filtrável
                mask_proc = (~mask_vazio) & (~mask_termo)
                # Linhas filtradas: termo filtrável
                mask_filt = (~mask_vazio) & mask_termo
    
                df.loc[mask_proc, "Filtrado"] = 0
                df.loc[mask_filt, "Filtrado"] = 1
    
        now = datetime.now()
    
        if processamentoid is None:
            # Gera novo processamentoid
            from conf.funcoesbd import processamento_gerar_novo_id, processamento_salvar
    
            processamentoid, data_proc = processamento_gerar_novo_id(engine, ec_id, now)
            processamento_salvar(
                engine,
                ec_id=ec_id,
                cliente_id=cliente_id,
                id_processamento=processamentoid,
                descricao=arquivo_origem or "Importação Recebíveis",
                data_processamento=data_proc,
            )
    
        # Normaliza e filtra
        df = normalizar_dataframe_recebiveis(
            df, engine, ec_id, contexto, usuario
        )
    
        # NOTA: As datas já foram convertidas corretamente em normalizar_dataframe_recebiveis
        # com dayfirst=True, então não precisamos converter novamente aqui
    
        # Adiciona metadados ao DataFrame completo
        df["arquivo_origem"] = arquivo_origem or ""
        df["processamentoid"] = processamentoid
        df["cliente_id"] = cliente_id
    
        # ⚠️ CRÍTICO: Apenas preencher ec_id se não veio do de-para (coluna vazia/ausente)
        # Se ec_id já existe no DataFrame (via de-para), NÃO sobrescrever!
        if "ec_id" not in df.columns or df["ec_id"].isna().all():
            df["ec_id"] = ec_id
    
        # As datas já estão convertidas corretamente em normalizar_dataframe_recebiveis
    
        # Separa entre processados e filtrados baseado na coluna 'Filtrado'
        if "Filtrado" in df.columns:
            df_proc = df[df["Filtrado"] == 0].copy()
            df_filt = df[df["Filtrado"] == 1].copy()
        else:
            # Se não tem coluna Filtrado, todos vão para processados
            df_proc = df.copy()
            df_filt = pd.DataFrame(columns=df.columns)
    
        # Remove colunas auxiliares (igual às vendas)
        columns_to_remove = ["Filtrado", "planilha_origem"]
        df_proc_db = df_proc.drop(columns=columns_to_remove, errors="ignore")
        df_filt_db = df_filt.drop(columns=columns_to_remove, errors="ignore")
    
        # ✅ CORREÇÃO: Converter valores monetários para float ANTES do insert
        for col in ["valor_recebivel", "valor_liquido"]:
            if col in df_proc_db.columns:
                # ⚠️ CRÍTICO: Converter E arredondar para 2 casas decimais
                df_proc_db[col] = pd.to_numeric(df_proc_db[col], errors="coerce").round(2)
    
            if col in df_filt_db.columns:
                # ⚠️ CRÍTICO: Converter E arredondar para 2 casas decimais
                df_filt_db[col] = pd.to_numeric(df_filt_db[col], errors="coerce").round(2)
    
        n_proc, n_filt = len(df_proc_db), len(df_filt_db)
    
        # Inserir dados nas respectivas tabelas (igual às vendas)
        if n_proc:
            if progress_callback: progress_callback(70, "Gravando recebíveis processados...")
            recebiveis_processados_bulk_insert(engine, df_proc_db, progress_callback=progress_callback)
        if n_filt:
            if progress_callback: progress_callback(85, "Gravando recebíveis filtrados...")
            recebiveis_filtrados_bulk_insert(engine, df_filt_db, progress_callback=progress_callback)
    
        # Remover duplicadas (igual às vendas)
        # OTIMIZAÇÃO: Se for uma importação nova (was_fresh=True), a deduplicação em memória feita acima
        # já é suficiente e muito mais rápida que o self-join no banco de dados.
        if n_proc and not was_fresh:
            if progress_callback: progress_callback(90, "Removendo duplicadas (processados)...")
            recebiveis_remover_duplicadas(
                engine,
                "recebiveis_processados",
                processamentoid,
                df_proc_db.columns.tolist(),
            )
        elif n_proc and was_fresh:
            print(f"[DEBUG][DEDUP] Pulando remoção SQL de duplicadas para fresh import (processamentoid: {processamentoid})")
            if progress_callback: progress_callback(95, "Deduplicação em memória concluída.")
    
        if n_filt and not was_fresh:
            recebiveis_remover_duplicadas(
                engine, "recebiveis_filtrados", processamentoid, df_filt_db.columns.tolist()
            )
    
        return {
            "processadas": len(df_proc_db),
            "filtradas": len(df_filt_db),
            "total": len(df_proc_db) + len(df_filt_db),
            "processamentoid": processamentoid,
        }


def normalizar_dataframe_recebiveis(
    df: pd.DataFrame,
    engine: Engine,
    ec_id: str,
    contexto: str = "padrao",
    usuario: str = "desconhecido",
    debug_skip_filter: bool = False,  # Parâmetro para pular filtragem temporariamente
) -> pd.DataFrame:
    """
    Normaliza DataFrame de recebíveis (sem separar filtrados/processados):
    - Apenas normaliza dados e adiciona metadados
    - Aplica filtragem e adiciona coluna 'Filtrado'
    - Separação será feita posteriormente na função classificar_e_gravar_recebiveis
    """
    with PerformanceTimer("POLARS", "Normalização Recebíveis (Pandas Pipeline)", {"rows": len(df), "contexto": contexto}):
        df = df.copy()

        # Conversão explícita APENAS de colunas de data (não valor_recebivel, recebivel_id, etc.)
        # Lista explícita para evitar conversão incorreta de colunas numéricas/texto
        colunas_data_candidatas = [
            "data_pagamento",
            "data_recebivel",
            "data_processamento",
            "data_ajuste",
            "data_lancamento",
            "data_vencimento",
            "data_da_venda",
            "data_da_autorização_da_venda",
        ]
        colunas_data = [c for c in colunas_data_candidatas if c in df.columns]

        for col in colunas_data:
            # ⚠️ CORREÇÃO CRÍTICA: Detectar formato ISO 8601 (YYYY-MM-DD) vs brasileiro (DD/MM/YYYY)
            # - Se string contém '-' → formato ISO (não usar dayfirst)
            # - Se string contém '/' → formato brasileiro (usar dayfirst=True)
            sample_value = (
                str(df[col].dropna().iloc[0]) if len(df[col].dropna()) > 0 else ""
            )
            use_dayfirst = "/" in sample_value  # Apenas para formato DD/MM/YYYY
            
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=use_dayfirst)

        # Conversão explícita de colunas numéricas/monetárias
        colunas_numericas_candidatas = [
            "valor_recebivel",
            "valor_liquido",
            "valor_bruto",
            "valor_taxa",
            "valor_comissao",
            "valor_desconto",
        ]
        colunas_numericas = [c for c in colunas_numericas_candidatas if c in df.columns]

        for col in colunas_numericas:
            # ⚠️ CRÍTICO: Converter para numeric E arredondar para 2 casas decimais
            # Evita imprecisão de ponto flutuante (0.30 → 0.3097)
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

        # Adiciona metadados básicos
        df["data_processamento"] = datetime.now()
        df["usuario_processamento"] = usuario or "desconhecido"

        # --- NOVO: Preencher coluna 'Adquirente' baseada no contexto selecionado (igual às vendas) ---
        if contexto and contexto.lower() not in ["", "padrao"]:
            adquirente_valor = contexto.upper()
            if "Adquirente" not in df.columns:
                df["Adquirente"] = adquirente_valor
            else:
                # Preencher apenas onde está vazio/nulo
                mask_vazio = df["Adquirente"].isnull() | (
                    df["Adquirente"].astype(str).str.strip() == ""
                )
                df.loc[mask_vazio, "Adquirente"] = adquirente_valor

        # APLICAR FILTRAGEM BASEADA EM TERMOS
        # Identificar coluna de lançamento/descrição (prioridade para 'lancamento')
        lancamento_col = None

        # Primeira passada: buscar por 'lancamento'
        for c in df.columns:
            if str(c).strip().lower() in [
                "lancamento",
                "lançamento",
                "tipo de lancamento",
                "tipo de lançamento",
            ]:
                lancamento_col = c
                break

        # Segunda passada: se não encontrou 'lancamento', buscar por 'descricao'
        if not lancamento_col:
            for c in df.columns:
                if str(c).strip().lower() in ["descricao", "descrição"]:
                    lancamento_col = c
                    break

        if not lancamento_col:
            lancamento_col = df.columns[0] if len(df.columns) > 0 else None

        if not lancamento_col:
            df["Filtrado"] = 0
            return df

        # Função de normalização de texto
        def norm(s):
            return (
                unicodedata.normalize("NFKD", str(s or ""))
                .encode("ASCII", "ignore")
                .decode("ASCII")
                .upper()
                .strip()
            )

        # Carregar termos de filtro
        termos_raw = termos_listar(engine, str(ec_id), contexto, tipo="r")

        termos = [
            norm(t["termo"]) if isinstance(t, dict) and "termo" in t else norm(t)
            for t in termos_raw
        ]

        # 🔥 INICIALIZAR coluna Filtrado SEMPRE
        df["Filtrado"] = 0  # Default: não filtrado

        # 🔥 VALIDAÇÃO ESPECIAL CIELO: lançamento não pode estar vazio
        # IMPORTANTE: Após o De-Para, "motivo_ajuste" foi renomeado para "lancamento"
        # Esta validação acontece ANTES da filtragem por termos
        if contexto and contexto.upper() == "CIELO":
            # Procurar coluna lancamento (que é o destino do De-Para de motivo_ajuste)
            lancamento_col_validacao = None
            for col in df.columns:
                col_lower = col.lower()
                # Procurar por "lancamento" que é como motivo_ajuste foi renomeado
                if col_lower == "lancamento":
                    lancamento_col_validacao = col
                    break

            if lancamento_col_validacao:
                # Identificar linhas com lancamento vazio/nulo
                mask_vazio = (
                    df[lancamento_col_validacao].isnull()
                    | (df[lancamento_col_validacao].astype(str).str.strip() == "")
                    | (df[lancamento_col_validacao].astype(str).str.lower() == "nan")
                    | (df[lancamento_col_validacao].astype(str).str.lower() == "none")
                )

                linhas_vazias = mask_vazio.sum()

                if linhas_vazias > 0:
                    # Marcar como filtrado
                    df.loc[mask_vazio, "Filtrado"] = 1

        # Aplicar filtragem por TERMOS (adiciona mais filtros aos já existentes)
        if termos and lancamento_col in df.columns:
            # Criar padrão regex
            padrao_termos = re.compile(
                "|".join(map(re.escape, termos)), flags=re.IGNORECASE
            )

            # Aplicar filtro
            for idx, row in df.iterrows():
                valor_celula = str(row.get(lancamento_col, "")).strip()
                valor_normalizado = norm(valor_celula)

                match = padrao_termos.search(valor_normalizado)
                if match:
                    df.loc[idx, "Filtrado"] = 1

        return df


# proc/proc_importacao.py


# ---------- Utilidades básicas ----------
def preparar_para_tabulator(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara DataFrame para exibição no Tabulator (Panel).
    - Converte datas para string
    - Converte NaN/NaT para None
    - Mantém tipos originais para números e strings
    """

    if df is None or df.empty:
        # Retorna DataFrame vazio com as colunas originais, se possível
        if df is not None and hasattr(df, "columns"):
            return pd.DataFrame(columns=df.columns)
        return pd.DataFrame([{"Sem dados": "Nenhum registro encontrado"}])

    out = df.copy(deep=True)

    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = pd.to_datetime(out[col], errors="coerce").dt.strftime("%Y-%m-%d")
        elif pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].astype(object)
        # do not force string for all columns

    # Replace NaN/NaT with None for all columns
    out = out.where(pd.notnull(out), None)

    return out


def safe_read_multisheet_file(
    path: str,
    tipo_origem: str = "V",
    engine=None,
    contexto: str = "Rede",
    nrows: Optional[int] = None,
) -> dict:
    """
    Lê um arquivo Excel multi-planilhas para recebiveis da REDE:
    1) Ignora planilha "capa"
    2) Filtra apenas abas que têm configuração no depara
    3) Retorna dict com {nome_planilha: {df, headers, sheet_index}}
    4) Para mapeamento usa formato [nomedaplanilha]_[col_cabecalho]
    """
    ext = Path(path).suffix.lower()
    print(
        f"[DEBUG][MULTISHEET] Lendo arquivo multi-planilhas: {path} (extensão: {ext})"
    )

    if ext not in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
        raise ValueError(f"Arquivo {path} não é Excel válido para multi-planilhas")

    try:
        # Primeiro, listar todas as planilhas
        excel_file = pd.ExcelFile(path, engine="calamine")

        # Carregar configurações de depara para verificar quais abas são suportadas
        if engine and tipo_origem == "R":
            from conf.depara_utils import gerar_mapeamento_depara
            from conf.funcoesbd import depara_carregar_mapa_completo

            # Carregar apenas regras ativas do depara
            regras_depara_ativas = depara_carregar_mapa_completo(
                engine, contexto=contexto, tipo_origem=tipo_origem
            )

            # Filtrar apenas regras onde origem_nome não é None/vazio (regras reais de importação)
            regras_validas = [
                r
                for r in regras_depara_ativas
                if r.get("origem_nome") and str(r.get("origem_nome", "")).strip()
            ]

            # Extrair prefixos de abas que têm configuração ativa no depara
            abas_configuradas = set()
            for regra in regras_validas:
                col_origem = regra.get("origem_nome", "")
                # Extrair prefixo da aba (parte antes do primeiro _)
                if "_" in col_origem:
                    prefixo_aba = col_origem.split("_")[0]
                    abas_configuradas.add(prefixo_aba.lower())

            print(
                f"[DEBUG][MULTISHEET] Regras ativas encontradas: {len(regras_validas)}"
            )
            print(
                f"[DEBUG][MULTISHEET] Abas configuradas no depara: {sorted(abas_configuradas)}"
            )
        else:
            abas_configuradas = None

        # Para recebíveis, filtrar apenas abas que têm configuração no depara
        all_sheets = excel_file.sheet_names
        sheet_names = []

        print(f"[DEBUG][MULTISHEET] 📋 TODAS AS ABAS ENCONTRADAS: {all_sheets}")

        for name in all_sheets:
            name_lower = name.lower().strip()
            print(
                f"[DEBUG][MULTISHEET] 🔍 Processando aba: '{name}' (lower: '{name_lower}')"
            )

            # Excluir capa
            if name_lower == "capa":
                print(f"[DEBUG][MULTISHEET] ❌ Excluindo aba capa: {name}")
                continue

            # Para recebíveis, verificar se a aba tem configuração no depara
            if tipo_origem == "R" and abas_configuradas is not None:
                print(
                    f"[DEBUG][MULTISHEET] 📊 Verificando configuração para aba '{name}'..."
                )

                # Se não há abas configuradas, não processar nenhuma
                if not abas_configuradas:
                    print(
                        f"[DEBUG][MULTISHEET] ❌ Excluindo aba '{name}' - nenhuma configuração ativa encontrada no depara"
                    )
                    continue

                # Verificar se esta aba tem configuração
                nome_aba_clean = (
                    name_lower.replace(" ", "_").replace("e_", "e ").strip()
                )
                aba_tem_config = False

                print(
                    f"[DEBUG][MULTISHEET] 🔍 Testando '{name}' (clean: '{nome_aba_clean}') contra abas configuradas: {abas_configuradas}"
                )

                # Tentar várias formas de matching
                for aba_config in abas_configuradas:
                    print(f"[DEBUG][MULTISHEET] 🔄 Testando matching:")
                    print(f"[DEBUG][MULTISHEET]   - aba_config: '{aba_config}'")
                    print(f"[DEBUG][MULTISHEET]   - nome_aba_clean: '{nome_aba_clean}'")
                    print(f"[DEBUG][MULTISHEET]   - name_lower: '{name_lower}'")

                    condicao1 = aba_config in nome_aba_clean
                    condicao2 = nome_aba_clean in aba_config
                    condicao3 = aba_config.replace("_", " ") in name_lower
                    condicao4 = nome_aba_clean.replace("_", " ") == aba_config.replace(
                        "_", " "
                    )

                    print(
                        f"[DEBUG][MULTISHEET]   - Test1 ('{aba_config}' in '{nome_aba_clean}'): {condicao1}"
                    )
                    print(
                        f"[DEBUG][MULTISHEET]   - Test2 ('{nome_aba_clean}' in '{aba_config}'): {condicao2}"
                    )
                    print(
                        f"[DEBUG][MULTISHEET]   - Test3 ('{aba_config.replace('_', ' ')}' in '{name_lower}'): {condicao3}"
                    )
                    print(
                        f"[DEBUG][MULTISHEET]   - Test4 ('{nome_aba_clean.replace('_', ' ')}' == '{aba_config.replace('_', ' ')}'): {condicao4}"
                    )

                    if condicao1 or condicao2 or condicao3 or condicao4:
                        aba_tem_config = True
                        print(
                            f"[DEBUG][MULTISHEET] ✅ MATCH! Aba '{name}' corresponde ao depara '{aba_config}'"
                        )
                        break
                    else:
                        print(f"[DEBUG][MULTISHEET] ❌ Sem match com '{aba_config}'")

                if not aba_tem_config:
                    print(
                        f"[DEBUG][MULTISHEET] Excluindo aba sem configuração no depara: {name}"
                    )
                    print(
                        f"[DEBUG][MULTISHEET] Abas configuradas disponíveis: {sorted(abas_configuradas)}"
                    )
                    continue

            # Incluir aba aprovada
            sheet_names.append(name)

        print(f"[DEBUG][MULTISHEET] Planilhas selecionadas: {sheet_names}")
        print(
            f"[DEBUG][MULTISHEET] Planilhas excluídas: {[s for s in all_sheets if s not in sheet_names]}"
        )

        resultado = {}

        for sheet_name in sheet_names:
            print(f"[DEBUG][MULTISHEET] Processando planilha: {sheet_name}")
            try:
                # Ler planilha como DataFrame
                # ⚠️ CRÍTICO: keep_default_na=False para evitar conversão automática de datas
                df = pd.read_excel(
                    path,
                    sheet_name=sheet_name,
                    header=None,
                    dtype=str,
                    keep_default_na=False,
                    na_filter=False,
                    engine="calamine",
                    nrows=nrows,
                )

                # Encontrar cabeçalho usando lógica mais robusta
                header_row_idx = 0
                headers = []

                print(
                    f"[DEBUG][MULTISHEET] {sheet_name} - Analisando primeiras 10 linhas para cabeçalho..."
                )

                def is_likely_header_row(row):
                    """Verifica se uma linha parece ser cabeçalho"""
                    non_empty_cells = [
                        str(x).strip()
                        for x in row
                        if str(x).strip()
                        and str(x).strip().lower() not in ["nan", "none"]
                    ]

                    if len(non_empty_cells) < 2:  # Muito poucas colunas preenchidas
                        return False, 0

                    row_text = " ".join(str(x).lower() for x in non_empty_cells)

                    # Descartar linhas que contêm texto de cabeçalho de relatório
                    report_header_texts = [
                        "extrato para simples conferência",
                        "período:",
                        "data de emissão:",
                        "observação:",
                        "este documento pode sofrer alterações",
                    ]

                    for report_text in report_header_texts:
                        if report_text in row_text:
                            return False, -10  # Score negativo para forçar exclusão

                    score = 0

                    # Palavras que indicam cabeçalhos
                    header_keywords = [
                        "data",
                        "valor",
                        "cpf",
                        "cnpj",
                        "banco",
                        "agencia",
                        "conta",
                        "nome",
                        "cliente",
                        "codigo",
                        "id",
                        "numero",
                        "documento",
                        "lancamento",
                        "recebivel",
                        "venda",
                        "pagamento",
                        "transacao",
                        "bandeira",
                        "cartao",
                        "taxa",
                        "desconto",
                        "liquido",
                        "bruto",
                        "status",
                        "situacao",
                        "tipo",
                        "modalidade",
                        "parcela",
                        "cobranca",
                        "cobrado",
                        "aluguel",
                        "maquininha",
                    ]

                    # Pontuação por palavras-chave encontradas
                    for keyword in header_keywords:
                        if keyword in row_text:
                            score += 2

                    # Bonus se tem muitas colunas preenchidas
                    if len(non_empty_cells) >= 5:
                        score += 3
                    elif len(non_empty_cells) >= 3:
                        score += 1

                    # Para arquivos da REDE, ser mais preciso na detecção
                    # Evitar falsos positivos com dados reais
                    if len(non_empty_cells) >= 3:
                        # Verificar se contém dados reais (datas/valores ISO) que indicam NÃO ser cabeçalho
                        data_indicators = 0
                        numeric_count = 0  # Inicializar numeric_count
                        for cell in non_empty_cells[:5]:
                            cell_str = str(cell).strip()

                            # Data formato ISO (yyyy-mm-dd hh:mm:ss) - claramente dados
                            if len(cell_str) >= 10 and cell_str.count("-") == 2:
                                parts = cell_str.split()
                                if len(parts) >= 1:
                                    date_part = parts[0]
                                    if date_part.count("-") == 2:
                                        try:
                                            # Tentar parsear como data ISO
                                            year, month, day = date_part.split("-")
                                            if (
                                                len(year) == 4
                                                and len(month) == 2
                                                and len(day) == 2
                                            ):
                                                if (
                                                    1900 <= int(year) <= 2100
                                                    and 1 <= int(month) <= 12
                                                    and 1 <= int(day) <= 31
                                                ):
                                                    data_indicators += 1
                                                    score -= 5  # Forte indicador que NÃO é cabeçalho
                                        except:
                                            pass

                            # Valores monetários com decimais (provavelmente dados)
                            elif (
                                "." in cell_str
                                and cell_str.replace(".", "").replace(",", "").isdigit()
                            ):
                                data_indicators += 1
                                score -= 2

                            # Se é só números (provavelmente dados, não cabeçalho)
                            elif (
                                cell_str.replace(",", "")
                                .replace(".", "")
                                .replace("R$", "")
                                .strip()
                                .isdigit()
                            ):
                                numeric_count += 1

                        # Se tem muitos indicadores de dados reais, NÃO é cabeçalho
                        if data_indicators >= 2:
                            return False, score

                        # Se menos da metade são números, pode ser cabeçalho
                        if numeric_count < len(non_empty_cells) / 2:
                            score += 1

                    # Reduzir threshold para arquivos da REDE, mas manter precisão
                    # Só considerar cabeçalho se tem score positivo E não tem dados reais
                    return score >= 2 and data_indicators < 2, score

                best_header_idx = 0
                best_score = 0

                for idx in range(min(10, len(df))):
                    row = df.iloc[idx]
                    try:
                        is_header, score = is_likely_header_row(row)

                        print(
                            f"[DEBUG][MULTISHEET] Linha {idx}: score={score}, é_cabeçalho={is_header}"
                        )
                        print(f"[DEBUG][MULTISHEET] Conteúdo: {list(row[:5])}...")

                        if is_header and score > best_score:
                            best_header_idx = idx
                            best_score = score
                    except Exception as e:
                        print(f"[DEBUG][MULTISHEET] Erro ao analisar linha {idx}: {e}")
                        print(f"[DEBUG][MULTISHEET] Conteúdo da linha: {list(row[:5])}")
                        # Continuar com próxima linha

                # Para arquivos REDE, se não detectou cabeçalho automático, tentar linha 1 manualmente
                if best_score == 0 and len(df) > 1:
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name} - Tentando linha 1 manualmente como cabeçalho REDE"
                    )
                    # Verificar linha 1 especificamente para arquivos REDE
                    row1 = df.iloc[1]
                    row1_text = " ".join(
                        str(val).lower() for val in row1.values if pd.notna(val)
                    )

                    # Se linha 1 tem palavras típicas de cabeçalho, usar ela
                    if any(
                        word in row1_text
                        for word in [
                            "data",
                            "valor",
                            "banco",
                            "agencia",
                            "conta",
                            "recebimento",
                            "venda",
                        ]
                    ):
                        best_header_idx = 1
                        best_score = 5
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Forçando linha 1 como cabeçalho: {list(row1[:5])}"
                        )
                    else:
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Linha 1 não parece cabeçalho, criando genérico"
                        )
                        best_header_idx = -1
                        best_score = 1
                elif best_score == 0:
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name} - Nenhum cabeçalho detectado, assumindo dados começam na linha 0"
                    )
                    best_header_idx = -1  # Indica que não há linha de cabeçalho
                    best_score = 1

                if best_score > 0:
                    if best_header_idx == -1:
                        # Não há linha de cabeçalho, criar headers genéricos
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Sem cabeçalho, criando headers genéricos"
                        )
                        header_row_idx = -1
                        num_cols = len(df.columns)
                        headers = [
                            f"{sheet_name}_Coluna_{i+1}" for i in range(num_cols)
                        ]
                        print(f"[DEBUG][MULTISHEET] Headers criados: {headers}")
                    else:
                        header_row_idx = best_header_idx
                        row = df.iloc[header_row_idx]

                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Cabeçalho detectado na linha {header_row_idx} (score: {best_score})"
                        )
                        print(f"[DEBUG][MULTISHEET] Conteúdo: {list(row)}")

                        # Criar headers usando nome da planilha + valor real da célula
                        headers = []
                        for i, col_value in enumerate(row):
                            col_str = str(col_value).strip()
                            if col_str and col_str.lower() not in ["nan", "none", ""]:
                                # Limpar caracteres especiais do cabeçalho
                                col_clean = "".join(
                                    c if c.isalnum() or c in " _-" else "_"
                                    for c in col_str
                                )
                                col_clean = (
                                    col_clean.replace(" ", "_")
                                    .replace("__", "_")
                                    .strip("_")
                                )
                                header_name = f"{sheet_name}_{col_clean}"
                            else:
                                header_name = f"{sheet_name}_Coluna_{i+1}"
                            headers.append(header_name)
                            print(
                                f"[DEBUG][MULTISHEET] Coluna {i}: '{col_value}' -> '{header_name}'"
                            )

                if not headers:
                    # Se não encontrou cabeçalho com a nova lógica, tentar fallback
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name} - Cabeçalho não detectado, usando primeira linha como fallback"
                    )

                    if len(df) > 0:
                        header_row_idx = 0
                        first_row = df.iloc[0]
                        headers = []

                        print(f"[DEBUG][MULTISHEET] Primeira linha: {list(first_row)}")

                        for i, col_value in enumerate(first_row):
                            col_str = str(col_value).strip()
                            if col_str and col_str.lower() not in ["nan", "none", ""]:
                                col_clean = "".join(
                                    c if c.isalnum() or c in " _-" else "_"
                                    for c in col_str
                                )
                                col_clean = (
                                    col_clean.replace(" ", "_")
                                    .replace("__", "_")
                                    .strip("_")
                                )
                                header_name = f"{sheet_name}_{col_clean}"
                            else:
                                header_name = f"{sheet_name}_Coluna_{i+1}"
                            headers.append(header_name)

                    # Se ainda não há headers ou DataFrame está vazio, criar headers genéricos
                    if not headers:
                        # Último recurso: usar índices das colunas baseado no número de colunas do DataFrame
                        num_cols = (
                            len(df.columns) if len(df) > 0 else 10
                        )  # Default 10 colunas
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Último recurso: usando {num_cols} nomes de colunas por índice"
                        )
                        headers = [
                            f"{sheet_name}_Coluna_{i+1}" for i in range(num_cols)
                        ]
                        # Não há cabeçalho detectado, usar todos os dados
                        header_row_idx = -1
                        best_score = 1

                # Criar DataFrame final com dados
                # Se cabeçalho foi detectado e não é -1, pular a linha do cabeçalho
                # Senão, usar todos os dados desde a linha 0
                if header_row_idx == -1:
                    start_row = 0  # Sem cabeçalho, usar todos os dados
                else:
                    start_row = header_row_idx + 1 if best_score > 0 else 0

                print(
                    f"[DEBUG][MULTISHEET] {sheet_name} - Iniciando dados na linha {start_row}"
                )

                if start_row < len(df):
                    data_values = df.iloc[start_row:].values
                else:
                    # Se não há dados após o cabeçalho, usar o DataFrame completo
                    data_values = df.values

                # ⚠️ CRÍTICO: Manter dtype=str para evitar conversão automática de datas
                data_df = pd.DataFrame(
                    data_values,
                    columns=headers[
                        : len(data_values[0]) if len(data_values) > 0 else len(headers)
                    ],
                    dtype=str,
                )

                # Limpar linhas que são claramente texto de relatório, não dados
                if not data_df.empty:
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name} - Limpando linhas de relatório..."
                    )

                    # Detectar e remover linhas que são texto de relatório
                    mask_dados_validos = pd.Series([True] * len(data_df))

                    for idx in data_df.index:
                        row = data_df.iloc[idx]
                        first_cell = str(row.iloc[0]).strip() if len(row) > 0 else ""

                        # Textos que indicam linhas de relatório (não dados)
                        report_indicators = [
                            "EXTRATO PARA SIMPLES CONFERÊNCIA",
                            "PERÍODO:",
                            "DATA DE EMISSÃO:",
                            "Observação:",
                            "Este documento pode sofrer alterações",
                        ]

                        # Se primeira célula contém texto de relatório, marcar para remoção
                        is_report_line = any(
                            indicator.lower() in first_cell.lower()
                            for indicator in report_indicators
                        )

                        # Se linha duplica exatamente os nomes das colunas (cabeçalho duplicado)
                        row_values = [
                            str(val).strip().lower()
                            for val in row.values
                            if pd.notna(val)
                        ]
                        header_values = [
                            h.split("_", 1)[-1].lower() for h in headers if "_" in h
                        ]  # Remove prefixo planilha

                        exact_header_match = len(row_values) >= 3 and sum(
                            1 for rv in row_values[:5] if rv in header_values[:5]
                        ) >= min(3, len(row_values))

                        if is_report_line:
                            mask_dados_validos[idx] = False
                            print(
                                f"[DEBUG][MULTISHEET] Removendo linha de relatório: {first_cell}"
                            )
                        elif exact_header_match:
                            mask_dados_validos[idx] = False
                            phrases_count = sum(
                                1 for val in row_values if len(val.split()) > 1
                            )
                            columns_count = sum(
                                1 for val in row_values if val in header_values
                            )
                            print(
                                f"[DEBUG][MULTISHEET] Removendo linha de cabeçalho duplicada: {row_values} (frases: {phrases_count}, colunas: {columns_count})"
                            )

                    # Aplicar limpeza
                    linhas_antes = len(data_df)
                    data_df = data_df[mask_dados_validos]
                    linhas_removidas = linhas_antes - len(data_df)

                    if linhas_removidas > 0:
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Removidas {linhas_removidas} linhas de cabeçalho de relatório"
                        )

                        # Se limpeza removeu todos os dados, reverter para dados originais
                        if len(data_df) == 0 and linhas_antes > 0:
                            print(
                                f"[DEBUG][MULTISHEET] {sheet_name} - Limpeza removeu todos os dados, mantendo originais"
                            )
                            data_df = pd.DataFrame(
                                data_values,
                                columns=headers[
                                    : (
                                        len(data_values[0])
                                        if len(data_values) > 0
                                        else len(headers)
                                    )
                                ],
                            )
                data_df = data_df.fillna("")

                # Remover linhas completamente vazias, mas manter pelo menos uma linha se possível
                data_df_clean = data_df.dropna(how="all")

                # Remover linhas com texto de cabeçalho de relatório
                if not data_df_clean.empty:

                    def is_report_header_row(row):
                        row_text = " ".join(
                            str(x).lower() for x in row if str(x).strip()
                        ).strip()
                        report_texts = [
                            "extrato para simples conferência",
                            "período:",
                            "data de emissão:",
                            "observação:",
                            "este documento pode sofrer alterações",
                        ]
                        # Também verificar se é uma repetição do cabeçalho da planilha
                        # Se todos os valores são strings e correspondem aos nomes das colunas
                        if (
                            len(row.dropna()) >= 3
                        ):  # Se tem pelo menos 3 colunas preenchidas
                            row_values = [
                                str(x).lower().strip()
                                for x in row
                                if str(x).strip() and str(x) != "nan"
                            ]
                            # Verificar se é cabeçalho duplicado com base em frases específicas
                            row_text_complete = " ".join(row_values).lower()
                            header_phrases = [
                                "data do débito",
                                "cancelamento/chargeback",
                                "data original da venda",
                                "valor original da venda",
                                "motivo do cancelamento",
                                "banco agência conta-corrente",
                                "data do ajuste",
                                "tipo do ajuste",
                                "valor total original",
                                # Adicionar verificações específicas para evitar dados como cabeçalho
                                "data prevista do recebimento",
                                "data do recebimento",
                                "resumo de vendas",
                                "número do pedido",
                                "número da autorização",
                            ]

                            # Verificar colunas individuais que são claramente nomes de campos
                            column_name_indicators = [
                                "banco",
                                "agência",
                                "conta-corrente",
                                "valor original da venda",
                                "cancelamento/chargeback",
                                "data do débito",
                                "status",
                            ]

                            # Se contém frases de cabeçalho E não contém datas válidas
                            header_phrase_count = sum(
                                1
                                for phrase in header_phrases
                                if phrase in row_text_complete
                            )

                            # Verificar se valores são nomes de colunas conhecidos
                            is_column_names = sum(
                                1
                                for val in row_values[:5]
                                if str(val).strip().lower() in column_name_indicators
                            )

                            has_actual_dates = any(
                                "2025" in val or "2024" in val or "2026" in val
                                for val in row_values[:3]
                            )

                            # Remover se: tem frases de cabeçalho OU tem nomes de colunas E não tem datas válidas
                            if (
                                header_phrase_count >= 1 or is_column_names >= 2
                            ) and not has_actual_dates:
                                print(
                                    f"[DEBUG][MULTISHEET] Removendo linha de cabeçalho duplicada: {row_values[:5]} (frases: {header_phrase_count}, colunas: {is_column_names})"
                                )
                                return True

                        return any(text in row_text for text in report_texts)

                    # Filtrar linhas que não são cabeçalho de relatório
                    mask_report = data_df_clean.apply(is_report_header_row, axis=1)
                    data_df_clean = data_df_clean[~mask_report]

                    if mask_report.any():
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Removidas {mask_report.sum()} linhas de cabeçalho de relatório"
                        )

                # Se ficou vazio após limpeza, tentar manter dados originais (mas sem cabeçalhos de relatório)
                if data_df_clean.empty and not data_df.empty:
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name} - Limpeza removeu todos os dados, mantendo originais"
                    )
                    data_df_clean = data_df

                # Remover colunas completamente vazias
                if not data_df_clean.empty:
                    data_df_clean = data_df_clean.loc[:, data_df_clean.any()]

                if not data_df_clean.empty:
                    # Aplicar distinct especificamente para planilhas que contenham "pagamentos"
                    if "pagamentos" in sheet_name.lower():
                        linhas_antes = len(data_df_clean)

                        # Para pagamentos, fazer distinct apenas por banco, agência, conta
                        # Identificar colunas ESPECÍFICAS para banco, agência, conta (evitando false positives)
                        colunas_pagamento = []
                        for col in data_df_clean.columns:
                            col_lower = col.lower()
                            # Ser mais específico para evitar colunas como "valor_MDR_descontado"
                            if (
                                (col_lower.endswith("_banco") or col_lower == "banco")
                                or (
                                    col_lower.endswith("_agencia")
                                    or col_lower.endswith("_agência")
                                    or col_lower == "agencia"
                                    or col_lower == "agência"
                                )
                                or (
                                    col_lower.endswith("_conta")
                                    or col_lower.endswith("_conta-corrente")
                                    or col_lower == "conta"
                                )
                            ):
                                colunas_pagamento.append(col)

                        print(
                            f"[DEBUG][MULTISHEET] PAGAMENTOS - Colunas identificadas para distinct: {colunas_pagamento}"
                        )

                        if colunas_pagamento:
                            # Fazer distinct apenas pelas colunas de pagamento identificadas
                            data_df_clean = data_df_clean.drop_duplicates(
                                subset=colunas_pagamento
                            )
                        else:
                            # Se não encontrou colunas específicas, usar todas as colunas não-vazias
                            data_df_clean = data_df_clean.drop_duplicates()

                        linhas_depois = len(data_df_clean)
                        linhas_removidas = linhas_antes - linhas_depois

                        print(f"[DEBUG][MULTISHEET] PAGAMENTOS - DISTINCT aplicado:")
                        print(f"[DEBUG][MULTISHEET] - Linhas antes: {linhas_antes}")
                        print(f"[DEBUG][MULTISHEET] - Linhas depois: {linhas_depois}")
                        print(
                            f"[DEBUG][MULTISHEET] - Duplicatas removidas: {linhas_removidas}"
                        )
                        print(
                            f"[DEBUG][MULTISHEET] - Colunas usadas no distinct: {colunas_pagamento}"
                        )

                    resultado[sheet_name] = {
                        "df": data_df_clean,
                        "headers": list(data_df_clean.columns),
                        "header_row_idx": header_row_idx,
                    }
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name}: {len(data_df_clean)} linhas, {len(data_df_clean.columns)} colunas"
                    )
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name} - Primeira linha de dados: {data_df_clean.iloc[0].tolist()}"
                    )
                else:
                    print(
                        f"[DEBUG][MULTISHEET] {sheet_name}: planilha vazia após limpeza, ignorando"
                    )

            except Exception as e:
                print(
                    f"[DEBUG][MULTISHEET] Erro ao processar planilha {sheet_name}: {e}"
                )
                continue

        # Verificação final: se não há resultados, tentar salvar pelo menos uma planilha com dados brutos
        if not resultado and sheet_names:
            print(
                f"[DEBUG][MULTISHEET] Nenhuma planilha processada com sucesso, tentativa de recuperação..."
            )

            # Tentar ler a primeira planilha disponível de forma mais simples
            for sheet_name in sheet_names:
                try:
                    df_raw = pd.read_excel(
                        path,
                        sheet_name=sheet_name,
                        dtype=str,
                        na_filter=False,
                        engine="openpyxl",
                        nrows=nrows,
                    )

                    if len(df_raw) > 0:
                        # Tentar detectar cabeçalho na recuperação também
                        headers = []
                        header_row_idx = -1

                        # Procurar uma linha que parece cabeçalho (normalmente linha 1 em arquivos REDE)
                        for idx in range(min(3, len(df_raw))):
                            row = df_raw.iloc[idx]
                            row_text = " ".join(
                                str(val).lower() for val in row.values if pd.notna(val)
                            )

                            # Se tem palavras típicas de cabeçalho
                            if any(
                                word in row_text
                                for word in [
                                    "data",
                                    "valor",
                                    "banco",
                                    "agencia",
                                    "conta",
                                    "recebimento",
                                    "venda",
                                    "ajuste",
                                    "lancamento",
                                ]
                            ):
                                header_row_idx = idx
                                print(
                                    f"[DEBUG][MULTISHEET] Recuperação: cabeçalho detectado na linha {idx}"
                                )

                                # Criar headers baseado nos valores da linha
                                for i, col_value in enumerate(row):
                                    col_str = str(col_value).strip()
                                    if col_str and col_str.lower() not in [
                                        "nan",
                                        "none",
                                        "",
                                    ]:
                                        col_clean = "".join(
                                            c if c.isalnum() or c in " _-" else "_"
                                            for c in col_str
                                        )
                                        col_clean = (
                                            col_clean.replace(" ", "_")
                                            .replace("__", "_")
                                            .strip("_")
                                        )
                                        header_name = f"{sheet_name}_{col_clean}"
                                    else:
                                        header_name = f"{sheet_name}_Col_{i+1}"
                                    headers.append(header_name)
                                break

                        # Se não encontrou cabeçalho, usar genéricos
                        if not headers:
                            print(
                                f"[DEBUG][MULTISHEET] Recuperação: usando headers genéricos"
                            )
                            headers = [
                                f"{sheet_name}_Col_{i+1}"
                                for i in range(len(df_raw.columns))
                            ]
                            header_row_idx = -1

                        # Aplicar headers
                        df_raw.columns = headers

                        # Se encontrou cabeçalho, remover essa linha dos dados
                        if header_row_idx >= 0:
                            df_raw = df_raw.iloc[header_row_idx + 1 :].reset_index(
                                drop=True
                            )

                        # Remover linhas completamente vazias
                        df_clean = df_raw.dropna(how="all")

                        if len(df_clean) > 0:
                            # Aplicar distinct especificamente para planilhas que contenham "pagamentos" na recuperação também
                            if "pagamentos" in sheet_name.lower():
                                linhas_antes = len(df_clean)

                                # Para pagamentos, fazer distinct apenas por banco, agência, conta
                                # Identificar colunas ESPECÍFICAS para banco, agência, conta (evitando false positives)
                                colunas_pagamento = []
                                for col in df_clean.columns:
                                    col_lower = col.lower()
                                    # Ser mais específico para evitar colunas como "valor_MDR_descontado"
                                    if (
                                        (
                                            col_lower.endswith("_banco")
                                            or col_lower == "banco"
                                        )
                                        or (
                                            col_lower.endswith("_agencia")
                                            or col_lower.endswith("_agência")
                                            or col_lower == "agencia"
                                            or col_lower == "agência"
                                        )
                                        or (
                                            col_lower.endswith("_conta")
                                            or col_lower.endswith("_conta-corrente")
                                            or col_lower == "conta"
                                        )
                                    ):
                                        colunas_pagamento.append(col)

                                print(
                                    f"[DEBUG][MULTISHEET] RECUPERAÇÃO PAGAMENTOS - Colunas identificadas para distinct: {colunas_pagamento}"
                                )

                                if colunas_pagamento:
                                    # Fazer distinct apenas pelas colunas de pagamento identificadas
                                    df_clean = df_clean.drop_duplicates(
                                        subset=colunas_pagamento
                                    )
                                else:
                                    # Se não encontrou colunas específicas, usar todas as colunas
                                    df_clean = df_clean.drop_duplicates()

                                linhas_depois = len(df_clean)
                                linhas_removidas = linhas_antes - linhas_depois

                                print(
                                    f"[DEBUG][MULTISHEET] RECUPERAÇÃO PAGAMENTOS - DISTINCT aplicado:"
                                )
                                print(
                                    f"[DEBUG][MULTISHEET] - Linhas antes: {linhas_antes}"
                                )
                                print(
                                    f"[DEBUG][MULTISHEET] - Linhas depois: {linhas_depois}"
                                )
                                print(
                                    f"[DEBUG][MULTISHEET] - Duplicatas removidas: {linhas_removidas}"
                                )
                                print(
                                    f"[DEBUG][MULTISHEET] - Colunas usadas no distinct: {colunas_pagamento}"
                                )

                            resultado[sheet_name] = {
                                "df": df_clean,
                                "headers": headers,
                                "header_row_idx": 0,
                            }
                            print(
                                f"[DEBUG][MULTISHEET] Recuperação: {sheet_name} salva com {len(df_clean)} linhas"
                            )
                            break

                except Exception as e:
                    print(
                        f"[DEBUG][MULTISHEET] Erro na recuperação da planilha {sheet_name}: {e}"
                    )
                    continue

        return resultado

    except Exception as e:
        print(f"[DEBUG][MULTISHEET] Erro ao processar arquivo multi-planilhas: {e}")
        raise
    finally:
        # Garantir que o arquivo Excel seja fechado
        try:
            excel_file.close()
        except:
            pass


def safe_read_file(path: str, nrows: Optional[int] = None) -> tuple[pd.DataFrame, int, list[str]]:
    """
    Lê um arquivo de forma robusta:
    1) Tenta Excel com engine apropriado (openpyxl/xlrd).
    2) Se falhar, tenta CSV com vários encodings e separadores.
    Retorna uma tupla com:
    - DataFrame sem linhas/colunas totalmente vazias
    - Índice do cabeçalho encontrado
    - Lista com os nomes das colunas
    """
    ext = Path(path).suffix.lower()
    print(f"[DEBUG] Lendo arquivo: {path} (extensão: {ext})")

    # 🔥 VALIDAÇÃO INICIAL: Verificar se arquivo existe e tem tamanho válido
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    file_size = os.path.getsize(path)
    print(f"[DEBUG] Tamanho do arquivo: {file_size:,} bytes")

    if file_size == 0:
        raise ValueError("Arquivo está vazio (0 bytes)")

    # 🔥 VALIDAÇÃO: Verificar assinatura do arquivo Excel
    if ext in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        with open(path, "rb") as f:
            magic = f.read(4)
            # Excel moderno (ZIP format) deve começar com PK\x03\x04
            if magic[:2] != b"PK":
                raise ValueError(
                    f"Arquivo Excel corrompido ou inválido. Assinatura esperada: 'PK', encontrada: {magic[:2].hex()}"
                )
            print(f"[DEBUG] ✓ Assinatura válida de arquivo ZIP/Excel: {magic[:2]}")

    elif ext == ".xls":
        with open(path, "rb") as f:
            magic = f.read(8)
            # Excel antigo (.xls) deve começar com \xD0\xCF\x11\xA0
            if magic[:4] not in [b"\xd0\xcf\x11\xa0", b"\x09\x08\x10\x00"]:
                raise ValueError(
                    f"Arquivo Excel antigo (.xls) corrompido. Assinatura esperada: 'D0CF11A0', encontrada: {magic[:4].hex()}"
                )
            print(f"[DEBUG] ✓ Assinatura válida de arquivo Excel antigo (.xls)")

    # Detecta se é arquivo binário (possível .tmp ou corrompido)
    def is_binary_string(bytes_data):
        textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
        return bool(bytes_data.translate(None, textchars))

    # 1) Tenta Excel (todas as variações possíveis)
    if ext in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
        try:
            # Primeira tentativa: ler direto como texto
            # ⚠️ CRÍTICO: dtype=str + keep_default_na=False para evitar conversão de datas
            options = {
                "header": None,
                "engine": "openpyxl",
                "dtype": str,  # Força todas as colunas como string
                "keep_default_na": False,  # Não converte strings vazias em NaN
                "na_filter": False,  # Não tenta converter NaN/NA
                "nrows": nrows,
            }
            df = pd.read_excel(path, **options)
            print("[DEBUG] Leitura inicial bem sucedida, procurando cabeçalho...")

            # Procura o cabeçalho nas primeiras linhas (aumentado para 50 para suportar informativos longos)
            for idx in range(min(50, len(df))):
                row = df.iloc[idx]
                if len(row) >= 10:  # Mínimo de 10 colunas
                    row_text = " ".join(str(x).lower() for x in row if str(x).strip())
                    if (
                        ("cpf" in row_text or "cnpj" in row_text)
                        and "valor" in row_text
                        and "data" in row_text
                    ):
                        print(f"[DEBUG] Cabeçalho encontrado na linha {idx}")
                        # Usar esta linha como cabeçalho
                        header_row = [
                            str(x).strip() if str(x).strip() else f"Coluna_{i}"
                            for i, x in enumerate(row)
                        ]
                        # ⚠️ CRÍTICO: Manter dtype=str para evitar conversão automática de datas
                        result_df = pd.DataFrame(
                            df.iloc[idx + 1 :].values, columns=header_row, dtype=str
                        )
                        return result_df.fillna(""), 0, result_df.columns.tolist()

        except Exception as e:
            print(f"[DEBUG] Falha na primeira tentativa: {e}")

        # Se falhou, tenta as outras variações
        excel_errors = []
        for engine in ["openpyxl", None]:
            for header in [None, 0, 1]:
                try:
                    options = {
                        "header": header,
                        "engine": engine,
                        "dtype": str,  # Força todas as colunas como string
                        "keep_default_na": False,  # Não converte strings vazias em NaN
                        "na_filter": False,  # Não tenta converter NaN/NA
                        "nrows": nrows,
                    }
                    df = pd.read_excel(path, **options)
                    print(
                        f"[DEBUG] Primeiras linhas lidas do Excel (engine={engine}, header={header}):"
                    )
                    print(df.head(5))

                    # Se encontramos um cabeçalho válido, vamos usar ele
                    if header == 1:  # header está na linha 1
                        df.columns = [
                            str(col).strip() if col is not None else f"Coluna_{i}"
                            for i, col in enumerate(df.columns)
                        ]
                        df = df.iloc[
                            1:
                        ]  # Remove a primeira linha que agora é cabeçalho
                        print("[DEBUG] Usando cabeçalho encontrado na linha 1")
                        print("[DEBUG] Colunas:", df.columns.tolist())
                        df.dropna(how="all", inplace=True)
                        df.dropna(how="all", axis=1, inplace=True)
                        return df.fillna(""), 1, df.columns.tolist()

                    # ⚠️ CRÍTICO: Quando header=None, detectar cabeçalho manualmente
                    if header is None:
                        print(
                            "[DEBUG] Detectando cabeçalho automaticamente (header=None)..."
                        )
                        idx_header = detectar_cabecalho(df)
                        print(f"[DEBUG] Cabeçalho detectado na linha: {idx_header}")

                        if idx_header >= 0 and idx_header < len(df):
                            # Extrair nomes das colunas da linha detectada
                            header_row = df.iloc[idx_header]
                            header_names = [
                                (
                                    str(col).strip()
                                    if str(col).strip()
                                    and str(col).strip().lower() not in ["nan", "none"]
                                    else f"Coluna_{i}"
                                )
                                for i, col in enumerate(header_row)
                            ]
                            print(
                                f"[DEBUG] Nomes das colunas extraídos: {header_names[:10]}..."
                            )

                            # Aplicar cabeçalho e remover linhas antes dele
                            # ⚠️ CRÍTICO: Converter para string para evitar conversão automática de datas
                            df_with_header = df.iloc[idx_header + 1 :].astype(str)
                            df_with_header.columns = header_names
                            df_with_header.reset_index(drop=True, inplace=True)

                            print(
                                f"[DEBUG] DataFrame com cabeçalho aplicado - shape: {df_with_header.shape}"
                            )
                            print(
                                f"[DEBUG] Primeiras colunas: {list(df_with_header.columns)[:10]}"
                            )

                            df_with_header.dropna(how="all", inplace=True)
                            df_with_header.dropna(how="all", axis=1, inplace=True)
                            return (
                                df_with_header.fillna(""),
                                idx_header,
                                df_with_header.columns.tolist(),
                            )

                    df.dropna(how="all", inplace=True)
                    df.dropna(how="all", axis=1, inplace=True)
                    return df.fillna(""), 0, df.columns.tolist()
                except Exception as e:
                    excel_errors.append(f"engine={engine}, header={header}: {e}")
        print("[DEBUG] Falha ao ler Excel em todas as variações:")
        for err in excel_errors:
            print(f"  - {err}")
            # Fallback: leitura forçada via zipfile + xml (apenas para .xlsx)
            import zipfile
            import xml.etree.ElementTree as ET

            try:
                with zipfile.ZipFile(path) as z:
                    print("[DEBUG][FALLBACK] Arquivos no zip:")
                    for name in z.namelist():
                        print(f"  - {name}")
                    sheet_names = [
                        n
                        for n in z.namelist()
                        if n.startswith("xl/worksheets/") and n.endswith(".xml")
                    ]
                    print(f"[DEBUG][FALLBACK] Worksheets encontrados: {sheet_names}")
                    if not sheet_names:
                        raise ValueError("Nenhuma worksheet encontrada no xlsx")
                    print(f"[DEBUG][FALLBACK] Usando worksheet: {sheet_names[0]}")

                    # Primeiro carregar shared strings
                    print("[DEBUG][FALLBACK] Carregando shared strings...")
                    shared_strings = []
                    if "xl/sharedStrings.xml" in z.namelist():
                        with z.open("xl/sharedStrings.xml") as ssf:
                            ss_tree = ET.parse(ssf)
                            ss_root = ss_tree.getroot()
                            for si in ss_root.findall(
                                ".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"
                            ):
                                text = "".join(
                                    t.text or ""
                                    for t in si.findall(
                                        ".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
                                    )
                                )
                                shared_strings.append(text)
                    print(
                        f"[DEBUG][FALLBACK] {len(shared_strings)} shared strings carregadas"
                    )

                    # Agora ler o worksheet
                    print("[DEBUG][FALLBACK] Lendo conteúdo do worksheet...")
                    with z.open(sheet_names[0]) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        ns = {
                            "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                        }
                        print("[DEBUG][FALLBACK] Iniciando leitura das células...")
                        rows = []
                        print("[DEBUG][FALLBACK] Primeiras 5 linhas do arquivo:")
                        for i, row in enumerate(root.findall(".//a:row", ns)):
                            if nrows and i > (nrows + 50): # some buffer for header search
                                break
                            values = []
                            for c in row.findall("a:c", ns):
                                v = c.find("a:v", ns)
                                cell_type = c.attrib.get("t")
                                val = ""
                                if v is not None:
                                    if cell_type == "s" and shared_strings:
                                        try:
                                            idx = int(v.text)
                                            val = shared_strings[idx]
                                        except (ValueError, IndexError):
                                            val = v.text or ""
                                    else:
                                        val = v.text or ""
                                values.append(val)
                            rows.append(values)

                            # Mostrar as primeiras 5 linhas com seus valores
                            if i < 5:
                                print(f"[DEBUG][FALLBACK] Linha {i}:", values)

                        print("[DEBUG][FALLBACK] Procurando linha de cabeçalho...")

                        header = None
                        data_start = 0
                        max_cols = 0

                        # Analisamos cada linha sequencialmente, começando da primeira
                        for i, row in enumerate(rows):
                            if not row or all(not cell for cell in row):
                                continue

                            print(f"\n[DEBUG][FALLBACK] === Verificando linha {i} ===")
                            print(f"Número de colunas: {len(row)}")
                            print(
                                f"Conteúdo: {row[:5]}..."
                            )  # Mostra as 5 primeiras colunas

                            # Primeiro critério: mais de 10 colunas não vazias
                            non_empty = [v for v in row if v not in (None, "", "None")]
                            if len(non_empty) < 10:
                                print(
                                    "Linha descartada: menos de 10 colunas não vazias"
                                )
                                continue

                            print("✓ Tem mais de 10 colunas não vazias")

                            # Segundo critério: procura por palavras-chave específicas
                            row_text = " ".join(
                                str(cell).lower() for cell in row if cell
                            )

                            # Verificações específicas por coluna
                            found_cpf = any(
                                "cpf" in str(cell).lower()
                                or "cnpj" in str(cell).lower()
                                for cell in row
                            )
                            found_valor = any(
                                "valor" in str(cell).lower() for cell in row
                            )
                            found_data = any(
                                "data" in str(cell).lower() for cell in row
                            )

                            print(f"Encontrou CPF/CNPJ: {found_cpf}")
                            print(f"Encontrou Valor: {found_valor}")
                            print(f"Encontrou Data: {found_data}")

                            matches_count = sum([found_cpf, found_valor, found_data])
                            if matches_count >= 2:
                                print("✓ Encontrou as palavras-chave necessárias")

                                # Preservar nomes exatos das colunas do cabeçalho
                                header_fixed = []
                                for idx, h in enumerate(row):
                                    if not h or h == "None" or str(h).strip() == "":
                                        header_fixed.append(f"Coluna_{idx}")
                                    else:
                                        header_fixed.append(str(h).strip())

                                print("[DEBUG] Colunas identificadas:")
                                for idx, col in enumerate(header_fixed):
                                    print(f"   {idx}: {col}")

                                # Normalizar todas as linhas de dados para ter o mesmo número de colunas
                                data = rows[i + 1 :]
                                normalized_data = []
                                for data_row in data:
                                    if len(data_row) < len(header_fixed):
                                        data_row = data_row + [""] * (
                                            len(header_fixed) - len(data_row)
                                        )
                                    elif len(data_row) > len(header_fixed):
                                        data_row = data_row[: len(header_fixed)]
                                    normalized_data.append(data_row)

                                # Criar DataFrame com os nomes de colunas preservados
                                df = pd.DataFrame(normalized_data, columns=header_fixed)
                                print(
                                    f"[DEBUG] DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas"
                                )

                                # Verificar primeira linha de dados
                                print("\n[DEBUG] Amostra da primeira linha:")
                                for col in header_fixed[:5]:
                                    val = df[col].iloc[0] if len(df) > 0 else "N/A"
                                    print(f"   {col}: {val}")

                                return df.fillna(""), i, list(df.columns)
                                print(
                                    f"[DEBUG] Criando DataFrame com cabeçalho da linha {i}"
                                )

                                # Criar DataFrame com os dados a partir do cabeçalho
                                data = rows[
                                    i + 1 :
                                ]  # Pegar todas as linhas após o cabeçalho
                                header_row = row

                                # Corrigir nomes de colunas vazias
                                header_fixed = [
                                    h if h and h != "None" else f"Coluna_{idx}"
                                    for idx, h in enumerate(header_row)
                                ]

                                # Criar DataFrame com as colunas corretas
                                df = pd.DataFrame(data, columns=header_fixed)
                                print(
                                    f"[DEBUG] DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas"
                                )
                                return df.fillna(""), data_start - 1, header_fixed
                            else:
                                print(
                                    "✗ Não encontrou todas as palavras-chave necessárias"
                                )

                            # Se encontrarmos pelo menos 2 dos indicadores principais
                            if sum(matches.values()) >= 2:
                                print(
                                    f"[DEBUG][FALLBACK] >>> Encontrado cabeçalho na linha {i}"
                                )
                                print("[DEBUG][FALLBACK] Conteúdo do cabeçalho:")
                                for idx, val in enumerate(row):
                                    print(f"   Coluna {idx}: {val}")
                                header = row
                                data_start = i + 1
                                max_cols = len(row)
                                print(
                                    f"[DEBUG][FALLBACK] Total de {max_cols} colunas encontradas"
                                )
                                data = rows[
                                    data_start:
                                ]  # Pega todas as linhas após o cabeçalho

                                # Substitui strings vazias no cabeçalho por nomes de coluna numerados
                                header_fixed = []
                                for i, h in enumerate(header):
                                    if not h or h in (None, "None", ""):
                                        h = f"Coluna_{i}"
                                    header_fixed.append(h)

                                print(
                                    "\n[DEBUG][FALLBACK] Cabeçalho após correção de nomes vazios:"
                                )
                                for i, h in enumerate(header_fixed):
                                    print(f"   {i}: {h}")

                                # Cria DataFrame mantendo todas as colunas
                                df = pd.DataFrame(data, columns=header_fixed)
                                print(
                                    f"\n[DEBUG][FALLBACK] DataFrame criado com {len(df)} linhas e {len(df.columns)} colunas"
                                )
                                print("[DEBUG][FALLBACK] Colunas do DataFrame:")
                                for i, col in enumerate(df.columns):
                                    print(f"   {i}: {col}")
                                print("\n[DEBUG][FALLBACK] Primeiras 3 linhas:")
                                print(df.head(3))
                                return df.fillna(""), data_start - 1, header_fixed

                        # Se não encontrou cabeçalho nas primeiras 20 linhas, continua procurando
                        if not header:
                            print(
                                "\n[DEBUG][FALLBACK] Cabeçalho não encontrado nas primeiras 20 linhas, continuando busca..."
                            )
                            for i, row in enumerate(rows[20:], 20):
                                if not row or all(not cell for cell in row):
                                    continue

                                row_text = " ".join(
                                    str(cell).lower() for cell in row if cell
                                )
                                matches = {
                                    key: any(kw in row_text for kw in keywords)
                                    for key, keywords in header_indicators.items()
                                }

                                if sum(matches.values()) >= 2:
                                    print(
                                        f"[DEBUG][FALLBACK] >>> Encontrado cabeçalho na linha {i}"
                                    )
                                    header = row
                                    data_start = i + 1
                                    max_cols = len(row)
                                    print(
                                        f"[DEBUG][FALLBACK] Total de {max_cols} colunas encontradas"
                                    )
                                    data = rows[data_start:]

                                    # Substitui strings vazias no cabeçalho por nomes de coluna numerados
                                    header_fixed = []
                                    for i, h in enumerate(header):
                                        if not h or h in (None, "None", ""):
                                            h = f"Coluna_{i}"
                                        header_fixed.append(h)

                                    # Cria DataFrame mantendo todas as colunas
                                    df = pd.DataFrame(data, columns=header_fixed)
                                    return df.fillna(""), i, header_fixed

                        # Se mesmo assim não encontrou, usa a primeira linha não vazia
                        if not header:
                            # Normaliza os dados para ter o mesmo número de colunas
                            data = []
                            for row in rows[data_start:]:
                                # Preenche ou trunca para ter o mesmo número de colunas
                                if len(row) < max_cols:
                                    row = row + [""] * (max_cols - len(row))
                                else:
                                    row = row[:max_cols]
                                data.append(row)

                            # Remove linhas vazias e cria o DataFrame
                            data = [row for row in data if any(cell for cell in row)]
                            df = pd.DataFrame(data, columns=header)

                            # Remove colunas vazias e sem nome
                            df = df.loc[:, ~df.columns.isin([None, "", "None"])]
                            df = df.dropna(how="all", axis=1)

                            return df.fillna(""), data_start, header
                        else:
                            raise ValueError(
                                "Não foi possível identificar o cabeçalho no arquivo"
                            )
                    # ...não faz sentido usar sep aqui, removido bloco inválido...
            except Exception as e:
                print(f"[DEBUG] Falha na leitura forçada via zipfile/xml: {e}")
                # 🔥 SE É EXCEL VÁLIDO MAS TODAS AS TENTATIVAS FALHARAM, NÃO TENTE LER COMO TEXTO
                if ext in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
                    raise ValueError(
                        f"Arquivo Excel válido mas não foi possível ler o conteúdo. "
                        f"Possíveis causas:\n"
                        f"1. Arquivo protegido por senha\n"
                        f"2. Formato Excel corrompido internamente\n"
                        f"3. Arquivo muito grande ou complexo\n"
                        f"\nTente:\n"
                        f"- Abrir no Excel e Salvar Como novo arquivo .xlsx\n"
                        f"- Exportar como CSV\n"
                        f"- Remover proteção/senha se houver\n"
                        f"\nErro técnico: {e}"
                    )

    # 3) Tenta ler como texto puro (último recurso - APENAS PARA CSV/TXT)
    if ext not in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
        try:
            print("\n[DEBUG] Iniciando leitura de arquivo texto...", flush=True)
            if nrows:
                # Read only a chunk if nrows is provided (e.g. 1MB should be enough for few hundred rows)
                with open(path, "rb") as f:
                    raw = f.read(1024 * 1024) 
                print(f"[DEBUG] Bytes lidos (limitado): {len(raw)}", flush=True)
            else:
                with open(path, "rb") as f:
                    raw = f.read()
                print(f"[DEBUG] Bytes lidos: {len(raw)}", flush=True)

            text = raw.decode("utf-8", errors="replace")
            text = raw.decode("utf-8", errors="replace")
            linhas = [l.strip() for l in text.splitlines() if l.strip()]

            print("\n[DEBUG] === ANÁLISE DE TEXTO PURO ===", flush=True)
            print(f"[DEBUG] Total de linhas não vazias: {len(linhas)}", flush=True)
            print("\n[DEBUG] Primeiras 5 linhas do arquivo:", flush=True)

            # Vamos examinar cada byte das primeiras linhas
            for i, l in enumerate(linhas[:5]):
                print(f"\n[DEBUG] Linha {i}:", flush=True)
                print(f"Conteúdo (ASCII): {l[:150]}", flush=True)
                print(
                    f"Bytes (hex): {' '.join(hex(ord(c))[2:] for c in l[:50])}",
                    flush=True,
                )  # Palavras-chave críticas que indicam uma linha de cabeçalho
            header_indicators = {
                "cpf": ["cpf", "cnpj"],
                "venda": ["valor", "venda", "transacao", "transação"],
                "ec": ["estabelecimento", "ec", "loja", "número do ec"],
            }
            print("\n[DEBUG] Procurando por palavras-chave no texto:", flush=True)
            for categoria, palavras in header_indicators.items():
                print(f"- {categoria}: {', '.join(palavras)}", flush=True)

            # Tenta identificar o delimitador mais provável nas primeiras linhas
            for sep in [";", ",", "\t", "|"]:
                print(f"\n[DEBUG] === Testando separador: '{sep}' ===", flush=True)
                # Analisa apenas as primeiras 20 linhas
                for i, linha in enumerate(linhas[:20]):
                    if not linha:
                        print(f"[DEBUG] Linha {i}: vazia, pulando...", flush=True)
                        continue

                    # Divide a linha pelo separador
                    valores = linha.split(sep)
                    print(
                        f"\n[DEBUG] Linha {i}: encontradas {len(valores)} colunas",
                        flush=True,
                    )

                    if len(valores) <= 1:
                        print(
                            "[DEBUG] Insuficiente (precisa > 1), pulando...", flush=True
                        )
                        continue

                    # Verifica se tem células suficientes e indicadores de cabeçalho
                    if len(valores) >= 5:  # Mínimo de 5 colunas para ser considerado
                        print(
                            f"\n[DEBUG] >>> Linha {i} é candidata (tem {len(valores)} colunas):",
                            flush=True,
                        )
                        for j, val in enumerate(valores[:5]):
                            print(f"   Col {j}: {val}", flush=True)

                        texto_linha = " ".join(str(v).lower() for v in valores)
                        print(
                            "[DEBUG] Texto da linha (primeiros 150 caracteres):",
                            texto_linha[:150],
                        )

                        matches = {
                            key: any(kw in texto_linha for kw in keywords)
                            for key, keywords in header_indicators.items()
                        }
                        matches_count = sum(matches.values())
                        print(
                            f"\n[DEBUG] Quantidade de matches encontrados: {matches_count}/3",
                            flush=True,
                        )
                        print(f"[DEBUG] Detalhe dos matches: {matches}", flush=True)

                        if matches_count >= 2:
                            print(
                                f"\n[DEBUG] >>>>>>> CABEÇALHO ENCONTRADO NA LINHA {i} <<<<<<<",
                                flush=True,
                            )
                            print("\n[DEBUG] Detalhamento do cabeçalho:", flush=True)
                            for j, v in enumerate(valores):
                                print(f"   Coluna {j}: '{v}'", flush=True)

                            # Usa esta linha como cabeçalho
                            header = valores
                            # Pega as linhas seguintes como dados
                            print(
                                "\n[DEBUG] Iniciando processamento das linhas de dados...",
                                flush=True,
                            )
                            data = [linha.split(sep) for linha in linhas[i + 1 :]]
                            print(
                                f"[DEBUG] Total de {len(data)} linhas de dados encontradas",
                                flush=True,
                            )

                            if data:
                                print(
                                    "\n[DEBUG] Amostra da primeira linha de dados:",
                                    flush=True,
                                )
                                primeira_linha = data[0]
                                for j, v in enumerate(primeira_linha[:5]):
                                    print(f"   Col {j}: '{v}'", flush=True)
                            # Normaliza número de colunas
                            max_cols = len(header)
                            data = [
                                (
                                    row[:max_cols]
                                    if len(row) > max_cols
                                    else row + [""] * (max_cols - len(row))
                                )
                                for row in data
                            ]
                            df = pd.DataFrame(data, columns=header)
                            df = df.loc[:, ~df.columns.isin([None, "", "None"])]
                            df = df.dropna(how="all", axis=1)
                            return df.fillna(""), i, header
            # Se não encontrou nenhum padrão com separadores conhecidos
            print(
                "\n[DEBUG] Nenhum separador comum encontrado, tentando divisão por espaços..."
            )
            # Tenta usar a primeira linha não vazia como cabeçalho
            for i, linha in enumerate(linhas):
                valores = linha.split()  # divide por espaços
                if len(valores) >= 5:  # se tiver pelo menos 5 colunas
                    print(
                        f"\n[DEBUG] Encontrada linha {i} com {len(valores)} colunas usando espaços como separador"
                    )
                    print("[DEBUG] Conteúdo da linha:", valores)
                    header = valores
                    data = [l.split() for l in linhas[i + 1 :]]
                    max_cols = len(header)
                    print(
                        f"[DEBUG] Encontradas {len(data)} linhas de dados após esta linha"
                    )
                    data = [
                        (
                            row[:max_cols]
                            if len(row) > max_cols
                            else row + [""] * (max_cols - len(row))
                        )
                        for row in data
                    ]
                    df = pd.DataFrame(data, columns=header)
                    df = df.loc[:, ~df.columns.isin([None, "", "None"])]
                    df = df.dropna(how="all", axis=1)
                    return df.fillna(""), i, header

            # Se não encontrou estrutura tabular, retorna DataFrame vazio e header vazio
            print(
                "[DEBUG] Não foi possível identificar estrutura tabular no arquivo. Retornando DataFrame vazio."
            )
            return pd.DataFrame(), 0, []
        except Exception as e:
            print(f"[DEBUG] Falha ao ler como texto puro: {e}")
            # Sempre retorna 3 valores mesmo em erro
            return pd.DataFrame(), 0, []

    # Se chegou aqui e o arquivo era Excel, já teria dado raise acima
    # Este ponto só é alcançado para arquivos não-Excel que falharam em tudo
    raise ValueError(
        f"Não foi possível ler o arquivo. Formato não reconhecido ou arquivo corrompido.\n"
        f"Extensão: {ext}\n"
        f"Tente converter para CSV ou .xlsx válido."
    )


def _to_datetime_pt(s: pd.Series) -> pd.Series:
    res = pd.to_datetime(s, errors="coerce", dayfirst=True)
    if not res.empty:
        # MySQL datetimes must be between 1000-01-01 and 9999-12-31
        mask_too_early = res < pd.Timestamp(1000, 1, 1)
        res[mask_too_early] = pd.NaT
    return res


def _to_float_br(s: pd.Series) -> pd.Series:
    # Se já for float, limpa infinitos e retorna
    if pd.api.types.is_float_dtype(s):
        return s.replace([np.inf, -np.inf], np.nan)
    # Se for inteiro, converte para float
    if pd.api.types.is_integer_dtype(s):
        return s.astype(float)
    # Se for string, trata formato brasileiro
    s = s.astype(str)
    # Só remove pontos se houver vírgula (milhar)
    if not s.empty:
        has_comma = s.str.contains(",")
        s1 = s.copy()
        if has_comma.any():
            s1[has_comma] = s1[has_comma].str.replace(".", "", regex=False)
        s1 = s1.str.replace(",", ".", regex=False)
        result = pd.to_numeric(s1, errors="coerce")
    else:
        result = pd.Series([], dtype=float)
    # Limpar valores infinitos do resultado
    return result.replace([np.inf, -np.inf], np.nan)


def detectar_cabecalho(df: pd.DataFrame, max_scan: int = 100) -> int:
    """
    Detecta a linha de cabeçalho usando heurística melhorada
    """
    # Palavras que indicam cabeçalho (expandido)
    header_keywords = {
        # Financeiro
        "nsu",
        "bandeira",
        "autorização",
        "ec",
        "cnpj",
        "cpf",
        "valor",
        "transação",
        "valor líquido",
        "valor bruto",
        "data da transação",
        "quantidade de parcelas",
        "taxa",
        "desconto",
        "liquido",
        "bruto",
        "pagamento",
        "recebimento",
        # Bancário
        "banco",
        "agencia",
        "conta",
        "codigo",
        "numero",
        "documento",
        # Identificação
        "nome",
        "cliente",
        "id",
        "codigo",
        "lancamento",
        "recebivel",
        "venda",
        # Status e tipos
        "status",
        "situacao",
        "tipo",
        "modalidade",
        "parcela",
        "cartao",
        # Datas
        "data",
        "vencimento",
        "liquidacao",
        "processamento",
    }

    best = (0, 0)  # (score, idx)

    print(
        f"[DEBUG][DETECTAR_CABECALHO] Analisando {min(max_scan, len(df))} linhas para cabeçalho..."
    )

    for i in range(min(max_scan, len(df))):
        row = df.iloc[i]
        vals = row.astype(str).fillna("").str.strip()

        # Filtrar células não vazias
        non_empty_vals = [v for v in vals if v and v.lower() not in ["nan", "none"]]
        non_empty_count = len(non_empty_vals)

        if non_empty_count < 2:  # Muito poucas colunas preenchidas
            continue

        score = non_empty_count  # Base score: quantidade de colunas preenchidas

        # Bonus por palavras-chave de cabeçalho
        header_text = " ".join(non_empty_vals).lower()
        keyword_matches = 0

        for keyword in header_keywords:
            if keyword in header_text:
                score += 3
                keyword_matches += 1

        # Bonus extra se tem muitas palavras-chave
        if keyword_matches >= 3:
            score += 5
        elif keyword_matches >= 2:
            score += 2

        # Penalidade se parece com dados (não cabeçalho)
        data_penalty = 0
        for val in non_empty_vals[:5]:  # Só verifica as primeiras 5 células
            val_clean = (
                val.replace(",", "").replace(".", "").replace("/", "").replace("-", "")
            )

            # Se é só números (provavelmente valor monetário ou data)
            if val_clean.isdigit() and len(val_clean) >= 4:
                data_penalty += 2
            # Se tem padrão de data dd/mm/yyyy
            elif "/" in val and len(val) >= 8:
                parts = val.split("/")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    data_penalty += 2

        score -= data_penalty

        print(
            f"[DEBUG][DETECTAR_CABECALHO] Linha {i}: score={score} (keywords={keyword_matches}, penalty={data_penalty})"
        )
        print(f"[DEBUG][DETECTAR_CABECALHO] Conteúdo: {non_empty_vals[:5]}...")

        if score > best[0]:
            best = (score, i)

    detected_idx = best[1]
    print(
        f"[DEBUG][DETECTAR_CABECALHO] Cabeçalho detectado na linha {detected_idx} (score: {best[0]})"
    )

    return detected_idx


# ---------- Contrato dos parsers ----------


class FonteParser(Protocol):
    def detect_score(self, path: str, head_df: pd.DataFrame) -> int: ...
    def parse(
        self, path: str, nrows: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]: ...


@dataclass
class ParseMeta:
    source: str
    header_row: int
    columns_raw: List[str]


# ---------- Parsers específicos ----------


class CieloHistoricoDetalheParser:
    SOURCE = "cielo_historico_detalhe"

    def detect_score(self, path: str, head_df: pd.DataFrame) -> int:
        name = path.lower()
        score = 0
        if "cielo" in name and "historico" in name:
            score += 40
        idx = detectar_cabecalho(head_df)
        headers = [str(h).strip().lower() for h in head_df.iloc[idx].tolist()]
        keys = {"nsu", "bandeira", "autorização", "data", "valor", "parcelas", "ec"}
        score += sum(1 for k in keys if any(k in h for h in headers)) * 5
        return score

    def parse(
        self, path: str, nrows: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_raw = pd.read_excel(
            path,
            header=None,
            engine="openpyxl",
            dtype=str,
            keep_default_na=False,
            nrows=nrows,
        )
        print("[DEBUG][CieloHistoricoDetalheParser] Primeiras linhas do arquivo:")
        print(df_raw.head(5))
        idx = detectar_cabecalho(df_raw)
        print(
            f"[DEBUG][CieloHistoricoDetalheParser] Índice do cabeçalho detectado: {idx}"
        )
        print(
            f"[DEBUG][CieloHistoricoDetalheParser] Linha do cabeçalho: {df_raw.iloc[idx].tolist()}"
        )
        headers = [str(h).strip() if h is not None else "" for h in df_raw.iloc[idx]]
        df = df_raw.iloc[idx + 1 :].reset_index(drop=True).copy()
        # Ajusta largura para cabeçalho
        if df.shape[1] != len(headers):
            df = (
                df.iloc[:, : len(headers)]
                if df.shape[1] > len(headers)
                else df.reindex(columns=list(range(len(headers))), fill_value=None)
            )
        df.columns = headers

        # Normalizações de coluna típicas de Cielo
        # Renomeação robusta: aceita variações de maiúsculas/minúsculas, espaços, underscores e acentos

        def norm(s):
            return (
                unicodedata.normalize("NFKD", s)
                .encode("ASCII", "ignore")
                .decode("ASCII")
                .replace("_", " ")
                .replace("-", " ")
                .lower()
                .strip()
            )

        rename_sug = {
            "data da transacao": "Data da Transação",
            "data da venda": "Data_da_venda",
            "bandeira": "Bandeira",
            "valor liquido": "Valor Líquido",
            "valor da transacao": "Valor da Transação",
            "quantidade de parcelas": "Quantidade_de_parcelas",
        }
        # Mapeia colunas normalizadas para o nome real
        cols_norm = {norm(c): c for c in df.columns}
        for k, v in rename_sug.items():
            if k in cols_norm:
                df.rename(columns={cols_norm[k]: v}, inplace=True)

        # tipos
        for c in ["Data_da_venda", "Data da Transação"]:
            if c in df.columns:
                df[c] = _to_datetime_pt(df[c])

        for c in [
            "Valor da Transação",
            "Valor Líquido",
            "Valor_da_venda",
            "Valor_líquido_da_venda",
            "Valor_descontado",
        ]:
            if c in df.columns:
                df[c] = _to_float_br(df[c])

        if "Quantidade_de_parcelas" in df.columns:
            df["Quantidade_de_parcelas"] = (
                pd.to_numeric(df["Quantidade_de_parcelas"], errors="coerce")
                .replace([np.inf, -np.inf], np.nan)  # Remove infinitos
                .fillna(1)
                .astype(int)
            )

        meta = {
            "source": self.SOURCE,
            "header_row": idx,
            "columns_raw": headers,
        }
        return df, meta


class FaturamentoECParser:
    SOURCE = "faturamento_ec"

    def detect_score(self, path: str, head_df: pd.DataFrame) -> int:
        name = path.lower()
        score = 0
        if "faturamento" in name and "ec" in name:
            score += 40
        idx = detectar_cabecalho(head_df)
        headers = [str(h).strip().lower() for h in head_df.iloc[idx].tolist()]
        keys = {"cnpj", "ec", "data", "valor", "comissão", "líquido", "transação"}
        score += sum(1 for k in keys if any(k in h for h in headers)) * 4
        return score

    def parse(
        self, path: str, nrows: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_raw = pd.read_excel(
            path,
            header=None,
            engine="openpyxl",
            dtype=str,
            keep_default_na=False,
            nrows=nrows,
        )
        idx = detectar_cabecalho(df_raw)
        headers = [str(h).strip() if h is not None else "" for h in df_raw.iloc[idx]]
        df = df_raw.iloc[idx + 1 :].reset_index(drop=True).copy()
        if df.shape[1] != len(headers):
            df = (
                df.iloc[:, : len(headers)]
                if df.shape[1] > len(headers)
                else df.reindex(columns=list(range(len(headers))), fill_value=None)
            )
        df.columns = headers

        # Normalizações prováveis
        date_candidates = [c for c in df.columns if "data" in c.lower()]
        for c in date_candidates:
            df[c] = _to_datetime_pt(df[c])

        money_candidates = [
            c
            for c in df.columns
            if any(
                k in c.lower() for k in ["valor", "líquido", "bruto", "comiss", "taxa"]
            )
        ]
        for c in money_candidates:
            df[c] = _to_float_br(df[c])
            # Ajuste: Multiplica taxas percentuais por 100 apenas para registros da REDE
            if c in ["Taxas_Perc", "Taxas_RR"] and "Bandeira" in df.columns:
                mask_rede = (
                    df["Bandeira"]
                    .astype(str)
                    .str.upper()
                    .str.contains("REDE", na=False)
                )
                df.loc[mask_rede, c] = df.loc[mask_rede, c] * 100
                print(
                    f"[DEBUG][REDE] Taxa {c} multiplicada por 100 para {mask_rede.sum()} registros da REDE"
                )

        meta = {
            "source": self.SOURCE,
            "header_row": idx,
            "columns_raw": headers,
        }
        return df, meta


class GenericoPlanilhaParser:
    SOURCE = "generico"

    def detect_score(self, path: str, head_df: pd.DataFrame) -> int:
        # fallback baixo score
        return 10

    def parse(
        self, path: str, nrows: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df_raw = pd.read_excel(
            path,
            header=None,
            engine="openpyxl",
            dtype=str,
            keep_default_na=False,
            nrows=nrows,
        )
        idx = detectar_cabecalho(df_raw)
        headers = [str(h).strip() if h is not None else "" for h in df_raw.iloc[idx]]
        df = df_raw.iloc[idx + 1 :].reset_index(drop=True).copy()
        if df.shape[1] != len(headers):
            df = (
                df.iloc[:, : len(headers)]
                if df.shape[1] > len(headers)
                else df.reindex(columns=list(range(len(headers))), fill_value=None)
            )
        df.columns = headers
        meta = {"source": self.SOURCE, "header_row": idx, "columns_raw": headers}
        return df, meta


# ---------- Registro/Fábrica ----------

PARSERS: List[FonteParser] = [
    CieloHistoricoDetalheParser(),
    FaturamentoECParser(),
    GenericoPlanilhaParser(),
]


def escolher_parser(path: str, head_df: pd.DataFrame) -> FonteParser:
    scored = [(p.detect_score(path, head_df), p) for p in PARSERS]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


# ---------- Fluxos de alto nível ----------


def read_file_with_header(path: str) -> tuple[pd.DataFrame, int, list[str]]:
    """
    Lê um arquivo Excel e retorna o DataFrame, índice do cabeçalho e nomes das colunas.
    Reutiliza a lógica robusta do safe_read_file.
    """
    return safe_read_file(path)


def is_multisheet_rede_file(path: str) -> bool:
    """
    Detecta se é arquivo multi-planilhas (independente de contexto)
    Critérios: arquivo Excel + múltiplas planilhas + planilha "capa"
    """
    ext = Path(path).suffix.lower()
    print(f"[DEBUG][MULTISHEET_DETECT] Verificando arquivo: {path}")
    print(f"[DEBUG][MULTISHEET_DETECT] Extensão: {ext}")

    try:
        with open("debug_detection.txt", "a") as f:
            f.write(f"\nis_multisheet_rede_file called at {datetime.now()}\n")
            f.write(f"Path: {path}\n")
            f.write(f"Ext: {ext}\n")
    except:
        pass

    if ext not in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"):
        print(f"[DEBUG][MULTISHEET_DETECT] Extensão não suportada: {ext}")
        return False

    try:
        excel_file = pd.ExcelFile(path, engine="openpyxl")
        sheet_names = excel_file.sheet_names
        sheet_names_lower = [name.lower() for name in sheet_names]

        print(f"[DEBUG][MULTISHEET_DETECT] Planilhas encontradas: {sheet_names}")
        print(f"[DEBUG][MULTISHEET_DETECT] Planilhas (lowercase): {sheet_names_lower}")

        # Critérios: tem planilha "capa" e pelo menos 2 planilhas no total
        has_capa = "capa" in sheet_names_lower
        multiple_sheets = len(sheet_names) >= 2

        print(f"[DEBUG][MULTISHEET_DETECT] Tem capa: {has_capa}")
        print(
            f"[DEBUG][MULTISHEET_DETECT] Múltiplas planilhas: {multiple_sheets} (total: {len(sheet_names)})"
        )

        result = has_capa and multiple_sheets
        print(f"[DEBUG][MULTISHEET_DETECT] Resultado final: {result}")

        return result

    except Exception as e:
        print(f"[DEBUG][MULTISHEET_DETECT] Erro ao verificar multi-planilhas: {e}")
        return False


def preparar_dataframe_de_arquivo(
    path: str,
    engine: Engine,
    cliente_id: int,
    ec_id: str = "",
    usuario: str = "desconhecido",
    contexto: str = "",
    tipo_origem: str = "V",
    progress_callback=None,
    log_callback=None,
    nrows: Optional[int] = None,
):
    """
    Processa o arquivo com feedback de progresso e logs.
    Reutiliza a lógica robusta de safe_read_file para leitura e detecção de cabeçalho.
    progress_callback: função(percentual:int) para atualizar barra de progresso
    log_callback: função(msg:str) para atualizar logs na UI
    """

    with PerformanceTimer("IO_ORCHESTRATOR", "Preparar DataFrame de Arquivo", {"file": os.path.basename(path), "contexto": contexto}):
        # Inicializar variáveis que podem ser usadas no return
        meta = {"source": "Unknown", "header_row": 0, "columns_raw": []}
        df_final = pd.DataFrame()
        transformacoes = {}
    
        def update_progress(val, message=None):
            if progress_callback:
                if message:
                    try:
                        progress_callback(val, message)
                    except TypeError:
                        progress_callback(val)
                else:
                    progress_callback(val)
    
        def log(msg):
            now = datetime.now().strftime("%H:%M:%S")
            if log_callback:
                log_callback(f"[{now}] {msg}")
    
        update_progress(5)
        log(f"Processando arquivo (1/10): Iniciando leitura robusta do arquivo...")
        
        log_to_debug_file(f"\n--- PREPARAR DF AT {datetime.now()} ---")
        log_to_debug_file(f"Path: {path}")
        log_to_debug_file(f"Contexto: {contexto}")
        log_to_debug_file(f"Tipo: {tipo_origem}")
        
        print(f"[DEBUG][PROCESSAR] 🚀 INICIANDO preparar_dataframe_de_arquivo")
        print(f"[DEBUG][PROCESSAR] - Arquivo: {path}")
        print(f"[DEBUG][PROCESSAR] - Contexto: '{contexto}'")
        print(f"[DEBUG][PROCESSAR] - Tipo origem: '{tipo_origem}'")
    
        try:
            # Verificar se é arquivo multi-planilhas (independente de contexto)
            print(f"[DEBUG][PROCESSAR] 🔍 Verificando se é multi-sheet...")
            print(
                f"[DEBUG][PROCESSAR] - Contexto: '{contexto}' (upper: '{contexto.upper()}')"
            )
            is_multisheet = is_multisheet_rede_file(path)
            log_to_debug_file(f"IS_MULTISHEET: {is_multisheet}")
            
            # --- TENTATIVA MODULAR (Strategy Pattern) ---
            if not is_multisheet:
                importer = ImporterFactory.get_importer(engine, path, ec_id, cliente_id, contexto, usuario, tipo_origem)
                if importer:
                    log(f"Executando motor de importação modular: {importer.__class__.__name__}")
                    importer.read(path, nrows=nrows, progress_callback=update_progress)
                    importer.parse(progress_callback=update_progress)
                    importer.normalize(progress_callback=update_progress)
                    
                    # Enriquecimento de metadados antes de retornar
                    if importer.df_proc is not None and not importer.df_proc.empty:
                        importer.df_proc["arquivo_origem"] = os.path.basename(path)
                        if "ec_id" not in importer.df_proc.columns or importer.df_proc["ec_id"].isna().all():
                            importer.df_proc["ec_id"] = str(ec_id)
                    
                    update_progress(100)
                    # Formato esperado: (df_final, transformacoes, header_row)
                    return importer.df_proc, getattr(importer, 'transformacoes', {}), getattr(importer, 'header_idx', 0)
                else:
                    raise ValueError("Nenhum motor de importação compatível encontrado para este arquivo.")
    
            if is_multisheet:
                log(
                    f"Processando arquivo (2/10): Detectado arquivo multi-planilhas, processando todas as abas..."
                )
                print("[DEBUG][PROCESSAR] Arquivo multi-planilhas detectado")
    
                multisheet_data = safe_read_multisheet_file(
                    path, tipo_origem, engine, contexto, nrows=nrows
                )
    
                if not multisheet_data:
                    raise ValueError(
                        "Nenhuma planilha válida encontrada no arquivo multi-planilhas"
                    )
    
                # Combinar todas as planilhas em um único DataFrame
                combined_dfs = []
                all_transformacoes = {}
    
                print(f"[DEBUG][MULTISHEET] 📊 COMBINANDO PLANILHAS")
                print(
                    f"[DEBUG][MULTISHEET] - Total de planilhas para processar: {len(multisheet_data)}"
                )
                print(
                    f"[DEBUG][MULTISHEET] - Planilhas encontradas: {list(multisheet_data.keys())}"
                )
    
                for sheet_name, sheet_info in multisheet_data.items():
                    df_sheet = sheet_info["df"]
                    headers_sheet = sheet_info["headers"]
    
                    print(
                        f"[DEBUG][MULTISHEET] Processando planilha {sheet_name}: {len(df_sheet)} linhas"
                    )
    
                    log_to_debug_file(f"[DEBUG][MULTISHEET] {sheet_name} - Carregando regras de de/para...")
                    log_to_debug_file(f"[DEBUG][MULTISHEET] {sheet_name} - Parâmetros: contexto='{contexto}', tipo_origem='{tipo_origem}'")
                    regras = depara_carregar_mapa_completo(
                        engine, contexto=(contexto or ""), tipo_origem=tipo_origem
                    )
                    log_to_debug_file(f"[DEBUG][MULTISHEET] {sheet_name} - Total de regras carregadas: {len(regras)}")
    
                    if df_sheet is not None and not df_sheet.empty:
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - DataFrame antes do de/para:"
                        )
                        print(f"[DEBUG][MULTISHEET] {sheet_name} - Linhas: {len(df_sheet)}")
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Colunas: {list(df_sheet.columns)}"
                        )
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Regras carregadas: {len(regras)}"
                        )
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - Primeiras 3 linhas do DataFrame:"
                        )
                        print(df_sheet.head(3))
    
                        df_sheet_final, transformacoes_sheet = aplicar_regras_depara(
                            df_sheet, regras
                        )
    
                        log_to_debug_file(f"[DEBUG][MULTISHEET] {sheet_name} - DataFrame após de/para:")
                        log_to_debug_file(f"[DEBUG][MULTISHEET] {sheet_name} - Linhas resultantes: {len(df_sheet_final) if df_sheet_final is not None else 0}")
                        log_to_debug_file(f"[DEBUG][MULTISHEET] {sheet_name} - Colunas resultantes: {list(df_sheet_final.columns) if df_sheet_final is not None else []}")
    
                        if not df_sheet_final.empty:
                            # Adicionar coluna identificadora da planilha
                            df_sheet_final["planilha_origem"] = sheet_name
                            combined_dfs.append(df_sheet_final)
                            all_transformacoes.update(transformacoes_sheet)
    
                            print(
                                f"[DEBUG][MULTISHEET] {sheet_name} processada: {len(df_sheet_final)} linhas"
                            )
                        else:
                            print(
                                f"[DEBUG][MULTISHEET] {sheet_name} - DataFrame final está vazio após de/para!"
                            )
                    else:
                        print(
                            f"[DEBUG][MULTISHEET] {sheet_name} - DataFrame original está vazio ou é None"
                        )
    
                if not combined_dfs:
                    raise ValueError(
                        "Nenhuma planilha teve dados válidos após processamento"
                    )
    
                # Combinar todos os DataFrames
                print(f"[DEBUG][MULTISHEET] 🔄 COMBINANDO DATAFRAMES FINAIS")
                print(
                    f"[DEBUG][MULTISHEET] - DataFrames para combinar: {len(combined_dfs)}"
                )
    
                for i, df in enumerate(combined_dfs):
                    print(
                        f"[DEBUG][MULTISHEET] - DataFrame {i}: {len(df)} linhas, {len(df.columns)} colunas"
                    )
                    if len(df) > 0:
                        print(f"[DEBUG][MULTISHEET]   Colunas: {list(df.columns)}")
    
                if combined_dfs:
                    # Antes de combinar, limpar campos que cada aba não deve preencher
                    print(f"[DEBUG][MULTISHEET] 🧹 Limpando campos específicos por aba...")
    
                    for i, df in enumerate(combined_dfs):
                        if "planilha_origem" in df.columns:
                            planilha_origem = (
                                df["planilha_origem"].iloc[0] if len(df) > 0 else "unknown"
                            )
    
                            if planilha_origem == "pagamentos":
                                # Aba PAGAMENTOS: manter apenas banco, agencia, conta
                                # Limpar data_pagamento, data_recebivel, lancamento, valor_liquido, valor_recebivel, descricao
                                campos_para_limpar = [
                                    "data_pagamento",
                                    "data_recebivel",
                                    "lancamento",
                                    "valor_liquido",
                                    "valor_recebivel",
                                    "descricao",
                                ]
                                for campo in campos_para_limpar:
                                    if campo in df.columns:
                                        df[campo] = None
                                        print(
                                            f"[DEBUG][MULTISHEET] - Pagamentos: limpando campo '{campo}'"
                                        )
    
                            elif planilha_origem == "ajustes":
                                # Aba AJUSTES: pode preencher todos os campos principais
                                print(
                                    f"[DEBUG][MULTISHEET] - Ajustes: mantendo todos os campos preenchidos"
                                )
    
                            elif planilha_origem == "cancelamentos e contestações":
                                # Aba CANCELAMENTOS: manter os campos que já tem mapeados
                                print(
                                    f"[DEBUG][MULTISHEET] - Cancelamentos: mantendo campos mapeados"
                                )
    
                    df_final = pd.concat(combined_dfs, ignore_index=True, sort=False)
                    transformacoes = all_transformacoes
    
                    # Aplicar distinct final para registros de planilhas "pagamentos" baseado em banco/agencia/conta
                    linhas_antes_final = len(df_final)
                    if "planilha_origem" in df_final.columns:
                        mask_pagamentos = df_final["planilha_origem"].str.contains(
                            "pagamentos", case=False, na=False
                        )
                        if mask_pagamentos.any():
                            df_pagamentos = df_final[mask_pagamentos]
                            df_outros = df_final[~mask_pagamentos]
    
                            # Distinct apenas nos registros de pagamentos por banco/agencia/conta
                            colunas_distinct = [
                                col
                                for col in ["banco", "agencia", "conta"]
                                if col in df_pagamentos.columns
                            ]
                            if colunas_distinct:
                                linhas_antes_pag = len(df_pagamentos)
                                df_pagamentos_distinct = df_pagamentos.drop_duplicates(
                                    subset=colunas_distinct
                                )
                                linhas_depois_pag = len(df_pagamentos_distinct)
    
                                print(f"[DEBUG][MULTISHEET] 🎯 DISTINCT FINAL APLICADO:")
                                print(
                                    f"[DEBUG][MULTISHEET] - Registros pagamentos antes: {linhas_antes_pag}"
                                )
                                print(
                                    f"[DEBUG][MULTISHEET] - Registros pagamentos depois: {linhas_depois_pag}"
                                )
                                print(
                                    f"[DEBUG][MULTISHEET] - Duplicatas pagamentos removidas: {linhas_antes_pag - linhas_depois_pag}"
                                )
                                print(
                                    f"[DEBUG][MULTISHEET] - Colunas usadas: {colunas_distinct}"
                                )
    
                                # Recombinar
                                df_final = pd.concat(
                                    [df_pagamentos_distinct, df_outros],
                                    ignore_index=True,
                                    sort=False,
                                )
    
                    print(f"[DEBUG][MULTISHEET] ✅ COMBINAÇÃO CONCLUÍDA")
                    print(
                        f"[DEBUG][MULTISHEET] - DataFrame final: {len(df_final)} linhas, {len(df_final.columns)} colunas"
                    )
                    print(f"[DEBUG][MULTISHEET] - Colunas finais: {list(df_final.columns)}")
                    linhas_depois_final = len(df_final)
                    print(
                        f"[DEBUG][MULTISHEET] - Total de duplicatas removidas no processo final: {linhas_antes_final - linhas_depois_final}"
                    )
    
                    # Mostrar primeiras linhas do resultado final
                    if len(df_final) > 0:
                        print(
                            f"[DEBUG][MULTISHEET] - Primeiras 3 linhas do resultado final (após limpeza por aba):"
                        )
                        for idx, row in df_final.head(3).iterrows():
                            print(f"[DEBUG][MULTISHEET]   Linha {idx}: {dict(row)}")
                else:
                    print(
                        f"[DEBUG][MULTISHEET] ❌ ERRO: Nenhum DataFrame válido para combinar!"
                    )
                    df_final = pd.DataFrame()
                    transformacoes = {}
    
                # Definir meta para multi-sheet
                meta = {
                    "source": "MultiSheet",
                    "header_row": 1,  # Multi-sheets geralmente têm header na linha 1
                    "columns_raw": list(df_final.columns),
                    "sheets_processed": len(multisheet_data),
                }
    
                print(f"[DEBUG][MULTISHEET] 📋 RESUMO FINAL:")
                print(
                    f"[DEBUG][MULTISHEET] - Resultado final: {len(df_final)} linhas de {len(multisheet_data)} planilhas"
                )
                print(
                    f"[DEBUG][MULTISHEET] - Transformações: {len(transformacoes)} aplicadas"
                )
    
        except Exception as e:
            log(f"Erro na leitura do arquivo: {e}")
            print(f"[DEBUG][PROCESSAR][ERRO] {e}")
            raise Exception(f"Falha na leitura do arquivo: {e}")
    
        # --- Lógica comum para ambos os casos (multi-sheet e single-sheet) ---
    
        # --- REGRA ESPECÍFICA DA REDE: CONCATENAR MODALIDADE + TIPO = FORMA_DE_PAGAMENTO ---
        print("[DEBUG][REDE] Verificando necessidade de concatenar modalidade + tipo...")
    
        # Verificar se é arquivo da REDE e tem as colunas necessárias
        tem_modalidade = any("modalidade" in str(col).lower() for col in df_final.columns)
        tem_tipo = any("tipo" in str(col).lower() for col in df_final.columns)
        try:
            tem_rede = any("rede" in str(col).lower() for col in df_final.columns) or any(
                df_final[col].astype(str).str.upper().str.contains("REDE", na=False).any()
                for col in df_final.columns
                if pd.api.types.is_object_dtype(df_final[col])
            )
        except Exception as e:
            print(f"[DEBUG][REDE] Erro ao verificar REDE: {e}")
            tem_rede = False
    
        # Verificar se já existe coluna Forma_de_pagamento (criada pelo mapeamento)
        tem_forma_pagamento = "Forma_de_pagamento" in df_final.columns
    
        if tem_rede and tem_modalidade and tem_tipo and not tem_forma_pagamento:
            print(
                "[DEBUG][REDE] Detectado arquivo REDE com colunas modalidade e tipo - criando Forma_de_pagamento"
            )
    
            # Encontrar as colunas exatas
            col_modalidade = None
            col_tipo = None
    
            for col in df_final.columns:
                if "modalidade" in str(col).lower():
                    col_modalidade = col
                    print(f"[DEBUG][REDE] Coluna modalidade encontrada: {col}")
                elif "tipo" in str(col).lower():
                    col_tipo = col
                    print(f"[DEBUG][REDE] Coluna tipo encontrada: {col}")
    
            if col_modalidade and col_tipo:
                # Concatenar modalidade + " " + tipo
                df_final["Forma_de_pagamento"] = (
                    df_final[col_modalidade].astype(str).str.upper().str.strip()
                    + " "
                    + df_final[col_tipo].astype(str).str.upper().str.strip()
                )
    
                # Normalizar acentos e limpar espaços
                df_final["Forma_de_pagamento"] = (
                    df_final["Forma_de_pagamento"]
                    .str.replace("À", "A", regex=False)
                    .str.replace("Á", "A", regex=False)
                    .str.replace("Ã", "A", regex=False)
                    .str.replace("É", "E", regex=False)
                    .str.replace("Ê", "E", regex=False)
                    .str.replace("Í", "I", regex=False)
                    .str.replace("Ó", "O", regex=False)
                    .str.replace("Ô", "O", regex=False)
                    .str.replace("Ú", "U", regex=False)
                    .str.replace("Ç", "C", regex=False)
                    .str.replace("  ", " ", regex=False)  # Remove espaços duplos
                )
        elif tem_rede and tem_modalidade and tem_tipo and tem_forma_pagamento:
            print(
                "[DEBUG][REDE] Arquivo REDE já possui coluna Forma_de_pagamento - concatenando modalidade+tipo na coluna existente"
            )
    
            # Encontrar as colunas exatas
            col_modalidade = None
            col_tipo = None
    
            for col in df_final.columns:
                if "modalidade" in str(col).lower() and col != "Forma_de_pagamento":
                    col_modalidade = col
                    print(f"[DEBUG][REDE] Coluna modalidade encontrada: {col}")
                elif "tipo" in str(col).lower() and col != "Forma_de_pagamento":
                    col_tipo = col
                    print(f"[DEBUG][REDE] Coluna tipo encontrada: {col}")
    
            if col_modalidade and col_tipo:
                # Sobrescrever a coluna Forma_de_pagamento existente com modalidade + " " + tipo
                df_final["Forma_de_pagamento"] = (
                    df_final[col_modalidade].astype(str).str.upper().str.strip()
                    + " "
                    + df_final[col_tipo].astype(str).str.upper().str.strip()
                )
    
                # Normalizar acentos e limpar espaços
                df_final["Forma_de_pagamento"] = (
                    df_final["Forma_de_pagamento"]
                    .str.replace("À", "A", regex=False)
                    .str.replace("Á", "A", regex=False)
                    .str.replace("Ã", "A", regex=False)
                    .str.replace("É", "E", regex=False)
                    .str.replace("Ê", "E", regex=False)
                    .str.replace("Í", "I", regex=False)
                    .str.replace("Ó", "O", regex=False)
                    .str.replace("Ô", "O", regex=False)
                    .str.replace("Ú", "U", regex=False)
                    .str.replace("Ç", "C", regex=False)
                    .str.replace("  ", " ", regex=False)  # Remove espaços duplos
                )
    
                # Remover as colunas originais modalidade e tipo para evitar duplicatas
                if col_modalidade in df_final.columns:
                    df_final = df_final.drop(columns=[col_modalidade])
                    print(
                        f"[DEBUG][REDE] Removida coluna {col_modalidade} após concatenação"
                    )
                if col_tipo in df_final.columns:
                    df_final = df_final.drop(columns=[col_tipo])
                    print(f"[DEBUG][REDE] Removida coluna {col_tipo} após concatenação")
        print(
            f"[DEBUG][PROCESSAR] DataFrame final: {df_final.shape[0]} linhas, {df_final.shape[1]} colunas"
        )
        print(f"[DEBUG][PROCESSAR] Colunas finais: {list(df_final.columns)}")
        print(f"[DEBUG][PROCESSAR] Primeiras 3 linhas finais:\n{df_final.head(3)}")
        print(f"[DEBUG][PROCESSAR] Transformações aplicadas: {transformacoes}")
    
        # --- NORMALIZAÇÃO FINAL DE FORMA_DE_PAGAMENTO ---
        if "Forma_de_pagamento" in df_final.columns:
            print(
                "[DEBUG][PROCESSAR] Aplicando normalização final em Forma_de_pagamento (pré-pago → à vista)"
            )
    
            def normalizar_forma_pagamento_final(valor):
                if pd.isna(valor):
                    return valor
                v = str(valor).upper().strip()
                # Normalizar acentos
                v = (
                    v.replace("À", "A")
                    .replace("Á", "A")
                    .replace("Ã", "A")
                    .replace("É", "E")
                    .replace("Ê", "E")
                    .replace("Í", "I")
                    .replace("Ó", "O")
                    .replace("Ô", "O")
                    .replace("Ú", "U")
                    .replace("Ç", "C")
                )
                # Normalizar pré-pago para à vista
                if (
                    "PRE PAGO" in v or "PREPAGO" in v or "PRE-PAGO" in v or "PRE PAGO" in v
                ) and "CREDITO" in v:
                    return "CREDITO A VISTA"
                if (
                    "PRE PAGO" in v or "PREPAGO" in v or "PRE-PAGO" in v or "PRE PAGO" in v
                ) and "DEBITO" in v:
                    return "DEBITO A VISTA"
                return valor
    
            valores_antes = df_final["Forma_de_pagamento"].unique()
            df_final["Forma_de_pagamento"] = df_final["Forma_de_pagamento"].apply(
                normalizar_forma_pagamento_final
            )
            valores_depois = df_final["Forma_de_pagamento"].unique()
    
            print(f"[DEBUG][PROCESSAR] Valores antes: {valores_antes}")
            print(f"[DEBUG][PROCESSAR] Valores depois: {valores_depois}")
    
        update_progress(80)
        # Pequena pausa para garantir atualização visual
        import time
    
        time.sleep(0.1)
        update_progress(100)
        return df_final, transformacoes, meta.get("header_row", 0)


def aplicar_regras_depara(
    df_origem: pd.DataFrame, regras: List[Dict[str, Any]]
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    with PerformanceTimer("TRANSFORM", "Aplicação de Regras De-Para", {"rows": len(df_origem), "regras": len(regras) if regras else 0}):
        print(
            "[DEBUG][aplicar_regras_depara] Início do processamento com lógica de agrupamento."
        )
        print(
            f"[DEBUG][aplicar_regras_depara] Regras recebidas: {len(regras) if regras else 0}"
        )
        print(
            f"[DEBUG][aplicar_regras_depara] Colunas do DataFrame origem: {list(df_origem.columns)}"
        )
        print(f"[DEBUG][aplicar_regras_depara] DF Origem (primeiras 5 linhas):\n{df_origem.head(5)}")

        if not isinstance(regras, list) or (regras and not isinstance(regras[0], dict)):
            raise TypeError("O argumento 'regras' deve ser uma lista de dicts.")

        # Criar mapeamento a partir das regras
        # IMPORTANTE: Agora mapeamento é dict de LISTAS para suportar 1:N
        mapeamento = {}  # {origem: [destino1, destino2, ...]}
        transformacoes = {}

        if regras:
            print(f"[DEBUG][aplicar_regras_depara] Primeiras 3 regras: {regras[:3]}")
            for i, regra in enumerate(regras):
                origem_nome = regra.get("origem_nome")
                destino_nome = regra.get("destino_nome")

                if i < 3:  # Debug das primeiras 3 regras
                    print(
                        f"[DEBUG][aplicar_regras_depara] Regra {i}: origem='{origem_nome}', destino='{destino_nome}'"
                    )

                # Regras já vêm filtradas por ativo=1 do banco
                if origem_nome and destino_nome:
                    # Converter para string se não for
                    origem = (
                        str(origem_nome).strip()
                        if not isinstance(origem_nome, str)
                        else origem_nome.strip()
                    )
                    destino = (
                        str(destino_nome).strip()
                        if not isinstance(destino_nome, str)
                        else destino_nome.strip()
                    )

                    # Acumular múltiplos destinos para a mesma origem
                    if origem not in mapeamento:
                        mapeamento[origem] = []
                    mapeamento[origem].append(destino)

                    transformacoes[origem] = destino  # Manter compatibilidade

            print(f"[DEBUG][aplicar_regras_depara] Mapeamento básico criado: {mapeamento}")

            # CORREÇÃO TEMPORÁRIA: Adicionar regras faltantes para todas as abas
            # Detectar tipo de aba pelas colunas presentes
            colunas_pagamentos = [
                col
                for col in df_origem.columns
                if isinstance(col, str) and col.startswith("pagamentos_")
            ]
            colunas_ajustes = [
                col
                for col in df_origem.columns
                if isinstance(col, str) and col.startswith("ajustes_")
            ]
            colunas_cancelamentos = [
                col
                for col in df_origem.columns
                if isinstance(col, str) and col.startswith("cancelamentos e contestações_")
            ]

            # Regras para PAGAMENTOS - APENAS banco, agencia, conta
            if colunas_pagamentos:
                print(
                    f"[DEBUG][aplicar_regras_depara] Detectada aba PAGAMENTOS com {len(colunas_pagamentos)} colunas"
                )
                print(
                    f"[DEBUG][aplicar_regras_depara] PAGAMENTOS: Mapeando APENAS banco/agencia/conta (outros campos ficam vazios)"
                )
                # Aba pagamentos só deve preencher banco, agencia, conta
                # Outros campos como data_pagamento, data_recebivel devem vir apenas da aba AJUSTES
                # NÃO mapear data_pagamento, data_recebivel, valor_liquido, etc. da aba pagamentos

            # Regras para AJUSTES
            if colunas_ajustes:
                print(
                    f"[DEBUG][aplicar_regras_depara] Detectada aba AJUSTES com {len(colunas_ajustes)} colunas"
                )
                regras_faltantes = {
                    "ajustes_data_do_ajuste": "data_pagamento",
                    "ajustes_data_do_lançamento": "data_recebivel",
                    "ajustes_valor_total_original_do_ajuste": "valor_liquido",
                    "ajustes_motivo": "lancamento",
                    "ajustes_forma_de_compensação": "descricao",
                }
                for origem, destino in regras_faltantes.items():
                    if origem in df_origem.columns and origem not in mapeamento:
                        print(
                            f"[DEBUG][aplicar_regras_depara] AJUSTES: {origem} -> {destino}"
                        )
                        mapeamento[origem] = [destino]  # LISTA
                        transformacoes[origem] = destino

            # Regras para CANCELAMENTOS
            if colunas_cancelamentos:
                print(
                    f"[DEBUG][aplicar_regras_depara] Detectada aba CANCELAMENTOS com {len(colunas_cancelamentos)} colunas"
                )
                regras_faltantes = {
                    "cancelamentos e contestações_data_do_débito": "data_pagamento",
                    "cancelamentos e contestações_data_original_da_venda": "data_recebivel",
                    "cancelamentos e contestações_valor_original_da_venda": "valor_recebivel",  # Nota: valor_recebivel, not valor_liquido!
                    "cancelamentos e contestações_cancelamento_chargeback": "descricao",
                }
                for origem, destino in regras_faltantes.items():
                    if origem in df_origem.columns and origem not in mapeamento:
                        print(
                            f"[DEBUG][aplicar_regras_depara] CANCELAMENTOS: {origem} -> {destino}"
                        )
                        mapeamento[origem] = [destino]  # LISTA
                        transformacoes[origem] = destino

            # Correção específica para valores de cancelamentos
            # cancelamentos devem mapear valor_original_da_venda para valor_recebivel, não valor_liquido
            for origem, destinos in list(mapeamento.items()):
                if (
                    "cancelamentos e contestações_valor_original_da_venda" in origem
                    and "valor_liquido" in destinos
                ):
                    print(
                        f"[DEBUG][aplicar_regras_depara] Corrigindo mapeamento: {origem} -> valor_recebivel (era valor_liquido)"
                    )
                    mapeamento[origem] = ["valor_recebivel"]  # LISTA
                    transformacoes[origem] = "valor_recebivel"

            # Correção específica para modalidade+tipo em vendas REDE
            # Evitar colunas duplicadas no DataFrame final
            tem_modalidade_vendas = "modalidade" in df_origem.columns
            tem_tipo_vendas = "tipo" in df_origem.columns
            ambos_mapeiam_forma_pagamento = (
                tem_modalidade_vendas
                and tem_tipo_vendas
                and mapeamento.get("modalidade") == ["Forma_de_pagamento"]  # LISTA
                and mapeamento.get("tipo") == ["Forma_de_pagamento"]  # LISTA
            )

            if ambos_mapeiam_forma_pagamento:
                print(
                    "[DEBUG][aplicar_regras_depara] Detectado mapeamento duplicado modalidade+tipo -> Forma_de_pagamento"
                )
                print(
                    "[DEBUG][aplicar_regras_depara] Concatenando modalidade+tipo ANTES do mapeamento para evitar duplicatas"
                )

                # Concatenar modalidade + " " + tipo na própria coluna modalidade
                df_origem["modalidade"] = (
                    df_origem["modalidade"].astype(str).str.upper().str.strip()
                    + " "
                    + df_origem["tipo"].astype(str).str.upper().str.strip()
                ).str.replace(
                    "  ", " ", regex=False
                )  # Remover espaços duplos

                # Remover o mapeamento da coluna tipo para evitar duplicata
                if "tipo" in mapeamento:
                    del mapeamento["tipo"]
                    del transformacoes["tipo"]
                    print(
                        "[DEBUG][aplicar_regras_depara] Removido mapeamento de 'tipo' - dados concatenados em 'modalidade'"
                    )

            print(f"[DEBUG][aplicar_regras_depara] Mapeamento final: {mapeamento}")

        # Remover colunas auxiliares
        columns_to_remove = ["Filtrado", "planilha_origem"]
        df_limpo = df_origem.drop(columns=columns_to_remove, errors="ignore")
        
        log_to_debug_file(f"\n[APLICAR_REGRAS] Colunas Origem: {list(df_origem.columns)}")
        log_to_debug_file(f"Regras: {len(regras)} encontradas")
        if mapeamento:
            log_to_debug_file(f"Mapeamento criado para: {list(mapeamento.keys())}")
        else:
            log_to_debug_file("AVISO: NENHUM MAPEAMENTO CRIADO!")

        if not mapeamento:
            print(
                "[DEBUG][aplicar_regras_depara] AVISO: Nenhum mapeamento ativo encontrado!"
            )
            print(
                "[DEBUG][aplicar_regras_depara] SEM regras ativas, retornando DataFrame vazio para evitar importação incorreta..."
            )

            # Retornar DataFrame vazio se não há regras ativas
            # Isso evita importar dados incorretamente mapeados
            from conf.colunas_recebiveis import listar_colunas_recebiveis_processados
            from conf.conf_bd import get_engine

            engine_vazio = get_engine()
            colunas_validas = listar_colunas_recebiveis_processados(engine_vazio)
            df_vazio = pd.DataFrame(columns=colunas_validas)

            print(
                "[DEBUG][aplicar_regras_depara] Retornando DataFrame vazio - configure regras depara ativas primeiro!"
            )
            return df_vazio, {}

    # Filtrar apenas colunas que têm mapeamento (Case-Insensitive)
    # Criar um mapa de nomes de colunas originais para suas versões em minúsculo
    col_map_orig_to_lower = {col.lower().strip(): col for col in df_limpo.columns if isinstance(col, str)}
    
    # Criar mapeamento de regras com chaves em minúsculo
    mapeamento_lower = {k.lower().strip(): v for k, v in mapeamento.items()}
    
    colunas_mapeadas = [orig_col for lower_col, orig_col in col_map_orig_to_lower.items() if lower_col in mapeamento_lower]

    if not colunas_mapeadas:
        print(
            "[DEBUG][aplicar_regras_depara] AVISO: Nenhuma coluna do DataFrame tem mapeamento específico!"
        )
        print(
            "[DEBUG][aplicar_regras_depara] SEM colunas mapeadas, retornando DataFrame vazio..."
        )

        # Retornar DataFrame vazio se não há colunas mapeadas
        from conf.colunas_recebiveis import listar_colunas_recebiveis_processados
        from conf.conf_bd import get_engine

        engine = get_engine()
        colunas_validas = listar_colunas_recebiveis_processados(engine)
        df_vazio = pd.DataFrame(columns=colunas_validas)

        print(
            "[DEBUG][aplicar_regras_depara] Retornando DataFrame vazio - configure mapeamentos específicos primeiro!"
        )
        return df_vazio, {}

        # Código removido - esta seção foi desabilitada para evitar mapeamento automático incorreto
        if False:  # Desabilitado temporariamente
            mapeamento_rede = {
                "data_pagamento": [
                    "data",
                    "data_do_ajuste",
                    "data_do_lançamento",
                    "data_do_recebimento",
                    "data_do_débito",
                    "data_original_da_venda",
                ],
                "data_recebivel": [
                    "data",
                    "data_do_ajuste",
                    "data_do_lançamento",
                    "data_do_recebimento",
                    "data_original_da_venda",
                    "data_original_de_vencimento",
                ],
                "valor_recebivel": [
                    "valor_depositado",
                    "valor_total_original_do_ajuste",
                    "valor_bruto_da_parcela",
                    "valor_original_da_venda",
                    "valor_cobrado_nesta_data",
                    "valor_creditado_nesta_data",
                ],
                "valor_liquido": [
                    "valor_depositado",
                    "valor_líquido_da_parcela",
                    "valor_creditado_nesta_data",
                    "valor_líquido",
                ],
                "lancamento": [
                    "motivo",
                    "tipo_do_ajuste",
                    "status",
                    "forma_de_compensação",
                    "cancelamento_chargeback",
                    "tipo_do_bloqueio",
                ],
                "descricao": [
                    "nome_do_estabelecimento",
                    "estabelecimento",
                    "tipo_do_ajuste",
                    "motivo",
                    "resumo_de_vendas_número_do_lote_ajustado",
                ],
                "banco": ["banco", "banco_domicilio"],
                "agencia": ["agência", "agencia"],
                "conta": ["conta-corrente", "conta_corrente", "conta"],
            }

            for col_destino, possibilidades in mapeamento_rede.items():
                if col_destino in colunas_validas:
                    for col_origem in df_limpo.columns:
                        # Converter para string se for numérico
                        col_origem_clean = (
                            str(col_origem).lower()
                            if not isinstance(col_origem, str)
                            else col_origem.lower()
                        )
                        for prefixo in [
                            "ajustes_",
                            "recebidos_",
                            "cancelamentos e contestações_",
                            "bloqueados suspenso_",
                            "bloqueados retido e penhorado_",
                            "desagendamentos de cessão_",
                            "cobranças em aberto_",
                        ]:
                            if col_origem_clean.startswith(prefixo):
                                col_origem_clean = col_origem_clean[len(prefixo) :]
                                break

                        pass  # Código desabilitado

            # Fim do bloco desabilitado
            pass

    print(f"[DEBUG][aplicar_regras_depara] Colunas com mapeamento: {colunas_mapeadas}")

    # mapeamento já está no formato {origem: [destino1, destino2, ...]}
    print(
        f"[DEBUG][aplicar_regras_depara] Mapeamento com múltiplos destinos: {mapeamento}"
    )

    # Criar lista de todos os destinos únicos
    destinos_unicos = set()
    for destinos_lista in mapeamento.values():
        destinos_unicos.update(destinos_lista)

    df_resultado = pd.DataFrame(index=df_limpo.index)

    # Função auxiliar para dividir "Produto cielo" em Bandeira e Forma de Pagamento
    def dividir_produto_cielo(valor):
        """
        Divide e normaliza strings de "Produto cielo":

        NORMALIZAÇÕES DE BANDEIRA:
        - MC, MAESTRO → MASTERCARD

        NORMALIZAÇÕES DE FORMA DE PAGAMENTO:
        - CREDITO PRE PAGO (todas variações) → CREDITO A VISTA
        - DEBITO PRE PAGO (todas variações) → DEBITO A VISTA
        - PARCELADO LOJA → CREDITO PARCELADO LOJA

        Exemplos:
        - 'VISA ELECTRON DEBITO A VISTA' → 'VISA ELECTRON', 'DEBITO A VISTA'
        - 'MC CREDITO PRE-PAGO' → 'MASTERCARD', 'CREDITO A VISTA'
        - 'MAESTRO DEBITO PRÉ PAGO' → 'MASTERCARD', 'DEBITO A VISTA'
        - 'VISA PARCELADO LOJA' → 'VISA', 'CREDITO PARCELADO LOJA'
        """
        if pd.isna(valor):
            return None, None

        texto = str(valor).strip().upper()

        # Normalizar acentos e caracteres especiais para comparação
        texto_norm = (
            texto.replace("Á", "A")
            .replace("À", "A")
            .replace("Ã", "A")
            .replace("É", "E")
            .replace("Ê", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
            .replace("Ç", "C")
            .replace("-", " ")  # Remove hífens
        )

        # Bandeiras conhecidas (ordem: mais específicas primeiro)
        bandeiras_conhecidas = [
            "VISA ELECTRON",
            "MASTERCARD",
            "MAESTRO",
            "AMERICAN EXPRESS",
            "HIPERCARD",
            "DINERS",
            "DISCOVER",
            "AMEX",
            "VISA",
            "ELO",
            "MC",  # Adicionar MC como bandeira
        ]

        bandeira = None
        forma = None

        # Identificar a bandeira no início
        for bandeira_candidata in bandeiras_conhecidas:
            if texto.startswith(bandeira_candidata):
                bandeira = bandeira_candidata
                # Remover bandeira do texto para processar o resto
                resto = texto[len(bandeira_candidata) :].strip()
                resto_norm = texto_norm[len(bandeira_candidata) :].strip()

                # 🔥 NORMALIZAR BANDEIRA: MC ou MAESTRO → MASTERCARD
                if bandeira in ["MC", "MAESTRO"]:
                    bandeira = "MASTERCARD"

                # 🔥 NORMALIZAR FORMA DE PAGAMENTO
                # Verificar se tem PRE PAGO (todas as variações: "PRE PAGO", "PRE-PAGO", "PREPAGO")
                tem_pre_pago = (
                    "PRE PAGO" in resto_norm
                    or "PREPAGO" in resto_norm
                    or ("PRE" in resto_norm and "PAGO" in resto_norm)
                )

                if tem_pre_pago and "CREDITO" in resto_norm:
                    # CREDITO PRE PAGO → CREDITO A VISTA
                    forma = "CREDITO A VISTA"
                elif tem_pre_pago and "DEBITO" in resto_norm:
                    # DEBITO PRE PAGO → DEBITO A VISTA
                    forma = "DEBITO A VISTA"
                elif resto_norm == "PARCELADO LOJA":
                    # PARCELADO LOJA → CREDITO PARCELADO LOJA
                    forma = "CREDITO PARCELADO LOJA"
                else:
                    # Manter como está
                    forma = resto if resto else None

                break

        # Se não identificou bandeira, tentar heurística
        if not bandeira:
            palavras = texto.split()
            palavras_norm = texto_norm.split()

            if len(palavras) >= 2:
                bandeira = palavras[0]
                resto = " ".join(palavras[1:])
                resto_norm = " ".join(palavras_norm[1:])

                # 🔥 NORMALIZAR BANDEIRA
                if bandeira in ["MC", "MAESTRO"]:
                    bandeira = "MASTERCARD"

                # 🔥 NORMALIZAR FORMA DE PAGAMENTO
                tem_pre_pago = (
                    "PRE PAGO" in resto_norm
                    or "PREPAGO" in resto_norm
                    or ("PRE" in resto_norm and "PAGO" in resto_norm)
                )

                if tem_pre_pago and "CREDITO" in resto_norm:
                    forma = "CREDITO A VISTA"
                elif tem_pre_pago and "DEBITO" in resto_norm:
                    forma = "DEBITO A VISTA"
                elif resto_norm == "PARCELADO LOJA":
                    forma = "CREDITO PARCELADO LOJA"
                else:
                    forma = resto
            else:
                # Caso genérico: tudo como bandeira
                bandeira = texto
                # 🔥 NORMALIZAR BANDEIRA
                if bandeira in ["MC", "MAESTRO"]:
                    bandeira = "MASTERCARD"
                forma = None

        return bandeira, forma

    # Aplicar mapeamento coluna por coluna, duplicando quando necessário
    # Usar mapeamento_lower criado acima para garantir detecção case-insensitive
    for orig_col_name in df_limpo.columns:
        lower_col = str(orig_col_name).lower().strip()
        if lower_col in mapeamento_lower:
            destinos = mapeamento_lower[lower_col]
            
            # Se tiver múltiplos destinos, logar
            if len(destinos) > 1:
                print(
                    f"[DEBUG][aplicar_regras_depara] ⚡ Duplicando coluna '{orig_col_name}' para {len(destinos)} destinos: {destinos}"
                )

            # 🔥 LÓGICA ESPECIAL: Dividir "Produto cielo" em Bandeira e Forma_de_pagamento
            if lower_col == "produto cielo" and set(
                ["Bandeira", "Forma_de_pagamento"]
            ).issubset(set(destinos)):
                print(
                    f"[DEBUG][aplicar_regras_depara] 🎯 DIVISÃO ESPECIAL: '{orig_col_name}' será dividido em Bandeira e Forma_de_pagamento"
                )

                # Aplicar divisão
                bandeiras = []
                formas = []

                for idx in df_limpo.index:
                    valor = df_limpo.loc[idx, orig_col_name]
                    bandeira, forma = dividir_produto_cielo(valor)
                    bandeiras.append(bandeira)
                    formas.append(forma)

                # Atribuir resultados
                if "Bandeira" in destinos:
                    df_resultado["Bandeira"] = bandeiras
                    print(
                        f"[DEBUG][aplicar_regras_depara]    '{orig_col_name}' → 'Bandeira' (extraído: {len([b for b in bandeiras if b])} valores)"
                    )

                if "Forma_de_pagamento" in destinos:
                    df_resultado["Forma_de_pagamento"] = formas
                    print(
                        f"[DEBUG][aplicar_regras_depara]    '{orig_col_name}' → 'Forma_de_pagamento' (extraído: {len([f for f in formas if f])} valores)"
                    )
            else:
                # Copiar dados da origem para cada destino (comportamento normal)
                for destino in destinos:
                    # Não sobrescrever Forma_de_pagamento se já foi gerada pela divisão especial
                    if (
                        destino == "Forma_de_pagamento"
                        and "Forma_de_pagamento" in df_resultado.columns
                    ):
                        continue
                    df_resultado[destino] = df_limpo[orig_col_name].copy()
                    print(
                        f"[DEBUG][aplicar_regras_depara]    '{orig_col_name}' → '{destino}' ({len(df_limpo[orig_col_name].dropna())} valores não-nulos)"
                    )

    # FILTRO DE DADOS INVÁLIDOS: Remover apenas linhas que são claramente cabeçalhos
    if not df_resultado.empty:
        print(f"[DEBUG][aplicar_regras_depara] Filtrando dados inválidos...")

        # Detectar linhas com dados de cabeçalho/relatório - mais inteligente
        mask_dados_validos = pd.Series(
            [True] * len(df_resultado), index=df_resultado.index
        )

        # Detectar linhas que são claramente cabeçalhos baseado em múltiplos indicadores
        for idx in df_resultado.index:
            row = df_resultado.loc[idx]
            row_str = " ".join(str(val).lower() for val in row.values if pd.notna(val))

            # Indicadores fortes de que é linha de cabeçalho/relatório
            header_indicators = [
                "extrato para simples conferência",
                "período:",
                "data de emissão:",
                "observação:",
                "data do débito cancelamento/chargeback data original",  # múltiplas colunas juntas
                "data do recebimento data original da venda",  # múltiplas colunas juntas
                "data do ajuste data do lançamento id ajuste",  # múltiplas colunas juntas
            ]

            # Se múltiplas colunas contêm exatamente os mesmos nomes de colunas padrão
            exact_column_matches = 0
            exact_column_names = [
                "data do débito",
                "cancelamento/chargeback",
                "data original da venda",
                "valor original da venda",
                "banco",
                "agência",
                "conta-corrente",
                "data do ajuste",
                "data do lançamento",
                "tipo do ajuste",
                "data prevista do recebimento",
                "resumo de vendas",
            ]

            for col_name in exact_column_names:
                if any(
                    str(val).strip().lower() == col_name.lower()
                    for val in row.values
                    if pd.notna(val)
                ):
                    exact_column_matches += 1

            # É cabeçalho se tem múltiplos matches exatos de nomes de colunas OU contém texto de relatório
            is_header = (exact_column_matches >= 2) or any(
                indicator in row_str for indicator in header_indicators
            )

            if is_header:
                mask_dados_validos[idx] = False
                print(
                    f"[DEBUG][aplicar_regras_depara] Removendo linha {idx} (cabeçalho/relatório): {dict(row)}"
                )

        # Aplicar filtro
        linhas_antes = len(df_resultado)
        df_resultado = df_resultado[mask_dados_validos].copy()
        linhas_removidas = linhas_antes - len(df_resultado)

        print(f"[DEBUG][aplicar_regras_depara] Filtro inteligente aplicado:")
        print(f"[DEBUG][aplicar_regras_depara] - Linhas antes: {linhas_antes}")
        print(f"[DEBUG][aplicar_regras_depara] - Linhas removidas: {linhas_removidas}")
        print(f"[DEBUG][aplicar_regras_depara] - Linhas restantes: {len(df_resultado)}")

    print(
        f"[DEBUG][aplicar_regras_depara] Resultado final: {len(df_resultado)} linhas, colunas: {list(df_resultado.columns)}"
    )

    return df_resultado, transformacoes


def normalizar_dataframe_vendas(
    df: pd.DataFrame,
    engine: Engine,
    ec_id: str,
    contexto: str = "padrao",
    usuario: str = "desconhecido",
    tipo_arquivo: str = "venda",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with PerformanceTimer("POLARS", "Normalização Vendas (Pandas Pipeline)", {"rows": len(df), "contexto": contexto}):
        df = df.copy()
    
        # --- INÍCIO DO CÓDIGO DE NORMALIZAÇÃO ---
        # Limpeza de valores infinitos e fora do range permitido em todo o DataFrame
        print(f"[DEBUG] Limpando valores infinitos do DataFrame...")
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                inf_count = (
                    df[col].replace([np.inf, -np.inf], np.nan).isna().sum()
                    - df[col].isna().sum()
                )
                if inf_count > 0:
                    print(f"[DEBUG] Coluna {col}: removidos {inf_count} valores infinitos")
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)
    
        # Conversão de tipos de dados (datas e valores monetários)
    
        # --- NOVO: Preencher coluna 'Adquirente' baseada no contexto selecionado ---
        if contexto and contexto.lower() not in ["", "padrao"]:
            adquirente_valor = contexto.upper()
            if "Adquirente" not in df.columns:
                df["Adquirente"] = adquirente_valor
            else:
                # Preencher apenas onde está vazio/nulo
                mask_vazio = df["Adquirente"].isnull() | (
                    df["Adquirente"].astype(str).str.strip() == ""
                )
                df.loc[mask_vazio, "Adquirente"] = adquirente_valor
        for c in [
            "Data_da_venda",
            "Data_da_autorização_da_venda",
            "Previsão_de_pagamento",
            "Data da Transação",
            "Data Crédito Ec",
        ]:
            if c in df.columns:
                df[c] = _to_datetime_pt(df[c])
    
        # ⚠️ CRÍTICO: Converter valores monetários para float SEM arredondar ainda
        # O arredondamento será feito DEPOIS do ajuste das taxas da REDE
        colunas_valores = [
            "Valor_da_venda",
            "Valor_descontado",
            "Valor_RR",
            "Valor_líquido_da_venda",
            "Valor da Transação",
            "Comissão_Mínima",
            "Valor_da_entrada",
            "Valor_do_saque",
            "Valor Comissão Bruta",
            "Valor Líquido",
            "Taxa_de_embarque",
        ]
    
        for c in colunas_valores:
            if c in df.columns:
                # Converter para float sem arredondar (arredondar depois do ajuste REDE)
                df[c] = _to_float_br(df[c])
    
        # ⚠️ IMPORTANTE: Taxas percentuais - converter mas NÃO arredondar ainda
        # Arredondamento será feito APÓS multiplicação por 100 da REDE (se aplicável)
        colunas_taxa = ["Taxas_Perc", "Taxas_RR"]
        for c in colunas_taxa:
            if c in df.columns:
                df[c] = _to_float_br(df[c])
    
        if "Quantidade_de_parcelas" in df.columns:
            df["Quantidade_de_parcelas"] = (
                pd.to_numeric(df["Quantidade_de_parcelas"], errors="coerce")
                .replace([np.inf, -np.inf], np.nan)
                .fillna(1)
                .astype(int)
            )
    
        # --- AJUSTE ESPECÍFICO: MULTIPLICAR TAXAS DA REDE POR 100 SE NECESSÁRIO ---
        print("[DEBUG][REDE] Verificando necessidade de ajustar taxas da REDE...")
    
        # Identificar registros da REDE pela coluna Adquirente
        mask_rede_adquirente = pd.Series([False] * len(df), index=df.index)
    
        if "Adquirente" in df.columns:
            mask_rede_adquirente = (
                df["Adquirente"].astype(str).str.upper().str.contains("REDE", na=False)
            )
    
        # Aplicar multiplicação por 100 nas taxas percentuais APENAS se valores < 1
        # (Proteção contra multiplicação dupla: 0.0235 → 2.35, mas não 2.35 → 235)
        for coluna_taxa in colunas_taxa:
            if coluna_taxa in df.columns and mask_rede_adquirente.any():
                # Máscara combinada: registros REDE com taxa < 1 (formato decimal)
                mask_ajuste = (
                    mask_rede_adquirente & (df[coluna_taxa] < 1) & df[coluna_taxa].notnull()
                )
    
                if mask_ajuste.any():
                    registros_afetados = mask_ajuste.sum()
                    df.loc[mask_ajuste, coluna_taxa] = (
                        df.loc[mask_ajuste, coluna_taxa] * 100
                    )
                    print(
                        f"[DEBUG][REDE] {coluna_taxa} multiplicada por 100 para {registros_afetados} registros da REDE (valores < 1)"
                    )
                else:
                    print(
                        f"[DEBUG][REDE] {coluna_taxa} já está no formato correto (valores >= 1)"
                    )
    
        # ⚠️ AGORA SIM: Arredondar todos os valores monetários e taxas para 2 casas decimais
        print(
            "[DEBUG] Aplicando arredondamento final (round(2)) em valores monetários e taxas..."
        )
        for c in colunas_valores + colunas_taxa:
            if c in df.columns:
                df[c] = df[c].round(2)
    
        # --- CÁLCULO DE VALOR_RR BASEADO EM TAXAS_RR ---
        print("[DEBUG] Calculando Valor_RR baseado em Taxas_RR...")
    
        if "Taxas_RR" in df.columns and "Valor_da_venda" in df.columns:
            # Identificar registros que têm Taxas_RR válidas e valor da venda
            mask_calc_rr = (
                df["Taxas_RR"].notnull()
                & (df["Taxas_RR"] != 0)
                & df["Valor_da_venda"].notnull()
                & (df["Valor_da_venda"] != 0)
            )
    
            if mask_calc_rr.any():
                # Se Valor_RR não existe, criar coluna
                if "Valor_RR" not in df.columns:
                    df["Valor_RR"] = 0.0
    
                # Calcular Valor_RR = (Valor_da_venda * Taxas_RR) / 100
                # ⚠️ CRÍTICO: Arredondar para 2 casas decimais (evitar imprecisão de ponto flutuante)
                df.loc[mask_calc_rr, "Valor_RR"] = (
                    (
                        df.loc[mask_calc_rr, "Valor_da_venda"]
                        * df.loc[mask_calc_rr, "Taxas_RR"]
                    )
                    / 100
                ).round(2)
    
                registros_calculados = mask_calc_rr.sum()
                print(
                    f"[DEBUG] Valor_RR calculado para {registros_calculados} registros com Taxas_RR válidas"
                )
    
                # Log de exemplo
                if registros_calculados > 0:
                    exemplo_idx = df[mask_calc_rr].index[0]
                    valor_venda = df.loc[exemplo_idx, "Valor_da_venda"]
                    taxa_rr = df.loc[exemplo_idx, "Taxas_RR"]
                    valor_rr = df.loc[exemplo_idx, "Valor_RR"]
                    print(
                        f"[DEBUG] Exemplo cálculo: R$ {valor_venda:.2f} × {taxa_rr:.2f}% = R$ {valor_rr:.2f}"
                    )
        else:
            print("[DEBUG] Colunas Taxas_RR ou Valor_da_venda não encontradas para cálculo")
    
        # --- FIM DO CÓDIGO DE NORMALIZAÇÃO ---
    
        # --- REGRA ESPECÍFICA DA REDE: PREVISÃO DE PAGAMENTO = DATA_DA_VENDA + 31 DIAS ---
        print(
            "[DEBUG][REDE] Verificando se existem dados da REDE para aplicar regra de previsão..."
        )
    
        # Identificar se há registros da REDE
        tem_rede = False
        colunas_adquirente = [
            "Adquirente",
            "adquirente",
            "ADQUIRENTE",
            "Bandeira",
            "bandeira",
        ]
    
        for col in colunas_adquirente:
            if col in df.columns:
                rede_count = (
                    df[col].astype(str).str.upper().str.contains("REDE", na=False).sum()
                )
                if rede_count > 0:
                    tem_rede = True
                    print(
                        f"[DEBUG][REDE] Detectado {rede_count} registros da REDE na coluna {col}"
                    )
                    break
    
        if tem_rede:
            # Buscar coluna de data da venda
            colunas_data_venda = [
                "Data_da_venda",
                "data_da_venda",
                "Data da Transação",
                "data_transacao",
            ]
            coluna_data_encontrada = None
    
            for col in colunas_data_venda:
                if col in df.columns:
                    coluna_data_encontrada = col
                    break
    
            if coluna_data_encontrada:
                # Garantir que existe a coluna de previsão de pagamento
                if "Previsão_de_pagamento" not in df.columns:
                    df["Previsão_de_pagamento"] = pd.NaT
    
                # Criar máscara para registros da REDE
                mask_rede = pd.Series([False] * len(df), index=df.index)
                for col in colunas_adquirente:
                    if col in df.columns:
                        mask_col = (
                            df[col].astype(str).str.upper().str.contains("REDE", na=False)
                        )
                        mask_rede = mask_rede | mask_col
    
                # Aplicar regra: Data_da_venda + 31 dias para registros da REDE
                if mask_rede.any():
                    try:
                        # Garantir que a data está em formato datetime
                        df[coluna_data_encontrada] = pd.to_datetime(
                            df[coluna_data_encontrada], errors="coerce"
                        )
    
                        # Aplicar regra apenas para registros da REDE com data válida
                        mask_data_valida = df[coluna_data_encontrada].notnull()
                        mask_aplicar = mask_rede & mask_data_valida
    
                        if mask_aplicar.any():
                            df.loc[mask_aplicar, "Previsão_de_pagamento"] = df.loc[
                                mask_aplicar, coluna_data_encontrada
                            ] + pd.Timedelta(days=31)
    
                            registros_atualizados = mask_aplicar.sum()
                            print(
                                f"[DEBUG][REDE] Previsão de pagamento calculada para {registros_atualizados} registros da REDE (Data_da_venda + 31 dias)"
                            )
    
                            # Log de exemplo
                            if registros_atualizados > 0:
                                exemplo_idx = df[mask_aplicar].index[0]
                                data_venda = df.loc[exemplo_idx, coluna_data_encontrada]
                                previsao = df.loc[exemplo_idx, "Previsão_de_pagamento"]
                                print(
                                    f"[DEBUG][REDE] Exemplo: Venda {data_venda.strftime('%d/%m/%Y')} → Previsão {previsao.strftime('%d/%m/%Y')}"
                                )
    
                    except Exception as e:
                        print(f"[DEBUG][REDE] Erro ao aplicar regra de previsão: {e}")
            else:
                print(f"[DEBUG][REDE] Nenhuma coluna de data da venda encontrada")
        else:
            print(f"[DEBUG][REDE] Nenhum registro da REDE detectado")
    
        # --- Lógica de vendas_diversas removida conforme solicitado ---
    
        # --- INÍCIO DA LÓGICA DE FILTRAGEM ---
        lancamento_col = None
        for c in df.columns:
            if str(c).strip().lower() in [
                "lancamento",
                "lançamento",
                "descricao",
                "descrição",
            ]:
                lancamento_col = c
                break
        if not lancamento_col:
            lancamento_col = df.columns[0] if len(df.columns) > 0 else None
    
        def norm(s):
            return (
                unicodedata.normalize("NFKD", str(s or ""))
                .encode("ASCII", "ignore")
                .decode("ASCII")
                .upper()
                .strip()
            )
    
        termos_raw = termos_listar(engine, str(ec_id), contexto, tipo="v")
    
        print("[DEBUG][VENDAS] Colunas do DataFrame:", list(df.columns))
        print("[DEBUG][VENDAS] Coluna de lançamento detectada:", lancamento_col)
        print("[DEBUG][VENDAS] termos_raw:", termos_raw)
    
        termos = [
            norm(t["termo"]) if isinstance(t, dict) and "termo" in t else norm(t)
            for t in termos_raw
        ]
        print("[DEBUG][VENDAS] termos normalizados:", termos)
    
        padrao_termos = (
            re.compile("|".join(map(re.escape, termos)), flags=re.IGNORECASE)
            if termos
            else None
        )
    
        # --- NOVA LÓGICA: Verificar status da venda usando termos filtráveis ---
        mask_status_filtravel = pd.Series([False] * len(df), index=df.index)
    
        # Procurar por coluna de status da venda
        status_col = None
        for col in df.columns:
            if str(col).strip().lower() in [
                "status_da_venda",
                "status da venda",
                "status_venda",
                "status",
                "situacao",
                "situação",
            ]:
                status_col = col
                break
    
        if status_col is not None:
            print(f"[DEBUG][STATUS] Coluna de status encontrada: {status_col}")
            print(f"[DEBUG][STATUS] Valores únicos de status: {df[status_col].unique()}")
            print(f"[DEBUG][STATUS] EC: {ec_id}, Contexto: {contexto}")
    
            # Buscar termos filtráveis para status da tabela termos_filtraveis
            # Usar os termos existentes do tipo 'v' para filtrar por status
            try:
                # Buscar todos os termos do tipo 'v' para este EC e contexto
                termos_status_raw = termos_listar(engine, str(ec_id), contexto, tipo="v")
                termos_status = [t["termo"] for t in termos_status_raw if t.get("termo")]
    
                print(
                    f"[DEBUG][STATUS] Termos filtráveis encontrados na tabela (tipo v): {termos_status}"
                )
    
                if termos_status:
                    # Criar padrão regex com os termos da tabela
                    padrao_status = re.compile(
                        "|".join(map(re.escape, termos_status)), flags=re.IGNORECASE
                    )
    
                    print(f"[DEBUG][STATUS] Padrão regex criado: {padrao_status.pattern}")
                    print(f"[DEBUG][STATUS] Testando alguns valores normalizados:")
    
                    # Debug de algumas comparações
                    for val in df[status_col].unique()[:5]:
                        val_norm = norm(val)
                        match = padrao_status.search(val_norm)
                        print(
                            f"[DEBUG][STATUS]   '{val}' -> norm: '{val_norm}' -> match: {bool(match)}"
                        )
    
                    # Aplicar filtro usando termos da tabela na coluna de status
                    mask_status_filtravel = (
                        df[status_col]
                        .astype(str)
                        .apply(lambda x: bool(padrao_status.search(norm(x))))
                    )
    
                    print(
                        f"[DEBUG][STATUS] Total filtradas por termos da tabela: {mask_status_filtravel.sum()}"
                    )
                    print(
                        f"[DEBUG][STATUS] Exemplos de valores que batem: {df[mask_status_filtravel][status_col].unique()[:5] if mask_status_filtravel.any() else 'Nenhum'}"
                    )
                else:
                    print(
                        "[DEBUG][STATUS] Nenhum termo encontrado na tabela termos_filtraveis"
                    )
    
            except Exception as e:
                print(f"[DEBUG][STATUS] Erro ao buscar termos de status: {e}")
        else:
            print("[DEBUG][STATUS] Nenhuma coluna de status encontrada")
    
        mask_vazio = df[lancamento_col].isnull() | (
            df[lancamento_col].astype(str).str.strip() == ""
        )
    
        # 🔥 FILTRAR POR LANÇAMENTO (termos na coluna de lançamento)
        if padrao_termos:
            mask_termo_lancamento = (
                df[lancamento_col]
                .astype(str)
                .apply(lambda x: bool(padrao_termos.search(norm(x))))
            )
        else:
            mask_termo_lancamento = pd.Series([False] * len(df), index=df.index)
    
        # 🔥 FILTRAR POR FORMA DE PAGAMENTO (termos na coluna Forma_de_pagamento)
        mask_termo_forma_pagamento = pd.Series([False] * len(df), index=df.index)
    
        # Procurar coluna Forma_de_pagamento
        forma_pagamento_col = None
        for col in df.columns:
            if str(col).strip().lower() in [
                "forma_de_pagamento",
                "forma de pagamento",
                "formadepagamento",
                "forma_pagamento",
            ]:
                forma_pagamento_col = col
                break
    
        if forma_pagamento_col and padrao_termos:
            print(f"[DEBUG][FORMA_PAGAMENTO] Coluna encontrada: {forma_pagamento_col}")
            print(
                f"[DEBUG][FORMA_PAGAMENTO] Valores únicos: {df[forma_pagamento_col].unique()}"
            )
    
            mask_termo_forma_pagamento = (
                df[forma_pagamento_col]
                .astype(str)
                .apply(lambda x: bool(padrao_termos.search(norm(x))))
            )
    
            if mask_termo_forma_pagamento.any():
                print(
                    f"[DEBUG][FORMA_PAGAMENTO] ⚠️ {mask_termo_forma_pagamento.sum()} registros filtrados por forma de pagamento"
                )
                print(
                    f"[DEBUG][FORMA_PAGAMENTO] Exemplos: {df[mask_termo_forma_pagamento][forma_pagamento_col].unique()[:5]}"
                )
    
        # Combinar todas as máscaras de termos
        mask_termo = mask_termo_lancamento | mask_termo_forma_pagamento
    
        # Combinar máscaras: filtradas = (termos OU status filtrável) E não vazio
        mask_filt = (~mask_vazio) & (mask_termo | mask_status_filtravel)
        mask_proc = (~mask_vazio) & (~mask_termo) & (~mask_status_filtravel)
    
        df_proc = df.loc[mask_proc].copy()
        df_filt = df.loc[mask_filt].copy()
    
        # Debug da separação
        print(f"[DEBUG][SEPARAÇÃO] Total original: {len(df)}")
        print(f"[DEBUG][SEPARAÇÃO] Processadas (aprovadas): {len(df_proc)}")
        print(f"[DEBUG][SEPARAÇÃO] Filtradas (termos + status): {len(df_filt)}")
        print(
            f"[DEBUG][SEPARAÇÃO] Filtradas por termos no lançamento: {mask_termo_lancamento.sum()}"
        )
        print(
            f"[DEBUG][SEPARAÇÃO] Filtradas por termos na forma_de_pagamento: {mask_termo_forma_pagamento.sum()}"
        )
        print(f"[DEBUG][SEPARAÇÃO] Filtradas por termos (total): {mask_termo.sum()}")
        print(
            f"[DEBUG][SEPARAÇÃO] Filtradas por status (tabela termos): {mask_status_filtravel.sum()}"
        )
        print(f"[DEBUG][SEPARAÇÃO] Vazias ignoradas: {mask_vazio.sum()}")
    
        # Adicionar metadados para todos os DataFrames
        for _df in (df_proc, df_filt):
            _df["data_processamento"] = datetime.now()
            _df["usuario_processamento"] = usuario or "desconhecido"
            _df["Filtrado"] = 0 if _df is df_proc else 1
    
        return df_proc, df_filt


def classificar_por_bandeira_e_termos(
    df: pd.DataFrame, engine: Engine, ec_id: str, contexto: str = "padrao"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    log_to_debug_file(f"[DEBUG][NORM] Iniciando normalizar_dataframe_vendas com {len(df)} linhas...")
    import unicodedata

    def norm(s):
        import unicodedata

        s = str(s) or ""
        s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("ASCII")
        s = s.replace("_", " ").replace("-", " ").upper().strip()
        return s

    mapa_bandeiras = bandeiras_por_ec(engine, str(ec_id), contexto)
    # Normaliza as bandeiras ativas para UPPER e sem acentos
    bandeiras_ativas = {
        norm(b) for b, ativo in mapa_bandeiras.items() if int(ativo or 0) == 1
    }
    # Normaliza os termos para UPPER e sem acentos
    termos = [
        norm(t["termo"]) if isinstance(t, dict) and "termo" in t else norm(t)
        for t in termos_listar(engine, str(ec_id), contexto)
    ]
    print("[DEBUG] termos normalizados:", termos)
    padrao_termos = (
        re.compile("|".join(map(re.escape, termos)), flags=re.IGNORECASE)
        if termos
        else None
    )

    def _texto(df):
        cols = [
            c
            for c in [
                "Resumo_da_operação",
                "Forma_de_pagamento",
                "Canal_de_venda",
                "Status",
                "Tipo_de_lançamento",
            ]
            if c in df.columns
        ]
        if not cols: return pd.Series("", index=df.index)
        # Optimized join using direct string concatenation
        res = df[cols[0]].astype(str).fillna("")
        for c in cols[1:]:
            res += " " + df[c].astype(str).fillna("")
        return res

    # Normaliza a coluna Bandeira antes de comparar
    if "Bandeira" in df.columns:
        col_bandeira = df["Bandeira"]
        if not col_bandeira.empty:
            col_bandeira_norm = col_bandeira.astype(str).map(norm)
            mask_bandeira_ok = col_bandeira_norm.isin(bandeiras_ativas)
        else:
            mask_bandeira_ok = pd.Series(False, index=df.index)
    else:
        mask_bandeira_ok = pd.Series(True, index=df.index)

    # Normaliza o texto de busca de termos
    if padrao_termos:
        log_to_debug_file("[DEBUG][NORM] Agregando colunas de texto para busca de termos...")
        texto = _texto(df)
        if not texto.empty:
            log_to_debug_file("[DEBUG][NORM] Aplicando normalização vetorial de texto...")
            # Vectorized normalization
            texto_norm = texto.str.normalize("NFKD").str.encode("ascii", errors="ignore").str.decode("ascii").str.upper().str.strip()
            log_to_debug_file("[DEBUG][NORM] Buscando termos no texto normalizado...")
            mask_termo = texto_norm.str.contains(padrao_termos, na=False)
        else:
            mask_termo = pd.Series(False, index=df.index)
    else:
        mask_termo = pd.Series(False, index=df.index)

    mask_filtrado = (~mask_bandeira_ok) | mask_termo

    df_filt = df.loc[mask_filtrado].copy()
    df_proc = df.loc[~mask_filtrado].copy()
    df_filt["Filtrado"] = 1
    df_proc["Filtrado"] = 0
    return df_proc, df_filt


def classificar_e_gravar_vendas(
    engine: Engine,
    df: pd.DataFrame,
    *,
    cliente_id: int,
    ec_id: str,
    contexto: str,
    usuario: str,
    arquivo_origem: str = "",
    processamentoid: str = None,
    progress_callback = None
) -> Dict[str, Any]:
    print(f"[RECORD][VENDAS] Colunas recebidas no DataFrame: {list(df.columns)}")
    
    try:
        with PerformanceTimer("RECORD", "Gravação Vendas (Bulk Insert)", {"rows": len(df), "contexto": contexto}):
            now = datetime.now()
            was_fresh = processamentoid is None

            if processamentoid is None:
                processamentoid, _ = processamento_gerar_novo_id(engine, ec_id, now)
                print(f"[RECORD][VENDAS] Gerado novo ID: {processamentoid}")
                processamento_salvar(
                    engine,
                    ec_id=ec_id,
                    cliente_id=cliente_id,
                    id_processamento=processamentoid,
                    descricao=f"Importação {contexto or '-'} ({arquivo_origem or 'arquivo'})",
                    data_processamento=now,
                )
            else:
                print(f"[RECORD][VENDAS] Usando processamentoid existente: {processamentoid}")

            # Garantir que df_proc e df_filt comecem definidos
            df_proc, df_filt = pd.DataFrame(), pd.DataFrame()

            # Se a coluna Filtrado não existe ou se queremos re-checkar (padrão)
            log_to_debug_file(f"[RECORD][VENDAS] Chamando normalizar_dataframe_vendas para {len(df)} linhas...")
            df_proc, df_filt = normalizar_dataframe_vendas(
                df, engine=engine, ec_id=ec_id, contexto=contexto
            )
            log_to_debug_file(f"[RECORD][VENDAS] -> Processar: {len(df_proc)} | Filtradas: {len(df_filt)}")

            for _df in (df_proc, df_filt):
                if _df is not None and not _df.empty:
                    _df["arquivo_origem"] = arquivo_origem or ""
                    _df["processamentoid"] = processamentoid
                    _df["cliente_id"] = int(cliente_id)
                    if "ec_id" not in _df.columns or _df["ec_id"].isna().all():
                        _df["ec_id"] = str(ec_id)

            # --- DEDUPLICAÇÃO EM MEMÓRIA (PYTHON) ---
            cols_ignorar = {"id", "data_processamento", "usuario_processamento", "arquivo_origem", "processamentoid"}
            n_proc, n_filt = len(df_proc), len(df_filt)

            if n_proc:
                cols_dedup_proc = [c for c in df_proc.columns if c not in cols_ignorar]
                len_antes = len(df_proc)
                df_proc = df_proc.drop_duplicates(subset=cols_dedup_proc).copy()
                n_proc = len(df_proc)
                if len_antes > n_proc:
                    print(f"[DEBUG][DEDUP] Removidas {len_antes - n_proc} duplicadas (Vendas Processadas) em memória.")
            
            print(f"[RECORD][VENDAS] Preparado para inserção bulk: {n_proc} linhas")

            if n_filt:
                cols_dedup_filt = [c for c in df_filt.columns if c not in cols_ignorar]
                len_antes = len(df_filt)
                df_filt = df_filt.drop_duplicates(subset=cols_dedup_filt).copy()
                n_filt = len(df_filt)
                if len_antes > n_filt:
                    print(f"[DEBUG][DEDUP] Removidas {len_antes - n_filt} duplicadas (Vendas Filtradas) em memória.")

            # Inserir dados nas respectivas tabelas
            if n_proc:
                if progress_callback: progress_callback(70, "Gravando vendas processadas...")
                log_to_debug_file(f"[RECORD][VENDAS] Chamando bulk_insert para {n_proc} vendas processadas...")
                vendas_processadas_bulk_insert(engine, df_proc, progress_callback=progress_callback)
            if n_filt:
                if progress_callback: progress_callback(85, "Gravando vendas filtradas...")
                print(f"[RECORD][VENDAS] Gravando {n_filt} vendas filtradas...")
                vendas_filtradas_bulk_insert(engine, df_filt, progress_callback=progress_callback)

            # Remover duplicadas
            if n_proc and not was_fresh:
                if progress_callback: progress_callback(90, "Removendo duplicadas SQL...")
                vendas_remover_duplicadas(engine, "vendas_processadas", processamentoid, df_proc.columns.tolist())
            elif n_proc and was_fresh:
                print(f"[DEBUG][DEDUP] Pulando remoção SQL de duplicadas para fresh import")
                if progress_callback: progress_callback(95, "Deduplicação concluída.")

            if n_filt and not was_fresh:
                vendas_remover_duplicadas(engine, "vendas_filtradas", processamentoid, df_filt.columns.tolist())

            print(f"[DEBUG][VENDAS] Processadas: {n_proc}, Filtradas: {n_filt}")

            return {
                "processadas": n_proc,
                "filtradas": n_filt,
                "diversas": 0,
                "total": n_proc + n_filt,
                "processamentoid": processamentoid,
            }

    except Exception as e:
        print(f"\n[RECORD][VENDAS] !!! ERRO FATAL NA GRAVAÇÃO !!!")
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e
