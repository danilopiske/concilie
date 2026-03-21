from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.processamento import Processamento
from app.models.taxa_contratada import TaxaContratada
from app.schemas.taxa_contratada import (
    ComparacaoResponse,
    ComparativoItem,
    ComparativoResponse,
    DesvioTaxa,
    HistoricoDesvioItem,
    HistoricoDesviosResponse,
    TaxaContratadaCreate,
    TaxaContratadaUpdate,
)


def _calcular_status(desvio: float) -> str:
    if desvio <= 2.0:
        return "ok"
    if desvio <= 10.0:
        return "atencao"
    return "abusivo"


def _comparar(cliente_id: int, processamento_id: str, db: Session) -> List[DesvioTaxa]:
    """Compara taxas contratadas vs cobradas para um processamento."""
    # Data do processamento para verificar vigência
    proc = db.query(Processamento).filter(Processamento.id == int(processamento_id)).first()
    data_proc: Optional[date] = proc.data_inicio.date() if proc and proc.data_inicio else date.today()

    # Taxas cobradas agrupadas por bandeira+forma_pagamento
    sql = text("""
        SELECT
            bandeira,
            forma_pagamento,
            AVG(CAST(tx_venda AS FLOAT))  AS taxa_media,
            SUM(CAST(vl_venda  AS FLOAT))  AS valor_total,
            COUNT(*)                        AS quantidade
        FROM vendas_calculos
        WHERE calc_id = :calc_id
          AND tx_venda IS NOT NULL
          AND bandeira IS NOT NULL
          AND forma_pagamento IS NOT NULL
        GROUP BY bandeira, forma_pagamento
    """)
    rows = db.execute(sql, {"calc_id": str(processamento_id)}).fetchall()

    desvios: List[DesvioTaxa] = []
    for row in rows:
        bandeira, forma_pag, taxa_media, valor_total, quantidade = row
        taxa_media = float(taxa_media or 0)
        valor_total = float(valor_total or 0)

        # Buscar taxa contratada vigente
        taxa_obj = (
            db.query(TaxaContratada)
            .filter(
                TaxaContratada.cliente_id == cliente_id,
                TaxaContratada.bandeira == bandeira,
                TaxaContratada.modalidade == forma_pag,
                TaxaContratada.vigencia_inicio <= data_proc,
                (TaxaContratada.vigencia_fim.is_(None))
                | (TaxaContratada.vigencia_fim >= data_proc),
            )
            .first()
        )
        if taxa_obj is None:
            continue  # sem referência contratual — pular

        contratada = taxa_obj.taxa_contratada
        desvio = ((taxa_media - contratada) / contratada * 100) if contratada > 0 else 0.0
        excesso = valor_total * (desvio / 100) if desvio > 0 else 0.0

        desvios.append(
            DesvioTaxa(
                bandeira=bandeira,
                modalidade=forma_pag,
                taxa_contratada=round(contratada, 4),
                taxa_media_cobrada=round(taxa_media, 4),
                desvio_percentual=round(desvio, 2),
                valor_total_transacoes=round(valor_total, 2),
                valor_excesso_estimado=round(excesso, 2),
                status=_calcular_status(desvio),
                quantidade_transacoes=int(quantidade),
            )
        )

    return desvios


# ── CRUD ─────────────────────────────────────────────────────────────────────

def listar(cliente_id: int, vigente: Optional[bool], db: Session) -> list:
    q = db.query(TaxaContratada).filter(TaxaContratada.cliente_id == cliente_id)
    if vigente is True:
        q = q.filter(TaxaContratada.vigencia_fim.is_(None))
    return q.order_by(TaxaContratada.bandeira, TaxaContratada.modalidade).all()


def criar(cliente_id: int, data: TaxaContratadaCreate, db: Session) -> TaxaContratada:
    # Encerrar vigência anterior para mesma bandeira+modalidade
    anterior = (
        db.query(TaxaContratada)
        .filter(
            TaxaContratada.cliente_id == cliente_id,
            TaxaContratada.bandeira == data.bandeira,
            TaxaContratada.modalidade == data.modalidade,
            TaxaContratada.vigencia_fim.is_(None),
        )
        .first()
    )
    if anterior:
        anterior.vigencia_fim = data.vigencia_inicio - timedelta(days=1)

    obj = TaxaContratada(cliente_id=cliente_id, **data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def atualizar(id: int, cliente_id: int, data: TaxaContratadaUpdate, db: Session) -> Optional[TaxaContratada]:
    obj = db.query(TaxaContratada).filter(
        TaxaContratada.id == id,
        TaxaContratada.cliente_id == cliente_id,
    ).first()
    if not obj:
        return None
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def remover(id: int, cliente_id: int, db: Session) -> bool:
    obj = db.query(TaxaContratada).filter(
        TaxaContratada.id == id,
        TaxaContratada.cliente_id == cliente_id,
    ).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


# ── Comparação ────────────────────────────────────────────────────────────────

def comparar_contratado_vs_cobrado(
    cliente_id: int, processamento_id: str, db: Session
) -> ComparacaoResponse:
    desvios = _comparar(cliente_id, processamento_id, db)
    excesso_total = round(sum(d.valor_excesso_estimado for d in desvios), 2)
    return ComparacaoResponse(
        cliente_id=cliente_id,
        processamento_id=processamento_id,
        desvios=desvios,
        valor_excesso_total=excesso_total,
    )


def comparativo_geral(cliente_id: int, db: Session) -> ComparativoResponse:
    """Compara taxas contratadas vs média cobrada em todos os processamentos do cliente."""
    sql = text("""
        SELECT
            vc.bandeira,
            vc.forma_pagamento,
            AVG(CAST(vc.tx_venda AS FLOAT)) AS taxa_media,
            COUNT(*)                         AS quantidade
        FROM vendas_calculos vc
        JOIN processamentos p ON p.id = CAST(vc.calc_id AS INTEGER)
        WHERE p.cliente_id = :cliente_id
          AND vc.tx_venda IS NOT NULL
          AND vc.bandeira IS NOT NULL
          AND vc.forma_pagamento IS NOT NULL
        GROUP BY vc.bandeira, vc.forma_pagamento
    """)
    rows = db.execute(sql, {"cliente_id": cliente_id}).fetchall()

    itens: List[ComparativoItem] = []
    for row in rows:
        bandeira, forma_pag, taxa_media, quantidade = row
        taxa_media = float(taxa_media or 0)

        taxa_obj = (
            db.query(TaxaContratada)
            .filter(
                TaxaContratada.cliente_id == cliente_id,
                TaxaContratada.bandeira == bandeira,
                TaxaContratada.modalidade == forma_pag,
                TaxaContratada.vigencia_fim.is_(None),
            )
            .first()
        )
        if taxa_obj is None:
            continue

        contratada = taxa_obj.taxa_contratada
        diferenca = round(taxa_media - contratada, 4)

        if diferenca > 0.5:
            status = "critico"
        elif diferenca > 0:
            status = "divergente"
        else:
            status = "ok"

        itens.append(
            ComparativoItem(
                bandeira=bandeira,
                modalidade=forma_pag,
                taxa_contratada=round(contratada, 4),
                taxa_media_cobrada=round(taxa_media, 4),
                diferenca=diferenca,
                status=status,
                quantidade_transacoes=int(quantidade),
            )
        )

    itens.sort(key=lambda x: (x.status == "ok", x.status == "divergente"))
    return ComparativoResponse(
        cliente_id=cliente_id,
        itens=itens,
        total_critico=sum(1 for i in itens if i.status == "critico"),
        total_divergente=sum(1 for i in itens if i.status == "divergente"),
        total_ok=sum(1 for i in itens if i.status == "ok"),
    )


def historico_desvios(cliente_id: int, db: Session) -> HistoricoDesviosResponse:
    procs = (
        db.query(Processamento)
        .filter(Processamento.cliente_id == cliente_id)
        .order_by(Processamento.data_inicio.desc())
        .limit(12)
        .all()
    )
    historico = []
    for proc in procs:
        desvios = _comparar(cliente_id, str(proc.id), db)
        if not desvios:
            continue
        excesso_total = round(sum(d.valor_excesso_estimado for d in desvios), 2)
        historico.append(
            HistoricoDesvioItem(
                processamento_id=str(proc.id),
                data_processamento=proc.data_inicio,
                desvios=desvios,
                valor_excesso_total=excesso_total,
            )
        )
    return HistoricoDesviosResponse(cliente_id=cliente_id, historico=historico)
