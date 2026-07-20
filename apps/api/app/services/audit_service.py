"""
Serviço de auditoria — registra e lista ações críticas do sistema.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def registrar(
        db: Session,
        acao: str,
        usuario_id: Optional[int] = None,
        usuario: Optional[str] = None,
        detalhes: Optional[str] = None,
        ip: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            usuario_id=usuario_id,
            usuario=usuario,
            acao=acao,
            detalhes=detalhes,
            ip=ip,
        )
        db.add(log)
        db.commit()
        return log

    @staticmethod
    def listar(
        db: Session,
        usuario_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLog]:
        query = db.query(AuditLog)
        if usuario_id is not None:
            query = query.filter(AuditLog.usuario_id == usuario_id)
        return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
