"""Seed OpenRouter models to model table

Revision ID: k0l1m2n3o4p5
Revises: 7b128ccfa63c
Create Date: 2025-11-20 09:36:44.000000

This migration records the addition of 3 OpenRouter models that were seeded via:
    python -m app.scripts.seed_openrouter_models

Models added:
1. Llama 3.1 8B (Meta) - meta-llama/llama-3.1-8b-instruct
2. Qwen 2.5 7B (Alibaba) - qwen/qwen-2.5-7b-instruct
3. Phi-3 Medium (Microsoft) - microsoft/phi-3-medium-128k-instruct

All models use OpenRouter endpoint: https://openrouter.ai/api/v1
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'k0l1m2n3o4p5'
down_revision = '7b128ccfa63c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    This is a recording migration - the data was already inserted via:
        python -m app.scripts.seed_openrouter_models

    This migration just marks the database state in Alembic history.
    No action needed - the 3 OpenRouter models are already in the database.
    """
    # Check if models already exist (they should)
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            """
            SELECT COUNT(*) as count FROM model
            WHERE provider = 'openrouter'
            AND name IN (
                'meta-llama/llama-3.1-8b-instruct',
                'qwen/qwen-2.5-7b-instruct',
                'microsoft/phi-3-medium-128k-instruct'
            )
            """
        )
    )
    count = result.scalar()

    if count == 3:
        print("✅ All 3 OpenRouter models already present in database")
    else:
        print(f"⚠️  Warning: Only {count}/3 OpenRouter models found in database")
        print("   Please run: python -m app.scripts.seed_openrouter_models")


def downgrade() -> None:
    """
    Remove the 3 OpenRouter models from model table
    """
    op.execute(
        sa.text(
            """
            DELETE FROM model
            WHERE provider = 'openrouter'
            AND name IN (
                'meta-llama/llama-3.1-8b-instruct',
                'qwen/qwen-2.5-7b-instruct',
                'microsoft/phi-3-medium-128k-instruct'
            )
            """
        )
    )
