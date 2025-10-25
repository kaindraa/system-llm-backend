from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID


class Message(BaseModel):
    """Single message in a conversation"""
    role: str = Field(
        ...,
        description="Role of the message sender (system, user, or assistant)"
    )
    content: str = Field(..., description="Content of the message")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What is machine learning?"
            }
        }


class ChatRequest(BaseModel):
    """Request schema for chat/inference endpoint. All models use their own defaults."""
    model_id: str = Field(
        ...,
        description="Model ID (UUID) or name, or 'provider:model_name' format"
    )
    messages: List[Message] = Field(
        ...,
        description="List of messages in the conversation"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Optional: API key for the provider (overrides environment variable)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "openai:gpt-5-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": "Explain quantum computing in simple terms."
                    }
                ]
            }
        }


class ChatResponse(BaseModel):
    """Response schema for chat/inference endpoint"""
    response: str = Field(..., description="Generated response from the model")
    model_info: Dict[str, Any] = Field(
        ...,
        description="Information about the model used"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Quantum computing is a type of computation that...",
                "model_info": {
                    "provider": "openai",
                    "model_name": "gpt-5-mini",
                    "config": {}
                }
            }
        }


class ModelInfo(BaseModel):
    """Model information schema"""
    id: UUID = Field(..., description="Model UUID")
    name: str = Field(..., description="Model name")
    display_name: str = Field(..., description="Display name for the model")
    provider: str = Field(..., description="Provider name (e.g., openai, ollama)")
    api_endpoint: Optional[str] = Field(
        None,
        description="API endpoint for the model"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "gpt-5-mini",
                "display_name": "GPT-5 Mini",
                "provider": "openai",
                "api_endpoint": "https://api.openai.com/v1/chat/completions"
            }
        }


class AvailableProvidersResponse(BaseModel):
    """Response schema for available providers endpoint"""
    providers: List[str] = Field(..., description="List of available provider names")

    class Config:
        json_schema_extra = {
            "example": {
                "providers": ["openai", "ollama", "anthropic"]
            }
        }


class ModelListResponse(BaseModel):
    """Response schema for listing models"""
    models: List[ModelInfo] = Field(..., description="List of available models")
    count: int = Field(..., description="Total number of models")

    class Config:
        json_schema_extra = {
            "example": {
                "models": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "gpt-5-mini",
                        "display_name": "GPT-5 Mini",
                        "provider": "openai",
                        "api_endpoint": "https://api.openai.com/v1/chat/completions"
                    }
                ],
                "count": 1
            }
        }
