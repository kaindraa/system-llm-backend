from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, get_current_user
from app.schemas.llm import (
    ChatRequest,
    ChatResponse,
    AvailableProvidersResponse,
    ModelListResponse,
    ModelInfo,
)
from app.services.llm import LLMService
from app.models.user import User
from app.models.model import Model
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a response using the specified LLM model.

    This endpoint allows testing LLM integration by sending messages
    and receiving AI-generated responses.

    **Authentication required.**
    """
    try:
        logger.info(
            f"User {current_user.email} requesting chat with model: {request.model_id}"
        )

        # Initialize LLM service with database session
        llm_service = LLMService(db=db)

        # Convert Pydantic messages to dict format
        messages = [msg.model_dump() for msg in request.messages]

        # Get API key from request or settings
        api_key = request.api_key or settings.OPENAI_API_KEY

        # Generate response (uses provider defaults)
        response_text = await llm_service.generate_async(
            model_id=request.model_id,
            messages=messages,
            api_key=api_key if api_key else None
        )

        # Get model info
        model_info = llm_service.get_model_info(request.model_id)

        logger.info(
            f"Successfully generated response for user {current_user.email} "
            f"using model {request.model_id}"
        )

        return ChatResponse(response=response_text, model_info=model_info)

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}",
        )


@router.get("/providers", response_model=AvailableProvidersResponse)
async def get_available_providers(
    current_user: User = Depends(get_current_user),
):
    """
    Get list of available LLM providers.

    Returns all providers that are currently supported by the system.

    **Authentication required.**
    """
    try:
        llm_service = LLMService()
        providers = llm_service.get_available_providers()

        return AvailableProvidersResponse(providers=providers)

    except Exception as e:
        logger.error(f"Error fetching providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch providers: {str(e)}",
        )


@router.get("/models", response_model=ModelListResponse)
async def get_available_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of available LLM models from database.

    Returns all registered models that can be used for chat.

    **Authentication required.**
    """
    try:
        models = db.query(Model).all()

        model_list = [
            ModelInfo(
                id=model.id,
                name=model.name,
                display_name=model.display_name,
                provider=model.provider,
                api_endpoint=model.api_endpoint,
            )
            for model in models
        ]

        return ModelListResponse(models=model_list, count=len(model_list))

    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch models: {str(e)}",
        )


@router.get("/models/{model_id}/info")
async def get_model_info(
    model_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific model.

    Returns configuration and capability information for the specified model.

    **Authentication required.**
    """
    try:
        llm_service = LLMService(db=db)

        # This will initialize the provider and return its info
        model_info = llm_service.get_model_info(model_id)

        return model_info

    except ValueError as e:
        logger.error(f"Model not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching model info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch model info: {str(e)}",
        )
