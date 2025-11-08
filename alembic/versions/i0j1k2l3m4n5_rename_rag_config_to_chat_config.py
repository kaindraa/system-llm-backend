"""Rename rag_config to chat_config and add prompt_general

Revision ID: i0j1k2l3m4n5
Revises: h8i9j0k1l2m3
Create Date: 2025-11-08 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i0j1k2l3m4n5'
down_revision = 'h8i9j0k1l2m3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename table from rag_config to chat_config
    op.rename_table('rag_config', 'chat_config')

    # Add prompt_general column
    op.add_column('chat_config', sa.Column('prompt_general', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove prompt_general column
    op.drop_column('chat_config', 'prompt_general')

    # Rename table back to rag_config
    op.rename_table('chat_config', 'rag_config')
