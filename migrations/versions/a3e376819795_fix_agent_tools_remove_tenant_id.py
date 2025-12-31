"""fix agent_tools remove tenant_id

Revision ID: a3e376819795
Revises: af8b15d310a2
Create Date: 2025-12-30 16:55:41.371764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3e376819795'
down_revision: Union[str, Sequence[str], None] = 'af8b15d310a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_agent_tools_tenant_id", table_name="agent_tools")
    op.drop_table("agent_tools")

    op.create_table(
        "agent_tools",
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("agent_id", "tool_id"),
        sa.UniqueConstraint("agent_id", "tool_id", name="uq_agent_tools_agent_tool"),
    )



def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration")

