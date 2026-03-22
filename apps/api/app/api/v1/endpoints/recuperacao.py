"""
Ranking de recuperação financeira — clientes ordenados por valor contestável.
PUBLIC — intencional: relatório de ranking para uso interno sem restrição de perfil.
"""

import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import String, cast, func
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter()


def _build_ranking(limit: int, db: Session) -> dict:
    from app.models.cliente import Cliente, ECCliente
    from app.models.vendas_calculos import VendasCalculos

    # VendasCalculos.ec_id (BigInteger) → cast to String → ECCliente.ec_id (String)
    resultados = (
        db.query(
            ECCliente.cliente_id,
            func.sum(VendasCalculos.perda).label("total_perda"),
            func.count(VendasCalculos.id).label("count_transacoes"),
        )
        .join(ECCliente, cast(VendasCalculos.ec_id, String) == ECCliente.ec_id)
        .filter(VendasCalculos.perda > 0)
        .group_by(ECCliente.cliente_id)
        .order_by(func.sum(VendasCalculos.perda).desc())
        .limit(limit)
        .all()
    )

    ranking = []
    for row in resultados:
        cliente_id = row.cliente_id
        if not cliente_id:
            continue
        cliente = db.get(Cliente, int(cliente_id))
        nome = ""
        if cliente:
            nome = (
                getattr(cliente, "nome_fantasia", None)
                or getattr(cliente, "razao_social", None)
                or str(cliente_id)
            )
        ranking.append(
            {
                "posicao": len(ranking) + 1,
                "cliente_id": cliente_id,
                "nome": nome,
                "total_perda_rs": round(float(row.total_perda or 0), 2),
                "count_transacoes": row.count_transacoes,
                "media_perda_rs": round(
                    float(row.total_perda or 0) / max(row.count_transacoes, 1), 2
                ),
            }
        )

    total_geral = sum(r["total_perda_rs"] for r in ranking)

    return {
        "total_clientes_com_perda": len(ranking),
        "total_recuperavel_rs": round(total_geral, 2),
        "ranking": ranking,
    }


def _build_ranking_fallback(limit: int, db: Session) -> dict:
    """Fallback: agrupa por ec_id quando ECCliente não tem dados."""
    from app.models.vendas_calculos import VendasCalculos

    resultados = (
        db.query(
            VendasCalculos.ec_id,
            func.sum(VendasCalculos.perda).label("total_perda"),
            func.count(VendasCalculos.id).label("count_transacoes"),
        )
        .filter(VendasCalculos.perda > 0)
        .group_by(VendasCalculos.ec_id)
        .order_by(func.sum(VendasCalculos.perda).desc())
        .limit(limit)
        .all()
    )

    ranking = [
        {
            "posicao": i + 1,
            "cliente_id": row.ec_id,
            "nome": f"EC {row.ec_id}",
            "total_perda_rs": round(float(row.total_perda or 0), 2),
            "count_transacoes": row.count_transacoes,
            "media_perda_rs": round(
                float(row.total_perda or 0) / max(row.count_transacoes, 1), 2
            ),
        }
        for i, row in enumerate(resultados)
    ]
    total_geral = sum(r["total_perda_rs"] for r in ranking)
    return {
        "total_clientes_com_perda": len(ranking),
        "total_recuperavel_rs": round(total_geral, 2),
        "ranking": ranking,
    }


@router.get("/ranking")
def ranking_recuperacao(
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Retorna clientes rankeados pelo total de perdas financeiras contestáveis.

    Estratégia de join:
      VendasCalculos.ec_id → ECCliente.ec_id → ECCliente.cliente_id → Cliente
    """
    try:
        resultado = _build_ranking(limit=limit, db=db)
        if resultado["total_clientes_com_perda"] > 0:
            return resultado
        # Se não achou via join, tenta fallback por ec_id
        return _build_ranking_fallback(limit=limit, db=db)
    except Exception:
        try:
            return _build_ranking_fallback(limit=limit, db=db)
        except Exception:
            return {
                "total_clientes_com_perda": 0,
                "total_recuperavel_rs": 0.0,
                "ranking": [],
            }


@router.get("/ranking/exportar-csv")
def exportar_ranking_csv(
    db: Session = Depends(get_db),
):
    """Exporta o ranking de recuperação em formato CSV."""
    dados = ranking_recuperacao(limit=100, db=db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Posição",
            "Cliente ID",
            "Nome",
            "Total Perda (R$)",
            "Qtd Transações",
            "Média Perda/Transação (R$)",
        ]
    )
    for r in dados["ranking"]:
        writer.writerow(
            [
                r["posicao"],
                r["cliente_id"],
                r["nome"],
                r["total_perda_rs"],
                r["count_transacoes"],
                r["media_perda_rs"],
            ]
        )
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=ranking_recuperacao.csv"
        },
    )
