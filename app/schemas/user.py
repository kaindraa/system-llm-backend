from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str
    role: Optional[UserRole] = UserRole.STUDENT


class UserResponse(UserBase):
    """Schema for user response (without password)"""
    id: UUID
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('id')
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string for JSON serialization"""
        return str(value)


class UserInDB(UserBase):
    """Schema for user in database (with hashed password)"""
    id: UUID
    password_hash: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
