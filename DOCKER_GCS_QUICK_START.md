# Docker + GCS Quick Start Guide

Setup cepat untuk menjalankan System LLM Backend di Docker dengan GCS.

## Mode: Development (Local Storage)

**Paling mudah untuk development & testing**

```bash
# 1. Copy environment file
cp .env.docker.local .env

# 2. Build & run
docker-compose build
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f api
```

Akses API: `http://localhost:8000/docs`

Data files disimpan: `./storage/uploads/`

---

## Mode: Production (GCS)

**Untuk production dengan Google Cloud Storage**

### 1. Download GCS Service Account Key

```bash
# Option A: Menggunakan gcloud CLI
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com

# Option B: Download dari Google Cloud Console
# IAM & Admin > Service Accounts > system-llm-storage > Keys > Create Key > JSON
```

Hasil: File `gcs-key.json` di root directory

### 2. Setup Environment

```bash
# Copy production environment
cp .env.docker.production .env

# Edit .env untuk customize:
# - POSTGRES_PASSWORD
# - DATABASE_URL
# - SECRET_KEY
# - BACKEND_CORS_ORIGINS
```

### 3. Enable GCS Volume Mount

Edit `docker-compose.yml`, uncomment line di service `api`:

```yaml
volumes:
  - .:/app
  - /app/logs
  - ./gcs-key.json:/app/gcs-key.json:ro  # <-- UNCOMMENT INI
```

### 4. Build & Run

```bash
docker-compose build
docker-compose up -d
```

### 5. Verify

```bash
# Check GCS initialization
docker-compose logs -f api | grep -i "gcs\|storage"

# Expected: "📦 Using GCS storage (bucket: system-llm-storage)"
```

---

## Quick Switching

### Local → GCS

```bash
# 1. Get service account key
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com

# 2. Update .env
echo "STORAGE_TYPE=gcs" >> .env
echo "GCS_BUCKET_NAME=system-llm-storage" >> .env
echo "GCS_PROJECT_ID=system-llm" >> .env
echo "GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json" >> .env

# 3. Uncomment volume di docker-compose.yml (line 45)

# 4. Restart
docker-compose restart api
```

### GCS → Local

```bash
# 1. Update .env
echo "STORAGE_TYPE=local" >> .env

# 2. Comment volume di docker-compose.yml (line 45)

# 3. Restart
docker-compose restart api
```

---

## Useful Commands

```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f api              # API logs
docker-compose logs -f postgres         # Database logs

# Restart API
docker-compose restart api

# Rebuild everything
docker-compose down
docker-compose build
docker-compose up -d

# Execute command di container
docker-compose exec api bash
docker-compose exec api python -c "from app.core.config import settings; print(settings.STORAGE_TYPE)"

# Stop all
docker-compose down
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `gcs-key.json not found` | Run: `gcloud iam service-accounts keys create gcs-key.json ...` |
| `Permission denied` | Check service account role: `roles/storage.objectAdmin` |
| `Storage not initialized` | Check logs: `docker-compose logs -f api` |
| `Can't connect to database` | Check postgres health: `docker-compose ps` |

---

## File Structure

```
system-llm-backend/
├── gcs-key.json              # ← Service account key (DO NOT COMMIT!)
├── .env                       # ← Environment file (DO NOT COMMIT!)
├── .env.docker.local         # Development template
├── .env.docker.production    # Production template
├── Dockerfile
├── docker-compose.yml
├── DOCKER_GCS_SETUP.md       # Full detailed guide
├── DOCKER_GCS_QUICK_START.md # This file
├── .gitignore                # Updated with gcs-key.json
├── .dockerignore             # Updated with gcs-key.json
└── app/
    ├── services/file_service.py      # GCS provider implementation
    ├── core/config.py                # Storage configuration
    └── main.py                       # Storage initialization
```

---

## Next Steps

1. ✅ Setup complete
2. Visit API docs: http://localhost:8000/docs
3. Upload test file via `/api/v1/files/upload`
4. Check GCS Console: https://console.cloud.google.com/storage/

---

**Full documentation**: See `DOCKER_GCS_SETUP.md` for complete guide
