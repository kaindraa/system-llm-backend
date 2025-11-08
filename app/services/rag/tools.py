"""
Langchain Tools for RAG Integration

Defines tool definitions for LLM to call RAG functions.
"""

from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from sqlalchemy.orm import Session

from app.services.rag.rag_service import RAGService
from app.core.logging import get_logger

logger = get_logger(__name__)


class SemanticSearchInput(BaseModel):
    """Input schema for semantic search tool."""
    query: str = Field(..., description="The search query or question to find relevant documents for")
    top_k: int = Field(default=5, description="Number of results to return (default: 5, max: 10)")


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
            Search for relevant documents using semantic similarity.

            This tool searches through all available documents in the system
            to find content relevant to the user's query.

            Args:
                query: The search query or question (required, must not be empty)
                top_k: Maximum number of document chunks to return (default: 5, recommended: 3-10)

            Returns:
                Dictionary containing:
                - results: List of document chunks with content, filename, page number
                - sources: Unique document sources that were found
                - count: Number of results returned
                - error: Error message if search failed

            Example:
                If user asks "What is NAT?", search for documents explaining NAT.
                If user asks "Difference between X and Y", search for documents comparing them.
            """
            try:
                # Validate and constrain top_k
                if not isinstance(query, str) or not query.strip():
                    logger.error(f"Invalid query: empty or non-string (got: {repr(query)})")
                    raise ValueError("Query must be a non-empty string")

                top_k = max(1, min(int(top_k), 10))  # Constrain to 1-10

                logger.info(f"RAG tool called: semantic_search(query='{query}', top_k={top_k})")

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

        # Create wrapper to properly handle argument extraction from OpenAI tool calls
        def tool_wrapper(**kwargs) -> Dict[str, Any]:
            """Wrapper to handle OpenAI tool call format with flexible arg names."""
            # OpenAI sometimes uses __arg1, __arg2 for positional args
            # Extract query from either 'query' or '__arg1' key
            query = kwargs.get("query") or kwargs.get("__arg1")

            if not query:
                raise ValueError("query parameter is required")

            top_k = kwargs.get("top_k", 5)

            logger.debug(f"Tool wrapper received kwargs: {kwargs}, extracted query: {query}, top_k: {top_k}")

            return semantic_search_impl(query=query, top_k=top_k)

        # Create tool with explicit schema for better LLM understanding
        tool = Tool(
            name="semantic_search",
            func=tool_wrapper,
            args_schema=SemanticSearchInput,
            description="""Semantically search documents for information relevant to a question.

Use this tool whenever you need to find specific information from the uploaded documents.
Pass the user's question or search terms as the query parameter.

IMPORTANT: Always provide a clear, specific search query based on what the user is asking about.

Parameters:
    query (REQUIRED string): The search query or question. Examples: "What is NAT?", "explain OSPF", "speech processing"
    top_k (optional integer): Number of document chunks to return (default 5, max 10)

Returns a dictionary with:
    - results: List of matching document chunks with content, filename, page number
    - sources: Document files that contained matches
    - count: Number of results returned
    - error: Error message if something failed
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
