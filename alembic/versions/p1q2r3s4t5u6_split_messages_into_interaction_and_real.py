"""Split messages into interaction_messages and real_messages

Revision ID: p1q2r3s4t5u6
Revises: o9p0q1r2s3t4
Create Date: 2025-11-21 17:45:00.000000

This migration adds two new JSONB columns to chat_session:
- interaction_messages: Simple format for display (100% OpenAI standard)
- real_messages: Exact LLM context with tool calling (Langchain format)

The old 'messages' column is kept for backward compatibility and will be deprecated.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'p1q2r3s4t5u6'
down_revision = 'o9p0q1r2s3t4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add interaction_messages and real_messages columns"""
    op.add_column('chat_session', sa.Column('interaction_messages', postgresql.JSONB()))
    op.add_column('chat_session', sa.Column('real_messages', postgresql.JSONB()))


def downgrade() -> None:
    """Remove interaction_messages and real_messages columns"""

    # Copy interaction_messages back to messages before dropping
    op.execute("""
        UPDATE chat_session
        SET messages = interaction_messages
        WHERE interaction_messages != '[]'
        AND messages = '[]'
    """)

    # Drop real_messages column
    op.drop_column('chat_session', 'real_messages')

    # Drop interaction_messages column
    op.drop_column('chat_session', 'interaction_messages')
