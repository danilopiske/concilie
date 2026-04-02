from typing import List, Optional

from sqlalchemy import delete, func, insert, select, or_
from sqlalchemy.orm import Session

from app.models.log import LogCorrecao
from app.models.recebiveis import Recebivel, RecebivelFiltrado
from app.models.vendas import Venda, VendaFiltrada
from app.models.vendas_calculos import VendasCalculos
from app.schemas.correcao import HistoricoItem, ResumoItem, ResumoResponse


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

    def atualizar_em_massa(self, processamento_id: str, campo: str, valores_antigos: List[str], valor_novo: str, usuario: str = "sistema") -> int:
        target_col = None
        has_na = "N/A" in valores_antigos
        v_rest = [v for v in valores_antigos if v != "N/A"]

        if campo == 'lancamento':
            # Update Recebiveis
            query = self.db.query(Recebivel).filter(
                Recebivel.processamentoid == processamento_id
            )
            conds = []
            if v_rest: conds.append(Recebivel.lancamento.in_(v_rest))
            if has_na: conds.append(Recebivel.lancamento.is_(None))
            
            if conds:
                result = query.filter(or_(*conds)).update({Recebivel.lancamento: valor_novo}, synchronize_session=False)
            else:
                result = 0

            self._registrar_log(
                processamento_id,
                'atualizacao_lancamento_recebiveis',
                ", ".join(valores_antigos),
                valor_novo,
                result,
                usuario
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

            query = self.db.query(Venda).filter(
                Venda.processamentoid == processamento_id
            )
            conds = []
            if v_rest: conds.append(target_col.in_(v_rest))
            if has_na: conds.append(target_col.is_(None))

            if conds:
                result = query.filter(or_(*conds)).update({target_col: valor_novo}, synchronize_session=False)
            else:
                result = 0

            self._registrar_log(
                processamento_id,
                f'atualizacao_{campo}',
                ", ".join(valores_antigos),
                valor_novo,
                result,
                usuario
            )

        self.db.commit()
        return result

    def mover_para_filtradas(self, processamento_id: str, campo: str, valores: List[str], usuario: str = "sistema") -> int:
        try:
            has_na = "N/A" in valores
            v_rest = [v for v in valores if v != "N/A"]

            if campo == 'lancamento':
                # 1. Copiar dados para RecebivelFiltrado usando INSERT ... SELECT
                q_select = self.db.query(
                    Recebivel.processamentoid, Recebivel.lancamento, Recebivel.valor_recebivel,
                    Recebivel.valor_liquido, Recebivel.data_pagamento, Recebivel.data_recebivel,
                    Recebivel.recebivel_id, Recebivel.adquirente, Recebivel.descricao,
                    Recebivel.banco, Recebivel.agencia, Recebivel.conta, Recebivel.cliente_id,
                    Recebivel.ec_id, Recebivel.data_processamento, Recebivel.usuario_processamento,
                    Recebivel.arquivo_origem
                ).filter(Recebivel.processamentoid == processamento_id)

                conds = []
                if v_rest: conds.append(Recebivel.lancamento.in_(v_rest))
                if has_na: conds.append(Recebivel.lancamento.is_(None))

                if conds:
                    stmt = insert(RecebivelFiltrado).from_select(
                        [
                            "processamentoid", "lancamento", "valor_recebivel", "valor_liquido",
                            "data_pagamento", "data_recebivel", "recebivel_id", "adquirente",
                            "descricao", "banco", "agencia", "conta", "cliente_id", "ec_id",
                            "data_processamento", "usuario_processamento", "arquivo_origem"
                        ],
                        q_select.filter(or_(*conds))
                    )
                    self.db.execute(stmt)

                    # 2. Remover da tabela original
                    result = self.db.query(Recebivel).filter(
                        Recebivel.processamentoid == processamento_id
                    ).filter(or_(*conds)).delete(synchronize_session=False)
                else:
                    result = 0

                self._registrar_log(
                    processamento_id,
                    'remocao_lancamento_recebiveis',
                    ", ".join(valores),
                    None,
                    result,
                    usuario
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
                q_select = self.db.query(
                    Venda.processamentoid, Venda.cliente_id, Venda.ec_id, Venda.data_venda,
                    Venda.valor_venda, Venda.valor_liquido, Venda.nsu, Venda.autorizacao,
                    Venda.bandeira, Venda.forma_pagamento, Venda.status, Venda.adquirente,
                    Venda.data_processamento
                ).filter(Venda.processamentoid == processamento_id)

                conds = []
                if v_rest: conds.append(target_col.in_(v_rest))
                if has_na: conds.append(target_col.is_(None))

                if conds:
                    stmt = insert(VendaFiltrada).from_select(
                        [
                            VendaFiltrada.processamentoid, VendaFiltrada.cliente_id, VendaFiltrada.ec_id,
                            VendaFiltrada.data_venda, VendaFiltrada.valor_venda, VendaFiltrada.valor_liquido,
                            VendaFiltrada.nsu, VendaFiltrada.autorizacao, VendaFiltrada.bandeira,
                            VendaFiltrada.forma_pagamento, VendaFiltrada.status, VendaFiltrada.adquirente,
                            VendaFiltrada.data_processamento
                        ],
                        q_select.filter(or_(*conds))
                    )
                    self.db.execute(stmt)

                    # 2. DELETE DEPENDENCIES (vendas_calculos) using subquery
                    subquery_ids = self.db.query(Venda.id).filter(
                        Venda.processamentoid == processamento_id
                    ).filter(or_(*conds)).subquery()

                    # Get the count first for logging
                    result = self.db.query(Venda).filter(
                        Venda.id.in_(select(subquery_ids))
                    ).count()

                    if result > 0:
                        # Delete from calculations
                        self.db.query(VendasCalculos).filter(
                            VendasCalculos.id_venda.in_(select(subquery_ids))
                        ).delete(synchronize_session=False)

                        # Delete from Venda
                        self.db.query(Venda).filter(
                            Venda.id.in_(select(subquery_ids))
                        ).delete(synchronize_session=False)
                    else:
                        result = 0
                else:
                    result = 0

                if result > 0:
                    self._registrar_log(
                        processamento_id,
                        f'remocao_{campo}',
                        ", ".join(valores),
                        None,
                        result,
                        usuario
                    )

                self.db.commit()
                return result

        except Exception as e:
            import traceback
            with open("debug_error_full.txt", "w") as f:
                f.write(f"Error in mover_para_filtradas: {str(e)}\n{traceback.format_exc()}")
            raise e

    def deletar_filtradas(self, processamento_id: str, campo: str, valores: List[str], usuario: str = "sistema") -> int:
        """
        Remove permanentemente itens da tabela de filtrados (VendaFiltrada ou RecebivelFiltrado).
        Ação destrutiva.
        """
        try:
            has_na = "N/A" in valores
            v_rest = [v for v in valores if v != "N/A"]

            if campo == 'lancamento':
                # Delete from RecebivelFiltrado
                query = self.db.query(RecebivelFiltrado).filter(
                    RecebivelFiltrado.processamentoid == processamento_id
                )
                conds = []
                if v_rest: conds.append(RecebivelFiltrado.lancamento.in_(v_rest))
                if has_na: conds.append(RecebivelFiltrado.lancamento.is_(None))

                if conds:
                    result = query.filter(or_(*conds)).delete(synchronize_session=False)
                else:
                    result = 0

                self._registrar_log(
                    processamento_id,
                    'exclusao_permanente_recebiveis_filtrados',
                    ", ".join(valores),
                    None,
                    result,
                    usuario
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

                query = self.db.query(VendaFiltrada).filter(
                    VendaFiltrada.processamentoid == processamento_id
                )
                conds = []
                if v_rest: conds.append(target_col.in_(v_rest))
                if has_na: conds.append(target_col.is_(None))

                if conds:
                    result = query.filter(or_(*conds)).delete(synchronize_session=False)
                else:
                    result = 0

                self._registrar_log(
                    processamento_id,
                    f'exclusao_permanente_{campo}_filtradas',
                    ", ".join(valores),
                    None,
                    result,
                    usuario
                )

                self.db.commit()
                return result

        except Exception as e:
            import traceback
            with open("debug_error_delete_filtered.txt", "w") as f:
                f.write(f"Error in deletar_filtradas: {str(e)}\n{traceback.format_exc()}")
            raise e

    def listar_resumo_filtradas(self, processamento_id: str) -> ResumoResponse:
        def get_summary(model, column, value_col):
            return self.db.query(
                column.label("valor"),
                func.count().label("quantidade"),
                func.sum(value_col).label("valor_total")
            ).filter(
                model.processamentoid == processamento_id
            ).group_by(column).all()

        formas = get_summary(VendaFiltrada, VendaFiltrada.forma_pagamento, VendaFiltrada.valor_venda)
        bandeiras = get_summary(VendaFiltrada, VendaFiltrada.bandeira, VendaFiltrada.valor_venda)
        status = get_summary(VendaFiltrada, VendaFiltrada.status, VendaFiltrada.valor_venda)
        recebiveis = get_summary(RecebivelFiltrado, RecebivelFiltrado.lancamento, RecebivelFiltrado.valor_recebivel)

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

    def atualizar_filtradas(self, processamento_id: str, campo: str, valores_antigos: List[str], valor_novo: str, usuario: str = "sistema") -> int:
        has_na = "N/A" in valores_antigos
        v_rest = [v for v in valores_antigos if v != "N/A"]

        if campo == 'lancamento':
            query = self.db.query(RecebivelFiltrado).filter(
                RecebivelFiltrado.processamentoid == processamento_id
            )
            conds = []
            if v_rest: conds.append(RecebivelFiltrado.lancamento.in_(v_rest))
            if has_na: conds.append(RecebivelFiltrado.lancamento.is_(None))

            if conds:
                result = query.filter(or_(*conds)).update({RecebivelFiltrado.lancamento: valor_novo}, synchronize_session=False)
            else:
                result = 0

            self._registrar_log(
                processamento_id,
                'atualizacao_lancamento_recebiveis_filtrados',
                ", ".join(valores_antigos),
                valor_novo,
                result,
                usuario
            )
        else:
            column_map = {
                "forma_pagamento": VendaFiltrada.forma_pagamento,
                "bandeira": VendaFiltrada.bandeira,
                "status": VendaFiltrada.status
            }
            target_col = column_map.get(campo)
            if not target_col:
                raise ValueError(f"Campo inválido: {campo}")

            query = self.db.query(VendaFiltrada).filter(
                VendaFiltrada.processamentoid == processamento_id
            )
            conds = []
            if v_rest: conds.append(target_col.in_(v_rest))
            if has_na: conds.append(target_col.is_(None))

            if conds:
                result = query.filter(or_(*conds)).update({target_col: valor_novo}, synchronize_session=False)
            else:
                result = 0

            self._registrar_log(
                processamento_id,
                f'atualizacao_{campo}_filtradas',
                ", ".join(valores_antigos),
                valor_novo,
                result,
                usuario
            )
        self.db.commit()
        return result

    def listar_filtros_taxa_bc(self, processamento_id: str) -> dict:
        """
        Retorna formas de pagamento e bandeiras únicas para o calc_id (processamento_id).
        """
        formas = self.db.query(VendasCalculos.forma_pagamento).filter(
            VendasCalculos.calc_id == processamento_id
        ).distinct().all()

        bandeiras = self.db.query(VendasCalculos.bandeira).filter(
            VendasCalculos.calc_id == processamento_id
        ).distinct().all()

        return {
            "formas": [r[0] for r in formas if r[0]],
            "bandeiras": [r[0] for r in bandeiras if r[0]]
        }

    def aplicar_taxa_bc(
        self,
        processamento_id: str,
        forma_pagamento: str,
        bandeira: str,
        data_ini: Optional[str],
        data_fim: Optional[str],
        nova_taxa: float,
        usuario: str = "sistema"
    ) -> int:
        """
        Aplica nova taxa BC e recalcula campos financeiros.
        """
        query = self.db.query(VendasCalculos).filter(VendasCalculos.calc_id == processamento_id)

        if forma_pagamento and forma_pagamento != "TODOS":
            query = query.filter(VendasCalculos.forma_pagamento == forma_pagamento)

        if bandeira and bandeira != "TODOS":
            query = query.filter(VendasCalculos.bandeira == bandeira)

        if data_ini:
            query = query.filter(VendasCalculos.data_venda >= data_ini)

        if data_fim:
            query = query.filter(VendasCalculos.data_venda <= data_fim)

        # SQLAlchemy update with expressions
        result = query.update({
            VendasCalculos.tx_calc: nova_taxa,
            VendasCalculos.desc_calc: VendasCalculos.vl_venda * nova_taxa / 100,
            VendasCalculos.vl_liq_calc: VendasCalculos.vl_venda - (VendasCalculos.vl_venda * nova_taxa / 100),
            VendasCalculos.perda: VendasCalculos.vl_liq_venda - (VendasCalculos.vl_venda - (VendasCalculos.vl_venda * nova_taxa / 100))
        }, synchronize_session=False)

        self._registrar_log(
            processamento_id,
            'taxa_bc',
            None,
            f"Taxa: {nova_taxa}% | FP: {forma_pagamento} | B: {bandeira}",
            result,
            usuario
        )

        self.db.commit()
        return result
