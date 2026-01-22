"""
Cliente Model
"""

from sqlalchemy import Column, Integer, String, Text
from app.models.base import Base


class Cliente(Base):
    __tablename__ = "clientes"

    cliente_id = Column(Integer, primary_key=True)
    nome_fantasia = Column(String(255))
    razao_social = Column(String(255))
    cnpj = Column(String(20))

    def __repr__(self):
        return f"<Cliente(id={self.cliente_id}, nome={self.nome_fantasia})>"


class Endereco(Base):
    __tablename__ = "enderecos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=False, index=True)
    logradouro = Column(String(255))
    numero = Column(String(20))
    complemento = Column(String(100))
    bairro = Column(String(100))
    cidade = Column(String(100))
    uf_id = Column(String(2))


class Contato(Base):
    __tablename__ = "contatos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=False, index=True)
    telefone1 = Column(String(20))
    telefone2 = Column(String(20))
    telefone3 = Column(String(20))
    email1 = Column(String(100))
    email2 = Column(String(100))


class DadoBancario(Base):
    __tablename__ = "dados_bancarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, nullable=False, index=True)
    banco = Column(String(100))
    agencia = Column(String(20))
    conta = Column(String(20))


class EC(Base):
    __tablename__ = "ecs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ec_id = Column(String(20), nullable=False, unique=True)
    descricao = Column(String(255))


class ECCliente(Base):
    __tablename__ = "ecs_cliente"

    cliente_id = Column(Integer, primary_key=True)
    ec_id = Column(String(100), primary_key=True)
