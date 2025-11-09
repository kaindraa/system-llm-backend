"""
Chat API Endpoints

Provides REST API for chat session management and conversation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from uuid import UUID
import json

from app.api.dependencies import get_db, get_current_user, get_current_admin, get_current_student, get_llm_service
from app.models.user import User
from app.models.chat_session import SessionStatus, ChatSession
from app.models.model import Model
from app.models.prompt import Prompt
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatSessionUpdate,
    ChatRequest,
    ChatResponse,
    SessionListResponse,
    ChatMessageResponse,
    ConfigResponse,
    ModelInfo,
    PromptInfo,
    SessionAnalysisResponse,
)
from app.services.chat import ChatService
from app.services.llm import LLMService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Create a new chat session.

    Creates a new conversation session with a specific LLM model.
    Optionally can use a system prompt from the database.

    **Student only.**
    """
    try:
        # DEBUG: Log incoming request
        logger.info(f"[CREATE_SESSION] Request received from user {current_user.id}")
        logger.info(f"[CREATE_SESSION] Request data: model_id={request.model_id}, title={request.title}, prompt_id={request.prompt_id}")

        # Log all prompt fields in detail
        logger.info("=" * 80)
        logger.info("[CREATE_SESSION] PROMPT CONFIGURATION DETAILS:")
        logger.info(f"  prompt_general: {request.prompt_general if request.prompt_general else '(not provided)'}")
        logger.info(f"  task: {request.task if request.task else '(not provided)'}")
        logger.info(f"  persona: {request.persona if request.persona else '(not provided)'}")
        logger.info(f"  mission_objective: {request.mission_objective if request.mission_objective else '(not provided)'}")
        logger.info("=" * 80)

        chat_service = ChatService(db=db, llm_service=llm_service)

        session = chat_service.create_session(
            user_id=current_user.id,
            model_id=request.model_id,
            title=request.title,
            prompt_id=request.prompt_id,
            prompt_general=request.prompt_general,
            task=request.task,
            persona=request.persona,
            mission_objective=request.mission_objective
        )

        # DEBUG: Log created session
        logger.info(f"[CREATE_SESSION] Created session {session.id} with prompt_id={session.prompt_id}")

        return session

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions", response_model=SessionListResponse)
async def list_chat_sessions(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    List all chat sessions for the current user.

    Returns sessions ordered by most recent first.
    Supports filtering by status and pagination.

    **Student only.**
    """
    try:
        chat_service = ChatService(db=db, llm_service=llm_service)

        status_enum = None
        if status_filter:
            try:
                status_enum = SessionStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Use 'active' or 'completed'"
                )

        sessions = chat_service.list_sessions(
            user_id=current_user.id,
            status=status_enum,
            limit=limit,
            offset=offset
        )

        return SessionListResponse(
            sessions=sessions,
            total=len(sessions)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Get a specific chat session with all messages.

    Returns the session details including full conversation history.

    Students can only view their own sessions.
    Admins can view any session.

    **Authentication required.**
    """
    try:
        chat_service = ChatService(db=db, llm_service=llm_service)

        # Admins can view any session, students can only view their own
        if current_user.role == "admin":
            # Admin: fetch session without user_id filter
            from app.models.chat_session import ChatSession as ChatSessionModel
            session = db.query(ChatSessionModel).filter(ChatSessionModel.id == session_id).first()
        else:
            # Student: fetch only their own session
            session = chat_service.get_session(
                session_id=session_id,
                user_id=current_user.id
            )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        # Convert to dict and add model_name
        session_dict = {
            **session.__dict__,
            "model_name": session.model.display_name if session.model else None
        }

        # Remove SQLAlchemy internal attributes
        session_dict = {k: v for k, v in session_dict.items() if not k.startswith("_")}

        return session_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: UUID,
    request: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Update a chat session.

    Allows updating the title or status of a session.

    **Admin only.**
    """
    try:
        chat_service = ChatService(db=db, llm_service=llm_service)

        status_enum = None
        if request.status:
            try:
                status_enum = SessionStatus(request.status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status. Use 'active' or 'completed'"
                )

        session = chat_service.update_session(
            session_id=session_id,
            user_id=current_user.id,
            title=request.title,
            status=status_enum
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Delete a chat session.

    Permanently deletes the session and all its messages.

    **Admin only.**
    """
    try:
        chat_service = ChatService(db=db, llm_service=llm_service)

        deleted = chat_service.delete_session(
            session_id=session_id,
            user_id=current_user.id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Send a message in a chat session with streaming response.

    Sends a user message and streams back the AI-generated response in real-time.
    Maintains conversation context (short-term memory).

    Returns Server-Sent Events (SSE) format:
    - event: user_message - The user's message
    - event: chunk - Text chunks as they are generated
    - event: done - Final assistant message after completion
    - event: error - Error information if something fails

    **Student only.**
    """
    async def generate_stream():
        try:
            chat_service = ChatService(db=db, llm_service=llm_service)

            logger.info(
                f"User {current_user.email} sending streaming message to session {session_id}"
            )

            # Get session to determine which model/provider is being used
            # Use eager loading to fetch model relationship
            from app.models.chat_session import ChatSession
            session = db.query(ChatSession).options(
                joinedload(ChatSession.model)
            ).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id
            ).first()

            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Get appropriate API key based on model provider
            api_key = None
            if session.model:
                provider_name = session.model.provider.lower()
                api_key_mapping = {
                    "openai": settings.OPENAI_API_KEY,
                    "anthropic": settings.ANTHROPIC_API_KEY,
                    "google": settings.GOOGLE_API_KEY,
                }
                api_key = api_key_mapping.get(provider_name)
                logger.info(f"Using {provider_name} provider with API key")

            async for event in chat_service.send_message_stream(
                session_id=session_id,
                user_id=current_user.id,
                message_content=request.message,
                api_key=api_key,
                use_rag=True  # Enable RAG by default - LLM decides if it needs to search
            ):
                event_type = event["type"]
                content = event["content"]

                if event_type == "user_message":
                    yield f"event: user_message\ndata: {json.dumps(content)}\n\n"
                elif event_type == "rag_search":
                    # RAG tool call event
                    yield f"event: rag_search\ndata: {json.dumps(content)}\n\n"
                elif event_type == "chunk":
                    # Text chunk from LLM response
                    yield f"event: chunk\ndata: {json.dumps({'content': content})}\n\n"
                elif event_type == "done":
                    # Final response with sources
                    yield f"event: done\ndata: {json.dumps(content)}\n\n"

        except ValueError as e:
            logger.error(f"Invalid request: {str(e)}")
            yield f"event: error\ndata: {json.dumps({'error': str(e), 'status': 400})}\n\n"
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': f'Failed to send message: {str(e)}', 'status': 500})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/config", response_model=ConfigResponse)
async def get_chat_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student),
):
    """
    Get chat configuration with available models and active prompt.

    Returns all available models and the currently active system prompt.
    This is used by the frontend to display options when creating a new chat.

    **Student only.**
    """
    try:
        # Get all models, ordered by priority (lower order = higher priority)
        models = db.query(Model).order_by(Model.order, Model.name).all()
        model_infos = [
            ModelInfo(
                id=model.id,
                name=model.name,
                display_name=model.display_name,
                provider=model.provider
            )
            for model in models
        ]

        # Get active prompt
        active_prompt = db.query(Prompt).filter(Prompt.is_active == True).first()
        active_prompt_info = None
        if active_prompt:
            active_prompt_info = PromptInfo(
                id=active_prompt.id,
                name=active_prompt.name,
                description=active_prompt.description
            )

        return ConfigResponse(
            models=model_infos,
            active_prompt=active_prompt_info
        )

    except Exception as e:
        logger.error(f"Error getting config: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}"
        )


@router.post("/sessions/{session_id}/analysis", response_model=SessionAnalysisResponse)
async def analyze_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Analyze a completed chat session.

    Generates a summary and comprehension level assessment based on the conversation history.
    Results are saved to the database.

    Students can only analyze their own sessions.
    Admins can analyze any session.

    **Authenticated users only.**
    """
    try:
        chat_service = ChatService(db=db, llm_service=llm_service)

        # For students, analyze only their own session
        # For admins, get the actual session first to find the real user_id
        if current_user.role == "admin":
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session {session_id} not found"
                )
            user_id_for_analysis = session.user_id
        else:
            user_id_for_analysis = current_user.id

        analysis = await chat_service.analyze_session(
            session_id=session_id,
            user_id=user_id_for_analysis
        )

        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return analysis

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error analyzing session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze session: {str(e)}"
        )
