"""Remove prompt_semantic_search column from chat_config (now hardcoded in code)

Revision ID: o9p0q1r2s3t4
Revises: n7o8p9q0r1s2
Create Date: 2025-11-20 15:30:00.000000

This migration removes the prompt_semantic_search column from chat_config because:
1. semantic_search tool description is now hardcoded in tools.py (stable, not changing)
2. semantic_search tool doesn't call LLM in TAHAP 2, so no dynamic instruction needed
3. Only TAHAP 2 instructions (that affect LLM behavior) should be in database

Architecture clarification:
- semantic_search: TAHAP 1 description = hardcoded, TAHAP 2 = none (just DB query)
- refine_prompt: TAHAP 1 description = hardcoded, TAHAP 2 = ChatConfig.prompt_refine (LLM instruction)
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'o9p0q1r2s3t4'
down_revision = 'n7o8p9q0r1s2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove prompt_semantic_search column from chat_config table"""
    op.drop_column('chat_config', 'prompt_semantic_search')
    print("✅ Removed prompt_semantic_search column from chat_config table")


def downgrade() -> None:
    """Restore prompt_semantic_search column to chat_config table"""
    op.add_column(
        'chat_config',
        sa.Column(
            'prompt_semantic_search',
            sa.Text(),
            nullable=True,
            comment='Tool description for semantic search - instructs LLM how to use semantic search tool'
        )
    )
    print("✅ Restored prompt_semantic_search column to chat_config table")
