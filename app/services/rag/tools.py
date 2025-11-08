"""
Langchain Tools for RAG Integration

Defines tool definitions for LLM to call RAG functions.
"""

from typing import Any, Dict, List, Optional, Callable
from langchain_core.tools import Tool
from sqlalchemy.orm import Session

from app.services.rag.rag_service import RAGService
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGToolFactory:
    """Factory for creating Langchain RAG tools."""

    def __init__(self, db: Session):
        """Initialize tool factory with database session."""
        self.db = db
        self.rag_service = RAGService(db)

    def create_semantic_search_tool(self) -> Tool:
        """
        Create a Langchain tool for semantic search.

        The LLM can call this tool to search for relevant documents.

        Returns:
            Langchain Tool object
        """

        def semantic_search_impl(query: str, top_k: int = 5) -> Dict[str, Any]:
            """
            Search for relevant documents.

            Args:
                query: Search query
                top_k: Number of results to return (default: 5)

            Returns:
                Dict with 'results' (list of chunks) and 'sources' (list of unique sources)
            """
            try:
                logger.info(f"RAG tool called: semantic_search(query='{query[:50]}...', top_k={top_k})")

                # Perform semantic search
                chunks = self.rag_service.semantic_search(
                    query_text=query,
                    top_k=top_k,
                    similarity_threshold=0.65  # Slightly relaxed for tool usage
                )

                # Extract unique sources
                sources = self.rag_service.extract_sources(chunks)

                # Format results for LLM
                results_for_llm = []
                for chunk in chunks:
                    results_for_llm.append({
                        "filename": chunk['filename'],
                        "page": chunk['page'],
                        "content": chunk['content'],
                        "similarity": round(chunk['similarity_score'], 3)
                    })

                return {
                    "query": query,
                    "results": results_for_llm,
                    "sources": sources,
                    "count": len(chunks)
                }

            except Exception as e:
                logger.error(f"Semantic search tool error: {e}")
                return {
                    "query": query,
                    "results": [],
                    "sources": [],
                    "count": 0,
                    "error": str(e)
                }

        tool = Tool(
            name="semantic_search",
            func=semantic_search_impl,
            description="""Search for relevant documents using semantic similarity.

Use this tool to find information from uploaded documents that's relevant to the user's question.
The tool will return the most relevant document chunks along with their sources.

Args:
    query (str): The search query or question to find relevant documents for
    top_k (int): Number of results to return (default: 5, max: 10)

Returns a dict with:
    - results: List of relevant document chunks with filename, page, and content
    - sources: List of unique document sources found
    - count: Number of results returned
"""
        )

        return tool

    def create_rag_tools_list(self) -> List[Tool]:
        """
        Create list of all RAG tools for LLM.

        Returns:
            List of Langchain Tool objects
        """
        tools = [
            self.create_semantic_search_tool(),
        ]

        logger.info(f"Created {len(tools)} RAG tools")
        return tools


def create_rag_tools(db: Session) -> List[Tool]:
    """
    Convenience function to create RAG tools.

    Args:
        db: Database session

    Returns:
        List of Langchain Tool objects
    """
    factory = RAGToolFactory(db)
    return factory.create_rag_tools_list()
