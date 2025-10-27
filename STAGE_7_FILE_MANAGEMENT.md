# Stage 7: File Management - Implementation Guide

## Overview

Stage 7 mengimplementasikan sistem manajemen file (PDF) dengan abstraction layer untuk file storage. Sistem dapat diskalakan untuk mendukung cloud storage nantinya.

## Architecture

### File Storage Provider Pattern

```
FileStorageProvider (Abstract Interface)
├── LocalFileStorage (Current Implementation)
│   └── Stores files di: storage/uploads/
└── S3FileStorage (Future Implementation)
    └── Stores files di: AWS S3 / Compatible Storage
```

Saat migration ke cloud, hanya perlu ganti 1-2 baris konfigurasi, tidak perlu refactor endpoint.

## Features Implemented

### 1. **POST /api/v1/files/upload**
Upload file PDF untuk learning materials.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf"
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "document.pdf",
  "file_size": 2048576,
  "mime_type": "application/pdf",
  "status": "uploaded",
  "uploaded_at": "2025-01-23T10:30:00+00:00"
}
```

**Validations:**
- ✅ File harus PDF (application/pdf)
- ✅ Max file size: 50MB
- ✅ Requires authentication
- ✅ File disimpan dengan unique UUID

---

### 2. **GET /api/v1/files**
List semua file milik user dengan pagination.

**Request:**
```bash
curl "http://localhost:8000/api/v1/files?skip=0&limit=10&status=processed" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Query Parameters:**
- `skip` (int, default=0): Offset untuk pagination
- `limit` (int, default=10, max=100): Jumlah item per halaman
- `status` (enum, optional): Filter by status (uploaded, processing, processed, failed)

**Response (200 OK):**
```json
{
  "files": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "550e8400-e29b-41d4-a716-446655440000",
      "original_filename": "document.pdf",
      "file_size": 2048576,
      "mime_type": "application/pdf",
      "status": "processed",
      "uploaded_at": "2025-01-23T10:30:00+00:00",
      "processed_at": "2025-01-23T10:35:00+00:00"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 10
}
```

---

### 3. **GET /api/v1/files/{file_id}**
Get detail file specific.

**Request:**
```bash
curl "http://localhost:8000/api/v1/files/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "document.pdf",
  "file_size": 2048576,
  "mime_type": "application/pdf",
  "status": "uploaded",
  "uploaded_at": "2025-01-23T10:30:00+00:00",
  "processed_at": null
}
```

**Error Response (404):**
```json
{
  "detail": "File with ID '550e8400-e29b-41d4-a716-446655440000' not found"
}
```

---

### 4. **GET /api/v1/files/{file_id}/download**
Download file PDF.

**Request:**
```bash
curl "http://localhost:8000/api/v1/files/550e8400-e29b-41d4-a716-446655440000/download" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o document.pdf
```

**Response:**
- Binary file content
- HTTP Header: `Content-Disposition: attachment; filename=document.pdf`
- Media Type: `application/pdf`

---

### 5. **DELETE /api/v1/files/{file_id}**
Delete file (dari storage dan database).

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/files/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response (204 No Content):**
```
(empty response)
```

**Error Responses:**
- 404: File not found
- 403: User doesn't have permission to delete this file
- 500: Server error

---

### 6. **PATCH /api/v1/files/{file_id}/status**
Update file processing status (untuk RAG pipeline).

**Request:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/files/550e8400-e29b-41d4-a716-446655440000/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "processing"}'
```

**Request Body:**
```json
{
  "status": "processing"  // uploaded, processing, processed, atau failed
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "550e8400-e29b-41d4-a716-446655440000",
  "original_filename": "document.pdf",
  "file_size": 2048576,
  "mime_type": "application/pdf",
  "status": "processing",
  "uploaded_at": "2025-01-23T10:30:00+00:00",
  "processed_at": null
}
```

---

## Database Schema

File metadata disimpan di table `document`:

```sql
CREATE TABLE document (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES user(id),
  filename VARCHAR(255) NOT NULL,           -- UUID filename di storage
  original_filename VARCHAR(255) NOT NULL,  -- Original filename dari user
  file_path VARCHAR(500) NOT NULL,          -- Lokasi file di storage
  file_size BIGINT NOT NULL,                -- Ukuran file dalam bytes
  mime_type VARCHAR(100),                   -- MIME type (application/pdf)
  status ENUM NOT NULL,                     -- uploaded, processing, processed, failed
  uploaded_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_status (status)
);
```

---

## File Storage Structure

```
system-llm-backend/
└── storage/
    └── uploads/
        ├── 550e8400-e29b-41d4-a716-446655440000.pdf
        ├── 660e8400-e29b-41d4-a716-446655440001.pdf
        └── ...
```

**Catatan:** Folder `storage/` harus di-ignore di .gitignore untuk mencegah commit file besar.

---

## Integration with RAG Pipeline (Stage 8)

Saat Stage 8 (RAG Pipeline) diimplementasikan:

1. File status di-update ke "processing" sebelum RAG processing dimulai
2. System membaca file dari storage menggunakan `FileService.get_file_content()`
3. File di-extract, chunked, dan di-embed
4. File status di-update ke "processed" setelah selesai
5. Jika ada error, status di-set ke "failed"

**Contoh code untuk Stage 8:**

```python
from app.services.file_service import FileService

file_service = FileService(db=db)

# 1. Update status ke processing
file_service.update_file_status(file_id, DocumentStatus.PROCESSING)

# 2. Get file content
content = file_service.get_file_content(file_id)

# 3. Process dengan RAG pipeline
chunks = rag_pipeline.process_pdf(content, file_id)

# 4. Update status ke processed
file_service.update_file_status(file_id, DocumentStatus.PROCESSED)
```

---

## Security Considerations

### ✅ Implemented Safeguards

1. **Ownership Verification**: User hanya bisa akses file mereka sendiri
2. **File Type Validation**: Only PDF files allowed
3. **Size Limits**: Max 50MB per file
4. **Authentication**: Semua endpoint require JWT token
5. **Error Handling**: Graceful error messages tanpa expose system internals

### ⚠️ Production Considerations

Saat deploy ke production:

1. **Increase storage limit** jika diperlukan (ubah `max_size` di `file.py`)
2. **Setup backup strategy** untuk folder `storage/`
3. **Configure cloud storage** (migrate ke S3 atau equivalent)
4. **Setup file cleanup** untuk deleted files
5. **Add virus scanning** untuk uploaded files (optional)

---

## Future Enhancements

### 1. Cloud Storage Migration (Stage 11)
Ganti `LocalFileStorage` dengan `S3FileStorage` atau cloud provider lainnya:

```python
# app/services/file_service.py
if ENVIRONMENT == "production":
    storage_provider = S3FileStorage(
        bucket_name="system-llm-files",
        region="us-east-1"
    )
else:
    storage_provider = LocalFileStorage()
```

### 2. Async File Processing
Untuk file besar, gunakan background task untuk RAG processing:

```python
from celery import shared_task

@shared_task
def process_pdf_async(file_id: str):
    """Process PDF in background"""
    file_service = FileService(db=db)
    file_service.update_file_status(file_id, DocumentStatus.PROCESSING)
    # ... RAG processing ...
```

### 3. File Versioning
Track multiple versions of same file:

```python
# Tambah kolom di Document model
version = Column(Integer, default=1)
parent_id = Column(UUID, ForeignKey("document.id"), nullable=True)
```

### 4. Virus Scanning
Integrate dengan ClamAV atau similar:

```python
def scan_file_for_virus(content: bytes) -> bool:
    """Returns True if file is clean"""
    result = clam_av_client.scan_stream(content)
    return result is None
```

---

## Testing

### Manual Testing dengan Postman/cURL

1. **Register & login user**
   ```bash
   POST /api/v1/auth/register
   POST /api/v1/auth/login  # Get JWT token
   ```

2. **Upload file**
   ```bash
   POST /api/v1/files/upload
   ```

3. **List files**
   ```bash
   GET /api/v1/files
   ```

4. **Download file**
   ```bash
   GET /api/v1/files/{file_id}/download
   ```

5. **Delete file**
   ```bash
   DELETE /api/v1/files/{file_id}
   ```

### Unit Tests (Optional)

Create `tests/test_file_service.py`:

```python
import pytest
from app.services.file_service import LocalFileStorage, FileService

def test_upload_file(db):
    content = b"PDF content here"
    file_service = FileService(db=db)

    document = file_service.create_file(
        user_id="user-uuid",
        filename="test-file-id",
        original_filename="test.pdf",
        content=content
    )

    assert document.id is not None
    assert document.status == DocumentStatus.UPLOADED

def test_file_ownership(db):
    """User can only access their own files"""
    # Setup: Create file for user A
    # Try: User B access file
    # Expect: 403 Forbidden
    pass
```

---

## Admin Dashboard

File dapat dimanage melalui admin dashboard:

- URL: `http://localhost:8000/admin`
- Menu: **Document** (untuk view/manage files)
- Fitur:
  - View list semua files dari semua users
  - Filter by status
  - View file metadata
  - Delete files
  - Update status (untuk testing)

---

## Troubleshooting

### Issue: "File not found" saat download

**Cause**: File dihapus dari storage tapi record masih di database

**Solution**:
```python
# Cleanup orphaned records
from app.services.file_service import FileService
file_service.delete_file(file_id)  # Will handle gracefully
```

### Issue: Permission denied saat save file

**Cause**: `storage/` folder tidak memiliki write permission

**Solution**:
```bash
# Create folder with correct permissions
mkdir -p storage/uploads
chmod 755 storage/uploads
```

### Issue: Out of disk space

**Cause**: Too many files in `storage/` folder

**Solution**:
- Implement cleanup task untuk old files
- Migrate ke cloud storage
- Add disk quota per user

---

## Summary

✅ File Management API fully implemented dengan:
- Upload file dengan validation
- Download file
- List file dengan pagination
- Delete file
- Update processing status
- Permission-based access control
- Scalable storage abstraction layer

**Next Steps for Stage 8 (RAG Pipeline):**
- Extract PDF content
- Create chunks
- Generate embeddings
- Store di vector DB
- Integrate dengan chat flow

---

**Created:** 2025-01-23
**Status:** ✅ Completed
**Stage:** 7 - File Management
