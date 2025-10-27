"""
User Management API Endpoints

Provides REST API for admin to manage users and view their activity.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from sqlalchemy import func

from app.api.dependencies import get_db, get_current_admin
from app.models.user import User
from app.models.chat_session import ChatSession
from app.schemas.user import UserResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


class UserWithChatCount(UserResponse):
    """User response with chat session count"""
    chat_count: int


@router.get("", response_model=dict)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    search: str = Query(None, min_length=1, description="Search by email or full name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List all users with their chat session counts.

    Returns users ordered by creation date (newest first).
    Supports search filtering and pagination.

    **Admin only.**
    """
    try:
        query = db.query(User)

        # Apply search filter
        if search:
            query = query.filter(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%"))
            )

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        # Build response with chat counts
        users_with_counts = []
        for user in users:
            chat_count = db.query(func.count(ChatSession.id)).filter(
                ChatSession.user_id == user.id
            ).scalar()

            users_with_counts.append({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "chat_count": chat_count or 0,
            })

        return {
            "users": users_with_counts,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit,
        }

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )


@router.get("/{user_id}/chats", response_model=dict)
async def get_user_chats(
    user_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Get all chat sessions for a specific user.

    Returns sessions ordered by most recent first.
    Supports pagination.

    **Admin only.**
    """
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        # Get total count
        total = db.query(func.count(ChatSession.id)).filter(
            ChatSession.user_id == user_id
        ).scalar()

        # Get paginated chat sessions
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.started_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # Format response
        sessions_data = [
            {
                "id": session.id,
                "title": session.title,
                "status": session.status.value,
                "total_messages": session.total_messages,
                "started_at": session.started_at,
                "ended_at": session.ended_at,
                "model_id": session.model_id,
                "prompt_id": session.prompt_id,
            }
            for session in sessions
        ]

        return {
            "user_id": user_id,
            "user_email": user.email,
            "user_name": user.full_name,
            "sessions": sessions_data,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "page_size": limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user chats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user chats: {str(e)}"
        )
