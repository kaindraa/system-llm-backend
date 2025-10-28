"""add_content_column_to_document

Revision ID: f1a2b3c4d5e6
Revises: b5ede45b7881
Create Date: 2025-01-23 10:00:00.000000

Add content column to document table for storing raw extracted PDF text.
This column will be populated by the RAG preprocessing pipeline.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'b5ede45b7881'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add content column to document table.

    This column will store the raw text extracted from PDF files
    before being chunked and embedded for RAG processing.
    """
    op.add_column(
        'document',
        sa.Column('content', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """
    Remove content column from document table.
    """
    op.drop_column('document', 'content')
