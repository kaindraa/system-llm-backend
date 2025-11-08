"""Add prompt configuration fields to chat_session table

Revision ID: h8i9j0k1l2m3
Revises: g2c3d4e5f6a7
Create Date: 2025-11-08 09:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'h8i9j0k1l2m3'
down_revision = 'g2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 4 new TEXT columns to chat_session table
    op.add_column('chat_session', sa.Column('prompt_general', sa.Text(), nullable=True))
    op.add_column('chat_session', sa.Column('task', sa.Text(), nullable=True))
    op.add_column('chat_session', sa.Column('persona', sa.Text(), nullable=True))
    op.add_column('chat_session', sa.Column('mission_objective', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove the columns in reverse order
    op.drop_column('chat_session', 'mission_objective')
    op.drop_column('chat_session', 'persona')
    op.drop_column('chat_session', 'task')
    op.drop_column('chat_session', 'prompt_general')
