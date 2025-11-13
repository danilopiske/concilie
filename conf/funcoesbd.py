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
        filters.append("contexto = :ctx")
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
    exec_sql(
        engine,
        sql,
        {
            "origem": (origem_nome or "").strip() if origem_nome else None,
            "destino": (destino_nome or "").strip(),
            "contexto": (contexto or "").strip(),
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
    exec_sql(
        engine,
        sql,
        {
            "id": depara_id,
            "origem": (origem_nome or "").strip() if origem_nome else None,
            "destino": (destino_nome or "").strip(),
            "contexto": (contexto or "").strip(),
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
    sql = "SELECT id, origem_nome, destino_nome, contexto, tipo_origem, ativo FROM depara_colunas WHERE origem_nome = :origem AND contexto = :contexto AND tipo_origem = :tipo LIMIT 1"
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
        sql += " AND contexto = :ctx"
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


def bandeiras_por_ec(
    engine: Engine, ec: str, contexto: str = "padrao"
) -> Dict[str, int]:
    with get_conn(engine) as conn:
        rows = (
            conn.execute(
                text(
                    "SELECT bandeira, ativo FROM bandeiras_cliente WHERE ec = :ec AND contexto = :contexto"
                ),
                {"ec": ec, "contexto": contexto},
            )
            .mappings()
            .all()
        )
        return {r["bandeira"]: r["ativo"] for r in rows}


def bandeiras_salvar_para_ec(
    engine: Engine, ec: str, bandeiras: Dict[str, int], contexto: str = "padrao"
) -> None:
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
                {"ec": ec, "bandeira": bandeira, "ativo": ativo, "contexto": contexto},
            )


# ===================
# Termos filtráveis
# ===================


def termos_listar(
    engine: Engine, ec: str, contexto: str = "padrao", tipo: Optional[str] = None
) -> List[Dict[str, Any]]:
    with get_conn(engine) as conn:
        sql = "SELECT termo, tipo FROM termos_filtraveis WHERE ec = :ec AND contexto = :contexto"
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
        exec_sql(
            engine,
            "DELETE FROM termos_filtraveis WHERE ec = :ec AND termo = :termo AND contexto = :contexto",
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
    if _is_sqlite(engine):
        # SQLite: usa PRAGMA table_info
        rows = fetch_all(
            engine,
            "PRAGMA table_info(vendas_processadas)",
        )
        return [r["name"] for r in rows]
    else:
        # MySQL: usa INFORMATION_SCHEMA
        rows = fetch_all(
            engine,
            """
            SELECT COLUMN_NAME AS coluna FROM INFORMATION_SCHEMA.COLUMNS
             WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'vendas_processadas'
             ORDER BY ORDINAL_POSITION
            """,
        )
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
    rows = fetch_all(
        engine,
        """
        SELECT campo FROM vendas_colunas_controle
         WHERE ativo = 1 AND mapeavel = 1 AND contexto = :contexto AND tipo_arquivo = :tipo_arquivo
         ORDER BY campo
    """,
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

    if _is_sqlite(engine):
        # SQLite: usa PRAGMA table_info
        cols_real = {
            str(r["name"])
            for r in fetch_all(
                engine,
                "PRAGMA table_info(vendas_processadas)",
            )
        }
    else:
        # MySQL: usa INFORMATION_SCHEMA
        cols_real = {
            str(r["coluna"])
            for r in fetch_all(
                engine,
                """
            SELECT COLUMN_NAME AS coluna FROM INFORMATION_SCHEMA.COLUMNS
             WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'vendas_processadas'
        """,
            )
        }

    cadastradas = {
        str(r["campo"])
        for r in fetch_all(
            engine,
            "SELECT campo FROM vendas_colunas_controle WHERE contexto = :ctx AND tipo_arquivo = :tipo",
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
    sql = """
    SELECT id, ec, bandeira, forma_pagamento, parcelado,
           parcelas_ini, parcelas_fim, data_ini, data_fim, taxa, contexto
      FROM taxas
     WHERE ec = :ec AND contexto = :contexto
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
