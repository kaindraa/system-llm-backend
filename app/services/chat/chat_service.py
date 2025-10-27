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
from app.services.llm import LLMService
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for managing chat sessions and conversations."""

    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db=db)

    def create_session(
        self,
        user_id: UUID,
        model_id: str,
        title: Optional[str] = None,
        prompt_id: Optional[UUID] = None
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
            total_messages=0
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Created chat session {session.id} for user {user_id} with prompt_id={prompt_id}")
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

        user_message = {
            "role": "user",
            "content": message_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": None
        }

        conversation_context = self._build_conversation_context(session)
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

    def _build_conversation_context(self, session: ChatSession) -> List[Dict[str, str]]:
        """Build conversation context from session messages."""
        context = []

        if session.prompt_id:
            prompt = self.db.query(Prompt).filter(Prompt.id == session.prompt_id).first()
            if prompt:
                context.append({
                    "role": "system",
                    "content": prompt.content
                })

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
        api_key: Optional[str] = None
    ):
        """
        Send a message in a chat session and stream LLM response.
        Yields chunks of the assistant's response as they are generated.

        Args:
            session_id: Chat session ID
            user_id: User ID
            message_content: User's message content
            api_key: Optional API key for LLM provider

        Yields:
            Dict with 'type' and 'content':
            - {'type': 'user_message', 'content': {...}}
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

        # Create user message
        user_message = {
            "role": "user",
            "content": message_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": None
        }

        # Yield user message first
        yield {"type": "user_message", "content": user_message}

        # Build conversation context
        conversation_context = self._build_conversation_context(session)
        conversation_context.append({
            "role": "user",
            "content": message_content
        })

        logger.info(f"Session {session_id}: Streaming message to LLM (context: {len(conversation_context)} msgs)")

        # Stream LLM response
        full_content = ""
        try:
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

        # Create assistant message with full content
        assistant_message = {
            "role": "assistant",
            "content": full_content,
            "created_at": datetime.utcnow().isoformat(),
            "sources": None
        }

        # Save messages to database
        session.messages.append(user_message)
        session.messages.append(assistant_message)
        session.total_messages = len(session.messages)

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(session, "messages")

        self.db.commit()
        self.db.refresh(session)

        logger.info(f"Session {session_id}: Streaming completed (total: {len(session.messages)})")

        # Yield done signal with assistant message
        yield {"type": "done", "content": assistant_message}
