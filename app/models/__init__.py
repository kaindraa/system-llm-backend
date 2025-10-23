"""
Database models for System LLM application.

This module imports all SQLAlchemy models to ensure they are registered
with SQLAlchemy's Base metadata for Alembic migrations.
"""

from app.models.user import User, UserRole
from app.models.model import Model
from app.models.prompt import Prompt
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.chat_session import ChatSession, SessionStatus, ComprehensionLevel

__all__ = [
    # Models
    "User",
    "Model",
    "Prompt",
    "Document",
    "DocumentChunk",
    "ChatSession",
    # Enums
    "UserRole",
    "DocumentStatus",
    "SessionStatus",
    "ComprehensionLevel",
]
