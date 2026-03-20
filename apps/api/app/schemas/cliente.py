"""
Cliente Schemas
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EnderecoBase(BaseModel):
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf_id: Optional[str] = Field(None, max_length=2)


class ContatoBase(BaseModel):
    telefone1: Optional[str] = None
    telefone2: Optional[str] = None
    telefone3: Optional[str] = None
    email1: Optional[str] = None
    email2: Optional[str] = None


class DadoBancarioBase(BaseModel):
    banco: Optional[str] = None
    agencia: Optional[str] = None
    conta: Optional[str] = None


class ClienteBase(BaseModel):
    cliente_id: int
    nome_fantasia: str
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None


class ClienteCreate(BaseModel):
    cliente_id: Optional[int] = None
    nome_fantasia: str
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    endereco: Optional[EnderecoBase] = None
    contatos: Optional[ContatoBase] = None
    bancario: Optional[DadoBancarioBase] = None
    ecs: List[str] = []


class ClienteUpdate(BaseModel):
    nome_fantasia: Optional[str] = None
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    endereco: Optional[EnderecoBase] = None
    contatos: Optional[ContatoBase] = None
    bancario: Optional[DadoBancarioBase] = None
    ecs: Optional[List[str]] = None


class ClienteResponse(BaseModel):
    cliente_id: int
    nome_fantasia: Optional[str]
    razao_social: Optional[str]
    cnpj: Optional[str]
    endereco: Optional[EnderecoBase] = None
    contatos: Optional[ContatoBase] = None
    bancario: Optional[DadoBancarioBase] = None
    ecs: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class ECResponse(BaseModel):
    ec_id: str
    descricao: Optional[str]

    model_config = ConfigDict(from_attributes=True)
