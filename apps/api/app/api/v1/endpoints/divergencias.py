"""
Relatório de divergências (taxas contratadas vs cobradas) por cliente.

Lógica: TaxaContratada tem cliente_id direto. Taxa tem ec (código EC).
A relação cliente → EC é via tabela ECCliente (cliente_id ↔ ec_id).
Comparação por bandeira + modalidade/forma_pagamento.
"""

import csv
import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cliente import Cliente, ECCliente
from app.models.taxa import Taxa
from app.models.taxa_contratada import TaxaContratada

router = APIRouter()


def _calcular_divergencias(cliente_id: int, db: Session) -> dict:
    """Lógica central: compara taxas contratadas vs cobradas do cliente."""
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Taxas contratadas do cliente (vigentes e históricas)
    contratadas = (
        db.query(TaxaContratada)
        .filter(TaxaContratada.cliente_id == cliente_id)
        .all()
    )

    # ECs vinculados ao cliente para buscar taxas cobradas
    ecs_cliente = (
        db.query(ECCliente.ec_id)
        .filter(ECCliente.cliente_id == cliente_id)
        .all()
    )
    ec_ids = [row.ec_id for row in ecs_cliente]

    # Taxas cobradas via EC do cliente
    cobradas: list[Taxa] = []
    if ec_ids:
        cobradas = (
            db.query(Taxa)
            .filter(Taxa.ec.in_(ec_ids))
            .all()
        )

    # Montar índice de taxas cobradas por (bandeira, forma_pagamento)
    # forma_pagamento na Taxa mapeia para modalidade em TaxaContratada
    cobradas_idx: dict[tuple[str, str], list[float]] = {}
    for cob in cobradas:
        bandeira = (cob.bandeira or "").strip().lower()
        forma = (cob.forma_pagamento or "").strip().lower()
        key = (bandeira, forma)
        cobradas_idx.setdefault(key, [])
        cobradas_idx[key].append(float(cob.taxa))

    # Calcular divergências por taxa contratada
    divergencias = []
    for cont in contratadas:
        bandeira_key = (cont.bandeira or "").strip().lower()
        modalidade_key = (cont.modalidade or "").strip().lower()
        key = (bandeira_key, modalidade_key)

        taxas_cobradas_match = cobradas_idx.get(key, [])
        if not taxas_cobradas_match:
            continue

        # Usar a maior taxa cobrada como referência para divergência
        max_cobrada = max(taxas_cobradas_match)
        taxa_ref = float(cont.taxa_contratada)

        if max_cobrada > taxa_ref:
            diferenca = round(max_cobrada - taxa_ref, 4)
            divergencias.append(
                {
                    "bandeira": cont.bandeira,
                    "modalidade": cont.modalidade,
                    "taxa_contratada": taxa_ref,
                    "taxa_cobrada": round(max_cobrada, 4),
                    "diferenca_pct": diferenca,
                    "status": "divergente",
                }
            )

    return {
        "cliente_id": cliente_id,
        "nome": cliente.nome_fantasia or cliente.razao_social or str(cliente_id),
        "total_divergencias": len(divergencias),
        "nota": (
            "Nenhum EC vinculado ao cliente — sem taxas cobradas para comparar."
            if not ec_ids
            else None
        ),
        "divergencias": divergencias,
    }


@router.get("/{cliente_id}")
def divergencias_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Compara taxas contratadas vs taxas cobradas para o cliente.
    Retorna lista de divergências encontradas.
    """
    return _calcular_divergencias(cliente_id, db)


@router.get("/{cliente_id}/exportar-csv")
def exportar_divergencias_csv(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Exporta divergências do cliente como CSV."""
    dados = _calcular_divergencias(cliente_id, db)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["Bandeira", "Modalidade", "Taxa Contratada (%)", "Taxa Cobrada (%)", "Diferença (%)", "Status"]
    )
    for d in dados["divergencias"]:
        writer.writerow(
            [
                d["bandeira"],
                d["modalidade"],
                d["taxa_contratada"],
                d["taxa_cobrada"],
                d["diferenca_pct"],
                d["status"],
            ]
        )

    output.seek(0)
    filename = f"divergencias_cliente_{cliente_id}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
