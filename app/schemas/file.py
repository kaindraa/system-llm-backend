"""
File Schema

Pydantic models for file management API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.models.document import DocumentStatus


class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    id: UUID
    filename: str
    original_filename: str
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str
    status: DocumentStatus
    uploaded_at: datetime

    class Config:
        from_attributes = True


class FileDetailResponse(BaseModel):
    """Response model for file details"""
    id: UUID
    filename: str
    original_filename: str
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str
    status: DocumentStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """Response model for file list"""
    files: List[FileDetailResponse]
    total: int = Field(..., description="Total number of files")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class FileStatusUpdate(BaseModel):
    """Request model for updating file status"""
    status: DocumentStatus = Field(..., description="New status for the file")


class FileMetadataResponse(BaseModel):
    """Response model for file metadata (without content)"""
    id: UUID
    original_filename: str
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str
    status: DocumentStatus
    uploaded_at: datetime

    class Config:
        from_attributes = True
