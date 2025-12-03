import panel as pn
import pandas as pd
from datetime import datetime
from conf.funcoesbd import fetch_all, _is_sqlite


def _remove_collate_if_sqlite(engine, sql: str) -> str:
    """Remove COLLATE clauses do SQL se for SQLite"""
    if _is_sqlite(engine):
        # Remove todas as ocorrências de COLLATE utf8mb4_0900_ai_ci
        import re

        sql = re.sub(r"\s+COLLATE\s+utf8mb4_0900_ai_ci", "", sql, flags=re.IGNORECASE)
    return sql


def _remove_update_alias_if_sqlite(engine, sql: str) -> str:
    """
    Remove alias de UPDATE statements para SQLite.
    MySQL: UPDATE vendas_calculos vc SET vc.column = value
    SQLite: UPDATE vendas_calculos SET column = value
    """
    if not _is_sqlite(engine):
        return sql

    import re

    # Remove alias do UPDATE (ex: "UPDATE vendas_calculos vc" -> "UPDATE vendas_calculos")
    sql = re.sub(
        r"UPDATE\s+(\w+)\s+\w+\s+SET", r"UPDATE \1 SET", sql, flags=re.IGNORECASE
    )

    # Remove prefixo do alias nas colunas (ex: "vc.tx_rr_calc" -> "tx_rr_calc")
    # Mas apenas nas linhas SET e WHERE
    sql = re.sub(r"\b\w+\.([\w_]+)\s*=", r"\1 =", sql)

    return sql


def _convert_update_join_for_sqlite(engine, sql: str) -> str:
    """
    Converte UPDATE ... JOIN ... SET (MySQL) para sintaxe compatível com SQLite.
    SQLite não suporta UPDATE JOIN, então usamos UPDATE com subquery.
    """
    if not _is_sqlite(engine):
        return sql

    import re

    # Pattern: UPDATE table1 alias1 JOIN ... SET ... WHERE ...
    # Converte para: UPDATE table1 SET ... WHERE rowid IN (SELECT rowid FROM table1 JOIN ...)

    # Para SQLite, a abordagem mais simples é reescrever manualmente cada query
    # Por ora, vamos identificar o padrão e converter dinamicamente

    # Se contém "UPDATE ... JOIN", precisa ser reescrito
    if re.search(r"UPDATE\s+\w+\s+\w+\s+JOIN", sql, re.IGNORECASE):
        # Cada query tem estrutura específica, então vamos tratá-las caso a caso
        # baseado em palavras-chave identificadoras

        # Caso 1: Update com taxas (JOIN taxas t)
        if "JOIN taxas t" in sql:
            return _convert_taxas_update_for_sqlite(sql)

        # Caso 2: Update com min_txs (agregação de mínima taxa - inclui min_txs_rr)
        elif (
            "min_txs" in sql
            or "MIN(vc2.tx_venda)" in sql
            or "MIN(vc2.tx_rr_venda)" in sql
        ):
            return _convert_min_tx_update_for_sqlite(sql)

        # Caso 3: Update com max_txs (agregação de máxima taxa)
        elif "max_txs" in sql or "MAX(vc2.tx_venda)" in sql:
            return _convert_max_tx_update_for_sqlite(sql)

        # Caso 4: Update simples com apenas vendas_processadas
        elif (
            "JOIN vendas_processadas vp ON vc.id_venda = vp.id" in sql
            and "JOIN taxas" not in sql
        ):
            return _convert_simple_join_update_for_sqlite(sql)

    return sql


def _convert_simple_join_update_for_sqlite(sql: str) -> str:
    """Converte UPDATE JOIN simples (apenas com vendas_processadas) para SQLite usando CTE"""
    import re

    # Extrair SET clause
    set_match = re.search(r"SET\s+(.+?)\s+WHERE", sql, re.DOTALL | re.IGNORECASE)
    if not set_match:
        return sql

    set_clause = set_match.group(1).strip()

    # Extrair WHERE clause
    where_match = re.search(r"WHERE\s+(.+)$", sql, re.DOTALL | re.IGNORECASE)
    where_clause = where_match.group(1).strip() if where_match else "1=1"

    # Ajustar SET clause: trocar vc. por vazio (já estamos no contexto de vendas_calculos)
    # e criar subqueries para valores que vem de vp
    set_clause_adjusted = set_clause
    set_clause_adjusted = re.sub(r"\bvc\.", "", set_clause_adjusted)

    # Construir query SQLite com CTE
    # A ideia é criar uma CTE que faça o JOIN e depois usar ela no UPDATE
    cte_sql = f"""
        WITH venda_data AS (
            SELECT 
                vc.rowid as vc_rowid,
                vp.Valor_da_venda,
                vc.tx_calc,
                vc.tx_venda,
                vc.vl_liq_venda,
                vc.tx_rr_calc,
                vc.vl_rr_venda,
                vc.calc_id,
                vc.calc_tipo
            FROM vendas_calculos vc
            JOIN vendas_processadas vp ON vc.id_venda = vp.id
        )
        UPDATE vendas_calculos
        SET
            {set_clause_adjusted}
        WHERE rowid IN (
            SELECT vc_rowid 
            FROM venda_data 
            WHERE {where_clause.replace('vc.', '')}
        )
        """

    # Substituir referências a vp.Valor_da_venda por subquery
    # Isso é complexo, então vamos fazer diferente:
    # Usar múltiplas subqueries inline

    # Para simplificar, gerar UPDATE com subquery inline para cada campo que precisa de vp
    if "vp.Valor_da_venda" in set_clause:
        # Precisa reescrever com subqueries
        # Exemplo: desc_calc = ... vp.Valor_da_venda ...
        # Se torna: desc_calc = ... (SELECT vp.Valor_da_venda FROM vendas_processadas vp WHERE vp.id = vendas_calculos.id_venda) ...

        set_clause_final = re.sub(
            r"vp\.Valor_da_venda",
            "(SELECT vp.Valor_da_venda FROM vendas_processadas vp WHERE vp.id = vendas_calculos.id_venda)",
            set_clause_adjusted,
        )

        final_sql = f"""
            UPDATE vendas_calculos
            SET
                {set_clause_final}
            WHERE {where_clause.replace('vc.', '')}
            """

        return final_sql

    return cte_sql


def _convert_taxas_update_for_sqlite(sql: str) -> str:
    """Converte UPDATE JOIN com tabela taxas para SQLite"""
    import re

    # Extrair parâmetros SET
    set_match = re.search(r"SET\s+(.+?)\s+WHERE", sql, re.DOTALL | re.IGNORECASE)
    if not set_match:
        return sql

    set_clause = set_match.group(1).strip()

    # Extrair condição WHERE final
    where_match = re.search(
        r"WHERE\s+vc\.calc_id\s*=\s*:calc_id\s+AND\s+vc\.calc_tipo\s*=\s*:calc_tipo",
        sql,
        re.IGNORECASE,
    )
    if not where_match:
        return sql

    # Construir query SQLite usando UPDATE com subquery
    sqlite_sql = f"""
        UPDATE vendas_calculos
        SET
            {set_clause}
        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
        AND EXISTS (
            SELECT 1
            FROM vendas_processadas vp
            JOIN taxas t ON t.ec = vp.ec_id 
                AND LOWER(t.contexto) = LOWER(vp.Adquirente)
                AND LOWER(t.bandeira) = LOWER(vp.Bandeira)
                AND LOWER(t.forma_pagamento) = LOWER(vp.Forma_de_pagamento)
                AND vp.data_processamento BETWEEN t.data_ini AND t.data_fim
            WHERE vendas_calculos.id_venda = vp.id
        )
        """

    # Ajustar referências de alias vc para vendas_calculos
    sqlite_sql = sqlite_sql.replace("vc.tx_calc", "tx_calc")
    sqlite_sql = sqlite_sql.replace("vc.desc_calc", "desc_calc")
    sqlite_sql = sqlite_sql.replace("vc.vl_liq_calc", "vl_liq_calc")
    sqlite_sql = sqlite_sql.replace("vc.perda", "perda")
    sqlite_sql = sqlite_sql.replace("vc.tx_venda", "tx_venda")
    sqlite_sql = sqlite_sql.replace("vc.vl_liq_venda", "vl_liq_venda")

    # Precisamos incluir os valores de t.taxa e vp.Valor_da_venda via subquery
    # Isso é complexo, melhor usar abordagem WITH CTE

    # Extrair lógica do SET para reconstruir com subqueries
    cte_sql = f"""
        WITH matched_records AS (
            SELECT 
                vc.rowid as vc_rowid,
                t.taxa,
                vp.Valor_da_venda,
                vc.tx_venda,
                vc.vl_liq_venda
            FROM vendas_calculos vc
            JOIN vendas_processadas vp ON vc.id_venda = vp.id
            JOIN taxas t ON t.ec = vp.ec_id 
                AND LOWER(t.contexto) = LOWER(vp.Adquirente)
                AND LOWER(t.bandeira) = LOWER(vp.Bandeira)
                AND LOWER(t.forma_pagamento) = LOWER(vp.Forma_de_pagamento)
                AND vp.data_processamento BETWEEN t.data_ini AND t.data_fim
            WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
        )
        UPDATE vendas_calculos
        SET
            tx_calc = (SELECT taxa FROM matched_records WHERE vc_rowid = vendas_calculos.rowid),
            desc_calc = (SELECT Valor_da_venda * taxa / 100 FROM matched_records WHERE vc_rowid = vendas_calculos.rowid),
            vl_liq_calc = (SELECT Valor_da_venda - (Valor_da_venda * taxa / 100) FROM matched_records WHERE vc_rowid = vendas_calculos.rowid),
            perda = (SELECT 
                CASE 
                    WHEN tx_venda IS NULL OR tx_venda = 0 THEN 0
                    ELSE vl_liq_venda - (Valor_da_venda - (Valor_da_venda * taxa / 100))
                END
                FROM matched_records WHERE vc_rowid = vendas_calculos.rowid)
        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
        AND rowid IN (SELECT vc_rowid FROM matched_records)
        """

    return cte_sql


def _convert_min_tx_update_for_sqlite(sql: str) -> str:
    """Converte UPDATE JOIN com MIN(tx_venda) ou MIN(tx_rr_venda) para SQLite"""
    import re

    # Extrair a subquery de agregação (min_txs ou min_txs_rr)
    subquery_match = re.search(
        r"JOIN\s*\(\s*(SELECT.+?)\)\s+(min_txs|min_txs_rr)",
        sql,
        re.DOTALL | re.IGNORECASE,
    )
    if not subquery_match:
        return sql

    aggregation_query = subquery_match.group(1).strip()
    alias_name = subquery_match.group(2)  # min_txs or min_txs_rr

    # Detectar se é MIN(tx_venda) ou MIN(tx_rr_venda)
    if "MIN(vc2.tx_rr_venda)" in aggregation_query:
        col_name = "min_tx_rr_venda"
        target_col = "tx_rr_calc"
    else:
        col_name = "min_tx_venda"
        target_col = "tx_calc"

    # Detectar a fórmula de periodo_ini para usar no WHERE
    periodo_pattern = (
        r"(strftime\('%Y', vp\.Data_da_venda\) \|\| '-01-01'|YEAR\(vp\.Data_da_venda\))"
    )
    periodo_match = re.search(periodo_pattern, sql)
    if periodo_match:
        periodo_formula = periodo_match.group(1)
    else:
        # Default
        periodo_formula = "strftime('%Y', vp.Data_da_venda) || '-01-01'"

    # Construir query SQLite usando CTE
    cte_sql = f"""
        WITH {alias_name} AS (
            {aggregation_query}
        )
        UPDATE vendas_calculos
        SET {target_col} = (
            SELECT {alias_name}.{col_name}
            FROM vendas_processadas vp
            JOIN {alias_name} 
                ON vp.ec_id = {alias_name}.ec_id
                AND LOWER(TRIM(vendas_calculos.bandeira)) = {alias_name}.bandeira
                AND LOWER(TRIM(vendas_calculos.forma_pagamento)) = {alias_name}.forma_pagamento
                AND {periodo_formula} = {alias_name}.periodo_ini
            WHERE vendas_calculos.id_venda = vp.id
            LIMIT 1
        )
        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
        AND EXISTS (
            SELECT 1
            FROM vendas_processadas vp
            JOIN {alias_name} 
                ON vp.ec_id = {alias_name}.ec_id
                AND LOWER(TRIM(vendas_calculos.bandeira)) = {alias_name}.bandeira
                AND LOWER(TRIM(vendas_calculos.forma_pagamento)) = {alias_name}.forma_pagamento
                AND {periodo_formula} = {alias_name}.periodo_ini
            WHERE vendas_calculos.id_venda = vp.id
        )
        """

    return cte_sql


def _convert_max_tx_update_for_sqlite(sql: str) -> str:
    """Converte UPDATE JOIN com MAX(tx_venda) para SQLite"""
    import re

    # Extrair a subquery de agregação
    subquery_match = re.search(
        r"JOIN\s+\((.+?)\)\s+max_txs", sql, re.DOTALL | re.IGNORECASE
    )
    if not subquery_match:
        return sql

    aggregation_query = subquery_match.group(1).strip()

    # Construir query SQLite usando CTE
    cte_sql = f"""
        WITH max_txs AS (
            {aggregation_query}
        )
        UPDATE vendas_calculos
        SET tx_calc = (
            SELECT max_txs.max_tx_venda
            FROM vendas_processadas vp
            JOIN max_txs 
                ON vp.ec_id = max_txs.ec_id
                AND LOWER(TRIM(vendas_calculos.bandeira)) = max_txs.bandeira
                AND LOWER(TRIM(vendas_calculos.forma_pagamento)) = max_txs.forma_pagamento
                AND strftime('%Y', vp.Data_da_venda) || '-01-01' = max_txs.periodo_ini
            WHERE vendas_calculos.id_venda = vp.id
            LIMIT 1
        )
        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
        AND EXISTS (
            SELECT 1
            FROM vendas_processadas vp
            JOIN max_txs 
                ON vp.ec_id = max_txs.ec_id
                AND LOWER(TRIM(vendas_calculos.bandeira)) = max_txs.bandeira
                AND LOWER(TRIM(vendas_calculos.forma_pagamento)) = max_txs.forma_pagamento
                AND strftime('%Y', vp.Data_da_venda) || '-01-01' = max_txs.periodo_ini
            WHERE vendas_calculos.id_venda = vp.id
        )
        """

    return cte_sql


# Painel de seleção de processamento e tipo de taxa
def make_calculos_view(engine):
    # 1. Dropdown de processamento
    processamentos = fetch_all(
        engine,
        """
        SELECT id_processamento, descricao, data_processamento
        FROM controle_processamentos
        ORDER BY data_processamento DESC, id_processamento DESC
        
        """,
    )

    # Converter data_processamento para datetime se for string
    for p in processamentos:
        if isinstance(p["data_processamento"], str):
            try:
                p["data_processamento"] = pd.to_datetime(p["data_processamento"])
            except:
                from datetime import datetime

                p["data_processamento"] = datetime.now()

    proc_opts = {
        f"{p['id_processamento']} - {p['descricao']} ({p['data_processamento']:%d/%m/%Y})": p[
            "id_processamento"
        ]
        for p in processamentos
    }
    proc_select = pn.widgets.Select(
        name="Processamento",
        options=list(proc_opts.keys()),
        value=(list(proc_opts.keys())[0] if proc_opts else None),
        width=400,
    )

    # 2. Checkbox para Taxa CAD
    usar_taxa_cad_checkbox = pn.widgets.Checkbox(
        name="Usar Taxa CAD quando disponível",
        value=False,
        width=300,
        styles={
            "fontWeight": "bold",
            "fontSize": "16px",
            "color": "#1976d2",
        },
        margin=(10, 0, 10, 0),
    )

    # 3. Select/radio para tipo de taxa (apenas Log)
    taxa_labels = [
        "Log Mensal",
        "Log Trimestral",
        "Log Semestral",
        "Log Anual",
    ]
    taxa_values = [
        "log_mensal",
        "log_trimestral",
        "log_semestral",
        "log_anual",
    ]
    taxa_select = pn.widgets.RadioBoxGroup(
        name="Tipo de Taxa (Log)",
        options=taxa_labels,
        value=taxa_labels[0],
        width=380,
        styles={
            "borderRadius": "6px",
            "fontWeight": "bold",
            "fontSize": "16px",
            "border": "2px solid #1976d2",
        },
    )

    # 4. Checkbox para Receba Rápido
    receba_rapido_checkbox = pn.widgets.Checkbox(
        name="Cliente tem Receba Rápido?",
        value=False,
        width=300,
        styles={
            "fontWeight": "bold",
            "fontSize": "16px",
            "color": "#1976d2",
        },
        margin=(10, 0, 10, 0),
    )

    # 4. Botão de preview
    btn_preview = pn.widgets.Button(
        name="🔍 Preview do Cálculo",
        button_type="light",
        width=200,
        height=48,
        styles={
            "borderRadius": "8px",
            "fontWeight": "bold",
            "fontSize": "16px",
        },
        margin=(10, 0, 10, 0),
        align="center",
    )

    # 5. Botão de processamento
    btn_processar = pn.widgets.Button(
        name="Calcular Taxas",
        button_type="primary",
        width=260,
        height=48,
        styles={
            "borderRadius": "8px",
            "fontWeight": "bold",
            "fontSize": "18px",
            "border": "2px solid #1976d2",
        },
        margin=(10, 0, 10, 0),
        align="center",
    )

    # 6. Mensagem de status
    status_msg = pn.pane.Alert("", alert_type="info", visible=False)

    # 7. Preview pane
    preview_pane = pn.pane.Markdown("", visible=False)

    # 8. Tabela de resultados (Tabulator)
    tabulator = pn.widgets.Tabulator(
        pd.DataFrame(), page_size=50, sizing_mode="stretch_width", height=350
    )
    resumo_tabulator = pn.widgets.Tabulator(
        pd.DataFrame(), page_size=1, sizing_mode="stretch_width", height=80
    )

    def preview_action(event=None):
        """Gera preview das estatísticas antes de calcular"""
        proc_key = proc_select.value
        if not proc_key:
            preview_pane.object = "⚠️ **Selecione um processamento primeiro.**"
            preview_pane.visible = True
            return

        proc_id = None
        for k, v in proc_opts.items():
            if k == proc_key:
                proc_id = v
                break

        if not proc_id:
            preview_pane.object = "⚠️ **Processamento inválido.**"
            preview_pane.visible = True
            return

        taxa_label_to_value = dict(zip(taxa_labels, taxa_values))
        tipo_taxa = taxa_label_to_value.get(taxa_select.value, "log_mensal")
        usar_taxa_cad = usar_taxa_cad_checkbox.value
        tem_receba_rapido = receba_rapido_checkbox.value

        try:
            from sqlalchemy import text

            with engine.connect() as conn:
                # Buscar vendas do processamento
                vendas = fetch_all(
                    engine,
                    """
                    SELECT id, Bandeira, Forma_de_pagamento, data_processamento, 
                           Valor_da_venda, Taxas_Perc, Taxas_RR, ec_id
                    FROM vendas_processadas 
                    WHERE processamentoid = :proc_id
                    """,
                    {"proc_id": proc_id},
                )

                if not vendas:
                    preview_pane.object = "⚠️ **Nenhuma venda encontrada para este processamento.**"
                    preview_pane.visible = True
                    return

                total_vendas = len(vendas)
                
                # Estatísticas gerais
                valores = [v.get("Valor_da_venda", 0) or 0 for v in vendas]
                valor_total = sum(valores)
                valor_medio = valor_total / total_vendas if total_vendas > 0 else 0

                # Verificar quantas terão taxa CAD
                vendas_com_cad = 0
                if usar_taxa_cad:
                    # Contar vendas que têm taxa cadastrada
                    for venda in vendas:
                        ec_id = venda.get("ec_id")
                        bandeira = venda.get("Bandeira", "")
                        forma_pgto = venda.get("Forma_de_pagamento", "")
                        data_proc = venda.get("data_processamento")

                        if ec_id and bandeira and forma_pgto and data_proc:
                            sql_taxa = text("""
                                SELECT COUNT(*) as cnt
                                FROM taxas t
                                WHERE t.ec = :ec_id
                                AND LOWER(t.bandeira) = LOWER(:bandeira)
                                AND LOWER(t.forma_pagamento) = LOWER(:forma_pgto)
                                AND :data_proc BETWEEN t.data_ini AND t.data_fim
                            """)
                            result = conn.execute(sql_taxa, {
                                "ec_id": ec_id,
                                "bandeira": bandeira,
                                "forma_pgto": forma_pgto,
                                "data_proc": data_proc
                            }).fetchone()
                            if result and result[0] > 0:
                                vendas_com_cad += 1

                vendas_com_log = total_vendas - vendas_com_cad if usar_taxa_cad else total_vendas

                # Estatísticas de taxas originais
                taxas_orig = [v.get("Taxas_Perc", 0) or 0 for v in vendas if v.get("Taxas_Perc")]
                taxas_rr_orig = [v.get("Taxas_RR", 0) or 0 for v in vendas if v.get("Taxas_RR")]

                min_taxa_orig = min(taxas_orig) if taxas_orig else 0
                max_taxa_orig = max(taxas_orig) if taxas_orig else 0
                media_taxa_orig = sum(taxas_orig) / len(taxas_orig) if taxas_orig else 0

                # Montar preview
                preview_text = f"""
### 📊 Preview do Cálculo de Taxas

**Processamento:** {proc_id}  
**Tipo de Taxa:** {tipo_taxa.replace('_', ' ').title()}  
**Usar Taxa CAD:** {'✅ Sim' if usar_taxa_cad else '❌ Não'}  
**Receba Rápido:** {'✅ Sim' if tem_receba_rapido else '❌ Não'}

---

#### 📈 Estatísticas das Vendas

- **Total de vendas:** {total_vendas:,}
- **Valor total:** R$ {valor_total:,.2f}
- **Valor médio:** R$ {valor_medio:,.2f}

#### 💰 Taxas Originais (do arquivo)

- **Taxa mínima:** {min_taxa_orig:.2f}%
- **Taxa máxima:** {max_taxa_orig:.2f}%
- **Taxa média:** {media_taxa_orig:.2f}%

#### 🎯 Estratégia de Cálculo

"""
                if usar_taxa_cad:
                    preview_text += f"""
- **Vendas com Taxa CAD:** {vendas_com_cad:,} ({vendas_com_cad/total_vendas*100:.1f}%)
  - Estas vendas usarão a taxa cadastrada na tabela `taxas`
  
- **Vendas com Log ({tipo_taxa.replace('_', ' ').title()}):** {vendas_com_log:,} ({vendas_com_log/total_vendas*100:.1f}%)
  - Estas vendas usarão a menor taxa do período (lógica de log)
"""
                else:
                    preview_text += f"""
- **Todas as vendas usarão Log ({tipo_taxa.replace('_', ' ').title()}):** {total_vendas:,}
  - Será aplicada a menor taxa do período para cada venda
"""

                if tem_receba_rapido:
                    preview_text += f"""
#### 💳 Receba Rápido

- **Taxas RR serão calculadas** para todas as vendas
- **Total de vendas com Taxas_RR:** {len(taxas_rr_orig):,}
"""
                else:
                    preview_text += f"""
#### 💳 Receba Rápido

- **Taxas RR serão zeradas** (Receba Rápido desativado)
"""

                preview_text += f"""
---

**⚠️ Atenção:** Este é apenas um preview. Clique em **Calcular Taxas** para executar o cálculo real.
"""

                preview_pane.object = preview_text
                preview_pane.visible = True

        except Exception as e:
            preview_pane.object = f"❌ **Erro ao gerar preview:** {e}"
            preview_pane.visible = True

    def processar_action(event=None):
        def processamento_longo():
            import datetime
            from sqlalchemy import text

            print(
                "[DEBUG] Iniciando processamento de cálculo de taxas (modo SQL massivo)..."
            )
            status_msg.visible = True
            status_msg.alert_type = "info"
            status_msg.object = "Processando..."
            proc_key = proc_select.value
            if not proc_key:
                status_msg.object = "Selecione um processamento."
                status_msg.alert_type = "warning"
                return
            # Extrair apenas o id_processamento numérico para calc_id
            proc_id = None
            for k, v in proc_opts.items():
                if k == proc_key:
                    proc_id = v
                    break
            if not proc_id:
                status_msg.object = "Processamento inválido."
                status_msg.alert_type = "danger"
                return
            taxa_label_to_value = dict(zip(taxa_labels, taxa_values))
            tipo_taxa = taxa_label_to_value.get(taxa_select.value, "log_mensal")
            usar_taxa_cad = usar_taxa_cad_checkbox.value
            tem_receba_rapido = receba_rapido_checkbox.value
            usuario_logado = "sistema"  # Troque para o usuário real se disponível
            data_atual = datetime.datetime.now()

            print(f"[DEBUG] Receba Rápido ativo: {tem_receba_rapido}")

            # Buscar vendas processadas com informações de EC e contexto
            print("[DEBUG] Buscando vendas processadas e contextos do processamento...")
            vendas = fetch_all(
                engine,
                """
                SELECT id, Bandeira, Forma_de_pagamento, data_processamento, 
                       Valor_da_venda, Valor_líquido_da_venda, Quantidade_de_parcelas, 
                       ec_id, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR
                FROM vendas_processadas 
                WHERE processamentoid = :proc_id
                ORDER BY data_processamento, id
                """,
                {"proc_id": proc_id},
            )
            print(f"[DEBUG] {len(vendas)} vendas encontradas.")
            if not vendas:
                status_msg.object = "Nenhuma venda encontrada para o processamento."
                status_msg.alert_type = "warning"
                return

            # Debug: contagem antes do delete
            with engine.begin() as conn:
                count_before = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(f"[DEBUG] vendas_calculos antes do delete: {count_before}")

            # Montar lista de inserts com campos de cálculo nulos
            print("[DEBUG] Preparando inserts na tabela vendas_calculos...")
            insert_sql = text(
                """
                INSERT INTO vendas_calculos (
                    id_venda, calc_id, calc_tipo, calc_usuario, bandeira, forma_pagamento, calc_data,
                    vl_venda, tx_venda, desc_venda, vl_liq_venda,
                    tx_rr_venda, vl_rr_venda,
                    tx_calc, desc_calc, vl_liq_calc, tx_rr_calc, vl_rr_calc, perda_rr
                ) VALUES (
                    :id_venda, :calc_id, :calc_tipo, :calc_usuario, :bandeira, :forma_pagamento, :calc_data,
                    :vl_venda, :tx_venda, :desc_venda, :vl_liq_venda,
                    :tx_rr_venda, :vl_rr_venda,
                    NULL, NULL, NULL, NULL, NULL, NULL
                )
                """
            )
            params_list = []
            for idx, row in enumerate(vendas):
                vl_venda = row.get("Valor_da_venda", 0) or 0
                tx_venda = row.get("Taxas_Perc", 0) or 0
                tx_rr_venda = row.get("Taxas_RR", 0) or 0

                # Forçar cálculo do desc_venda e vl_rr_venda
                desc_venda_calc = vl_venda * tx_venda / 100
                vl_rr_venda_calc = vl_venda * tx_rr_venda / 100

                # Forçar cálculo do vl_liq_venda
                vl_liq_venda_calc = vl_venda - desc_venda_calc

                params = {
                    "id_venda": row.get("id"),
                    "calc_id": proc_id,
                    "calc_tipo": tipo_taxa,
                    "calc_usuario": usuario_logado,
                    "bandeira": row.get("Bandeira"),
                    "forma_pagamento": row.get("Forma_de_pagamento"),
                    "calc_data": data_atual,
                    "vl_venda": vl_venda,
                    "tx_venda": tx_venda,
                    "desc_venda": desc_venda_calc,
                    "vl_liq_venda": vl_liq_venda_calc,
                    "tx_rr_venda": tx_rr_venda,
                    "vl_rr_venda": vl_rr_venda_calc,
                }
                params_list.append(params)

            if params_list:
                print("[DEBUG] Exemplo de params para insert:", params_list[0])
            batch_size = 1000
            total = len(params_list)
            print(f"[DEBUG] Executando insert em lotes de {batch_size} registros...")
            with engine.begin() as conn:
                # Limpar vendas_calculos para este processamento/tipo_taxa antes de inserir
                delete_sql = text(
                    """
                    DELETE FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                """
                )
                conn.execute(delete_sql, {"calc_id": proc_id, "calc_tipo": tipo_taxa})
                for i in range(0, total, batch_size):
                    batch = params_list[i : i + batch_size]
                    conn.execute(insert_sql, batch)
                    print(
                        f"[DEBUG] Insertado {min(i+batch_size, total)}/{total} registros..."
                    )
                    status_msg.object = f"Processando... {min(i+batch_size, total)}/{total} registros inseridos."
                # Debug: contagem após insert
                count_after = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(f"[DEBUG] vendas_calculos após insert: {count_after}")

                # Debug: contar vendas com tx_venda = 0 ou NULL
                count_tx_zero = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND (tx_venda IS NULL OR tx_venda = 0)"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(f"[DEBUG] Vendas com tx_venda = 0 ou NULL: {count_tx_zero}")
                if count_tx_zero > 0:
                    print(
                        f"[DEBUG] ⚠️  Essas {count_tx_zero} vendas terão perda = 0 (sem taxa original, não há perda real)"
                    )

                # Atualizar taxas e valores via UPDATE JOIN, corrigindo collation
                print("[DEBUG] Executando UPDATE JOIN para calcular taxas...")
                print(f"[DEBUG] Usar Taxa CAD: {usar_taxa_cad}, Tipo Log: {tipo_taxa}")
                
                # Se checkbox CAD estiver marcado, primeiro tentar aplicar taxa CAD
                if usar_taxa_cad:
                    print("[DEBUG] Aplicando Taxa CAD primeiro...")
                    update_sql_raw = f"""
                        UPDATE vendas_calculos vc
                        JOIN vendas_processadas vp ON vc.id_venda = vp.id
                        JOIN taxas t ON t.ec = vp.ec_id 
                            AND LOWER(t.contexto) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Adquirente) COLLATE utf8mb4_0900_ai_ci
                            AND LOWER(t.bandeira) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Bandeira) COLLATE utf8mb4_0900_ai_ci
                            AND LOWER(t.forma_pagamento) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Forma_de_pagamento) COLLATE utf8mb4_0900_ai_ci
                            AND vp.data_processamento BETWEEN t.data_ini AND t.data_fim
                        SET
                            vc.tx_calc = t.taxa,
                            vc.desc_calc = vp.Valor_da_venda * t.taxa / 100,
                            vc.vl_liq_calc = vp.Valor_da_venda - (vp.Valor_da_venda * t.taxa / 100),
                            vc.perda = CASE 
                                WHEN vc.tx_venda IS NULL OR vc.tx_venda = 0 THEN 0
                                ELSE vc.vl_liq_venda - (vp.Valor_da_venda - (vp.Valor_da_venda * t.taxa / 100))
                            END
                        WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                        """
                    # Apply both COLLATE removal and UPDATE JOIN conversion for SQLite
                    update_sql_processed = _remove_collate_if_sqlite(
                        engine, update_sql_raw
                    )
                    update_sql_processed = _convert_update_join_for_sqlite(
                        engine, update_sql_processed
                    )
                    update_sql = text(update_sql_processed)
                    conn.execute(
                        update_sql,
                        {
                            "calc_id": proc_id,
                            "calc_tipo": tipo_taxa,
                        },
                    )

                    # Debug: estatísticas de perda após CAD
                    stats_cad = conn.execute(
                        text(
                            """
                            SELECT 
                                COUNT(*) as total,
                                SUM(CASE WHEN tx_calc IS NOT NULL THEN 1 ELSE 0 END) as com_taxa_cad,
                                SUM(CASE WHEN tx_calc IS NULL THEN 1 ELSE 0 END) as sem_taxa_cad
                            FROM vendas_calculos 
                            WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                            """
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).fetchone()
                    print(f"[DEBUG] Estatísticas após Taxa CAD:")
                    print(f"  • Total de vendas: {stats_cad[0]}")
                    print(f"  • Com taxa CAD encontrada: {stats_cad[1]}")
                    print(f"  • Sem taxa CAD (será aplicado Log): {stats_cad[2]}")

                    # Atualizar taxas RR (Receba Rápido) para vendas com CAD
                    if tem_receba_rapido:
                        print("[DEBUG] Atualizando taxas RR para vendas com CAD...")
                        update_rr_sql_raw = f"""
                            UPDATE vendas_calculos vc
                            JOIN vendas_processadas vp ON vc.id_venda = vp.id
                            JOIN taxas t ON t.ec = vp.ec_id 
                                AND LOWER(t.contexto) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Adquirente) COLLATE utf8mb4_0900_ai_ci
                                AND LOWER(t.bandeira) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Bandeira) COLLATE utf8mb4_0900_ai_ci
                                AND LOWER(t.forma_pagamento) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Forma_de_pagamento) COLLATE utf8mb4_0900_ai_ci
                                AND vp.data_processamento BETWEEN t.data_ini AND t.data_fim
                            SET
                                vc.tx_rr_calc = COALESCE(t.taxa_rr, t.taxa),
                                vc.vl_rr_calc = vp.Valor_da_venda * COALESCE(t.taxa_rr, t.taxa) / 100,
                                vc.perda_rr = CASE 
                                    WHEN vc.vl_rr_venda IS NOT NULL AND (vp.Valor_da_venda * COALESCE(t.taxa_rr, t.taxa) / 100) IS NOT NULL 
                                    THEN (vp.Valor_da_venda * COALESCE(t.taxa_rr, t.taxa) / 100) - vc.vl_rr_venda
                                    ELSE NULL 
                                END
                            WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                            AND vc.tx_calc IS NOT NULL
                            """
                        update_rr_sql_processed = _remove_collate_if_sqlite(
                            engine, update_rr_sql_raw
                        )
                        update_rr_sql_processed = _convert_update_join_for_sqlite(
                            engine, update_rr_sql_processed
                        )
                        update_rr_sql = text(update_rr_sql_processed)
                        conn.execute(
                            update_rr_sql,
                            {
                                "calc_id": proc_id,
                                "calc_tipo": tipo_taxa,
                            },
                        )

                # Agora aplicar lógica de LOG para vendas que não têm tx_calc (se usar_taxa_cad) ou todas (se não usar)
                # Se usar_taxa_cad, só aplicar LOG onde tx_calc IS NULL
                # Se não usar_taxa_cad, aplicar LOG em todas
                aplicar_log = True
                if usar_taxa_cad:
                    print("[DEBUG] Aplicando lógica de Log para vendas sem Taxa CAD...")
                else:
                    print(f"[DEBUG] Aplicando lógica de Log ({tipo_taxa}) para todas as vendas...")
                
                if aplicar_log:
                    # Lógica para tipos log: aplicar menor taxa das vendas_calculos do período
                    # Compatibilidade MySQL/SQLite
                    if _is_sqlite(engine):
                        # SQLite - usar strftime
                        if tipo_taxa == "log_mensal":
                            periodo_ini_sql = "strftime('%Y-%m-01', vp.Data_da_venda)"
                            periodo_fim_sql = "date(vp.Data_da_venda, 'start of month', '+1 month', '-1 day')"
                        elif tipo_taxa == "log_trimestral":
                            periodo_ini_sql = "date(vp.Data_da_venda, 'start of month', '-' || (CAST(strftime('%m', vp.Data_da_venda) AS INTEGER) - 1) % 3 || ' months')"
                            periodo_fim_sql = "date(vp.Data_da_venda, 'start of month', '-' || (CAST(strftime('%m', vp.Data_da_venda) AS INTEGER) - 1) % 3 || ' months', '+3 months', '-1 day')"
                        elif tipo_taxa == "log_semestral":
                            periodo_ini_sql = "CASE WHEN CAST(strftime('%m', vp.Data_da_venda) AS INTEGER) <= 6 THEN strftime('%Y', vp.Data_da_venda) || '-01-01' ELSE strftime('%Y', vp.Data_da_venda) || '-07-01' END"
                            periodo_fim_sql = "CASE WHEN CAST(strftime('%m', vp.Data_da_venda) AS INTEGER) <= 6 THEN strftime('%Y', vp.Data_da_venda) || '-06-30' ELSE strftime('%Y', vp.Data_da_venda) || '-12-31' END"
                        elif tipo_taxa == "log_anual":
                            periodo_ini_sql = (
                                "strftime('%Y', vp.Data_da_venda) || '-01-01'"
                            )
                            periodo_fim_sql = (
                                "strftime('%Y', vp.Data_da_venda) || '-12-31'"
                            )
                        else:
                            periodo_ini_sql = "vp.Data_da_venda"
                            periodo_fim_sql = "vp.Data_da_venda"
                    else:
                        # MySQL - usar DATE_FORMAT e CONCAT
                        if tipo_taxa == "log_mensal":
                            periodo_ini_sql = (
                                "DATE_FORMAT(vp.Data_da_venda, '%Y-%m-01')"
                            )
                            periodo_fim_sql = "LAST_DAY(vp.Data_da_venda)"
                        elif tipo_taxa == "log_trimestral":
                            periodo_ini_sql = "DATE_FORMAT(DATE_SUB(vp.Data_da_venda, INTERVAL (MONTH(vp.Data_da_venda)-1)%3 MONTH), '%Y-%m-01')"
                            periodo_fim_sql = "LAST_DAY(DATE_ADD(DATE_SUB(vp.Data_da_venda, INTERVAL (MONTH(vp.Data_da_venda)-1)%3 MONTH), INTERVAL 2 MONTH))"
                        elif tipo_taxa == "log_semestral":
                            periodo_ini_sql = "CASE WHEN MONTH(vp.Data_da_venda) <= 6 THEN CONCAT(YEAR(vp.Data_da_venda), '-01-01') ELSE CONCAT(YEAR(vp.Data_da_venda), '-07-01') END"
                            periodo_fim_sql = "CASE WHEN MONTH(vp.Data_da_venda) <= 6 THEN CONCAT(YEAR(vp.Data_da_venda), '-06-30') ELSE CONCAT(YEAR(vp.Data_da_venda), '-12-31') END"
                        elif tipo_taxa == "log_anual":
                            periodo_ini_sql = "CONCAT(YEAR(vp.Data_da_venda), '-01-01')"
                            periodo_fim_sql = "CONCAT(YEAR(vp.Data_da_venda), '-12-31')"
                        else:
                            periodo_ini_sql = "vp.Data_da_venda"
                            periodo_fim_sql = "vp.Data_da_venda"

                    # Primeiro UPDATE: preenche tx_calc com a menor tx_venda do período, usando derived table para evitar erro 1093
                    # Ajuste: usar vp2.data_processamento no subselect para periodo_ini
                    periodo_ini_sql_sub = periodo_ini_sql.replace("vp.", "vp2.")

                    # Debug: verificar os dados agregados
                    debug_sql_raw = f"""
                        SELECT
                            vp2.ec_id,
                            LOWER(TRIM(vc2.bandeira)) COLLATE utf8mb4_0900_ai_ci AS bandeira,
                            LOWER(TRIM(vc2.forma_pagamento)) COLLATE utf8mb4_0900_ai_ci AS forma_pagamento,
                            {periodo_ini_sql_sub} AS periodo_ini,
                            MIN(vc2.tx_venda) AS min_tx_venda,
                            COUNT(*) as qtd
                        FROM vendas_calculos vc2
                        JOIN vendas_processadas vp2 ON vc2.id_venda = vp2.id
                        WHERE vc2.calc_id = :calc_id AND vc2.calc_tipo = :calc_tipo
                        AND vc2.tx_venda IS NOT NULL AND vc2.tx_venda > 0
                        GROUP BY vp2.ec_id, LOWER(TRIM(vc2.bandeira)), LOWER(TRIM(vc2.forma_pagamento)), periodo_ini
                        LIMIT 5
                        """
                    debug_sql = text(_remove_collate_if_sqlite(engine, debug_sql_raw))
                    debug_result = conn.execute(
                        debug_sql, {"calc_id": proc_id, "calc_tipo": tipo_taxa}
                    )
                    print("[DEBUG] Primeiros 5 grupos agregados:")
                    for row in debug_result:
                        print(
                            f"  ec_id={row[0]}, bandeira={row[1]}, forma={row[2]}, periodo={row[3]}, min_tx={row[4]}, qtd={row[5]}"
                        )

                    # Condição adicional: se usar_taxa_cad, só atualizar onde tx_calc IS NULL
                    condicao_tx_calc = "AND vc.tx_calc IS NULL" if usar_taxa_cad else ""
                    
                    update_tx_sql_raw = f"""
                        UPDATE vendas_calculos vc
                        JOIN vendas_processadas vp ON vc.id_venda = vp.id
                        JOIN (
                            SELECT
                                vp2.ec_id,
                                LOWER(TRIM(vc2.bandeira)) COLLATE utf8mb4_0900_ai_ci AS bandeira,
                                LOWER(TRIM(vc2.forma_pagamento)) COLLATE utf8mb4_0900_ai_ci AS forma_pagamento,
                                {periodo_ini_sql_sub} AS periodo_ini,
                                MIN(vc2.tx_venda) AS min_tx_venda
                            FROM vendas_calculos vc2
                            JOIN vendas_processadas vp2 ON vc2.id_venda = vp2.id
                            WHERE vc2.calc_id = :calc_id AND vc2.calc_tipo = :calc_tipo
                            AND vc2.tx_venda IS NOT NULL AND vc2.tx_venda > 0
                            GROUP BY vp2.ec_id, LOWER(TRIM(vc2.bandeira)), LOWER(TRIM(vc2.forma_pagamento)), periodo_ini
                        ) min_txs
                        ON vp.ec_id = min_txs.ec_id
                        AND LOWER(TRIM(vc.bandeira)) COLLATE utf8mb4_0900_ai_ci = min_txs.bandeira
                        AND LOWER(TRIM(vc.forma_pagamento)) COLLATE utf8mb4_0900_ai_ci = min_txs.forma_pagamento
                        AND {periodo_ini_sql} = min_txs.periodo_ini
                        SET vc.tx_calc = min_txs.min_tx_venda
                        WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                        {condicao_tx_calc}
                        """
                    update_tx_sql_processed = _remove_collate_if_sqlite(
                        engine, update_tx_sql_raw
                    )
                    update_tx_sql_processed = _convert_update_join_for_sqlite(
                        engine, update_tx_sql_processed
                    )
                    update_tx_sql = text(update_tx_sql_processed)
                    result = conn.execute(
                        update_tx_sql,
                        {
                            "calc_id": proc_id,
                            "calc_tipo": tipo_taxa,
                        },
                    )
                    print(f"[DEBUG] UPDATE tx_calc affected rows: {result.rowcount}")
                    # Segundo UPDATE: preenche desc_calc, vl_liq_calc e perda (desc_calc - desc_venda)
                    # Atualizar todas as vendas que têm tx_calc (tanto CAD quanto LOG já preencheram)
                    update_desc_sql_raw = """
                        UPDATE vendas_calculos vc
                        JOIN vendas_processadas vp ON vc.id_venda = vp.id
                        SET
                            vc.desc_calc = CASE WHEN vc.tx_calc IS NOT NULL THEN vp.Valor_da_venda * vc.tx_calc / 100 ELSE NULL END,
                            vc.vl_liq_calc = CASE WHEN vc.tx_calc IS NOT NULL THEN vp.Valor_da_venda - (vp.Valor_da_venda * vc.tx_calc / 100) ELSE NULL END,
                            vc.perda = CASE 
                                WHEN vc.tx_calc IS NULL THEN NULL
                                WHEN vc.tx_venda IS NULL OR vc.tx_venda = 0 THEN 0
                                ELSE vc.vl_liq_venda - (vp.Valor_da_venda - (vp.Valor_da_venda * vc.tx_calc / 100))
                            END
                        WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                        AND vc.tx_calc IS NOT NULL
                        """
                    update_desc_sql_processed = _convert_update_join_for_sqlite(
                        engine, update_desc_sql_raw
                    )
                    update_desc_sql = text(update_desc_sql_processed)
                    result2 = conn.execute(
                        update_desc_sql,
                        {
                            "calc_id": proc_id,
                            "calc_tipo": tipo_taxa,
                        },
                    )
                    print(
                        f"[DEBUG] UPDATE desc_calc/vl_liq_calc/perda affected rows: {result2.rowcount}"
                    )

                    # Debug: estatísticas de perda para LOG
                    stats = conn.execute(
                        text(
                            """
                            SELECT 
                                COUNT(*) as total,
                                SUM(CASE WHEN perda = 0 THEN 1 ELSE 0 END) as com_perda_zero,
                                SUM(CASE WHEN perda > 0 THEN 1 ELSE 0 END) as com_perda_positiva,
                                SUM(CASE WHEN perda < 0 THEN 1 ELSE 0 END) as com_perda_negativa,
                                SUM(CASE WHEN perda IS NULL THEN 1 ELSE 0 END) as sem_perda_calculada
                            FROM vendas_calculos 
                            WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                            """
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).fetchone()
                    print(f"[DEBUG] Estatísticas de Perda (Taxa {tipo_taxa.upper()}):")
                    print(f"  • Total de vendas: {stats[0]}")
                    print(f"  • Perda = 0 (sem taxa original): {stats[1]}")
                    print(f"  • Perda > 0 (cobrado a mais): {stats[2]}")
                    print(f"  • Perda < 0 (cobrado a menos): {stats[3]}")
                    print(f"  • Sem cálculo (tx_calc não encontrado): {stats[4]}")

                    # Terceiro UPDATE para LOG: preencher taxas RR usando mesma lógica de menor taxa
                    print(
                        f"[DEBUG] Atualizando taxas RR para LOG - Receba Rápido ativo: {tem_receba_rapido}"
                    )
                    if tem_receba_rapido:
                        # Primeiro: atualizar tx_rr_calc com a menor taxa RR do período
                        # Se usar_taxa_cad, só atualizar onde tx_rr_calc ainda não foi preenchido pelo CAD
                        condicao_rr = "AND (vc.tx_rr_calc IS NULL OR vc.tx_rr_calc = 0)" if usar_taxa_cad else ""
                        
                        periodo_ini_sql_sub_rr = periodo_ini_sql.replace("vp.", "vp2.")
                        update_tx_rr_sql_raw = f"""
                            UPDATE vendas_calculos vc
                            JOIN vendas_processadas vp ON vc.id_venda = vp.id
                            JOIN (
                                SELECT
                                    vp2.ec_id,
                                    LOWER(TRIM(vc2.bandeira)) COLLATE utf8mb4_0900_ai_ci AS bandeira,
                                    LOWER(TRIM(vc2.forma_pagamento)) COLLATE utf8mb4_0900_ai_ci AS forma_pagamento,
                                    {periodo_ini_sql_sub_rr} AS periodo_ini,
                                    MIN(vc2.tx_rr_venda) AS min_tx_rr_venda
                                FROM vendas_calculos vc2
                                JOIN vendas_processadas vp2 ON vc2.id_venda = vp2.id
                                WHERE vc2.calc_id = :calc_id AND vc2.calc_tipo = :calc_tipo 
                                AND vc2.tx_rr_venda IS NOT NULL AND vc2.tx_rr_venda > 0
                                GROUP BY vp2.ec_id, LOWER(TRIM(vc2.bandeira)), LOWER(TRIM(vc2.forma_pagamento)), periodo_ini
                            ) min_txs_rr
                            ON vp.ec_id = min_txs_rr.ec_id
                            AND LOWER(TRIM(vc.bandeira)) COLLATE utf8mb4_0900_ai_ci = min_txs_rr.bandeira
                            AND LOWER(TRIM(vc.forma_pagamento)) COLLATE utf8mb4_0900_ai_ci = min_txs_rr.forma_pagamento
                            AND {periodo_ini_sql} = min_txs_rr.periodo_ini
                            SET vc.tx_rr_calc = min_txs_rr.min_tx_rr_venda
                            WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                            {condicao_rr}
                            """
                        update_tx_rr_sql_processed = _remove_collate_if_sqlite(
                            engine, update_tx_rr_sql_raw
                        )
                        update_tx_rr_sql_processed = _convert_update_join_for_sqlite(
                            engine, update_tx_rr_sql_processed
                        )
                        update_tx_rr_sql = text(update_tx_rr_sql_processed)
                        result_tx_rr = conn.execute(
                            update_tx_rr_sql,
                            {
                                "calc_id": proc_id,
                                "calc_tipo": tipo_taxa,
                            },
                        )
                        print(
                            f"[DEBUG] UPDATE tx_rr_calc affected rows: {result_tx_rr.rowcount}"
                        )

                        # Segundo: atualizar vl_rr_calc e perda_rr baseado na tx_rr_calc
                        # Se usar_taxa_cad, só atualizar onde tx_rr_calc foi preenchido pelo LOG
                        condicao_rr_calc = "AND (vc.tx_rr_calc IS NOT NULL AND (vc.tx_rr_calc != COALESCE((SELECT t2.taxa_rr FROM taxas t2 JOIN vendas_processadas vp2 ON t2.ec = vp2.ec_id WHERE vp2.id = vc.id_venda LIMIT 1), 0)))" if usar_taxa_cad else "AND vc.tx_rr_calc IS NOT NULL"
                        # Simplificando: se usar_taxa_cad, só atualizar onde tx_rr_calc foi preenchido pelo LOG (não pelo CAD)
                        # Vamos usar uma abordagem mais simples: atualizar todos que têm tx_rr_calc, mas só se não foi preenchido pelo CAD
                        # Na verdade, vamos atualizar todos que têm tx_rr_calc, pois o CAD já preencheu os seus
                        update_rr_calc_sql_raw = """
                            UPDATE vendas_calculos vc
                            JOIN vendas_processadas vp ON vc.id_venda = vp.id
                            SET
                                vc.vl_rr_calc = CASE WHEN vc.tx_rr_calc IS NOT NULL THEN vp.Valor_da_venda * vc.tx_rr_calc / 100 ELSE NULL END,
                                vc.perda_rr = CASE 
                                    WHEN vc.tx_rr_calc IS NOT NULL AND vc.vl_rr_venda IS NOT NULL 
                                    THEN (vp.Valor_da_venda * vc.tx_rr_calc / 100) - vc.vl_rr_venda
                                    ELSE NULL 
                                END
                            WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo AND vc.tx_rr_calc IS NOT NULL
                            """
                        update_rr_calc_sql_processed = _convert_update_join_for_sqlite(
                            engine, update_rr_calc_sql_raw
                        )
                        update_rr_calc_sql = text(update_rr_calc_sql_processed)
                        result_calc = conn.execute(
                            update_rr_calc_sql,
                            {
                                "calc_id": proc_id,
                                "calc_tipo": tipo_taxa,
                            },
                        )
                        print(
                            f"[DEBUG] UPDATE vl_rr_calc/perda_rr affected rows: {result_calc.rowcount}"
                        )
                        update_rr_log_sql = None  # Não usar a query anterior
                    else:
                        # Se não tem Receba Rápido, zerar os campos RR apenas onde não foram preenchidos pelo CAD
                        if usar_taxa_cad:
                            # Zerar apenas onde tx_rr_calc não foi preenchido pelo CAD
                            update_rr_log_sql_raw = """
                                UPDATE vendas_calculos vc
                                SET
                                    vc.tx_rr_calc = 0,
                                    vc.vl_rr_calc = 0,
                                    vc.perda_rr = 0
                                WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                                AND (vc.tx_rr_calc IS NULL OR vc.tx_rr_calc = 0)
                                """
                        else:
                            # Zerar todas
                            update_rr_log_sql_raw = """
                                UPDATE vendas_calculos vc
                                SET
                                    vc.tx_rr_calc = 0,
                                    vc.vl_rr_calc = 0,
                                    vc.perda_rr = 0
                                WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                                """
                        update_rr_log_sql = text(
                            _remove_update_alias_if_sqlite(
                                engine, update_rr_log_sql_raw
                            )
                        )
                        result3 = conn.execute(
                            update_rr_log_sql,
                            {
                                "calc_id": proc_id,
                                "calc_tipo": tipo_taxa,
                            },
                        )
                        print(
                            f"[DEBUG] UPDATE taxas RR (zerar) affected rows: {result3.rowcount}"
                        )

                    # Debug adicional: verificar se existem dados de tx_rr_venda
                    debug_count = conn.execute(
                        text(
                            "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_rr_venda IS NOT NULL AND tx_rr_venda > 0"
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).scalar()
                    print(f"[DEBUG] Registros com tx_rr_venda válidos: {debug_count}")

                    # Debug: verificar se tx_rr_calc foi preenchido
                    debug_calc = conn.execute(
                        text(
                            "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_rr_calc IS NOT NULL AND tx_rr_calc > 0"
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).scalar()
                    print(f"[DEBUG] Registros com tx_rr_calc preenchidos: {debug_calc}")
                print("[DEBUG] UPDATE JOIN finalizado.")

            # Buscar resultados atualizados para exibir
            print("[DEBUG] Buscando resultados atualizados para exibir...")
            df_result = pd.read_sql(
                text(
                    """
                    SELECT vc.*, vp.Bandeira, vp.Forma_de_pagamento, vp.data_processamento, vp.Quantidade_de_parcelas, vp.ec_id
                    FROM vendas_calculos vc
                    JOIN vendas_processadas vp ON vc.id_venda = vp.id
                    WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                    ORDER BY vp.data_processamento, vc.id_venda
                """
                ),
                engine,
                params={"calc_id": proc_id, "calc_tipo": tipo_taxa},
            )
            tabulator.value = df_result.head(50)

            # Calcular resumo estatístico
            if not df_result.empty:
                resumo_dict = {
                    "Quantidade de vendas": [len(df_result)],
                    "Total da venda": [df_result["tx_venda"].sum()],
                    "Total do desconto": [df_result["desc_calc"].sum(skipna=True)],
                    "% aferido (média)": [df_result["tx_calc"].mean(skipna=True)],
                    "Menor %": [df_result["tx_calc"].min(skipna=True)],
                    "Maior %": [df_result["tx_calc"].max(skipna=True)],
                }
                df_resumo = pd.DataFrame(resumo_dict)
                resumo_tabulator.value = df_resumo
            else:
                resumo_tabulator.value = pd.DataFrame()

            print("[DEBUG] Processamento finalizado com sucesso!")
            tipo_calc_desc = f"Taxa CAD + {tipo_taxa}" if usar_taxa_cad else tipo_taxa
            status_msg.object = f"Processamento {proc_id} com {tipo_calc_desc}. Todos os ECs e contextos do processamento foram processados. Exibindo as 50 primeiras vendas."
            status_msg.alert_type = "success"

        pn.state.execute(processamento_longo)

    btn_preview.on_click(preview_action)
    btn_processar.on_click(processar_action)

    # --- Sub-aba Gestão de Cálculos ---
    def make_gestao_calculos_view():
        import datetime
        from sqlalchemy import text

        # Filtros
        filtro_tipo = pn.widgets.Select(
            name="Tipo de Cálculo",
            options=[
                "Todos",
                "cad",
                "log_mensal",
                "log_trimestral",
                "log_semestral",
                "log_anual",
            ],
            value="Todos",
            width=180,
        )
        filtro_usuario = pn.widgets.TextInput(
            name="Usuário", placeholder="(qualquer)", width=180
        )
        filtro_data_ini = pn.widgets.DatePicker(name="Data Inicial", width=150)
        filtro_data_fim = pn.widgets.DatePicker(name="Data Final", width=150)
        btn_atualizar = pn.widgets.Button(
            name="🔄 Atualizar", button_type="primary", width=120
        )
        btn_deletar = pn.widgets.Button(
            name="🗑️ Deletar Selecionado(s)",
            button_type="danger",
            width=200,
            disabled=True,
        )
        status_gestao = pn.pane.Alert("", alert_type="info", visible=False)

        # Tabulator
        tab_gestao = pn.widgets.Tabulator(
            pd.DataFrame(),
            selectable=True,
            height=350,
            page_size=30,
            sizing_mode="stretch_width",
        )

        def carregar_calculos():
            query = """
                SELECT calc_id, calc_tipo, calc_usuario, MIN(calc_data) as data_ini, MAX(calc_data) as data_fim, COUNT(*) as qtd_vendas
                FROM vendas_calculos
                WHERE 1=1
            """
            params = {}
            if filtro_tipo.value != "Todos":
                query += " AND calc_tipo = :tipo"
                params["tipo"] = filtro_tipo.value
            if filtro_usuario.value.strip():
                query += " AND calc_usuario LIKE :usuario"
                params["usuario"] = f"%{filtro_usuario.value.strip()}%"
            if filtro_data_ini.value:
                query += " AND calc_data >= :data_ini"
                params["data_ini"] = datetime.datetime.combine(
                    filtro_data_ini.value, datetime.time.min
                )
            if filtro_data_fim.value:
                query += " AND calc_data <= :data_fim"
                params["data_fim"] = datetime.datetime.combine(
                    filtro_data_fim.value, datetime.time.max
                )
            query += " GROUP BY calc_id, calc_tipo, calc_usuario ORDER BY data_fim DESC"
            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
            tab_gestao.value = df
            btn_deletar.disabled = df.empty

        # Atualizar ao abrir e ao clicar
        btn_atualizar.on_click(lambda e: carregar_calculos())

        # Habilitar botão deletar se houver seleção
        def on_select(event):
            btn_deletar.disabled = not bool(tab_gestao.selection)

        tab_gestao.param.watch(on_select, "selection")

        # Deletar cálculos selecionados
        def deletar_calculos(event):
            if not tab_gestao.selection:
                return
            ids = tab_gestao.value.iloc[tab_gestao.selection][
                ["calc_id", "calc_tipo"]
            ].values.tolist()
            with engine.begin() as conn:
                for calc_id, calc_tipo in ids:
                    conn.execute(
                        text(
                            "DELETE FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo"
                        ),
                        {"calc_id": calc_id, "calc_tipo": calc_tipo},
                    )
            status_gestao.object = f"{len(ids)} cálculo(s) deletado(s) com sucesso."
            status_gestao.alert_type = "success"
            status_gestao.visible = True
            carregar_calculos()

        btn_deletar.on_click(deletar_calculos)
        # Inicializar
        carregar_calculos()
        return pn.Column(
            pn.pane.Markdown("### Gestão de Cálculos Existentes"),
            pn.Row(
                filtro_tipo,
                filtro_usuario,
                filtro_data_ini,
                filtro_data_fim,
                btn_atualizar,
            ),
            tab_gestao,
            pn.Row(btn_deletar, status_gestao),
            sizing_mode="stretch_width",
        )

    # --- Tabs principal ---
    aba_calculo = pn.Column(
        pn.pane.Markdown(
            "## Cálculo de Taxas sobre Vendas", sizing_mode="stretch_width"
        ),
        pn.Card(
            pn.Column(
                pn.Row(proc_select, sizing_mode="stretch_width"),
                pn.Spacer(height=10),
                pn.Row(usar_taxa_cad_checkbox, sizing_mode="stretch_width"),
                pn.Spacer(height=10),
                pn.Row(taxa_select, sizing_mode="stretch_width"),
                pn.Spacer(height=10),
                pn.Row(receba_rapido_checkbox, sizing_mode="stretch_width"),
                pn.Spacer(height=10),
                pn.Row(btn_preview, btn_processar, sizing_mode="stretch_width", align="center"),
                sizing_mode="stretch_width",
            ),
            title="Parâmetros do Cálculo",
            sizing_mode="stretch_width",
            margin=(10, 0, 10, 0),
            header_background="#f5f5f5",
        ),
        status_msg,
        preview_pane,
        pn.pane.Markdown(
            "### Vendas processadas com taxas aplicadas", sizing_mode="stretch_width"
        ),
        tabulator,
        pn.pane.Markdown(
            "### Resumo estatístico da amostra", sizing_mode="stretch_width"
        ),
        resumo_tabulator,
        sizing_mode="stretch_width",
        min_width=500,
    )

    return pn.Tabs(
        ("Cálculo de Taxas", aba_calculo),
        ("Gestão de Cálculos", make_gestao_calculos_view()),
        sizing_mode="stretch_width",
    )
