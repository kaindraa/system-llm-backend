"""Add prompt_refine column to chat_config table for LLM prompt refinement

Revision ID: m5n6o7p8q9r0
Revises: k0l1m2n3o4p5
Create Date: 2025-11-20 10:00:00.000000

This migration adds a new column to store the prompt template for refining student questions.
The refine_prompt tool will use this as the system instruction when LLM decides to refine
an ambiguous or unclear student question before performing RAG search.

Example prompt_refine content:
    "Anda adalah prompt refinement specialist. Tugas Anda adalah mengambil pertanyaan
    student yang mungkin ambigu/tidak jelas, dan mengubahnya menjadi pertanyaan yang lebih
    spesifik dan jelas untuk semantic search. Hanya return pertanyaan yang di-refine,
    tanpa penjelasan tambahan."
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'm5n6o7p8q9r0'
down_revision = 'k0l1m2n3o4p5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add prompt_refine column to chat_config table"""
    op.add_column(
        'chat_config',
        sa.Column(
            'prompt_refine',
            sa.Text(),
            nullable=True,
            comment='Prompt template for LLM to refine/clarify student questions'
        )
    )
    print("✅ Added prompt_refine column to chat_config table")


def downgrade() -> None:
    """Remove prompt_refine column from chat_config table"""
    op.drop_column('chat_config', 'prompt_refine')
    print("✅ Removed prompt_refine column from chat_config table")
