"""
Resumo executivo por cliente — consolida importações, cálculos, relatórios e notificações.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db

router = APIRouter()


@router.get("/{cliente_id}/resumo")
def resumo_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.calculo_task import CalculoTask
    from app.models.cliente import Cliente
    from app.models.import_task import ImportTask
    from app.models.notificacao import Notificacao
    from app.models.relatorio_task import RelatorioTask

    # Verificar cliente existe
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Últimas 5 importações filtradas por cliente (ImportTask tem cliente_id)
    import_tasks = (
        db.query(ImportTask)
        .filter(ImportTask.cliente_id == cliente_id)
        .order_by(ImportTask.created_at.desc())
        .limit(5)
        .all()
    )

    # Últimas 5 tarefas de cálculo (sem cliente_id direto — globais)
    calculo_tasks = (
        db.query(CalculoTask)
        .order_by(CalculoTask.created_at.desc())
        .limit(5)
        .all()
    )

    # Últimas 5 tarefas de relatório (sem cliente_id direto — globais)
    relatorio_tasks = (
        db.query(RelatorioTask)
        .order_by(RelatorioTask.created_at.desc())
        .limit(5)
        .all()
    )

    # Notificações não lidas do usuário atual
    notificacoes_nao_lidas = (
        db.query(Notificacao)
        .filter(
            Notificacao.lida.is_(False),
            (Notificacao.usuario_id == current_user.id) | (Notificacao.usuario_id.is_(None)),
        )
        .count()
    )

    def fmt_import(t: ImportTask) -> dict:
        return {
            "id": t.id,
            "status": t.status,
            "progress": t.progress,
            "tipo_arquivo": t.tipo_arquivo,
            "contexto": t.contexto,
            "usuario": t.usuario,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }

    def fmt_calculo(t: CalculoTask) -> dict:
        return {
            "id": t.id,
            "status": t.status,
            "progress": t.progress,
            "processamento_id": t.processamento_id,
            "tipo_taxa": t.tipo_taxa,
            "usuario": t.usuario,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }

    def fmt_relatorio(t: RelatorioTask) -> dict:
        return {
            "id": t.id,
            "status": t.status,
            "progress": t.progress,
            "processamento_id": t.processamento_id,
            "tipo_relatorio": t.tipo_relatorio,
            "usuario": t.usuario,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }

    return {
        "cliente_id": cliente_id,
        "nome": cliente.nome_fantasia or cliente.razao_social or str(cliente_id),
        "cnpj": cliente.cnpj,
        "notificacoes_nao_lidas": notificacoes_nao_lidas,
        "import_tasks_recentes": [fmt_import(t) for t in import_tasks],
        "calculo_tasks_recentes": [fmt_calculo(t) for t in calculo_tasks],
        "relatorio_tasks_recentes": [fmt_relatorio(t) for t in relatorio_tasks],
    }
