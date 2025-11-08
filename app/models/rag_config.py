"""
RAG Configuration Model

Stores RAG system settings that can be configured via API.
"""

from sqlalchemy import Column, Float, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class RAGConfig(Base):
    """RAG system configuration settings."""
    __tablename__ = "rag_config"

    # Only one row in this table - singleton pattern
    # We use a fixed id=1 to ensure uniqueness
    id = Column(Integer, primary_key=True, default=1)

    # Semantic search parameters
    default_top_k = Column(Integer, default=5, nullable=False)
    max_top_k = Column(Integer, default=10, nullable=False)
    similarity_threshold = Column(Float, default=0.7, nullable=False)

    # Tool calling parameters
    tool_calling_max_iterations = Column(Integer, default=10, nullable=False)
    tool_calling_enabled = Column(Integer, default=1, nullable=False)  # SQLite doesn't have Boolean

    # RAG instruction in system prompt
    include_rag_instruction = Column(Integer, default=1, nullable=False)

    # Metadata
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<RAGConfig(top_k={self.default_top_k}, threshold={self.similarity_threshold})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "default_top_k": self.default_top_k,
            "max_top_k": self.max_top_k,
            "similarity_threshold": self.similarity_threshold,
            "tool_calling_max_iterations": self.tool_calling_max_iterations,
            "tool_calling_enabled": bool(self.tool_calling_enabled),
            "include_rag_instruction": bool(self.include_rag_instruction),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
