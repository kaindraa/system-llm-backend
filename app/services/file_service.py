"""
File Storage Service

Provides abstraction layer for file storage operations.
Currently implements LocalFileStorage and GCSStorageProvider.
Can be extended to support other cloud storage services (S3, Azure, etc.).
"""

from abc import ABC, abstractmethod
from pathlib import Path
import os
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentStatus
from app.core.logging import get_logger
from google.cloud import storage as gcs_storage
from google.oauth2 import service_account

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

    @abstractmethod
    def stream(self, file_id: str, chunk_size: int = 1024 * 1024):
        """
        Stream file content in chunks.

        Args:
            file_id: Unique identifier for the file
            chunk_size: Size of each chunk to yield (default 1MB)

        Yields:
            Chunks of file content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
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

    def stream(self, file_id: str, chunk_size: int = 1024 * 1024):
        """Stream file from local storage in chunks"""
        try:
            file_path = self._get_file_path(file_id)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_id}")

            logger.info(f"[LocalFileStorage.stream] Streaming file: {file_id}, chunk_size: {chunk_size} bytes")

            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

            logger.info(f"[LocalFileStorage.stream] Streaming completed: {file_id}")

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[LocalFileStorage.stream] Error streaming file {file_id}: {str(e)}")
            raise


class GCSStorageProvider(FileStorageProvider):
    """Google Cloud Storage provider"""

    def __init__(self, bucket_name: str, credentials_path: str = None, project_id: str = None):
        """
        Initialize Google Cloud Storage provider.

        Args:
            bucket_name: GCS bucket name (e.g., 'gs://system-llm-storage')
            credentials_path: Path to service account JSON credentials file
            project_id: GCP project ID
        """
        # Remove 'gs://' prefix if present
        if bucket_name.startswith('gs://'):
            bucket_name = bucket_name[5:]

        self.bucket_name = bucket_name
        self.project_id = project_id
        self.chunk_size = 1024 * 1024  # 1MB chunks for streaming
        self.timeout = 300  # 5 minutes timeout for GCS operations

        try:
            # Initialize GCS client with timeout configuration
            if credentials_path and os.path.exists(credentials_path):
                # Use service account credentials from file
                logger.info(f"[GCSStorageProvider.__init__] Using credentials from file: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                self.client = gcs_storage.Client(
                    credentials=credentials,
                    project=project_id or credentials.project_id
                )
                logger.info(f"[GCSStorageProvider.__init__] Client initialized with service account credentials")
            else:
                # Use default application credentials (e.g., from Cloud Run environment)
                logger.info(f"[GCSStorageProvider.__init__] Using default application credentials (ADC/IAM)")
                self.client = gcs_storage.Client(project=project_id)
                logger.info(f"[GCSStorageProvider.__init__] Client initialized with default credentials")

            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"[GCSStorageProvider.__init__] Bucket reference created: {self.bucket_name}")

            # Verify bucket exists and is accessible
            logger.info(f"[GCSStorageProvider.__init__] Verifying bucket exists...")
            try:
                exists = self.bucket.exists()
                logger.info(f"[GCSStorageProvider.__init__] Bucket exists check result: {exists}")
                if not exists:
                    raise ValueError(f"GCS bucket does not exist or is not accessible: {self.bucket_name}")
            except Exception as check_error:
                logger.error(f"[GCSStorageProvider.__init__] Error checking bucket existence: {str(check_error)}", exc_info=True)
                raise ValueError(f"Cannot access GCS bucket '{self.bucket_name}': {str(check_error)}")

            logger.info(f"[GCSStorageProvider.__init__] Successfully initialized with bucket: gs://{self.bucket_name} (timeout={self.timeout}s)")

        except Exception as e:
            logger.error(f"[GCSStorageProvider.__init__] Initialization failed: {str(e)}", exc_info=True)
            raise

    def _get_blob_name(self, file_id: str) -> str:
        """Get GCS blob name for given file_id"""
        return f"uploads/{file_id}.pdf"

    def save(self, file_id: str, content: bytes) -> str:
        """Save file to GCS with verification"""
        max_retries = 3
        retry_delay = 1

        try:
            blob_name = self._get_blob_name(file_id)
            blob = self.bucket.blob(blob_name)

            # Upload file to GCS with retry logic
            for attempt in range(max_retries):
                try:
                    logger.info(f"[GCSStorageProvider.save] Uploading file - file_id: {file_id}, blob_name: {blob_name}, size: {len(content)} bytes (attempt {attempt + 1}/{max_retries})")

                    blob.upload_from_string(
                        content,
                        content_type='application/pdf',
                        timeout=self.timeout
                    )
                    logger.info(f"[GCSStorageProvider.save] Upload completed, verifying file exists...")

                    # VERIFICATION: Check if file actually exists in GCS
                    if not blob.exists():
                        raise Exception(f"File upload verification failed: file does not exist in GCS after upload")

                    # Verify file size matches
                    blob.reload()  # Refresh blob metadata from GCS
                    if blob.size and blob.size != len(content):
                        logger.warning(f"[GCSStorageProvider.save] Size mismatch: expected {len(content)}, got {blob.size}")

                    logger.info(f"[GCSStorageProvider.save] ✅ File verified successfully - size: {blob.size} bytes")
                    logger.info(f"File saved successfully to GCS: {file_id} at gs://{self.bucket_name}/{blob_name}")

                    # Return GCS path for storage in database
                    return f"gs://{self.bucket_name}/{blob_name}"

                except Exception as attempt_error:
                    if attempt < max_retries - 1:
                        import time
                        logger.warning(f"[GCSStorageProvider.save] Upload/verification failed (attempt {attempt + 1}/{max_retries}): {str(attempt_error)}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        raise attempt_error

        except Exception as e:
            logger.error(f"[GCSStorageProvider.save] ❌ Error saving file to GCS {file_id}: {str(e)}", exc_info=True)
            raise

    def get(self, file_id: str) -> bytes:
        """Retrieve file from GCS"""
        try:
            blob_name = self._get_blob_name(file_id)
            logger.info(f"[GCSStorageProvider.get] file_id: {file_id}, blob_name: {blob_name}, bucket: {self.bucket_name}")

            blob = self.bucket.blob(blob_name)
            logger.info(f"[GCSStorageProvider.get] Created blob reference: gs://{self.bucket_name}/{blob_name}")

            exists = blob.exists()
            logger.info(f"[GCSStorageProvider.get] Blob exists check result: {exists}")

            if not exists:
                logger.error(f"[GCSStorageProvider.get] File not found in GCS - file_id: {file_id}, blob_path: gs://{self.bucket_name}/{blob_name}")
                raise FileNotFoundError(f"File not found in GCS: {file_id} (path: gs://{self.bucket_name}/{blob_name})")

            # Download file content
            logger.info(f"[GCSStorageProvider.get] Downloading content from blob...")
            content = blob.download_as_bytes()

            logger.info(f"[GCSStorageProvider.get] File retrieved successfully - file_id: {file_id}, size: {len(content)} bytes")
            return content

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[GCSStorageProvider.get] Error retrieving file - file_id: {file_id}, error: {str(e)}", exc_info=True)
            raise

    def delete(self, file_id: str) -> None:
        """Delete file from GCS"""
        try:
            blob_name = self._get_blob_name(file_id)
            blob = self.bucket.blob(blob_name)

            if not blob.exists():
                raise FileNotFoundError(f"File not found in GCS: {file_id}")

            blob.delete()
            logger.info(f"File deleted successfully from GCS: {file_id}")

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error deleting file from GCS {file_id}: {str(e)}")
            raise

    def exists(self, file_id: str) -> bool:
        """Check if file exists in GCS"""
        try:
            blob_name = self._get_blob_name(file_id)
            blob = self.bucket.blob(blob_name)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking file existence in GCS {file_id}: {str(e)}")
            return False

    def stream(self, file_id: str, chunk_size: int = 10 * 1024 * 1024):
        """
        Stream file from GCS in chunks - OPTIMIZED FOR SPEED.

        Uses larger chunks (10MB default) for faster throughput.
        Downloads full blob and streams in chunks (GCS doesn't support efficient range requests).
        """
        try:
            blob_name = self._get_blob_name(file_id)
            blob = self.bucket.blob(blob_name)

            # Download full file from GCS with timeout handling
            # GCS library handles all optimizations internally
            logger.info(f"[GCSStorageProvider.stream] Starting download from GCS - file_id: {file_id}, blob: {blob_name}")

            try:
                full_content = blob.download_as_bytes(timeout=120)  # 2-minute timeout
            except Exception as gcs_error:
                logger.error(f"[GCSStorageProvider.stream] GCS download failed - file_id: {file_id}, error: {str(gcs_error)}", exc_info=True)
                raise

            if not full_content:
                raise FileNotFoundError(f"File is empty in GCS: {file_id}")

            logger.info(f"[GCSStorageProvider.stream] Downloaded {len(full_content)} bytes from GCS")

            # Stream in chunks for memory efficiency
            offset = 0
            total_size = len(full_content)

            while offset < total_size:
                chunk_end = min(offset + chunk_size, total_size)
                chunk = full_content[offset:chunk_end]

                if not chunk:
                    raise RuntimeError(f"Failed to read chunk at offset {offset}")

                yield chunk
                offset = chunk_end

            logger.info(f"[GCSStorageProvider.stream] Completed streaming file {file_id}")

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"[GCSStorageProvider.stream] Error streaming file {file_id}: {str(e)}", exc_info=True)
            raise


# Global instance - will be initialized in main.py based on config
storage_provider: FileStorageProvider = None


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
        self.logger.info(f"[FileService.get_file_content] Starting - file_id: {file_id}")
        document = self.get_file(file_id)
        self.logger.info(f"[FileService.get_file_content] Document found - filename: {document.filename}, file_path: {document.file_path}")
        self.logger.info(f"[FileService.get_file_content] Storage provider: {self.storage.__class__.__name__}")

        try:
            content = self.storage.get(document.filename)
            self.logger.info(f"[FileService.get_file_content] Successfully retrieved content - size: {len(content)} bytes")
            return content
        except Exception as e:
            self.logger.error(f"[FileService.get_file_content] Failed to retrieve file - file_id: {file_id}, error: {str(e)}", exc_info=True)
            raise

    def stream_file_content(self, file_id: str, chunk_size: int = 1024 * 1024):
        """
        Stream file content by document ID in chunks (memory efficient).

        This is the recommended method for downloads, especially for large files.
        It streams the file in chunks instead of loading everything into memory.

        Args:
            file_id: UUID of the document
            chunk_size: Size of each chunk to stream (default 1MB)

        Yields:
            Chunks of file content as bytes
        """
        self.logger.info(f"[FileService.stream_file_content] Starting - file_id: {file_id}, chunk_size: {chunk_size}")
        document = self.get_file(file_id)
        self.logger.info(f"[FileService.stream_file_content] Document found - filename: {document.filename}, storage: {self.storage.__class__.__name__}")

        try:
            # Stream from storage provider
            for chunk in self.storage.stream(document.filename, chunk_size=chunk_size):
                yield chunk
            self.logger.info(f"[FileService.stream_file_content] Successfully streamed file - file_id: {file_id}")
        except Exception as e:
            self.logger.error(f"[FileService.stream_file_content] Failed to stream file - file_id: {file_id}, error: {str(e)}", exc_info=True)
            raise

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

    def list_all_files(
        self,
        skip: int = 0,
        limit: int = 10,
        status: DocumentStatus = None
    ) -> tuple[list[Document], int]:
        """
        List ALL files from database with pagination (no user filter).

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Optional filter by document status

        Returns:
            Tuple of (documents list, total count)
        """
        query = self.db.query(Document)

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


def initialize_storage_provider(config) -> FileStorageProvider:
    """
    Initialize storage provider based on configuration.

    Args:
        config: Settings object from app.core.config

    Returns:
        Initialized FileStorageProvider instance
    """
    global storage_provider

    # Log configuration for debugging
    logger.info("="*60)
    logger.info("STORAGE PROVIDER INITIALIZATION")
    logger.info("="*60)
    logger.info(f"[CONFIG] STORAGE_TYPE: {config.STORAGE_TYPE}")
    logger.info(f"[CONFIG] GCS_BUCKET_NAME: {config.GCS_BUCKET_NAME}")
    logger.info(f"[CONFIG] GCS_PROJECT_ID: {config.GCS_PROJECT_ID}")
    logger.info(f"[CONFIG] GCS_CREDENTIALS_PATH: {config.GCS_CREDENTIALS_PATH}")

    storage_type = config.STORAGE_TYPE.lower()
    logger.info(f"[DECISION] Storage type (lowercase): '{storage_type}'")

    if storage_type == "gcs":
        logger.info("[CHOICE] Selected: GCS Storage Provider")
        logger.info(f"[VALIDATION] Checking GCS_BUCKET_NAME: {'PRESENT' if config.GCS_BUCKET_NAME else 'EMPTY'}")

        if not config.GCS_BUCKET_NAME:
            logger.error("[ERROR] GCS_BUCKET_NAME is not configured!")
            raise ValueError("GCS_BUCKET_NAME not configured")

        logger.info(f"[VALIDATION] GCS_CREDENTIALS_PATH: {config.GCS_CREDENTIALS_PATH if config.GCS_CREDENTIALS_PATH else 'None (will use ADC/IAM)'}")
        logger.info(f"[VALIDATION] GCS_PROJECT_ID: {config.GCS_PROJECT_ID if config.GCS_PROJECT_ID else 'Not set'}")

        try:
            logger.info("[INIT] Creating GCSStorageProvider instance...")
            storage_provider = GCSStorageProvider(
                bucket_name=config.GCS_BUCKET_NAME,
                credentials_path=config.GCS_CREDENTIALS_PATH if config.GCS_CREDENTIALS_PATH else None,
                project_id=config.GCS_PROJECT_ID if config.GCS_PROJECT_ID else None
            )
            logger.info("[SUCCESS] GCSStorageProvider initialized successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize GCSStorageProvider: {str(e)}")
            raise
    else:
        logger.info(f"[CHOICE] Selected: Local File Storage Provider")
        logger.info(f"[REASON] STORAGE_TYPE is '{storage_type}' (not 'gcs'), defaulting to local storage")
        try:
            logger.info("[INIT] Creating LocalFileStorage instance...")
            storage_provider = LocalFileStorage()
            logger.info("[SUCCESS] LocalFileStorage initialized successfully")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize LocalFileStorage: {str(e)}")
            raise

    logger.info("="*60)
    logger.info(f"✅ Storage provider initialized: {storage_provider.__class__.__name__}")
    logger.info("="*60)
    return storage_provider
