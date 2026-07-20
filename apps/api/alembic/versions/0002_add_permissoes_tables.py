"""add usuario_permissoes, usuario_contextos, usuario_clientes

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-22

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuario_permissoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("perfil", sa.Enum("admin", "operador", "visualizador", name="perfil_enum"), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("usuario_id"),
    )
    op.create_index("ix_usuario_permissoes_usuario_id", "usuario_permissoes", ["usuario_id"])

    op.create_table(
        "usuario_contextos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("contexto_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contexto_id"], ["contextos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usuario_contextos_usuario_id", "usuario_contextos", ["usuario_id"])

    op.create_table(
        "usuario_clientes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.cliente_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usuario_clientes_usuario_id", "usuario_clientes", ["usuario_id"])

    # Usuários existentes recebem perfil 'admin' para não perder acesso
    op.execute(
        "INSERT INTO usuario_permissoes (usuario_id, perfil, criado_em, atualizado_em) "
        "SELECT id, 'admin', NOW(), NOW() FROM usuarios"
    )


def downgrade() -> None:
    op.drop_index("ix_usuario_clientes_usuario_id", table_name="usuario_clientes")
    op.drop_table("usuario_clientes")
    op.drop_index("ix_usuario_contextos_usuario_id", table_name="usuario_contextos")
    op.drop_table("usuario_contextos")
    op.drop_index("ix_usuario_permissoes_usuario_id", table_name="usuario_permissoes")
    op.drop_table("usuario_permissoes")
    op.execute("DROP TYPE IF EXISTS perfil_enum")
