"""
RAG (Retrieval-Augmented Generation) Endpoints

Provides RAG health check, configuration, and direct search capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.services.rag import RAGService
from app.models.user import User
from app.schemas.rag import (
    RAGSearchResponse,
    RAGConfigResponse,
    RAGHealthResponse,
    RAGSearchResult,
    RAGSource
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/rag",
    tags=["RAG"]
)


@router.get("/health", response_model=RAGHealthResponse)
async def rag_health(db: Session = Depends(get_db)):
    """
    Check RAG system health.

    Returns information about:
    - OpenAI embeddings availability
    - pgvector database connectivity
    - Total documents and chunks stored

    **No authentication required** (public endpoint for monitoring)
    """
    try:
        rag_service = RAGService(db)
        health = rag_service.health_check()

        return RAGHealthResponse(
            status="healthy" if health["embeddings_ok"] and health["pgvector_ok"] else "degraded",
            embeddings={
                "available": health["embeddings_ok"],
                "model": "text-embedding-3-small (1536 dimensions)"
            },
            pgvector={
                "available": health["pgvector_ok"],
                "total_chunks": health["total_chunks"],
                "total_documents": health["total_documents"],
                "processed_documents": health["processed_documents"]
            },
            errors=health.get("errors", [])
        )
    except Exception as e:
        logger.error(f"RAG health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/search", response_model=RAGSearchResponse)
async def semantic_search(
    query: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return"),
    similarity_threshold: float = Query(0.7, ge=0, le=1, description="Minimum similarity threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform semantic search on documents.

    This is a direct search endpoint for testing/debugging RAG.
    In normal chat flow, the LLM calls this via tool calling.

    **Query Parameters:**
    - `query`: Search query string (required)
    - `top_k`: Number of results to return (default: 5, max: 20)
    - `similarity_threshold`: Minimum relevance score 0-1 (default: 0.7)

    **Returns:** List of relevant document chunks with similarity scores and sources

    **Authentication:** Required
    """
    try:
        if top_k > 20:
            top_k = 20

        rag_service = RAGService(db)
        results = rag_service.semantic_search(
            query_text=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

        # Convert results to schema objects
        search_results = [
            RAGSearchResult(
                chunk_id=r["chunk_id"],
                content=r["content"],
                document_id=r["document_id"],
                filename=r["filename"],
                page=r["page"],
                similarity_score=r["similarity_score"],
                chunk_index=r["chunk_index"],
                metadata=r.get("metadata")
            )
            for r in results
        ]

        return RAGSearchResponse(
            query=query,
            results=search_results,
            count=len(search_results),
            top_k=top_k,
            threshold=similarity_threshold
        )
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/config", response_model=RAGConfigResponse)
async def rag_configuration(db: Session = Depends(get_db)):
    """
    Get RAG configuration and statistics.

    Returns comprehensive information about:
    - Embeddings model and availability
    - Vector database (pgvector) configuration
    - Document statistics
    - Search settings and limits

    **No authentication required** (public endpoint for configuration)
    """
    try:
        rag_service = RAGService(db)
        health = rag_service.health_check()

        return RAGConfigResponse(
            embeddings={
                "provider": "OpenAI",
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "available": health["embeddings_ok"]
            },
            vector_database={
                "system": "PostgreSQL with pgvector extension",
                "similarity_metric": "Cosine similarity (1 - distance)",
                "available": health["pgvector_ok"]
            },
            documents={
                "total": health["total_documents"],
                "processed": health["processed_documents"],
                "pending": health["total_documents"] - health["processed_documents"],
                "total_chunks": health["total_chunks"]
            },
            search_settings={
                "default_top_k": 5,
                "min_similarity_threshold": 0.65,
                "max_results": 20
            }
        )
    except Exception as e:
        logger.error(f"Failed to get RAG config: {e}")
        raise HTTPException(status_code=500, detail=f"Config retrieval failed: {str(e)}")
