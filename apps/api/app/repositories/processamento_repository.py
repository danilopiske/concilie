from sqlalchemy.orm import Session
from app.models.legacy_processamento import LegacyProcessamento
from app.schemas.processamento import ProcessamentoResponse, ProcessamentoFilter
from typing import List, Optional
from datetime import datetime
from sqlalchemy import text

class ProcessamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, skip: int = 0, limit: int = 100, filtros: ProcessamentoFilter = None, simple: bool = False) -> List[ProcessamentoResponse]:
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
                SELECT processamentoid, COUNT(*), MIN(data_processamento), MAX(data_processamento)
                FROM vendas_processadas 
                WHERE processamentoid IN :pids
                GROUP BY processamentoid
            """).bindparams(bindparam('pids', expanding=True))
            
            try:
                rows_proc = self.db.execute(query_proc, {"pids": list(proc_ids)}).fetchall()
                for r in rows_proc:
                    stats_processadas[r[0]] = {
                        'count': r[1],
                        'min': r[2],
                        'max': r[3]
                    }
            except Exception as e:
                print(f"Error getting stats: {e}")

        # 2. Contagem de Vendas Filtradas
        stats_filtradas = {}
        if not simple and proc_ids:
            from sqlalchemy import bindparam
            query_filt = text("""
                SELECT processamentoid, COUNT(*)
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
