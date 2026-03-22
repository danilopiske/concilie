"""add FK indexes: import_tasks.cliente_id, usuario_clientes.cliente_id, usuario_contextos.contexto_id

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-22

"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_import_tasks_cliente_id", "import_tasks", ["cliente_id"])
    op.create_index("ix_usuario_clientes_cliente_id", "usuario_clientes", ["cliente_id"])
    op.create_index("ix_usuario_contextos_contexto_id", "usuario_contextos", ["contexto_id"])


def downgrade() -> None:
    op.drop_index("ix_usuario_contextos_contexto_id", table_name="usuario_contextos")
    op.drop_index("ix_usuario_clientes_cliente_id", table_name="usuario_clientes")
    op.drop_index("ix_import_tasks_cliente_id", table_name="import_tasks")
