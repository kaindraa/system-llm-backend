# Cloud SQL Quick Start Guide

Setup cepat untuk connect ke Google Cloud SQL dalam 5 menit.

## Prerequisites

✅ Cloud SQL instance sudah ada (e.g., `system-llm-db`)
✅ gcloud CLI installed & authenticated
✅ Service account dengan Cloud SQL permission

## Quick Setup (5 menit)

### 1. Download Service Account Key (30 detik)

```bash
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com
```

**File `gcs-key.json` akan tercipta di root backend directory**

### 2. Get Cloud SQL Instance Info (30 detik)

```bash
# Get connection name
gcloud sql instances describe system-llm-db --format='value(connectionName)'

# Output: system-llm:asia-southeast2:system-llm-db
```

### 3. Setup Environment (1 menit)

```bash
# Copy template
cp .env.cloud-sql .env

# Edit .env dengan:
nano .env
```

Update values:
```env
# Change these
POSTGRES_PASSWORD=your-very-secure-password-here
SECRET_KEY=generate-with-command-below
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
OPENAI_API_KEY=sk-...

# Keep these (sesuaikan dengan instance Anda)
# CLOUD_SQL_INSTANCES=system-llm:asia-southeast2:system-llm-db
```

Generate SECRET_KEY:
```bash
openssl rand -hex 32
```

### 4. Build & Run (2 menit)

```bash
# Build image
docker-compose -f docker-compose.cloud-sql.yml build

# Run
docker-compose -f docker-compose.cloud-sql.yml up -d

# Check status
docker-compose -f docker-compose.cloud-sql.yml ps
```

### 5. Verify Connection (1 menit)

```bash
# Check Cloud SQL Proxy
docker-compose -f docker-compose.cloud-sql.yml logs api | grep -i "cloud sql\|proxy\|storage"

# Expected output:
# → Starting Cloud SQL Proxy for: system-llm:asia-southeast2:system-llm-db
# ✓ Cloud SQL Proxy started with PID: XXX
# ✓ Cloud SQL Proxy is healthy
# ✓ Storage: GCS (bucket: system-llm-storage)

# Test API
curl http://localhost:8000/health
```

✅ **Done!** Application is connected to Cloud SQL

---

## Useful Commands

```bash
# View logs
docker-compose -f docker-compose.cloud-sql.yml logs -f api

# Stop
docker-compose -f docker-compose.cloud-sql.yml down

# Restart
docker-compose -f docker-compose.cloud-sql.yml restart api

# Execute command in container
docker-compose -f docker-compose.cloud-sql.yml exec api bash
```

---

## Make Default (Optional)

Gunakan Cloud SQL config sebagai default:

```bash
# Linux/Mac
export COMPOSE_FILE=docker-compose.cloud-sql.yml

# Atau add ke ~/.bashrc atau ~/.zshrc
echo 'export COMPOSE_FILE=docker-compose.cloud-sql.yml' >> ~/.bashrc
source ~/.bashrc

# Sekarang bisa langsung:
docker-compose up -d
docker-compose logs -f api
```

---

## Verify Cloud SQL Instance

```bash
# List instances
gcloud sql instances list

# Describe instance
gcloud sql instances describe system-llm-db

# Test database connection
gcloud sql connect system-llm-db --user=postgres
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Cloud SQL Proxy won't start | Check `CLOUD_SQL_INSTANCES` format & service account permissions |
| Database connection refused | Verify DATABASE_URL has correct instance name |
| Permission denied | Download fresh `gcs-key.json` & verify service account roles |
| Can't find instance | Run `gcloud sql instances list` to verify instance exists |

---

## Common Issues & Fixes

### ❌ "Connection refused"

```bash
# Verify instance is running
gcloud sql instances describe system-llm-db --format='value(state)'
# Output: RUNNABLE

# If not, start it
gcloud sql instances patch system-llm-db --no-assign-ip
```

### ❌ "Authentication failed"

```bash
# Regenerate service account key
gcloud iam service-accounts keys list
# Delete old keys, create new one
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com
```

### ❌ "Instance not found"

```bash
# Check instance name & project
gcloud sql instances list --project=system-llm

# Format CONNECTION_NAME:
# PROJECT:REGION:INSTANCE_NAME
```

### ❌ Slow startup (takes 1+ minute)

This is normal! Cloud SQL Proxy needs to:
1. Authenticate dengan GCP
2. Establish secure tunnel
3. Wait untuk database ready
4. FastAPI startup

Increase `start_period` di docker-compose jika perlu lebih lama.

---

## Production Checklist

- ✅ Cloud SQL automatic backups enabled
- ✅ Strong password set (20+ chars)
- ✅ Cloud SQL activity logs enabled
- ✅ Service account minimal permissions (`roles/cloudsql.client`)
- ✅ GCS bucket configured for file storage
- ✅ CORS properly configured
- ✅ DEBUG=False in production
- ✅ SECRET_KEY generated with openssl

---

## Next Steps

1. Deploy to Cloud Run atau Compute Engine
2. Setup Cloud SQL automatic backups
3. Monitor dengan Cloud Monitoring
4. Setup CI/CD pipeline untuk auto-deploy

---

**Full documentation**: See `CLOUD_SQL_SETUP.md` for complete reference
