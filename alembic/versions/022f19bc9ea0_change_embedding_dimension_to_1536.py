"""Change embedding dimension to 1536

Revision ID: 022f19bc9ea0
Revises: c82c550cf83d
Create Date: 2025-11-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '022f19bc9ea0'
down_revision: Union[str, None] = 'c82c550cf83d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter the embedding column type from Vector(768) to Vector(1536)
    op.alter_column('document_chunk', 'embedding',
               existing_type=Vector(768),
               type_=Vector(1536),
               existing_nullable=True)


def downgrade() -> None:
    # Revert back to Vector(768)
    op.alter_column('document_chunk', 'embedding',
               existing_type=Vector(1536),
               type_=Vector(768),
               existing_nullable=True)
