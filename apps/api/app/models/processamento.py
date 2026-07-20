from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class Processamento(Base):
    __tablename__ = "processamentos"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, nullable=True)
    tipo_arquivo = Column(String(50), nullable=False) # 'Venda', 'Recebivel'
    nome_arquivo = Column(String(255), nullable=False)

    status = Column(String(50), default="Pendente") # Pendente, Em Andamento, Sucesso, Erro, Cancelado

    data_inicio = Column(DateTime(timezone=True), server_default=func.now())
    data_fim = Column(DateTime(timezone=True), nullable=True)

    linhas_total = Column(Integer, default=0)
    linhas_processadas = Column(Integer, default=0)
    linhas_sucesso = Column(Integer, default=0)
    linhas_erro = Column(Integer, default=0)

    # Log detalhado ou mensagem de erro principal
    log_info = Column(JSON, nullable=True)
    mensagem_erro = Column(Text, nullable=True)

    criado_por = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Processamento(id={self.id}, arquivo='{self.nome_arquivo}', status='{self.status}')>"
