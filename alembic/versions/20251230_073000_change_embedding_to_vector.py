"""change embedding to vector

Revision ID: 20251230_073000
Revises: z0a1b2c3d4e5f
Create Date: 2025-12-30 07:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251230_073000'
down_revision = 'z0a1b2c3d4e5f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER TABLE document_chunk ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)')


def downgrade() -> None:
    op.execute('ALTER TABLE document_chunk ALTER COLUMN embedding TYPE text USING embedding::text')
