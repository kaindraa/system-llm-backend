"""
Prompt Service

Handles system prompt management for LLM conversations.
Supports CRUD operations and prompt activation.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.prompt import Prompt
from app.models.user import UserRole
from app.core.logging import get_logger
from app.schemas.prompt import PromptCreate, PromptUpdate

logger = get_logger(__name__)


class PromptService:
    """Service for managing system prompts."""

    def __init__(self, db: Session):
        self.db = db

    def create_prompt(
        self,
        prompt_data: PromptCreate,
        user_id: UUID
    ) -> Prompt:
        """Create a new system prompt."""
        # If this is the first active prompt or is_active is True, deactivate others
        if prompt_data.is_active:
            self.db.query(Prompt).update({Prompt.is_active: False})

        prompt = Prompt(
            name=prompt_data.name,
            content=prompt_data.content,
            description=prompt_data.description,
            is_active=prompt_data.is_active,
            created_by=user_id
        )

        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)

        logger.info(f"Created prompt '{prompt.name}' (ID: {prompt.id}) by user {user_id}")
        return prompt

    def get_prompt(self, prompt_id: UUID) -> Optional[Prompt]:
        """Get a prompt by ID."""
        prompt = self.db.query(Prompt).filter(Prompt.id == prompt_id).first()
        return prompt

    def get_active_prompt(self) -> Optional[Prompt]:
        """Get the currently active prompt."""
        prompt = self.db.query(Prompt).filter(Prompt.is_active == True).first()
        return prompt

    def list_prompts(
        self,
        skip: int = 0,
        limit: int = 10,
        search: Optional[str] = None
    ) -> Tuple[List[Prompt], int]:
        """
        List prompts with optional search.

        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            search: Search term to filter by name or description

        Returns:
            Tuple of (prompts list, total count)
        """
        query = self.db.query(Prompt)

        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Prompt.name.ilike(search_term)) |
                (Prompt.description.ilike(search_term))
            )

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        prompts = (
            query
            .order_by(Prompt.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return prompts, total

    def update_prompt(
        self,
        prompt_id: UUID,
        prompt_data: PromptUpdate
    ) -> Optional[Prompt]:
        """Update a prompt."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        # Update fields if provided
        if prompt_data.name is not None:
            prompt.name = prompt_data.name

        if prompt_data.content is not None:
            prompt.content = prompt_data.content

        if prompt_data.description is not None:
            prompt.description = prompt_data.description

        # Handle is_active with special logic
        if prompt_data.is_active is not None:
            if prompt_data.is_active:
                # Deactivate all other prompts if this one becomes active
                self.db.query(Prompt).filter(Prompt.id != prompt_id).update({Prompt.is_active: False})
            prompt.is_active = prompt_data.is_active

        self.db.commit()
        self.db.refresh(prompt)

        logger.info(f"Updated prompt '{prompt.name}' (ID: {prompt_id})")
        return prompt

    def delete_prompt(self, prompt_id: UUID) -> bool:
        """Delete a prompt."""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return False

        self.db.delete(prompt)
        self.db.commit()

        logger.info(f"Deleted prompt (ID: {prompt_id})")
        return True

    def activate_prompt(self, prompt_id: UUID) -> Optional[Prompt]:
        """
        Activate a prompt and deactivate all others.

        Args:
            prompt_id: ID of the prompt to activate

        Returns:
            Updated prompt or None if not found
        """
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return None

        # Deactivate all other prompts
        self.db.query(Prompt).filter(Prompt.id != prompt_id).update({Prompt.is_active: False})

        # Activate this prompt
        prompt.is_active = True
        self.db.commit()
        self.db.refresh(prompt)

        logger.info(f"Activated prompt '{prompt.name}' (ID: {prompt_id})")
        return prompt

    def get_total_count(self) -> int:
        """Get total number of prompts in database."""
        return self.db.query(Prompt).count()
