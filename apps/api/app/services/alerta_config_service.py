from typing import Optional

from sqlalchemy.orm import Session

from app.models.alerta_config import AlertaConfig


class AlertaConfigService:
    @staticmethod
    def criar(
        db: Session,
        tipo_alerta: str,
        threshold_valor: float,
        usuario_id: Optional[int] = None,
        descricao: Optional[str] = None,
    ) -> AlertaConfig:
        config = AlertaConfig(
            usuario_id=usuario_id,
            tipo_alerta=tipo_alerta,
            threshold_valor=threshold_valor,
            descricao=descricao,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def listar(db: Session, usuario_id: Optional[int] = None) -> list[AlertaConfig]:
        query = db.query(AlertaConfig)
        if usuario_id is not None:
            query = query.filter(
                (AlertaConfig.usuario_id == usuario_id)
                | (AlertaConfig.usuario_id.is_(None))
            )
        return query.filter(AlertaConfig.ativo == True).all()  # noqa: E712

    @staticmethod
    def listar_todos(db: Session, usuario_id: Optional[int] = None) -> list[AlertaConfig]:
        """Lista todos os registros (ativos e inativos) do usuário."""
        query = db.query(AlertaConfig)
        if usuario_id is not None:
            query = query.filter(
                (AlertaConfig.usuario_id == usuario_id)
                | (AlertaConfig.usuario_id.is_(None))
            )
        return query.all()

    @staticmethod
    def atualizar(
        db: Session,
        config_id: str,
        threshold_valor: Optional[float] = None,
        ativo: Optional[bool] = None,
        descricao: Optional[str] = None,
    ) -> Optional[AlertaConfig]:
        config = db.get(AlertaConfig, config_id)
        if not config:
            return None
        if threshold_valor is not None:
            config.threshold_valor = threshold_valor
        if ativo is not None:
            config.ativo = ativo
        if descricao is not None:
            config.descricao = descricao
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def remover(db: Session, config_id: str) -> bool:
        config = db.get(AlertaConfig, config_id)
        if config:
            db.delete(config)
            db.commit()
            return True
        return False

    @staticmethod
    def verificar_threshold(
        db: Session,
        tipo_alerta: str,
        valor_atual: float,
        usuario_id: Optional[int] = None,
    ) -> Optional[AlertaConfig]:
        """Retorna a config violada se valor_atual superar o threshold."""
        configs = AlertaConfigService.listar(db, usuario_id=usuario_id)
        for c in configs:
            if c.tipo_alerta == tipo_alerta and valor_atual >= c.threshold_valor:
                return c
        return None
