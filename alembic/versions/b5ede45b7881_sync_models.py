"""sync models

Revision ID: b5ede45b7881
Revises: e7b67a707145
Create Date: 2025-10-25 11:18:00.896877
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b5ede45b7881'
down_revision = 'e7b67a707145'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tambah kolom baru
    op.add_column('chat_session', sa.Column('total_messages', sa.Integer(), nullable=True))

    # Drop kolom lama (aman walau sudah hilang)
    try:
        op.drop_column('chat_session', 'total_user_msg')
    except Exception:
        pass
    try:
        op.drop_column('chat_session', 'total_assistant_msg')
    except Exception:
        pass


def downgrade() -> None:
    # Balikkan perubahan
    op.add_column('chat_session', sa.Column('total_assistant_msg', sa.Integer(), nullable=True))
    op.add_column('chat_session', sa.Column('total_user_msg', sa.Integer(), nullable=True))
    try:
        op.drop_column('chat_session', 'total_messages')
    except Exception:
        pass
