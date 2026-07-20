import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.contestacao import Contestacao
from app.models.processamento import Processamento
from app.schemas.contestacao import ContestacaoStatusUpdate
from app.services.taxa_contratada_service import comparar_contratado_vs_cobrado

# Diretório de saída das cartas geradas
CONTESTACOES_DIR = Path("contestacoes")
CONTESTACOES_DIR.mkdir(exist_ok=True)

# Diretório dos templates Jinja2
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "relatorios"


def _render_template(context: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATES_DIR)), autoescape=False)
    tmpl = env.get_template("template_contestacao.html")
    return tmpl.render(**context)


def gerar_contestacao(cliente_id: int, processamento_id: int, db: Session) -> Contestacao:
    """Gera carta de contestação com base nos desvios do processamento."""
    cliente = db.query(Cliente).filter(Cliente.cliente_id == cliente_id).first()
    if not cliente:
        raise ValueError(f"Cliente {cliente_id} não encontrado")

    proc = db.query(Processamento).filter(Processamento.id == processamento_id).first()

    # Buscar desvios
    comparacao = comparar_contratado_vs_cobrado(cliente_id, str(processamento_id), db)
    desvios = comparacao.desvios

    # Calcular datas do período
    periodo_inicio = proc.data_inicio.date() if proc and proc.data_inicio else datetime.utcnow().date()
    periodo_fim = proc.data_fim.date() if proc and proc.data_fim else datetime.utcnow().date()

    adquirente = desvios[0].bandeira if desvios else "Adquirente"
    valor_total = comparacao.valor_excesso_total

    contestacao_id = str(uuid.uuid4())
    data_geracao = datetime.utcnow().strftime("%d/%m/%Y")

    ctx = {
        "contestacao_id": contestacao_id,
        "cliente_nome": cliente.nome_fantasia or cliente.razao_social or f"Cliente {cliente_id}",
        "cliente_cnpj": cliente.cnpj or "—",
        "adquirente": adquirente,
        "periodo_inicio": periodo_inicio.strftime("%d/%m/%Y"),
        "periodo_fim": periodo_fim.strftime("%d/%m/%Y"),
        "valor_total": valor_total,
        "desvios": desvios,
        "data_geracao": data_geracao,
    }

    html = _render_template(ctx)

    # Persistir HTML no disco
    html_path = CONTESTACOES_DIR / f"{contestacao_id}.html"
    html_path.write_text(html, encoding="utf-8")

    contestacao = Contestacao(
        id=contestacao_id,
        cliente_id=cliente_id,
        processamento_id=processamento_id,
        adquirente=adquirente,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        valor_excesso_total=valor_total,
        status="rascunho",
        html_carta=html,
        created_by="sistema",
    )
    db.add(contestacao)
    db.commit()
    db.refresh(contestacao)
    return contestacao


def listar(cliente_id: Optional[int], status: Optional[str], db: Session) -> List[Contestacao]:
    q = db.query(Contestacao)
    if cliente_id is not None:
        q = q.filter(Contestacao.cliente_id == cliente_id)
    if status:
        q = q.filter(Contestacao.status == status)
    return q.order_by(Contestacao.created_at.desc()).all()


def obter(contestacao_id: str, db: Session) -> Optional[Contestacao]:
    return db.query(Contestacao).filter(Contestacao.id == contestacao_id).first()


def atualizar_status(contestacao_id: str, body: ContestacaoStatusUpdate, db: Session) -> Optional[Contestacao]:
    obj = db.query(Contestacao).filter(Contestacao.id == contestacao_id).first()
    if not obj:
        return None
    obj.status = body.status
    obj.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj


def save_edit(contestacao_id: str, html_content: str, db: Session) -> Optional[str]:
    obj = db.query(Contestacao).filter(Contestacao.id == contestacao_id).first()
    if not obj:
        return None
    obj.html_carta = html_content
    obj.updated_at = datetime.utcnow()
    db.commit()
    # Persistir no disco também
    html_path = CONTESTACOES_DIR / f"{contestacao_id}.html"
    html_path.write_text(html_content, encoding="utf-8")
    return str(html_path)


def get_html_path(contestacao_id: str) -> Optional[Path]:
    p = CONTESTACOES_DIR / f"{contestacao_id}.html"
    return p if p.exists() else None


def remover(contestacao_id: str, db: Session) -> bool:
    obj = db.query(Contestacao).filter(Contestacao.id == contestacao_id).first()
    if not obj:
        return False
    if obj.status != "rascunho":
        raise ValueError("Apenas contestações em rascunho podem ser removidas")
    html_path = CONTESTACOES_DIR / f"{contestacao_id}.html"
    if html_path.exists():
        html_path.unlink()
    db.delete(obj)
    db.commit()
    return True
