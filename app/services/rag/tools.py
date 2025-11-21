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
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return (default from config, max: from config)")


class RefinePromptInput(BaseModel):
    """Input schema for refine prompt tool."""
    original_prompt: str = Field(..., description="The original student question that needs refinement/clarification")


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
        Tool description is hardcoded (TAHAP 1) - no dynamic instruction needed since
        this tool doesn't call LLM in TAHAP 2 (just queries pgvector database).

        Returns:
            Langchain Tool object
        """
        # TAHAP 1: Tool description (hardcoded - used by LLM to decide whether to call this tool)
        semantic_search_description = (
            "Semantically search the knowledge base to find documents and information "
            "relevant to a question. Use this when you need to retrieve specific information "
            "from the available documents to answer a user's question."
        )

        def semantic_search_impl(query: str, top_k: int = None) -> Dict[str, Any]:
            """
            Search for relevant documents using semantic similarity.

            This tool searches through all available documents in the system
            to find content relevant to the user's query.

            Args:
                query: The search query or question (required, must not be empty)
                top_k: Maximum number of document chunks to return (None = use config default)

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
                # Validate query
                if not isinstance(query, str) or not query.strip():
                    logger.error(f"Invalid query: empty or non-string (got: {repr(query)})")
                    raise ValueError("Query must be a non-empty string")

                # Get config from RAG service
                config = self.rag_service.get_config()

                # Use provided top_k or fallback to config default
                if top_k is None:
                    top_k = config.get("default_top_k", 5)

                # Enforce max limit from config
                max_top_k = config.get("max_top_k", 10)
                top_k = max(1, min(int(top_k), max_top_k))

                logger.info(f"RAG tool called: semantic_search(query='{query}', top_k={top_k})")

                # Get similarity threshold from config (slightly relaxed for tool usage)
                similarity_threshold = max(config.get("similarity_threshold", 0.7) - 0.05, 0.0)

                # Perform semantic search
                chunks = self.rag_service.semantic_search(
                    query_text=query,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
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

            # Get top_k from kwargs, or None to let semantic_search_impl use config default
            top_k = kwargs.get("top_k")
            if top_k is not None:
                top_k = int(top_k)

            logger.debug(f"Tool wrapper received kwargs: {kwargs}, extracted query: {query}, top_k: {top_k}")

            return semantic_search_impl(query=query, top_k=top_k)

        # Create tool with TAHAP 1 description (hardcoded, no TAHAP 2 instruction needed)
        tool = Tool(
            name="semantic_search",
            func=tool_wrapper,
            args_schema=SemanticSearchInput,
            description=semantic_search_description  # TAHAP 1 - used by LLM to decide
        )

        return tool

    def create_refine_prompt_tool(self) -> Tool:
        """
        Create a Langchain tool for refining student prompts.

        The LLM can call this tool to refine/clarify ambiguous student questions.
        - TAHAP 1 (Tool Definition): Description is hardcoded below for consistency
        - TAHAP 2 (Tool Execution): Uses prompt_refine instruction from ChatConfig

        Returns:
            Langchain Tool object
        """
        # TAHAP 1: Tool description (hardcoded - used by LLM to decide whether to call this tool)
        refine_prompt_description = (
            "Refine and clarify an ambiguous or unclear student question.\n\n"
            "Use this tool when the student's question is vague, incomplete, or could be "
            "interpreted multiple ways. This will rewrite the question to be more specific "
            "and clearer for semantic search.\n\n"
            "IMPORTANT: Only use this tool if you think the question needs clarification before "
            "searching documents. If the question is already clear and specific, skip this tool "
            "and proceed directly to semantic_search."
        )

        # TAHAP 2: Get refine prompt instruction from ChatConfig (used during LLM execution)
        from app.models.chat_config import ChatConfig
        config = self.db.query(ChatConfig).filter(ChatConfig.id == 1).first()
        refine_prompt_template = config.prompt_refine if config and config.prompt_refine else (
            "Refine the student's question to be more specific and clear for better search results."
        )

        def refine_prompt_impl(original_prompt: str) -> Dict[str, Any]:
            """
            Refine a student's question using LLM.

            This tool helps clarify ambiguous or vague student questions into more
            specific and searchable questions before performing RAG search.

            Args:
                original_prompt: The original student question/prompt

            Returns:
                Dictionary containing:
                - original: Original prompt provided
                - refined: Refined/clarified version of the prompt
                - success: Whether refinement was successful

            Example:
                Input: "gimana loop?"
                Output: "Jelaskan perbedaan antara for loop dan while loop dalam Python"
            """
            try:
                from app.services.llm.llm_service import LLMService

                # ========== STEP 1: Validate Input ==========
                logger.info("="*80)
                logger.info("[REFINE_PROMPT] STEP 1: Validating input")
                if not isinstance(original_prompt, str) or not original_prompt.strip():
                    logger.error(f"[REFINE_PROMPT] ❌ Invalid prompt: empty or non-string (got: {repr(original_prompt)})")
                    raise ValueError("Prompt must be a non-empty string")
                logger.info(f"[REFINE_PROMPT] ✅ Input valid - length: {len(original_prompt)} characters")
                logger.debug(f"[REFINE_PROMPT] Original prompt: '{original_prompt}'")

                # ========== STEP 2: Setup LLM Service ==========
                logger.info("[REFINE_PROMPT] STEP 2: Initializing LLM service")
                llm_service = LLMService(db=self.db)
                logger.info("[REFINE_PROMPT] ✅ LLM service initialized")

                # ========== STEP 3: Prepare System & User Messages ==========
                logger.info("[REFINE_PROMPT] STEP 3: Preparing messages for LLM")
                logger.debug(f"[REFINE_PROMPT] System prompt length: {len(refine_prompt_template)} characters")
                logger.debug(f"[REFINE_PROMPT] System prompt content:\n{refine_prompt_template[:200]}...")

                messages = [
                    {
                        "role": "system",
                        "content": refine_prompt_template
                    },
                    {
                        "role": "user",
                        "content": original_prompt
                    }
                ]
                logger.info("[REFINE_PROMPT] ✅ Messages prepared (1 system + 1 user message)")

                # ========== STEP 4: Call LLM to Refine Prompt ==========
                logger.info("[REFINE_PROMPT] STEP 4: Calling LLM to refine prompt")
                logger.info("[REFINE_PROMPT] Model: gpt-4.1-nano (fast & efficient)")

                import asyncio
                logger.info("[REFINE_PROMPT] 🔄 Sending request to LLM...")

                try:
                    # Try to use existing event loop if running, otherwise create new one
                    try:
                        loop = asyncio.get_running_loop()
                        logger.debug("[REFINE_PROMPT] Using existing event loop")
                        # If there's already a running loop, we need to run in executor
                        import concurrent.futures
                        import threading

                        def run_async():
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                return new_loop.run_until_complete(
                                    llm_service.generate_async(
                                        model_id="gpt-4.1-nano",
                                        messages=messages
                                    )
                                )
                            finally:
                                new_loop.close()

                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            refined_prompt = executor.submit(run_async).result()
                    except RuntimeError:
                        # No event loop running, create one
                        logger.debug("[REFINE_PROMPT] Creating new event loop")
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            refined_prompt = loop.run_until_complete(
                                llm_service.generate_async(
                                    model_id="gpt-4.1-nano",
                                    messages=messages
                                )
                            )
                        finally:
                            loop.close()

                    logger.info("[REFINE_PROMPT] ✅ LLM response received successfully")
                except Exception as e:
                    logger.error(f"[REFINE_PROMPT] ❌ LLM call failed: {str(e)}")
                    raise

                # ========== STEP 5: Return Result ==========
                logger.info("[REFINE_PROMPT] STEP 5: Processing result")
                logger.debug(f"[REFINE_PROMPT] Refined prompt: '{refined_prompt}'")
                logger.info(f"[REFINE_PROMPT] ✅ Refinement successful")
                logger.info(f"[REFINE_PROMPT] Original length: {len(original_prompt)} → Refined length: {len(refined_prompt)}")
                logger.info("="*80)

                return {
                    "original": original_prompt,
                    "refined": refined_prompt,
                    "success": True
                }

            except Exception as e:
                logger.error("="*80)
                logger.error(f"[REFINE_PROMPT] ❌ ERROR during execution")
                logger.error(f"[REFINE_PROMPT] Error type: {type(e).__name__}")
                logger.error(f"[REFINE_PROMPT] Error message: {str(e)}")
                logger.error(f"[REFINE_PROMPT] Original prompt: '{original_prompt}'", exc_info=True)
                logger.error("="*80)

                return {
                    "original": original_prompt,
                    "refined": original_prompt,  # Return original if refinement fails
                    "success": False,
                    "error": str(e)
                }

        # Create wrapper to handle tool call format
        def tool_wrapper(**kwargs) -> Dict[str, Any]:
            """Wrapper to handle OpenAI tool call format."""
            logger.info("[REFINE_PROMPT_WRAPPER] Tool called by LLM")
            logger.debug(f"[REFINE_PROMPT_WRAPPER] Raw kwargs: {kwargs}")

            # Extract original_prompt from either 'original_prompt' or '__arg1' (OpenAI format)
            original_prompt = kwargs.get("original_prompt") or kwargs.get("__arg1")

            if not original_prompt:
                logger.error("[REFINE_PROMPT_WRAPPER] ❌ original_prompt parameter missing")
                raise ValueError("original_prompt parameter is required")

            logger.info(f"[REFINE_PROMPT_WRAPPER] ✅ Extracted prompt (length: {len(original_prompt)} chars)")
            logger.debug(f"[REFINE_PROMPT_WRAPPER] Forwarding to refine_prompt_impl...")

            return refine_prompt_impl(original_prompt=original_prompt)

        # Create tool with explicit schema
        tool = Tool(
            name="refine_prompt",
            func=tool_wrapper,
            args_schema=RefinePromptInput,
            description=refine_prompt_description  # TAHAP 1 - used by LLM to decide
        )

        return tool

    def create_rag_tools_list(self) -> List[Tool]:
        """
        Create list of all RAG tools for LLM.

        Returns:
            List of Langchain Tool objects
        """
        tools = [
            self.create_refine_prompt_tool(),
            self.create_semantic_search_tool(),
        ]

        logger.info(f"Created {len(tools)} RAG tools: {[t.name for t in tools]}")
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
