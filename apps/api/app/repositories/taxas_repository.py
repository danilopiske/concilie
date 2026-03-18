"""
Repository de Taxas — sem dependências de conf.funcoesbd.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.db_helpers import exec_sql, fetch_all, normalize_compare
from app.schemas.taxa import TaxaCreate, TaxaUpdate, TaxaCopiarRequest

logger = logging.getLogger(__name__)


class TaxasRepository:
    """Repository para operações de taxas"""

    def __init__(self, db: Session):
        self.db = db
        self.engine = db.get_bind()

    def listar_por_ec(self, ec: str, contexto: str = "padrao") -> List[Dict[str, Any]]:
        sql = (
            "SELECT id, ec, bandeira, forma_pagamento, parcelado, "
            "parcelas_ini, parcelas_fim, data_ini, data_fim, taxa, contexto "
            "FROM taxas "
            f"WHERE ec = :ec AND {normalize_compare(self.engine, 'contexto', 'contexto')} "
            "ORDER BY bandeira, forma_pagamento, parcelas_ini"
        )
        return fetch_all(self.engine, sql, {"ec": ec, "contexto": contexto})

    def criar(self, taxa: TaxaCreate) -> bool:
        taxa_dict = taxa.model_dump()
        taxa_dict["taxa"] = float(taxa_dict["taxa"])
        taxa_dict["contexto"] = taxa.contexto
        sql = (
            "INSERT INTO taxas "
            "(ec, bandeira, forma_pagamento, parcelado, parcelas_ini, parcelas_fim, "
            "data_ini, data_fim, taxa, contexto) "
            "VALUES (:ec, :bandeira, :forma_pagamento, :parcelado, :parcelas_ini, "
            ":parcelas_fim, :data_ini, :data_fim, :taxa, :contexto)"
        )
        try:
            exec_sql(self.engine, sql, taxa_dict)
            return True
        except Exception as e:
            logger.error("Erro ao inserir taxa: %s", e)
            return False

    def atualizar(self, taxa_id: int, taxa: TaxaUpdate) -> bool:
        taxa_dict = taxa.model_dump(exclude_unset=True)
        if "taxa" in taxa_dict and taxa_dict["taxa"] is not None:
            taxa_dict["taxa"] = float(taxa_dict["taxa"])
        taxa_dict["id"] = taxa_id
        sql = (
            "UPDATE taxas SET ec=:ec, bandeira=:bandeira, forma_pagamento=:forma_pagamento, "
            "parcelado=:parcelado, parcelas_ini=:parcelas_ini, parcelas_fim=:parcelas_fim, "
            "data_ini=:data_ini, data_fim=:data_fim, taxa=:taxa, contexto=:contexto "
            "WHERE id=:id"
        )
        try:
            exec_sql(self.engine, sql, taxa_dict)
            return True
        except Exception as e:
            logger.error("Erro ao atualizar taxa: %s", e)
            return False

    def deletar(self, taxa_id: int) -> bool:
        try:
            exec_sql(self.engine, "DELETE FROM taxas WHERE id = :id", {"id": taxa_id})
            return True
        except Exception as e:
            logger.error("Erro ao excluir taxa: %s", e)
            return False

    def copiar(self, request: TaxaCopiarRequest) -> Dict[str, Any]:
        resultado: Dict[str, Any] = {"copiadas": 0, "removidas": 0, "erros": []}
        taxas_origem = self.listar_por_ec(request.ec_origem, request.contexto)
        if not taxas_origem:
            resultado["erros"].append(f"Nenhuma taxa encontrada para o EC {request.ec_origem}")
            return resultado

        for ec_dest in request.ecs_destino:
            if ec_dest == request.ec_origem:
                resultado["erros"].append(f"EC destino {ec_dest} igual ao de origem")
                continue
            try:
                if request.sobrescrever:
                    exec_sql(
                        self.engine,
                        f"DELETE FROM taxas WHERE ec = :ec AND {normalize_compare(self.engine, 'contexto', 'contexto')}",
                        {"ec": ec_dest, "contexto": request.contexto},
                    )
                    resultado["removidas"] += 1

                for taxa in taxas_origem:
                    nova = {k: v for k, v in taxa.items() if k != "id"}
                    nova["ec"] = ec_dest
                    nova["contexto"] = request.contexto
                    sql = (
                        "INSERT INTO taxas "
                        "(ec, bandeira, forma_pagamento, parcelado, parcelas_ini, parcelas_fim, "
                        "data_ini, data_fim, taxa, contexto) "
                        "VALUES (:ec, :bandeira, :forma_pagamento, :parcelado, :parcelas_ini, "
                        ":parcelas_fim, :data_ini, :data_fim, :taxa, :contexto)"
                    )
                    exec_sql(self.engine, sql, nova)
                    resultado["copiadas"] += 1
            except Exception as e:
                logger.error("Erro ao copiar taxas para %s: %s", ec_dest, e)
                resultado["erros"].append(str(e))

        return resultado
