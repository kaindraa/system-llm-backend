"""
File Storage Service

Provides abstraction layer for file storage operations.
Currently implements LocalFileStorage for development.
Can be extended to support cloud storage (S3, Azure, etc.) in the future.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import os
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileStorageProvider(ABC):
    """Abstract base class for file storage providers"""

    @abstractmethod
    def save(self, file_id: str, content: bytes) -> str:
        """
        Save file content and return file path/reference.

        Args:
            file_id: Unique identifier for the file
            content: File content as bytes

        Returns:
            File path or reference (for later retrieval)
        """
        pass

    @abstractmethod
    def get(self, file_id: str) -> bytes:
        """
        Retrieve file content by file_id.

        Args:
            file_id: Unique identifier for the file

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    def delete(self, file_id: str) -> None:
        """
        Delete file by file_id.

        Args:
            file_id: Unique identifier for the file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    def exists(self, file_id: str) -> bool:
        """
        Check if file exists.

        Args:
            file_id: Unique identifier for the file

        Returns:
            True if file exists, False otherwise
        """
        pass


class LocalFileStorage(FileStorageProvider):
    """Local file system storage provider"""

    def __init__(self, base_path: str = "storage/uploads"):
        """
        Initialize local file storage.

        Args:
            base_path: Base directory for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalFileStorage initialized with base_path: {self.base_path}")

    def _get_file_path(self, file_id: str) -> Path:
        """Get full file path for given file_id"""
        return self.base_path / f"{file_id}.pdf"

    def save(self, file_id: str, content: bytes) -> str:
        """Save file to local storage"""
        try:
            file_path = self._get_file_path(file_id)

            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(content)

            logger.info(f"File saved successfully: {file_id} at {file_path}")

            # Return relative path for storage in database
            return str(file_path)

        except Exception as e:
            logger.error(f"Error saving file {file_id}: {str(e)}")
            raise

    def get(self, file_id: str) -> bytes:
        """Retrieve file from local storage"""
        try:
            file_path = self._get_file_path(file_id)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_id}")

            with open(file_path, 'rb') as f:
                content = f.read()

            logger.info(f"File retrieved successfully: {file_id}")
            return content

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {str(e)}")
            raise

    def delete(self, file_id: str) -> None:
        """Delete file from local storage"""
        try:
            file_path = self._get_file_path(file_id)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_id}")

            file_path.unlink()
            logger.info(f"File deleted successfully: {file_id}")

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise

    def exists(self, file_id: str) -> bool:
        """Check if file exists in local storage"""
        return self._get_file_path(file_id).exists()


# Global instance - will be initialized in main.py or config
storage_provider: FileStorageProvider = LocalFileStorage()


class FileService:
    """Service for managing file operations with database"""

    def __init__(self, db: Session, storage: FileStorageProvider = None):
        """
        Initialize file service.

        Args:
            db: SQLAlchemy session
            storage: Storage provider instance (defaults to global storage_provider)
        """
        self.db = db
        self.storage = storage or storage_provider
        self.logger = get_logger(__name__)

    def create_file(
        self,
        user_id: str,
        filename: str,
        original_filename: str,
        content: bytes,
        mime_type: str = "application/pdf"
    ) -> Document:
        """
        Create and save a new file.

        Args:
            user_id: UUID of the user uploading the file
            filename: System filename (usually UUID)
            original_filename: Original filename from user
            content: File content as bytes
            mime_type: MIME type of the file

        Returns:
            Created Document instance
        """
        try:
            # Save file to storage
            file_path = self.storage.save(filename, content)

            # Create document record
            document = Document(
                user_id=user_id,
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=len(content),
                mime_type=mime_type,
                status=DocumentStatus.UPLOADED
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            self.logger.info(f"File created: {filename} for user {user_id}")
            return document

        except Exception as e:
            self.db.rollback()
            # Try to clean up the file if DB operation failed
            try:
                self.storage.delete(filename)
            except Exception:
                pass
            self.logger.error(f"Error creating file: {str(e)}")
            raise

    def get_file(self, file_id: str) -> Document:
        """
        Get file metadata by ID.

        Args:
            file_id: UUID of the document

        Returns:
            Document instance
        """
        document = self.db.query(Document).filter(Document.id == file_id).first()
        if not document:
            raise FileNotFoundError(f"Document not found: {file_id}")
        return document

    def get_file_content(self, file_id: str) -> bytes:
        """
        Get file content by document ID.

        Args:
            file_id: UUID of the document

        Returns:
            File content as bytes
        """
        document = self.get_file(file_id)
        return self.storage.get(document.filename)

    def list_files(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10,
        status: DocumentStatus = None
    ) -> tuple[list[Document], int]:
        """
        List files for a user with pagination.

        Args:
            user_id: UUID of the user
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional filter by document status

        Returns:
            Tuple of (documents list, total count)
        """
        query = self.db.query(Document).filter(Document.user_id == user_id)

        if status:
            query = query.filter(Document.status == status)

        total = query.count()
        documents = query.order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()

        return documents, total

    def delete_file(self, file_id: str, user_id: str = None) -> bool:
        """
        Delete a file (both from storage and database).

        Args:
            file_id: UUID of the document
            user_id: Optional UUID to verify ownership

        Returns:
            True if successful
        """
        try:
            document = self.get_file(file_id)

            # Verify ownership if user_id provided
            if user_id and document.user_id != user_id:
                raise PermissionError("User does not have permission to delete this file")

            # Delete from storage
            self.storage.delete(document.filename)

            # Delete from database
            self.db.delete(document)
            self.db.commit()

            self.logger.info(f"File deleted: {file_id}")
            return True

        except FileNotFoundError:
            # File doesn't exist in storage, but try to delete DB record
            try:
                document = self.get_file(file_id)
                self.db.delete(document)
                self.db.commit()
                return True
            except FileNotFoundError:
                return False
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error deleting file: {str(e)}")
            raise

    def update_file_status(self, file_id: str, status: DocumentStatus) -> Document:
        """
        Update file processing status.

        Args:
            file_id: UUID of the document
            status: New status

        Returns:
            Updated Document instance
        """
        try:
            document = self.get_file(file_id)
            document.status = status

            if status == DocumentStatus.PROCESSED:
                document.processed_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(document)

            self.logger.info(f"File status updated: {file_id} -> {status}")
            return document

        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating file status: {str(e)}")
            raise
