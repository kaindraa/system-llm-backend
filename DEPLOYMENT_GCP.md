# 🚀 Deployment Guide - GCP (Cloud Run)

## Overview

Backend siap di-deploy ke **Google Cloud Run** dengan:
- **Containerized** application dengan Docker
- **Cloud SQL Proxy** untuk koneksi database yang aman
- **Google Cloud Storage** untuk file management
- **Automatic scaling** berdasarkan traffic
- **Zero-downtime** deployments

---

## 📋 Deployment Files

### Docker Configuration

| File | Purpose | Usage |
|------|---------|-------|
| **Dockerfile** | GCP Production | `docker build -f Dockerfile -t system-llm-api:prod .` |
| **Dockerfile.local** | Local Development | `docker build -f Dockerfile.local -t system-llm-api:local .` |
| **entrypoint.sh** | Cloud Run Startup Script | Manages Cloud SQL Proxy + FastAPI |

### Configuration Files

| File | Type | Status |
|------|------|--------|
| **.env** | GCP Configuration | ✅ Active |
| **.env.remote** | GCP Template | 📖 Reference |
| **docker-compose.yml** | GCP Local Testing | ✅ Active |

---

## 🏗️ Architecture

### Cloud Run Setup
```
┌─────────────────────────────────────────────────────────────┐
│                    Cloud Run Service                         │
│                  (system-llm-api:prod)                       │
│                                                              │
│  ┌────────────────┐         ┌──────────────────────────┐   │
│  │ FastAPI App    │ ◄──────►│  Cloud SQL Proxy         │   │
│  │ (port 8000)    │         │  (localhost:5432)        │   │
│  └────────────────┘         └──────────────────────────┘   │
│                                     │                        │
│                                     │ TCP 5432               │
└─────────────────────────────────────┼────────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  Cloud SQL       │
                            │ system-llm-db    │
                            │ (asia-southeast2)│
                            └──────────────────┘
```

### Storage Setup
```
┌──────────────────────────────────┐
│     Google Cloud Storage         │
│    system-llm-storage bucket     │
│                                  │
│  ├── uploads/                    │
│  │   ├── {uuid}.pdf              │
│  │   └── ...                     │
│  └── chunks/                     │
│      ├── {uuid}.txt              │
│      └── ...                     │
└──────────────────────────────────┘
```

---

## 📦 Building Docker Image

### Prerequisites
```bash
# Install Docker
# https://docs.docker.com/install/

# Setup GCP authentication
gcloud auth configure-docker gcr.io
```

### Build for GCP (Cloud Run)
```bash
# Build image
docker build -f Dockerfile -t system-llm-api:prod .

# Tag for GCP Container Registry
docker tag system-llm-api:prod gcr.io/system-llm/system-llm-api:prod

# Push to GCP Container Registry
docker push gcr.io/system-llm/system-llm-api:prod
```

### Build for Local Testing
```bash
docker build -f Dockerfile.local -t system-llm-api:local .
```

---

## 🚀 Deployment to Cloud Run

### Option 1: Using gcloud CLI

```bash
# Deploy to Cloud Run
gcloud run deploy system-llm-api \
  --image gcr.io/system-llm/system-llm-api:prod \
  --platform managed \
  --region asia-southeast2 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --env-vars-file .env.cloud-run \
  --service-account system-llm-sa@system-llm.iam.gserviceaccount.com \
  --add-cloudsql-instances system-llm:asia-southeast2:system-llm-db \
  --set-cloudsql-instances system-llm:asia-southeast2:system-llm-db \
  --allow-unauthenticated
```

### Option 2: Using Google Cloud Console
1. Go to **Cloud Run**
2. Click **Create Service**
3. Choose **Deploy one revision from an existing image**
4. Select image: `gcr.io/system-llm/system-llm-api:prod`
5. Configure:
   - **Service name**: `system-llm-api`
   - **Region**: `asia-southeast2`
   - **Memory**: `2 GB`
   - **CPU**: `2`
   - **Timeout**: `3600 seconds` (1 hour)
   - **Minimum instances**: `0` (untuk cost savings)
   - **Maximum instances**: `10`
6. Click **Create**

### Option 3: Using Cloud Build (CI/CD)

Create `cloudbuild.yaml`:
```yaml
steps:
  # Build image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'Dockerfile', '-t', 'gcr.io/$PROJECT_ID/system-llm-api:$COMMIT_SHA', '.']

  # Push to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/system-llm-api:$COMMIT_SHA']

  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
      - run
      - --filename=k8s
      - --image=gcr.io/$PROJECT_ID/system-llm-api:$COMMIT_SHA
      - --location=asia-southeast2
      - --cluster=system-llm

images:
  - 'gcr.io/$PROJECT_ID/system-llm-api:$COMMIT_SHA'
```

Deploy:
```bash
gcloud builds submit --config cloudbuild.yaml
```

---

## 🔐 Environment Configuration for Cloud Run

### Create `.env.cloud-run` file
```bash
# Database
POSTGRES_USER=llm_user
POSTGRES_PASSWORD=anLLMUser123123
POSTGRES_DB=system_llm
DATABASE_URL=postgresql://llm_user:anLLMUser123123@127.0.0.1:5432/system_llm

# Storage
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=system-llm-storage
GCS_PROJECT_ID=system-llm
GCS_CREDENTIALS_PATH=/app/credentials/system-llm-storage-key.json

# API Keys (load from Secret Manager)
OPENAI_API_KEY=<from-secret-manager>
OPENROUTER_API_KEY=<from-secret-manager>
GOOGLE_API_KEY=<from-secret-manager>

# Security
SECRET_KEY=<from-secret-manager>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
BACKEND_CORS_ORIGINS=["https://system-llm-chat.fly.dev","https://yourdomain.com"]

# Cloud Run
PORT=8080
DEBUG=false
CLOUD_SQL_INSTANCES=system-llm:asia-southeast2:system-llm-db

# Admin
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=<secure-password>
```

### Store Secrets in Secret Manager
```bash
# Create secrets
echo "sk-proj-..." | gcloud secrets create OPENAI_API_KEY --data-file=-
echo "sk-or-v1-..." | gcloud secrets create OPENROUTER_API_KEY --data-file=-
echo "<secure-key>" | gcloud secrets create SECRET_KEY --data-file=-

# Reference in deployment
--set-secrets OPENAI_API_KEY=OPENAI_API_KEY:latest
```

---

## 📊 Docker Compose for Local Testing (before deployment)

### Test image locally
```bash
# Start services
docker-compose -f docker-compose.yml up -d

# Verify
curl http://localhost:8000/api/v1/health

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

---

## ✅ Pre-Deployment Checklist

### GCP Resources
- [ ] Cloud SQL instance created: `system-llm:asia-southeast2:system-llm-db`
- [ ] Cloud Storage bucket created: `system-llm-storage`
- [ ] Service account created: `system-llm-sa`
- [ ] Service account has permissions:
  - [ ] Cloud SQL Client
  - [ ] Storage Object Creator
  - [ ] Storage Object Viewer

### Application
- [ ] `.env` file configured with GCP settings
- [ ] All API keys added to Secret Manager
- [ ] Database migrations run (alembic upgrade head)
- [ ] Local testing passed with docker-compose

### Docker
- [ ] Dockerfile builds successfully
- [ ] Image tested locally with docker-compose
- [ ] Image pushed to Container Registry
- [ ] Image tagged properly: `gcr.io/system-llm/system-llm-api:prod`

### Cloud Run
- [ ] Memory set to 2GB (minimum recommended)
- [ ] CPU set to 2 (for database connections)
- [ ] Timeout set to 3600s (for file uploads)
- [ ] Cloud SQL instance linked
- [ ] Service account configured
- [ ] Health check endpoint accessible
- [ ] Logging enabled

---

## 🔍 Post-Deployment Verification

### Check Cloud Run Service
```bash
# Get service details
gcloud run services describe system-llm-api --region asia-southeast2

# View logs
gcloud run services logs read system-llm-api --region asia-southeast2 --limit 50

# Test health endpoint
curl https://system-llm-api-<hash>-southeast2.a.run.app/health
```

### Test API Endpoints
```bash
# Health check
curl https://system-llm-api-<hash>-southeast2.a.run.app/api/v1/health

# Get API info
curl https://system-llm-api-<hash>-southeast2.a.run.app/api/v1/

# Test with authentication
curl -X POST https://system-llm-api-<hash>-southeast2.a.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'
```

### Check Database Connectivity
```bash
# Via Cloud Run logs
gcloud run services logs read system-llm-api --region asia-southeast2 | grep -i database

# Via Cloud SQL Proxy logs
gcloud logging read "resource.type=cloudsql_database" --limit 10
```

### Monitor Storage Usage
```bash
# List GCS bucket contents
gsutil ls -r gs://system-llm-storage/

# Get bucket size
gsutil du -s gs://system-llm-storage/
```

---

## 🔄 Update Deployment

### Deploy new version
```bash
# Build and push new image
docker build -f Dockerfile -t gcr.io/system-llm/system-llm-api:prod .
docker push gcr.io/system-llm/system-llm-api:prod

# Deploy new version
gcloud run deploy system-llm-api \
  --image gcr.io/system-llm/system-llm-api:prod \
  --region asia-southeast2
```

### Rollback to previous version
```bash
# List revisions
gcloud run revisions list --service system-llm-api --region asia-southeast2

# Rollback to specific revision
gcloud run services update-traffic system-llm-api \
  --to-revisions REVISION_NAME=100 \
  --region asia-southeast2
```

---

## 💰 Cost Optimization

### Recommendations
1. **Minimum instances**: Set to 0 (default) for cost savings
2. **Maximum instances**: 10 (adjust based on traffic)
3. **Memory**: 2GB minimum for database + application
4. **CPU**: 2 recommended (1 might bottleneck)
5. **Cloud SQL**: Use shared instance or scaling configuration

### Cost Estimation
```
Cloud Run:
- Requests: $0.40 per 1M requests
- GB-seconds: $0.00002778 per GB-second
- vCPU-seconds: $0.00004167 per vCPU-second

Cloud SQL:
- Instance: ~$15/month (db-f1-micro)
- Storage: $0.18 per GB/month

Cloud Storage:
- Storage: $0.020 per GB/month
- Requests: $0.004 per 1k read operations
```

---

## 🐛 Troubleshooting

### Issue: Cloud Run service won't start
```bash
# Check logs
gcloud run services logs read system-llm-api --region asia-southeast2 --limit 100

# Common causes:
# 1. Database not accessible - check Cloud SQL instance
# 2. Credentials not mounted - check service account
# 3. Port mismatch - check PORT env var in entrypoint.sh
```

### Issue: Database connection timeout
```bash
# Verify Cloud SQL instance is running
gcloud sql instances describe system-llm-db

# Verify service account can access Cloud SQL
gcloud sql instances get-iam-policy system-llm-db

# Check Cloud SQL Proxy logs in Cloud Run
gcloud run services logs read system-llm-api --region asia-southeast2 | grep "Proxy"
```

### Issue: GCS bucket access denied
```bash
# Check service account permissions
gcloud projects get-iam-policy system-llm

# Add Storage Object Creator role
gcloud projects add-iam-policy-binding system-llm \
  --member serviceAccount:system-llm-sa@system-llm.iam.gserviceaccount.com \
  --role roles/storage.objectCreator
```

---

## 📚 Useful Commands

### View deployment status
```bash
gcloud run services list
gcloud run services describe system-llm-api --region asia-southeast2
```

### View logs and metrics
```bash
# Real-time logs
gcloud run services logs read system-llm-api --region asia-southeast2 --follow

# Historical logs
gcloud logging read "resource.type=cloud_run_revision" --limit 100

# Metrics
gcloud monitoring metrics-descriptors list | grep cloud_run
```

### Scale service
```bash
# Manual scaling
gcloud run services update system-llm-api \
  --min-instances 1 \
  --max-instances 20 \
  --region asia-southeast2

# Without scaling (request-based only)
gcloud run services update system-llm-api \
  --min-instances 0 \
  --max-instances 10 \
  --region asia-southeast2
```

---

## 🎯 Current Deployment Status

- ✅ Dockerfile ready for GCP
- ✅ entrypoint.sh configured for Cloud Run
- ✅ Cloud SQL Proxy integration complete
- ✅ GCS integration ready
- ✅ Environment configuration prepared
- ✅ Docker image can be built
- ✅ Ready for Cloud Run deployment

---

**Last Updated:** 2025-01-08
**Status:** Ready for GCP Cloud Run deployment
