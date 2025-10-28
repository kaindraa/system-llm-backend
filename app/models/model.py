from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Model(Base):
    """AI Model registry for LLM models (Llama, Qwen, Phi, etc.)"""
    __tablename__ = "model"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    provider = Column(String(100))  # 'ollama', 'openai', 'anthropic', etc.
    api_endpoint = Column(String(500))
    order = Column(Integer, default=0, index=True)  # Display order (lower = higher priority/first)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="model")

    def __repr__(self):
        return f"<Model {self.display_name}>"
