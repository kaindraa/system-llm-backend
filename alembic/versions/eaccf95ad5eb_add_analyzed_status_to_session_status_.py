"""add analyzed status to session_status enum

Revision ID: eaccf95ad5eb
Revises: 171dfa425590
Create Date: 2025-11-09 16:23:59.043478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaccf95ad5eb'
down_revision: Union[str, None] = '171dfa425590'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add "analyzed" status to sessionstatus enum
    # Remove "completed" status - recreate enum type without it
    op.execute("ALTER TYPE sessionstatus RENAME TO sessionstatus_old")
    op.execute("CREATE TYPE sessionstatus AS ENUM ('active', 'analyzed')")
    # Convert existing values to lowercase before casting
    op.execute("ALTER TABLE chat_session ALTER COLUMN status TYPE sessionstatus USING LOWER(status::text)::sessionstatus")
    op.execute("DROP TYPE sessionstatus_old")


def downgrade() -> None:
    # Revert to original enum with 'completed'
    op.execute("ALTER TYPE sessionstatus RENAME TO sessionstatus_old")
    op.execute("CREATE TYPE sessionstatus AS ENUM ('active', 'completed')")
    op.execute("ALTER TABLE chat_session ALTER COLUMN status TYPE sessionstatus USING 'active'::sessionstatus")
    op.execute("DROP TYPE sessionstatus_old")
