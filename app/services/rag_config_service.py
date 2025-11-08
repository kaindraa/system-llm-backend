"""
RAG Configuration Service

Manages RAG system settings from database.
Provides CRUD operations for RAG configuration.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.rag_config import RAGConfig
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGConfigService:
    """Service for managing RAG configuration."""

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    @staticmethod
    def _ensure_config_exists(db: Session) -> RAGConfig:
        """Ensure singleton config row exists, create if not."""
        config = db.query(RAGConfig).filter(RAGConfig.id == 1).first()

        if not config:
            logger.info("RAG config not found, creating default...")
            config = RAGConfig(
                id=1,
                default_top_k=5,
                max_top_k=10,
                similarity_threshold=0.7,
                tool_calling_max_iterations=10,
                tool_calling_enabled=True,
                include_rag_instruction=True,
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            logger.info("RAG config created with defaults")

        return config

    def get_config(self) -> RAGConfig:
        """Get current RAG configuration."""
        config = self.db.query(RAGConfig).filter(RAGConfig.id == 1).first()

        if not config:
            config = self._ensure_config_exists(self.db)

        logger.debug(f"Retrieved RAG config: {config.to_dict()}")
        return config

    def update_config(
        self,
        default_top_k: Optional[int] = None,
        max_top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        tool_calling_max_iterations: Optional[int] = None,
        tool_calling_enabled: Optional[bool] = None,
        include_rag_instruction: Optional[bool] = None,
    ) -> RAGConfig:
        """
        Update RAG configuration.

        Args:
            default_top_k: Default number of search results
            max_top_k: Maximum number of search results
            similarity_threshold: Minimum similarity score (0-1)
            tool_calling_max_iterations: Max tool calling iterations
            tool_calling_enabled: Enable/disable tool calling
            include_rag_instruction: Include RAG instruction in system prompt

        Returns:
            Updated RAGConfig object
        """
        config = self.get_config()

        # Update fields if provided
        if default_top_k is not None:
            if not (1 <= default_top_k <= 100):
                raise ValueError("default_top_k must be between 1 and 100")
            config.default_top_k = default_top_k

        if max_top_k is not None:
            if not (1 <= max_top_k <= 100):
                raise ValueError("max_top_k must be between 1 and 100")
            config.max_top_k = max_top_k

        if similarity_threshold is not None:
            if not (0.0 <= similarity_threshold <= 1.0):
                raise ValueError("similarity_threshold must be between 0 and 1")
            config.similarity_threshold = similarity_threshold

        if tool_calling_max_iterations is not None:
            if not (1 <= tool_calling_max_iterations <= 100):
                raise ValueError("tool_calling_max_iterations must be between 1 and 100")
            config.tool_calling_max_iterations = tool_calling_max_iterations

        if tool_calling_enabled is not None:
            config.tool_calling_enabled = int(tool_calling_enabled)

        if include_rag_instruction is not None:
            config.include_rag_instruction = int(include_rag_instruction)

        self.db.commit()
        self.db.refresh(config)

        logger.info(f"RAG config updated: {config.to_dict()}")
        return config

    def reset_to_defaults(self) -> RAGConfig:
        """Reset configuration to default values."""
        config = self.get_config()

        config.default_top_k = 5
        config.max_top_k = 10
        config.similarity_threshold = 0.7
        config.tool_calling_max_iterations = 10
        config.tool_calling_enabled = 1
        config.include_rag_instruction = 1

        self.db.commit()
        self.db.refresh(config)

        logger.info("RAG config reset to defaults")
        return config

    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        config = self.get_config()
        return config.to_dict()
