"""
Prompt Schemas for API requests and responses.

These schemas define the structure for system prompts used in chat sessions.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class PromptCreate(BaseModel):
    """Schema for creating a new system prompt"""
    name: str = Field(..., min_length=1, max_length=255, description="Prompt name")
    content: str = Field(..., min_length=1, description="Prompt content/template")
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional description of the prompt"
    )
    is_active: bool = Field(
        default=False,
        description="Whether this prompt should be used by default"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python Tutor",
                "content": "You are an experienced Python programming tutor. Help students learn Python concepts step by step.",
                "description": "A prompt for teaching Python programming",
                "is_active": False
            }
        }


class PromptUpdate(BaseModel):
    """Schema for updating an existing prompt"""
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Prompt name"
    )
    content: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Prompt content/template"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Description of the prompt"
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Whether this prompt should be used by default"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Python Tutor",
                "content": None,
                "description": "Updated description",
                "is_active": True
            }
        }


class PromptResponse(BaseModel):
    """Schema for prompt in API responses"""
    id: UUID = Field(..., description="Prompt ID")
    name: str = Field(..., description="Prompt name")
    content: str = Field(..., description="Prompt content/template")
    description: Optional[str] = Field(None, description="Prompt description")
    is_active: bool = Field(..., description="Whether prompt is active")
    created_by: UUID = Field(..., description="User ID who created the prompt")
    created_at: datetime = Field(..., description="When prompt was created")
    updated_at: datetime = Field(..., description="When prompt was last updated")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Python Tutor",
                "content": "You are an experienced Python programming tutor...",
                "description": "A prompt for teaching Python programming",
                "is_active": False,
                "created_by": "660e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-25T10:00:00Z",
                "updated_at": "2025-01-25T10:00:00Z"
            }
        }


class PromptListResponse(BaseModel):
    """Schema for listing prompts with pagination"""
    prompts: List[PromptResponse] = Field(..., description="List of prompts")
    total: int = Field(..., description="Total number of prompts")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")

    class Config:
        json_schema_extra = {
            "example": {
                "prompts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Python Tutor",
                        "content": "You are an experienced Python programming tutor...",
                        "description": "A prompt for teaching Python programming",
                        "is_active": False,
                        "created_by": "660e8400-e29b-41d4-a716-446655440000",
                        "created_at": "2025-01-25T10:00:00Z",
                        "updated_at": "2025-01-25T10:00:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }
