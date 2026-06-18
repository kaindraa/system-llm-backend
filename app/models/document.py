from sqlalchemy import Column, String, BigInteger, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy import text as sql_text
from app.core.database import Base
import uuid
import enum


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IngestionStage(str, enum.Enum):
    """Fine-grained stage within PROCESSING (for dashboard progress)."""
    QUEUED = "queued"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INSERTING = "inserting"
    DONE = "done"


class Document(Base):
    """PDF document metadata"""
    __tablename__ = "document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    content = Column(Text)  # Raw extracted text from PDF (nullable until processed)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED, index=True)
    # Processing/ingestion tracking (used by the background ingestion pipeline + dashboard)
    current_stage = Column(String(20))  # one of IngestionStage values; null when not processing
    last_error = Column(Text)  # error message of last failed ingestion attempt
    retry_count = Column(Integer, nullable=False, server_default="0", default=0)
    cancel_requested = Column(Boolean, nullable=False, server_default=sql_text("false"), default=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<Document {self.original_filename}>"
