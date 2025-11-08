from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum


class SessionStatus(str, enum.Enum):
    """Chat session status"""
    ACTIVE = "active"
    COMPLETED = "completed"


class ComprehensionLevel(str, enum.Enum):
    """Student comprehension level from analytics"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ChatSession(Base):
    """Chat session with messages stored as JSONB and analytics fields"""
    __tablename__ = "chat_session"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    prompt_id = Column(UUID(as_uuid=True), ForeignKey("prompt.id"))
    model_id = Column(UUID(as_uuid=True), ForeignKey("model.id"), nullable=False, index=True)
    title = Column(String(255))

    # Messages stored as JSONB array
    # Format: [{"role": "user|assistant|system", "content": "...", "created_at": "...", "sources": [...]}]
    messages = Column(JSONB, nullable=False, default=list)

    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, index=True)

    # Prompt fields - stored for tracking the concatenated prompt that was used
    # Order: prompt_general + task + persona + mission_objective (from Prompt table handled separately)
    prompt_general = Column(Text, nullable=True)        # From ChatConfig
    task = Column(Text, nullable=True)                  # From User profile
    persona = Column(Text, nullable=True)               # From User profile
    mission_objective = Column(Text, nullable=True)     # From User profile

    # Analytics fields (Stage 9)
    total_messages = Column(Integer, default=0)
    comprehension_level = Column(SQLEnum(ComprehensionLevel), nullable=True)
    summary = Column(Text)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))
    analyzed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    model = relationship("Model", back_populates="chat_sessions")

    def __repr__(self):
        return f"<ChatSession {self.id} - {self.title or 'Untitled'}>"
