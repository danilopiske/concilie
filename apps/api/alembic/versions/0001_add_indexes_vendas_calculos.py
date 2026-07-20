"""add indexes vendas_calculos e relatorio_tasks

Revision ID: 0001
Revises: None
Create Date: 2026-03-21

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # vendas_calculos — queries de abusividade filtram por calc_id + data_venda
    op.create_index(
        "ix_vendas_calculos_calc_data",
        "vendas_calculos",
        ["calc_id", "data_venda"],
    )
    # vendas_calculos — queries de comparativo filtram por bandeira + forma_pagamento
    op.create_index(
        "ix_vendas_calculos_bandeira_forma",
        "vendas_calculos",
        ["bandeira", "forma_pagamento"],
    )
    # relatorio_tasks — listagem de relatórios por status e data
    op.create_index(
        "ix_relatorio_tasks_status_created",
        "relatorio_tasks",
        ["status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_relatorio_tasks_status_created", table_name="relatorio_tasks")
    op.drop_index("ix_vendas_calculos_bandeira_forma", table_name="vendas_calculos")
    op.drop_index("ix_vendas_calculos_calc_data", table_name="vendas_calculos")
