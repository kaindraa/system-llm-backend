# ⚡ Quick Reference - GCP Commands

## 🚀 Getting Started (GCP Mode)

### Local Testing with GCP Services
```bash
# Start services (uses cloud-sql-proxy + GCS)
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Health check
curl http://localhost:8000/api/v1/health
```

---

## 🐳 Docker Commands

### Build for GCP (Production)
```bash
docker build -f Dockerfile -t system-llm-api:prod .
```

### Build for Local (Development)
```bash
docker build -f Dockerfile.local -t system-llm-api:local .
```

### Tag for GCP Container Registry
```bash
docker tag system-llm-api:prod gcr.io/system-llm/system-llm-api:prod
```

### Push to GCP
```bash
docker push gcr.io/system-llm/system-llm-api:prod
```

### Run container locally
```bash
docker run -p 8000:8000 --env-file .env system-llm-api:prod
```

---

## 🌐 Cloud Run Deployment

### Deploy to Cloud Run
```bash
gcloud run deploy system-llm-api \
  --image gcr.io/system-llm/system-llm-api:prod \
  --platform managed \
  --region asia-southeast2 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --add-cloudsql-instances system-llm:asia-southeast2:system-llm-db \
  --allow-unauthenticated
```

### Get Cloud Run Service URL
```bash
gcloud run services describe system-llm-api --region asia-southeast2 --format='value(status.url)'
```

### Update existing Cloud Run service
```bash
gcloud run deploy system-llm-api \
  --image gcr.io/system-llm/system-llm-api:prod \
  --region asia-southeast2
```

### View Cloud Run logs (real-time)
```bash
gcloud run services logs read system-llm-api --region asia-southeast2 --follow
```

### Scale Cloud Run service
```bash
# Set minimum and maximum instances
gcloud run services update system-llm-api \
  --min-instances 0 \
  --max-instances 10 \
  --region asia-southeast2
```

### Delete Cloud Run service
```bash
gcloud run services delete system-llm-api --region asia-southeast2
```

---

## ☁️ Cloud SQL Commands

### List Cloud SQL instances
```bash
gcloud sql instances list
```

### Connect to Cloud SQL instance
```bash
gcloud sql connect system-llm-db --user=llm_user
```

### View Cloud SQL instance details
```bash
gcloud sql instances describe system-llm-db
```

### Create database backup
```bash
gcloud sql backups create --instance=system-llm-db
```

### List backups
```bash
gcloud sql backups list --instance=system-llm-db
```

---

## 🗄️ Cloud Storage (GCS) Commands

### List bucket contents
```bash
gsutil ls gs://system-llm-storage/
```

### List all files recursively
```bash
gsutil ls -r gs://system-llm-storage/
```

### Get bucket size
```bash
gsutil du -s gs://system-llm-storage/
```

### Upload file to GCS
```bash
gsutil cp file.pdf gs://system-llm-storage/uploads/
```

### Download file from GCS
```bash
gsutil cp gs://system-llm-storage/uploads/file.pdf .
```

### Delete file from GCS
```bash
gsutil rm gs://system-llm-storage/uploads/file.pdf
```

### Set public access to bucket
```bash
gsutil iam ch serviceAccount:system-llm-sa@system-llm.iam.gserviceaccount.com:objectCreator gs://system-llm-storage
```

---

## 🔐 GCP Authentication & Setup

### Setup gcloud authentication
```bash
gcloud auth login
gcloud config set project system-llm
```

### Setup Docker authentication
```bash
gcloud auth configure-docker gcr.io
```

### Setup Application Default Credentials (ADC)
```bash
gcloud auth application-default login
```

### Create service account
```bash
gcloud iam service-accounts create system-llm-sa \
  --display-name="System LLM Service Account"
```

### Grant permissions to service account
```bash
# Cloud SQL Client
gcloud projects add-iam-policy-binding system-llm \
  --member serviceAccount:system-llm-sa@system-llm.iam.gserviceaccount.com \
  --role roles/cloudsql.client

# Storage Object Creator
gcloud projects add-iam-policy-binding system-llm \
  --member serviceAccount:system-llm-sa@system-llm.iam.gserviceaccount.com \
  --role roles/storage.objectCreator

# Storage Object Viewer
gcloud projects add-iam-policy-binding system-llm \
  --member serviceAccount:system-llm-sa@system-llm.iam.gserviceaccount.com \
  --role roles/storage.objectViewer
```

---

## 🔑 Secret Manager Commands

### Create a secret
```bash
echo "sk-proj-..." | gcloud secrets create OPENAI_API_KEY --data-file=-
```

### Update a secret
```bash
echo "sk-proj-..." | gcloud secrets versions add OPENAI_API_KEY --data-file=-
```

### Get a secret
```bash
gcloud secrets versions access latest --secret OPENAI_API_KEY
```

### List all secrets
```bash
gcloud secrets list
```

### Delete a secret
```bash
gcloud secrets delete OPENAI_API_KEY
```

---

## 📊 Monitoring & Logs

### View Cloud Run metrics
```bash
gcloud monitoring metrics-descriptors list | grep cloud_run
```

### View application logs
```bash
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

### View Cloud SQL logs
```bash
gcloud logging read "resource.type=cloudsql_database" --limit 50
```

### Stream logs in real-time
```bash
gcloud logging read "resource.type=cloud_run_revision" --follow
```

### Filter logs by service
```bash
gcloud logging read "resource.service_name=system-llm-api" --limit 100
```

---

## 🔄 Configuration Switching

### Switch to GCP mode
```bash
# .env already contains GCP config
# Just ensure you're using docker-compose.yml
docker-compose -f docker-compose.yml up -d
```

### Switch to Local mode (if needed)
```bash
# Copy local config
cp .env.local .env

# Use local docker-compose
docker-compose -f docker-compose.local.yml up -d
```

---

## 🐍 Python/Alembic Commands

### Run database migrations
```bash
alembic upgrade head
```

### Create a new migration
```bash
alembic revision --autogenerate -m "description"
```

### View migration history
```bash
alembic current
```

### Downgrade database
```bash
alembic downgrade -1
```

---

## 📝 Environment Files

### View current .env (GCP)
```bash
cat .env
```

### View .env.local (local backup)
```bash
cat .env.local
```

### View .env.remote (GCP template)
```bash
cat .env.remote
```

### Validate .env syntax
```bash
python3 -c "from dotenv import load_dotenv; load_dotenv('.env'); print('✅ .env is valid')"
```

---

## 🧪 Testing & Verification

### Health check API
```bash
curl http://localhost:8000/api/v1/health
```

### Get API info
```bash
curl http://localhost:8000/api/v1/
```

### List documents (with auth required)
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/documents
```

### Check database connection (from container)
```bash
docker exec system-llm-api psql -h cloud-sql-proxy -U llm_user -d system_llm -c "SELECT version();"
```

### Check GCS bucket access
```bash
gsutil ls gs://system-llm-storage/uploads/ | head -5
```

---

## 🚨 Troubleshooting

### Check if Docker containers are running
```bash
docker ps
```

### View container logs
```bash
docker logs system-llm-api
docker logs system-llm-cloud-sql-proxy
docker logs system-llm-pgadmin
```

### Restart a service
```bash
docker restart system-llm-api
```

### Remove all stopped containers
```bash
docker container prune
```

### Check Docker disk usage
```bash
docker system df
docker system prune
```

### Debug container shell
```bash
docker exec -it system-llm-api /bin/bash
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `GCP_CONFIGURATION.md` | Detailed GCP setup & config |
| `DEPLOYMENT_GCP.md` | Cloud Run deployment guide |
| `MIGRATION_SUMMARY.md` | Summary of changes |
| `QUICK_REFERENCE.md` | This file |
| `ingest_docs_for_rag_gcp.ipynb` | RAG document ingestion notebook |

---

## 🎯 Common Workflows

### 1. Local Development (with GCP services)
```bash
# Start
docker-compose -f docker-compose.yml up -d

# Work on code
code app/

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 2. Deploy to Production
```bash
# Build
docker build -f Dockerfile -t system-llm-api:prod .

# Tag
docker tag system-llm-api:prod gcr.io/system-llm/system-llm-api:prod

# Push
docker push gcr.io/system-llm/system-llm-api:prod

# Deploy
gcloud run deploy system-llm-api \
  --image gcr.io/system-llm/system-llm-api:prod \
  --region asia-southeast2
```

### 3. Debug Database Issues
```bash
# Check Cloud SQL instance
gcloud sql instances describe system-llm-db

# Check proxy logs
docker logs system-llm-cloud-sql-proxy

# Test connection
docker exec system-llm-api psql -h cloud-sql-proxy -U llm_user -d system_llm -c "SELECT 1;"
```

### 4. Upload Documents to GCS
```bash
# Single file
gsutil cp documents/*.pdf gs://system-llm-storage/uploads/

# Entire directory
gsutil -m cp -r documents/* gs://system-llm-storage/uploads/

# Verify
gsutil ls -r gs://system-llm-storage/uploads/ | wc -l
```

---

## ✅ Quick Checklist

- [ ] .env file exists and has GCP config
- [ ] Docker is installed and running
- [ ] gcloud CLI is installed and authenticated
- [ ] GCP project is set: `gcloud config list`
- [ ] GCP credentials are available
- [ ] Cloud SQL instance is running
- [ ] GCS bucket exists
- [ ] Can build Docker image locally
- [ ] Can connect to Cloud SQL from local
- [ ] Can access GCS from local

---

**Last Updated:** 2025-01-08
**Status:** Ready for Use
