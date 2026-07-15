"""add document ingestion progress fields

Revision ID: t6u7v8w9x0y1
Revises: s5t6u7v8w9x0
Create Date: 2026-07-15 17:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "t6u7v8w9x0y1"
down_revision = "s5t6u7v8w9x0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document", sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("document", sa.Column("processed_pages", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("document", sa.Column("total_pages", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("document", sa.Column("processing_detail", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("document", "processing_detail")
    op.drop_column("document", "total_pages")
    op.drop_column("document", "processed_pages")
    op.drop_column("document", "progress_percent")
