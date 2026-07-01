"""
Chat Service

Handles chat session management, message storage, and conversation flow.
Integrates with LLM service for generating responses.
"""

import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from app.models.chat_session import ChatSession, SessionStatus
from app.models.model import Model
from app.models.prompt import Prompt
from app.models.user import User
from app.models.chat_config import ChatConfig
from app.services.llm import LLMService
from app.services.rag import RAGService, create_rag_tools
from app.services.rag_config_service import ChatConfigService
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

        user = None
        if prompt_general is None or task is None or persona is None or mission_objective is None:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User '{user_id}' not found")

        if prompt_general is None:
            try:
                prompt_general = ChatConfigService(self.db).get_config().prompt_general
            except Exception as e:
                logger.warning(f"Failed to load chat config for prompt_general: {e}")

        if user:
            if task is None:
                task = user.task
            if persona is None:
                persona = user.persona
            if mission_objective is None:
                mission_objective = user.mission_objective

        session = ChatSession(
            user_id=user_id,
            model_id=model.id,
            title=title or f"Chat with {model.display_name}",
            prompt_id=prompt_id,
            messages=[],
            status=SessionStatus.ACTIVE.value,  # Convert enum to string value
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

    def _get_chat_runtime_config(self) -> Dict[str, Any]:
        """Load chat runtime config with safe fallbacks for latency-sensitive paths."""
        defaults = {
            "tool_calling_enabled": True,
            "tool_calling_max_iterations": 4,
        }
        try:
            config = ChatConfigService(self.db).get_config_dict()
            return {
                "tool_calling_enabled": config.get("tool_calling_enabled", True),
                "tool_calling_max_iterations": max(
                    1,
                    min(int(config.get("tool_calling_max_iterations", 4)), 4),
                ),
            }
        except Exception as e:
            logger.warning(f"Failed to load chat runtime config, using defaults: {e}")
            return defaults

    @staticmethod
    def _is_small_talk_message(message: str) -> bool:
        """
        Skip RAG/tool-calling for trivial conversational turns that do not benefit
        from retrieval and only add latency.
        """
        normalized = " ".join(message.lower().split())
        trivial_messages = {
            "hi",
            "hello",
            "hey",
            "halo",
            "hai",
            "ok",
            "oke",
            "sip",
            "siap",
            "thanks",
            "thank you",
            "terima kasih",
            "makasih",
            "lanjut",
            "lanjutkan",
            "ya",
            "iya",
            "yes",
            "no",
        }
        return normalized in trivial_messages

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
            # Convert enum to string value for database comparison
            status_value = status.value if isinstance(status, SessionStatus) else status
            query = query.filter(ChatSession.status == status_value)

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
            # Convert enum to string value for database storage
            status_value = status.value if isinstance(status, SessionStatus) else status
            session.status = status_value
            # Mark session as ended if status changed to ANALYZED
            if status_value == SessionStatus.ANALYZED.value:
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

        if session.status != SessionStatus.ACTIVE.value:
            raise ValueError(f"Session {session_id} is not active")

        # Build conversation context to get system prompt
        conversation_context = self._build_conversation_context(session)

        # Extract system message from context (first message with role: "system")
        # MINIMAL format - ONLY role + content for interaction_messages
        system_message = None
        if conversation_context and conversation_context[0].get("role") == "system":
            system_message = {
                "role": "system",
                "content": conversation_context[0]["content"]
            }

        # MINIMAL format - ONLY role + content for interaction_messages
        user_message = {
            "role": "user",
            "content": message_content
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

        # MINIMAL format - ONLY role + content for interaction_messages
        assistant_message = {
            "role": "assistant",
            "content": assistant_content
        }

        # Save to BOTH interaction_messages (minimal format) and legacy messages column

        # INTERACTION_MESSAGES (minimal: ONLY role + content)
        interaction_to_save = []
        if system_message and len(session.interaction_messages) == 0:
            interaction_to_save.append(system_message)
        interaction_to_save.append(user_message)
        interaction_to_save.append(assistant_message)
        session.interaction_messages.extend(interaction_to_save)

        # LEGACY messages column (for backward compatibility)
        if system_message and len(session.messages) == 0:
            session.messages.append(system_message)
        session.messages.append(user_message)
        session.messages.append(assistant_message)

        session.total_messages = len(session.interaction_messages)

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(session, "interaction_messages")
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

        if session.status != SessionStatus.ACTIVE.value:
            raise ValueError(f"Session {session_id} is not active")

        # Build conversation context to get system prompt
        conversation_context = self._build_conversation_context(session)

        # Extract system message from context (first message with role: "system")
        system_message = None
        if conversation_context and conversation_context[0].get("role") == "system":
            system_message = {
                "role": "system",
                "content": conversation_context[0]["content"]
            }

        # Create user message (MINIMAL format - ONLY role + content for interaction_messages)
        user_message = {
            "role": "user",
            "content": message_content
        }

        # Yield user message first
        yield {"type": "user_message", "content": user_message}

        # Add user message to conversation context
        conversation_context.append({
            "role": "user",
            "content": message_content
        })

        # Initialize variables
        full_content = ""
        sources_list = []
        real_messages_list = []  # Track for real_messages column (Option A: User original)
        tool_messages = []  # Track tool calls and results for real_messages
        tools_used = []  # Track tools actually executed, for the "done" event (frontend "Completed · Used" badge)

        # Build real_messages (Option A: User message ORIGINAL)
        # Add system message to real_messages only if first message
        if system_message and len(session.interaction_messages) == 0:
            real_messages_list.append({
                "role": "system",
                "content": system_message["content"],
                "created_at": datetime.utcnow().isoformat()
            })
            logger.debug(f"[REAL_MESSAGES] Added system message")

        # Add user message to real_messages (ORIGINAL - not refined)
        real_messages_list.append({
            "role": "user",
            "content": message_content,  # ORIGINAL user input
            "created_at": datetime.utcnow().isoformat()
        })
        logger.debug(f"[REAL_MESSAGES] Added user message (original): {message_content[:50]}...")

        runtime_config = self._get_chat_runtime_config()
        use_tools = (
            use_rag
            and runtime_config["tool_calling_enabled"]
            and not self._is_small_talk_message(message_content)
        )

        try:
            if use_tools:
                # --- RAG Mode: Tool Calling ---
                # Create RAG tools
                rag_tools = create_rag_tools(self.db)

                # Get LLM provider for tool calling
                provider = self.llm_service.get_provider(str(session.model_id), api_key=api_key)

                # Use tool calling with RAG
                async for event in provider.agenerate_stream_with_tools(
                    messages=conversation_context,
                    tools=rag_tools,
                    max_iterations=runtime_config["tool_calling_max_iterations"],
                ):
                    event_type = event.get("type")
                    event_content = event.get("content")

                    if event_type == "tool_call":
                        # LLM is calling a tool
                        tool_name = event_content.get("tool_name")
                        tool_input = event_content.get("tool_input", {})

                        # IMPORTANT: Transform generic tool_call events to specific event types
                        # This is needed because some providers (OpenAI) only emit generic "tool_call" events
                        # Different event types for different tools
                        if tool_name == "refine_prompt":
                            # Extract original_prompt from tool_input
                            if isinstance(tool_input, dict):
                                original_prompt = tool_input.get("original_prompt", "")
                            else:
                                original_prompt = str(tool_input) if tool_input else ""

                            logger.info(f"[CHAT_SERVICE] TRANSFORMING tool_call → refine_prompt event")
                            logger.info(f"[REFINE_PROMPT_EVENT] Yielding refine_prompt event with prompt: '{original_prompt}'")
                            # Forward the event before tool execution (TAHAP 1)
                            event_to_yield = {
                                "type": "refine_prompt",
                                "content": {
                                    "original_prompt": original_prompt,
                                    "status": "refining"
                                }
                            }
                            yield event_to_yield
                        elif tool_name == "semantic_search":
                            # Extract query from tool_input (handle different possible formats)
                            if isinstance(tool_input, dict):
                                query = tool_input.get("query", "")
                            else:
                                query = str(tool_input) if tool_input else ""

                            # Forward the event before tool execution (TAHAP 1)
                            yield {
                                "type": "rag_search",
                                "content": {
                                    "query": query,
                                    "status": "searching"
                                }
                            }
                        else:
                            # Default for other tools
                            yield {
                                "type": "tool_call",
                                "content": {
                                    "tool_name": tool_name,
                                    "status": "executing"
                                }
                            }

                    elif event_type == "refine_prompt_result":
                        # Refine prompt tool executed and returned refined question
                        tool_name = event_content.get("tool_name")
                        result = event_content.get("result")
                        error = event_content.get("error")

                        if error:
                            logger.warning(f"[REFINE_PROMPT_RESULT] Tool {tool_name} error: {error}")
                            event_to_yield = {
                                "type": "refine_prompt_result",
                                "content": {
                                    "original": result.get("original", "") if isinstance(result, dict) else "",
                                    "refined": result.get("original", "") if isinstance(result, dict) else "",  # Return original on error
                                    "success": False,
                                    "error": error
                                }
                            }
                        else:
                            if isinstance(result, dict):
                                original = result.get("original", "")
                                refined = result.get("refined", "")
                                success = result.get("success", True)
                            else:
                                original = str(result)
                                refined = str(result)
                                success = True
                                logger.warning(f"[REFINE_PROMPT_RESULT] Result is not dict: {result}")

                            event_to_yield = {
                                "type": "refine_prompt_result",
                                "content": {
                                    "original": original,
                                    "refined": refined,
                                    "success": success
                                }
                            }

                            # Add to real_messages (Option A)
                            # First add the tool_call message
                            if not any(msg.get("role") == "assistant" and msg.get("tool_calls") for msg in real_messages_list):
                                # Add assistant message with tool_calls if not already there
                                real_messages_list.append({
                                    "role": "assistant",
                                    "content": "",
                                    "created_at": datetime.utcnow().isoformat(),
                                    "tool_calls": [{"name": tool_name, "args": {"original_prompt": original}}]
                                })

                            # Then add tool message with result
                            import json
                            real_messages_list.append({
                                "role": "tool",
                                "content": json.dumps({
                                    "original": original,
                                    "refined": refined,
                                    "success": success
                                }, ensure_ascii=False),
                                "created_at": datetime.utcnow().isoformat(),
                                "tool_call_id": f"tool_call_{tool_name}"
                            })
                            logger.debug(f"[REAL_MESSAGES] Added tool message for {tool_name}")

                        if "refine_prompt" not in tools_used:
                            tools_used.append("refine_prompt")

                        yield event_to_yield

                    elif event_type == "rag_search_result":
                        # RAG/semantic_search tool executed and returned results
                        tool_name = event_content.get("tool_name")
                        result = event_content.get("result")
                        error = event_content.get("error")

                        if error:
                            logger.warning(f"Tool {tool_name} error: {error}")
                        else:
                            results_count = result.get('count', 0) if isinstance(result, dict) else 0

                            # Extract sources from tool result
                            if isinstance(result, dict):
                                tool_sources = result.get("sources", [])
                                sources_list.extend(tool_sources)

                                # Add to real_messages (Option A) - CHUNKS ARE HERE!
                                import json

                                # First add the tool_call message for semantic_search
                                search_query = result.get("query", "")
                                real_messages_list.append({
                                    "role": "assistant",
                                    "content": "",
                                    "created_at": datetime.utcnow().isoformat(),
                                    "tool_calls": [{"name": tool_name, "args": {"query": search_query}}]
                                })
                                logger.debug(f"[REAL_MESSAGES] Added tool_call for {tool_name}")

                                # Prepare chunks data - normalize structure
                                # Provider might return "results" or "chunks" field, standardize to "chunks"
                                chunks = result.get("chunks") or result.get("results", [])

                                # Create standardized result for storage
                                standardized_result = {
                                    "query": result.get("query", ""),
                                    "chunks": chunks,
                                    "sources": result.get("sources", []),
                                    "count": result.get("count", len(chunks))
                                }

                                # Then add tool message with chunks result - THIS IS WHERE CHUNKS ARE PRESERVED!
                                real_messages_list.append({
                                    "role": "tool",
                                    "content": json.dumps(standardized_result, ensure_ascii=False, indent=2),  # FULL result dengan chunks
                                    "created_at": datetime.utcnow().isoformat(),
                                    "tool_call_id": f"tool_call_{tool_name}"
                                })
                                logger.info(f"[REAL_MESSAGES] Added ToolMessage with {results_count} chunks (CHUNKS PRESERVED HERE!)")

                                event_to_yield = {
                                    "type": "rag_search",
                                    "content": {
                                        "query": result.get("query", ""),
                                        "results_count": result.get("count", 0),
                                        "status": "completed"
                                    }
                                }
                                if "semantic_search" not in tools_used:
                                    tools_used.append("semantic_search")

                                yield event_to_yield

                    elif event_type == "tool_result":
                        # Tool executed and returned result (fallback for other tools)
                        tool_name = event_content.get("tool_name")
                        result = event_content.get("result")
                        error = event_content.get("error")

                        if error:
                            logger.warning(f"Tool {tool_name} error: {error}")
                        else:
                            logger.debug(f"Tool {tool_name} executed successfully")

                            # Also extract sources for semantic_search tool in tool_result event
                            if tool_name == "semantic_search" and isinstance(result, dict):
                                tool_sources = result.get("sources", [])
                                sources_list.extend(tool_sources)

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

        # Remove duplicate sources (by document_id and page) and normalize field names
        unique_sources = []
        if use_tools and sources_list:
            seen = set()
            for source in sources_list:
                # Normalize field names for consistency with frontend
                # RAG service returns: document_id, filename, page, similarity_score
                # Frontend expects: document_id, document_name, page_number, similarity_score
                normalized = {
                    "document_id": source.get("document_id", ""),
                    "document_name": source.get("filename") or source.get("document_name", "Document"),  # Support both field names
                    "page_number": source.get("page") or source.get("page_number", 1),  # Support both field names
                    "similarity_score": source.get("similarity_score", 0.85)
                }
                key = (normalized["document_id"], normalized["page_number"])
                if key not in seen:
                    unique_sources.append(normalized)
                    seen.add(key)

        # Create assistant message (MINIMAL format - ONLY role + content for interaction_messages)
        assistant_message = {
            "role": "assistant",
            "content": full_content
        }

        # Build real_messages: Add final assistant message with sources
        real_messages_list.append({
            "role": "assistant",
            "content": full_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": unique_sources if unique_sources else None
        })
        logger.debug(f"[REAL_MESSAGES] Added final assistant message")

        # Save messages to database (populate BOTH columns)
        # NOTE:
        # - interaction_messages: Simple format (system, user, assistant) - for display
        # - real_messages: Full format (with tool messages for Option A) - for exact replay
        # - messages: Legacy column (for backward compatibility)

        # INTERACTION_MESSAGES (Simple format for display)
        interaction_messages_to_save = []

        # Add system message only if it's the first message
        if system_message and len(session.interaction_messages) == 0:
            interaction_messages_to_save.append(system_message)

        interaction_messages_to_save.append(user_message)
        interaction_messages_to_save.append(assistant_message)

        # Append to interaction_messages
        session.interaction_messages.extend(interaction_messages_to_save)
        # REAL_MESSAGES (Full format with tools for Option A)
        session.real_messages.extend(real_messages_list)

        # LEGACY: Keep messages column for backward compatibility
        if system_message and len(session.messages) == 0:
            session.messages.append(system_message)

        session.messages.append(user_message)
        session.messages.append(assistant_message)

        # Update total messages and flag modified
        session.total_messages = len(session.interaction_messages)

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(session, "interaction_messages")
        flag_modified(session, "real_messages")
        flag_modified(session, "messages")

        self.db.commit()
        self.db.refresh(session)

        # Yield done signal with assistant message and sources
        done_payload = {
            "type": "done",
            "content": full_content,  # Send the string content, not the entire message object
            "sources": unique_sources if unique_sources else [],  # Include sources in done event
            # Tools actually executed this turn — drives the frontend "Completed · Used: ..." badge
            "tool_calls": [{"name": name, "args": {}} for name in tools_used]
        }
        yield done_payload

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

        # End Chat is best-effort: the session must ALWAYS be closed, even when
        # analysis cannot be produced. Analysis failures (missing prompt, LLM
        # error, malformed response) are logged loudly (captured by Sentry) but
        # never raise to the caller or block ending the session.
        now = datetime.utcnow()

        def _finalize(*, summary=None, comprehension_level=None, analyzed=False, detail=None):
            session.summary = summary
            session.comprehension_level = comprehension_level
            session.ended_at = now
            if analyzed:
                session.status = "analyzed"
                session.analyzed_at = now
            else:
                session.status = "ended"
                session.analyzed_at = None
            self.db.commit()
            self.db.refresh(session)
            return {
                "session_id": session.id,
                "status": session.status,
                "analysis_available": analyzed,
                "summary": summary,
                "comprehension_level": comprehension_level.upper() if comprehension_level else None,
                "analyzed_at": session.analyzed_at.isoformat() if session.analyzed_at else None,
                "detail": detail,
            }

        if not session.messages:
            logger.warning(f"[ANALYSIS] Session {session_id}: no messages; ending without analysis")
            return _finalize(detail="Session has no messages to analyze")

        try:
            # Analysis prompt is a deliberate business-rule input — NO silent
            # fallback. If it is not configured we end the session and surface
            # the misconfiguration via logs/Sentry instead of guessing a prompt.
            chat_config = self.db.query(ChatConfig).filter(ChatConfig.id == 1).first()
            if not chat_config or not chat_config.prompt_analysis:
                raise ValueError("Analysis prompt not configured in ChatConfig")

            # Build analysis context (conversation history rendered to text)
            messages_text = self._format_messages_for_analysis(session.messages)
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

            logger.info(f"[ANALYSIS] Session {session_id}: Analysis completed - Level: {comprehension_level_raw}")
            return _finalize(summary=summary, comprehension_level=comprehension_level_raw, analyzed=True)

        except json.JSONDecodeError as e:
            logger.error(f"[ANALYSIS] Session {session_id}: LLM response not valid JSON; ending without analysis: {str(e)}", exc_info=True)
            self.db.rollback()
            return _finalize(detail="LLM response could not be parsed as JSON")
        except Exception as e:
            logger.error(f"[ANALYSIS] Session {session_id}: Analysis failed; ending without analysis: {str(e)}", exc_info=True)
            self.db.rollback()
            return _finalize(detail=f"Analysis failed: {str(e)}")

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
