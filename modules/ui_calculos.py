from sqlalchemy import text
import panel as pn
import pandas as pd
from datetime import datetime
from conf.funcoesbd import fetch_all


def _remove_collate_if_sqlite(engine, sql: str) -> str:
    """MySQL: COLLATE clauses são suportadas nativamente - retorna SQL sem alteração"""
    return sql


def _remove_update_alias_if_sqlite(engine, sql: str) -> str:
    """MySQL: aliases em UPDATE são suportados nativamente - retorna SQL sem alteração"""
    return sql


def _convert_agg_update_simple_for_sqlite(
    engine, sql: str, periodo_field: str, periodo_join: str
) -> str:
    """Converte UPDATE JOIN com agregação (MIN) para sintaxe SQLite - SEM JOIN com vendas_processadas"""
    from conf.sql_adapter import get_db_type

    # Se não for SQLite, retorna SQL original
    if get_db_type(engine) != "sqlite":
        return sql

    # SQLite: usar subquery correlacionada (data_venda já está em vendas_calculos!)
    sqlite_sql = f"""
        UPDATE vendas_calculos
        SET tx_calc = (
            SELECT MIN(vc2.tx_venda)
            FROM vendas_calculos vc2
            WHERE vc2.calc_id = :calc_id 
              AND vc2.calc_tipo = :calc_tipo
              AND {periodo_field} = {periodo_join.replace('vc.', 'vendas_calculos.')}
              AND vc2.forma_pagamento = vendas_calculos.forma_pagamento
              AND vc2.bandeira = vendas_calculos.bandeira
        )
        WHERE calc_id = :calc_id 
          AND calc_tipo = :calc_tipo
          AND tx_calc IS NULL
    """
    return sqlite_sql


def _convert_update_join_for_sqlite(engine, sql: str) -> str:
    """Converte UPDATE JOIN do MySQL para sintaxe compatível com SQLite usando subqueries"""
    from conf.sql_adapter import get_db_type

    # Se não for SQLite, retorna SQL original (MySQL suporta UPDATE JOIN)
    if get_db_type(engine) != "sqlite":
        return sql

    import re

    # Detectar se é UPDATE com JOIN de taxas (mais complexo)
    if "JOIN taxas t" in sql:
        # Detectar se é taxa genérica (bandeira IS NULL) ou específica (bandeira IS NOT NULL)
        is_generic = "IS NULL" in sql and "t.bandeira IS NULL" in sql

        # Construir condições do JOIN com taxas
        if is_generic:
            # Taxa genérica: sem condição de bandeira
            join_conditions = """
            AND LOWER(t.contexto) = LOWER(vp.Adquirente)
            AND LOWER(t.forma_pagamento) = LOWER(vp.Forma_de_pagamento)
            AND vp.Data_da_venda BETWEEN t.data_ini AND t.data_fim
            AND t.bandeira IS NULL
"""
        else:
            # Taxa específica: com bandeira
            join_conditions = """
            AND LOWER(t.contexto) = LOWER(vp.Adquirente)
            AND LOWER(t.bandeira) = LOWER(vp.Bandeira)
            AND LOWER(t.forma_pagamento) = LOWER(vp.Forma_de_pagamento)
            AND vp.Data_da_venda BETWEEN t.data_ini AND t.data_fim
            AND t.bandeira IS NOT NULL
"""

        # Construir SQL compatível com SQLite usando subqueries
        sqlite_sql = f"""
UPDATE vendas_calculos
SET
    tx_calc = (
        SELECT t.taxa
        FROM vendas_processadas vp
        JOIN taxas t ON t.ec = vp.ec_id{join_conditions}
        WHERE vp.id = vendas_calculos.id_venda
        LIMIT 1
    ),
    desc_calc = (
        SELECT vp.Valor_da_venda * t.taxa / 100
        FROM vendas_processadas vp
        JOIN taxas t ON t.ec = vp.ec_id{join_conditions}
        WHERE vp.id = vendas_calculos.id_venda
        LIMIT 1
    ),
    vl_liq_calc = (
        SELECT vp.Valor_da_venda - (vp.Valor_da_venda * t.taxa / 100)
        FROM vendas_processadas vp
        JOIN taxas t ON t.ec = vp.ec_id{join_conditions}
        WHERE vp.id = vendas_calculos.id_venda
        LIMIT 1
    ),
    perda = CASE
        WHEN tx_venda IS NULL OR tx_venda = 0 THEN 0
        ELSE vl_liq_venda - (
            SELECT vp.Valor_da_venda - (vp.Valor_da_venda * t.taxa / 100)
            FROM vendas_processadas vp
            JOIN taxas t ON t.ec = vp.ec_id{join_conditions}
            WHERE vp.id = vendas_calculos.id_venda
            LIMIT 1
        )
    END
WHERE 
    calc_id = :calc_id 
    AND calc_tipo = :calc_tipo
    AND EXISTS (
        SELECT 1
        FROM vendas_processadas vp
        JOIN taxas t ON t.ec = vp.ec_id{join_conditions}
        WHERE vp.id = vendas_calculos.id_venda
    )
"""
        return sqlite_sql

    # JOIN simples com vendas_processadas (sem taxas)
    elif "JOIN vendas_processadas vp" in sql and "JOIN taxas" not in sql:
        # Converter UPDATE vc JOIN vp ... SET vc.campo = vp.campo para SQLite
        # Extrair a cláusula SET
        set_match = re.search(r"SET\s+(.+?)\s+WHERE", sql, re.DOTALL | re.IGNORECASE)
        if not set_match:
            return sql

        set_clause = set_match.group(1).strip()

        # Extrair a cláusula WHERE
        where_match = re.search(r"WHERE\s+(.+)$", sql, re.DOTALL | re.IGNORECASE)
        where_clause = where_match.group(1).strip() if where_match else "1=1"

        # Remover prefixo "vc." das colunas no SET (já estamos no contexto de vendas_calculos)
        set_clause = re.sub(r"\bvc\.", "", set_clause)

        # Substituir "vp.campo" por subqueries
        # Criar subquery base: SELECT campo FROM vendas_processadas WHERE id = vendas_calculos.id_venda
        def replace_vp_field(match):
            field = match.group(1)
            return f"(SELECT {field} FROM vendas_processadas WHERE id = vendas_calculos.id_venda)"

        set_clause = re.sub(r"vp\.(\w+)", replace_vp_field, set_clause)

        # Remover prefixo "vc." do WHERE também
        where_clause = re.sub(r"\bvc\.", "", where_clause)

        # Montar SQL SQLite
        sqlite_sql = f"""
UPDATE vendas_calculos
SET
    {set_clause}
WHERE {where_clause}
"""
        return sqlite_sql

    # Para outros padrões, retornar original
    return sql


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
                    preview_pane.object = (
                        "⚠️ **Nenhuma venda encontrada para este processamento.**"
                    )
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
                            sql_taxa = text(
                                """
                                SELECT COUNT(*) as cnt
                                FROM taxas t
                                WHERE t.ec = :ec_id
                                AND LOWER(t.bandeira) = LOWER(:bandeira)
                                AND LOWER(t.forma_pagamento) = LOWER(:forma_pgto)
                                AND :data_proc BETWEEN t.data_ini AND t.data_fim
                            """
                            )
                            result = conn.execute(
                                sql_taxa,
                                {
                                    "ec_id": ec_id,
                                    "bandeira": bandeira,
                                    "forma_pgto": forma_pgto,
                                    "data_proc": data_proc,
                                },
                            ).fetchone()
                            if result and result[0] > 0:
                                vendas_com_cad += 1

                vendas_com_log = (
                    total_vendas - vendas_com_cad if usar_taxa_cad else total_vendas
                )

                # Estatísticas de taxas originais
                taxas_orig = [
                    v.get("Taxas_Perc", 0) or 0 for v in vendas if v.get("Taxas_Perc")
                ]
                taxas_rr_orig = [
                    v.get("Taxas_RR", 0) or 0 for v in vendas if v.get("Taxas_RR")
                ]

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
            import time
            from sqlalchemy import text

            # ⏱️ Timestamp inicial
            t_inicio = time.time()
            print(
                f"[DEBUG] [00:00] Iniciando processamento de cálculo de taxas (modo SQL massivo)..."
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

            print(
                f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Receba Rápido ativo: {tem_receba_rapido}"
            )

            # Buscar vendas processadas com informações de EC e contexto
            t_query_vendas = time.time()
            print(
                f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Buscando vendas processadas..."
            )
            vendas = fetch_all(
                engine,
                """
                SELECT id, Bandeira, Forma_de_pagamento, data_processamento, 
                       Data_da_venda, Adquirente,
                       Valor_da_venda, Valor_líquido_da_venda, Quantidade_de_parcelas, 
                       ec_id, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                       arquivo_origem
                FROM vendas_processadas 
                WHERE processamentoid = :proc_id
                ORDER BY data_processamento, id
                """,
                {"proc_id": proc_id},
            )
            print(
                f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] {len(vendas)} vendas encontradas em {time.time()-t_query_vendas:.2f}s"
            )
            if not vendas:
                status_msg.object = "Nenhuma venda encontrada para o processamento."
                status_msg.alert_type = "warning"
                return

            # Montar lista de inserts com campos de cálculo nulos
            t_prepare = time.time()
            print(
                f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Preparando dados para insert..."
            )
            insert_sql = text(
                """
                INSERT INTO vendas_calculos (
                    id_venda, calc_id, calc_tipo, calc_usuario, bandeira, forma_pagamento, calc_data,
                    data_venda, ec_id, adquirente, arquivo_origem,
                    nsu, cod_autorizacao,
                    vl_venda, tx_venda, desc_venda, vl_liq_venda,
                    tx_rr_venda, vl_rr_venda,
                    tx_calc, desc_calc, vl_liq_calc, tx_rr_calc, vl_rr_calc, perda_rr
                ) VALUES (
                    :id_venda, :calc_id, :calc_tipo, :calc_usuario, :bandeira, :forma_pagamento, :calc_data,
                    :data_venda, :ec_id, :adquirente, :arquivo_origem,
                    :nsu, :cod_autorizacao,
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
                    "data_venda": row.get("Data_da_venda"),  # ⚡ Data para evitar JOINs
                    "ec_id": row.get("ec_id"),  # ⚡ EC para queries RR
                    "adquirente": row.get("Adquirente"),  # ⚡ Adquirente/contexto
                    "arquivo_origem": row.get(
                        "arquivo_origem"
                    ),  # ⚡ Arquivo para auditoria
                    "nsu": row.get("NSU"),  # ⚡ NSU para evidências
                    "cod_autorizacao": row.get(
                        "Código_de_autorização"
                    ),  # ⚡ Cód.Aut para evidências
                    "vl_venda": vl_venda,
                    "tx_venda": tx_venda,
                    "desc_venda": desc_venda_calc,
                    "vl_liq_venda": vl_liq_venda_calc,
                    "tx_rr_venda": tx_rr_venda,
                    "vl_rr_venda": vl_rr_venda_calc,
                }
                params_list.append(params)

            if params_list:
                print(
                    f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] {len(params_list)} registros preparados em {time.time()-t_prepare:.2f}s"
                )
            # DEBUG após insert
            with engine.connect() as _conn:
                count_inserted = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(
                    f"[DEBUG] TOTAL vendas_calculos inseridos para processamento: {count_inserted}"
                )

            # ⚡ OTIMIZAÇÃO: aumentar batch_size de 1000 para 5000 (reduz iterações de 1550 para 310)
            batch_size = 5000
            total = len(params_list)

            t_inserts = time.time()
            print(
                f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Executando insert em lotes de {batch_size} registros ({total//batch_size + 1} lotes)..."
            )
            with engine.begin() as conn:
                # Limpar vendas_calculos para este processamento/tipo_taxa antes de inserir
                t_delete = time.time()
                delete_sql = text(
                    """
                    DELETE FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                """
                )
                conn.execute(delete_sql, {"calc_id": proc_id, "calc_tipo": tipo_taxa})
                print(
                    f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] DELETE executado em {time.time()-t_delete:.2f}s"
                )

                # Log apenas a cada 10% de progresso para não poluir
                last_pct = 0
                for i in range(0, total, batch_size):
                    batch = params_list[i : i + batch_size]
                    conn.execute(insert_sql, batch)

                    current_pct = (
                        int((i / total) * 10) * 10
                    )  # Arredonda para múltiplos de 10%
                    if current_pct > last_pct and current_pct > 0:
                        elapsed = time.time() - t_inserts
                        eta = (elapsed / (i + len(batch))) * (total - (i + len(batch)))
                        print(
                            f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Insert: {current_pct}% ({min(i+batch_size, total)}/{total}) - ETA: {eta:.0f}s"
                        )
                        last_pct = current_pct
                    status_msg.object = f"Processando... {min(i+batch_size, total)}/{total} registros inseridos."

                print(
                    f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] ✅ Todos os inserts concluídos em {time.time()-t_inserts:.2f}s"
                )

                # ⚡ OTIMIZAÇÃO: Consolidar queries de estatísticas em uma única query (economia: ~35s → ~5s)
                t_stats_consolidado = time.time()
                stats_insert = conn.execute(
                    text(
                        """
                        SELECT 
                            COUNT(*) as total_inserido,
                            SUM(CASE WHEN tx_venda IS NULL OR tx_venda = 0 THEN 1 ELSE 0 END) as tx_venda_zero
                        FROM vendas_calculos 
                        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                    """
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).fetchone()
                print(
                    f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Estatísticas insert: {stats_insert[0]} registros, {stats_insert[1]} com tx_venda=0/NULL ({time.time()-t_stats_consolidado:.2f}s)"
                )
                if stats_insert[1] > 0:
                    print(
                        f"[DEBUG] ⚠️  Essas {stats_insert[1]} vendas terão perda = 0 (sem taxa original, não há perda real)"
                    )

                # Verificar se dados foram inseridos corretamente
                sample_check = conn.execute(
                    text(
                        """
                        SELECT COUNT(*) as total, 
                               COUNT(DISTINCT calc_tipo) as tipos,
                               GROUP_CONCAT(DISTINCT calc_tipo) as tipos_list
                        FROM vendas_calculos 
                        WHERE calc_id = :calc_id
                    """
                    ),
                    {"calc_id": proc_id},
                ).fetchone()
                print(f"[DEBUG] 🔍 Verificação pós-insert:")
                print(
                    f"[DEBUG]    Total registros com calc_id '{proc_id}': {sample_check[0]}"
                )
                print(
                    f"[DEBUG]    Tipos encontrados ({sample_check[1]}): {sample_check[2]}"
                )

                # 🚀 OPÇÃO FUTURA: LOAD DATA INFILE (80-90% mais rápido que batch insert)
                # Para implementar: exportar params_list para CSV e usar:
                # LOAD DATA LOCAL INFILE 'temp.csv' INTO TABLE vendas_calculos ...
                # Redução esperada: 612s → 30-60s

                # Atualizar taxas e valores via UPDATE JOIN, corrigindo collation
                t_updates = time.time()
                print(
                    f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] ⏳ Iniciando UPDATEs JOIN..."
                )
                print(f"[DEBUG] Usar Taxa CAD: {usar_taxa_cad}, Tipo Log: {tipo_taxa}")

                # Se checkbox CAD estiver marcado, primeiro tentar aplicar taxa CAD
                if usar_taxa_cad:
                    t_cad = time.time()
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Aplicando Taxa CAD (camada 1: específica)..."
                    )
                    # ⚡ NOVO: Sem JOIN com vendas_processadas! Usa campos locais
                    # CAMADA 1: Tentar taxa específica (forma + bandeira)
                    update_sql_raw = f"""
                        UPDATE vendas_calculos vc
                        JOIN taxas t ON t.ec = vc.ec_id 
                            AND LOWER(t.contexto) COLLATE utf8mb4_0900_ai_ci = LOWER(vc.adquirente) COLLATE utf8mb4_0900_ai_ci
                            AND LOWER(t.bandeira) COLLATE utf8mb4_0900_ai_ci = LOWER(vc.bandeira) COLLATE utf8mb4_0900_ai_ci
                            AND LOWER(t.forma_pagamento) COLLATE utf8mb4_0900_ai_ci = LOWER(vc.forma_pagamento) COLLATE utf8mb4_0900_ai_ci
                            AND vc.data_venda BETWEEN t.data_ini AND t.data_fim
                            AND t.bandeira IS NOT NULL
                        SET
                            vc.tx_calc = t.taxa,
                            vc.desc_calc = vc.vl_venda * t.taxa / 100,
                            vc.vl_liq_calc = vc.vl_venda - (vc.vl_venda * t.taxa / 100),
                            vc.perda = CASE 
                                WHEN vc.tx_venda IS NULL OR vc.tx_venda = 0 THEN 0
                                ELSE vc.vl_liq_venda - (vc.vl_venda - (vc.vl_venda * t.taxa / 100))
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
                    result_camada1 = conn.execute(
                        update_sql,
                        {
                            "calc_id": proc_id,
                            "calc_tipo": tipo_taxa,
                        },
                    )
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] CAD Camada 1: {result_camada1.rowcount} registros ({time.time()-t_cad:.2f}s)"
                    )

                    # CAMADA 2: Tentar taxa genérica (só forma, bandeira = NULL)
                    t_cad2 = time.time()
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Aplicando Taxa CAD (camada 2: genérica)..."
                    )
                    # ⚡ NOVO: Sem JOIN com vendas_processadas! Usa campos locais
                    update_sql_generica_raw = f"""
                        UPDATE vendas_calculos vc
                        JOIN taxas t ON t.ec = vc.ec_id 
                            AND LOWER(t.contexto) COLLATE utf8mb4_0900_ai_ci = LOWER(vc.adquirente) COLLATE utf8mb4_0900_ai_ci
                            AND LOWER(t.forma_pagamento) COLLATE utf8mb4_0900_ai_ci = LOWER(vc.forma_pagamento) COLLATE utf8mb4_0900_ai_ci
                            AND vc.data_venda BETWEEN t.data_ini AND t.data_fim
                            AND t.bandeira IS NULL
                        SET
                            vc.tx_calc = t.taxa,
                            vc.desc_calc = vc.vl_venda * t.taxa / 100,
                            vc.vl_liq_calc = vc.vl_venda - (vc.vl_venda * t.taxa / 100),
                            vc.perda = CASE 
                                WHEN vc.tx_venda IS NULL OR vc.tx_venda = 0 THEN 0
                                ELSE vc.vl_liq_venda - (vc.vl_venda - (vc.vl_venda * t.taxa / 100))
                            END
                        WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                        AND vc.tx_calc IS NULL
                        """
                    update_sql_generica_processed = _remove_collate_if_sqlite(
                        engine, update_sql_generica_raw
                    )
                    update_sql_generica_processed = _convert_update_join_for_sqlite(
                        engine, update_sql_generica_processed
                    )
                    update_sql_generica = text(update_sql_generica_processed)
                    result_camada2 = conn.execute(
                        update_sql_generica,
                        {
                            "calc_id": proc_id,
                            "calc_tipo": tipo_taxa,
                        },
                    )
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] CAD Camada 2: {result_camada2.rowcount} registros ({time.time()-t_cad2:.2f}s)"
                    )

                    # ⚡ Estatísticas já conhecidas pelos rowcounts (economiza ~21s de query)
                    vendas_com_cad = result_camada1.rowcount + result_camada2.rowcount
                    vendas_sem_cad = len(vendas) - vendas_com_cad
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Estatísticas após Taxa CAD (calculado sem query):"
                    )
                    print(f"  • Total de vendas: {len(vendas)}")
                    print(
                        f"  • Com taxa CAD encontrada: {vendas_com_cad} (camada1: {result_camada1.rowcount}, camada2: {result_camada2.rowcount})"
                    )
                    print(f"  • Sem taxa CAD (será aplicado Log): {vendas_sem_cad}")

                    # Atualizar taxas RR (Receba Rápido) para vendas com CAD
                    if tem_receba_rapido:
                        print("[DEBUG] Atualizando taxas RR para vendas com CAD...")
                        # CAMADA 1 RR: Taxa específica (forma + bandeira)
                        update_rr_sql_raw = f"""
                            UPDATE vendas_calculos vc
                            JOIN vendas_processadas vp ON vc.id_venda = vp.id
                            JOIN taxas t ON t.ec = vp.ec_id 
                                AND LOWER(t.contexto) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Adquirente) COLLATE utf8mb4_0900_ai_ci
                                AND LOWER(t.bandeira) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Bandeira) COLLATE utf8mb4_0900_ai_ci
                                AND LOWER(t.forma_pagamento) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Forma_de_pagamento) COLLATE utf8mb4_0900_ai_ci
                                AND vp.Data_da_venda BETWEEN t.data_ini AND t.data_fim
                                AND t.bandeira IS NOT NULL
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
                        result_rr1 = conn.execute(
                            update_rr_sql,
                            {
                                "calc_id": proc_id,
                                "calc_tipo": tipo_taxa,
                            },
                        )
                        print(
                            f"[DEBUG] RR Camada 1 (forma+bandeira): {result_rr1.rowcount} registros"
                        )

                        # CAMADA 2 RR: Taxa genérica (só forma)
                        update_rr_generica_sql_raw = f"""
                            UPDATE vendas_calculos vc
                            JOIN vendas_processadas vp ON vc.id_venda = vp.id
                            JOIN taxas t ON t.ec = vp.ec_id 
                                AND LOWER(t.contexto) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Adquirente) COLLATE utf8mb4_0900_ai_ci
                                AND LOWER(t.forma_pagamento) COLLATE utf8mb4_0900_ai_ci = LOWER(vp.Forma_de_pagamento) COLLATE utf8mb4_0900_ai_ci
                                AND vp.Data_da_venda BETWEEN t.data_ini AND t.data_fim
                                AND t.bandeira IS NULL
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
                            AND (vc.tx_rr_calc IS NULL OR vc.tx_rr_calc = 0)
                            """
                        update_rr_generica_sql_processed = _remove_collate_if_sqlite(
                            engine, update_rr_generica_sql_raw
                        )
                        update_rr_generica_sql_processed = (
                            _convert_update_join_for_sqlite(
                                engine, update_rr_generica_sql_processed
                            )
                        )
                        update_rr_generica_sql = text(update_rr_generica_sql_processed)
                        result_rr2 = conn.execute(
                            update_rr_generica_sql,
                            {
                                "calc_id": proc_id,
                                "calc_tipo": tipo_taxa,
                            },
                        )
                        print(
                            f"[DEBUG] RR Camada 2 (só forma): {result_rr2.rowcount} registros"
                        )

                # Agora aplicar lógica de LOG para vendas que não têm tx_calc (se usar_taxa_cad) ou todas (se não usar)
                # Se usar_taxa_cad, só aplicar LOG onde tx_calc IS NULL
                # Se não usar_taxa_cad, aplicar LOG em todas
                aplicar_log = True
                if usar_taxa_cad:
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Aplicando lógica de Log para vendas sem Taxa CAD..."
                    )
                else:
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Aplicando lógica de Log ({tipo_taxa}) para todas as vendas..."
                    )

                if aplicar_log:
                    # ⚠️ DEFINIR periodo_format e periodo_ini_sql baseado no tipo_taxa ANTES de usar
                    if tipo_taxa == "log_mensal":
                        periodo_format = "%Y-%m-01"  # Apenas o formato
                        periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-%m-01')"  # Com DATE_FORMAT
                    elif tipo_taxa == "log_trimestral":
                        periodo_format = "%Y-Q"
                        periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-Q')"
                    elif tipo_taxa == "log_semestral":
                        periodo_format = "%Y-S"
                        periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-S')"
                    else:  # log_anual (padrão)
                        periodo_format = "%Y-01-01"
                        periodo_ini_sql = "DATE_FORMAT(vp.Data_da_venda, '%Y-01-01')"

                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Período configurado: {periodo_format}"
                    )
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] SQL período: {periodo_ini_sql}"
                    )

                    # Estatísticas ANTES do update LOG (usar conn existente para ver INSERT não comitado)
                    count_null_pre = conn.execute(
                        text(
                            "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NULL"
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).scalar()
                    count_nonnull_pre = conn.execute(
                        text(
                            "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NOT NULL"
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).scalar()
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] 📊 ANTES update LOG: {count_nonnull_pre} com tx_calc preenchido, {count_null_pre} NULL"
                    )

                    if count_null_pre == 0:
                        print(
                            f"[DEBUG] ⚠️  PROBLEMA: Nenhum registro com tx_calc IS NULL encontrado!"
                        )
                        print(f"[DEBUG]    calc_id = '{proc_id}'")
                        print(f"[DEBUG]    calc_tipo = '{tipo_taxa}'")
                        print(
                            f"[DEBUG]    Possível causa: Conexão não está vendo INSERTs da transação"
                        )
                    else:
                        print(
                            f"[DEBUG] ✅ Iniciando UPDATE LOG para {count_null_pre} registros..."
                        )

                    # ============================================================================
                    # UPDATE LOG INLINE (versão simplificada - sem função separada)
                    #
                    # ✅ VANTAGENS desta abordagem:
                    #    - Usa mesma conexão/transação (vê INSERTs pendentes)
                    #    - Menos código (~120 linhas removidas)
                    #    - Mais legível (tudo em sequência)
                    #    - Sem overhead de chamada de função
                    #
                    # 🔄 ROLLBACK: Se precisar voltar para função separada:
                    #    - Veja código comentado nas linhas 4-105 deste arquivo
                    #    - Descomente a função update_log_tx_calc_em_lotes
                    #    - Substitua este bloco por: update_log_tx_calc_em_lotes(engine, proc_id, tipo_taxa, lote=10000, conn_externa=conn)
                    # ============================================================================
                    # Definir campos de período baseado no tipo_taxa
                    # ⚡ NOVO: Usar data_venda local (não precisa JOIN com vendas_processadas)
                    if tipo_taxa == "log_mensal":
                        # MySQL
                        periodo_field_mysql = "DATE_FORMAT(vc2.data_venda, '%Y-%m')"
                        periodo_join_mysql = "DATE_FORMAT(vc.data_venda, '%Y-%m')"
                        # SQLite
                        periodo_field_sqlite = "strftime('%Y-%m', vc2.data_venda)"
                        periodo_join_sqlite = "strftime('%Y-%m', vc.data_venda)"
                    elif tipo_taxa == "log_trimestral":
                        # MySQL
                        periodo_field_mysql = "CONCAT(YEAR(vc2.data_venda), '-Q', QUARTER(vc2.data_venda))"
                        periodo_join_mysql = (
                            "CONCAT(YEAR(vc.data_venda), '-Q', QUARTER(vc.data_venda))"
                        )
                        # SQLite - aproximação (sem QUARTER nativo)
                        periodo_field_sqlite = "strftime('%Y', vc2.data_venda) || '-Q' || CAST((CAST(strftime('%m', vc2.data_venda) AS INTEGER) + 2) / 3 AS TEXT)"
                        periodo_join_sqlite = "strftime('%Y', vc.data_venda) || '-Q' || CAST((CAST(strftime('%m', vc.data_venda) AS INTEGER) + 2) / 3 AS TEXT)"
                    elif tipo_taxa == "log_semestral":
                        # MySQL
                        periodo_field_mysql = "CONCAT(YEAR(vc2.data_venda), '-S', CEILING(MONTH(vc2.data_venda)/6))"
                        periodo_join_mysql = "CONCAT(YEAR(vc.data_venda), '-S', CEILING(MONTH(vc.data_venda)/6))"
                        # SQLite - aproximação (sem CEILING/MONTH nativos)
                        periodo_field_sqlite = "strftime('%Y', vc2.data_venda) || '-S' || CAST((CAST(strftime('%m', vc2.data_venda) AS INTEGER) + 5) / 6 AS TEXT)"
                        periodo_join_sqlite = "strftime('%Y', vc.data_venda) || '-S' || CAST((CAST(strftime('%m', vc.data_venda) AS INTEGER) + 5) / 6 AS TEXT)"
                    else:  # log_anual
                        # MySQL
                        periodo_field_mysql = "YEAR(vc2.data_venda)"
                        periodo_join_mysql = "YEAR(vc.data_venda)"
                        # SQLite
                        periodo_field_sqlite = "strftime('%Y', vc2.data_venda)"
                        periodo_join_sqlite = "strftime('%Y', vc.data_venda)"

                    # ⚡ UPDATE LOG SIMPLIFICADO - Sem JOIN com vendas_processadas!
                    print(
                        f"[DEBUG] 🚀 Executando UPDATE LOG em query única (sem batches, sem JOINs)..."
                    )

                    # Detectar banco de dados
                    from conf.sql_adapter import get_db_type

                    db_type = get_db_type(engine)

                    if db_type == "sqlite":
                        periodo_field = periodo_field_sqlite
                        periodo_join = periodo_join_sqlite
                    else:
                        periodo_field = periodo_field_mysql
                        periodo_join = periodo_join_mysql

                    # UPDATE direto SEM JOIN - usa apenas data_venda local!
                    update_log_sql_raw = f"""
                        UPDATE vendas_calculos vc
                        JOIN (
                            SELECT 
                                {periodo_field} AS periodo,
                                vc2.forma_pagamento,
                                vc2.bandeira,
                                MIN(vc2.tx_venda) AS min_tx_venda
                            FROM vendas_calculos vc2
                            WHERE vc2.calc_id = :calc_id 
                              AND vc2.calc_tipo = :calc_tipo
                            GROUP BY periodo, vc2.forma_pagamento, vc2.bandeira
                        ) agg
                            ON agg.periodo = {periodo_join}
                           AND agg.forma_pagamento = vc.forma_pagamento
                           AND agg.bandeira = vc.bandeira
                        SET vc.tx_calc = agg.min_tx_venda
                        WHERE vc.calc_id = :calc_id 
                          AND vc.calc_tipo = :calc_tipo
                          AND vc.tx_calc IS NULL
                    """

                    # Converter para SQLite se necessário (ainda precisa converter UPDATE JOIN)
                    update_log_sql = _convert_agg_update_simple_for_sqlite(
                        engine, update_log_sql_raw, periodo_field, periodo_join
                    )

                    t_log_update_start = time.time()
                    result_log = conn.execute(
                        text(update_log_sql),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    )
                    t_log_update = time.time() - t_log_update_start

                    print(
                        f"[DEBUG] ✅ UPDATE LOG: {result_log.rowcount} registros atualizados em {t_log_update:.2f}s"
                    )

                    if result_log.rowcount == 0:
                        print(
                            f"[DEBUG] ⚠️  Nenhum registro atualizado - possíveis causas:"
                        )
                        print(
                            f"[DEBUG]    1. Todos registros já têm tx_calc preenchido"
                        )
                        print(
                            f"[DEBUG]    2. Não há dados suficientes para agregação por período/bandeira/forma"
                        )
                        print(
                            f"[DEBUG]    3. Filtro de período não retornou resultados"
                        )
                    # ============================================================================
                    # FIM DO BLOCO UPDATE LOG INLINE
                    # Refatoração: 2025-12-12 - Substituiu update_log_tx_calc_em_lotes()
                    # Resultado: Código mais simples, menos bugs, mesma funcionalidade
                    # ============================================================================

                    # Estatísticas APÓS o update LOG (usar conn existente para ver resultado do UPDATE)
                    count_null_pos = conn.execute(
                        text(
                            "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NULL"
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).scalar()
                    count_nonnull_pos = conn.execute(
                        text(
                            "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NOT NULL"
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).scalar()

                    delta = count_nonnull_pos - count_nonnull_pre
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] 📊 APÓS update LOG: {count_nonnull_pos} com tx_calc preenchido, {count_null_pos} NULL"
                    )

                    if delta > 0:
                        print(
                            f"[DEBUG] ✅ Sucesso! +{delta} registros preenchidos pela lógica LOG ({(delta/len(vendas))*100:.1f}% do total)"
                        )
                    else:
                        print(
                            f"[DEBUG] ❌ FALHA: Nenhum registro foi atualizado pelo LOG!"
                        )
                        print(f"[DEBUG]    Esperado: {count_null_pre} atualizações")
                        print(f"[DEBUG]    Realizado: 0 atualizações")

                    t_log_desc = time.time()
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Executando UPDATE desc_calc/perda..."
                    )
                    # ⚡ NOVO: Sem JOIN! Usa vl_venda que já está em vendas_calculos
                    update_desc_sql_raw = """
                        UPDATE vendas_calculos
                        SET
                            desc_calc = CASE WHEN tx_calc IS NOT NULL THEN vl_venda * tx_calc / 100 ELSE NULL END,
                            vl_liq_calc = CASE WHEN tx_calc IS NOT NULL THEN vl_venda - (vl_venda * tx_calc / 100) ELSE NULL END,
                            perda = CASE 
                                WHEN tx_calc IS NULL THEN NULL
                                WHEN tx_venda IS NULL OR tx_venda = 0 THEN 0
                                ELSE vl_liq_venda - (vl_venda - (vl_venda * tx_calc / 100))
                            END
                        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                        AND tx_calc IS NOT NULL
                        """
                    # Não precisa mais de conversão para SQLite! Sintaxe é idêntica
                    update_desc_sql = text(update_desc_sql_raw)
                    result2 = conn.execute(
                        update_desc_sql,
                        {
                            "calc_id": proc_id,
                            "calc_tipo": tipo_taxa,
                        },
                    )
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] UPDATE desc_calc/vl_liq_calc/perda affected rows: {result2.rowcount} ({time.time()-t_log_desc:.2f}s)"
                    )

                    # ⚡ Estatísticas de perda (OPCIONAL - comentar para economizar ~15s)
                    # Descomente se precisar de detalhamento de perdas
                    # t_stats_perda = time.time()
                    # stats = conn.execute(
                    #     text("""
                    #         SELECT COUNT(*) as total,
                    #                SUM(CASE WHEN perda = 0 THEN 1 ELSE 0 END) as com_perda_zero,
                    #                SUM(CASE WHEN perda > 0 THEN 1 ELSE 0 END) as com_perda_positiva,
                    #                SUM(CASE WHEN perda < 0 THEN 1 ELSE 0 END) as com_perda_negativa,
                    #                SUM(CASE WHEN perda IS NULL THEN 1 ELSE 0 END) as sem_perda_calculada
                    #         FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                    #     """),
                    #     {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    # ).fetchone()
                    # print(f"[DEBUG] Estatísticas de Perda (Taxa {tipo_taxa.upper()}, query: {time.time()-t_stats_perda:.2f}s):")
                    # print(f"  • Total: {stats[0]} | Perda=0: {stats[1]} | Perda>0: {stats[2]} | Perda<0: {stats[3]} | Sem cálculo: {stats[4]}")

                    # Terceiro UPDATE para LOG: preencher taxas RR usando mesma lógica de menor taxa
                    print(
                        f"[DEBUG] Atualizando taxas RR para LOG - Receba Rápido ativo: {tem_receba_rapido}"
                    )
                    if tem_receba_rapido:
                        # Primeiro: atualizar tx_rr_calc com a menor taxa RR do período
                        # Se usar_taxa_cad, só atualizar onde tx_rr_calc ainda não foi preenchido pelo CAD
                        condicao_rr = (
                            "AND (vc.tx_rr_calc IS NULL OR vc.tx_rr_calc = 0)"
                            if usar_taxa_cad
                            else ""
                        )

                        # ⚠️ USAR periodo_format (não periodo_ini_sql) para evitar duplicação
                        print(
                            f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Iniciando UPDATE tx_rr_calc com período: {periodo_format}"
                        )

                        # Detectar banco de dados para formato de data correto
                        from conf.sql_adapter import get_db_type

                        db_type = get_db_type(engine)

                        if db_type == "sqlite":
                            # SQLite: usar strftime
                            periodo_func = f"strftime('{periodo_format.replace('%', '%').replace('Y', 'Y').replace('m', 'm')}',"
                            periodo_close = ")"
                        else:
                            # MySQL: usar DATE_FORMAT
                            periodo_func = f"DATE_FORMAT("
                            periodo_close = f", '{periodo_format}')"

                        # ⚡ NOVO: Sem JOIN com vendas_processadas! Usa campos locais (ec_id, bandeira, forma_pagamento, data_venda, tx_rr_venda)
                        update_tx_rr_sql_raw = f"""
                            UPDATE vendas_calculos vc
                            JOIN (
                                SELECT
                                    vc2.ec_id,
                                    LOWER(TRIM(vc2.bandeira)) AS bandeira,
                                    LOWER(TRIM(vc2.forma_pagamento)) AS forma_pagamento,
                                    {periodo_func}vc2.data_venda{periodo_close} AS periodo_ini,
                                    MIN(vc2.tx_rr_venda) AS min_tx_rr_venda
                                FROM vendas_calculos vc2
                                WHERE vc2.calc_id = :calc_id AND vc2.calc_tipo = :calc_tipo 
                                AND vc2.tx_rr_venda IS NOT NULL AND vc2.tx_rr_venda > 0
                                GROUP BY vc2.ec_id, LOWER(TRIM(vc2.bandeira)), LOWER(TRIM(vc2.forma_pagamento)), periodo_ini
                            ) min_txs_rr
                            ON vc.ec_id = min_txs_rr.ec_id
                            AND LOWER(TRIM(vc.bandeira)) = min_txs_rr.bandeira
                            AND LOWER(TRIM(vc.forma_pagamento)) = min_txs_rr.forma_pagamento
                            AND {periodo_func}vc.data_venda{periodo_close} = min_txs_rr.periodo_ini
                            SET vc.tx_rr_calc = min_txs_rr.min_tx_rr_venda
                            WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                            {condicao_rr}
                            """
                        update_tx_rr_sql_processed = _remove_collate_if_sqlite(
                            engine, update_tx_rr_sql_raw
                        )
                        # Converter para SQLite se necessário (ainda precisa converter UPDATE JOIN com subquery)
                        if db_type == "sqlite":
                            # Para SQLite, converter para subquery correlacionada
                            update_tx_rr_sql_processed = f"""
                                UPDATE vendas_calculos
                                SET tx_rr_calc = (
                                    SELECT MIN(vc2.tx_rr_venda)
                                    FROM vendas_calculos vc2
                                    WHERE vc2.calc_id = :calc_id AND vc2.calc_tipo = :calc_tipo
                                    AND vc2.tx_rr_venda IS NOT NULL AND vc2.tx_rr_venda > 0
                                    AND vc2.ec_id = vendas_calculos.ec_id
                                    AND LOWER(TRIM(vc2.bandeira)) = LOWER(TRIM(vendas_calculos.bandeira))
                                    AND LOWER(TRIM(vc2.forma_pagamento)) = LOWER(TRIM(vendas_calculos.forma_pagamento))
                                    AND {periodo_func}vc2.data_venda{periodo_close} = {periodo_func}vendas_calculos.data_venda{periodo_close}
                                )
                                WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                                {condicao_rr.replace('vc.', '')}
                            """

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
                        condicao_rr_calc = (
                            "AND (vc.tx_rr_calc IS NOT NULL AND (vc.tx_rr_calc != COALESCE((SELECT t2.taxa_rr FROM taxas t2 JOIN vendas_processadas vp2 ON t2.ec = vp2.ec_id WHERE vp2.id = vc.id_venda LIMIT 1), 0)))"
                            if usar_taxa_cad
                            else "AND vc.tx_rr_calc IS NOT NULL"
                        )
                        # Simplificando: se usar_taxa_cad, só atualizar onde tx_rr_calc foi preenchido pelo LOG (não pelo CAD)
                        # Vamos usar uma abordagem mais simples: atualizar todos que têm tx_rr_calc, pois o CAD já preencheu os seus
                        # ⚡ NOVO: Sem JOIN com vendas_processadas! Usa vl_venda local
                        update_rr_calc_sql_raw = """
                            UPDATE vendas_calculos
                            SET
                                vl_rr_calc = CASE WHEN tx_rr_calc IS NOT NULL THEN vl_venda * tx_rr_calc / 100 ELSE NULL END,
                                perda_rr = CASE 
                                    WHEN tx_rr_calc IS NOT NULL AND vl_rr_venda IS NOT NULL 
                                    THEN (vl_venda * tx_rr_calc / 100) - vl_rr_venda
                                    ELSE NULL 
                                END
                            WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_rr_calc IS NOT NULL
                            """
                        # Não precisa mais de conversão - sintaxe é idêntica em MySQL e SQLite!
                        update_rr_calc_sql = text(update_rr_calc_sql_raw)
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
                        # Se não tem Receba Rápido, zerar tx_rr_calc e vl_rr_calc
                        # MAS calcular perda_rr = -vl_rr_venda (economia por não usar RR)
                        print(
                            "[DEBUG] Cliente SEM Receba Rápido - calculando economia..."
                        )
                        if usar_taxa_cad:
                            # Zerar apenas onde tx_rr_calc não foi preenchido pelo CAD
                            update_rr_log_sql_raw = """
                                UPDATE vendas_calculos vc
                                SET
                                    vc.tx_rr_calc = 0,
                                    vc.vl_rr_calc = 0,
                                    vc.perda_rr = CASE 
                                        WHEN vc.vl_rr_venda IS NOT NULL AND vc.vl_rr_venda != 0 
                                        THEN -vc.vl_rr_venda
                                        ELSE 0
                                    END
                                WHERE vc.calc_id = :calc_id AND vc.calc_tipo = :calc_tipo
                                AND (vc.tx_rr_calc IS NULL OR vc.tx_rr_calc = 0)
                                """
                        else:
                            # Zerar todas, mas calcular perda_rr como economia
                            update_rr_log_sql_raw = """
                                UPDATE vendas_calculos vc
                                SET
                                    vc.tx_rr_calc = 0,
                                    vc.vl_rr_calc = 0,
                                    vc.perda_rr = CASE 
                                        WHEN vc.vl_rr_venda IS NOT NULL AND vc.vl_rr_venda != 0 
                                        THEN -vc.vl_rr_venda
                                        ELSE 0
                                    END
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
                            f"[DEBUG] UPDATE taxas RR (economia) affected rows: {result3.rowcount}"
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
                    print(
                        f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Registros com tx_rr_calc preenchidos: {debug_calc}"
                    )

                print(
                    f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] ✅ UPDATE JOIN finalizado (total: {time.time()-t_updates:.2f}s)"
                )

            # ===== ESTATÍSTICAS FINAIS DETALHADAS =====
            print(f"\n[DEBUG] {'='*60}")
            print(f"[DEBUG] ESTATÍSTICAS FINAIS DO PROCESSAMENTO")
            print(f"[DEBUG] {'='*60}")

            with engine.connect() as _conn:
                # Contagem geral
                count_total = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(f"[DEBUG] Total de registros: {count_total}")

                # tx_calc
                count_txcalc = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NOT NULL"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                count_txcalc_null = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NULL"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(
                    f"[DEBUG] tx_calc preenchidos: {count_txcalc} ({count_txcalc/count_total*100:.2f}%)"
                )
                print(
                    f"[DEBUG] tx_calc NULL: {count_txcalc_null} ({count_txcalc_null/count_total*100:.2f}%)"
                )

                # desc_calc e perda
                count_desc = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND desc_calc IS NOT NULL"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                count_perda = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND perda IS NOT NULL"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(
                    f"[DEBUG] desc_calc preenchidos: {count_desc} ({count_desc/count_total*100:.2f}%)"
                )
                print(
                    f"[DEBUG] perda preenchidos: {count_perda} ({count_perda/count_total*100:.2f}%)"
                )

                # tx_rr_calc
                count_txrr = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_rr_calc IS NOT NULL AND tx_rr_calc != 0"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                count_perdarr = _conn.execute(
                    text(
                        "SELECT COUNT(*) FROM vendas_calculos WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND perda_rr IS NOT NULL AND perda_rr != 0"
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).scalar()
                print(
                    f"[DEBUG] tx_rr_calc preenchidos (≠0): {count_txrr} ({count_txrr/count_total*100:.2f}%)"
                )
                print(
                    f"[DEBUG] perda_rr preenchidos (≠0): {count_perdarr} ({count_perdarr/count_total*100:.2f}%)"
                )

                # Amostras de dados
                print(f"\n[DEBUG] Amostra de registros COM tx_calc:")
                amostra_preench = _conn.execute(
                    text(
                        """SELECT id_venda, bandeira, forma_pagamento, 
                           ROUND(tx_venda, 2) as tx_venda, ROUND(tx_calc, 2) as tx_calc, 
                           ROUND(perda, 2) as perda 
                        FROM vendas_calculos 
                        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NOT NULL 
                        LIMIT 3"""
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).fetchall()
                for row in amostra_preench:
                    print(
                        f"  ID:{row[0]} | {row[1]}/{row[2]} | tx_venda:{row[3]}% tx_calc:{row[4]}% perda:{row[5]}"
                    )

                if count_txcalc_null > 0:
                    print(f"\n[DEBUG] Amostra de registros SEM tx_calc (problema!):")
                    amostra_null = _conn.execute(
                        text(
                            """SELECT id_venda, bandeira, forma_pagamento, 
                               ROUND(tx_venda, 2) as tx_venda 
                            FROM vendas_calculos 
                            WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo AND tx_calc IS NULL 
                            LIMIT 3"""
                        ),
                        {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                    ).fetchall()
                    for row in amostra_null:
                        print(f"  ID:{row[0]} | {row[1]}/{row[2]} | tx_venda:{row[3]}%")

                print(f"[DEBUG] {'='*60}\n")

            # Buscar resultados atualizados para exibir (apenas primeiros 50 registros)
            t_final = time.time()
            print(
                f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Buscando amostra de 50 registros para exibir..."
            )
            # ⚡ OTIMIZAÇÃO: LIMIT no SQL (não carregar 1.5M registros para mostrar só 50!)
            # ⚡ NOVO: Sem JOIN! Todas as colunas já estão em vendas_calculos
            df_result = pd.read_sql(
                text(
                    """
                    SELECT id, id_venda, bandeira, forma_pagamento, 
                           vl_venda, tx_venda, desc_venda, vl_liq_venda,
                           tx_calc, desc_calc, vl_liq_calc, perda,
                           tx_rr_venda, vl_rr_venda, tx_rr_calc, vl_rr_calc, perda_rr,
                           ec_id, data_venda
                    FROM vendas_calculos
                    WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                    LIMIT 50
                """
                ),
                engine,
                params={"calc_id": proc_id, "calc_tipo": tipo_taxa},
            )
            tabulator.value = df_result

            # ⚡ OTIMIZAÇÃO: Calcular resumo estatístico direto no SQL (não carregar 1.5M para memória!)
            print(
                f"[DEBUG] [{time.strftime('%M:%S', time.gmtime(time.time()-t_inicio))}] Calculando estatísticas agregadas..."
            )
            with engine.connect() as _conn_resumo:
                resumo_stats = _conn_resumo.execute(
                    text(
                        """
                        SELECT 
                            COUNT(*) as qtd_vendas,
                            SUM(tx_venda) as total_tx_venda,
                            SUM(desc_calc) as total_desc_calc,
                            AVG(tx_calc) as media_tx_calc,
                            MIN(tx_calc) as min_tx_calc,
                            MAX(tx_calc) as max_tx_calc
                        FROM vendas_calculos
                        WHERE calc_id = :calc_id AND calc_tipo = :calc_tipo
                    """
                    ),
                    {"calc_id": proc_id, "calc_tipo": tipo_taxa},
                ).fetchone()

                if resumo_stats and resumo_stats[0] > 0:
                    resumo_dict = {
                        "Quantidade de vendas": [int(resumo_stats[0])],
                        "Total da venda": [
                            float(resumo_stats[1]) if resumo_stats[1] else 0.0
                        ],
                        "Total do desconto": [
                            float(resumo_stats[2]) if resumo_stats[2] else 0.0
                        ],
                        "% aferido (média)": [
                            round(float(resumo_stats[3]), 2) if resumo_stats[3] else 0.0
                        ],
                        "Menor %": [
                            round(float(resumo_stats[4]), 2) if resumo_stats[4] else 0.0
                        ],
                        "Maior %": [
                            round(float(resumo_stats[5]), 2) if resumo_stats[5] else 0.0
                        ],
                    }
                    df_resumo = pd.DataFrame(resumo_dict)
                    resumo_tabulator.value = df_resumo
                else:
                    resumo_tabulator.value = pd.DataFrame()

            # 📊 Resumo de performance final
            tempo_total = time.time() - t_inicio
            print(f"\n{'='*60}")
            print(f"[DEBUG] ✅ PROCESSAMENTO CONCLUÍDO com sucesso!")
            print(
                f"[DEBUG] ⏱️  TEMPO TOTAL: {tempo_total:.2f}s ({tempo_total/60:.1f} min)"
            )
            print(f"{'='*60}\n")

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

        # Tabulator com checkboxes
        tab_gestao = pn.widgets.Tabulator(
            pd.DataFrame(),
            selectable="checkbox",  # Habilita checkboxes para seleção múltipla
            header_filters=True,  # Habilita filtros no cabeçalho
            height=350,
            page_size=30,
            sizing_mode="stretch_width",
            configuration={
                "selectableRangeMode": "click",  # Permite selecionar múltiplas linhas
            },
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
                pn.Row(
                    btn_preview,
                    btn_processar,
                    sizing_mode="stretch_width",
                    align="center",
                ),
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
