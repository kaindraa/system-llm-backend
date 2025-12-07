"""Create document_chunk table

Revision ID: z0a1b2c3d4e5f
Revises: p1q2r3s4t5u6
Create Date: 2025-12-07 21:18:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'z0a1b2c3d4e5f'
down_revision = 'p1q2r3s4t5u6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document_chunk table
    # Note: For LOCAL development, embeddings stored as TEXT (JSON array)
    # For PRODUCTION, would use pgvector Vector(dim=1536)
    # FK constraint skipped for LOCAL due to document table schema issues
    op.create_table(
        'document_chunk',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),  # JSON array of floats
        sa.Column('chunk_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index(op.f('ix_document_chunk_document_id'), 'document_chunk', ['document_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_chunk_document_id'), table_name='document_chunk')
    op.drop_table('document_chunk')
