from sqlalchemy.orm import Session
from sqlalchemy import func, insert, delete, select
from app.models.vendas import Venda, VendaFiltrada
from app.models.recebiveis import Recebivel, RecebivelFiltrado
from app.models.vendas_calculos import VendasCalculos
from app.models.log import LogCorrecao
from app.schemas.correcao import ResumoResponse, ResumoItem, HistoricoItem
from typing import List, Optional

class CorrecaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar_resumo(self, processamento_id: str) -> ResumoResponse:
        
        def get_summary(model, column, value_col):
            return self.db.query(
                column.label("valor"),
                func.count().label("quantidade"),
                func.sum(value_col).label("valor_total")
            ).filter(
                model.processamentoid == processamento_id
            ).group_by(column).all()

        formas = get_summary(Venda, Venda.forma_pagamento, Venda.valor_venda)
        bandeiras = get_summary(Venda, Venda.bandeira, Venda.valor_venda)
        status = get_summary(Venda, Venda.status, Venda.valor_venda)
        
        recebiveis = get_summary(Recebivel, Recebivel.lancamento, Recebivel.valor_recebivel)

        def map_items(rows):
            return [
                ResumoItem(
                    valor=str(row.valor) if row.valor else "N/A",
                    quantidade=row.quantidade,
                    valor_total=float(row.valor_total or 0)
                ) for row in rows
            ]

        return ResumoResponse(
            formas_pagamento=map_items(formas),
            bandeiras=map_items(bandeiras),
            status=map_items(status),
            recebiveis=map_items(recebiveis)
        )

    def listar_historico(self, processamento_id: str) -> List[HistoricoItem]:
        logs = self.db.query(LogCorrecao).filter(
            LogCorrecao.processamentoid == processamento_id
        ).order_by(LogCorrecao.data_correcao.desc()).all()
        
        return [
            HistoricoItem(
                id=log.id,
                data_correcao=log.data_correcao,
                usuario=log.usuario,
                tipo_correcao=log.tipo_correcao,
                valor_antigo=log.valor_antigo,
                valor_novo=log.valor_novo,
                linhas_afetadas=log.linhas_afetadas
            ) for log in logs
        ]

    def _registrar_log(self, processamento_id: str, tipo: str, valor_antigo: Optional[str], valor_novo: Optional[str], linhas: int, usuario: str = "sistema"):
        log = LogCorrecao(
            processamentoid=processamento_id,
            tipo_correcao=tipo,
            valor_antigo=str(valor_antigo) if valor_antigo else None,
            valor_novo=str(valor_novo) if valor_novo else None,
            linhas_afetadas=linhas,
            usuario=usuario,
            data_correcao=func.now()
        )
        self.db.add(log)

    def atualizar_em_massa(self, processamento_id: str, campo: str, valor_antigo: str, valor_novo: str) -> int:
        if campo == 'lancamento':
            # Update Recebiveis
            result = self.db.query(Recebivel).filter(
                Recebivel.processamentoid == processamento_id,
                Recebivel.lancamento == valor_antigo
            ).update({Recebivel.lancamento: valor_novo}, synchronize_session=False)
            
            self._registrar_log(
                processamento_id, 
                'atualizacao_lancamento_recebiveis', 
                valor_antigo, 
                valor_novo, 
                result
            )
        else:
            # Update Vendas
            column_map = {
                "forma_pagamento": Venda.forma_pagamento,
                "bandeira": Venda.bandeira,
                "status": Venda.status
            }
            
            target_col = column_map.get(campo)
            if not target_col:
                raise ValueError(f"Campo inválido: {campo}")

            result = self.db.query(Venda).filter(
                Venda.processamentoid == processamento_id,
                target_col == valor_antigo
            ).update({target_col: valor_novo}, synchronize_session=False)
            
            self._registrar_log(
                processamento_id, 
                f'atualizacao_{campo}', 
                valor_antigo, 
                valor_novo, 
                result
            )
        
        self.db.commit()
        return result

    def mover_para_filtradas(self, processamento_id: str, campo: str, valor: str) -> int:
        try:
            if campo == 'lancamento':
                # 1. Copiar dados para RecebivelFiltrado usando INSERT ... SELECT
                stmt = insert(RecebivelFiltrado).from_select(
                    [
                        "processamentoid", "lancamento", "valor_recebivel", "valor_liquido",
                        "data_pagamento", "data_recebivel", "recebivel_id", "adquirente", 
                        "descricao", "banco", "agencia", "conta", "cliente_id", "ec_id",
                        "data_processamento", "usuario_processamento", "arquivo_origem"
                    ],
                    self.db.query(
                        Recebivel.processamentoid, Recebivel.lancamento, Recebivel.valor_recebivel,
                        Recebivel.valor_liquido, Recebivel.data_pagamento, Recebivel.data_recebivel,
                        Recebivel.recebivel_id, Recebivel.adquirente, Recebivel.descricao,
                        Recebivel.banco, Recebivel.agencia, Recebivel.conta, Recebivel.cliente_id,
                        Recebivel.ec_id, Recebivel.data_processamento, Recebivel.usuario_processamento,
                        Recebivel.arquivo_origem
                    ).filter(
                        Recebivel.processamentoid == processamento_id,
                        Recebivel.lancamento == valor
                    )
                )
                self.db.execute(stmt)

                # 2. Remover da tabela original
                result = self.db.query(Recebivel).filter(
                    Recebivel.processamentoid == processamento_id,
                    Recebivel.lancamento == valor
                ).delete(synchronize_session=False)

                self._registrar_log(
                    processamento_id, 
                    'remocao_lancamento_recebiveis', 
                    valor, 
                    None, 
                    result
                )
                
                self.db.commit()
                return result

            else:
                # Mapeamento de colunas para Vendas
                column_map = {
                    "forma_pagamento": Venda.forma_pagamento,
                    "bandeira": Venda.bandeira,
                    "status": Venda.status
                }
                
                target_col = column_map.get(campo)
                if not target_col:
                    raise ValueError(f"Campo inválido: {campo}")

                # 1. INSERT ... SELECT para Vendas
                stmt = insert(VendaFiltrada).from_select(
                    [
                        VendaFiltrada.processamentoid, VendaFiltrada.cliente_id, VendaFiltrada.ec_id, 
                        VendaFiltrada.data_venda, VendaFiltrada.valor_venda, VendaFiltrada.valor_liquido, 
                        VendaFiltrada.nsu, VendaFiltrada.autorizacao, VendaFiltrada.bandeira, 
                        VendaFiltrada.forma_pagamento, VendaFiltrada.status, VendaFiltrada.adquirente, 
                        VendaFiltrada.data_processamento
                    ],
                    self.db.query(
                        Venda.processamentoid, Venda.cliente_id, Venda.ec_id, Venda.data_venda,
                        Venda.valor_venda, Venda.valor_liquido, Venda.nsu, Venda.autorizacao,
                        Venda.bandeira, Venda.forma_pagamento, Venda.status, Venda.adquirente,
                        Venda.data_processamento
                    ).filter(
                        Venda.processamentoid == processamento_id,
                        target_col == valor
                    )
                )
                self.db.execute(stmt)

                # 2. DELETE DEPENDENCIES (vendas_calculos)
                # Optimize: Get IDs first to avoid subquery locking issues in MySQL
                ids_to_delete = [
                    r[0] for r in self.db.query(Venda.id).filter(
                        Venda.processamentoid == processamento_id,
                        target_col == valor
                    ).all()
                ]

                if ids_to_delete:
                    # Delete in chunks if too many? (Assuming typical volume is manageable)
                    self.db.query(VendasCalculos).filter(
                        VendasCalculos.id_venda.in_(ids_to_delete)
                    ).delete(synchronize_session=False)

                    # 3. Remover da tabela original using same IDs for consistency/speed
                    result = self.db.query(Venda).filter(
                        Venda.id.in_(ids_to_delete)
                    ).delete(synchronize_session=False)

                    self._registrar_log(
                        processamento_id, 
                        f'remocao_{campo}', 
                        valor, 
                        None, 
                        result
                    )
                else:
                    result = 0
            
                self.db.commit()
                return result

        except Exception as e:
            import traceback
            with open("debug_error_full.txt", "w") as f:
                f.write(f"Error in mover_para_filtradas: {str(e)}\n{traceback.format_exc()}")
            raise e

    def deletar_filtradas(self, processamento_id: str, campo: str, valor: str) -> int:
        """
        Remove permanentemente itens da tabela de filtrados (VendaFiltrada ou RecebivelFiltrado).
        Ação destrutiva.
        """
        try:
            if campo == 'lancamento':
                # Delete from RecebivelFiltrado
                result = self.db.query(RecebivelFiltrado).filter(
                    RecebivelFiltrado.processamentoid == processamento_id,
                    RecebivelFiltrado.lancamento == valor
                ).delete(synchronize_session=False)

                self._registrar_log(
                    processamento_id, 
                    'exclusao_permanente_recebiveis_filtrados', 
                    valor, 
                    None, 
                    result
                )
                
                self.db.commit()
                return result

            else:
                # Delete from VendaFiltrada
                column_map = {
                    "forma_pagamento": VendaFiltrada.forma_pagamento,
                    "bandeira": VendaFiltrada.bandeira,
                    "status": VendaFiltrada.status
                }
                
                target_col = column_map.get(campo)
                if not target_col:
                    raise ValueError(f"Campo inválido: {campo}")

                result = self.db.query(VendaFiltrada).filter(
                    VendaFiltrada.processamentoid == processamento_id,
                    target_col == valor
                ).delete(synchronize_session=False)

                self._registrar_log(
                    processamento_id, 
                    f'exclusao_permanente_{campo}_filtradas', 
                    valor, 
                    None, 
                    result
                )
            
                self.db.commit()
                return result

        except Exception as e:
            import traceback
            with open("debug_error_delete_filtered.txt", "w") as f:
                f.write(f"Error in deletar_filtradas: {str(e)}\n{traceback.format_exc()}")
            raise e
