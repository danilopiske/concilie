from typing import Optional

from sqlalchemy.orm import Session

from app.models.notificacao import Notificacao


class NotificacaoService:
    @staticmethod
    def criar(
        db: Session,
        tipo: str,
        titulo: str,
        mensagem: str,
        usuario_id: Optional[int] = None,
        link: Optional[str] = None,
    ) -> Notificacao:
        notif = Notificacao(
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo,
            mensagem=mensagem,
            link=link,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def listar(
        db: Session,
        usuario_id: Optional[int] = None,
        lida: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Notificacao]:
        query = db.query(Notificacao)
        if usuario_id is not None:
            query = query.filter(
                (Notificacao.usuario_id == usuario_id) | (Notificacao.usuario_id.is_(None))
            )
        if lida is not None:
            query = query.filter(Notificacao.lida == lida)
        return query.order_by(Notificacao.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def contar_nao_lidas(db: Session, usuario_id: Optional[int] = None) -> int:
        query = db.query(Notificacao).filter(Notificacao.lida == False)  # noqa: E712
        if usuario_id is not None:
            query = query.filter(
                (Notificacao.usuario_id == usuario_id) | (Notificacao.usuario_id.is_(None))
            )
        return query.count()

    @staticmethod
    def marcar_lida(db: Session, notificacao_id: str) -> Optional[Notificacao]:
        notif = db.get(Notificacao, notificacao_id)
        if notif:
            notif.lida = True
            db.commit()
            db.refresh(notif)
        return notif

    @staticmethod
    def marcar_todas_lidas(db: Session, usuario_id: Optional[int] = None) -> None:
        query = db.query(Notificacao).filter(Notificacao.lida == False)  # noqa: E712
        if usuario_id is not None:
            query = query.filter(
                (Notificacao.usuario_id == usuario_id) | (Notificacao.usuario_id.is_(None))
            )
        query.update({"lida": True}, synchronize_session=False)
        db.commit()

    @staticmethod
    def remover(db: Session, notificacao_id: str) -> bool:
        notif = db.get(Notificacao, notificacao_id)
        if notif:
            db.delete(notif)
            db.commit()
            return True
        return False
