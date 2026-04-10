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
            if filtros.data_ini:
                try:
                    data_limite = datetime.fromisoformat(filtros.data_ini)
                    query = query.filter(LegacyProcessamento.data_processamento >= data_limite)
                except ValueError:
                    pass

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
        Remove múltiplos processamentos e todas as tabelas relacionadas de forma otimizada.
        Usa DELETE direto para performance máxima.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not ids:
            return False

        success_count = 0

        # Tabelas filhas (ordem de dependência)
        tables_map = [
            ("vendas_calculos", "calc_id"),
            ("vendas_processadas", "processamentoid"),
            ("vendas_filtradas", "processamentoid"),
            ("recebiveis_processados", "processamentoid"),
            ("recebiveis_filtrados", "processamentoid")
        ]

        for pid in ids:
            logger.info(f"--- Iniciando deleção rápida do Processamento: {pid} ---")
            try:
                # 1. Remover registros das tabelas filhas (Bulk Delete)
                for table, col_fk in tables_map:
                    # DELETE direto é MUITO mais rápido que SELECT + DELETE em loop
                    delete_sql = text(f"DELETE FROM {table} WHERE {col_fk} = :pid")
                    res = self.db.execute(delete_sql, {"pid": pid})
                    logger.info(f"[{pid}] Removidos registros de {table}. Linhas afetadas: {res.rowcount}")

                # 2. Remover tabela pai
                sql_pai = text("DELETE FROM controle_processamentos WHERE id_processamento = :pid")
                self.db.execute(sql_pai, {"pid": pid})
                
                # Commit único por processamento para garantir integridade e velocidade
                self.db.commit()
                logger.info(f"[{pid}] DELEÇÃO CONCLUÍDA COM SUCESSO.")
                success_count += 1

            except Exception as e:
                self.db.rollback()
                logger.error(f"ERRO ao deletar processamento {pid}: {e}")
                # Tenta proximo
                continue

        return success_count > 0
