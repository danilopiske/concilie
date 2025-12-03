from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Any
from sqlalchemy.engine import Engine
from sqlalchemy import text
from datetime import datetime


# ==============================
# Helper para compatibilidade MySQL/SQLite
# ==============================


def _is_sqlite(engine: Engine) -> bool:
    """Verifica se a engine é SQLite"""
    return engine.dialect.name == "sqlite"


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
    """Retorna SQL para comparação case-insensitive de texto

    Args:
        engine: Engine do banco de dados
        column: Nome da coluna a comparar
        param: Nome do parâmetro (ex: 'ctx')

    Returns:
        SQL compatível com SQLite/MySQL para comparação case-insensitive
    """
    if _is_sqlite(engine):
        # SQLite: usar UPPER() para case-insensitive
        return f"UPPER({column}) = UPPER(:{param})"
    else:
        # MySQL: já é case-insensitive por padrão
        return f"{column} = :{param}"


def _date_format_sql(engine: Engine, column: str, format_str: str) -> str:
    """Retorna SQL de formatação de data compatível com MySQL e SQLite

    Args:
        column: Nome da coluna de data
        format_str: Formato MySQL (ex: '%Y-%m-%d', '%Y-%m')

    Returns:
        SQL formatado para o banco correto
    """
    if _is_sqlite(engine):
        # SQLite usa strftime
        # Converter formato MySQL para SQLite:
        # %Y-%m-%d -> %Y-%m-%d (mesmo)
        # %Y-%m -> %Y-%m (mesmo)
        sqlite_format = format_str  # A maioria dos formatos é compatível
        return f"strftime('{sqlite_format}', {column})"
    else:
        # MySQL usa DATE_FORMAT
        return f"DATE_FORMAT({column}, '{format_str}')"


def _concat_sql(engine: Engine, *args: str) -> str:
    """Retorna SQL de concatenação compatível com MySQL e SQLite

    Args:
        *args: Expressões SQL a concatenar

    Returns:
        SQL de concatenação para o banco correto
    """
    if _is_sqlite(engine):
        # SQLite usa || para concatenação
        return " || ".join(args)
    else:
        # MySQL usa CONCAT()
        return f"CONCAT({', '.join(args)})"


def _insert_ignore_sql(engine: Engine, table: str, columns: str, values: str) -> str:
    """Retorna SQL de INSERT IGNORE compatível com MySQL e SQLite"""
    if _is_sqlite(engine):
        return f"INSERT OR IGNORE INTO {table} ({columns}) VALUES ({values})"
    else:
        return f"INSERT IGNORE INTO {table} ({columns}) VALUES ({values})"


def _year_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para extrair ano de uma data"""
    if _is_sqlite(engine):
        return f"strftime('%Y', {column})"
    else:
        return f"YEAR({column})"


def _month_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para extrair mês (número) de uma data"""
    if _is_sqlite(engine):
        return f"CAST(strftime('%m', {column}) AS INTEGER)"
    else:
        return f"MONTH({column})"


def _quarter_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para calcular trimestre de uma data"""
    if _is_sqlite(engine):
        # SQLite: calcular trimestre com CASE baseado no mês
        return f"""CASE 
            WHEN {_month_sql(engine, column)} <= 3 THEN '1'
            WHEN {_month_sql(engine, column)} <= 6 THEN '2'
            WHEN {_month_sql(engine, column)} <= 9 THEN '3'
            ELSE '4'
        END"""
    else:
        return f"QUARTER({column})"


def _semester_sql(engine: Engine, column: str) -> str:
    """Retorna SQL para calcular semestre de uma data"""
    month_sql = _month_sql(engine, column)
    if _is_sqlite(engine):
        return f"CASE WHEN {month_sql} <= 6 THEN '1' ELSE '2' END"
    else:
        return f"IF({month_sql} <= 6, '1', '2')"


def _get_table_columns(engine: Engine, table_name: str) -> List[str]:
    """Retorna lista de colunas de uma tabela"""
    if _is_sqlite(engine):
        # SQLite: usa PRAGMA table_info
        rows = fetch_all(engine, f"PRAGMA table_info({table_name})")
        return [r["name"] for r in rows]
    else:
        # MySQL: usa INFORMATION_SCHEMA
        rows = fetch_all(
            engine,
            f"""
            SELECT COLUMN_NAME AS coluna FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """,
        )
        return [r["coluna"] for r in rows]


def _upsert_sql(
    engine: Engine, table: str, columns: List[str], update_columns: List[str]
) -> str:
    """Retorna SQL de UPSERT (INSERT ... ON DUPLICATE KEY UPDATE) compatível"""
    cols_str = ", ".join(columns)
    placeholders = ", ".join([f":{col}" for col in columns])

    if _is_sqlite(engine):
        # SQLite usa INSERT OR REPLACE ou INSERT ... ON CONFLICT
        # Para ON CONFLICT precisamos saber as colunas únicas
        # Vamos usar a estratégia mais simples: INSERT OR REPLACE
        return f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders})"
    else:
        # MySQL: INSERT ... ON DUPLICATE KEY UPDATE
        updates = ", ".join([f"{col}=VALUES({col})" for col in update_columns])
        return f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {updates}"


# ==============================
# Recebíveis - Processados e Filtrados
# ==============================


def recebiveis_processados_bulk_insert(engine: Engine, df) -> int:
    df.to_sql(
        name="recebiveis_processados",
        con=engine,
        index=False,
        if_exists="append",
        chunksize=10000,
    )
    return len(df)


def recebiveis_filtrados_bulk_insert(engine: Engine, df) -> int:
    df.to_sql(
        name="recebiveis_filtrados",
        con=engine,
        index=False,
        if_exists="append",
        chunksize=10000,
    )
    return len(df)


def recebiveis_remover_duplicadas(
    engine: Engine, nome_tabela: str, processamento_id: str, df_cols: List[str]
) -> None:
    if nome_tabela not in {"recebiveis_processados", "recebiveis_filtrados"}:
        raise ValueError("Nome de tabela inválido para recebíveis.")

    # Colunas para deduplicação (fixas)
    colunas_para_groupby = [
        "`recebivel_id`",
        "`lancamento`",
        "`valor_liquido`",
        "`ec_id`",
        "`data_recebivel`",
        "`data_pagamento`",
    ]

    print(f"[DEBUG][RECEBIVEIS_DUPLICADAS] Tabela: {nome_tabela}")
    print(f"[DEBUG][RECEBIVEIS_DUPLICADAS] Colunas recebidas: {df_cols}")
    # print(f"[DEBUG][RECEBIVEIS_DUPLICADAS] Colunas ignoradas: {colunas_a_ignorar}")
    print(
        f"[DEBUG][RECEBIVEIS_DUPLICADAS] Colunas para agrupamento: {[col.replace('`', '') for col in colunas_para_groupby]}"
    )

    if not colunas_para_groupby:
        print(
            f"[DEBUG][RECEBIVEIS_DUPLICADAS] Nenhuma coluna para agrupamento, retornando sem fazer nada"
        )
        return

    group_by_cols = ", ".join(colunas_para_groupby)

    sql = f"""
    DELETE FROM {nome_tabela}
    WHERE id IN (
        SELECT * FROM (
            SELECT r.id FROM {nome_tabela} r
            WHERE r.processamentoid = :id_proc
            AND r.id NOT IN (
                SELECT MIN(id) FROM {nome_tabela}
                WHERE processamentoid = :id_proc
                GROUP BY {group_by_cols}
            )
        ) AS sub
    )
    """

    print(f"[DEBUG][RECEBIVEIS_DUPLICADAS] SQL a ser executado:")
    print(sql.replace(":id_proc", f"'{processamento_id}'"))

    exec_sql(engine, sql, {"id_proc": processamento_id})
    print(
        f"[DEBUG][RECEBIVEIS_DUPLICADAS] Remoção de duplicadas concluída para {nome_tabela}"
    )


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
    with get_conn(engine) as conn:
        conn.execute(text(sql), params or {})


def fetch_one(
    engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Fetches a single row from a SQL query."""
    with get_conn(engine) as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None


def fetch_all(
    engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Fetches all rows from a SQL query."""
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
    # Normalizar contexto para uppercase se for SQLite
    contexto_norm = (contexto or "").strip()
    if _is_sqlite(engine):
        contexto_norm = contexto_norm.upper()

    exec_sql(
        engine,
        sql,
        {
            "origem": (origem_nome or "").strip() if origem_nome else None,
            "destino": (destino_nome or "").strip(),
            "contexto": contexto_norm,
            "tipo": (tipo_origem or "V"),
            "ativo": int(ativo),
            "criado_por": criado_por,
            "tipo_preenchimento": tipo_preenchimento,
            "valor_padrao": valor_padrao,
        },
    )


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
    # Normalizar contexto para uppercase se for SQLite
    contexto_norm = (contexto or "").strip()
    if _is_sqlite(engine):
        contexto_norm = contexto_norm.upper()

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
    sql = "DELETE FROM clientes WHERE cliente_id = :cliente_id"
    exec_sql(engine, sql, {"cliente_id": cliente_id})


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
    # Normalizar contexto para uppercase se for SQLite
    contexto_norm = contexto
    if _is_sqlite(engine):
        contexto_norm = contexto.upper()

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


def vendas_processadas_bulk_insert(engine: Engine, df) -> int:
    df.to_sql(
        name="vendas_processadas",
        con=engine,
        index=False,
        if_exists="append",
        chunksize=10000,
    )
    return len(df)


def vendas_filtradas_bulk_insert(engine: Engine, df) -> int:
    df.to_sql(
        name="vendas_filtradas",
        con=engine,
        index=False,
        if_exists="append",
        chunksize=10000,
    )
    return len(df)


def vendas_diversas_bulk_insert(engine: Engine, df) -> int:
    df.to_sql(
        name="vendas_diversas",
        con=engine,
        index=False,
        if_exists="append",
        chunksize=10000,
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

    group_by_cols = ", ".join(colunas_para_groupby)

    sql = f"""
    DELETE FROM {nome_tabela}
    WHERE id IN (
        SELECT * FROM (
            SELECT v.id FROM {nome_tabela} v
            LEFT JOIN vendas_calculos c ON v.id = c.id_venda
            WHERE v.processamentoid = :id_proc AND c.id_venda IS NULL
            AND v.id NOT IN (
                SELECT MIN(id) FROM {nome_tabela}
                WHERE processamentoid = :id_proc
                GROUP BY {group_by_cols}
            )
        ) AS sub
    )
    """
    exec_sql(engine, sql, {"id_proc": processamento_id})


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
    return _get_table_columns(engine, "vendas_processadas")


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
    cols_real = set(_get_table_columns(engine, "vendas_processadas"))

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
    exec_sql(
        engine,
        sql,
        {
            "nome": (nome or "").strip(),
            "descricao": (descricao or "").strip() if descricao else None,
            "ativo": int(ativo),
            "criado_por": criado_por,
        },
    )


def contexto_atualizar(
    engine: Engine,
    contexto_id: int,
    *,
    nome: str,
    descricao: Optional[str] = None,
    ativo: int = 1,
) -> None:
    """Atualiza um contexto existente."""
    sql = """
    UPDATE contextos
    SET nome = :nome,
        descricao = :descricao,
        ativo = :ativo,
        atualizado_em = CURRENT_TIMESTAMP
    WHERE id = :id
    """
    exec_sql(
        engine,
        sql,
        {
            "id": contexto_id,
            "nome": (nome or "").strip(),
            "descricao": (descricao or "").strip() if descricao else None,
            "ativo": int(ativo),
        },
    )


def contexto_deletar(engine: Engine, contexto_id: int) -> bool:
    """Deleta um contexto se não houver de-para associado."""
    if not contexto_pode_deletar(engine, contexto_id):
        return False
    sql = "DELETE FROM contextos WHERE id = :id"
    try:
        exec_sql(engine, sql, {"id": contexto_id})
        return True
    except Exception as e:
        print(f"Erro ao deletar contexto: {e}")
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
    if _is_sqlite(engine):
        sql = sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")

    with get_conn(engine) as conn:
        result = conn.execute(
            text(sql),
            {
                "nome_analise": nome_analise.strip(),
                "descricao": descricao.strip() if descricao else None,
                "usuario_criador": usuario_criador,
            },
        )
        if _is_sqlite(engine):
            return result.lastrowid
        else:
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

    if _is_sqlite(engine):
        updates.append("data_atualizacao = CURRENT_TIMESTAMP")
    else:
        updates.append("data_atualizacao = NOW()")

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
    """Deleta um contexto se não houver dependências."""
    # Primeiro verifica se há depara_colunas usando este contexto
    sql = "SELECT COUNT(*) as total FROM depara_colunas WHERE contexto = (SELECT nome FROM contextos WHERE id = :id)"
    result = fetch_one(engine, sql, {"id": contexto_id})
    if result and result["total"] > 0:
        return False

    # Se não houver dependências, deleta o contexto
    sql = "DELETE FROM contextos WHERE id = :id"
    exec_sql(engine, sql, {"id": contexto_id})
    return True


def contexto_pode_deletar(engine: Engine, contexto_id: int) -> bool:
    """Verifica se um contexto pode ser deletado (não tem dependências)."""
    sql = "SELECT COUNT(*) as total FROM depara_colunas WHERE contexto = (SELECT nome FROM contextos WHERE id = :id)"
    result = fetch_one(engine, sql, {"id": contexto_id})
    return result["total"] == 0 if result else True


# ==============================
# Agregações Otimizadas para Analista
# ==============================


def agregar_bandeiras_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega dados de bandeiras diretamente no banco de dados (muito mais rápido)"""
    print(
        f"[DEBUG agregar_bandeiras_db] Iniciando agregação para processamento: {processamentoid}"
    )
    print(
        f"[DEBUG agregar_bandeiras_db] Tipo do banco: {'SQLite' if _is_sqlite(engine) else 'MySQL'}"
    )

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


def agregar_periodos_db(engine: Engine, processamentoid: str) -> List[Dict[str, Any]]:
    """Agrega dados por períodos (mês, trimestre, semestre, ano) diretamente no banco"""
    print(
        f"[DEBUG agregar_periodos_db] Iniciando agregação para processamento: {processamentoid}"
    )
    print(
        f"[DEBUG agregar_periodos_db] Tipo do banco: {'SQLite' if _is_sqlite(engine) else 'MySQL'}"
    )

    # Construir expressões SQL compatíveis com ambos os bancos
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
    print(f"[DEBUG agregar_recebiveis_db] Nenhuma coluna de tipo de recebível encontrada")
    return []
