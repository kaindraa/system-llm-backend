from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.core.database import Base
import uuid


class DocumentChunk(Base):
    """Chunked document text with vector embeddings for RAG"""
    __tablename__ = "document_chunk"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer)
    embedding = Column(Vector(1536))  # Updated to 1536 dimensions for text-embedding-3-small
    chunk_metadata = Column(JSONB)  # Additional metadata (e.g., headings, context)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<DocumentChunk {self.document_id}:{self.chunk_index}>"
