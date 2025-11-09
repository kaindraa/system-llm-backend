"""
RAG (Retrieval-Augmented Generation) Request/Response Schemas

Pydantic models for RAG endpoints to ensure proper API documentation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class RAGSearchResult(BaseModel):
    """A single search result chunk from semantic search."""
    chunk_id: str = Field(..., description="Unique ID of the document chunk")
    content: str = Field(..., description="Text content of the chunk")
    document_id: str = Field(..., description="Parent document ID")
    filename: str = Field(..., description="Original filename of the document")
    page: int = Field(..., description="Page number in the PDF")
    similarity_score: float = Field(..., description="Similarity score (0-1, 1=most similar)")
    chunk_index: int = Field(..., description="Index of this chunk in the document")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata (heading, section, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
                "content": "Network Address Translation (NAT) allows private networks to use private IP addresses...",
                "document_id": "660e8400-e29b-41d4-a716-446655440000",
                "filename": "H03 - NAT & OSPF.pdf",
                "page": 5,
                "similarity_score": 0.92,
                "chunk_index": 2,
                "metadata": {"heading": "NAT Definition"}
            }
        }


class RAGSource(BaseModel):
    """Source document reference for citations."""
    document_id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Document filename")
    page: Optional[int] = Field(None, description="Page number where content was found")
    similarity_score: float = Field(..., description="Relevance score (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "python-basics.pdf",
                "page": 5,
                "similarity_score": 0.92
            }
        }


class RAGSearchRequest(BaseModel):
    """Request body for semantic search."""
    query: str = Field(..., description="Search query text", min_length=1)
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)
    similarity_threshold: float = Field(0.7, description="Minimum relevance threshold (0-1)", ge=0, le=1)


class RAGSearchResponse(BaseModel):
    """Response from semantic search."""
    query: str = Field(..., description="The original search query")
    results: List[RAGSearchResult] = Field(..., description="List of relevant chunks")
    count: int = Field(..., description="Number of results returned")
    top_k: int = Field(..., description="Requested top-k value")
    threshold: float = Field(..., description="Similarity threshold used")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "what is NAT",
                "results": [
                    {
                        "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
                        "content": "Network Address Translation...",
                        "document_id": "660e8400-e29b-41d4-a716-446655440000",
                        "filename": "H03 - NAT & OSPF.pdf",
                        "page": 5,
                        "similarity_score": 0.92,
                        "chunk_index": 2,
                        "metadata": {"heading": "NAT Definition"}
                    }
                ],
                "count": 1,
                "top_k": 5,
                "threshold": 0.7
            }
        }


class RAGEmbeddingInfo(BaseModel):
    """Embeddings configuration info."""
    provider: str = Field(..., description="Embedding provider")
    model: str = Field(..., description="Embedding model name")
    dimensions: int = Field(..., description="Embedding vector dimensions")
    available: bool = Field(..., description="Is embeddings service available")


class RAGVectorDBInfo(BaseModel):
    """Vector database configuration info."""
    system: str = Field(..., description="Vector database system")
    similarity_metric: str = Field(..., description="Similarity calculation method")
    available: bool = Field(..., description="Is vector database available")


class RAGDocumentStats(BaseModel):
    """Document statistics."""
    total: int = Field(..., description="Total documents in system")
    processed: int = Field(..., description="Processed and indexed documents")
    pending: int = Field(..., description="Documents pending processing")
    total_chunks: int = Field(..., description="Total document chunks indexed")


class RAGSearchSettings(BaseModel):
    """RAG search configuration."""
    default_top_k: int = Field(..., description="Default number of results")
    min_similarity_threshold: float = Field(..., description="Minimum similarity threshold")
    max_results: int = Field(..., description="Maximum allowed results")


class RAGConfigResponse(BaseModel):
    """RAG system configuration."""
    embeddings: RAGEmbeddingInfo = Field(..., description="Embeddings configuration")
    vector_database: RAGVectorDBInfo = Field(..., description="Vector database configuration")
    documents: RAGDocumentStats = Field(..., description="Document statistics")
    search_settings: RAGSearchSettings = Field(..., description="Search configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "embeddings": {
                    "provider": "OpenAI",
                    "model": "text-embedding-3-small",
                    "dimensions": 1536,
                    "available": True
                },
                "vector_database": {
                    "system": "PostgreSQL with pgvector extension",
                    "similarity_metric": "Cosine similarity (1 - distance)",
                    "available": True
                },
                "documents": {
                    "total": 3,
                    "processed": 3,
                    "pending": 0,
                    "total_chunks": 42
                },
                "search_settings": {
                    "default_top_k": 5,
                    "min_similarity_threshold": 0.65,
                    "max_results": 20
                }
            }
        }


class RAGHealthResponse(BaseModel):
    """RAG system health status."""
    status: str = Field(..., description="Overall health status (healthy/degraded)")
    embeddings: Dict[str, Any] = Field(..., description="Embeddings status")
    pgvector: Dict[str, Any] = Field(..., description="pgvector status and statistics")
    errors: List[str] = Field(default_factory=list, description="List of errors if any")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "embeddings": {
                    "available": True,
                    "model": "text-embedding-3-small (1536 dimensions)"
                },
                "pgvector": {
                    "available": True,
                    "total_chunks": 42,
                    "total_documents": 3,
                    "processed_documents": 3
                },
                "errors": []
            }
        }


class RAGSearchEvent(BaseModel):
    """RAG search event from streaming response."""
    query: str = Field(..., description="Search query")
    status: str = Field(..., description="Event status (searching/completed)")
    results_count: Optional[int] = Field(None, description="Number of results (only when status=completed)")


class RAGSettingsResponse(BaseModel):
    """RAG system settings from database."""
    id: int = Field(..., description="Config ID (always 1 - singleton)")
    prompt_general: str = Field(..., description="General system prompt prepended to all conversations")
    prompt_analysis: Optional[str] = Field(None, description="Analysis prompt for evaluating student learning sessions")
    default_top_k: int = Field(..., description="Default number of search results", ge=1, le=100)
    max_top_k: int = Field(..., description="Maximum number of search results", ge=1, le=100)
    similarity_threshold: float = Field(..., description="Minimum similarity score (0-1)", ge=0, le=1)
    tool_calling_max_iterations: int = Field(..., description="Max tool calling iterations", ge=1, le=100)
    tool_calling_enabled: bool = Field(..., description="Enable/disable tool calling")
    include_rag_instruction: bool = Field(..., description="Include RAG instruction in system prompt")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last update")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "prompt_general": "You are a helpful AI assistant...",
                "prompt_analysis": "Analyze the student learning session and provide...",
                "default_top_k": 5,
                "max_top_k": 10,
                "similarity_threshold": 0.7,
                "tool_calling_max_iterations": 10,
                "tool_calling_enabled": True,
                "include_rag_instruction": True,
                "updated_at": "2025-11-08T10:30:00Z"
            }
        }


class RAGSettingsUpdate(BaseModel):
    """Request body for updating RAG settings."""
    prompt_general: Optional[str] = Field(None, description="General system prompt prepended to all conversations")
    prompt_analysis: Optional[str] = Field(None, description="Analysis prompt for evaluating student learning sessions")
    default_top_k: Optional[int] = Field(None, description="Default number of search results", ge=1, le=100)
    max_top_k: Optional[int] = Field(None, description="Maximum number of search results", ge=1, le=100)
    similarity_threshold: Optional[float] = Field(None, description="Minimum similarity score (0-1)", ge=0, le=1)
    tool_calling_max_iterations: Optional[int] = Field(None, description="Max tool calling iterations", ge=1, le=100)
    tool_calling_enabled: Optional[bool] = Field(None, description="Enable/disable tool calling")
    include_rag_instruction: Optional[bool] = Field(None, description="Include RAG instruction in system prompt")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt_general": "You are a helpful AI assistant...",
                "prompt_analysis": "Analyze the student learning session and provide...",
                "default_top_k": 5,
                "max_top_k": 10,
                "similarity_threshold": 0.7,
                "tool_calling_max_iterations": 10,
                "tool_calling_enabled": True,
                "include_rag_instruction": True
            }
        }


class ChatMessageWithSources(BaseModel):
    """Chat message with optional source citations."""
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    created_at: str = Field(..., description="ISO timestamp of creation")
    sources: Optional[List[RAGSource]] = Field(None, description="Source documents for RAG-based responses")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "assistant",
                "content": "A loop is a control structure that repeats a block of code...",
                "created_at": "2025-11-08T10:30:00Z",
                "sources": [
                    {
                        "document_id": "660e8400-e29b-41d4-a716-446655440000",
                        "filename": "python-basics.pdf",
                        "page": 5,
                        "similarity_score": 0.92
                    }
                ]
            }
        }
