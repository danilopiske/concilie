"""
Cliente Repository
"""

from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.cliente import EC, Cliente, Contato, DadoBancario, ECCliente, Endereco
from app.repositories.base import BaseRepository


class ClienteRepository(BaseRepository[Cliente]):
    def __init__(self, db: Session):
        super().__init__(Cliente, db)

    def get_by_id(self, cliente_id: int) -> Optional[Cliente]:
        """Get cliente by cliente_id"""
        return self.db.query(Cliente).filter(Cliente.cliente_id == cliente_id).first()

    def list_all(self) -> List[Dict[str, Any]]:
        """List all clientes"""
        clientes = self.db.query(Cliente).order_by(Cliente.nome_fantasia).all()
        return [
            {
                "cliente_id": c.cliente_id,
                "nome_fantasia": c.nome_fantasia,
                "razao_social": c.razao_social,
                "cnpj": c.cnpj,
            }
            for c in clientes
        ]

    def get_detalhes(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed cliente information"""
        cliente = self.get_by_id(cliente_id)
        if not cliente:
            return None

        endereco = (
            self.db.query(Endereco).filter(Endereco.cliente_id == cliente_id).first()
        )

        contato = (
            self.db.query(Contato).filter(Contato.cliente_id == cliente_id).first()
        )

        bancario = (
            self.db.query(DadoBancario)
            .filter(DadoBancario.cliente_id == cliente_id)
            .first()
        )

        ecs = (
            self.db.query(ECCliente.ec_id)
            .filter(ECCliente.cliente_id == cliente_id)
            .all()
        )

        return {
            "cliente_id": cliente.cliente_id,
            "nome_fantasia": cliente.nome_fantasia,
            "razao_social": cliente.razao_social,
            "cnpj": cliente.cnpj,
            "endereco": (
                {
                    "logradouro": endereco.logradouro if endereco else None,
                    "numero": endereco.numero if endereco else None,
                    "complemento": endereco.complemento if endereco else None,
                    "bairro": endereco.bairro if endereco else None,
                    "cidade": endereco.cidade if endereco else None,
                    "uf_id": endereco.uf_id if endereco else None,
                }
                if endereco
                else None
            ),
            "contatos": (
                {
                    "telefone1": contato.telefone1 if contato else None,
                    "telefone2": contato.telefone2 if contato else None,
                    "telefone3": contato.telefone3 if contato else None,
                    "email1": contato.email1 if contato else None,
                    "email2": contato.email2 if contato else None,
                }
                if contato
                else None
            ),
            "bancario": (
                {
                    "banco": bancario.banco if bancario else None,
                    "agencia": bancario.agencia if bancario else None,
                    "conta": bancario.conta if bancario else None,
                }
                if bancario
                else None
            ),
            "ecs": [ec[0] for ec in ecs] if ecs else [],
        }

    def salvar_cliente(self, dados: Dict[str, Any], is_update: bool = False):
        """Save cliente with all related data"""
        cliente_id = dados.get("cliente_id")

        # Cliente main data
        cliente_data = {
            "cliente_id": cliente_id,
            "nome_fantasia": dados.get("nome_fantasia"),
            "razao_social": dados.get("razao_social"),
            "cnpj": dados.get("cnpj"),
        }
        # Remove None keys to allow auto-increment/defaults
        cliente_data = {k: v for k, v in cliente_data.items() if v is not None}

        if is_update:
            self.db.query(Cliente).filter(Cliente.cliente_id == cliente_id).update(
                cliente_data
            )
        else:
            # Fix for missing AUTO_INCREMENT in DB: generate ID manually if not provided
            if not cliente_data.get("cliente_id"):
                from sqlalchemy import func
                max_id = self.db.query(func.max(Cliente.cliente_id)).scalar()
                next_id = (max_id or 0) + 1
                cliente_data["cliente_id"] = next_id
                # Update the ID for subsequent related data (endereco, contatos, etc)
                cliente_id = next_id

            cliente = Cliente(**cliente_data)
            self.db.add(cliente)
            self.db.flush() # Flush to ensure ID is reserved/used in transaction

        # Endereco - UPSERT (cria se não existe, atualiza se existe)
        if dados.get("endereco"):
            endereco_data = {"cliente_id": cliente_id, **dados["endereco"]}

            # Verificar se já existe
            endereco_existente = (
                self.db.query(Endereco)
                .filter(Endereco.cliente_id == cliente_id)
                .first()
            )

            if endereco_existente:
                # Atualizar
                self.db.query(Endereco).filter(
                    Endereco.cliente_id == cliente_id
                ).update(endereco_data)
            else:
                # Criar novo
                endereco = Endereco(**endereco_data)
                self.db.add(endereco)

        # Contatos - UPSERT
        if dados.get("contatos"):
            contato_data = {"cliente_id": cliente_id, **dados["contatos"]}

            # Verificar se já existe
            contato_existente = (
                self.db.query(Contato).filter(Contato.cliente_id == cliente_id).first()
            )

            if contato_existente:
                # Atualizar
                self.db.query(Contato).filter(Contato.cliente_id == cliente_id).update(
                    contato_data
                )
            else:
                # Criar novo
                contato = Contato(**contato_data)
                self.db.add(contato)

        # Dados Bancarios - UPSERT
        if dados.get("bancario"):
            bancario_data = {"cliente_id": cliente_id, **dados["bancario"]}

            # Verificar se já existe
            bancario_existente = (
                self.db.query(DadoBancario)
                .filter(DadoBancario.cliente_id == cliente_id)
                .first()
            )

            if bancario_existente:
                # Atualizar
                self.db.query(DadoBancario).filter(
                    DadoBancario.cliente_id == cliente_id
                ).update(bancario_data)
            else:
                # Criar novo
                bancario = DadoBancario(**bancario_data)
                self.db.add(bancario)

        # ECs - processar sempre no update para permitir remoção de todos
        if is_update or dados.get("ecs"):
            # Get current ECs
            ecs_atuais = set(
                [
                    ec[0]
                    for ec in self.db.query(ECCliente.ec_id)
                    .filter(ECCliente.cliente_id == cliente_id)
                    .all()
                ]
            )
            ecs_desejados = set(dados.get("ecs", []))

            # Add new ECs
            for ec in ecs_desejados - ecs_atuais:
                # Ensure EC exists in ecs table
                ec_obj = self.db.query(EC).filter(EC.ec_id == ec).first()
                if not ec_obj:
                    ec_obj = EC(ec_id=ec)
                    self.db.add(ec_obj)

                # Add to ecs_cliente
                ec_cliente = ECCliente(cliente_id=cliente_id, ec_id=ec)
                self.db.add(ec_cliente)

            # Remove deleted ECs
            for ec in ecs_atuais - ecs_desejados:
                self.db.query(ECCliente).filter(
                    ECCliente.cliente_id == cliente_id, ECCliente.ec_id == ec
                ).delete()

        self.db.commit()
        return cliente_id

    def deletar_cliente(self, cliente_id: int):
        """Delete cliente and all related data"""
        # Get ECs
        ecs = [
            ec[0]
            for ec in self.db.query(ECCliente.ec_id)
            .filter(ECCliente.cliente_id == cliente_id)
            .all()
        ]

        if ecs:
            ecs_str = "', '".join(ecs)
            ecs_list = f"'{ecs_str}'"

            # Delete related data
            self.db.execute(
                text(f"DELETE FROM termos_filtraveis WHERE ec IN ({ecs_list})")
            )
            self.db.execute(text(f"DELETE FROM taxas WHERE ec IN ({ecs_list})"))
            self.db.execute(
                text(f"DELETE FROM bandeiras_cliente WHERE ec IN ({ecs_list})")
            )

        # Delete ECs
        self.db.query(ECCliente).filter(ECCliente.cliente_id == cliente_id).delete()

        # Delete other data
        self.db.query(Endereco).filter(Endereco.cliente_id == cliente_id).delete()
        self.db.query(Contato).filter(Contato.cliente_id == cliente_id).delete()
        self.db.query(DadoBancario).filter(
            DadoBancario.cliente_id == cliente_id
        ).delete()

        # Delete cliente
        self.db.query(Cliente).filter(Cliente.cliente_id == cliente_id).delete()

        self.db.commit()

    def get_ecs_por_cliente(self, cliente_id: int) -> List[str]:
        """Get ECs for a cliente"""
        ecs = (
            self.db.query(ECCliente.ec_id)
            .filter(ECCliente.cliente_id == cliente_id)
            .order_by(ECCliente.ec_id)
            .all()
        )
        return [ec[0] for ec in ecs]
