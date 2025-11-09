"""Add prompt_analysis to chat_config table

Revision ID: a1b2c3d4e5f6
Revises: j5k6l7m8n9o0
Create Date: 2025-11-09 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'j5k6l7m8n9o0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add prompt_analysis column to chat_config table
    op.add_column('chat_config', sa.Column('prompt_analysis', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove prompt_analysis column from chat_config table
    op.drop_column('chat_config', 'prompt_analysis')
