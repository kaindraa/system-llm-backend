"""
Script to seed LLM models into the database.
This script adds default models (OpenAI) that can be used for testing and production.

Run this script using:
python -m app.scripts.seed_models
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.model import Model
from app.core.logging import get_logger
import sys

logger = get_logger(__name__)


def seed_models(db: Session):
    """Seed default LLM models into the database."""

    # Default models to seed (OpenAI 2025 models)
    # Model names use lowercase with dash format (e.g., gpt-5-mini) for API compatibility
    default_models = [
        {
            "name": "gpt-5-mini",
            "display_name": "GPT-5 Mini",
            "provider": "openai",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
        },
        {
            "name": "gpt-5",
            "display_name": "GPT-5",
            "provider": "openai",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
        },
        {
            "name": "gpt-5-nano",
            "display_name": "GPT-5 Nano",
            "provider": "openai",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
        },
        {
            "name": "gpt-4.1",
            "display_name": "GPT-4.1",
            "provider": "openai",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
        },
        {
            "name": "gpt-4.1-nano",
            "display_name": "GPT-4.1 Nano",
            "provider": "openai",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
        },
        {
            "name": "gpt-4o",
            "display_name": "GPT-4o (Multimodal)",
            "provider": "openai",
            "api_endpoint": "https://api.openai.com/v1/chat/completions",
        },
    ]

    created_count = 0
    skipped_count = 0

    for model_data in default_models:
        # Check if model already exists
        existing_model = (
            db.query(Model).filter(Model.name == model_data["name"]).first()
        )

        if existing_model:
            logger.info(f"Model '{model_data['name']}' already exists. Skipping...")
            skipped_count += 1
            continue

        # Create new model
        new_model = Model(**model_data)
        db.add(new_model)
        logger.info(f"Created model: {model_data['display_name']} ({model_data['name']})")
        created_count += 1

    # Commit changes
    db.commit()

    logger.info(
        f"Seeding complete! Created: {created_count}, Skipped: {skipped_count}"
    )


def main():
    """Main function to run the seeding script."""
    logger.info("Starting model seeding...")

    try:
        # Create database session
        db = SessionLocal()

        # Seed models
        seed_models(db)

        logger.info("Model seeding completed successfully!")

    except Exception as e:
        logger.error(f"Error during model seeding: {str(e)}", exc_info=True)
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
