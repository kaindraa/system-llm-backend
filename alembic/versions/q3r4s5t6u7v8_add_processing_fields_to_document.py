"""add processing fields to document

Revision ID: q3r4s5t6u7v8
Revises: 20251230_073000
Create Date: 2026-06-13 16:00:00.000000

Adds fields used by the in-app document ingestion pipeline + monitoring
dashboard:
  - status value CANCELLED (added to the documentstatus enum)
  - current_stage : fine-grained stage within PROCESSING (parsing/chunking/...)
  - last_error    : error message of the last failed ingestion attempt
  - retry_count   : number of times ingestion has been retried
  - cancel_requested : cooperative-cancel flag checked between stages
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'q3r4s5t6u7v8'
down_revision = '20251230_073000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add CANCELLED to the native documentstatus enum.
    #    ALTER TYPE ... ADD VALUE cannot run inside a transaction block, so use
    #    an autocommit block (standard alembic pattern for enum value additions).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE documentstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")

    # 2. Add processing/tracking columns.
    op.add_column('document', sa.Column('current_stage', sa.String(length=20), nullable=True))
    op.add_column('document', sa.Column('last_error', sa.Text(), nullable=True))
    op.add_column(
        'document',
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'document',
        sa.Column('cancel_requested', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )


def downgrade() -> None:
    op.drop_column('document', 'cancel_requested')
    op.drop_column('document', 'retry_count')
    op.drop_column('document', 'last_error')
    op.drop_column('document', 'current_stage')
    # Note: PostgreSQL cannot easily drop a single enum value; CANCELLED is left
    # in the documentstatus type on downgrade (harmless).
