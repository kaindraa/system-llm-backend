"""
File Management API Endpoints

Provides REST API for file upload, download, and management.
Supports PDF file operations for learning materials.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File as FastAPIFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
import uuid
from io import BytesIO

from app.api.dependencies import get_db, get_current_user, get_current_admin
from app.models.user import User
from app.models.document import DocumentStatus
from app.schemas.file import (
    FileUploadResponse,
    FileDetailResponse,
    FileListResponse,
    FileStatusUpdate,
    FileMetadataResponse,
)
from app.services.file_service import FileService, storage_provider
from app.core.logging import get_logger
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


# Diagnostic schemas
class FileDownloadDiagnostics(BaseModel):
    """Diagnostic info for file download troubleshooting"""
    file_id: str
    database_record_exists: bool
    database_details: dict = {}
    storage_file_exists: bool
    storage_provider_type: str
    gcs_blob_details: dict = {}
    potential_issues: list[str] = []
    recommendations: list[str] = []


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
    summary="List all files in the system"
)
async def list_files(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    status: DocumentStatus = Query(None, description="Filter by document status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List ALL files in the system with pagination.

    Query Parameters:
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (1-100)
    - **status**: Optional filter by document status (uploaded, processing, processed, failed)

    Returns list of all files ordered by upload date (newest first).

    **Requires authentication. All authenticated users can see all files.**
    """
    try:
        file_service = FileService(db=db)
        documents, total = file_service.list_all_files(
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

    **Requires authentication. All users can access any file.**
    """
    try:
        file_service = FileService(db=db)
        document = file_service.get_file(str(file_id))

        # Allow all authenticated users to read file details
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
    "/{file_id}/diagnose",
    response_model=FileDownloadDiagnostics,
    summary="Diagnose file download issues (Admin only)"
)
async def diagnose_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Diagnostic endpoint to identify why file downloads are failing.

    This endpoint checks:
    1. If file metadata exists in database
    2. If file exists in storage (GCS/local)
    3. Storage provider type and configuration
    4. GCS blob details (for GCS storage)
    5. Potential issues and recommendations

    **Requires ADMIN role only.**
    """
    try:
        file_service = FileService(db=db)
        file_id_str = str(file_id)

        # 1. Check if database record exists
        db_record_exists = False
        db_details = {}
        potential_issues = []
        recommendations = []

        try:
            document = file_service.get_file(file_id_str)
            db_record_exists = True
            db_details = {
                "id": str(document.id),
                "filename": document.filename,
                "original_filename": document.original_filename,
                "file_path": document.file_path,
                "file_size": document.file_size,
                "mime_type": document.mime_type,
                "status": document.status,
                "user_id": str(document.user_id),
                "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
            }
            logger.info(f"[DIAGNOSE] Database record found for file {file_id_str}")
        except FileNotFoundError:
            logger.warning(f"[DIAGNOSE] Database record NOT found for file {file_id_str}")
            potential_issues.append("FILE_NOT_IN_DATABASE: File metadata not found in database")
            recommendations.append("Check if file ID is correct or if file was deleted")

        # 2. Check if file exists in storage
        storage_exists = False
        gcs_blob_details = {}

        try:
            if db_record_exists:
                storage_exists = file_service.storage.exists(document.filename)
                logger.info(f"[DIAGNOSE] Storage file exists check: {storage_exists}")

                if not storage_exists:
                    potential_issues.append("FILE_NOT_IN_STORAGE: File metadata exists but file not found in storage")
                    recommendations.append("File might have been deleted from GCS or local storage")
                    recommendations.append("Check GCS bucket for uploads/ folder and verify file exists")

                # If GCS, get blob details
                if storage_provider.__class__.__name__ == "GCSStorageProvider":
                    try:
                        blob_name = storage_provider._get_blob_name(document.filename)
                        blob = storage_provider.bucket.blob(blob_name)

                        if blob.exists():
                            gcs_blob_details = {
                                "blob_name": blob_name,
                                "bucket": storage_provider.bucket_name,
                                "size": blob.size,
                                "content_type": blob.content_type,
                                "time_created": blob.time_created.isoformat() if blob.time_created else None,
                                "updated": blob.updated.isoformat() if blob.updated else None,
                                "generation": blob.generation,
                                "metageneration": blob.metageneration,
                            }
                            logger.info(f"[DIAGNOSE] GCS blob details retrieved: {blob_name}")
                        else:
                            gcs_blob_details["error"] = f"Blob not found at path: gs://{storage_provider.bucket_name}/{blob_name}"
                            logger.warning(f"[DIAGNOSE] GCS blob not found: {blob_name}")
                    except Exception as gcs_error:
                        gcs_blob_details["error"] = str(gcs_error)
                        potential_issues.append(f"GCS_ERROR: {str(gcs_error)}")
                        recommendations.append("Check GCS credentials and permissions")
        except Exception as storage_check_error:
            logger.error(f"[DIAGNOSE] Error checking storage: {str(storage_check_error)}", exc_info=True)
            potential_issues.append(f"STORAGE_CHECK_ERROR: {str(storage_check_error)}")

        # 3. Storage provider info
        storage_provider_type = storage_provider.__class__.__name__ if storage_provider else "UNKNOWN"

        # 4. Additional checks and recommendations
        if db_record_exists:
            if document.status != "uploaded" and document.status != "processed":
                potential_issues.append(f"INVALID_STATUS: File status is '{document.status}' (expected 'uploaded' or 'processed')")
                recommendations.append(f"File is in '{document.status}' state - may not be ready for download")

            # Check if blob name construction is correct
            if storage_provider_type == "GCSStorageProvider":
                expected_blob_name = f"uploads/{document.filename}.pdf"
                recommendations.append(f"Expected GCS blob path: gs://{storage_provider.bucket_name}/{expected_blob_name}")

        if not db_record_exists and not storage_exists:
            recommendations.append("File does not exist - verify file ID and try uploading again")

        if storage_provider_type == "GCSStorageProvider" and db_record_exists and not storage_exists:
            recommendations.append("Run: gsutil ls gs://system-llm-storage/uploads/ to check available files")
            recommendations.append("Check GCS service account permissions (need storage.objects.get)")

        return FileDownloadDiagnostics(
            file_id=file_id_str,
            database_record_exists=db_record_exists,
            database_details=db_details,
            storage_file_exists=storage_exists,
            storage_provider_type=storage_provider_type,
            gcs_blob_details=gcs_blob_details,
            potential_issues=potential_issues,
            recommendations=recommendations,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DIAGNOSE] Error during diagnosis - file_id: {file_id}, error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnosis failed: {str(e)}"
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

    Returns the PDF file as binary response for download using chunked streaming.
    This method streams the file in chunks, avoiding memory issues with large files.

    **Requires authentication. All users can download any file.**
    """
    try:
        file_service = FileService(db=db)
        document = file_service.get_file(str(file_id))

        # Allow all authenticated users to download files
        logger.info(f"File download started by user {current_user.id}: {file_id} ({document.original_filename})")

        # Stream file content in chunks (memory efficient, especially for large files)
        # This is critical for production Cloud Run environments with limited memory
        def file_iterator():
            """Generator function to stream file content in chunks with integrity checking"""
            bytes_streamed = 0
            try:
                for chunk in file_service.stream_file_content(str(file_id), chunk_size=1024 * 1024):  # 1MB chunks
                    bytes_streamed += len(chunk)
                    yield chunk

                # Verify integrity: total bytes streamed should match expected file size
                if bytes_streamed != document.file_size:
                    logger.warning(
                        f"File download integrity check - size mismatch: "
                        f"expected: {document.file_size}, streamed: {bytes_streamed} - "
                        f"FILE MIGHT BE CORRUPT - user: {current_user.id}, file: {file_id}"
                    )
                    # Still complete the download, but log the issue for investigation
                else:
                    logger.info(
                        f"File download completed successfully - "
                        f"user: {current_user.id}, file_id: {file_id}, "
                        f"size: {bytes_streamed} bytes"
                    )
            except Exception as e:
                logger.error(
                    f"Error streaming file chunks - "
                    f"user: {current_user.id}, file: {file_id}, "
                    f"bytes_streamed_so_far: {bytes_streamed}, "
                    f"expected_size: {document.file_size}, "
                    f"error: {str(e)}",
                    exc_info=True
                )
                raise

        # Return file as streaming response with proper headers
        # Include X-File-Size header for client-side validation
        return StreamingResponse(
            file_iterator(),
            media_type=document.mime_type or "application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={document.original_filename}",
                "Content-Type": document.mime_type or "application/pdf",
                "Content-Length": str(document.file_size),  # Important for client validation
                "X-File-ID": str(file_id),
                "X-File-Name": document.original_filename,
                "X-File-Size": str(document.file_size),  # For client-side integrity check
                "Cache-Control": "no-cache, no-store, must-revalidate",  # Don't cache file downloads
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
        logger.error(f"Error downloading file - file_id: {file_id}, user: {current_user.id}, error: {str(e)}", exc_info=True)
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
    current_admin: User = Depends(get_current_admin),
):
    """
    Delete a file (removes from both storage and database).

    - **file_id**: UUID of the file

    **Requires ADMIN role only.**
    """
    try:
        file_service = FileService(db=db)

        # Delete file (admin can delete any file)
        deleted = file_service.delete_file(str(file_id), user_id=None)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID '{file_id}' not found"
            )

        logger.info(f"File deleted by admin {current_admin.id}: {file_id}")

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
    current_admin: User = Depends(get_current_admin),
):
    """
    Update the processing status of a file.

    Used internally by the system to update status during RAG processing.

    - **file_id**: UUID of the file
    - **request**: New status (uploaded, processing, processed, failed)

    **Requires ADMIN role only.**
    """
    try:
        file_service = FileService(db=db)

        # Update status (admin can update any file)
        updated_document = file_service.update_file_status(str(file_id), request.status)

        logger.info(f"File status updated by admin {current_admin.id}: {file_id} -> {request.status}")

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
