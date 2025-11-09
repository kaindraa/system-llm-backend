"""
Chat Service

Handles chat session management, message storage, and conversation flow.
Integrates with LLM service for generating responses.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from app.models.chat_session import ChatSession, SessionStatus
from app.models.model import Model
from app.models.prompt import Prompt
from app.models.chat_config import ChatConfig
from app.services.llm import LLMService
from app.services.rag import RAGService, create_rag_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for managing chat sessions and conversations."""

    def __init__(self, db: Session, llm_service: Optional[LLMService] = None):
        self.db = db
        # Use provided singleton or create new instance for testing
        self.llm_service = llm_service if llm_service else LLMService(db=db)

    def create_session(
        self,
        user_id: UUID,
        model_id: str,
        title: Optional[str] = None,
        prompt_id: Optional[UUID] = None,
        prompt_general: Optional[str] = None,
        task: Optional[str] = None,
        persona: Optional[str] = None,
        mission_objective: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session.

        If prompt_id is not provided, automatically uses the active prompt.
        """
        model = self._get_model(model_id)
        if not model:
            raise ValueError(f"Model '{model_id}' not found")

        # If no prompt_id provided, try to use active prompt
        if not prompt_id:
            active_prompt = self.db.query(Prompt).filter(Prompt.is_active == True).first()
            if active_prompt:
                prompt_id = active_prompt.id
                logger.info(f"Using active prompt: {active_prompt.name} (ID: {prompt_id})")
            else:
                logger.info("No active prompt found, creating session without prompt")
        else:
            # Verify provided prompt exists
            prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
            if not prompt:
                raise ValueError(f"Prompt with ID '{prompt_id}' not found")
            logger.info(f"Using provided prompt: {prompt.name} (ID: {prompt_id})")

        session = ChatSession(
            user_id=user_id,
            model_id=model.id,
            title=title or f"Chat with {model.display_name}",
            prompt_id=prompt_id,
            messages=[],
            status=SessionStatus.ACTIVE,
            total_messages=0,
            prompt_general=prompt_general,
            task=task,
            persona=persona,
            mission_objective=mission_objective
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Log session creation with all prompt fields
        logger.info(f"[SERVICE] Created chat session {session.id} for user {user_id}")
        logger.info("[SERVICE] Session Prompt Configuration:")
        logger.info(f"  - prompt_id (from Prompt table): {session.prompt_id}")
        logger.info(f"  - prompt_general: {session.prompt_general if session.prompt_general else '(not set)'}")
        logger.info(f"  - task: {session.task if session.task else '(not set)'}")
        logger.info(f"  - persona: {session.persona if session.persona else '(not set)'}")
        logger.info(f"  - mission_objective: {session.mission_objective if session.mission_objective else '(not set)'}")

        return session

    def get_session(self, session_id: UUID, user_id: UUID) -> Optional[ChatSession]:
        """Get a chat session by ID."""
        session = (
            self.db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
            .first()
        )
        return session

    def list_sessions(
        self,
        user_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatSession]:
        """List chat sessions for a user."""
        query = self.db.query(ChatSession).filter(ChatSession.user_id == user_id)

        if status:
            query = query.filter(ChatSession.status == status)

        sessions = (
            query
            .order_by(ChatSession.started_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return sessions

    def update_session(
        self,
        session_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        status: Optional[SessionStatus] = None
    ) -> Optional[ChatSession]:
        """Update a chat session."""
        session = self.get_session(session_id, user_id)
        if not session:
            return None

        if title is not None:
            session.title = title

        if status is not None:
            session.status = status
            if status == SessionStatus.COMPLETED:
                session.ended_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Updated session {session_id}")
        return session

    def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """Delete a chat session."""
        session = self.get_session(session_id, user_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()

        logger.info(f"Deleted session {session_id}")
        return True

    async def send_message(
        self,
        session_id: UUID,
        user_id: UUID,
        message_content: str,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message in a chat session and get LLM response."""
        session = self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session {session_id} is not active")

        # Build conversation context to get system prompt
        conversation_context = self._build_conversation_context(session)

        # Extract system message from context (first message with role: "system")
        system_message = None
        if conversation_context and conversation_context[0].get("role") == "system":
            system_message = {
                "role": "system",
                "content": conversation_context[0]["content"],
                "created_at": datetime.utcnow().isoformat(),
                "sources": None
            }

        user_message = {
            "role": "user",
            "content": message_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": None
        }

        conversation_context.append({
            "role": "user",
            "content": message_content
        })

        logger.info(f"Session {session_id}: Sending message to LLM (context: {len(conversation_context)} msgs)")

        try:
            assistant_content = await self.llm_service.generate_async(
                model_id=str(session.model_id),
                messages=conversation_context,
                api_key=api_key
            )
        except Exception as e:
            logger.error(f"LLM error in session {session_id}: {str(e)}")
            raise

        assistant_message = {
            "role": "assistant",
            "content": assistant_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": None
        }

        # Add system message only if it's the first message (not already in session)
        if system_message and len(session.messages) == 0:
            session.messages.append(system_message)

        session.messages.append(user_message)
        session.messages.append(assistant_message)
        session.total_messages = len(session.messages)

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(session, "messages")

        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Session {session_id}: Message exchange completed (total: {len(session.messages)})")

        return {
            "user_message": user_message,
            "assistant_message": assistant_message
        }

    def _build_conversation_context(self, session: ChatSession, include_rag_instruction: Optional[bool] = None) -> List[Dict[str, str]]:
        """
        Build conversation context from session messages.

        Concatenates prompt sources with structured format:
        - Student Learning Profile section (task, persona, mission_objective)
        - Teacher's Specific Prompt section (prompt_general + prompt from Prompt table)

        Args:
            session: Chat session
            include_rag_instruction: Whether to add RAG instruction to system prompt (None = use database config)
        """
        context = []

        # Build concatenated system prompt with structured format
        prompt_sections = []

        # SECTION 1: General Prompt (top priority)
        if session.prompt_general:
            prompt_sections.append(f"# General Prompt\n{session.prompt_general}")

        # SECTION 2: Student Learning Profile
        student_profile = []
        if session.task:
            student_profile.append(f"# Task\n{session.task}")
        if session.persona:
            student_profile.append(f"# Persona\n{session.persona}")
        if session.mission_objective:
            student_profile.append(f"# Mission Objective\n{session.mission_objective}")

        if student_profile:
            prompt_sections.append("Student Learning Profile\n" + "\n\n".join(student_profile))

        # SECTION 3: Specific Prompt (from Prompt table - lowest priority/specific)
        if session.prompt_id:
            prompt = self.db.query(Prompt).filter(Prompt.id == session.prompt_id).first()
            if prompt:
                prompt_sections.append(f"# Specific Prompt\n{prompt.content}")

        # Concatenate sections with double newline separator
        system_content = "\n\n".join(prompt_sections) if prompt_sections else ""

        # Get RAG instruction setting from database if not explicitly provided
        if include_rag_instruction is None:
            try:
                rag_service = RAGService(self.db)
                config = rag_service.get_config()
                include_rag_instruction = config.get("include_rag_instruction", True)
            except Exception as e:
                logger.warning(f"Failed to load RAG config, using default include_rag_instruction=True: {e}")
                include_rag_instruction = True

        # RAG instruction is now included in prompt_general (Teacher's Specific Prompt)
        # No additional RAG instruction appended here

        # Log the complete concatenated system prompt
        if system_content:
            logger.info(f"[CONTEXT] Session {session.id} - Building conversation context")
            logger.info("=" * 100)
            logger.info("[FINAL SYSTEM PROMPT (Concatenated)]:")
            logger.info("-" * 100)
            logger.info(system_content)
            logger.info("-" * 100)
            logger.info("=" * 100)

        if system_content:
            context.append({
                "role": "system",
                "content": system_content
            })

        # Add conversation history
        for msg in session.messages:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        return context

    def _get_model(self, model_id: str) -> Optional[Model]:
        """Get model from database by ID or name."""
        try:
            uuid_obj = UUID(model_id)
            model = self.db.query(Model).filter(Model.id == uuid_obj).first()
            if model:
                return model
        except (ValueError, AttributeError):
            pass

        model = self.db.query(Model).filter(Model.name == model_id).first()
        return model

    def get_session_context(self, session_id: UUID, user_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """Get the full conversation context for a session."""
        session = self.get_session(session_id, user_id)
        if not session:
            return None

        return session.messages

    async def send_message_stream(
        self,
        session_id: UUID,
        user_id: UUID,
        message_content: str,
        api_key: Optional[str] = None,
        use_rag: bool = True
    ):
        """
        Send a message in a chat session and stream LLM response.

        Can optionally use RAG tool calling: LLM can call semantic_search to find
        relevant documents, then generates response with document context.

        Args:
            session_id: Chat session ID
            user_id: User ID
            message_content: User's message content
            api_key: Optional API key for LLM provider
            use_rag: Enable RAG tool calling (default: True)

        Yields:
            Dict with 'type' and 'content':
            - {'type': 'user_message', 'content': {...}}
            - {'type': 'rag_search', 'content': {...}} (only if use_rag=True)
            - {'type': 'chunk', 'content': 'text chunk'}
            - {'type': 'done', 'content': {...}}

        Raises:
            ValueError: If session not found or not active
        """
        session = self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Session {session_id} is not active")

        # Build conversation context to get system prompt
        conversation_context = self._build_conversation_context(session)

        # Extract system message from context (first message with role: "system")
        system_message = None
        if conversation_context and conversation_context[0].get("role") == "system":
            system_message = {
                "role": "system",
                "content": conversation_context[0]["content"],
                "created_at": datetime.utcnow().isoformat(),
                "sources": None
            }

        # Create user message
        user_message = {
            "role": "user",
            "content": message_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": None
        }

        # Yield user message first
        yield {"type": "user_message", "content": user_message}

        # Add user message to conversation context
        conversation_context.append({
            "role": "user",
            "content": message_content
        })

        logger.info(
            f"Session {session_id}: Streaming message (rag={use_rag}, context: {len(conversation_context)} msgs)"
        )

        # Initialize variables
        full_content = ""
        sources_list = []

        try:
            if use_rag:
                # --- RAG Mode: Tool Calling ---
                # Create RAG tools
                rag_tools = create_rag_tools(self.db)

                # Get LLM provider for tool calling
                provider = self.llm_service.get_provider(str(session.model_id), api_key=api_key)

                # Use tool calling with RAG
                async for event in provider.agenerate_stream_with_tools(
                    messages=conversation_context,
                    tools=rag_tools
                ):
                    event_type = event.get("type")
                    event_content = event.get("content")

                    if event_type == "tool_call":
                        # LLM is calling a tool
                        tool_name = event_content.get("tool_name")
                        tool_input = event_content.get("tool_input", {})

                        # Extract query from tool_input (handle different possible formats)
                        if isinstance(tool_input, dict):
                            query = tool_input.get("query", "")
                        else:
                            query = str(tool_input) if tool_input else ""

                        logger.info(f"Tool '{tool_name}' called with input: {tool_input}")

                        yield {
                            "type": "rag_search",
                            "content": {
                                "query": query,
                                "status": "searching"
                            }
                        }

                    elif event_type == "tool_result":
                        # Tool executed and returned result
                        tool_name = event_content.get("tool_name")
                        result = event_content.get("result")
                        error = event_content.get("error")

                        if error:
                            logger.warning(f"Tool {tool_name} error: {error}")
                        else:
                            logger.debug(f"Tool {tool_name} returned {result.get('count', 0)} results")

                            # Extract sources from tool result
                            if isinstance(result, dict):
                                tool_sources = result.get("sources", [])
                                sources_list.extend(tool_sources)

                                yield {
                                    "type": "rag_search",
                                    "content": {
                                        "query": result.get("query", ""),
                                        "results_count": result.get("count", 0),
                                        "status": "completed"
                                    }
                                }

                    elif event_type == "chunk":
                        # Streaming text response from LLM
                        chunk_content = event_content
                        full_content += chunk_content
                        yield {"type": "chunk", "content": chunk_content}

            else:
                # --- Regular Mode: No RAG ---
                async for chunk in self.llm_service.generate_stream(
                    model_id=str(session.model_id),
                    messages=conversation_context,
                    api_key=api_key
                ):
                    full_content += chunk
                    yield {"type": "chunk", "content": chunk}

        except Exception as e:
            logger.error(f"LLM error in session {session_id}: {str(e)}")
            raise

        # Remove duplicate sources (by document_id and page)
        unique_sources = []
        if use_rag and sources_list:
            seen = set()
            for source in sources_list:
                key = (source.get("document_id"), source.get("page"))
                if key not in seen:
                    unique_sources.append(source)
                    seen.add(key)

        # Create assistant message with full content and sources
        assistant_message = {
            "role": "assistant",
            "content": full_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": unique_sources if unique_sources else None
        }

        # Save messages to database
        # Add system message only if it's the first message (not already in session)
        if system_message and len(session.messages) == 0:
            session.messages.append(system_message)

        session.messages.append(user_message)
        session.messages.append(assistant_message)
        session.total_messages = len(session.messages)

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(session, "messages")

        self.db.commit()
        self.db.refresh(session)

        logger.info(
            f"Session {session_id}: Streaming completed (total: {len(session.messages)}, "
            f"sources: {len(unique_sources)})"
        )

        # Yield done signal with assistant message
        yield {"type": "done", "content": assistant_message}

    async def analyze_session(
        self,
        session_id: UUID,
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a completed chat session.

        Generates summary and comprehension level assessment based on conversation history.
        Saves results to database columns: summary, comprehension_level (as string: "low"/"medium"/"high"), analyzed_at.

        Args:
            session_id: Chat session ID
            user_id: User ID

        Returns:
            Dict with analysis results or None if session not found
        """
        session = self.get_session(session_id, user_id)
        if not session:
            return None

        if not session.messages:
            raise ValueError(f"Session {session_id} has no messages to analyze")

        try:
            # Get analysis prompt from ChatConfig
            chat_config = self.db.query(ChatConfig).filter(ChatConfig.id == 1).first()
            if not chat_config or not chat_config.prompt_analysis:
                raise ValueError("Analysis prompt not configured in ChatConfig")

            # Build analysis context
            # Convert messages to readable format
            messages_text = self._format_messages_for_analysis(session.messages)

            # Prepare analysis prompt with conversation history
            analysis_context = [
                {
                    "role": "system",
                    "content": chat_config.prompt_analysis
                },
                {
                    "role": "user",
                    "content": f"Please analyze the following chat session and provide summary and comprehension level assessment:\n\n{messages_text}"
                }
            ]

            logger.info(f"[ANALYSIS] Session {session_id}: Starting analysis...")

            # Call LLM to generate analysis
            analysis_json = await self.llm_service.generate_async(
                model_id=str(session.model_id),
                messages=analysis_context
            )

            logger.info(f"[ANALYSIS] Session {session_id}: Raw LLM response received")

            # Parse LLM response as JSON
            import json
            analysis_data = json.loads(analysis_json)

            # Extract summary and comprehension_level from LLM response
            summary = analysis_data.get("summary", "").strip()
            comprehension_level_raw = analysis_data.get("comprehension_level", "")

            # Ensure lowercase
            if isinstance(comprehension_level_raw, str):
                comprehension_level_raw = comprehension_level_raw.strip().lower()
            else:
                comprehension_level_raw = str(comprehension_level_raw).strip().lower()

            logger.info(f"[ANALYSIS] Extracted level: '{comprehension_level_raw}' (type: {type(comprehension_level_raw).__name__})")

            # Validate
            if not summary or not comprehension_level_raw:
                raise ValueError("Invalid analysis response from LLM")

            if comprehension_level_raw not in ["low", "medium", "high"]:
                raise ValueError(f"Invalid comprehension level: {comprehension_level_raw}")

            # Save to database columns
            session.summary = summary
            logger.info(f"[ANALYSIS] Saving to database with level: {comprehension_level_raw}")
            # Store comprehension_level as lowercase string ("low", "medium", "high")
            session.comprehension_level = comprehension_level_raw
            session.status = "analyzed"  # Update status to analyzed
            session.ended_at = datetime.utcnow()
            session.analyzed_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(session)

            logger.info(f"[ANALYSIS] Session {session_id}: Analysis completed - Level: {comprehension_level_raw}")

            return {
                "session_id": session.id,
                "summary": summary,
                "comprehension_level": comprehension_level_raw.upper(),
                "analyzed_at": datetime.utcnow().isoformat()
            }

        except json.JSONDecodeError as e:
            logger.error(f"[ANALYSIS] Session {session_id}: Failed to parse LLM response as JSON: {str(e)}")
            raise ValueError("LLM response could not be parsed as JSON")
        except Exception as e:
            logger.error(f"[ANALYSIS] Session {session_id}: Error during analysis: {str(e)}", exc_info=True)
            raise

    def _format_messages_for_analysis(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format messages array into readable text for analysis.

        Args:
            messages: List of message dicts from session.messages

        Returns:
            Formatted text representation of conversation
        """
        formatted = []

        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")

            if role == "SYSTEM":
                continue  # Skip system messages in formatted output

            formatted.append(f"{role}: {content}")

        return "\n\n".join(formatted)
