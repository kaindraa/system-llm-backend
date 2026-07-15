"""add document ingestion lease metadata

Revision ID: r4s5t6u7v8w9
Revises: q3r4s5t6u7v8
Create Date: 2026-07-15 16:00:00.000000

The worker uses these fields to atomically claim a queued document and renew
its lease while processing. A replacement worker may only reclaim a document
after the previous lease has expired.
"""

from alembic import op
import sqlalchemy as sa


revision = "r4s5t6u7v8w9"
down_revision = "q3r4s5t6u7v8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document",
        sa.Column("processing_owner", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "document",
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document",
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "document",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_index(
        "ix_document_ingestion_queue",
        "document",
        ["status", "lease_expires_at", "uploaded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_document_ingestion_queue", table_name="document")
    op.drop_column("document", "attempt_count")
    op.drop_column("document", "last_heartbeat_at")
    op.drop_column("document", "lease_expires_at")
    op.drop_column("document", "processing_owner")
