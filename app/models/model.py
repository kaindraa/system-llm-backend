from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    is_active = Column(Boolean, default=True, index=True)
    config = Column(JSONB)  # {temperature, max_tokens, etc.}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Model {self.display_name}>"
