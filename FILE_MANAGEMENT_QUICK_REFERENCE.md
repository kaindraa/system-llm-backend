# File Management - Quick Reference

## 📁 Files Created/Modified

### New Files Created
```
✅ app/services/file_service.py           - File storage abstraction layer
✅ app/schemas/file.py                    - Pydantic schemas for API
✅ app/api/v1/endpoints/file.py           - File management endpoints
✅ STAGE_7_FILE_MANAGEMENT.md             - Detailed documentation
✅ example_file_api_usage.py              - Example test script
✅ FILE_MANAGEMENT_QUICK_REFERENCE.md     - This file
```

### Modified Files
```
✅ app/main.py                            - Added file router import & registration
```

### Existing Models (Already Available)
```
✅ app/models/document.py                 - Document model (dengan status enum)
✅ app/admin/views.py                     - DocumentAdmin view
```

---

## 🚀 Quick Start

### 1. Test Using Example Script
```bash
cd system-llm-backend
python example_file_api_usage.py
```

This will:
- Register a test user
- Login and get JWT token
- Upload a sample PDF
- List files
- Update file status
- Download file
- Delete file
- Verify deletion

### 2. Manual Testing with cURL

**Register user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123",
    "full_name": "Test Student",
    "role": "student"
  }'
```

**Login:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "password123"
  }'
```
Save the `access_token` from response.

**Upload file:**
```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

**List files:**
```bash
curl "http://localhost:8000/api/v1/files" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Test in Swagger UI
```
http://localhost:8000/docs
```

Look for **Files** section to test all endpoints interactively.

---

## 📋 API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---|
| POST | `/api/v1/files/upload` | Upload PDF file | ✅ Yes |
| GET | `/api/v1/files` | List user's files | ✅ Yes |
| GET | `/api/v1/files/{file_id}` | Get file detail | ✅ Yes |
| GET | `/api/v1/files/{file_id}/download` | Download file | ✅ Yes |
| DELETE | `/api/v1/files/{file_id}` | Delete file | ✅ Yes |
| PATCH | `/api/v1/files/{file_id}/status` | Update file status | ✅ Yes |

---

## 🏗️ Architecture: File Storage Provider Pattern

```
┌─────────────────────────────────────┐
│   File Management API Endpoints      │
│   (app/api/v1/endpoints/file.py)    │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   FileService                        │
│   (app/services/file_service.py)    │
│   - Create, read, delete, update    │
│   - Database operations              │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│   FileStorageProvider (Abstract)    │
│                                      │
│   ├─ LocalFileStorage (Current)     │
│   │  └─ Stores in: storage/uploads/ │
│   │                                  │
│   └─ S3FileStorage (Future)         │
│      └─ Stores in: AWS S3           │
└─────────────────────────────────────┘
```

**Keuntungan:**
- ✅ Easy to extend dengan new storage providers
- ✅ No endpoint changes when migrating storage
- ✅ Mockable untuk testing
- ✅ Single responsibility principle

---

## 🔒 Security Features

### ✅ Implemented

1. **Authentication**: All endpoints require valid JWT token
2. **Authorization**: Users can only access their own files
3. **Input Validation**:
   - Only PDF files allowed
   - File size limit: 50MB
   - Filename validation
4. **Error Handling**:
   - Graceful error messages
   - No system internals exposed
5. **Logging**: All operations logged for audit trail

### ⚠️ Consider for Production

1. **Virus Scanning**: Integrate with ClamAV or similar
2. **File Quotas**: Limit total storage per user
3. **Rate Limiting**: Prevent upload bombing
4. **Encryption**: Encrypt files at rest (if sensitive data)
5. **Access Logging**: Log all download/access events

---

## 📊 Database Schema

**Table: `document`**
```sql
id              UUID PRIMARY KEY        -- File unique identifier
user_id         UUID NOT NULL           -- Owner of the file
filename        VARCHAR(255)            -- System filename (UUID)
original_filename VARCHAR(255)          -- Original filename from user
file_path       VARCHAR(500)            -- Path to file in storage
file_size       BIGINT                  -- File size in bytes
mime_type       VARCHAR(100)            -- MIME type (e.g., application/pdf)
status          ENUM                    -- uploaded, processing, processed, failed
uploaded_at     TIMESTAMP               -- When file was uploaded
processed_at    TIMESTAMP               -- When processing completed

INDEXES:
- user_id (for listing user's files)
- status (for filtering by processing status)
```

---

## 🔄 Integration Points

### Current Integration (Already Working)
- ✅ Authentication (use JWT from auth endpoints)
- ✅ User authorization (automatic via `get_current_user` dependency)
- ✅ Database (uses existing SQLAlchemy session)
- ✅ Logging (uses existing logger)

### Future Integration (Stage 8 - RAG)
```python
# Example: How RAG pipeline will use file service
from app.services.file_service import FileService
from app.services.rag_pipeline import RAGPipeline

file_service = FileService(db=db)
rag_pipeline = RAGPipeline()

# 1. Get uploaded files
documents, _ = file_service.list_files(user_id=user_id, status="uploaded")

# 2. Process each file
for document in documents:
    file_service.update_file_status(str(document.id), "processing")

    try:
        # Get file content
        content = file_service.get_file_content(str(document.id))

        # Process with RAG
        chunks = rag_pipeline.process_pdf(content)

        # Mark as completed
        file_service.update_file_status(str(document.id), "processed")
    except Exception as e:
        file_service.update_file_status(str(document.id), "failed")
```

---

## 📦 Storage Structure

```
system-llm-backend/
├── storage/                          # ⚠️ Add to .gitignore
│   └── uploads/
│       ├── 550e8400-e29b-....pdf    # File 1
│       ├── 660e8400-e29b-....pdf    # File 2
│       └── ...
├── app/
│   ├── services/
│   │   ├── file_service.py          # ✅ New
│   │   └── ...
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── file.py          # ✅ New
│   │           └── ...
│   ├── schemas/
│   │   ├── file.py                  # ✅ New
│   │   └── ...
│   └── ...
└── ...
```

**Important:** Make sure `.gitignore` includes:
```
storage/
storage/uploads/
*.pdf
```

---

## 🧪 Testing

### Option 1: Use Provided Example Script
```bash
python example_file_api_usage.py
```

### Option 2: Use Swagger UI
```
http://localhost:8000/docs
```
Click on "Files" section and try endpoints.

### Option 3: Write Unit Tests
Create `tests/test_file_service.py`:
```python
import pytest
from app.services.file_service import LocalFileStorage

def test_upload_and_retrieve():
    storage = LocalFileStorage()
    content = b"test content"

    path = storage.save("test-file", content)
    retrieved = storage.get("test-file")

    assert retrieved == content

    storage.delete("test-file")
    assert not storage.exists("test-file")
```

### Option 4: Admin Dashboard
```
http://localhost:8000/admin
```
Navigate to **Document** section to manage files.

---

## 🎯 Migration to Cloud Storage (Preparation)

When you're ready to migrate to S3 or similar:

### Step 1: Create S3FileStorage class
```python
# app/services/file_service.py

class S3FileStorage(FileStorageProvider):
    def __init__(self, bucket_name: str, region: str):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket = bucket_name

    def save(self, file_id: str, content: bytes) -> str:
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=f"uploads/{file_id}.pdf",
            Body=content
        )
        return f"s3://{self.bucket}/uploads/{file_id}.pdf"

    # ... implement other methods
```

### Step 2: Update config
```python
# app/core/config.py or main.py

if ENVIRONMENT == "production":
    storage_provider = S3FileStorage(
        bucket_name=settings.S3_BUCKET,
        region=settings.AWS_REGION
    )
else:
    storage_provider = LocalFileStorage()
```

### Step 3: No endpoint changes needed! 🎉
All existing API endpoints work without modifications.

---

## 🛠️ Troubleshooting

### Issue: "File uploaded but can't download"
**Cause**: File path mismatch or file not in storage
**Fix**: Check if `storage/uploads/` folder exists and has correct permissions
```bash
mkdir -p storage/uploads
chmod 755 storage/uploads
```

### Issue: "Only PDF files are allowed" error
**Cause**: Wrong content-type header
**Fix**: Make sure file is actual PDF and upload with correct type
```bash
curl -F "file=@document.pdf" ...
```

### Issue: "User doesn't have permission" (403)
**Cause**: User trying to access file from another user
**Fix**: Use correct file_id and ensure you're authenticated

### Issue: "File not found" after upload
**Cause**: Database transaction not committed
**Fix**: Check database logs and ensure migrations ran successfully

---

## 📝 Next Steps

### For Stage 8 (RAG Pipeline)
1. Create `app/services/rag_pipeline.py`
2. Implement PDF text extraction (PyPDF2, pdfplumber, etc.)
3. Create chunking strategy
4. Generate embeddings
5. Store in vector DB
6. Integrate with chat flow

### For Stage 10 (UI)
1. Create file upload form
2. Display file list
3. Add download button
4. Show processing status
5. Integrate with chat interface

### For Stage 11 (Deployment)
1. Migrate to cloud storage (S3)
2. Setup file backup strategy
3. Configure CDN for downloads
4. Add virus scanning
5. Setup monitoring

---

## 📞 Quick Reference Commands

```bash
# Run tests
python example_file_api_usage.py

# View logs
tail -f logs/app.log

# Access admin
open http://localhost:8000/admin

# View Swagger
open http://localhost:8000/docs

# Count files in storage
ls storage/uploads/ | wc -l

# Cleanup storage
rm -rf storage/uploads/*
```

---

## ✅ Checklist - File Management Complete!

- ✅ File upload endpoint with validation
- ✅ File listing with pagination
- ✅ File download with proper headers
- ✅ File deletion (from storage & DB)
- ✅ File status management
- ✅ Permission-based access control
- ✅ Abstraction layer for storage (local + future cloud)
- ✅ Database integration
- ✅ Logging & error handling
- ✅ API documentation (Swagger)
- ✅ Admin dashboard integration
- ✅ Example test script
- ✅ Complete documentation

**Status**: 🎉 **READY FOR STAGE 8 (RAG PIPELINE)**

---

Generated: 2025-01-23
Stage: 7 - File Management
