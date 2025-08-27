# conf/funcoesbd.py
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.engine import Engine
from sqlalchemy import text

# =========================
# Helpers básicos de acesso
# =========================

@contextmanager
def get_conn(engine: Engine):
    with engine.begin() as conn:
        yield conn

def exec_sql(engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None) -> None:
    with get_conn(engine) as conn:
        conn.execute(text(sql), params or {})

def fetch_one(engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    with get_conn(engine) as conn:
        row = conn.execute(text(sql), params or {}).mappings().first()
        return dict(row) if row else None

def fetch_all(engine: Engine, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    with get_conn(engine) as conn:
        rows = conn.execute(text(sql), params or {}).mappings().all()
        return [dict(r) for r in rows]

# ==================
# De-Para de colunas
# ==================

def depara_listar(engine: Engine, contexto: str = "", tipo_origem: str = "V") -> List[Dict[str, Any]]:
    """
    Lista mapeamentos. Se contexto == "" (vazio), não filtra por contexto.
    """
    if (contexto or "") == "":
        sql = """
        SELECT id, origem_nome, destino_nome, contexto, tipo_origem, ativo, criado_por, criado_em, atualizado_em
          FROM depara_colunas
         WHERE tipo_origem = :tipo
         ORDER BY ativo DESC, origem_nome ASC
        """
        return fetch_all(engine, sql, {"tipo": tipo_origem})
    else:
        sql = """
        SELECT id, origem_nome, destino_nome, contexto, tipo_origem, ativo, criado_por, criado_em, atualizado_em
          FROM depara_colunas
         WHERE tipo_origem = :tipo AND contexto = :ctx
         ORDER BY ativo DESC, origem_nome ASC
        """
        return fetch_all(engine, sql, {"tipo": tipo_origem, "ctx": contexto})

def depara_upsert(
    engine: Engine, *,
    origem_nome: str, destino_nome: str,
    contexto: str = "", tipo_origem: str = "V",
    ativo: int = 1, criado_por: Optional[str] = None
) -> None:
    """
    Insere/atualiza conforme UNIQUE KEY (origem_nome, contexto, tipo_origem).
    Observação: tabela usa contexto NOT NULL DEFAULT ''.
    """
    sql = """
    INSERT INTO depara_colunas (origem_nome, destino_nome, contexto, tipo_origem, ativo, criado_por)
    VALUES (:origem, :destino, :contexto, :tipo, :ativo, :criado_por)
    ON DUPLICATE KEY UPDATE
      destino_nome = VALUES(destino_nome),
      ativo        = VALUES(ativo)
    """
    exec_sql(engine, sql, {
        "origem": (origem_nome or "").strip(),
        "destino": (destino_nome or "").strip(),
        "contexto": (contexto or "").strip(),
        "tipo": (tipo_origem or "V"),
        "ativo": int(ativo),
        "criado_por": criado_por
    })

def depara_inserir(
    engine: Engine, *,
    origem_nome: str, destino_nome: str,
    contexto: str = "", tipo_origem: str = "V",
    ativo: int = 1, criado_por: Optional[str] = None
) -> None:
    """
    Insert estrito (deixa o BD acusar duplicidade).
    """
    sql = """
    INSERT INTO depara_colunas
      (origem_nome, destino_nome, contexto, tipo_origem, ativo, criado_por)
    VALUES
      (:origem, :destino, :contexto, :tipo, :ativo, :criado_por)
    """
    exec_sql(engine, sql, {
        "origem": (origem_nome or "").strip(),
        "destino": (destino_nome or "").strip(),
        "contexto": (contexto or "").strip(),
        "tipo": (tipo_origem or "V"),
        "ativo": int(ativo),
        "criado_por": criado_por,
    })

def depara_atualizar(
    engine: Engine, depara_id: int, *,
    origem_nome: str, destino_nome: str,
    contexto: str = "", tipo_origem: str = "V",
    ativo: int = 1
) -> None:
    sql = """
    UPDATE depara_colunas
       SET origem_nome  = :origem,
           destino_nome = :destino,
           contexto     = :contexto,
           tipo_origem  = :tipo,
           ativo        = :ativo
     WHERE id = :id
    """
    exec_sql(engine, sql, {
        "id": depara_id,
        "origem": (origem_nome or "").strip(),
        "destino": (destino_nome or "").strip(),
        "contexto": (contexto or "").strip(),
        "tipo": (tipo_origem or "V"),
        "ativo": int(ativo),
    })

def depara_deletar(engine: Engine, depara_id: int) -> None:
    exec_sql(engine, "DELETE FROM depara_colunas WHERE id = :id", {"id": depara_id})

def depara_buscar_por_chave(engine: Engine, *, origem_nome: str, contexto: str = "", tipo_origem: str = "V") -> Optional[Dict[str, Any]]:
    sql = """
    SELECT id, origem_nome, destino_nome, contexto, tipo_origem, ativo
      FROM depara_colunas
     WHERE origem_nome = :origem
       AND contexto = :contexto
       AND tipo_origem = :tipo
     LIMIT 1
    """
    return fetch_one(engine, sql, {
        "origem": (origem_nome or "").strip(),
        "contexto": (contexto or "").strip(),
        "tipo": (tipo_origem or "V"),
    })

def depara_carregar_mapa(engine: Engine, contexto: str = "", tipo_origem: str = "V") -> Dict[str, str]:
    """
    Retorna {origem_nome: destino_nome} somente de registros ativos.
    """
    if (contexto or "") == "":
        rows = fetch_all(engine, """
            SELECT origem_nome, destino_nome
              FROM depara_colunas
             WHERE ativo = 1 AND tipo_origem = :tipo
        """, {"tipo": tipo_origem})
    else:
        rows = fetch_all(engine, """
            SELECT origem_nome, destino_nome
              FROM depara_colunas
             WHERE ativo = 1 AND tipo_origem = :tipo AND contexto = :ctx
        """, {"tipo": tipo_origem, "ctx": contexto})
    return {r["origem_nome"]: r["destino_nome"] for r in rows}

# -------------------------------
# Listas dinâmicas para a camada UI
# -------------------------------

def listar_bandeiras_distintas(engine: Engine) -> List[str]:
    """
    Retorna a lista de contextos (bandeiras) distintos para popular selects de contexto.
    """
    rows = fetch_all(engine, "SELECT DISTINCT bandeira FROM bandeiras_cliente ORDER BY bandeira")
    vals: List[str] = []
    for r in rows:
        b = str(r.get("bandeira", "")).strip()
        if b:
            vals.append(b)
    # remove duplicados preservando ordem
    seen = set()
    out: List[str] = []
    for v in vals:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out

def listar_colunas_vendas_processadas(engine: Engine) -> List[str]:
    """
    Lista as colunas disponíveis na tabela vendas_processadas via INFORMATION_SCHEMA.
    """
    sql = """
    SELECT COLUMN_NAME
      FROM INFORMATION_SCHEMA.COLUMNS
     WHERE TABLE_SCHEMA = DATABASE()
       AND TABLE_NAME   = 'vendas_processadas'
     ORDER BY ORDINAL_POSITION
    """
    rows = fetch_all(engine, sql)
    cols = [str(r["COLUMN_NAME"]) for r in rows if r.get("COLUMN_NAME")]
    return cols

# ==============
# Clientes / ECs
# ==============

def cliente_inserir(engine: Engine, dados: Dict[str, Any]) -> None:
    with get_conn(engine) as conn:
        conn.execute(text("""
            INSERT INTO clientes (cliente_id, nome_fantasia, razao_social, cnpj)
            VALUES (:cliente_id, :nome_fantasia, :razao_social, :cnpj)
        """), dados)
        conn.execute(text("""
            INSERT INTO enderecos (cliente_id, logradouro, numero, complemento, bairro, cidade, uf_id)
            VALUES (:cliente_id, :logradouro, :numero, :complemento, :bairro, :cidade, :uf_id)
        """), dados)
        conn.execute(text("""
            INSERT INTO contatos (cliente_id, telefone1, telefone2, telefone3, email1, email2)
            VALUES (:cliente_id, :telefone1, :telefone2, :telefone3, :email1, :email2)
        """), dados)
        conn.execute(text("""
            INSERT INTO dados_bancarios (cliente_id, banco, agencia, conta)
            VALUES (:cliente_id, :banco, :agencia, :conta)
        """), dados)
        for ec in dados.get("ecs", []):
            try:
                conn.execute(text("""
                    INSERT INTO ecs_cliente (cliente_id, ec_id)
                    VALUES (:cliente_id, :ec_id)
                """), {"cliente_id": dados["cliente_id"], "ec_id": ec})
            except Exception:
                # se já existir, ignora
                pass

def cliente_atualizar(engine: Engine, dados: Dict[str, Any]) -> None:
    with get_conn(engine) as conn:
        conn.execute(text("""
            UPDATE clientes SET nome_fantasia = :nome_fantasia,
                razao_social = :razao_social, cnpj = :cnpj
            WHERE cliente_id = :cliente_id
        """), dados)
        conn.execute(text("""
            UPDATE enderecos SET logradouro = :logradouro, numero = :numero,
                complemento = :complemento, bairro = :bairro, cidade = :cidade, uf_id = :uf_id
            WHERE cliente_id = :cliente_id
        """), dados)
        conn.execute(text("""
            UPDATE contatos SET telefone1 = :telefone1, telefone2 = :telefone2,
                telefone3 = :telefone3, email1 = :email1, email2 = :email2
            WHERE cliente_id = :cliente_id
        """), dados)
        conn.execute(text("""
            UPDATE dados_bancarios SET banco = :banco, agencia = :agencia, conta = :conta
            WHERE cliente_id = :cliente_id
        """), dados)

def cliente_deletar(engine: Engine, cliente_id: int) -> None:
    with get_conn(engine) as conn:
        conn.execute(text("DELETE FROM ecs_cliente WHERE cliente_id = :id"), {"id": cliente_id})
        conn.execute(text("DELETE FROM dados_bancarios WHERE cliente_id = :id"), {"id": cliente_id})
        conn.execute(text("DELETE FROM contatos WHERE cliente_id = :id"), {"id": cliente_id})
        conn.execute(text("DELETE FROM enderecos WHERE cliente_id = :id"), {"id": cliente_id})
        conn.execute(text("DELETE FROM clientes WHERE cliente_id = :id"), {"id": cliente_id})

def clientes_listar(engine: Engine) -> List[Dict[str, Any]]:
    sql = """
    SELECT c.cliente_id, c.nome_fantasia, c.razao_social, c.cnpj,
           e.cidade, e.uf_id
      FROM clientes c
      JOIN enderecos e ON e.cliente_id = c.cliente_id
     ORDER BY c.nome_fantasia
    """
    return fetch_all(engine, sql)

def cliente_por_id(engine: Engine, cliente_id: int) -> Optional[Dict[str, Any]]:
    with get_conn(engine) as conn:
        cliente = conn.execute(text("SELECT * FROM clientes WHERE cliente_id = :id"),
                               {"id": cliente_id}).mappings().first()
        if not cliente:
            return None
        endereco = conn.execute(text("SELECT * FROM enderecos WHERE cliente_id = :id"),
                                {"id": cliente_id}).mappings().first()
        contatos = conn.execute(text("SELECT * FROM contatos WHERE cliente_id = :id"),
                                {"id": cliente_id}).mappings().first()
        bancario = conn.execute(text("SELECT * FROM dados_bancarios WHERE cliente_id = :id"),
                                {"id": cliente_id}).mappings().first()
        ecs = conn.execute(text("SELECT ec_id FROM ecs_cliente WHERE cliente_id = :id"),
                           {"id": cliente_id}).scalars().all()

    return {
        "cliente_id": cliente_id,
        "nome_fantasia": cliente["nome_fantasia"],
        "razao_social": cliente["razao_social"],
        "cnpj": cliente["cnpj"],
        "endereco": dict(endereco) if endereco else {},
        "contatos": dict(contatos) if contatos else {},
        "bancario": dict(bancario) if bancario else {},
        "ecs": ecs
    }

def ecs_adicionar(engine: Engine, cliente_id: int, ec_id: int) -> bool:
    try:
        exec_sql(engine, """
            INSERT INTO ecs_cliente (cliente_id, ec_id)
            VALUES (:cliente_id, :ec_id)
        """, {"cliente_id": cliente_id, "ec_id": ec_id})
        return True
    except Exception:
        return False

def ecs_remover(engine: Engine, cliente_id: int, ec_id: int) -> bool:
    with get_conn(engine) as conn:
        result = conn.execute(text("""
            DELETE FROM ecs_cliente
            WHERE cliente_id = :cliente_id AND ec_id = :ec_id
        """), {"cliente_id": cliente_id, "ec_id": ec_id})
        return result.rowcount > 0

def ecs_por_cliente(engine: Engine, cliente_id: int) -> List[int]:
    with get_conn(engine) as conn:
        rows = conn.execute(text("SELECT ec_id FROM ecs_cliente WHERE cliente_id = :id"),
                            {"id": cliente_id}).fetchall()
        return [r[0] for r in rows]

# =====
# Taxas
# =====

def taxa_adicionar(engine: Engine, taxa: Dict[str, Any]) -> None:
    sql = """
    INSERT INTO taxas (
        ec, bandeira, forma_pagamento, parcelado,
        parcelas_ini, parcelas_fim, data_ini, data_fim, taxa
    )
    VALUES (
        :ec, :bandeira, :forma_pagamento, :parcelado,
        :parcelas_ini, :parcelas_fim, :data_ini, :data_fim, :taxa
    )
    """
    exec_sql(engine, sql, taxa)

def taxa_excluir(engine: Engine, taxa_id: int) -> None:
    exec_sql(engine, "DELETE FROM taxas WHERE id = :id", {"id": taxa_id})

def taxa_atualizar(engine: Engine, taxa_id: int, dados: Dict[str, Any]) -> None:
    sql = """
    UPDATE taxas SET
        ec = :ec,
        bandeira = :bandeira,
        forma_pagamento = :forma_pagamento,
        parcelado = :parcelado,
        parcelas_ini = :parcelas_ini,
        parcelas_fim = :parcelas_fim,
        data_ini = :data_ini,
        data_fim = :data_fim,
        taxa = :taxa
    WHERE id = :id
    """
    exec_sql(engine, sql, {**dados, "id": taxa_id})

def taxas_por_ec(engine: Engine, ec: str) -> List[Dict[str, Any]]:
    sql = """
    SELECT id, ec, bandeira, forma_pagamento, parcelado,
           parcelas_ini, parcelas_fim,
           DATE_FORMAT(data_ini, '%d/%m/%Y') as data_ini,
           DATE_FORMAT(data_fim, '%d/%m/%Y') as data_fim,
           taxa
      FROM taxas
     WHERE ec = :ec
     ORDER BY data_ini DESC
    """
    return fetch_all(engine, sql, {"ec": ec})

def taxas_excluir_todas_de_ec(engine: Engine, ec: str) -> None:
    exec_sql(engine, "DELETE FROM taxas WHERE ec = :ec", {"ec": ec})

# ===================
# Termos filtráveis
# ===================

def termos_listar(engine: Engine, ec: str) -> List[str]:
    with get_conn(engine) as conn:
        return conn.execute(
            text("SELECT termo FROM termos_filtraveis WHERE ec = :ec ORDER BY termo"),
            {"ec": ec}
        ).scalars().all()

def termo_adicionar(engine: Engine, ec: str, termo: str) -> None:
    exec_sql(engine, """
        INSERT IGNORE INTO termos_filtraveis (ec, termo)
        VALUES (:ec, :termo)
    """, {"ec": ec, "termo": termo.strip().lower()})

def termo_excluir(engine: Engine, ec: str, termo: str) -> None:
    exec_sql(engine, """
        DELETE FROM termos_filtraveis WHERE ec = :ec AND termo = :termo
    """, {"ec": ec, "termo": termo.strip().lower()})

# ======================
# Bandeiras por cliente
# ======================

def bandeiras_por_ec(engine: Engine, ec: str) -> Dict[str, int]:
    with get_conn(engine) as conn:
        rows = conn.execute(
            text("SELECT bandeira, ativo FROM bandeiras_cliente WHERE ec = :ec"),
            {"ec": ec}
        ).mappings().all()
        return {r["bandeira"]: r["ativo"] for r in rows}

def bandeiras_salvar_para_ec(engine: Engine, ec: str, bandeiras: Dict[str, int]) -> None:
    with get_conn(engine) as conn:
        for bandeira, ativo in bandeiras.items():
            conn.execute(text("""
                INSERT INTO bandeiras_cliente (ec, bandeira, ativo)
                VALUES (:ec, :bandeira, :ativo)
                ON DUPLICATE KEY UPDATE ativo = :ativo
            """), {"ec": ec, "bandeira": bandeira, "ativo": ativo})

# ===============
# Processamentos
# ===============

def processamento_gerar_novo_id(engine: Engine, ec_id: int, now) -> Tuple[str, Any]:
    """
    Gera um id no formato: "{ec_id}_{sequencial:04d} - dd/mm/yyyy HH:MM:SS"
    """
    with get_conn(engine) as conn:
        total = conn.execute(text("""
            SELECT COUNT(*) AS total
              FROM controle_processamentos
             WHERE ec_id = :ec_id
        """), {"ec_id": ec_id}).scalar()
    sequencial = (total or 0) + 1
    return f"{ec_id}_{sequencial:04d} - {now.strftime('%d/%m/%Y %H:%M:%S')}", now

def processamento_salvar(engine: Engine, ec_id: int, cliente_id: int,
                         id_processamento: str, descricao: str, data_processamento) -> None:
    exec_sql(engine, """
        INSERT INTO controle_processamentos (id_processamento, cliente_id, ec_id, descricao, data_processamento)
        VALUES (:id_processamento, :cliente_id, :ec_id, :descricao, :data_processamento)
    """, {
        "id_processamento": id_processamento,
        "cliente_id": cliente_id,
        "ec_id": ec_id,
        "descricao": descricao,
        "data_processamento": data_processamento
    })

def processamentos_existentes_por_ec(engine: Engine, ec_id: int) -> Dict[str, str]:
    with get_conn(engine) as conn:
        rows = conn.execute(text("""
            SELECT id_processamento, data_processamento
              FROM controle_processamentos
             WHERE ec_id = :ec_id
             ORDER BY data_processamento DESC
        """), {"ec_id": ec_id}).fetchall()
    return {
        f"{r[0]} - {r[1].strftime('%d/%m/%Y %H:%M')}": r[0]
        for r in rows
    }

def processamentos_resumo(engine: Engine) -> List[Dict[str, Any]]:
    sql = """
    SELECT 
        cp.id_processamento,
        cp.data_processamento,
        cp.ec_id,
        COUNT(vp.processamentoid) AS num_transacoes,
        FORMAT(SUM(vp.Valor_da_venda), 2) AS total_valor_venda
      FROM controle_processamentos cp
      LEFT JOIN vendas_processadas vp 
        ON vp.processamentoid = cp.id_processamento
      LEFT JOIN vendas_filtradas vf 
        ON vf.processamentoid = cp.id_processamento
     GROUP BY cp.id_processamento, cp.data_processamento, cp.ec_id
     ORDER BY cp.data_processamento DESC;
    """
    return fetch_all(engine, sql)

def processamentos_distintos(engine: Engine) -> List[str]:
    with get_conn(engine) as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT processamentoid
              FROM vendas_processadas
             ORDER BY processamentoid DESC
        """)).fetchall()
    return [r[0] for r in rows]

def processamento_deletar_cascata(engine: Engine, processamento_id: str) -> None:
    with get_conn(engine) as conn:
        conn.execute(text("""
            DELETE FROM vendas_calculos
             WHERE id_venda IN (
                SELECT id FROM vendas_processadas WHERE processamentoid = :pid
             )
        """), {"pid": processamento_id})
        conn.execute(text("DELETE FROM vendas_filtradas WHERE processamentoid = :pid"), {"pid": processamento_id})
        conn.execute(text("DELETE FROM vendas_processadas WHERE processamentoid = :pid"), {"pid": processamento_id})
        conn.execute(text("DELETE FROM controle_processamentos WHERE id_processamento = :pid"), {"pid": processamento_id})

# ======
# Vendas
# ======

def vendas_processadas_bulk_insert(engine: Engine, df) -> int:
    """
    Insere DataFrame em vendas_processadas (append).
    """
    df.to_sql(name="vendas_processadas", con=engine, index=False, if_exists="append", chunksize=10000)
    return len(df)

def vendas_filtradas_bulk_insert(engine: Engine, df) -> int:
    """
    Insere DataFrame em vendas_filtradas (append).
    """
    df.to_sql(name="vendas_filtradas", con=engine, index=False, if_exists="append", chunksize=10000)
    return len(df)

def vendas_remover_duplicadas(engine: Engine, nome_tabela: str, processamento_id: str) -> None:
    """
    Remove duplicadas mantendo o menor id por grupo, ignorando registros que já têm cálculo em vendas_calculos.
    Restringe a operação às tabelas esperadas.
    """
    if nome_tabela not in {"vendas_processadas", "vendas_filtradas"}:
        raise ValueError("Tabela inválida para remoção de duplicadas.")

    colunas = [
        "Data_da_venda","Data_da_autorização_da_venda","Bandeira","Forma_de_pagamento","Quantidade_de_parcelas",
        "Resumo_da_operação","Valor_da_venda","Taxas_Perc","Valor_descontado","Taxas_RR","Valor_RR",
        "Previsão_de_pagamento","Valor_líquido_da_venda","Canal_de_venda","Número_da_máquina",
        "Código_da_venda","Código_de_autorização","NSU","Número_do_cartão","Tipo_de_captura","Receba_rápido",
        "Comissão_Mínima","Número_da_nota_fiscal","Taxa_de_embarque","Valor_da_entrada","Valor_do_saque",
        "Status","Tratar_ou_Ignorar","Filtrado","processamentoid","cliente_id","ec_id"
    ]
    group_by_cols = ",\n                ".join([f"`{c}`" for c in colunas])

    sql = f"""
    DELETE FROM {nome_tabela}
    WHERE id IN (
        SELECT * FROM (
            SELECT v.id
              FROM {nome_tabela} v
              LEFT JOIN vendas_calculos c ON v.id = c.id_venda
             WHERE v.processamentoid = :id_proc
               AND c.id_venda IS NULL
               AND v.id NOT IN (
                    SELECT MIN(id)
                      FROM {nome_tabela}
                     WHERE processamentoid = :id_proc
                  GROUP BY {group_by_cols}
               )
        ) AS sub
    )
    """
    exec_sql(engine, sql, {"id_proc": processamento_id})

# =================
# Vendas - Cálculos
# =================

def vendas_calculos_bulk_insert(engine: Engine, rows: List[Dict[str, Any]]) -> None:
    """
    Insere lista de dicionários em vendas_calculos.
    """
    sql = text("""
        INSERT INTO vendas_calculos (
            id_venda, calc_id, calc_usuario, calc_data,
            tx_cad, desc_cad, vl_liq_cad,
            tx_log, desc_log, vl_liq_log
        )
        VALUES (
            :id_venda, :calc_id, :calc_usuario, :calc_data,
            :tx_cad, :desc_cad, :vl_liq_cad,
            :tx_log, :desc_log, :vl_liq_log
        )
    """)
    with get_conn(engine) as conn:
        conn.execute(sql, rows)

def listar_contextos(engine: Engine) -> List[str]:
    """
    Retorna a lista de contextos disponíveis (ex.: ['CIELO', 'REDE']).
    """
    rows = fetch_all(engine, "SELECT contexto FROM contextos ORDER BY contexto")
    return [str(r["contexto"]).strip() for r in rows if r.get("contexto")]

def inserir_contexto(engine: Engine, contexto: str) -> None:
    exec_sql(engine, "INSERT INTO contextos (contexto) VALUES (:ctx)", {"ctx": (contexto or "").strip()})

def excluir_contexto(engine: Engine, contexto: str) -> None:
    exec_sql(engine, "DELETE FROM contextos WHERE contexto = :ctx", {"ctx": (contexto or "").strip()})

# -------- vendas_colunas_controle (sem descricao/ordem)

def colunas_controle_listar(engine: Engine) -> List[Dict[str, Any]]:
    sql = """
    SELECT id, campo, preenchimento, mapeavel, ativo, created_at, updated_at
      FROM vendas_colunas_controle
     ORDER BY campo
    """
    return fetch_all(engine, sql)

def colunas_controle_inserir(engine: Engine, *, campo: str,
                             preenchimento: str = "importado",
                             mapeavel: int = 1,
                             ativo: int = 1) -> None:
    sql = """
    INSERT INTO vendas_colunas_controle
      (campo, preenchimento, mapeavel, ativo)
    VALUES
      (:campo, :preenchimento, :mapeavel, :ativo)
    """
    exec_sql(engine, sql, {
        "campo": (campo or "").strip(),
        "preenchimento": preenchimento,
        "mapeavel": int(mapeavel),
        "ativo": int(ativo),
    })

def colunas_controle_atualizar(engine: Engine, col_id: int, *, campo: str,
                               preenchimento: str, mapeavel: int, ativo: int) -> None:
    sql = """
    UPDATE vendas_colunas_controle
       SET campo         = :campo,
           preenchimento = :preenchimento,
           mapeavel      = :mapeavel,
           ativo         = :ativo
     WHERE id = :id
    """
    exec_sql(engine, sql, {
        "id": col_id,
        "campo": (campo or "").strip(),
        "preenchimento": preenchimento,
        "mapeavel": int(mapeavel),
        "ativo": int(ativo),
    })

def colunas_controle_deletar(engine: Engine, col_id: int) -> None:
    exec_sql(engine, "DELETE FROM vendas_colunas_controle WHERE id = :id", {"id": col_id})

def listar_colunas_mapeaveis(engine: Engine) -> List[str]:
    rows = fetch_all(engine, """
        SELECT campo FROM vendas_colunas_controle
         WHERE ativo = 1 AND mapeavel = 1
         ORDER BY campo
    """)
    return [r["campo"] for r in rows]

def colunas_controle_sincronizar(engine: Engine) -> Dict[str, int]:
    # 1) Colunas reais
    cols_real = fetch_all(engine, """
        SELECT COLUMN_NAME AS coluna
          FROM INFORMATION_SCHEMA.COLUMNS
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'vendas_processadas'
    """)
    cols_real = [str(r["coluna"]) for r in cols_real]

    # 2) Já cadastradas
    cadastradas = fetch_all(engine, "SELECT campo FROM vendas_colunas_controle")
    set_cadastradas = {str(r["campo"]) for r in cadastradas}

    sistema = {
        "id","processamentoid","cliente_id","ec_id",
        "arquivo_origem","data_processamento","usuario_processamento","Filtrado"
    }
    calculado = {"tx_cad","desc_cad","vl_liq_cad","tx_log","desc_log","vl_liq_log"}

    inseridos = 0
    for c in cols_real:
        if c in set_cadastradas:
            continue
        if c in sistema:
            pr, mapv = "sistema", 0
        elif c in calculado:
            pr, mapv = "calculado", 0
        else:
            pr, mapv = "importado", 1

        colunas_controle_inserir(engine, campo=c, preenchimento=pr, mapeavel=mapv, ativo=1)
        inseridos += 1

    return {"inseridos": inseridos, "existentes": len(set_cadastradas), "total_real": len(cols_real)}
