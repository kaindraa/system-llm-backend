"""
Seed script to add OpenRouter models to the database.

This script adds 3 open-source models via OpenRouter:
1. Llama 3.1 8B (Meta)
2. Qwen 2.5 7B (Alibaba)
3. Phi-3 Medium (Microsoft)

Usage:
    python -m app.scripts.seed_openrouter_models
"""

import logging
from uuid import uuid4
from app.core.database import SessionLocal
from app.models.model import Model

logger = logging.getLogger(__name__)


def seed_openrouter_models():
    """Add OpenRouter models to database"""
    db = SessionLocal()

    try:
        # Define OpenRouter models
        openrouter_models = [
            {
                "name": "meta-llama/llama-3.1-8b-instruct",
                "display_name": "Llama 3.1 8B (OpenRouter)",
                "provider": "openrouter",
                "description": "Meta's Llama 3.1 8B Instruct - Fast, efficient open-source model",
                "order": 10
            },
            {
                "name": "qwen/qwen-2.5-7b-instruct",
                "display_name": "Qwen 2.5 7B (OpenRouter)",
                "provider": "openrouter",
                "description": "Alibaba's Qwen 2.5 7B - Multilingual, code-aware model",
                "order": 11
            },
            {
                "name": "microsoft/phi-3-medium-128k-instruct",
                "display_name": "Phi-3 Medium (OpenRouter)",
                "provider": "openrouter",
                "description": "Microsoft's Phi-3 Medium - Efficient model with long context window (128K)",
                "order": 12
            }
        ]

        # Add models to database
        added_count = 0
        for model_data in openrouter_models:
            # Check if model already exists
            existing = db.query(Model).filter(
                Model.name == model_data["name"]
            ).first()

            if existing:
                print(f"⏭️  Model already exists: {model_data['display_name']}")
                continue

            # Create new model
            model = Model(
                id=uuid4(),
                name=model_data["name"],
                display_name=model_data["display_name"],
                provider=model_data["provider"],
                api_endpoint="https://openrouter.ai/api/v1",
                order=model_data["order"]
            )

            db.add(model)
            added_count += 1
            print(f"✅ Added model: {model_data['display_name']}")

        # Commit changes
        db.commit()
        print(f"\n✅ Successfully added {added_count} OpenRouter models!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding models: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Seeding OpenRouter models to database...")
    print("=" * 60)
    seed_openrouter_models()
    print("=" * 60)
    print("✨ Done!")
