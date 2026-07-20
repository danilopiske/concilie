"""
Métricas de efetividade das contestações.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter()


@router.get("")
def metricas_contestacoes(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.cliente import Cliente
    from app.models.contestacao import Contestacao

    # Contagem por status
    por_status = (
        db.query(Contestacao.status, func.count(Contestacao.id).label("total"))
        .group_by(Contestacao.status)
        .all()
    )
    status_map = {row.status: row.total for row in por_status}

    total_enviadas = sum(
        v
        for k, v in status_map.items()
        if k in ("enviada", "deferida", "indeferida", "em_analise")
    )
    total_deferidas = status_map.get("deferida", 0)
    taxa_sucesso = (
        round(total_deferidas / total_enviadas * 100, 1) if total_enviadas > 0 else 0.0
    )

    # Valor total recuperado (deferidas)
    valor_recuperado = (
        db.query(func.sum(Contestacao.valor_excesso_total))
        .filter(Contestacao.status == "deferida")
        .scalar()
        or 0.0
    )

    # Valor total em disputa (enviadas + em análise)
    valor_disputa = (
        db.query(func.sum(Contestacao.valor_excesso_total))
        .filter(Contestacao.status.in_(["enviada", "em_analise"]))
        .scalar()
        or 0.0
    )

    # Top 5 clientes por valor recuperado
    top_clientes_raw = (
        db.query(
            Contestacao.cliente_id,
            func.sum(Contestacao.valor_excesso_total).label("total_recuperado"),
            func.count(Contestacao.id).label("total_deferidas"),
        )
        .filter(Contestacao.status == "deferida")
        .group_by(Contestacao.cliente_id)
        .order_by(func.sum(Contestacao.valor_excesso_total).desc())
        .limit(5)
        .all()
    )

    top_clientes = []
    for row in top_clientes_raw:
        cliente = db.get(Cliente, row.cliente_id) if row.cliente_id else None
        nome = ""
        if cliente:
            nome = (
                getattr(cliente, "nome_fantasia", None)
                or getattr(cliente, "razao_social", None)
                or str(row.cliente_id)
            )
        top_clientes.append(
            {
                "cliente_id": row.cliente_id,
                "nome": nome,
                "total_recuperado_rs": round(float(row.total_recuperado or 0), 2),
                "total_deferidas": row.total_deferidas,
            }
        )

    return {
        "por_status": status_map,
        "total_contestacoes": sum(status_map.values()),
        "total_enviadas": total_enviadas,
        "total_deferidas": total_deferidas,
        "taxa_sucesso_pct": taxa_sucesso,
        "valor_recuperado_rs": round(float(valor_recuperado), 2),
        "valor_em_disputa_rs": round(float(valor_disputa), 2),
        "top_clientes_recuperacao": top_clientes,
    }
