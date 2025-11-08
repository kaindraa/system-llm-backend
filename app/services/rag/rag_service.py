"""
RAG Service - Semantic Search and Document Retrieval

Handles vector embeddings, semantic search using pgvector,
and retrieval of relevant document chunks for context augmentation.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text as sql_text
from uuid import UUID
import logging

from app.models.document_chunk import DocumentChunk
from app.models.document import Document
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGService:
    """Service for semantic search and RAG context retrieval."""

    def __init__(self, db: Session):
        """Initialize RAG service with database session."""
        self.db = db
        self._embeddings_client = None

    def _get_embeddings_client(self):
        """Lazy load embeddings client."""
        if self._embeddings_client is None:
            try:
                from openai import OpenAI
                from app.core.config import settings

                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY not configured")

                self._embeddings_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI embeddings client: {e}")
                raise

        return self._embeddings_client

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding (1536 dimensions)

        Raises:
            RuntimeError: If embedding generation fails
        """
        try:
            client = self._get_embeddings_client()
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text (len={len(text)}, dims={len(embedding)})")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")

    def semantic_search(
        self,
        query_text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using pgvector cosine similarity.

        Args:
            query_text: Query text to search for
            top_k: Number of top results to return
            similarity_threshold: Minimum similarity score (0-1, ignored if negative)

        Returns:
            List of dicts with keys: content, document_id, filename, page,
            similarity_score, chunk_index, chunk_metadata

        Raises:
            RuntimeError: If search fails
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query_text)

            # Convert to pgvector format: '[0.1, 0.2, ..., 1.5]'
            embedding_str = '[' + ','.join(str(float(v)) for v in query_embedding) + ']'

            # Use <=> operator for cosine similarity
            # Note: pgvector <=> returns distance, not similarity (1 - distance gives similarity)
            query = f"""
                SELECT
                    dc.id as chunk_id,
                    dc.content,
                    dc.document_id,
                    d.original_filename,
                    dc.page_number,
                    1 - (dc.embedding <=> '{embedding_str}'::vector) as similarity_score,
                    dc.chunk_index,
                    dc.chunk_metadata
                FROM document_chunk dc
                JOIN document d ON dc.document_id = d.id
                WHERE d.status = 'PROCESSED'
                ORDER BY dc.embedding <=> '{embedding_str}'::vector ASC
                LIMIT :limit
            """

            result = self.db.execute(sql_text(query), {"limit": top_k})

            results = []
            for row in result.fetchall():
                chunk_id, content, doc_id, filename, page_num, similarity, chunk_idx, metadata = row

                # Apply similarity threshold if specified
                if similarity_threshold > 0 and similarity < similarity_threshold:
                    continue

                results.append({
                    "chunk_id": str(chunk_id),
                    "content": content,
                    "document_id": str(doc_id),
                    "filename": filename,
                    "page": page_num,
                    "similarity_score": float(similarity) if similarity else 0.0,
                    "chunk_index": chunk_idx,
                    "metadata": metadata or {}
                })

            logger.info(f"Semantic search: found {len(results)} results (top_k={top_k}, threshold={similarity_threshold})")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise RuntimeError(f"Semantic search failed: {e}")

    def format_rag_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format retrieved chunks into a context string for LLM prompt.

        Args:
            chunks: List of chunk dicts from semantic_search()

        Returns:
            Formatted context string
        """
        if not chunks:
            return ""

        context_parts = ["### RELEVANT DOCUMENTS CONTEXT:\n"]

        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"\n[Source {i}] {chunk['filename']} (Page {chunk['page']}) - Similarity: {chunk['similarity_score']:.2%}")
            context_parts.append(f"{chunk['content']}\n")

        context_parts.append("\n### END CONTEXT ###\n")

        context_str = "".join(context_parts)
        logger.debug(f"Formatted RAG context: {len(context_str)} chars from {len(chunks)} chunks")

        return context_str

    def extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract source metadata from retrieved chunks.

        Args:
            chunks: List of chunk dicts from semantic_search()

        Returns:
            List of source dicts with: document_id, filename, page, similarity_score
        """
        sources = []
        seen = set()  # Track unique (doc_id, page) pairs

        for chunk in chunks:
            key = (chunk['document_id'], chunk['page'])
            if key not in seen:
                sources.append({
                    "document_id": chunk['document_id'],
                    "filename": chunk['filename'],
                    "page": chunk['page'],
                    "similarity_score": chunk['similarity_score']
                })
                seen.add(key)

        logger.debug(f"Extracted {len(sources)} unique sources from {len(chunks)} chunks")
        return sources

    def get_user_documents(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all processed documents for a user.

        Args:
            user_id: User UUID

        Returns:
            List of document dicts with: id, filename, status, chunk_count
        """
        try:
            query = """
                SELECT
                    d.id,
                    d.original_filename,
                    d.status,
                    COUNT(dc.id) as chunk_count
                FROM document d
                LEFT JOIN document_chunk dc ON d.id = dc.document_id
                WHERE d.user_id = :user_id
                GROUP BY d.id
                ORDER BY d.created_at DESC
            """

            result = self.db.execute(sql_text(query), {"user_id": str(user_id)})

            documents = []
            for row in result.fetchall():
                doc_id, filename, status, chunk_count = row
                documents.append({
                    "id": str(doc_id),
                    "filename": filename,
                    "status": status,
                    "chunk_count": chunk_count or 0
                })

            logger.debug(f"Found {len(documents)} documents for user {user_id}")
            return documents

        except Exception as e:
            logger.error(f"Failed to get user documents: {e}")
            raise RuntimeError(f"Failed to get user documents: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check RAG service health (embeddings, pgvector, documents).

        Returns:
            Dict with: embeddings_ok, pgvector_ok, total_chunks, total_documents
        """
        health = {
            "embeddings_ok": False,
            "pgvector_ok": False,
            "total_chunks": 0,
            "total_documents": 0,
            "processed_documents": 0,
            "errors": []
        }

        try:
            # Test embeddings client
            try:
                self.generate_embedding("test")
                health["embeddings_ok"] = True
            except Exception as e:
                health["errors"].append(f"Embeddings: {str(e)}")

            # Test pgvector
            try:
                result = self.db.execute(sql_text("SELECT COUNT(*) FROM document_chunk"))
                health["total_chunks"] = result.scalar() or 0

                result = self.db.execute(sql_text("SELECT COUNT(*) FROM document"))
                health["total_documents"] = result.scalar() or 0

                result = self.db.execute(sql_text("SELECT COUNT(*) FROM document WHERE status = 'PROCESSED'"))
                health["processed_documents"] = result.scalar() or 0

                health["pgvector_ok"] = True
            except Exception as e:
                health["errors"].append(f"pgvector: {str(e)}")

            logger.info(f"RAG health check: {health}")
            return health

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health["errors"].append(f"General: {str(e)}")
            return health
