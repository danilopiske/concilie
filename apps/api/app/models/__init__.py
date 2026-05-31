"""
Models Package
"""

from app.models.abusividade_task import AbusividadeTask
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.alerta_config import AlertaConfig
from app.models.audit_log import AuditLog
from app.models.bandeira import BandeiraCliente, BandeiraDisponivel
from app.models.base import Base
from app.models.calculo_task import CalculoTask
from app.models.cliente import EC, Cliente, Contato, DadoBancario, ECCliente, Endereco
from app.models.contestacao import Contestacao
from app.models.contexto import Contexto
from app.models.extrato_cliente import ExtratoCliente
from app.models.import_task import ImportTask
from app.models.log import LogCorrecao
from app.models.notificacao import Notificacao
from app.models.recebiveis import Recebivel, RecebivelFiltrado
from app.models.modelo_relatorio import ModeloRelatorio
from app.models.relatorio_tag import RelatorioTag
from app.models.relatorio_task import RelatorioTask
from app.models.taxa import Taxa
from app.models.taxa_contratada import TaxaContratada
from app.models.termo import TermoFiltravel

## Removido: formas de pagamento
from app.models.usuario import Usuario
from app.models.usuario_permissao import UsuarioPermissao
from app.models.usuario_contexto import UsuarioContexto
from app.models.usuario_cliente import UsuarioCliente
from app.models.vendas import Venda, VendaFiltrada

__all__ = [
    "Base",
    "AbusividadeTask",
    "AuditLog",
    "Contestacao",
    "Cliente",
    "Endereco",
    "Contato",
    "DadoBancario",
    "EC",
    "ECCliente",
    "Contexto",
    "BandeiraDisponivel",
    "BandeiraCliente",
    "TermoFiltravel",
    "Taxa",
    "TaxaContratada",
    "Venda",
    "VendaFiltrada",
    "Recebivel",
    "RecebivelFiltrado",
    "LogCorrecao",
    "Notificacao",
    "ImportTask",
    "CalculoTask",
    "RelatorioTask",
    "ModeloRelatorio",
    "RelatorioTag",
    "ExtratoCliente",
    "AlertaConfig",
    "Usuario",
    "UsuarioPermissao",
    "UsuarioContexto",
    "UsuarioCliente",
]
