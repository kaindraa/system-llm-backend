# System LLM Backend - Setup Reference

Complete reference untuk semua setup mode dan konfigurasi.

## 📊 Setup Mode Comparison

| Feature | Local Dev | Cloud SQL + GCS | Notes |
|---------|-----------|-----------------|-------|
| Database | PostgreSQL Container | Google Cloud SQL | Remote Cloud SQL lebih reliable |
| File Storage | Local Disk | Google Cloud Storage | GCS lebih scalable |
| Cloud SQL Proxy | ❌ No | ✅ Yes | Hanya untuk Cloud SQL |
| Docker Compose | docker-compose.yml | docker-compose.cloud-sql.yml | Separate config files |
| Data Persistence | Volume mount | Google Cloud | Cloud backup included |
| Cost | Free | GCP Pricing | Pay per usage |
| Network | Localhost only | GCP Network | Can deploy to production |

---

## 🚀 Quick Start by Use Case

### Use Case 1: Local Development

**Goal**: Development di laptop, test cepat

```bash
# 1. Setup
cp .env.docker.local .env
docker-compose build

# 2. Run
docker-compose up -d

# 3. Access
http://localhost:8000/docs

# 4. Files disimpan di
./storage/uploads/

# 5. Database
localhost:5432 (local PostgreSQL)
```

**Files**: `docker-compose.yml`, `.env.docker.local`

---

### Use Case 2: Cloud SQL + GCS (Production)

**Goal**: Production deployment di Google Cloud

```bash
# 1. Download Cloud SQL credentials
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com

# 2. Setup environment
cp .env.cloud-sql .env
nano .env  # Edit password & keys

# 3. Build & Run
docker-compose -f docker-compose.cloud-sql.yml build
docker-compose -f docker-compose.cloud-sql.yml up -d

# 4. Access
http://localhost:8000/docs

# 5. Files disimpan di
gs://system-llm-storage/

# 6. Database
Google Cloud SQL (asia-southeast2)
```

**Files**: `docker-compose.cloud-sql.yml`, `.env.cloud-sql`

---

### Use Case 3: Hybrid (Local DB + GCS)

**Goal**: Local development dengan remote file storage

```bash
# 1. Setup environment
cp .env.docker.local .env

# 2. Add GCS config
echo "STORAGE_TYPE=gcs" >> .env
echo "GCS_BUCKET_NAME=system-llm-storage" >> .env
echo "GCS_PROJECT_ID=system-llm" >> .env

# 3. Mount GCS key di docker-compose.yml
# - ./gcs-key.json:/app/gcs-key.json:ro  # UNCOMMENT

# 4. Run
docker-compose build
docker-compose up -d

# 5. Files disimpan di
gs://system-llm-storage/
```

**Files**: `docker-compose.yml`, `.env.docker.local` (modified)

---

## 🔧 Configuration Files Guide

### docker-compose.yml
- **Purpose**: Local development dengan PostgreSQL container
- **Database**: Local PostgreSQL (container)
- **Storage**: Local file system (default) atau GCS (with volume mount)
- **Use Case**: Development, testing
- **Command**: `docker-compose up -d`

### docker-compose.cloud-sql.yml
- **Purpose**: Production dengan Cloud SQL Proxy
- **Database**: Google Cloud SQL
- **Storage**: Google Cloud Storage (recommended)
- **Use Case**: Production deployment
- **Command**: `docker-compose -f docker-compose.cloud-sql.yml up -d`

### .env Files

#### .env.docker.local
- Purpose: Local development environment
- Database: Local PostgreSQL
- Storage: Local file system
- Use: `cp .env.docker.local .env && docker-compose up -d`

#### .env.docker.production
- Purpose: Production template (generic)
- Database: Placeholder untuk Cloud SQL
- Storage: GCS configuration
- Use: Reference hanya, edit sesuai kebutuhan

#### .env.cloud-sql
- Purpose: Cloud SQL specific environment
- Database: Cloud SQL connection string
- Storage: GCS
- Use: `cp .env.cloud-sql .env` untuk Cloud SQL setup

---

## 📝 Environment Variables Reference

### Database Configuration

```env
# Local PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/system_llm

# Cloud SQL dengan Proxy
DATABASE_URL=postgresql://postgres:PASSWORD@/system_llm?host=/cloudsql/PROJECT:REGION:INSTANCE

# Cloud SQL Proxy
CLOUD_SQL_INSTANCES=system-llm:asia-southeast2:system-llm-db
```

### Storage Configuration

```env
# Local Storage
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=storage/uploads

# Google Cloud Storage
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=system-llm-storage
GCS_PROJECT_ID=system-llm
GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json
```

### Application Settings

```env
# Security
SECRET_KEY=<use-openssl-rand-hex-32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application
PROJECT_NAME=System LLM
API_V1_PREFIX=/api/v1
DEBUG=True|False

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# LLM
OPENAI_API_KEY=sk-...
DEFAULT_LLM_MODEL=gpt-4-mini
```

---

## 🔄 Switching Between Modes

### Local → Cloud SQL

```bash
# 1. Get Cloud SQL credentials
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com

# 2. Setup environment
cp .env.cloud-sql .env
# Edit .env dengan password & API keys

# 3. Switch docker-compose
docker-compose down
docker-compose -f docker-compose.cloud-sql.yml up -d

# 4. Verify
docker-compose -f docker-compose.cloud-sql.yml logs -f api
```

### Cloud SQL → Local

```bash
# 1. Setup local environment
cp .env.docker.local .env

# 2. Switch back
docker-compose -f docker-compose.cloud-sql.yml down
docker-compose up -d

# 3. Verify
docker-compose logs -f api
```

### Local Storage → GCS

```bash
# 1. Get GCS key (jika belum)
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com

# 2. Edit .env
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=system-llm-storage
GCS_PROJECT_ID=system-llm
GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json

# 3. Uncomment volume mount di docker-compose.yml
# - ./gcs-key.json:/app/gcs-key.json:ro

# 4. Restart
docker-compose restart api

# 5. Verify
docker-compose logs api | grep -i "storage\|gcs"
```

### GCS → Local Storage

```bash
# 1. Edit .env
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=storage/uploads

# 2. Comment volume mount di docker-compose.yml
# # - ./gcs-key.json:/app/gcs-key.json:ro

# 3. Restart
docker-compose restart api

# 4. Verify
docker-compose logs api | grep -i "storage"
```

---

## 🐛 Troubleshooting Decision Tree

### Container Won't Start

```
docker-compose logs api

↓ Check error message ↓

"Cloud SQL Proxy failed to start"
→ See: CLOUD_SQL_SETUP.md → Troubleshooting
→ Check: CLOUD_SQL_INSTANCES format
→ Check: Service account permissions

"Connection refused"
→ Database not responding
→ Local: postgres container not healthy
→ Cloud SQL: instance not running

"Module not found"
→ Dependencies not installed
→ Solution: docker-compose build

"Permission denied"
→ GCS key issue
→ Solution: Check gcs-key.json path & permissions
```

### File Upload Issues

```
Upload fails

↓ Check storage type ↓

Local Storage:
→ Check ./storage/uploads/ directory exists
→ Check disk space
→ Check file permissions

GCS:
→ Check gcs-key.json is valid
→ Check GCS_BUCKET_NAME is correct
→ Check service account has permissions
```

### Database Connection Issues

```
Can't connect to database

↓ Check setup type ↓

Local PostgreSQL:
→ docker-compose ps (postgres should be healthy)
→ DATABASE_URL format
→ Port 5432 accessible

Cloud SQL:
→ Check CLOUD_SQL_INSTANCES format
→ Cloud SQL Proxy running
→ Service account authenticated
→ Cloud SQL instance status (RUNNABLE)
```

---

## 📚 Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| README.md | Project overview | First time setup |
| DOCKER_GCS_QUICK_START.md | Quick GCS setup | Using GCS for storage |
| DOCKER_GCS_SETUP.md | Detailed GCS guide | Need more details on GCS |
| CLOUD_SQL_QUICK_START.md | Quick Cloud SQL setup | Need Cloud SQL fast |
| CLOUD_SQL_SETUP.md | Detailed Cloud SQL | Deep dive on Cloud SQL |
| SETUP_REFERENCE.md | This file | When you're confused about modes |

---

## ✅ Verification Checklist

### Local Development

- [ ] `docker-compose ps` menunjukkan 3 containers: api, postgres, pgadmin
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `ls ./storage/uploads/` exists
- [ ] Database health check di `/health` returns true

### Cloud SQL Setup

- [ ] `gcloud sql instances list` menunjukkan instance
- [ ] `cat gcs-key.json` valid JSON
- [ ] `docker-compose -f docker-compose.cloud-sql.yml logs api | grep "Cloud SQL Proxy"` shows healthy
- [ ] `curl http://localhost:8000/health` returns 200

### GCS Setup

- [ ] `gsutil ls gs://system-llm-storage/` works
- [ ] Upload file, verify muncul di GCS console
- [ ] `docker-compose logs api | grep "Storage"` shows GCS

---

## 🚀 Deployment Paths

### Path 1: Local Testing → Cloud Run

```
Local Dev (docker-compose.yml)
    ↓
Cloud SQL + GCS (docker-compose.cloud-sql.yml)
    ↓
Test in Docker
    ↓
Deploy to Cloud Run (push to Google Artifact Registry)
    ↓
Production running on Cloud Run + Cloud SQL + GCS
```

### Path 2: Development → Self-Hosted

```
Local Dev (docker-compose.yml)
    ↓
Self-hosted server with Cloud SQL Proxy
    ↓
Push Dockerfile to server
    ↓
Run docker-compose.cloud-sql.yml on server
```

---

## 💰 Cost Estimation

### Local Development (Free)
- Docker/PostgreSQL: Free
- Storage: Local disk

### Cloud SQL + GCS (Low Cost)
- Cloud SQL: ~$30-50/month (shared instance)
- GCS Storage: ~$0.02 per GB/month
- GCS Operations: ~$0.004 per 10,000 writes
- Cloud Run: Pay per invocation (~free for low traffic)

**Example**: 100GB files, 1000 uploads/month = ~$30-60/month

---

## 🔐 Security Checklist

- [ ] Never commit `.env` or `gcs-key.json` to git
- [ ] Use strong passwords (20+ characters)
- [ ] Rotate credentials regularly
- [ ] Enable Cloud SQL automatic backups
- [ ] Enable Cloud Audit Logs
- [ ] Use minimal IAM permissions
- [ ] SSL/TLS for all connections
- [ ] Keep dependencies updated

---

## 📞 Getting Help

1. **Quick question**: Check this file
2. **Need GCS details**: Read `DOCKER_GCS_SETUP.md`
3. **Need Cloud SQL details**: Read `CLOUD_SQL_SETUP.md`
4. **Docker issue**: `docker-compose logs -f api`
5. **Cloud issue**: `gcloud logging read`

---

**Version**: 1.0
**Last Updated**: 2025-11-01
**Status**: Production Ready
