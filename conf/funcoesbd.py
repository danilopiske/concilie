from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Any
from sqlalchemy.engine import Engine
from sqlalchemy import text
from datetime import datetime

# Importa adaptador SQL híbrido
from conf import sql_adapter


# ==============================
# Helper functions - Híbrido MySQL/SQLite
# ==============================
# IMPORTANTE: Estas funções agora suportam ambos os bancos
# Mantidas para compatibilidade com código existente


# Busca detalhes de um processamento específico por id
def listar_processamentos_detalhado_por_id(
    engine: Engine, processamentoid: str
) -> list:
    sql = """
        SELECT
            id_processamento as processamentoid,
            cliente_id,
            ec_id,
            descricao,
            data_processamento
        FROM controle_processamentos
        WHERE id_processamento = :processamentoid
        ORDER BY data_processamento DESC, id_processamento DESC
    """
    return fetch_all(engine, sql, {"processamentoid": processamentoid})


def _normalize_text_compare(engine: Engine, column: str, param: str) -> str:
    """Retorna SQL para comparação case-insensitive de texto (MySQL/SQLite)

    Args:
        engine: Engine SQLAlchemy
        column: Nome da coluna a comparar
        param: Nome do parâmetro (ex: 'ctx')

    Returns:
        SQL para comparação case-insensitive
    """
    return sql_adapter.normalize_text_compare(engine, column, param)


def _date_format_sql(engine: Engine, column: str, format_str: str) -> str:
    """Retorna SQL de formatação de data (MySQL/SQLite)

    Args:
        engine: Engine SQLAlchemy
        column: Nome da coluna de data
        format_str: Formato MySQL (ex: '%Y-%m-%d', '%Y-%m')

    Returns:
        SQL formatado
    """
    return sql_adapter.date_format_sql(engine, column, format_str)


def _concat_sql(engine: Engine, *args: str) -> str:
    """Retorna SQL de concatenação (MySQL/SQLite)

    Args:
        engine: Engine SQLAlchemy
        *args: Expressões SQL a concatenar

    Returns:
        SQL de concatenação
    """
    return sql_adapter.concat_sql(engine, *args)


def _insert_ignore_sql(engine: Engine, table: str, columns: str, values: str) -> str:
    """Retorna SQL de INSERT IGNORE (MySQL/SQLite)"""
    return sql_adapter.insert_ignore_sql(engine, table, columns, values)


def _year_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para extrair ano de uma data (MySQL/SQLite)"""
    return sql_adapter.year_sql(engine, column)


def _month_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para extrair mês de uma data (MySQL/SQLite)"""
    return sql_adapter.month_sql(engine, column)


def _quarter_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para calcular trimestre de uma data (MySQL/SQLite)"""
    return sql_adapter.quarter_sql(engine, column)


def _semester_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para calcular semestre de uma data (MySQL/SQLite)"""
    return sql_adapter.semester_sql(engine, column)


def _get_table_columns(engine: Engine, table_name: str) -> str:
    """Retorna SQL para buscar colunas de uma tabela (MySQL/SQLite)"""
    return sql_adapter.get_table_columns_sql(engine, table_name)


def _current_timestamp_sql(engine: Engine) -> str:
    """Retorna SQL para timestamp atual (MySQL/SQLite)"""
    return sql_adapter.current_timestamp_sql(engine)


def _adapt_sql(engine: Engine, sql: str) -> str:
    """Adapta SQL do MySQL para SQLite quando necessário"""
    if sql_adapter.get_db_type(engine) == "sqlite":
        # Substitui INSERT IGNORE por INSERT OR IGNORE
        sql = sql.replace("INSERT IGNORE", "INSERT OR IGNORE")
    return sql


def _upsert_sql(
    engine: Engine, table: str, columns: List[str], update_columns: List[str]
) -> str:
    """Retorna SQL de UPSERT (MySQL/SQLite)"""
    return sql_adapter.upsert_sql(engine, table, columns, update_columns)


# ==============================
# Recebíveis - Processados e Filtrados
# ==============================


def recebiveis_processados_bulk_insert(engine: Engine, df, progress_callback=None) -> int:
    """Insere recebíveis processados em massa (MySQL/SQLite)"""
    # Usar tipo adequado ao banco
    decimal_type = sql_adapter.get_decimal_type(engine)

    # Definir tipos explícitos para colunas decimais/numéricas
    dtype_map = {}

    # Colunas monetárias e percentuais que precisam de precisão
    decimal_columns = [
        "valor_liquido",
        "valor_bruto",
        "taxa_percentual",
        "taxa_valor",
        "desconto_antecipacao",
        "valor_original",
    ]

    for col in decimal_columns:
        if col in df.columns:
            # MySQL: DECIMAL(18,2), SQLite: REAL
            if sql_adapter.get_db_type(engine) == "mysql":
                from sqlalchemy.types import DECIMAL

                dtype_map[col] = DECIMAL(18, 2)
            else:
                dtype_map[col] = REAL

    from sqlalchemy import inspect
    inspector = inspect(engine)
    valid_cols = [c["name"] for c in inspector.get_columns("recebiveis_processados")]
    total_rows = len(df)
    inserted = 0
    chunksize = 1000 # Further reduced chunksize to 1000 to minimize lock contention

    for i in range(0, total_rows, chunksize):
        chunk = df.iloc[i : i + chunksize]
        chunk.to_sql(
            name="recebiveis_processados",
            con=engine,
            index=False,
            if_exists="append",
            chunksize=chunksize,
            dtype=dtype_map if dtype_map else None,
        )
        inserted += len(chunk)
        if progress_callback:
            progress = int((inserted / total_rows) * 100)
            progress_callback(progress, f"Gravando recebíveis processados ({inserted}/{total_rows})...")
        print(f"[DEBUG][BULK_INSERT] Inseridos {inserted}/{total_rows} recebíveis processados...")

    return inserted


def recebiveis_filtrados_bulk_insert(engine: Engine, df, progress_callback=None) -> int:
    """Insere recebíveis filtrados em massa (MySQL/SQLite)"""
    # Usar tipo adequado ao banco
    decimal_type = sql_adapter.get_decimal_type(engine)

    # Definir tipos explícitos para colunas decimais/numéricas
    dtype_map = {}

    # Colunas monetárias e percentuais que precisam de precisão
    decimal_columns = [
        "valor_liquido",
        "valor_bruto",
        "taxa_percentual",
        "taxa_valor",
        "desconto_antecipacao",
        "valor_original",
    ]

    for col in decimal_columns:
        if col in df.columns:
            # MySQL: DECIMAL(18,2), SQLite: REAL
            if sql_adapter.get_db_type(engine) == "mysql":
                from sqlalchemy.types import DECIMAL

                dtype_map[col] = DECIMAL(18, 2)
            else:
                dtype_map[col] = REAL

    from sqlalchemy import inspect
    inspector = inspect(engine)
    valid_cols = [c["name"] for c in inspector.get_columns("recebiveis_filtrados")]
    total_rows = len(df)
    inserted = 0
    chunksize = 1000 # Further reduced chunksize to 1000 to minimize lock contention

    for i in range(0, total_rows, chunksize):
        chunk = df.iloc[i : i + chunksize]
        chunk.to_sql(
            name="recebiveis_filtrados",
            con=engine,
            index=False,
            if_exists="append",
            chunksize=chunksize,
            dtype=dtype_map if dtype_map else None,
        )
        inserted += len(chunk)
        if progress_callback:
            progress = int((inserted / total_rows) * 100)
            progress_callback(progress, f"Gravando recebíveis filtrados ({inserted}/{total_rows})...")
        print(f"[DEBUG][BULK_INSERT] Inseridos {inserted}/{total_rows} recebíveis filtrados...")

    return inserted


def recebiveis_remover_duplicadas(
    engine: Engine, nome_tabela: str, processamento_id: str, df_cols: List[str]
) -> None:
    """Remove duplicadas de recebíveis (MySQL/SQLite)"""
    if nome_tabela not in {"recebiveis_processados", "recebiveis_filtrados"}:
        raise ValueError("Nome de tabela inválido para recebíveis.")

    # Colunas para deduplicação (fixas)
    colunas_para_groupby = [
        sql_adapter.quote_identifier(engine, "recebivel_id"),
        sql_adapter.quote_identifier(engine, "lancamento"),
        sql_adapter.quote_identifier(engine, "valor_liquido"),
        sql_adapter.quote_identifier(engine, "ec_id"),
        sql_adapter.quote_identifier(engine, "data_recebivel"),
        sql_adapter.quote_identifier(engine, "data_pagamento"),
    ]

    if not colunas_para_groupby:
        return

    group_by_cols = ", ".join(colunas_para_groupby)
    
    # Identificar o tipo de banco
    db_type = sql_adapter.get_db_type(engine)

    if db_type == "sqlite":
        # SQLite: sintaxe mais simples
        sql = f"""
        DELETE FROM {nome_tabela}
        WHERE id NOT IN (
            SELECT MIN(id) FROM {nome_tabela}
            WHERE processamentoid = :id_proc
            GROUP BY {group_by_cols}
        )
        AND processamentoid = :id_proc
        """
        exec_sql(engine, sql, {"id_proc": processamento_id})
    else:
        # MySQL: Otimizado com TEMPORARY TABLE para evitar lock timeouts em grandes volumes
        # 1. Criar tabela temporária com IDs a manter
        sql_tmp = f"""
        CREATE TEMPORARY TABLE tmp_ids_to_keep AS
        SELECT MIN(id) as keep_id FROM {nome_tabela}
        WHERE processamentoid = :id_proc
        GROUP BY {group_by_cols}
        """
        
        # 2. Deletar os que não estão na tabela temporária usando JOIN (mais rápido que NOT IN)
        sql_del = f"""
        DELETE r1 FROM {nome_tabela} r1
        LEFT JOIN tmp_ids_to_keep r2 ON r1.id = r2.keep_id
        WHERE r1.processamentoid = :id_proc
        AND r2.keep_id IS NULL
        """
        
        # 2.5 Criar índice na tabela temporária para acelerar o JOIN
        sql_idx = "CREATE INDEX idx_keep_id ON tmp_ids_to_keep(keep_id)"
        
        # 3. Remover tabela temporária
        sql_drop = "DROP TEMPORARY TABLE IF EXISTS tmp_ids_to_keep"
        
        print(f"[DEBUG][DEDUP] Executando deduplicação otimizada (temp table) em {nome_tabela} para proc {processamento_id}...")
        with engine.begin() as conn:
            # Aumentar timeout para esta transação específica
            conn.execute(text("SET SESSION innodb_lock_wait_timeout = 300"))
            conn.execute(text(sql_tmp), {"id_proc": processamento_id})
            conn.execute(text(sql_idx))
            conn.execute(text(sql_del), {"id_proc": processamento_id})
            conn.execute(text(sql_drop))

# ...existing code...


# ==============================
# Listar Processamentos Detalhado
# ==============================
def listar_processamentos_detalhado(engine: Engine, limite: int = 100) -> list:
    """
    Lista todos os processamentos com detalhes para a interface de gestão.

    Args:
        engine: Conexão com o banco de dados
        limite: Número máximo de processamentos para retornar (padrão: 100)

    Returns:
        Lista de processamentos com estatísticas
    """
    # Primeiro obtemos apenas a lista básica de processamentos (mais rápido)
    sql_processamentos = """
        SELECT
            id_processamento as processamentoid,
            cliente_id,
            ec_id,
            descricao,
            data_processamento
        FROM controle_processamentos
        ORDER BY data_processamento DESC, id_processamento DESC
        LIMIT :limite
    """

    processamentos = fetch_all(engine, sql_processamentos, {"limite": limite})

    # Sem processamentos, retorna lista vazia
    if not processamentos:
        return []

    # Agora obtemos as estatísticas para cada processamento individualmente
    for proc in processamentos:
        proc_id = proc.get("processamentoid")

        # Estatísticas de vendas processadas
        sql_proc = """
            SELECT COUNT(*) as qtd
            FROM vendas_processadas
            WHERE processamentoid = :proc_id
        """
        result = fetch_all(engine, sql_proc, {"proc_id": proc_id})
        proc["qtd_processadas"] = (
            result[0]["qtd"] if result and result[0]["qtd"] is not None else 0
        )

        # Estatísticas de vendas filtradas
        sql_filt = """
            SELECT COUNT(*) as qtd
            FROM vendas_filtradas
            WHERE processamentoid = :proc_id
        """
        result = fetch_all(engine, sql_filt, {"proc_id": proc_id})
        proc["qtd_filtradas"] = (
            result[0]["qtd"] if result and result[0]["qtd"] is not None else 0
        )

        # Total
        proc["total_linhas"] = proc.get("qtd_processadas", 0) + proc.get(
            "qtd_filtradas", 0
        )

        # Datas (apenas se houver registros)
        proc["primeira_data"] = None
        proc["ultima_data"] = None
        if proc["qtd_processadas"] > 0:
            sql_datas = """
                SELECT
                    MIN(data_processamento) as primeira_data,
                    MAX(data_processamento) as ultima_data
                FROM vendas_processadas
                WHERE processamentoid = :proc_id
            """
            result = fetch_all(engine, sql_datas, {"proc_id": proc_id})
            if result:
                proc["primeira_data"] = result[0].get("primeira_data")
                proc["ultima_data"] = result[0].get("ultima_data")

        # Garante que todos os campos esperados existem
        for k in [
            "qtd_processadas",
            "qtd_filtradas",
            "total_linhas",
            "primeira_data",
            "ultima_data",
        ]:
            if k not in proc:
                proc[k] = 0 if "qtd" in k or "total" in k else None

    return processamentos


# ==============================
# Listar IDs de Processamento
# ==============================
def listar_processamentoids(engine: Engine) -> list:
    """Lista todos os IDs de processamento existentes, mais recentes primeiro."""
    rows = fetch_all(
        engine,
        """
        SELECT id_processamento FROM controle_processamentos
        ORDER BY data_processamento DESC, id_processamento DESC
        """,
    )
    return [r["id_processamento"] for r in rows]


# =========================
# Helpers básicos de acesso
# =========================


@contextmanager
def get_conn(engine: Engine):
    """Context manager for database connections."""
    with engine.begin() as conn:
        yield conn


def exec_sql(engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None) -> None:
    """Executes a SQL statement."""
    sql = _adapt_sql(engine, sql)  # Adapta SQL para SQLite quando necessário
    with get_conn(engine) as conn:
        # Increase lock wait timeout for MySQL for this session
        if sql_adapter.get_db_type(engine) == "mysql":
            try:
                conn.execute(text("SET SESSION innodb_lock_wait_timeout = 300"))
            except Exception as e_timeout:
                print(f"[WARNING] Could not set innodb_lock_wait_timeout: {e_timeout}")
                
        conn.execute(text(sql), params or {})


def fetch_one(
    engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Fetches a single row from a SQL query."""
    sql = _adapt_sql(engine, sql)  # Adapta SQL para SQLite quando necessário
    with get_conn(engine) as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def fetch_all(
    engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Fetches all rows from a SQL query."""
    sql = _adapt_sql(engine, sql)  # Adapta SQL para SQLite quando necessário
    with get_conn(engine) as conn:
        rows = conn.execute(text(sql), params or {}).mappings().all()
        return [dict(r) for r in rows]


# ==================
# De-Para de colunas
# ==================


def depara_listar(
    engine: Engine, contexto: str = "", tipo_origem: str = ""
) -> List[Dict[str, Any]]:
    sql = "SELECT id, origem_nome, destino_nome, contexto, tipo_origem, ativo, criado_por, criado_em, atualizado_em, tipo_preenchimento, valor_padrao FROM depara_colunas"
    filters = []
    params = {}
    if contexto:
        filters.append(_normalize_text_compare(engine, "contexto", "ctx"))
        params["ctx"] = contexto
    if tipo_origem:
        filters.append("tipo_origem = :tipo")
        params["tipo"] = tipo_origem

    if filters:
        sql += " WHERE " + " AND ".join(filters)
    sql += " ORDER BY ativo DESC, contexto, tipo_origem, destino_nome ASC"
    return fetch_all(engine, sql, params)


def depara_inserir(
    engine: Engine,
    *,
    origem_nome: Optional[str],
    destino_nome: str,
    contexto: str = "",
    tipo_origem: str = "V",
    ativo: int = 1,
    criado_por: Optional[str] = None,
    tipo_preenchimento: str = "importado",
    valor_padrao: Optional[str] = None,
) -> None:
    sql = "INSERT INTO depara_colunas (origem_nome, destino_nome, contexto, tipo_origem, ativo, criado_por, tipo_preenchimento, valor_padrao) VALUES (:origem, :destino, :contexto, :tipo, :ativo, :criado_por, :tipo_preenchimento, :valor_padrao)"
    contexto_norm = (contexto or "").strip()
    params = {
        "origem": (origem_nome or "").strip() if origem_nome else None,
        "destino": (destino_nome or "").strip(),
        "contexto": contexto_norm,
        "tipo": (tipo_origem or "V"),
        "ativo": int(ativo),
        "criado_por": criado_por,
        "tipo_preenchimento": tipo_preenchimento,
        "valor_padrao": valor_padrao,
    }
    exec_sql(engine, sql, params)
    # Proteção extra: nunca deixar código duplicado ou solto após a função


def depara_atualizar(
    engine: Engine,
    depara_id: int,
    *,
    origem_nome: Optional[str],
    destino_nome: str,
    contexto: str = "",
    tipo_origem: str = "V",
    ativo: int = 1,
    tipo_preenchimento: str = "importado",
    valor_padrao: Optional[str] = None,
) -> None:
    sql = "UPDATE depara_colunas SET origem_nome = :origem, destino_nome = :destino, contexto = :contexto, tipo_origem = :tipo, ativo = :ativo, tipo_preenchimento = :tipo_preenchimento, valor_padrao = :valor_padrao WHERE id = :id"
    contexto_norm = (contexto or "").strip()
    exec_sql(
        engine,
        sql,
        {
            "id": depara_id,
            "origem": (origem_nome or "").strip() if origem_nome else None,
            "destino": (destino_nome or "").strip(),
            "contexto": contexto_norm,
            "tipo": (tipo_origem or "V"),
            "ativo": int(ativo),
            "tipo_preenchimento": tipo_preenchimento,
            "valor_padrao": valor_padrao,
        },
    )


def depara_deletar(engine: Engine, depara_id: int) -> None:
    exec_sql(engine, "DELETE FROM depara_colunas WHERE id = :id", {"id": depara_id})


def depara_buscar_por_chave(
    engine: Engine, *, origem_nome: str, contexto: str = "", tipo_origem: str = "V"
) -> Optional[Dict[str, Any]]:
    sql = f"SELECT id, origem_nome, destino_nome, contexto, tipo_origem, ativo FROM depara_colunas WHERE origem_nome = :origem AND {_normalize_text_compare(engine, 'contexto', 'contexto')} AND tipo_origem = :tipo LIMIT 1"
    return fetch_one(
        engine,
        sql,
        {
            "origem": (origem_nome or "").strip(),
            "contexto": (contexto or "").strip(),
            "tipo": (tipo_origem or "V"),
        },
    )


def depara_carregar_mapa_completo(
    engine: Engine, contexto: str = "", tipo_origem: str = "V"
) -> List[Dict[str, Any]]:
    sql = "SELECT origem_nome, destino_nome, tipo_preenchimento, valor_padrao, ativo FROM depara_colunas WHERE ativo = 1"
    params = {}
    if contexto:
        # Usar comparação case-insensitive
        sql += f" AND {_normalize_text_compare(engine, 'contexto', 'ctx')}"
        params["ctx"] = contexto
    if tipo_origem:
        sql += " AND tipo_origem = :tipo"
        params["tipo"] = tipo_origem

    # Adicionar filtro para origem_nome válido
    sql += " AND origem_nome IS NOT NULL AND origem_nome != ''"

    return fetch_all(engine, sql, params)


# ==============
# Clientes / ECs
# ==============


def clientes_listar(engine: Engine) -> List[Dict[str, Any]]:
    sql = "SELECT cliente_id, nome_fantasia FROM clientes ORDER BY nome_fantasia;"
    return fetch_all(engine, sql)


def ecs_por_cliente(engine: Engine, cliente_id: int) -> List[str]:
    sql = "SELECT ec_id FROM ecs_cliente WHERE cliente_id = :cliente_id ORDER BY ec_id;"
    rows = fetch_all(engine, sql, {"cliente_id": cliente_id})
    return [row["ec_id"] for row in rows]


def cliente_detalhes_por_id(
    engine: Engine, cliente_id: int
) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT
        c.cliente_id, c.nome_fantasia, c.razao_social, c.cnpj,
        e.logradouro, e.numero, e.complemento, e.bairro, e.cidade, e.uf_id,
        ct.telefone1, ct.email1,
        db.banco, db.agencia, db.conta
    FROM clientes c
    LEFT JOIN enderecos e ON c.cliente_id = e.cliente_id
    LEFT JOIN contatos ct ON c.cliente_id = ct.cliente_id
    LEFT JOIN dados_bancarios db ON c.cliente_id = db.cliente_id
    WHERE c.cliente_id = :cliente_id;
    """
    return fetch_one(engine, sql, {"cliente_id": cliente_id})


def cliente_deletar(engine: Engine, cliente_id: int) -> None:
    """
    Deleta um cliente e todos os seus dados relacionados.
    Usa abordagem em duas etapas para evitar problemas de collation:
    1. Busca ECs do cliente
    2. Deleta dados relacionados aos ECs
    3. Deleta outros dados do cliente
    4. Deleta o cliente
    """
    with get_conn(engine) as conn:
        # Passo 1: Obter lista de ECs do cliente
        result = conn.execute(
            text("SELECT ec_id FROM ecs_cliente WHERE cliente_id = :cliente_id"),
            {"cliente_id": cliente_id},
        )
        ecs = [row[0] for row in result.fetchall()]

        # Passo 2: Deletar dados relacionados aos ECs (se houver)
        if ecs:
            # Criar string com lista de ECs entre aspas para evitar problema de collation
            ecs_str = "', '".join(ecs)
            ecs_list = f"'{ecs_str}'"

            # 2.1. Deletar termos filtráveis
            conn.execute(
                text(f"DELETE FROM termos_filtraveis WHERE ec IN ({ecs_list})")
            )

            # 2.2. Deletar taxas
            conn.execute(text(f"DELETE FROM taxas WHERE ec IN ({ecs_list})"))

            # 2.3. Deletar bandeiras
            conn.execute(
                text(f"DELETE FROM bandeiras_cliente WHERE ec IN ({ecs_list})")
            )

        # Passo 3: Deletar ECs do cliente
        conn.execute(
            text("DELETE FROM ecs_cliente WHERE cliente_id = :cliente_id"),
            {"cliente_id": cliente_id},
        )

        # Passo 4: Deletar outros dados do cliente
        conn.execute(
            text("DELETE FROM enderecos WHERE cliente_id = :cliente_id"),
            {"cliente_id": cliente_id},
        )

        conn.execute(
            text("DELETE FROM contatos WHERE cliente_id = :cliente_id"),
            {"cliente_id": cliente_id},
        )

        conn.execute(
            text("DELETE FROM dados_bancarios WHERE cliente_id = :cliente_id"),
            {"cliente_id": cliente_id},
        )

        # Passo 5: Deletar cliente
        conn.execute(
            text("DELETE FROM clientes WHERE cliente_id = :cliente_id"),
            {"cliente_id": cliente_id},
        )


def cliente_salvar(engine: Engine, dados: Dict[str, Any], is_update: bool = False):
    cliente_data = {
        k: dados.get(k) for k in ["cliente_id", "nome_fantasia", "razao_social", "cnpj"]
    }
    endereco_data = {"cliente_id": dados.get("cliente_id"), **dados.get("endereco", {})}
    contatos_data = {"cliente_id": dados.get("cliente_id"), **dados.get("contatos", {})}
    bancario_data = {"cliente_id": dados.get("cliente_id"), **dados.get("bancario", {})}

    with get_conn(engine) as conn:
        if is_update:
            conn.execute(
                text(
                    "UPDATE clientes SET nome_fantasia = :nome_fantasia, razao_social = :razao_social, cnpj = :cnpj WHERE cliente_id = :cliente_id"
                ),
                cliente_data,
            )

            # Endereços - UPSERT compatível
            sql_endereco = _upsert_sql(
                engine,
                "enderecos",
                [
                    "cliente_id",
                    "logradouro",
                    "numero",
                    "complemento",
                    "bairro",
                    "cidade",
                    "uf_id",
                ],
                ["logradouro", "numero", "complemento", "bairro", "cidade", "uf_id"],
            )
            conn.execute(text(sql_endereco), endereco_data)

            # Contatos - UPSERT compatível
            sql_contatos = _upsert_sql(
                engine,
                "contatos",
                ["cliente_id", "telefone1", "email1"],
                ["telefone1", "email1"],
            )
            conn.execute(text(sql_contatos), contatos_data)

            # Dados bancários - UPSERT compatível
            sql_bancario = _upsert_sql(
                engine,
                "dados_bancarios",
                ["cliente_id", "banco", "agencia", "conta"],
                ["banco", "agencia", "conta"],
            )
            conn.execute(text(sql_bancario), bancario_data)
        else:
            conn.execute(
                text(
                    "INSERT INTO clientes (cliente_id, nome_fantasia, razao_social, cnpj) VALUES (:cliente_id, :nome_fantasia, :razao_social, :cnpj)"
                ),
                cliente_data,
            )
            conn.execute(
                text(
                    "INSERT INTO enderecos (cliente_id, logradouro, numero, complemento, bairro, cidade, uf_id) VALUES (:cliente_id, :logradouro, :numero, :complemento, :bairro, :cidade, :uf_id)"
                ),
                endereco_data,
            )
            conn.execute(
                text(
                    "INSERT INTO contatos (cliente_id, telefone1, email1) VALUES (:cliente_id, :telefone1, :email1)"
                ),
                contatos_data,
            )
            conn.execute(
                text(
                    "INSERT INTO dados_bancarios (cliente_id, banco, agencia, conta) VALUES (:cliente_id, :banco, :agencia, :conta)"
                ),
                bancario_data,
            )

        ecs_atuais = set(ecs_por_cliente(engine, dados.get("cliente_id")))
        ecs_desejados = set(dados.get("ecs", []))

        for ec in ecs_desejados - ecs_atuais:
            sql_ec = _insert_ignore_sql(engine, "ecs", "ec_id", ":ec_id")
            conn.execute(text(sql_ec), {"ec_id": ec})
            conn.execute(
                text(
                    "INSERT INTO ecs_cliente (cliente_id, ec_id) VALUES (:cliente_id, :ec_id)"
                ),
                {"cliente_id": dados.get("cliente_id"), "ec_id": ec},
            )

        for ec in ecs_atuais - ecs_desejados:
            conn.execute(
                text(
                    "DELETE FROM ecs_cliente WHERE cliente_id = :cliente_id AND ec_id = :ec_id"
                ),
                {"cliente_id": dados.get("cliente_id"), "ec_id": ec},
            )


# ======================
# Bandeiras
# ======================


def bandeiras_disponiveis_listar(engine: Engine) -> List[Dict[str, Any]]:
    sql = "SELECT nome, padrao FROM bandeiras_disponiveis ORDER BY nome;"
    return fetch_all(engine, sql)


def bandeira_disponivel_inserir(engine: Engine, nome: str, padrao: int = 0) -> bool:
    """Insere uma nova bandeira na tabela bandeiras_disponiveis."""
    sql = "INSERT INTO bandeiras_disponiveis (nome, padrao) VALUES (:nome, :padrao)"
    try:
        exec_sql(engine, sql, {"nome": nome.strip().upper(), "padrao": int(padrao)})
        return True
    except Exception as e:
        print(f"Erro ao inserir bandeira: {e}")
        return False


def bandeira_disponivel_atualizar(
    engine: Engine, nome_antigo: str, nome_novo: str, padrao: int = 0
) -> bool:
    """Atualiza uma bandeira na tabela bandeiras_disponiveis."""
    sql = "UPDATE bandeiras_disponiveis SET nome = :nome_novo, padrao = :padrao WHERE nome = :nome_antigo"
    try:
        exec_sql(
            engine,
            sql,
            {
                "nome_antigo": nome_antigo.strip().upper(),
                "nome_novo": nome_novo.strip().upper(),
                "padrao": int(padrao),
            },
        )
        return True
    except Exception as e:
        print(f"Erro ao atualizar bandeira: {e}")
        return False


def bandeira_disponivel_deletar(engine: Engine, nome: str) -> bool:
    """Deleta uma bandeira da tabela bandeiras_disponiveis."""
    sql = "DELETE FROM bandeiras_disponiveis WHERE nome = :nome"
    try:
        exec_sql(engine, sql, {"nome": nome.strip().upper()})
        return True
    except Exception as e:
        print(f"Erro ao deletar bandeira: {e}")
        return False


def bandeiras_por_ec(
    engine: Engine, ec: str, contexto: str = "padrao"
) -> Dict[str, int]:
    with get_conn(engine) as conn:
        sql = f"SELECT bandeira, ativo FROM bandeiras_cliente WHERE ec = :ec AND {_normalize_text_compare(engine, 'contexto', 'contexto')}"
        rows = (
            conn.execute(
                text(sql),
                {"ec": ec, "contexto": contexto},
            )
            .mappings()
            .all()
        )
        return {r["bandeira"]: r["ativo"] for r in rows}


def bandeiras_salvar_para_ec(
    engine: Engine, ec: str, bandeiras: Dict[str, int], contexto: str = "padrao"
) -> None:
    # MySQL: case-insensitive por padrão
    contexto_norm = contexto

    with get_conn(engine) as conn:
        for bandeira, ativo in bandeiras.items():
            sql_bandeira = _upsert_sql(
                engine,
                "bandeiras_cliente",
                ["ec", "bandeira", "ativo", "contexto"],
                ["ativo"],
            )
            conn.execute(
                text(sql_bandeira),
                {
                    "ec": ec,
                    "bandeira": bandeira,
                    "ativo": ativo,
                    "contexto": contexto_norm,
                },
            )


# ===================
# Termos filtráveis
# ===================


def termos_listar(
    engine: Engine, ec: str, contexto: str = "padrao", tipo: Optional[str] = None
) -> List[Dict[str, Any]]:
    with get_conn(engine) as conn:
        sql = f"SELECT termo, tipo FROM termos_filtraveis WHERE ec = :ec AND {_normalize_text_compare(engine, 'contexto', 'contexto')}"
        params = {"ec": ec, "contexto": contexto}

        if tipo:
            sql += " AND tipo = :tipo"
            params["tipo"] = tipo

        sql += " ORDER BY termo"
        result = conn.execute(text(sql), params)
        # SQLAlchemy 2.0+ `fetchall()` retorna uma lista de objetos `Row`
        # que se comportam como tuplas, mas também têm acesso por chave como dicionários.
        # A conversão explícita para dict é uma boa prática para desacoplar do tipo de objeto do DB.
        termos = [dict(row._mapping) for row in result.fetchall()]

        print(
            f"[DEBUG][termos_listar] Retornando {len(termos)} termos. Tipo do primeiro: {type(termos[0]) if termos else None}"
        )
        print(f"[DEBUG][termos_listar] Amostra: {termos[:5]}")
        return termos


def termo_adicionar(
    engine: Engine, ec: str, termo: str, contexto: str = "padrao", tipo: str = "v"
) -> None:
    sql = _insert_ignore_sql(
        engine,
        "termos_filtraveis",
        "ec, termo, contexto, tipo",
        ":ec, :termo, :contexto, :tipo",
    )
    exec_sql(
        engine,
        sql,
        {"ec": ec, "termo": termo.strip().lower(), "contexto": contexto, "tipo": tipo},
    )


def termo_excluir(
    engine: Engine, ec: str, termo: str, contexto: str = "padrao"
) -> None:
    import unicodedata

    # Normaliza termo para remover acentos e minúsculas
    def norm(s):
        return (
            unicodedata.normalize("NFKD", s)
            .encode("ASCII", "ignore")
            .decode("ASCII")
            .strip()
            .lower()
        )

    termo_norm = norm(termo)

    # Busca todos os contextos possíveis para o termo e EC
    sql = "SELECT id, termo, contexto FROM termos_filtraveis WHERE ec = :ec"
    termos = fetch_all(engine, sql, {"ec": ec})
    ids_para_excluir = [t["id"] for t in termos if norm(t["termo"]) == termo_norm]
    if ids_para_excluir:
        for id_ in ids_para_excluir:
            exec_sql(
                engine, "DELETE FROM termos_filtraveis WHERE id = :id", {"id": id_}
            )
    else:
        # fallback: tenta exclusão padrão
        sql = f"DELETE FROM termos_filtraveis WHERE ec = :ec AND termo = :termo AND {_normalize_text_compare(engine, 'contexto', 'contexto')}"
        exec_sql(
            engine,
            sql,
            {"ec": ec, "termo": termo.strip().lower(), "contexto": contexto},
        )


# ==============================
# Vendas e Processamento
# ==============================


def processamento_gerar_novo_id(
    engine: Engine, ec_id: str, now: datetime
) -> Tuple[str, datetime]:
    with get_conn(engine) as conn:
        total = conn.execute(
            text(
                "SELECT COUNT(*) AS total FROM controle_processamentos WHERE ec_id = :ec_id"
            ),
            {"ec_id": ec_id},
        ).scalar()
    sequencial = (total or 0) + 1
    return f"{ec_id}_{sequencial:04d} - {now.strftime('%d/%m/%Y %H:%M:%S')}", now


def processamento_salvar(
    engine: Engine,
    ec_id: str,
    cliente_id: int,
    id_processamento: str,
    descricao: str,
    data_processamento: datetime,
) -> None:
    exec_sql(
        engine,
        "INSERT INTO controle_processamentos (id_processamento, cliente_id, ec_id, descricao, data_processamento) VALUES (:id_processamento, :cliente_id, :ec_id, :descricao, :data_processamento)",
        {
            "id_processamento": id_processamento,
            "cliente_id": cliente_id,
            "ec_id": ec_id,
            "descricao": descricao,
            "data_processamento": data_processamento,
        },
    )


def deletar_processamento(engine: Engine, id_processamento: str) -> Dict[str, int]:
    """
    Deleta um processamento e todos os dados relacionados a ele.

    Args:
        engine: Conexão com o banco de dados
        id_processamento: ID do processamento a ser deletado

    Returns:
        Dict[str, int]: Dicionário com contagem de registros excluídos
    """
    try:
        # Primeiro, conta quantos registros serão excluídos (VENDAS)
        filtradas_count = fetch_one(
            engine,
            "SELECT COUNT(*) as total FROM vendas_filtradas WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )
        vendas_filtradas = filtradas_count["total"] if filtradas_count else 0

        processadas_count = fetch_one(
            engine,
            "SELECT COUNT(*) as total FROM vendas_processadas WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )
        vendas_processadas = processadas_count["total"] if processadas_count else 0

        diversas_count = fetch_one(
            engine,
            "SELECT COUNT(*) as total FROM vendas_diversas WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )
        vendas_diversas = diversas_count["total"] if diversas_count else 0

        # Conta quantos registros serão excluídos (RECEBÍVEIS)
        recebiveis_proc_count = fetch_one(
            engine,
            "SELECT COUNT(*) as total FROM recebiveis_processados WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )
        recebiveis_processados = (
            recebiveis_proc_count["total"] if recebiveis_proc_count else 0
        )

        recebiveis_filt_count = fetch_one(
            engine,
            "SELECT COUNT(*) as total FROM recebiveis_filtrados WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )
        recebiveis_filtrados = (
            recebiveis_filt_count["total"] if recebiveis_filt_count else 0
        )

        # Deleta as vendas filtradas relacionadas ao processamento
        exec_sql(
            engine,
            "DELETE FROM vendas_filtradas WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )

        # Deleta as vendas diversas relacionadas ao processamento
        exec_sql(
            engine,
            "DELETE FROM vendas_diversas WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )

        # Deleta os cálculos relacionados às vendas do processamento
        exec_sql(
            engine,
            """
            DELETE FROM vendas_calculos
            WHERE id_venda IN (
                SELECT id FROM vendas_processadas
                WHERE processamentoid = :id_processamento
            )
            """,
            {"id_processamento": id_processamento},
        )

        # Deleta as vendas processadas relacionadas ao processamento
        exec_sql(
            engine,
            "DELETE FROM vendas_processadas WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )

        # Deleta os recebíveis processados relacionados ao processamento
        exec_sql(
            engine,
            "DELETE FROM recebiveis_processados WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )

        # Deleta os recebíveis filtrados relacionados ao processamento
        exec_sql(
            engine,
            "DELETE FROM recebiveis_filtrados WHERE processamentoid = :id_processamento",
            {"id_processamento": id_processamento},
        )

        # Por fim, deleta o registro do processamento
        exec_sql(
            engine,
            "DELETE FROM controle_processamentos WHERE id_processamento = :id_processamento",
            {"id_processamento": id_processamento},
        )

        return {
            "vendas_filtradas": vendas_filtradas,
            "vendas_processadas": vendas_processadas,
            "vendas_diversas": vendas_diversas,
            "recebiveis_processados": recebiveis_processados,
            "recebiveis_filtrados": recebiveis_filtrados,
        }
    except Exception as e:
        print(f"Erro ao deletar processamento {id_processamento}: {e}")
        raise Exception(f"Falha ao deletar processamento: {e}")


def vendas_processadas_bulk_insert(engine: Engine, df, progress_callback=None) -> int:
    from sqlalchemy.types import DECIMAL, Float

    # Definir tipos explícitos para colunas decimais/numéricas
    dtype_map = {}

    # Colunas monetárias e percentuais que precisam de precisão exata
    decimal_columns = [
        "Valor_da_venda",
        "Valor_descontado",
        "Valor_liquido",
        "Valor_RR",
        "Taxas_Perc",
        "Taxas_RR",
        "Valor_bruto_parcela",
        "Valor_liquido_parcela",
    ]

    for col in decimal_columns:
        if col in df.columns:
            dtype_map[col] = DECIMAL(
                18, 2
            )  # Precisão de 18 dígitos, 2 casas decimais (padrão monetário)

    from sqlalchemy import inspect
    inspector = inspect(engine)
    valid_cols = [c["name"] for c in inspector.get_columns("vendas_processadas")]
    df = df[[c for c in df.columns if c in valid_cols]]

    total_rows = len(df)
    inserted = 0
    chunksize = 1000 # Further reduced chunksize to prevent lock timeouts and long-running transactions
    
    for i in range(0, total_rows, chunksize):
        chunk = df.iloc[i : i + chunksize]
        chunk.to_sql(
            name="vendas_processadas",
            con=engine,
            index=False,
            if_exists="append",
            chunksize=chunksize,
            dtype=dtype_map if dtype_map else None,
        )
        inserted += len(chunk)
        if progress_callback:
            progress = int((inserted / total_rows) * 100)
            progress_callback(progress, f"Gravando vendas processadas ({inserted}/{total_rows})...")
        print(f"[DEBUG][BULK_INSERT] Inseridas {inserted}/{total_rows} vendas processadas...")

    return inserted


def vendas_filtradas_bulk_insert(engine: Engine, df, progress_callback=None) -> int:
    from sqlalchemy.types import DECIMAL, Float

    # Definir tipos explícitos para colunas decimais/numéricas
    dtype_map = {}

    # Colunas monetárias e percentuais que precisam de precisão exata
    decimal_columns = [
        "Valor_da_venda",
        "Valor_descontado",
        "Valor_liquido",
        "Valor_RR",
        "Taxas_Perc",
        "Taxas_RR",
        "Valor_bruto_parcela",
        "Valor_liquido_parcela",
    ]

    for col in decimal_columns:
        if col in df.columns:
            dtype_map[col] = DECIMAL(
                18, 2
            )  # Precisão de 18 dígitos, 2 casas decimais (padrão monetário)

    from sqlalchemy import inspect
    inspector = inspect(engine)
    valid_cols = [c["name"] for c in inspector.get_columns("vendas_filtradas")]
    df = df[[c for c in df.columns if c in valid_cols]]

    total_rows = len(df)
    inserted = 0
    chunksize = 1000 # Further reduced chunksize to prevent lock timeouts and long-running transactions
    
    for i in range(0, total_rows, chunksize):
        chunk = df.iloc[i : i + chunksize]
        chunk.to_sql(
            name="vendas_filtradas",
            con=engine,
            index=False,
            if_exists="append",
            chunksize=chunksize,
            dtype=dtype_map if dtype_map else None,
        )
        inserted += len(chunk)
        if progress_callback:
            progress = int((inserted / total_rows) * 100)
            progress_callback(progress, f"Gravando vendas filtradas ({inserted}/{total_rows})...")
        print(f"[DEBUG][BULK_INSERT] Inseridas {inserted}/{total_rows} vendas filtradas...")

    return inserted


def vendas_diversas_bulk_insert(engine: Engine, df) -> int:
    from sqlalchemy.types import DECIMAL, Float

    # Definir tipos explícitos para colunas decimais/numéricas
    dtype_map = {}

    # Colunas monetárias e percentuais que precisam de precisão exata
    decimal_columns = [
        "Valor_da_venda",
        "Valor_descontado",
        "Valor_liquido",
        "Valor_RR",
        "Taxas_Perc",
        "Taxas_RR",
        "Valor_bruto_parcela",
        "Valor_liquido_parcela",
    ]

    for col in decimal_columns:
        if col in df.columns:
            dtype_map[col] = DECIMAL(
                18, 2
            )  # Precisão de 18 dígitos, 2 casas decimais (padrão monetário)

    from sqlalchemy import inspect
    inspector = inspect(engine)
    valid_cols = [c["name"] for c in inspector.get_columns("vendas_diversas")]
    df = df[[c for c in df.columns if c in valid_cols]]

    df.to_sql(
        name="vendas_diversas",
        con=engine,
        index=False,
        if_exists="append",
        chunksize=10000,
        dtype=dtype_map if dtype_map else None,
    )
    return len(df)


def vendas_remover_duplicadas(
    engine: Engine, nome_tabela: str, processamento_id: str, df_cols: List[str]
) -> None:
    if nome_tabela not in {"vendas_processadas", "vendas_filtradas", "vendas_diversas"}:
        raise ValueError("Tabela inválida para remoção de duplicadas.")

    colunas_a_ignorar = {
        "id",
        "data_processamento",
        "usuario_processamento",
        "arquivo_origem",
    }
    colunas_para_groupby = [
        f"`{col}`" for col in df_cols if col not in colunas_a_ignorar
    ]

    if not colunas_para_groupby:
        return

    # Identificar o tipo de banco
    db_type = sql_adapter.get_db_type(engine)
    
    if db_type == "sqlite":
        # SQLite: sintaxe compatível
        sql = f"""
        DELETE FROM {nome_tabela}
        WHERE id IN (
            SELECT v.id FROM {nome_tabela} v
            LEFT JOIN vendas_calculos c ON v.id = c.id_venda
            WHERE v.processamentoid = :id_proc AND c.id_venda IS NULL
            AND v.id NOT IN (
                SELECT MIN(id) FROM {nome_tabela}
                WHERE processamentoid = :id_proc
                GROUP BY {", ".join(colunas_para_groupby)}
            )
        )
        """
        exec_sql(engine, sql, {"id_proc": processamento_id})
    else:
        # MySQL: Otimizado com TEMPORARY TABLE para evitar lock timeouts em grandes volumes
        # join_conditions = " AND ".join([f"v1.{col} <=> v2.{col}" for col in colunas_para_groupby])
        
        # 1. Criar tabela temporária com IDs a manter
        sql_tmp = f"""
        CREATE TEMPORARY TABLE tmp_vendas_to_keep AS
        SELECT MIN(id) as keep_id FROM {nome_tabela}
        WHERE processamentoid = :id_proc
        GROUP BY {", ".join(colunas_para_groupby)}
        """
        
        # 2. Deletar os duplicados que NÃO têm cálculos associados
        sql_del = f"""
        DELETE v1 FROM {nome_tabela} v1
        LEFT JOIN tmp_vendas_to_keep v2 ON v1.id = v2.keep_id
        LEFT JOIN vendas_calculos c ON v1.id = c.id_venda
        WHERE v1.processamentoid = :id_proc
        AND v2.keep_id IS NULL
        AND c.id_venda IS NULL
        """
        
        # 3. Remover tabela temporária
        sql_drop = "DROP TEMPORARY TABLE IF EXISTS tmp_vendas_to_keep"
        
        # 4. Criar índice para melhorar a performance absurda do JOIN no DELETE
        sql_idx = "CREATE INDEX idx_keep_id ON tmp_vendas_to_keep(keep_id)"
        
        print(f"[DEBUG][DEDUP] Executando deduplicação otimizada (temp table) em {nome_tabela} para proc {processamento_id}...")
        with engine.begin() as conn:
            # Aumentar timeout para esta transação específica
            conn.execute(text("SET SESSION innodb_lock_wait_timeout = 300"))
            conn.execute(text(sql_tmp), {"id_proc": processamento_id})
            conn.execute(text(sql_idx))
            conn.execute(text(sql_del), {"id_proc": processamento_id})
            conn.execute(text(sql_drop))


# ==============================
# Listas Dinâmicas e Controle de Colunas
# ==============================


def listar_contextos(engine: Engine) -> List[str]:
    rows = fetch_all(
        engine, "SELECT DISTINCT contexto FROM depara_colunas ORDER BY contexto"
    )
    return [str(r["contexto"]).strip() for r in rows if r.get("contexto")]


def listar_colunas_vendas_processadas(engine: Engine) -> List[str]:
    """Lista todas as colunas da tabela vendas_processadas"""
    # MySQL: buscar colunas via INFORMATION_SCHEMA
    rows = fetch_all(engine, _get_table_columns(engine, "vendas_processadas"))
    return [r["coluna"] for r in rows]


def colunas_controle_deletar(engine: Engine, col_id: int) -> None:
    exec_sql(
        engine, "DELETE FROM vendas_colunas_controle WHERE id = :id", {"id": col_id}
    )


def colunas_controle_listar(
    engine: Engine, contexto: str = "", tipo_arquivo: str = ""
) -> List[Dict[str, Any]]:
    """Lista o controle de colunas, filtrando por contexto e tipo de arquivo."""
    params = {}
    sql = "SELECT id, campo, contexto, tipo_arquivo, preenchimento, mapeavel, ativo FROM vendas_colunas_controle WHERE 1=1"
    if contexto:
        sql += " AND contexto = :contexto"
        params["contexto"] = contexto
    if tipo_arquivo:
        sql += " AND tipo_arquivo = :tipo_arquivo"
        params["tipo_arquivo"] = tipo_arquivo
    sql += " ORDER BY contexto, tipo_arquivo, campo"
    return fetch_all(engine, sql, params)


# Altere a função colunas_controle_inserir
def colunas_controle_inserir(
    engine: Engine,
    *,
    campo: str,
    contexto: str,
    tipo_arquivo: str,
    preenchimento: str = "importado",
    mapeavel: int = 1,
    ativo: int = 1,
) -> None:
    sql = """
    INSERT INTO vendas_colunas_controle
      (campo, contexto, tipo_arquivo, preenchimento, mapeavel, ativo)
    VALUES
      (:campo, :contexto, :tipo_arquivo, :preenchimento, :mapeavel, :ativo)
    """
    exec_sql(
        engine,
        sql,
        {
            "campo": (campo or "").strip(),
            "contexto": (contexto or "").strip(),
            "tipo_arquivo": (tipo_arquivo or "V").strip(),
            "preenchimento": preenchimento,
            "mapeavel": int(mapeavel),
            "ativo": int(ativo),
        },
    )


def colunas_controle_atualizar(
    engine: Engine,
    col_id: int,
    *,
    campo: str,
    contexto: str,
    tipo_arquivo: str,
    preenchimento: str,
    mapeavel: int,
    ativo: int,
) -> None:
    sql = """
    UPDATE vendas_colunas_controle
       SET campo         = :campo,
           contexto      = :contexto,
           tipo_arquivo  = :tipo_arquivo,
           preenchimento = :preenchimento,
           mapeavel      = :mapeavel,
           ativo         = :ativo
     WHERE id = :id
    """
    exec_sql(
        engine,
        sql,
        {
            "id": col_id,
            "campo": (campo or "").strip(),
            "contexto": (contexto or "").strip(),
            "tipo_arquivo": (tipo_arquivo or "V").strip(),
            "preenchimento": preenchimento,
            "mapeavel": int(mapeavel),
            "ativo": int(ativo),
        },
    )


# Altere a função listar_colunas_mapeaveis
def listar_colunas_mapeaveis(
    engine: Engine, contexto: str, tipo_arquivo: str
) -> List[str]:
    """Lista colunas mapeáveis, agora filtrando por contexto E tipo de arquivo."""
    if not contexto or not tipo_arquivo:
        return []
    sql = f"""
        SELECT campo FROM vendas_colunas_controle
         WHERE ativo = 1 AND mapeavel = 1 AND {_normalize_text_compare(engine, 'contexto', 'contexto')} AND tipo_arquivo = :tipo_arquivo
         ORDER BY campo
    """
    rows = fetch_all(
        engine,
        sql,
        {"contexto": contexto, "tipo_arquivo": tipo_arquivo},
    )
    return [r["campo"] for r in rows]


# Altere a função colunas_controle_sincronizar
def colunas_controle_sincronizar(
    engine: Engine, contexto: str, tipo_arquivo: str
) -> Dict[str, int]:
    if not contexto or not tipo_arquivo:
        raise ValueError(
            "Contexto e Tipo de Arquivo são obrigatórios para sincronização."
        )

    # Usar função helper para obter colunas
    # MySQL: buscar colunas via INFORMATION_SCHEMA
    cols_rows = fetch_all(engine, _get_table_columns(engine, "vendas_processadas"))
    cols_real = set([r["coluna"] for r in cols_rows])

    cadastradas = {
        str(r["campo"])
        for r in fetch_all(
            engine,
            f"SELECT campo FROM vendas_colunas_controle WHERE {_normalize_text_compare(engine, 'contexto', 'ctx')} AND tipo_arquivo = :tipo",
            {"ctx": contexto, "tipo": tipo_arquivo},
        )
    }

    sistema = {
        "id",
        "processamentoid",
        "cliente_id",
        "ec_id",
        "arquivo_origem",
        "data_processamento",
        "usuario_processamento",
        "Filtrado",
    }
    calculado = {"tx_cad", "desc_cad", "vl_liq_cad", "tx_log", "desc_log", "vl_liq_log"}

    inseridos = 0
    for c in cols_real:
        if c in cadastradas:
            continue

        pr, mapv = "importado", 1
        if c in sistema:
            pr, mapv = "sistema", 0
        elif c in calculado:
            pr, mapv = "calculado", 0

        colunas_controle_inserir(
            engine,
            campo=c,
            contexto=contexto,
            tipo_arquivo=tipo_arquivo,
            preenchimento=pr,
            mapeavel=mapv,
            ativo=1,
        )
        inseridos += 1

    return {
        "inseridos": inseridos,
        "existentes": len(cadastradas),
        "total_real": len(cols_real),
    }


def taxa_adicionar(
    engine: Engine, taxa: Dict[str, Any], contexto: str = "padrao"
) -> bool:
    """
    Adiciona um novo registro de taxa na tabela.
    Retorna True em caso de sucesso.
    """
    sql = """
    INSERT INTO taxas (
        ec, bandeira, forma_pagamento, parcelado,
        parcelas_ini, parcelas_fim, data_ini, data_fim, taxa, contexto
    )
    VALUES (
        :ec, :bandeira, :forma_pagamento, :parcelado,
        :parcelas_ini, :parcelas_fim, :data_ini, :data_fim, :taxa, :contexto
    )
    """
    taxa["contexto"] = contexto
    try:
        exec_sql(engine, sql, taxa)
        return True
    except Exception as e:
        print(f"Erro ao inserir taxa: {e}")
        return False


def taxa_excluir(engine: Engine, taxa_id: int) -> bool:
    """
    Exclui um registro de taxa pelo seu ID.
    Retorna True se a exclusão for bem-sucedida.
    """
    try:
        exec_sql(engine, "DELETE FROM taxas WHERE id = :id", {"id": taxa_id})
        return True
    except Exception as e:
        print(f"Erro ao excluir taxa: {e}")
        return False


def taxas_por_ec(
    engine: Engine, ec: str, contexto: str = "padrao"
) -> List[Dict[str, Any]]:
    sql = f"""
    SELECT id, ec, bandeira, forma_pagamento, parcelado,
           parcelas_ini, parcelas_fim, data_ini, data_fim, taxa, contexto
      FROM taxas
     WHERE ec = :ec AND {_normalize_text_compare(engine, 'contexto', 'contexto')}
     ORDER BY bandeira, forma_pagamento, parcelas_ini
    """
    return fetch_all(engine, sql, {"ec": ec, "contexto": contexto})


def taxa_atualizar(engine: Engine, taxa_id: int, taxa: Dict[str, Any]) -> bool:
    """
    Atualiza um registro de taxa existente.
    Retorna True em caso de sucesso.
    """
    sql = """
    UPDATE taxas 
    SET ec = :ec, 
        bandeira = :bandeira, 
        forma_pagamento = :forma_pagamento, 
        parcelado = :parcelado,
        parcelas_ini = :parcelas_ini, 
        parcelas_fim = :parcelas_fim, 
        data_ini = :data_ini, 
        data_fim = :data_fim, 
        taxa = :taxa, 
        contexto = :contexto
    WHERE id = :id
    """
    taxa["id"] = taxa_id
    try:
        exec_sql(engine, sql, taxa)
        return True
    except Exception as e:
        print(f"Erro ao atualizar taxa: {e}")
        return False


def taxas_copiar(
    engine: Engine,
    ec_origem: str,
    ecs_destino: List[str],
    contexto: str = "padrao",
    sobrescrever: bool = False,
) -> Dict[str, Any]:
    """
    Copia todas as taxas de um EC de origem para um ou mais ECs de destino.

    Args:
        engine: Engine do SQLAlchemy
        ec_origem: EC de origem das taxas
        ecs_destino: Lista de ECs de destino
        contexto: Contexto das taxas (padrão: "padrao")
        sobrescrever: Se True, remove taxas existentes nos ECs de destino antes de copiar

    Returns:
        Dicionário com estatísticas da operação:
        - copiadas: número de taxas copiadas
        - removidas: número de taxas removidas (se sobrescrever=True)
        - erros: lista de erros ocorridos
    """
    resultado = {"copiadas": 0, "removidas": 0, "erros": []}

    try:
        # Busca todas as taxas do EC de origem
        taxas_origem = taxas_por_ec(engine, ec_origem, contexto)

        if not taxas_origem:
            resultado["erros"].append(f"Nenhuma taxa encontrada para o EC {ec_origem}")
            return resultado

        for ec_dest in ecs_destino:
            if ec_dest == ec_origem:
                resultado["erros"].append(
                    f"EC de destino {ec_dest} é igual ao EC de origem"
                )
                continue

            try:
                # Se sobrescrever, remove taxas existentes no destino
                if sobrescrever:
                    sql_delete = f"""
                    DELETE FROM taxas 
                    WHERE ec = :ec AND {_normalize_text_compare(engine, 'contexto', 'contexto')}
                    """
                    exec_sql(engine, sql_delete, {"ec": ec_dest, "contexto": contexto})
                    # Conta quantas foram removidas (assumindo sucesso)
                    taxas_dest_antes = taxas_por_ec(engine, ec_dest, contexto)
                    resultado["removidas"] += (
                        len(taxas_dest_antes) if taxas_dest_antes else 0
                    )

                # Copia cada taxa
                for taxa_orig in taxas_origem:
                    nova_taxa = {
                        "ec": ec_dest,
                        "bandeira": taxa_orig.get("bandeira"),
                        "forma_pagamento": taxa_orig["forma_pagamento"],
                        "parcelado": taxa_orig["parcelado"],
                        "parcelas_ini": taxa_orig["parcelas_ini"],
                        "parcelas_fim": taxa_orig["parcelas_fim"],
                        "data_ini": taxa_orig["data_ini"],
                        "data_fim": taxa_orig["data_fim"],
                        "taxa": taxa_orig["taxa"],
                        "contexto": contexto,
                    }

                    if taxa_adicionar(engine, nova_taxa, contexto):
                        resultado["copiadas"] += 1
                    else:
                        resultado["erros"].append(
                            f"Falha ao copiar taxa {taxa_orig['id']} para EC {ec_dest}"
                        )

            except Exception as e:
                resultado["erros"].append(f"Erro ao copiar para EC {ec_dest}: {str(e)}")

    except Exception as e:
        resultado["erros"].append(f"Erro geral: {str(e)}")

    return resultado


# ==============================
# Contextos
# ==============================


def contextos_listar(
    engine: Engine, incluir_inativos: bool = False
) -> List[Dict[str, Any]]:
    """Lista todos os contextos cadastrados."""
    sql = "SELECT id, nome, descricao, ativo, criado_por, criado_em, atualizado_em FROM contextos"
    if not incluir_inativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome"
    return fetch_all(engine, sql)


def contexto_buscar_por_id(
    engine: Engine, contexto_id: int
) -> Optional[Dict[str, Any]]:
    """Busca um contexto específico pelo ID."""
    sql = "SELECT id, nome, descricao, ativo, criado_por, criado_em, atualizado_em FROM contextos WHERE id = :id"
    return fetch_one(engine, sql, {"id": contexto_id})


def contexto_buscar_por_nome(engine: Engine, nome: str) -> Optional[Dict[str, Any]]:
    """Busca um contexto específico pelo nome."""
    sql = "SELECT id, nome, descricao, ativo, criado_por, criado_em, atualizado_em FROM contextos WHERE nome = :nome"
    return fetch_one(engine, sql, {"nome": nome})


def contexto_inserir(
    engine: Engine,
    *,
    nome: str,
    descricao: Optional[str] = None,
    ativo: int = 1,
    criado_por: Optional[str] = None,
) -> None:
    """Insere um novo contexto."""
    sql = """
    INSERT INTO contextos (nome, descricao, ativo, criado_por)
    VALUES (:nome, :descricao, :ativo, :criado_por)
    """
    params = {
        "nome": (nome or "").strip(),
        "descricao": (descricao or "").strip() if descricao is not None else None,
        "ativo": int(ativo),
        "criado_por": criado_por,
    }
    print(f"[DEBUG contexto_inserir] Inserindo com parâmetros: {params}")
    try:
        with engine.begin() as conn:
            result = conn.execute(text(_adapt_sql(engine, sql)), params)
            print(f"[DEBUG contexto_inserir] Linhas inseridas: {result.rowcount}")
        print(f"[DEBUG contexto_inserir] COMMIT realizado com sucesso")
    except Exception as e:
        print(f"[DEBUG contexto_inserir] ERRO ao inserir: {e}")
        import traceback

        traceback.print_exc()
        raise


def contexto_atualizar(
    engine: Engine,
    contexto_id: int,
    *,
    nome: str,
    descricao: Optional[str] = None,
    ativo: int = 1,
) -> None:
    """Atualiza um contexto existente."""
    # Força conversão para int nativo do Python
    contexto_id = int(contexto_id)

    sql = """
    UPDATE contextos
    SET nome = :nome,
        descricao = :descricao,
        ativo = :ativo,
        atualizado_em = CURRENT_TIMESTAMP
    WHERE id = :id
    """
    params = {
        "id": contexto_id,
        "nome": (nome or "").strip(),
        "descricao": (descricao or "").strip() if descricao is not None else None,
        "ativo": int(ativo),
    }
    print(f"[DEBUG contexto_atualizar] Atualizando ID {contexto_id} com: {params}")
    adapted_sql = _adapt_sql(engine, sql)
    print(f"[DEBUG contexto_atualizar] SQL adaptado: {adapted_sql}")
    print(f"[DEBUG contexto_atualizar] Parâmetros: {params}")
    try:
        with engine.begin() as conn:
            result = conn.execute(text(adapted_sql), params)
            print(f"[DEBUG contexto_atualizar] Linhas atualizadas: {result.rowcount}")
        print(f"[DEBUG contexto_atualizar] COMMIT realizado com sucesso")
    except Exception as e:
        print(f"[DEBUG contexto_atualizar] ERRO ao atualizar: {e}")
        import traceback

        traceback.print_exc()
        raise


def contexto_deletar(engine: Engine, contexto_id: int) -> bool:
    """Deleta um contexto se não houver de-para associado."""

    from conf.sql_adapter import get_db_type

    # Força contexto_id para int puro
    contexto_id_int = int(contexto_id)
    print(
        f"[DEBUG contexto_deletar] Iniciando deleção de ID: {contexto_id_int} (tipo: {type(contexto_id_int)})"
    )
    print(f"[DEBUG contexto_deletar] Engine recebida: {engine}")
    print(f"[DEBUG contexto_deletar] Engine URL: {engine.url}")
    print(f"[DEBUG contexto_deletar] É SQLite? {get_db_type(engine) == 'sqlite'}")

    try:
        # Primeiro lista TODOS os contextos para debug
        list_all_sql = "SELECT id, nome FROM contextos ORDER BY id"
        with engine.connect() as test_conn:
            all_contexts = test_conn.execute(text(_adapt_sql(engine, list_all_sql)))
            all_rows = all_contexts.fetchall()
            print(f"[DEBUG contexto_deletar] TODOS os contextos no banco:")
            for row in all_rows:
                print(
                    f"  - ID: {row[0]} (tipo: {type(row[0])}), Nome: {row[1]} (tipo: {type(row[1])})"
                )

        # Usar UMA ÚNICA transação para tudo
        with engine.begin() as conn:
            # 1. Verifica se o registro existe e obtém o nome
            check_sql = "SELECT id, nome FROM contextos WHERE id = :id"
            print(f"[DEBUG contexto_deletar] Executando query: {check_sql}")
            print(
                f"[DEBUG contexto_deletar] Parâmetro: id={contexto_id_int} (tipo: {type(contexto_id_int)})"
            )
            check_result = conn.execute(
                text(_adapt_sql(engine, check_sql)), {"id": contexto_id_int}
            )
            registro = check_result.fetchone()
            print(
                f"[DEBUG contexto_deletar] Resultado da query: {registro} (tipo: {type(registro)})"
            )
            print(
                f"[DEBUG contexto_deletar] Registro encontrado: {dict(registro._mapping) if registro else None}"
            )

            if not registro:
                print(
                    f"[DEBUG contexto_deletar] ERRO: Registro ID {contexto_id_int} não existe!"
                )
                return False

            # 2. Verifica dependências usando o nome obtido (evita subquery e problema de collation)
            contexto_nome = registro[1]
            check_deps_sql = "SELECT COUNT(*) as total FROM depara_colunas WHERE UPPER(contexto) = UPPER(:contexto_nome)"
            deps_result = conn.execute(
                text(_adapt_sql(engine, check_deps_sql)),
                {"contexto_nome": contexto_nome},
            )
            deps_row = deps_result.fetchone()
            total_deps = deps_row[0] if deps_row else 0
            print(f"[DEBUG contexto_deletar] Dependências encontradas: {total_deps}")

            if total_deps > 0:
                print(f"[DEBUG contexto_deletar] Bloqueado - contexto em uso")
                return False

            # 3. Deleta
            sql = "DELETE FROM contextos WHERE id = :id"
            result = conn.execute(
                text(_adapt_sql(engine, sql)), {"id": contexto_id_int}
            )
            affected_rows = result.rowcount
            print(
                f"[DEBUG contexto_deletar] Linhas afetadas pelo DELETE: {affected_rows}"
            )

            # 4. Verifica se realmente foi deletado
            verify_result = conn.execute(
                text(_adapt_sql(engine, check_sql)), {"id": contexto_id_int}
            )
            ainda_existe = verify_result.fetchone()
            print(
                f"[DEBUG contexto_deletar] Registro após DELETE: {dict(ainda_existe._mapping) if ainda_existe else 'DELETADO!'}"
            )

        # Commit automático ao sair do 'with'
        print(f"[DEBUG contexto_deletar] COMMIT realizado com sucesso")
        return affected_rows > 0
    except Exception as e:
        print(f"[DEBUG contexto_deletar] EXCEÇÃO ao deletar contexto: {e}")
        import traceback

        traceback.print_exc()
        return False


# ==============================
# Análises
# ==============================


def analise_criar(
    engine: Engine,
    nome_analise: str,
    descricao: Optional[str] = None,
    usuario_criador: Optional[str] = None,
) -> int:
    """Cria uma nova análise e retorna o ID."""
    sql = """
    INSERT INTO analises (nome_analise, descricao, usuario_criador, status)
    VALUES (:nome_analise, :descricao, :usuario_criador, 'em_andamento')
    """
    # MySQL: AUTO_INCREMENT é o padrão

    with get_conn(engine) as conn:
        result = conn.execute(
            text(sql),
            {
                "nome_analise": nome_analise.strip(),
                "descricao": descricao.strip() if descricao else None,
                "usuario_criador": usuario_criador,
            },
        )
        # MySQL: retornar lastrowid
        return result.lastrowid


def analise_listar(
    engine: Engine, usuario: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Lista todas as análises, opcionalmente filtradas por usuário."""
    sql = "SELECT * FROM analises WHERE 1=1"
    params = {}
    if usuario:
        sql += " AND usuario_criador = :usuario"
        params["usuario"] = usuario
    sql += " ORDER BY data_criacao DESC"
    return fetch_all(engine, sql, params)


def analise_buscar_por_id(engine: Engine, analise_id: int) -> Optional[Dict[str, Any]]:
    """Busca uma análise por ID."""
    sql = "SELECT * FROM analises WHERE id = :id"
    return fetch_one(engine, sql, {"id": analise_id})


def analise_atualizar(
    engine: Engine,
    analise_id: int,
    nome_analise: Optional[str] = None,
    descricao: Optional[str] = None,
    status: Optional[str] = None,
    total_arquivos: Optional[int] = None,
    total_registros: Optional[int] = None,
    observacoes: Optional[str] = None,
) -> bool:
    """Atualiza uma análise existente."""
    updates = []
    params = {"id": analise_id}

    if nome_analise is not None:
        updates.append("nome_analise = :nome_analise")
        params["nome_analise"] = nome_analise.strip()
    if descricao is not None:
        updates.append("descricao = :descricao")
        params["descricao"] = descricao.strip()
    if status is not None:
        updates.append("status = :status")
        params["status"] = status
    if total_arquivos is not None:
        updates.append("total_arquivos = :total_arquivos")
        params["total_arquivos"] = total_arquivos
    if total_registros is not None:
        updates.append("total_registros = :total_registros")
        params["total_registros"] = total_registros
    if observacoes is not None:
        updates.append("observacoes = :observacoes")
        params["observacoes"] = observacoes.strip()

    if not updates:
        return False

    # Timestamp atual (compatível MySQL/SQLite)
    updates.append(f"data_atualizacao = {_current_timestamp_sql(engine)}")

    sql = f"UPDATE analises SET {', '.join(updates)} WHERE id = :id"
    try:
        exec_sql(engine, sql, params)
        return True
    except Exception as e:
        print(f"Erro ao atualizar análise: {e}")
        return False


def analise_deletar(engine: Engine, analise_id: int) -> bool:
    """Deleta uma análise e todos os dados relacionados (CASCADE)."""
    sql = "DELETE FROM analises WHERE id = :id"
    try:
        exec_sql(engine, sql, {"id": analise_id})
        return True
    except Exception as e:
        print(f"Erro ao deletar análise: {e}")
        return False


def analise_adicionar_arquivo(
    engine: Engine,
    analise_id: int,
    nome_arquivo: str,
    caminho_arquivo: Optional[str] = None,
    tipo_arquivo: Optional[str] = None,
    contexto: Optional[str] = None,
    total_registros: int = 0,
) -> int:
    """Adiciona um arquivo à análise."""
    sql = """
    INSERT INTO analises_arquivos 
    (analise_id, nome_arquivo, caminho_arquivo, tipo_arquivo, contexto, total_registros)
    VALUES (:analise_id, :nome_arquivo, :caminho_arquivo, :tipo_arquivo, :contexto, :total_registros)
    """
    with get_conn(engine) as conn:
        result = conn.execute(
            text(sql),
            {
                "analise_id": analise_id,
                "nome_arquivo": nome_arquivo,
                "caminho_arquivo": caminho_arquivo,
                "tipo_arquivo": tipo_arquivo,
                "contexto": contexto,
                "total_registros": total_registros,
            },
        )
        return result.lastrowid


def analise_salvar_bandeiras(
    engine: Engine, analise_id: int, bandeiras: List[Dict[str, Any]]
) -> None:
    """Salva os resultados de bandeiras da análise."""
    sql_delete = "DELETE FROM analises_bandeiras WHERE analise_id = :analise_id"
    exec_sql(engine, sql_delete, {"analise_id": analise_id})

    if not bandeiras:
        return

    sql_insert = """
    INSERT INTO analises_bandeiras (analise_id, bandeira, quantidade, valor_total)
    VALUES (:analise_id, :bandeira, :quantidade, :valor_total)
    """
    for b in bandeiras:
        exec_sql(
            engine,
            sql_insert,
            {
                "analise_id": analise_id,
                "bandeira": b["bandeira"],
                "quantidade": b.get("quantidade", 0),
                "valor_total": b.get("valor_total", 0.0),
            },
        )


def analise_salvar_formas_pagamento(
    engine: Engine, analise_id: int, formas: List[Dict[str, Any]]
) -> None:
    """Salva os resultados de formas de pagamento da análise."""
    sql_delete = "DELETE FROM analises_formas_pagamento WHERE analise_id = :analise_id"
    exec_sql(engine, sql_delete, {"analise_id": analise_id})

    if not formas:
        return

    sql_insert = """
    INSERT INTO analises_formas_pagamento (analise_id, forma_pagamento, quantidade, valor_total)
    VALUES (:analise_id, :forma_pagamento, :quantidade, :valor_total)
    """
    for f in formas:
        exec_sql(
            engine,
            sql_insert,
            {
                "analise_id": analise_id,
                "forma_pagamento": f["forma_pagamento"],
                "quantidade": f.get("quantidade", 0),
                "valor_total": f.get("valor_total", 0.0),
            },
        )


def analise_salvar_tipos_recebiveis(
    engine: Engine, analise_id: int, tipos: List[Dict[str, Any]]
) -> None:
    """Salva os resultados de tipos de recebíveis da análise."""
    sql_delete = "DELETE FROM analises_tipos_recebiveis WHERE analise_id = :analise_id"
    exec_sql(engine, sql_delete, {"analise_id": analise_id})

    if not tipos:
        return

    sql_insert = """
    INSERT INTO analises_tipos_recebiveis (analise_id, tipo_recebivel, quantidade, valor_total)
    VALUES (:analise_id, :tipo_recebivel, :quantidade, :valor_total)
    """
    for t in tipos:
        exec_sql(
            engine,
            sql_insert,
            {
                "analise_id": analise_id,
                "tipo_recebivel": t["tipo_recebivel"],
                "quantidade": t.get("quantidade", 0),
                "valor_total": t.get("valor_total", 0.0),
            },
        )


def analise_salvar_periodos(
    engine: Engine, analise_id: int, periodos: List[Dict[str, Any]]
) -> None:
    """Salva os resultados agregados por período da análise."""
    sql_delete = "DELETE FROM analises_periodos WHERE analise_id = :analise_id"
    exec_sql(engine, sql_delete, {"analise_id": analise_id})

    if not periodos:
        return

    sql_insert = """
    INSERT INTO analises_periodos (analise_id, tipo_periodo, periodo, quantidade, valor_total)
    VALUES (:analise_id, :tipo_periodo, :periodo, :quantidade, :valor_total)
    """
    for p in periodos:
        exec_sql(
            engine,
            sql_insert,
            {
                "analise_id": analise_id,
                "tipo_periodo": p["tipo_periodo"],
                "periodo": p["periodo"],
                "quantidade": p.get("quantidade", 0),
                "valor_total": p.get("valor_total", 0.0),
            },
        )


def analise_obter_resultados(engine: Engine, analise_id: int) -> Dict[str, Any]:
    """Obtém todos os resultados de uma análise."""
    return {
        "bandeiras": fetch_all(
            engine,
            "SELECT * FROM analises_bandeiras WHERE analise_id = :id ORDER BY valor_total DESC",
            {"id": analise_id},
        ),
        "formas_pagamento": fetch_all(
            engine,
            "SELECT * FROM analises_formas_pagamento WHERE analise_id = :id ORDER BY valor_total DESC",
            {"id": analise_id},
        ),
        "tipos_recebiveis": fetch_all(
            engine,
            "SELECT * FROM analises_tipos_recebiveis WHERE analise_id = :id ORDER BY valor_total DESC",
            {"id": analise_id},
        ),
        "periodos": fetch_all(
            engine,
            "SELECT * FROM analises_periodos WHERE analise_id = :id ORDER BY periodo",
            {"id": analise_id},
        ),
        "arquivos": fetch_all(
            engine,
            "SELECT * FROM analises_arquivos WHERE analise_id = :id ORDER BY data_upload",
            {"id": analise_id},
        ),
    }


def contexto_pode_deletar(engine: Engine, contexto_id: int) -> bool:
    """Verifica se um contexto pode ser deletado (não tem dependências)."""
    # Primeiro busca o nome do contexto para evitar problema de collation
    sql_contexto = "SELECT nome FROM contextos WHERE id = :id"
    contexto_result = fetch_one(engine, sql_contexto, {"id": contexto_id})

    if not contexto_result:
        return True  # Se o contexto não existe, pode "deletar"

    # Agora verifica dependências usando o nome obtido
    sql_deps = "SELECT COUNT(*) as total FROM depara_colunas WHERE UPPER(contexto) = UPPER(:contexto_nome)"
    result = fetch_one(engine, sql_deps, {"contexto_nome": contexto_result["nome"]})
    return result["total"] == 0 if result else True


# ==============================
# Agregações Otimizadas para Analista
# ==============================


def agregar_bandeiras_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega dados de bandeiras diretamente no banco de dados (muito mais rápido)"""
    print(
        f"[DEBUG agregar_bandeiras_db] Iniciando agregação para processamento: {processamentoid}"
    )
    print("[DEBUG agregar_bandeiras_db] Tipo do banco: MySQL")

    sql = """
        SELECT 
            Bandeira as bandeira,
            COUNT(*) as quantidade,
            SUM(Valor_da_venda) as valor_total,
            AVG(Valor_da_venda) as valor_medio,
            MIN(Valor_da_venda) as valor_min,
            MAX(Valor_da_venda) as valor_max,
            AVG(Taxas_Perc) as taxa_perc_media,
            MIN(Taxas_Perc) as taxa_perc_min,
            MAX(Taxas_Perc) as taxa_perc_max,
            SUM(Valor_descontado) as taxa_valor_total,
            AVG(Valor_descontado) as taxa_valor_media,
            MIN(Valor_descontado) as taxa_valor_min,
            MAX(Valor_descontado) as taxa_valor_max
        FROM vendas_processadas
        WHERE processamentoid = :pid
        GROUP BY Bandeira
        ORDER BY valor_total DESC
    """

    print(f"[DEBUG agregar_bandeiras_db] Executando SQL...")
    try:
        resultado = fetch_all(engine, sql, {"pid": processamentoid})
        print(
            f"[DEBUG agregar_bandeiras_db] Resultado obtido: {len(resultado)} registros"
        )
        return resultado
    except Exception as e:
        print(f"[ERROR agregar_bandeiras_db] Erro ao executar SQL: {e}")
        print(f"[ERROR agregar_bandeiras_db] SQL: {sql}")
        print(f"[ERROR agregar_bandeiras_db] Params: {{'pid': {processamentoid}}}")
        raise


def agregar_formas_pagamento_db(
    engine: Engine, processamentoid: str
) -> List[Dict[str, Any]]:
    """Agrega dados de formas de pagamento diretamente no banco de dados"""
    print(
        f"[DEBUG agregar_formas_pagamento_db] Iniciando agregação para processamento: {processamentoid}"
    )

    sql = """
        SELECT 
            Forma_de_pagamento as forma_pagamento,
            COUNT(*) as quantidade,
            SUM(Valor_da_venda) as valor_total,
            AVG(Valor_da_venda) as valor_medio,
            MIN(Valor_da_venda) as valor_min,
            MAX(Valor_da_venda) as valor_max,
            AVG(Taxas_Perc) as taxa_perc_media,
            MIN(Taxas_Perc) as taxa_perc_min,
            MAX(Taxas_Perc) as taxa_perc_max,
            SUM(Valor_descontado) as taxa_valor_total,
            AVG(Valor_descontado) as taxa_valor_media,
            MIN(Valor_descontado) as taxa_valor_min,
            MAX(Valor_descontado) as taxa_valor_max
        FROM vendas_processadas
        WHERE processamentoid = :pid
        GROUP BY Forma_de_pagamento
        ORDER BY valor_total DESC
    """

    print(f"[DEBUG agregar_formas_pagamento_db] Executando SQL...")
    try:
        resultado = fetch_all(engine, sql, {"pid": processamentoid})
        print(
            f"[DEBUG agregar_formas_pagamento_db] Resultado obtido: {len(resultado)} registros"
        )
        return resultado
    except Exception as e:
        print(f"[ERROR agregar_formas_pagamento_db] Erro ao executar SQL: {e}")
        print(f"[ERROR agregar_formas_pagamento_db] SQL: {sql}")
        raise


def agregar_formas_pagamento_por_ano_db(
    engine: Engine, processamentoid: str
) -> List[Dict[str, Any]]:
    """Agrega dados de formas de pagamento por ano"""
    year_expr = _year_sql(engine, "Data_da_venda")

    sql = f"""
        SELECT 
            {year_expr} as ano,
            Forma_de_pagamento as forma_pagamento,
            COUNT(*) as quantidade,
            SUM(Valor_da_venda) as valor_total,
            AVG(Valor_da_venda) as valor_medio,
            MIN(Taxas_Perc) as taxa_perc_minima,
            MAX(Taxas_Perc) as taxa_perc_maxima
        FROM vendas_processadas
        WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
        GROUP BY {year_expr}, Forma_de_pagamento
        ORDER BY {year_expr}, valor_total DESC
    """

    return fetch_all(engine, sql, {"pid": processamentoid})


def agregar_periodos_bandeira_forma_db(
    engine: Engine, processamentoid: str, tipo_periodo: str
) -> List[Dict[str, Any]]:
    """
    Agrega dados por período, bandeira e forma de pagamento.
    tipo_periodo: 'semestral', 'trimestral' ou 'anual'
    """
    print(
        f"[DEBUG agregar_periodos_bandeira_forma_db] Iniciando agregação {tipo_periodo} para: {processamentoid}"
    )

    # Construir expressão de período baseada no tipo
    year_expr = _year_sql(engine, "Data_da_venda")

    if tipo_periodo == "semestral":
        semester_expr = _semester_sql(engine, "Data_da_venda")
        periodo_expr = _concat_sql(engine, year_expr, "'-S'", semester_expr)
        periodo_label = "semestre"
    elif tipo_periodo == "trimestral":
        quarter_expr = _quarter_sql(engine, "Data_da_venda")
        periodo_expr = _concat_sql(engine, year_expr, "'-T'", quarter_expr)
        periodo_label = "trimestre"
    elif tipo_periodo == "anual":
        periodo_expr = year_expr
        periodo_label = "ano"
    else:
        raise ValueError(f"tipo_periodo inválido: {tipo_periodo}")

    sql = f"""
        SELECT 
            {periodo_expr} as periodo,
            Bandeira as bandeira,
            Forma_de_pagamento as forma_pagamento,
            SUM(Valor_da_venda) as valor_total,
            COUNT(*) as quantidade,
            MIN(Taxas_Perc) as taxa_perc_minima
        FROM vendas_processadas
        WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
        GROUP BY {periodo_expr}, Bandeira, Forma_de_pagamento
        ORDER BY {periodo_expr}, Bandeira, Forma_de_pagamento
    """

    try:
        resultados = fetch_all(engine, sql, {"pid": processamentoid})
        print(
            f"[DEBUG agregar_periodos_bandeira_forma_db] {tipo_periodo}: {len(resultados)} registros"
        )
        return resultados
    except Exception as e:
        print(f"[ERROR agregar_periodos_bandeira_forma_db] Erro: {e}")
        raise


def agregar_semestral_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega dados por semestre com bandeira e forma de pagamento"""
    year_expr = _year_sql(engine, "Data_da_venda")
    semester_expr = _semester_sql(engine, "Data_da_venda")
    periodo_expr = _concat_sql(engine, year_expr, "'-S'", semester_expr)

    sql = f"""
        SELECT 
            {periodo_expr} as semestre,
            Bandeira as bandeira,
            Forma_de_pagamento as forma_pagamento,
            SUM(Valor_da_venda) as valor_total,
            COUNT(*) as quantidade,
            MIN(Taxas_Perc) as taxa_perc_minima,
            MAX(Taxas_Perc) as taxa_perc_maxima
        FROM vendas_processadas
        WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
        GROUP BY {periodo_expr}, Bandeira, Forma_de_pagamento
        ORDER BY {periodo_expr}, Bandeira, Forma_de_pagamento
    """

    return fetch_all(engine, sql, {"pid": processamentoid})


def agregar_trimestral_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega dados por trimestre com bandeira e forma de pagamento"""
    year_expr = _year_sql(engine, "Data_da_venda")
    quarter_expr = _quarter_sql(engine, "Data_da_venda")
    periodo_expr = _concat_sql(engine, year_expr, "'-T'", quarter_expr)

    sql = f"""
        SELECT 
            {periodo_expr} as trimestre,
            Bandeira as bandeira,
            Forma_de_pagamento as forma_pagamento,
            SUM(Valor_da_venda) as valor_total,
            COUNT(*) as quantidade,
            MIN(Taxas_Perc) as taxa_perc_minima,
            MAX(Taxas_Perc) as taxa_perc_maxima
        FROM vendas_processadas
        WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
        GROUP BY {periodo_expr}, Bandeira, Forma_de_pagamento
        ORDER BY {periodo_expr}, Bandeira, Forma_de_pagamento
    """

    return fetch_all(engine, sql, {"pid": processamentoid})


def agregar_anual_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega dados por ano com bandeira e forma de pagamento"""
    year_expr = _year_sql(engine, "Data_da_venda")

    sql = f"""
        SELECT 
            {year_expr} as ano,
            Bandeira as bandeira,
            Forma_de_pagamento as forma_pagamento,
            SUM(Valor_da_venda) as valor_total,
            COUNT(*) as quantidade,
            MIN(Taxas_Perc) as taxa_perc_minima,
            MAX(Taxas_Perc) as taxa_perc_maxima
        FROM vendas_processadas
        WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
        GROUP BY {year_expr}, Bandeira, Forma_de_pagamento
        ORDER BY {year_expr}, Bandeira, Forma_de_pagamento
    """

    return fetch_all(engine, sql, {"pid": processamentoid})


def agregar_periodos_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega dados por períodos (mês, trimestre, semestre, ano) diretamente no banco"""
    print(
        f"[DEBUG agregar_periodos_db] Iniciando agregação para processamento: {processamentoid}"
    )
    print("[DEBUG agregar_periodos_db] Tipo do banco: MySQL")

    # Construir expressões SQL para MySQL
    year_expr = _year_sql(engine, "Data_da_venda")
    quarter_expr = _quarter_sql(engine, "Data_da_venda")
    semester_expr = _semester_sql(engine, "Data_da_venda")
    date_fmt_mes = _date_format_sql(engine, "Data_da_venda", "%Y-%m")

    # Expressões de período (para SELECT e GROUP BY devem ser idênticas)
    periodo_mes = date_fmt_mes
    periodo_trimestre = _concat_sql(engine, year_expr, "'-Q'", quarter_expr)
    periodo_semestre = _concat_sql(engine, year_expr, "'-S'", semester_expr)
    periodo_ano = year_expr

    # Template base para agregação
    sql_template = """
        SELECT 
            '{tipo}' as tipo_periodo,
            {periodo_expr} as periodo,
            COUNT(*) as quantidade,
            SUM(Valor_da_venda) as valor_total,
            AVG(Valor_da_venda) as valor_medio,
            MIN(Valor_da_venda) as valor_min,
            MAX(Valor_da_venda) as valor_max
        FROM vendas_processadas
        WHERE processamentoid = :pid AND Data_da_venda IS NOT NULL
        GROUP BY {periodo_expr}
    """

    # Gerar queries específicas para cada período
    sql_mes = sql_template.format(tipo="mes", periodo_expr=periodo_mes)
    sql_trimestre = sql_template.format(
        tipo="trimestre", periodo_expr=periodo_trimestre
    )
    sql_semestre = sql_template.format(tipo="semestre", periodo_expr=periodo_semestre)
    sql_ano = sql_template.format(tipo="ano", periodo_expr=periodo_ano)

    # Executar todas as queries e combinar resultados
    params = {"pid": processamentoid}
    resultados = []

    print(f"[DEBUG agregar_periodos_db] Executando agregação por MÊS...")
    try:
        res_mes = fetch_all(engine, sql_mes, params)
        print(f"[DEBUG agregar_periodos_db] Mês: {len(res_mes)} registros")
        resultados.extend(res_mes)
    except Exception as e:
        print(f"[ERROR agregar_periodos_db] Erro ao agregar por mês: {e}")

    print(f"[DEBUG agregar_periodos_db] Executando agregação por TRIMESTRE...")
    try:
        res_trim = fetch_all(engine, sql_trimestre, params)
        print(f"[DEBUG agregar_periodos_db] Trimestre: {len(res_trim)} registros")
        resultados.extend(res_trim)
    except Exception as e:
        print(f"[ERROR agregar_periodos_db] Erro ao agregar por trimestre: {e}")

    print(f"[DEBUG agregar_periodos_db] Executando agregação por SEMESTRE...")
    try:
        res_sem = fetch_all(engine, sql_semestre, params)
        print(f"[DEBUG agregar_periodos_db] Semestre: {len(res_sem)} registros")
        resultados.extend(res_sem)
    except Exception as e:
        print(f"[ERROR agregar_periodos_db] Erro ao agregar por semestre: {e}")

    print(f"[DEBUG agregar_periodos_db] Executando agregação por ANO...")
    try:
        res_ano = fetch_all(engine, sql_ano, params)
        print(f"[DEBUG agregar_periodos_db] Ano: {len(res_ano)} registros")
        resultados.extend(res_ano)
    except Exception as e:
        print(f"[ERROR agregar_periodos_db] Erro ao agregar por ano: {e}")

    print(f"[DEBUG agregar_periodos_db] Total de períodos agregados: {len(resultados)}")
    return resultados


def obter_total_registros_processamento(engine: Engine, processamentoid: str) -> int:
    """Obtém o total de registros de um processamento de forma otimizada"""
    print(
        f"[DEBUG obter_total_registros_processamento] Contando registros para: {processamentoid}"
    )

    sql = (
        "SELECT COUNT(*) as total FROM vendas_processadas WHERE processamentoid = :pid"
    )

    try:
        result = fetch_one(engine, sql, {"pid": processamentoid})
        total = result["total"] if result else 0
        print(
            f"[DEBUG obter_total_registros_processamento] Total encontrado: {total:,}"
        )
        return total
    except Exception as e:
        print(f"[ERROR obter_total_registros_processamento] Erro ao contar: {e}")
        print(f"[ERROR obter_total_registros_processamento] SQL: {sql}")
        raise


def agregar_recebiveis_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega tipos de recebíveis/produtos diretamente no banco"""
    print(
        f"[DEBUG agregar_recebiveis_db] Iniciando agregação para processamento: {processamentoid}"
    )

    # Tentar diferentes colunas que podem conter tipo de produto/recebível
    colunas_possiveis = [
        "Produto",
        "Produto_cielo",
        "Tipo_produto",
        "Tipo_recebivel",
        "Tipo",
    ]

    for coluna in colunas_possiveis:
        try:
            # Testar se a coluna existe
            test_sql = f"""
                SELECT {coluna}
                FROM vendas_processadas
                WHERE processamentoid = :pid
                LIMIT 1
            """
            fetch_one(engine, test_sql, {"pid": processamentoid})

            # Se chegou aqui, a coluna existe - fazer agregação
            sql = f"""
                SELECT 
                    {coluna} as tipo_recebivel,
                    COUNT(*) as quantidade,
                    SUM(Valor_da_venda) as valor_total,
                    AVG(Valor_da_venda) as valor_medio,
                    MIN(Valor_da_venda) as valor_min,
                    MAX(Valor_da_venda) as valor_max
                FROM vendas_processadas
                WHERE processamentoid = :pid AND {coluna} IS NOT NULL
                GROUP BY {coluna}
                ORDER BY valor_total DESC
            """

            print(f"[DEBUG agregar_recebiveis_db] Usando coluna: {coluna}")
            resultado = fetch_all(engine, sql, {"pid": processamentoid})
            print(
                f"[DEBUG agregar_recebiveis_db] Resultado obtido: {len(resultado)} registros"
            )
            return resultado

        except Exception as e:
            # Coluna não existe, tentar próxima
            print(f"[DEBUG agregar_recebiveis_db] Coluna {coluna} não encontrada: {e}")
            continue

    # Se nenhuma coluna foi encontrada
    print(
        f"[DEBUG agregar_recebiveis_db] Nenhuma coluna de tipo de recebível encontrada"
    )
    return []


# ==============================
# Funções de Correção de Importação
# ==============================


def atualizar_forma_pagamento_processamento(
    engine: Engine,
    processamentoid: str,
    forma_pagamento_antiga: str,
    forma_pagamento_nova: str,
    usuario: str = "sistema",
) -> Tuple[bool, str, int]:
    """
    Atualiza todas as linhas de uma forma de pagamento específica em um processamento.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        forma_pagamento_antiga: Forma de pagamento atual que será substituída
        forma_pagamento_nova: Nova forma de pagamento
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_afetadas)
    """
    try:
        print(f"[DEBUG atualizar_forma_pagamento] Processamento: {processamentoid}")
        print(
            f"[DEBUG atualizar_forma_pagamento] De: '{forma_pagamento_antiga}' Para: '{forma_pagamento_nova}'"
        )

        # Contar quantas linhas serão afetadas
        sql_count = """
            SELECT COUNT(*) as total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Forma_de_pagamento = :forma_antiga
        """
        result = fetch_one(
            engine,
            sql_count,
            {"pid": processamentoid, "forma_antiga": forma_pagamento_antiga},
        )
        linhas_afetadas = result.get("total", 0) if result else 0

        if linhas_afetadas == 0:
            return (
                False,
                f"Nenhuma linha encontrada com forma de pagamento '{forma_pagamento_antiga}'",
                0,
            )

        # Realizar atualização
        sql_update = """
            UPDATE vendas_processadas
            SET Forma_de_pagamento = :forma_nova
            WHERE processamentoid = :pid AND Forma_de_pagamento = :forma_antiga
        """

        exec_sql(
            engine,
            sql_update,
            {
                "pid": processamentoid,
                "forma_antiga": forma_pagamento_antiga,
                "forma_nova": forma_pagamento_nova,
            },
        )

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'forma_pagamento', :val_antigo, :val_novo, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": forma_pagamento_antiga,
                    "val_novo": forma_pagamento_nova,
                    "linhas": linhas_afetadas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Atualização concluída: {linhas_afetadas} linhas alteradas de '{forma_pagamento_antiga}' para '{forma_pagamento_nova}'"
        print(f"[SUCCESS atualizar_forma_pagamento] {msg}")
        return True, msg, linhas_afetadas

    except Exception as e:
        msg = f"Erro ao atualizar forma de pagamento: {str(e)}"
        print(f"[ERROR atualizar_forma_pagamento] {msg}")
        return False, msg, 0


def atualizar_bandeira_processamento(
    engine: Engine,
    processamentoid: str,
    bandeira_antiga: str,
    bandeira_nova: str,
    usuario: str = "sistema",
) -> Tuple[bool, str, int]:
    """
    Atualiza todas as linhas de uma bandeira específica em um processamento.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        bandeira_antiga: Bandeira atual que será substituída
        bandeira_nova: Nova bandeira
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_afetadas)
    """
    try:
        print(f"[DEBUG atualizar_bandeira] Processamento: {processamentoid}")
        print(
            f"[DEBUG atualizar_bandeira] De: '{bandeira_antiga}' Para: '{bandeira_nova}'"
        )

        # Contar quantas linhas serão afetadas
        sql_count = """
            SELECT COUNT(*) as total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Bandeira = :bandeira_antiga
        """
        result = fetch_one(
            engine,
            sql_count,
            {"pid": processamentoid, "bandeira_antiga": bandeira_antiga},
        )
        linhas_afetadas = result.get("total", 0) if result else 0

        if linhas_afetadas == 0:
            return (
                False,
                f"Nenhuma linha encontrada com bandeira '{bandeira_antiga}'",
                0,
            )

        # Realizar atualização
        sql_update = """
            UPDATE vendas_processadas
            SET Bandeira = :bandeira_nova
            WHERE processamentoid = :pid AND Bandeira = :bandeira_antiga
        """

        exec_sql(
            engine,
            sql_update,
            {
                "pid": processamentoid,
                "bandeira_antiga": bandeira_antiga,
                "bandeira_nova": bandeira_nova,
            },
        )

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'bandeira', :val_antigo, :val_novo, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": bandeira_antiga,
                    "val_novo": bandeira_nova,
                    "linhas": linhas_afetadas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Atualização concluída: {linhas_afetadas} linhas alteradas de '{bandeira_antiga}' para '{bandeira_nova}'"
        print(f"[SUCCESS atualizar_bandeira] {msg}")
        return True, msg, linhas_afetadas

    except Exception as e:
        msg = f"Erro ao atualizar bandeira: {str(e)}"
        print(f"[ERROR atualizar_bandeira] {msg}")
        return False, msg, 0


def remover_linhas_forma_pagamento(
    engine: Engine, processamentoid: str, forma_pagamento: str, usuario: str = "sistema"
) -> Tuple[bool, str, int]:
    """
    Remove todas as linhas de uma forma de pagamento específica em um processamento.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        forma_pagamento: Forma de pagamento a remover
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_removidas)
    """
    try:
        print(
            f"[DEBUG remover_linhas_forma_pagamento] Processamento: {processamentoid}"
        )
        print(
            f"[DEBUG remover_linhas_forma_pagamento] Forma de pagamento: '{forma_pagamento}'"
        )

        # Contar quantas linhas serão removidas
        sql_count = """
            SELECT COUNT(*) as total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Forma_de_pagamento = :forma_pag
        """
        result = fetch_one(
            engine, sql_count, {"pid": processamentoid, "forma_pag": forma_pagamento}
        )
        linhas_removidas = result.get("total", 0) if result else 0

        if linhas_removidas == 0:
            return (
                False,
                f"Nenhuma linha encontrada com forma de pagamento '{forma_pagamento}'",
                0,
            )

        # ⚠️ CRÍTICO: Deletar cálculos primeiro (FK constraint)
        sql_delete_calculos = """
            DELETE FROM vendas_calculos
            WHERE id_venda IN (
                SELECT id FROM vendas_processadas
                WHERE processamentoid = :pid AND Forma_de_pagamento = :forma_pag
            )
        """

        # Mover para vendas_filtradas ao invés de deletar
        # ⚠️ CRÍTICO: Especificar colunas (excluindo 'id' AUTO_INCREMENT) para evitar conflito
        sql_insert = """
            INSERT IGNORE INTO vendas_filtradas (
                Data_da_venda, Data_da_autorização_da_venda, status_da_venda, Adquirente,
                Bandeira, Forma_de_pagamento, Quantidade_de_parcelas, Resumo_da_operação,
                Valor_da_venda, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                Previsão_de_pagamento, Valor_líquido_da_venda, Número_da_máquina,
                Código_de_autorização, NSU, Número_do_cartão, Receba_rápido, Status,
                Tratar_ou_Ignorar, Filtrado, arquivo_origem, processamentoid,
                cliente_id, ec_id, data_processamento, usuario_processamento
            )
            SELECT 
                Data_da_venda, Data_da_autorização_da_venda, status_da_venda, Adquirente,
                Bandeira, Forma_de_pagamento, Quantidade_de_parcelas, Resumo_da_operação,
                Valor_da_venda, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                Previsão_de_pagamento, Valor_líquido_da_venda, Número_da_máquina,
                Código_de_autorização, NSU, Número_do_cartão, Receba_rápido, Status,
                Tratar_ou_Ignorar, Filtrado, arquivo_origem, processamentoid,
                cliente_id, ec_id, data_processamento, usuario_processamento
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Forma_de_pagamento = :forma_pag
        """

        sql_delete = """
            DELETE FROM vendas_processadas
            WHERE processamentoid = :pid AND Forma_de_pagamento = :forma_pag
        """

        print(f"[DEBUG] Movendo {linhas_removidas} linhas para vendas_filtradas...")

        # 1. Deletar cálculos associados (evita erro FK)
        exec_sql(
            engine,
            sql_delete_calculos,
            {"pid": processamentoid, "forma_pag": forma_pagamento},
        )
        print(f"[DEBUG] ✓ Cálculos deletados")

        # 2. Insere em vendas_filtradas (sem o campo 'id')
        exec_sql(
            engine, sql_insert, {"pid": processamentoid, "forma_pag": forma_pagamento}
        )
        print(f"[DEBUG] ✓ Linhas inseridas em vendas_filtradas")

        # 3. Remove de vendas_processadas
        exec_sql(
            engine, sql_delete, {"pid": processamentoid, "forma_pag": forma_pagamento}
        )
        print(f"[DEBUG] ✓ Linhas removidas de vendas_processadas")

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'remocao_forma_pagamento', :val_antigo, NULL, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": forma_pagamento,
                    "linhas": linhas_removidas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Remoção concluída: {linhas_removidas} linhas com forma de pagamento '{forma_pagamento}' movidas para vendas_filtradas"
        print(f"[SUCCESS remover_linhas_forma_pagamento] {msg}")
        return True, msg, linhas_removidas

    except Exception as e:
        msg = f"Erro ao remover linhas por forma de pagamento: {str(e)}"
        print(f"[ERROR remover_linhas_forma_pagamento] {msg}")
        return False, msg, 0


def remover_linhas_bandeira(
    engine: Engine, processamentoid: str, bandeira: str, usuario: str = "sistema"
) -> Tuple[bool, str, int]:
    """
    Remove todas as linhas de uma bandeira específica em um processamento.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        bandeira: Bandeira a remover
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_removidas)
    """
    try:
        print(f"[DEBUG remover_linhas_bandeira] Processamento: {processamentoid}")
        print(f"[DEBUG remover_linhas_bandeira] Bandeira: '{bandeira}'")

        # Contar quantas linhas serão removidas
        sql_count = """
            SELECT COUNT(*) as total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Bandeira = :bandeira
        """
        result = fetch_one(
            engine, sql_count, {"pid": processamentoid, "bandeira": bandeira}
        )
        linhas_removidas = result.get("total", 0) if result else 0

        if linhas_removidas == 0:
            return False, f"Nenhuma linha encontrada com bandeira '{bandeira}'", 0

        # ⚠️ CRÍTICO: Deletar cálculos primeiro (FK constraint)
        sql_delete_calculos = """
            DELETE FROM vendas_calculos
            WHERE id_venda IN (
                SELECT id FROM vendas_processadas
                WHERE processamentoid = :pid AND Bandeira = :bandeira
            )
        """

        # Mover para vendas_filtradas ao invés de deletar
        # ⚠️ CRÍTICO: Especificar colunas (excluindo 'id' AUTO_INCREMENT) para evitar conflito
        sql_insert = """
            INSERT IGNORE INTO vendas_filtradas (
                Data_da_venda, Data_da_autorização_da_venda, status_da_venda, Adquirente,
                Bandeira, Forma_de_pagamento, Quantidade_de_parcelas, Resumo_da_operação,
                Valor_da_venda, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                Previsão_de_pagamento, Valor_líquido_da_venda, Número_da_máquina,
                Código_de_autorização, NSU, Número_do_cartão, Receba_rápido, Status,
                Tratar_ou_Ignorar, Filtrado, arquivo_origem, processamentoid,
                cliente_id, ec_id, data_processamento, usuario_processamento
            )
            SELECT 
                Data_da_venda, Data_da_autorização_da_venda, status_da_venda, Adquirente,
                Bandeira, Forma_de_pagamento, Quantidade_de_parcelas, Resumo_da_operação,
                Valor_da_venda, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                Previsão_de_pagamento, Valor_líquido_da_venda, Número_da_máquina,
                Código_de_autorização, NSU, Número_do_cartão, Receba_rápido, Status,
                Tratar_ou_Ignorar, Filtrado, arquivo_origem, processamentoid,
                cliente_id, ec_id, data_processamento, usuario_processamento
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Bandeira = :bandeira
        """

        sql_delete = """
            DELETE FROM vendas_processadas
            WHERE processamentoid = :pid AND Bandeira = :bandeira
        """

        print(f"[DEBUG] Movendo {linhas_removidas} linhas para vendas_filtradas...")

        # 1. Deletar cálculos associados (evita erro FK)
        exec_sql(
            engine, sql_delete_calculos, {"pid": processamentoid, "bandeira": bandeira}
        )
        print(f"[DEBUG] ✓ Cálculos deletados")

        # 2. Insere em vendas_filtradas (sem o campo 'id')
        exec_sql(engine, sql_insert, {"pid": processamentoid, "bandeira": bandeira})
        print(f"[DEBUG] ✓ Linhas inseridas em vendas_filtradas")

        # 3. Remove de vendas_processadas
        exec_sql(engine, sql_delete, {"pid": processamentoid, "bandeira": bandeira})
        print(f"[DEBUG] ✓ Linhas removidas de vendas_processadas")

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'remocao_bandeira', :val_antigo, NULL, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": bandeira,
                    "linhas": linhas_removidas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Remoção concluída: {linhas_removidas} linhas com bandeira '{bandeira}' movidas para vendas_filtradas"
        print(f"[SUCCESS remover_linhas_bandeira] {msg}")
        return True, msg, linhas_removidas

    except Exception as e:
        msg = f"Erro ao remover linhas por bandeira: {str(e)}"
        print(f"[ERROR remover_linhas_bandeira] {msg}")
        return False, msg, 0


def listar_valores_unicos_processamento(
    engine: Engine, processamentoid: str, coluna: str
) -> List[str]:
    """
    Lista valores únicos de uma coluna para um processamento específico.
    Útil para preencher dropdowns de seleção na UI de correção.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento
        coluna: Nome da coluna (ex: 'Bandeira', 'Forma_de_pagamento')

    Returns:
        Lista de valores únicos ordenados
    """
    try:
        sql = f"""
            SELECT DISTINCT {coluna} as valor
            FROM vendas_processadas
            WHERE processamentoid = :pid AND {coluna} IS NOT NULL
            ORDER BY {coluna}
        """

        resultados = fetch_all(engine, sql, {"pid": processamentoid})
        valores = [r["valor"] for r in resultados]

        print(
            f"[DEBUG listar_valores_unicos] Coluna '{coluna}': {len(valores)} valores únicos"
        )
        return valores

    except Exception as e:
        print(
            f"[ERROR listar_valores_unicos] Erro ao listar valores de '{coluna}': {e}"
        )
        return []


def listar_historico_correcoes(
    engine: Engine,
    processamentoid: Optional[str] = None,
    usuario: Optional[str] = None,
    limite: int = 100,
) -> List[Dict[str, Any]]:
    """
    Lista histórico de correções realizadas.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: Filtrar por processamento específico (opcional)
        usuario: Filtrar por usuário específico (opcional)
        limite: Número máximo de registros a retornar

    Returns:
        Lista de dicionários com histórico de correções
    """
    try:
        where_clauses = []
        params = {}

        if processamentoid:
            where_clauses.append("processamentoid = :pid")
            params["pid"] = processamentoid

        if usuario:
            where_clauses.append("usuario = :usuario")
            params["usuario"] = usuario

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        # MySQL e SQLite suportam LIMIT, mas vamos usar de forma compatível
        sql = f"""
            SELECT 
                id,
                processamentoid,
                tipo_correcao,
                valor_antigo,
                valor_novo,
                linhas_afetadas,
                usuario,
                data_correcao
            FROM log_correcoes_importacao
            {where_sql}
            ORDER BY data_correcao DESC
            LIMIT {limite}
        """

        print(f"[DEBUG listar_historico_correcoes] SQL: {sql}")
        print(f"[DEBUG listar_historico_correcoes] Params: {params}")

        resultados = fetch_all(engine, sql, params)
        print(
            f"[DEBUG listar_historico_correcoes] {len(resultados)} registros encontrados"
        )
        return resultados

    except Exception as e:
        print(f"[WARNING listar_historico_correcoes] Erro ao buscar histórico: {e}")
        import traceback

        traceback.print_exc()
        return []


def listar_resumo_processamento(
    engine: Engine, processamentoid: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Lista resumo de formas de pagamento e bandeiras de um processamento.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento

    Returns:
        Dicionário com listas de formas_pagamento e bandeiras com suas quantidades
    """
    try:
        # Listar formas de pagamento com contagem
        sql_formas = """
            SELECT 
                Forma_de_pagamento as valor,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Forma_de_pagamento IS NOT NULL
            GROUP BY Forma_de_pagamento
            ORDER BY quantidade DESC
        """

        formas_pagamento = fetch_all(engine, sql_formas, {"pid": processamentoid})

        # Listar bandeiras com contagem
        sql_bandeiras = """
            SELECT 
                Bandeira as valor,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND Bandeira IS NOT NULL
            GROUP BY Bandeira
            ORDER BY quantidade DESC
        """

        bandeiras = fetch_all(engine, sql_bandeiras, {"pid": processamentoid})

        # Listar status com contagem
        sql_status = """
            SELECT 
                status_da_venda as valor,
                COUNT(*) as quantidade,
                SUM(Valor_da_venda) as valor_total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND status_da_venda IS NOT NULL
            GROUP BY status_da_venda
            ORDER BY quantidade DESC
        """

        status = fetch_all(engine, sql_status, {"pid": processamentoid})

        print(
            f"[DEBUG listar_resumo_processamento] {len(formas_pagamento)} formas de pagamento, {len(bandeiras)} bandeiras, {len(status)} status"
        )

        return {
            "formas_pagamento": formas_pagamento,
            "bandeiras": bandeiras,
            "status": status,
        }

    except Exception as e:
        print(f"[ERROR listar_resumo_processamento] Erro: {e}")
        return {"formas_pagamento": [], "bandeiras": []}


# ==============================
# Funções de Correção para Recebíveis
# ==============================


def listar_resumo_recebiveis_processamento(
    engine: Engine, processamentoid: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Lista resumo de tipos de lançamento de um processamento de recebíveis.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento

    Returns:
        Dicionário com lista de lancamentos com suas quantidades
    """
    try:
        # Listar tipos de lançamento com contagem
        sql_lancamentos = """
            SELECT 
                lancamento as valor,
                COUNT(*) as quantidade,
                SUM(valor_recebivel) as valor_total
            FROM recebiveis_processados
            WHERE processamentoid = :pid AND lancamento IS NOT NULL
            GROUP BY lancamento
            ORDER BY quantidade DESC
        """

        lancamentos = fetch_all(engine, sql_lancamentos, {"pid": processamentoid})

        print(
            f"[DEBUG listar_resumo_recebiveis_processamento] {len(lancamentos)} tipos de lançamento"
        )

        return {"lancamentos": lancamentos}

    except Exception as e:
        print(f"[ERROR listar_resumo_recebiveis_processamento] Erro: {e}")
        return {"lancamentos": []}


def atualizar_lancamento_recebiveis_processamento(
    engine: Engine,
    processamentoid: str,
    lancamento_antigo: str,
    lancamento_novo: str,
    usuario: str = "sistema",
) -> Tuple[bool, str, int]:
    """
    Atualiza o tipo de lançamento de recebíveis em um processamento específico.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        lancamento_antigo: Tipo de lançamento atual
        lancamento_novo: Novo tipo de lançamento
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_afetadas)
    """
    try:
        print(
            f"[DEBUG atualizar_lancamento_recebiveis] Processamento: {processamentoid}"
        )
        print(
            f"[DEBUG atualizar_lancamento_recebiveis] De: '{lancamento_antigo}' -> Para: '{lancamento_novo}'"
        )

        # Contar linhas que serão afetadas
        sql_count = """
            SELECT COUNT(*) as total
            FROM recebiveis_processados
            WHERE processamentoid = :pid AND lancamento = :lanc_antigo
        """
        result = fetch_one(
            engine,
            sql_count,
            {"pid": processamentoid, "lanc_antigo": lancamento_antigo},
        )
        linhas_afetadas = result.get("total", 0) if result else 0

        if linhas_afetadas == 0:
            return (
                False,
                f"Nenhuma linha encontrada com lançamento '{lancamento_antigo}'",
                0,
            )

        # Executar UPDATE
        sql_update = """
            UPDATE recebiveis_processados
            SET lancamento = :lanc_novo
            WHERE processamentoid = :pid AND lancamento = :lanc_antigo
        """

        exec_sql(
            engine,
            sql_update,
            {
                "pid": processamentoid,
                "lanc_antigo": lancamento_antigo,
                "lanc_novo": lancamento_novo,
            },
        )

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'atualizacao_lancamento_recebiveis', :val_antigo, :val_novo, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": lancamento_antigo,
                    "val_novo": lancamento_novo,
                    "linhas": linhas_afetadas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Atualização concluída: {linhas_afetadas} linhas de '{lancamento_antigo}' para '{lancamento_novo}'"
        print(f"[SUCCESS atualizar_lancamento_recebiveis] {msg}")
        return True, msg, linhas_afetadas

    except Exception as e:
        msg = f"Erro ao atualizar lançamento de recebíveis: {str(e)}"
        print(f"[ERROR atualizar_lancamento_recebiveis] {msg}")
        return False, msg, 0


def remover_linhas_lancamento_recebiveis(
    engine: Engine, processamentoid: str, lancamento: str, usuario: str = "sistema"
) -> Tuple[bool, str, int]:
    """
    Remove todas as linhas de um tipo de lançamento específico em um processamento de recebíveis.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        lancamento: Tipo de lançamento a remover
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_removidas)
    """
    try:
        print(
            f"[DEBUG remover_linhas_lancamento_recebiveis] Processamento: {processamentoid}"
        )
        print(
            f"[DEBUG remover_linhas_lancamento_recebiveis] Lançamento: '{lancamento}'"
        )

        # Contar quantas linhas serão removidas
        sql_count = """
            SELECT COUNT(*) as total
            FROM recebiveis_processados
            WHERE processamentoid = :pid AND lancamento = :lancamento
        """
        result = fetch_one(
            engine, sql_count, {"pid": processamentoid, "lancamento": lancamento}
        )
        linhas_removidas = result.get("total", 0) if result else 0

        if linhas_removidas == 0:
            return (
                False,
                f"Nenhuma linha encontrada com lançamento '{lancamento}'",
                0,
            )

        # Mover para recebiveis_filtrados ao invés de deletar
        # ⚠️ CRÍTICO: Especificar colunas (excluindo 'id' AUTO_INCREMENT) para evitar conflito de chaves
        sql_insert = """
            INSERT IGNORE INTO recebiveis_filtrados (
                data_pagamento, data_recebivel, lancamento, recebivel_id, 
                adquirente, valor_recebivel, valor_liquido, descricao, 
                banco, agencia, conta, processamentoid, cliente_id, ec_id,
                data_processamento, usuario_processamento, arquivo_origem
            )
            SELECT 
                data_pagamento, data_recebivel, lancamento, recebivel_id, 
                adquirente, valor_recebivel, valor_liquido, descricao, 
                banco, agencia, conta, processamentoid, cliente_id, ec_id,
                data_processamento, usuario_processamento, arquivo_origem
            FROM recebiveis_processados
            WHERE processamentoid = :pid AND lancamento = :lancamento
        """

        sql_delete = """
            DELETE FROM recebiveis_processados
            WHERE processamentoid = :pid AND lancamento = :lancamento
        """

        print(f"[DEBUG] Movendo {linhas_removidas} linhas para recebiveis_filtrados...")

        # 1. Insere em recebiveis_filtrados (sem o campo 'id')
        exec_sql(engine, sql_insert, {"pid": processamentoid, "lancamento": lancamento})
        print(f"[DEBUG] ✓ Linhas inseridas em recebiveis_filtrados")

        # 2. Remove de recebiveis_processados
        exec_sql(engine, sql_delete, {"pid": processamentoid, "lancamento": lancamento})
        print(f"[DEBUG] ✓ Linhas removidas de recebiveis_processados")

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'remocao_lancamento_recebiveis', :val_antigo, NULL, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": lancamento,
                    "linhas": linhas_removidas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Remoção concluída: {linhas_removidas} linhas com lançamento '{lancamento}' movidas para recebiveis_filtrados"
        print(f"[SUCCESS remover_linhas_lancamento_recebiveis] {msg}")
        return True, msg, linhas_removidas

    except Exception as e:
        msg = f"Erro ao remover linhas de lançamento de recebíveis: {str(e)}"
        print(f"[ERROR remover_linhas_lancamento_recebiveis] {msg}")
        return False, msg, 0


# ==============================
# Funções de Correção para Status
# ==============================


def atualizar_status_processamento(
    engine: Engine,
    processamentoid: str,
    status_antigo: str,
    status_novo: str,
    usuario: str = "sistema",
) -> Tuple[bool, str, int]:
    """
    Atualiza todas as linhas de um status específico em um processamento.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        status_antigo: Status atual que será substituído
        status_novo: Novo status
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_afetadas)
    """
    try:
        print(f"[DEBUG atualizar_status] Processamento: {processamentoid}")
        print(f"[DEBUG atualizar_status] De: '{status_antigo}' Para: '{status_novo}'")

        # Contar quantas linhas serão afetadas
        sql_count = """
            SELECT COUNT(*) as total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND status_da_venda = :status_antigo
        """
        result = fetch_one(
            engine,
            sql_count,
            {"pid": processamentoid, "status_antigo": status_antigo},
        )
        linhas_afetadas = result.get("total", 0) if result else 0

        if linhas_afetadas == 0:
            return (
                False,
                f"Nenhuma linha encontrada com status '{status_antigo}'",
                0,
            )

        # Realizar atualização
        sql_update = """
            UPDATE vendas_processadas
            SET status_da_venda = :status_novo
            WHERE processamentoid = :pid AND status_da_venda = :status_antigo
        """

        exec_sql(
            engine,
            sql_update,
            {
                "pid": processamentoid,
                "status_antigo": status_antigo,
                "status_novo": status_novo,
            },
        )

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'status_venda', :val_antigo, :val_novo, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": status_antigo,
                    "val_novo": status_novo,
                    "linhas": linhas_afetadas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Atualização concluída: {linhas_afetadas} linhas alteradas de '{status_antigo}' para '{status_novo}'"
        print(f"[SUCCESS atualizar_status] {msg}")
        return True, msg, linhas_afetadas

    except Exception as e:
        msg = f"Erro ao atualizar status: {str(e)}"
        print(f"[ERROR atualizar_status] {msg}")
        return False, msg, 0


def remover_linhas_status(
    engine: Engine, processamentoid: str, status: str, usuario: str = "sistema"
) -> Tuple[bool, str, int]:
    """
    Remove todas as linhas de um status específico em um processamento.

    Args:
        engine: Engine do SQLAlchemy
        processamentoid: ID do processamento a corrigir
        status: Status a remover
        usuario: Usuário que está fazendo a correção

    Returns:
        Tupla (sucesso, mensagem, linhas_removidas)
    """
    try:
        print(f"[DEBUG remover_linhas_status] Processamento: {processamentoid}")
        print(f"[DEBUG remover_linhas_status] Status: '{status}'")

        # Contar quantas linhas serão removidas
        sql_count = """
            SELECT COUNT(*) as total
            FROM vendas_processadas
            WHERE processamentoid = :pid AND status_da_venda = :status
        """
        result = fetch_one(
            engine, sql_count, {"pid": processamentoid, "status": status}
        )
        linhas_removidas = result.get("total", 0) if result else 0

        if linhas_removidas == 0:
            return (
                False,
                f"Nenhuma linha encontrada com status '{status}'",
                0,
            )

        # ⚠️ CRÍTICO: Deletar cálculos primeiro (FK constraint)
        sql_delete_calculos = """
            DELETE FROM vendas_calculos
            WHERE id_venda IN (
                SELECT id FROM vendas_processadas
                WHERE processamentoid = :pid AND status_da_venda = :status
            )
        """

        # Mover para vendas_filtradas ao invés de deletar
        # ⚠️ CRÍTICO: Especificar colunas (excluindo 'id' AUTO_INCREMENT) para evitar conflito
        sql_insert = """
            INSERT IGNORE INTO vendas_filtradas (
                Data_da_venda, Data_da_autorização_da_venda, status_da_venda, Adquirente,
                Bandeira, Forma_de_pagamento, Quantidade_de_parcelas, Resumo_da_operação,
                Valor_da_venda, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                Previsão_de_pagamento, Valor_líquido_da_venda, Número_da_máquina,
                Código_de_autorização, NSU, Número_do_cartão, Receba_rápido, Status,
                Tratar_ou_Ignorar, Filtrado, arquivo_origem, processamentoid,
                cliente_id, ec_id, data_processamento, usuario_processamento
            )
            SELECT 
                Data_da_venda, Data_da_autorização_da_venda, status_da_venda, Adquirente,
                Bandeira, Forma_de_pagamento, Quantidade_de_parcelas, Resumo_da_operação,
                Valor_da_venda, Taxas_Perc, Valor_descontado, Taxas_RR, Valor_RR,
                Previsão_de_pagamento, Valor_líquido_da_venda, Número_da_máquina,
                Código_de_autorização, NSU, Número_do_cartão, Receba_rápido, Status,
                Tratar_ou_Ignorar, Filtrado, arquivo_origem, processamentoid,
                cliente_id, ec_id, data_processamento, usuario_processamento
            FROM vendas_processadas
            WHERE processamentoid = :pid AND status_da_venda = :status
        """

        sql_delete = """
            DELETE FROM vendas_processadas
            WHERE processamentoid = :pid AND status_da_venda = :status
        """

        print(f"[DEBUG] Movendo {linhas_removidas} linhas para vendas_filtradas...")

        # 1. Deletar cálculos associados (evita erro FK)
        exec_sql(
            engine, sql_delete_calculos, {"pid": processamentoid, "status": status}
        )
        print(f"[DEBUG] ✓ Cálculos deletados")

        # 2. Insere em vendas_filtradas (sem o campo 'id')
        exec_sql(engine, sql_insert, {"pid": processamentoid, "status": status})
        print(f"[DEBUG] ✓ Linhas inseridas em vendas_filtradas")

        # 3. Remove de vendas_processadas
        exec_sql(engine, sql_delete, {"pid": processamentoid, "status": status})
        print(f"[DEBUG] ✓ Linhas removidas de vendas_processadas")

        # Registrar log de auditoria
        sql_log = f"""
            INSERT INTO log_correcoes_importacao 
            (processamentoid, tipo_correcao, valor_antigo, valor_novo, linhas_afetadas, usuario, data_correcao)
            VALUES (:pid, 'remocao_status', :val_antigo, NULL, :linhas, :usuario, {_current_timestamp_sql(engine)})
        """

        try:
            exec_sql(
                engine,
                sql_log,
                {
                    "pid": processamentoid,
                    "val_antigo": status,
                    "linhas": linhas_removidas,
                    "usuario": usuario,
                },
            )
        except Exception as e_log:
            print(f"[WARNING] Erro ao registrar log (tabela pode não existir): {e_log}")

        msg = f"Remoção concluída: {linhas_removidas} linhas com status '{status}' movidas para vendas_filtradas"
        print(f"[SUCCESS remover_linhas_status] {msg}")
        return True, msg, linhas_removidas

    except Exception as e:
        msg = f"Erro ao remover linhas de status: {str(e)}"
        print(f"[ERROR remover_linhas_status] {msg}")
        return False, msg, 0
