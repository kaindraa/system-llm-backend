"""Add learning profile fields to user table

Revision ID: j5k6l7m8n9o0
Revises: i0j1k2l3m4n5
Create Date: 2025-11-08 16:05:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j5k6l7m8n9o0'
down_revision = 'i0j1k2l3m4n5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add learning profile fields to user table
    op.add_column('user', sa.Column('task', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('persona', sa.Text(), nullable=True))
    op.add_column('user', sa.Column('mission_objective', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove the columns in reverse order
    op.drop_column('user', 'mission_objective')
    op.drop_column('user', 'persona')
    op.drop_column('user', 'task')
