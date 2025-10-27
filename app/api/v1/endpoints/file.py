"""
File Management API Endpoints

Provides REST API for file upload, download, and management.
Supports PDF file operations for learning materials.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
import uuid

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.document import DocumentStatus
from app.schemas.file import (
    FileUploadResponse,
    FileDetailResponse,
    FileListResponse,
    FileStatusUpdate,
    FileMetadataResponse,
)
from app.services.file_service import FileService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF file"
)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a PDF file for learning materials.

    - **file**: PDF file to upload (required)

    Returns uploaded file metadata with unique ID for later reference.

    **Requires authentication.**
    """
    try:
        # Validate file type
        if file.content_type not in ["application/pdf"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only PDF files are allowed"
            )

        # Validate filename
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have a filename"
            )

        # Read file content
        content = await file.read()

        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {max_size / (1024*1024):.0f}MB"
            )

        # Generate unique filename
        file_id = str(uuid.uuid4())

        # Create file using service
        file_service = FileService(db=db)
        document = file_service.create_file(
            user_id=current_user.id,
            filename=file_id,
            original_filename=file.filename,
            content=content,
            mime_type=file.content_type or "application/pdf"
        )

        logger.info(f"File uploaded by user {current_user.id}: {file.filename}")

        return FileUploadResponse.model_validate(document)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get(
    "",
    response_model=FileListResponse,
    summary="List user's uploaded files"
)
async def list_files(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    status: DocumentStatus = Query(None, description="Filter by document status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all files uploaded by the current user with pagination.

    Query Parameters:
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (1-100)
    - **status**: Optional filter by document status (uploaded, processing, processed, failed)

    Returns list of files ordered by upload date (newest first).

    **Requires authentication.**
    """
    try:
        file_service = FileService(db=db)
        documents, total = file_service.list_files(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status
        )

        return FileListResponse(
            files=[FileDetailResponse.model_validate(doc) for doc in documents],
            total=total,
            page=(skip // limit) + 1,
            page_size=limit
        )

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )


@router.get(
    "/{file_id}",
    response_model=FileDetailResponse,
    summary="Get file details"
)
async def get_file_detail(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific file.

    - **file_id**: UUID of the file

    Returns file metadata including upload date and processing status.

    **Requires authentication.**
    """
    try:
        file_service = FileService(db=db)
        document = file_service.get_file(str(file_id))

        # Verify ownership
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this file"
            )

        return FileDetailResponse.model_validate(document)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file detail: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file details: {str(e)}"
        )


@router.get(
    "/{file_id}/download",
    summary="Download file"
)
async def download_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download a file (PDF) for the user to view or save locally.

    - **file_id**: UUID of the file

    Returns the PDF file as binary response for download.

    **Requires authentication.**
    """
    try:
        file_service = FileService(db=db)
        document = file_service.get_file(str(file_id))

        # Verify ownership
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this file"
            )

        # Get file content
        content = file_service.get_file_content(str(file_id))

        logger.info(f"File downloaded by user {current_user.id}: {file_id}")

        return FileResponse(
            content=content,
            media_type=document.mime_type or "application/pdf",
            filename=document.original_filename,
            headers={
                "Content-Disposition": f"attachment; filename={document.original_filename}"
            }
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file"
)
async def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a file (removes from both storage and database).

    - **file_id**: UUID of the file

    **Requires authentication and file ownership.**
    """
    try:
        file_service = FileService(db=db)

        # Verify ownership by fetching first
        document = file_service.get_file(str(file_id))
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this file"
            )

        # Delete file
        deleted = file_service.delete_file(str(file_id), user_id=current_user.id)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID '{file_id}' not found"
            )

        logger.info(f"File deleted by user {current_user.id}: {file_id}")

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.patch(
    "/{file_id}/status",
    response_model=FileDetailResponse,
    summary="Update file processing status"
)
async def update_file_status(
    file_id: UUID,
    request: FileStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the processing status of a file.

    Used internally by the system to update status during RAG processing.

    - **file_id**: UUID of the file
    - **request**: New status (uploaded, processing, processed, failed)

    **Requires authentication and file ownership.**
    """
    try:
        file_service = FileService(db=db)

        # Verify ownership
        document = file_service.get_file(str(file_id))
        if document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this file"
            )

        # Update status
        updated_document = file_service.update_file_status(str(file_id), request.status)

        logger.info(f"File status updated by user {current_user.id}: {file_id} -> {request.status}")

        return FileDetailResponse.model_validate(updated_document)

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID '{file_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file status: {str(e)}"
        )
