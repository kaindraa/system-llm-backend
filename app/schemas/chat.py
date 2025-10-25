"""
Chat Schemas for API requests and responses.

These schemas define the structure for chat sessions and messages.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class SessionStatus(str, Enum):
    """Chat session status"""
    ACTIVE = "active"
    COMPLETED = "completed"


class MessageRole(str, Enum):
    """Message role in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessageCreate(BaseModel):
    """Schema for creating a new message in a chat"""
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., min_length=1, description="Content of the message")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Explain what is machine learning?"
            }
        }


class ChatMessageResponse(BaseModel):
    """Schema for a chat message in responses"""
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    created_at: datetime = Field(..., description="When the message was created")
    sources: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Sources from RAG (if applicable)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "role": "assistant",
                "content": "Machine learning is a subset of AI...",
                "created_at": "2025-01-25T10:30:00Z",
                "sources": None
            }
        }


class ChatSessionCreate(BaseModel):
    """Schema for creating a new chat session"""
    model_id: str = Field(
        ...,
        description="Model ID (UUID) or name to use for this session"
    )
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional title for the session"
    )
    prompt_id: Optional[UUID] = Field(
        default=None,
        description="System prompt to use (from database)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "gpt-5-mini",
                "title": "Learning about Machine Learning",
                "prompt_id": None
            }
        }


class ChatSessionUpdate(BaseModel):
    """Schema for updating a chat session"""
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Update session title"
    )
    status: Optional[SessionStatus] = Field(
        default=None,
        description="Update session status"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated title",
                "status": "completed"
            }
        }


class ChatSessionResponse(BaseModel):
    """Schema for chat session in responses"""
    id: UUID = Field(..., description="Session ID")
    user_id: UUID = Field(..., description="User ID")
    model_id: UUID = Field(..., description="Model ID")
    prompt_id: Optional[UUID] = Field(None, description="Prompt ID")
    title: Optional[str] = Field(None, description="Session title")
    status: str = Field(..., description="Session status")
    total_messages: int = Field(..., description="Total messages in session")
    started_at: datetime = Field(..., description="When session started")
    ended_at: Optional[datetime] = Field(None, description="When session ended")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "model_id": "770e8400-e29b-41d4-a716-446655440000",
                "prompt_id": None,
                "title": "Learning Session",
                "status": "active",
                "total_messages": 10,
                "started_at": "2025-01-25T10:00:00Z",
                "ended_at": None
            }
        }


class ChatSessionDetailResponse(ChatSessionResponse):
    """Schema for detailed chat session with messages"""
    messages: List[ChatMessageResponse] = Field(
        ...,
        description="All messages in the session"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "model_id": "770e8400-e29b-41d4-a716-446655440000",
                "prompt_id": None,
                "title": "Learning Session",
                "status": "active",
                "total_messages": 4,
                "started_at": "2025-01-25T10:00:00Z",
                "ended_at": None,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello!",
                        "created_at": "2025-01-25T10:01:00Z",
                        "sources": None
                    },
                    {
                        "role": "assistant",
                        "content": "Hi! How can I help you?",
                        "created_at": "2025-01-25T10:01:05Z",
                        "sources": None
                    }
                ]
            }
        }


class ChatRequest(BaseModel):
    """Schema for sending a message in a chat session"""
    message: str = Field(..., min_length=1, description="User message content")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Can you explain what is a neural network?"
            }
        }


class ChatResponse(BaseModel):
    """Schema for response after sending a message"""
    session_id: UUID = Field(..., description="Session ID")
    user_message: ChatMessageResponse = Field(..., description="User's message")
    assistant_message: ChatMessageResponse = Field(..., description="Assistant's response")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_message": {
                    "role": "user",
                    "content": "What is a neural network?",
                    "created_at": "2025-01-25T10:30:00Z",
                    "sources": None
                },
                "assistant_message": {
                    "role": "assistant",
                    "content": "A neural network is...",
                    "created_at": "2025-01-25T10:30:05Z",
                    "sources": None
                }
            }
        }


class SessionListResponse(BaseModel):
    """Schema for listing chat sessions"""
    sessions: List[ChatSessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")

    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "660e8400-e29b-41d4-a716-446655440000",
                        "model_id": "770e8400-e29b-41d4-a716-446655440000",
                        "prompt_id": None,
                        "title": "Session 1",
                        "status": "active",
                        "total_messages": 6,
                        "started_at": "2025-01-25T10:00:00Z",
                        "ended_at": None
                    }
                ],
                "total": 1
            }
        }
