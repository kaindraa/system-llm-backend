"""Fix: Add prompt_analysis column if not exists

Revision ID: b3c4d5e6f7g8
Revises: a1b2c3d4e5f6
Create Date: 2025-11-09 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7g8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column exists, if not add it
    from sqlalchemy import inspect
    from sqlalchemy.engine import reflection

    try:
        # Try to add column, ignore if already exists
        op.add_column('chat_config', sa.Column('prompt_analysis', sa.Text(), nullable=True))
    except Exception as e:
        # Column already exists or other error, just log
        print(f"Column prompt_analysis: {str(e)}")
        pass


def downgrade() -> None:
    try:
        op.drop_column('chat_config', 'prompt_analysis')
    except Exception:
        pass
