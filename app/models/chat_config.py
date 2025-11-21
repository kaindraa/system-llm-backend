"""
Chat Configuration Model

Stores system-wide chat settings (RAG parameters + general prompt).
Singleton pattern - only one row in this table (id=1).
"""

from sqlalchemy import Column, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class ChatConfig(Base):
    """Chat system configuration settings."""
    __tablename__ = "chat_config"

    # Singleton pattern: always id=1
    id = Column(Integer, primary_key=True, default=1)

    # General system prompt (for all users/sessions)
    prompt_general = Column(Text, nullable=True)

    # Refine prompt (for LLM to refine/clarify student questions before RAG)
    prompt_refine = Column(Text, nullable=True)

    # Analysis prompt (for session analysis)
    prompt_analysis = Column(Text, nullable=True)

    # Semantic search parameters
    default_top_k = Column(Integer, default=5, nullable=False)
    max_top_k = Column(Integer, default=10, nullable=False)
    similarity_threshold = Column(Float, default=0.7, nullable=False)

    # Tool calling parameters
    tool_calling_max_iterations = Column(Integer, default=10, nullable=False)
    tool_calling_enabled = Column(Integer, default=1, nullable=False)  # 1=True, 0=False

    # RAG instruction in system prompt
    include_rag_instruction = Column(Integer, default=1, nullable=False)  # 1=True, 0=False

    # Metadata
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ChatConfig(top_k={self.default_top_k}, threshold={self.similarity_threshold})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "prompt_general": self.prompt_general,
            "prompt_refine": self.prompt_refine,
            "prompt_analysis": self.prompt_analysis,
            "default_top_k": self.default_top_k,
            "max_top_k": self.max_top_k,
            "similarity_threshold": self.similarity_threshold,
            "tool_calling_max_iterations": self.tool_calling_max_iterations,
            "tool_calling_enabled": bool(self.tool_calling_enabled),
            "include_rag_instruction": bool(self.include_rag_instruction),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
