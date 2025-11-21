"""Add prompt_semantic_search column to chat_config for semantic search tool description

Revision ID: n7o8p9q0r1s2
Revises: m5n6o7p8q9r0
Create Date: 2025-11-20 10:10:00.000000

This migration adds a column to store the tool description for semantic search.
Instead of hardcoding the tool description in tools.py, we now store it in database
for consistency with other prompts (refine_prompt, prompt_general, prompt_analysis).

This allows admins to update semantic search tool behavior without touching code.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'n7o8p9q0r1s2'
down_revision = 'm5n6o7p8q9r0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add prompt_semantic_search column to chat_config table"""
    op.add_column(
        'chat_config',
        sa.Column(
            'prompt_semantic_search',
            sa.Text(),
            nullable=True,
            comment='Tool description for semantic search - instructs LLM how to use semantic search tool'
        )
    )
    print("✅ Added prompt_semantic_search column to chat_config table")


def downgrade() -> None:
    """Remove prompt_semantic_search column from chat_config table"""
    op.drop_column('chat_config', 'prompt_semantic_search')
    print("✅ Removed prompt_semantic_search column from chat_config table")
