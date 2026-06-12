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
    # Idempotent at the SQL level: avoids aborting the transaction on Postgres
    # when prompt_analysis was already added by revision a1b2c3d4e5f6.
    op.execute("ALTER TABLE chat_config ADD COLUMN IF NOT EXISTS prompt_analysis TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE chat_config DROP COLUMN IF EXISTS prompt_analysis")
