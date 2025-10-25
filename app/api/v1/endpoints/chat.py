"""
Chat API Endpoints

Provides REST API for chat session management and conversation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.api.dependencies import get_db, get_current_user, get_current_admin, get_current_student
from app.models.user import User
from app.models.chat_session import SessionStatus
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatSessionUpdate,
    ChatRequest,
    ChatResponse,
    SessionListResponse,
    ChatMessageResponse,
)
from app.services.chat import ChatService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student),
):
    """
    Create a new chat session.

    Creates a new conversation session with a specific LLM model.
    Optionally can use a system prompt from the database.

    **Student only.**
    """
    try:
        chat_service = ChatService(db=db)

        session = chat_service.create_session(
            user_id=current_user.id,
            model_id=request.model_id,
            title=request.title,
            prompt_id=request.prompt_id
        )

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
):
    """
    List all chat sessions for the current user.

    Returns sessions ordered by most recent first.
    Supports filtering by status and pagination.

    **Student only.**
    """
    try:
        chat_service = ChatService(db=db)

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
):
    """
    Get a specific chat session with all messages.

    Returns the session details including full conversation history.

    Students can only view their own sessions.
    Admins can view any session.

    **Authentication required.**
    """
    try:
        chat_service = ChatService(db=db)

        session = chat_service.get_session(
            session_id=session_id,
            user_id=current_user.id
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
):
    """
    Update a chat session.

    Allows updating the title or status of a session.

    **Admin only.**
    """
    try:
        chat_service = ChatService(db=db)

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
):
    """
    Delete a chat session.

    Permanently deletes the session and all its messages.

    **Admin only.**
    """
    try:
        chat_service = ChatService(db=db)

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


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: UUID,
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student),
):
    """
    Send a message in a chat session.

    Sends a user message and receives an AI-generated response.
    Maintains conversation context (short-term memory).

    **Student only.**
    """
    try:
        chat_service = ChatService(db=db)

        logger.info(
            f"User {current_user.email} sending message to session {session_id}"
        )

        api_key = settings.OPENAI_API_KEY

        result = await chat_service.send_message(
            session_id=session_id,
            user_id=current_user.id,
            message_content=request.message,
            api_key=api_key
        )

        return ChatResponse(
            session_id=session_id,
            user_message=ChatMessageResponse(**result["user_message"]),
            assistant_message=ChatMessageResponse(**result["assistant_message"])
        )

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )
