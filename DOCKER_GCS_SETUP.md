# Docker Setup untuk Google Cloud Storage (GCS)

Dokumentasi lengkap untuk menjalankan System LLM Backend di Docker dengan dukungan Google Cloud Storage.

## 📋 Daftar Isi

1. [Development (Local Storage)](#development-local-storage)
2. [Production (GCS)](#production-gcs)
3. [Switching Between Modes](#switching-between-modes)
4. [Troubleshooting](#troubleshooting)

---

## Development (Local Storage)

Untuk development, gunakan local storage di Docker. Ini adalah setup default.

### Step 1: Siapkan Environment

```bash
# Copy file environment development
cp .env.docker.local .env
```

Atau edit `.env` secara manual:
```env
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=storage/uploads
```

### Step 2: Build & Run Docker

```bash
# Build image
docker-compose build

# Run containers
docker-compose up -d
```

### Step 3: Verify Setup

```bash
# Check containers running
docker-compose ps

# View logs
docker-compose logs -f api

# Access API
curl http://localhost:8000/health
```

### Step 4: Upload Files (Test)

```bash
# Files akan disimpan di ./storage/uploads/ (di host machine)
curl -X POST http://localhost:8000/api/v1/files/upload \
  -F "file=@test.pdf" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Data Persistence

Files tersimpan di volume lokal:
```
system-llm-backend/
├── storage/
│   └── uploads/          # PDF files disimpan di sini
├── logs/                 # Application logs
└── ...
```

---

## Production (GCS)

Untuk production, gunakan Google Cloud Storage untuk penyimpanan file.

### Prerequisite

✅ Sudah setup GCS bucket: `gs://system-llm-storage`
✅ Sudah setup service account: `system-llm-storage@system-llm.iam.gserviceaccount.com`

### Step 1: Download Service Account Key

```bash
# Download dari Google Cloud Console atau gunakan gcloud CLI
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com
```

Simpan file `gcs-key.json` di root backend directory:
```
system-llm-backend/
├── gcs-key.json          # Service account key (JANGAN commit ke git!)
├── docker-compose.yml
├── Dockerfile
└── ...
```

### Step 2: Prepare Environment File

```bash
# Copy production environment template
cp .env.docker.production .env
```

Edit `.env` untuk update:
- `POSTGRES_PASSWORD` - Password database yang aman
- `DATABASE_URL` - Connection string ke Cloud SQL
- `SECRET_KEY` - Generate baru dengan `openssl rand -hex 32`
- `BACKEND_CORS_ORIGINS` - Domain frontend Anda

### Step 3: Enable Volume Mount (docker-compose.yml)

Uncomment volume mount untuk GCS key di docker-compose.yml:

```yaml
  api:
    volumes:
      - .:/app
      - /app/logs
      - ./gcs-key.json:/app/gcs-key.json:ro  # <-- UNCOMMENT INI
```

### Step 4: Build & Run

```bash
# Build image
docker-compose build

# Run containers
docker-compose up -d
```

### Step 5: Verify GCS Integration

```bash
# Check logs untuk GCS initialization
docker-compose logs -f api | grep "GCS\|storage"

# Expected output:
# 📦 Using GCS storage (bucket: system-llm-storage)
```

### Step 6: Test File Upload

```bash
# Upload file akan disimpan ke GCS
curl -X POST http://localhost:8000/api/v1/files/upload \
  -F "file=@test.pdf" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Verify di GCS Console atau gunakan gcloud:
gsutil ls gs://system-llm-storage/uploads/
```

---

## Switching Between Modes

### Local → GCS

```bash
# 1. Download GCS service account key
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com

# 2. Update .env
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=system-llm-storage
GCS_PROJECT_ID=system-llm
GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json

# 3. Uncomment volume mount di docker-compose.yml
# - ./gcs-key.json:/app/gcs-key.json:ro

# 4. Restart containers
docker-compose down
docker-compose up -d
```

### GCS → Local

```bash
# 1. Update .env
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=storage/uploads

# 2. Comment volume mount di docker-compose.yml
# # - ./gcs-key.json:/app/gcs-key.json:ro

# 3. Restart containers
docker-compose down
docker-compose up -d
```

---

## Detailed Configuration

### Environment Variables

#### Local Storage
```env
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=storage/uploads
```

#### GCS Storage
```env
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=system-llm-storage
GCS_PROJECT_ID=system-llm
GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json
```

### Docker Compose Structure

```yaml
api:
  environment:
    # Storage config
    - STORAGE_TYPE=${STORAGE_TYPE:-local}
    - LOCAL_STORAGE_PATH=${LOCAL_STORAGE_PATH:-storage/uploads}
    - GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
    - GCS_PROJECT_ID=${GCS_PROJECT_ID}
    - GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}
  volumes:
    - .:/app
    - /app/logs
    # Uncomment untuk GCS:
    # - ./gcs-key.json:/app/gcs-key.json:ro
```

---

## Troubleshooting

### Issue: "GCS bucket not found"

```
ERROR Failed to initialize storage provider: 404 Not found. Bucket 'system-llm-storage' does not exist.
```

**Solution:**
1. Pastikan bucket sudah dibuat: `gcloud storage buckets list`
2. Pastikan GCS_BUCKET_NAME di .env benar
3. Pastikan service account punya akses ke bucket

### Issue: "Permission denied" saat upload

```
ERROR Error saving file to GCS: 403 Forbidden
```

**Solution:**
1. Verify service account memiliki `roles/storage.objectAdmin`
2. Check GCS key validity: `gcloud iam service-accounts keys list`
3. Recreate key jika sudah expired

### Issue: "GOOGLE_APPLICATION_CREDENTIALS not found"

```
ERROR google.auth.exceptions.DefaultCredentialsError
```

**Solution:**
1. Pastikan gcs-key.json di root directory
2. Verify path di docker-compose.yml benar: `/app/gcs-key.json`
3. Check file permissions: `ls -la gcs-key.json`

### Issue: Files tidak appear di GCS

**Debug steps:**
```bash
# Check container logs
docker-compose logs -f api | grep -i "gcs\|save\|upload"

# Verify service account key
cat gcs-key.json

# List files di GCS
gsutil ls -r gs://system-llm-storage/

# Check GCS bucket permissions
gsutil iam ch serviceAccount:system-llm-storage@system-llm.iam.gserviceaccount.com:objectAdmin \
  gs://system-llm-storage
```

---

## Security Best Practices

### 1. Protect GCS Key

```bash
# Add to .gitignore
echo "gcs-key.json" >> .gitignore

# Set file permissions (Linux/Mac)
chmod 400 gcs-key.json

# Verify it's ignored
git status  # gcs-key.json tidak boleh muncul
```

### 2. Rotate Keys Regularly

```bash
# Delete old keys
gcloud iam service-accounts keys delete KEY_ID

# Create new key
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com
```

### 3. Use Least Privilege

Service account hanya perlu role:
- `roles/storage.objectAdmin` - Untuk read/write/delete di bucket

Hindari:
- ❌ `roles/owner` - Terlalu banyak permission
- ❌ Serviceaccount Editor di project level

### 4. Monitor Access

```bash
# View recent access logs
gcloud logging read "resource.type=gcs_bucket AND resource.labels.bucket_name=system-llm-storage" \
  --limit 50 --format json

# Setup Cloud Audit Logs
# Via Google Cloud Console > Bucket > Logs
```

---

## Performance Tips

### 1. Local Storage Development
- Lebih cepat untuk development (no network latency)
- Cocok untuk testing
- Limited by disk space

### 2. GCS Production
- Scalable untuk production
- Pay per usage
- Network latency ~100-500ms per operation

### 3. Caching Strategy

Untuk optimize GCS uploads:
```python
# Implement caching layer jika diperlukan
from functools import lru_cache

@lru_cache(maxsize=32)
def get_file_metadata(file_id):
    # Cache metadata untuk 5 menit
    return storage.get(file_id)
```

---

## Next Steps

1. ✅ Setup storage provider (done)
2. 📋 Monitor GCS costs via Cloud Console
3. 📋 Implement file backup strategy
4. 📋 Add file versioning (GCS versioning)
5. 📋 Setup lifecycle policies untuk old files

---

## Reference

- [Google Cloud Storage Python Client](https://cloud.google.com/python/docs/reference/storage/latest)
- [GCS Authentication](https://cloud.google.com/docs/authentication/getting-started)
- [Service Account Management](https://cloud.google.com/docs/authentication/managing-service-accounts)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
