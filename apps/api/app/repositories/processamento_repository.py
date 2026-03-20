from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.db_helpers import exec_sql, fetch_one
from app.models.legacy_processamento import LegacyProcessamento
from app.schemas.processamento import ProcessamentoFilter, ProcessamentoResponse

# ---------------------------------------------------------------------------
# Standalone helpers (replaces conf.funcoesbd.processamento_*)
# ---------------------------------------------------------------------------

def gerar_novo_id(engine: Engine, ec_id: str, now: datetime) -> Tuple[str, datetime]:
    """Generate a unique processamento ID based on sequence count."""
    total = fetch_one(
        engine,
        "SELECT COUNT(*) AS total FROM controle_processamentos WHERE ec_id = :ec_id",
        {"ec_id": ec_id},
    )
    sequencial = ((total or {}).get("total") or 0) + 1
    return f"{ec_id}_{sequencial:04d} - {now.strftime('%d/%m/%Y %H:%M:%S')}", now


def salvar(
    engine: Engine,
    ec_id: str,
    cliente_id: int,
    id_processamento: str,
    descricao: str,
    data_processamento: datetime,
) -> None:
    """Persist a new processamento record."""
    exec_sql(
        engine,
        "INSERT INTO controle_processamentos "
        "(id_processamento, cliente_id, ec_id, descricao, data_processamento) "
        "VALUES (:id_processamento, :cliente_id, :ec_id, :descricao, :data_processamento)",
        {
            "id_processamento": id_processamento,
            "cliente_id": cliente_id,
            "ec_id": ec_id,
            "descricao": descricao,
            "data_processamento": data_processamento,
        },
    )

class ProcessamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, skip: int = 0, limit: int = 20, filtros: ProcessamentoFilter = None, simple: bool = False) -> List[ProcessamentoResponse]:
        # Base query for processamentos
        query = self.db.query(LegacyProcessamento)

        if filtros:
            if filtros.cliente_id:
               query = query.filter(LegacyProcessamento.cliente_id == str(filtros.cliente_id))

        query = query.order_by(LegacyProcessamento.data_processamento.desc())
        items = query.offset(skip).limit(limit).all()

        if not items:
            return []

        # Coletar IDs para consulta em massa
        proc_ids = [item.id_processamento for item in items]

        # Consultas em massa (Bulk Queries)
        # 1. Contagem e Datas de Vendas Processadas
        stats_processadas = {}
        if not simple and proc_ids:
            from sqlalchemy import bindparam

            # Use bindparam with expanding=True for robust list handling
            query_proc = text("""
                SELECT processamentoid, COUNT(id)
                FROM vendas_processadas
                WHERE processamentoid IN :pids
                GROUP BY processamentoid
            """).bindparams(bindparam('pids', expanding=True))

            try:
                rows_proc = self.db.execute(query_proc, {"pids": list(proc_ids)}).fetchall()
                for r in rows_proc:
                    stats_processadas[r[0]] = {
                        'count': r[1],
                        'min': None,
                        'max': None
                    }
            except Exception as e:
                print(f"Error getting stats: {e}")

        # 2. Contagem de Vendas Filtradas
        stats_filtradas = {}
        if not simple and proc_ids:
            from sqlalchemy import bindparam
            query_filt = text("""
                SELECT processamentoid, COUNT(id)
                FROM vendas_filtradas
                WHERE processamentoid IN :pids
                GROUP BY processamentoid
            """).bindparams(bindparam('pids', expanding=True))

            try:
                rows_filt = self.db.execute(query_filt, {"pids": list(proc_ids)}).fetchall()
                for r in rows_filt:
                    stats_filtradas[r[0]] = r[1]
            except Exception as e:
                print(f"Error getting filtered stats: {e}")

        # [OPTIMIZATION] If simple mode, skip heavy counts entirely
        if simple:
             pass # Logic below handles empty dicts gracefully

        result = []
        for item in items:
            proc_id = item.id_processamento

            # Get cached stats
            s_proc = stats_processadas.get(proc_id, {'count': 0, 'min': None, 'max': None})
            qtd_processadas = s_proc['count']
            data_min = s_proc['min']
            data_max = s_proc['max']

            qtd_filtradas = stats_filtradas.get(proc_id, 0)

            # Mapeamento do legado para o esquema novo
            result.append(ProcessamentoResponse(
                id=item.id_processamento,
                cliente_id=int(item.cliente_id) if item.cliente_id and item.cliente_id.isdigit() else None,
                tipo_arquivo=item.adquirente or "Desconhecido",
                nome_arquivo=item.descricao or "Sem Nome",
                status="Sucesso",
                data_inicio=item.data_processamento or datetime.now(),
                data_fim=item.data_processamento,
                linhas_total=qtd_processadas + qtd_filtradas,
                linhas_processadas=qtd_processadas,
                linhas_sucesso=qtd_processadas,
                linhas_erro=qtd_filtradas,
                log_info={},
                mensagem_erro=None,

                # Extended Info
                ec_id=item.ec_id,
                qtd_processadas=qtd_processadas,
                qtd_filtradas=qtd_filtradas,
                total_linhas=qtd_processadas + qtd_filtradas,
                data_min=data_min,
                data_max=data_max
            ))

        return result

    def criar(self, dados: dict) -> ProcessamentoResponse:
        pass

    def deletar_lista(self, ids: List[str]) -> bool:
        """
        Remove múltiplos processamentos e todas as tabelas relacionadas.
        Estratégia: SELECT IDs em lotes -> DELETE por IDs.
        Mais robusto para grandes volumes e evita trava de tabela.
        """
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        if not ids:
            return False

        success_count = 0

        # Ordem de remoção (tabelas filhas primeiro)
        # Tuplas: (tabela, coluna_fk, coluna_pk)
        tables_map = [
            ("vendas_calculos", "calc_id", "id"),
            ("vendas_processadas", "processamentoid", "id"),
            ("vendas_filtradas", "processamentoid", "id"),
            ("recebiveis_processados", "processamentoid", "id"),
            ("recebiveis_filtrados", "processamentoid", "id")
        ]

        CHUNK_SIZE = 1000
        import time

        for pid in ids:
            logger.info(f"--- Iniciando deleção do Processamento: {pid} ---")
            try:
                # 1. Remover tabelas filhas EM CHUNKS (Select ID -> Delete ID)
                for table, col_fk, col_pk in tables_map:
                    total_deleted_table = 0
                    while True:
                        # Selecionar lote de IDs para deletar
                        select_sql = text(f"SELECT {col_pk} FROM {table} WHERE {col_fk} = :pid LIMIT :chunk")
                        rows = self.db.execute(select_sql, {"pid": pid, "chunk": CHUNK_SIZE}).fetchall()

                        if not rows:
                            break

                        # Extrair IDs
                        ids_to_del = [r[0] for r in rows]

                        # Deletar esses IDs especificos
                        # Usar bindparam expanding se possivel, ou criar query manualmente para garantir
                        if ids_to_del:
                            # Opcao segura usando text e bindparam
                            from sqlalchemy import bindparam
                            delete_sql = text(f"DELETE FROM {table} WHERE {col_pk} IN :del_ids").bindparams(bindparam('del_ids', expanding=True))
                            self.db.execute(delete_sql, {"del_ids": ids_to_del})
                            self.db.commit()

                            count = len(ids_to_del)
                            total_deleted_table += count
                            logger.info(f"[{pid}] Deletados {count} registros de {table}. Total nesta tabela: {total_deleted_table}")

                            # Pequena pausa para o banco respirar
                            time.sleep(0.1)
                        else:
                            break

                # 2. Remover tabela pai
                sql_pai = text("DELETE FROM controle_processamentos WHERE id_processamento = :pid")
                self.db.execute(sql_pai, {"pid": pid})
                self.db.commit()
                logger.info(f"[{pid}] DELEÇÃO CONCLUÍDA COM SUCESSO.")

                success_count += 1

            except Exception as e:
                self.db.rollback()
                logger.error(f"ERRO CRÍTICO ao deletar processamento {pid}: {e}")
                import traceback
                traceback.print_exc()
                # Tenta proximo
                continue

        return success_count > 0
