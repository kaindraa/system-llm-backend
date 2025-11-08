"""Create rag_config table for RAG system settings.

Revision ID: g2c3d4e5f6a7
Revises: f1a2b3c4d5e6
Create Date: 2025-11-08 02:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'g2c3d4e5f6a7'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create rag_config table with default values."""
    op.create_table(
        'rag_config',
        sa.Column('id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('default_top_k', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_top_k', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('similarity_threshold', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('tool_calling_max_iterations', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('tool_calling_enabled', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('include_rag_instruction', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Insert default config row (singleton pattern)
    op.execute(
        sa.text(
            "INSERT INTO rag_config (id, default_top_k, max_top_k, similarity_threshold, "
            "tool_calling_max_iterations, tool_calling_enabled, include_rag_instruction) "
            "VALUES (1, 5, 10, 0.7, 10, 1, 1)"
        )
    )


def downgrade() -> None:
    """Drop rag_config table."""
    op.drop_table('rag_config')
