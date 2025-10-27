"""
Prompt API Endpoints

Provides REST API for system prompt management (admin only).
Supports CRUD operations for system prompts used in chat sessions.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.dependencies import get_db, get_current_admin, get_current_user
from app.models.user import User
from app.schemas.prompt import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptListResponse,
)
from app.services.prompt_service import PromptService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/prompts", tags=["Prompts"])


@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt(
    request: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Create a new system prompt.

    Creates a new system prompt that can be used for chat sessions.
    If is_active is set to True, all other prompts will be deactivated.

    **Admin only.**
    """
    try:
        prompt_service = PromptService(db=db)
        prompt = prompt_service.create_prompt(
            prompt_data=request,
            user_id=current_user.id
        )

        return prompt

    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prompt: {str(e)}"
        )


@router.get("", response_model=PromptListResponse)
async def list_prompts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    search: str = Query(None, min_length=1, description="Search by name or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    List all system prompts with pagination and optional search.

    Returns prompts ordered by creation date (newest first).
    Supports search filtering and pagination.

    **Admin only.**
    """
    try:
        prompt_service = PromptService(db=db)
        prompts, total = prompt_service.list_prompts(
            skip=skip,
            limit=limit,
            search=search
        )

        return PromptListResponse(
            prompts=prompts,
            total=total,
            page=(skip // limit) + 1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Error listing prompts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific system prompt by ID.

    Retrieves detailed information about a single prompt. Requires authentication.
    """
    try:
        prompt_service = PromptService(db=db)
        prompt = prompt_service.get_prompt(prompt_id)

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt with ID '{prompt_id}' not found"
            )

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}"
        )


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: UUID,
    request: PromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update a system prompt.

    Updates one or more fields of an existing prompt.
    If is_active is set to True, all other prompts will be deactivated.

    **Admin only.**
    """
    try:
        prompt_service = PromptService(db=db)
        prompt = prompt_service.update_prompt(
            prompt_id=prompt_id,
            prompt_data=request
        )

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt with ID '{prompt_id}' not found"
            )

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update prompt: {str(e)}"
        )


@router.delete("/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(
    prompt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Delete a system prompt.

    Permanently removes a prompt from the database.
    If the deleted prompt was active, no other prompt will be automatically activated.

    **Admin only.**
    """
    try:
        prompt_service = PromptService(db=db)
        deleted = prompt_service.delete_prompt(prompt_id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt with ID '{prompt_id}' not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prompt: {str(e)}"
        )


@router.patch("/{prompt_id}/activate", response_model=PromptResponse)
async def activate_prompt(
    prompt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Activate a system prompt.

    Sets the specified prompt as active (deactivates all others).
    Only one prompt can be active at a time.

    **Admin only.**
    """
    try:
        prompt_service = PromptService(db=db)
        prompt = prompt_service.activate_prompt(prompt_id)

        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt with ID '{prompt_id}' not found"
            )

        return prompt

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating prompt: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate prompt: {str(e)}"
        )

