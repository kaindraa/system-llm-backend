"""change status column from enum to string

Revision ID: 7b128ccfa63c
Revises: eaccf95ad5eb
Create Date: 2025-11-09 16:28:11.731843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b128ccfa63c'
down_revision: Union[str, None] = 'eaccf95ad5eb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change status column from sessionstatus enum to String(50)
    op.alter_column('chat_session', 'status',
               existing_type=sa.Enum('active', 'analyzed', name='sessionstatus'),
               type_=sa.String(50),
               existing_nullable=False)


def downgrade() -> None:
    # Revert status column back to enum
    op.alter_column('chat_session', 'status',
               existing_type=sa.String(50),
               type_=sa.Enum('active', 'analyzed', name='sessionstatus'),
               existing_nullable=False)
