# Cloud SQL Setup untuk System LLM Backend

Panduan lengkap untuk connect backend ke Google Cloud SQL menggunakan Cloud SQL Proxy.

## 📋 Prasyarat

✅ Google Cloud Project setup: `system-llm`
✅ Cloud SQL instance sudah dibuat
✅ Service account sudah ada
✅ Cloud SQL Proxy binary di Dockerfile sudah di-download

## Step 1: Verify Cloud SQL Instance

```bash
# List Cloud SQL instances
gcloud sql instances list

# Output expected:
# NAME                LOCATION          STATUS
# system-llm-db       asia-southeast2   RUNNABLE
```

Catat:
- **Instance Name**: `system-llm-db`
- **Region**: `asia-southeast2`
- **Project ID**: `system-llm`

**CLOUD_SQL_INSTANCES format**: `PROJECT_ID:REGION:INSTANCE_NAME`
```
system-llm:asia-southeast2:system-llm-db
```

## Step 2: Get Cloud SQL Connection Info

```bash
# Get connection name
gcloud sql instances describe system-llm-db --format='value(connectionName)'

# Output format:
# system-llm:asia-southeast2:system-llm-db
```

## Step 3: Setup Database Connection

### Option A: Using Cloud SQL Proxy (Recommended for Docker)

Cloud SQL Proxy membuat secure tunnel dari aplikasi ke Cloud SQL.

**DATABASE_URL format untuk Cloud SQL Proxy:**
```
postgresql://USERNAME:PASSWORD@/DATABASE_NAME?host=/cloudsql/CONNECTION_NAME
```

**Contoh:**
```
postgresql://postgres:your-password@/system_llm?host=/cloudsql/system-llm:asia-southeast2:system-llm-db
```

### Option B: Direct Connection (Less Secure)

Hanya jika Anda sudah authorize IP address.

```
postgresql://USERNAME:PASSWORD@CLOUD_SQL_IP:5432/DATABASE_NAME
```

**Untuk Docker, gunakan Cloud SQL Proxy (Option A) - lebih aman & reliable.**

## Step 4: Update docker-compose.yml

Perubahan untuk menggunakan Cloud SQL Proxy:

```yaml
services:
  # REMOVE atau COMMENT postgres service jika tidak perlu
  # postgres:
  #   image: pgvector/pgvector:pg16
  #   ...

  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: system-llm-api
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/logs
      - ./gcs-key.json:/app/gcs-key.json:ro  # GCS key (optional)
    env_file:
      - .env
    environment:
      # Cloud SQL Configuration
      - CLOUD_SQL_INSTANCES=system-llm:asia-southeast2:system-llm-db
      - GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json
      # Database (untuk Cloud SQL Proxy)
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@/system_llm?host=/cloudsql/system-llm:asia-southeast2:system-llm-db
      # Storage
      - STORAGE_TYPE=${STORAGE_TYPE:-local}
      - GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
      - GCS_PROJECT_ID=${GCS_PROJECT_ID}
    # Tidak perlu wait untuk postgres sekarang (karena Cloud SQL)
    networks:
      - system-llm-network
    restart: unless-stopped

volumes:
  # Tidak perlu postgres_data untuk Cloud SQL

networks:
  system-llm-network:
    driver: bridge
```

## Step 5: Prepare .env File

```env
# Database (Cloud SQL)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password-here
POSTGRES_DB=system_llm

# Security
SECRET_KEY=generate-with-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Application
PROJECT_NAME=System LLM
API_V1_PREFIX=/api/v1
DEBUG=False

# CORS
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]

# LLM
OPENAI_API_KEY=sk-...

# Storage (GCS recommended for production)
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=system-llm-storage
GCS_PROJECT_ID=system-llm
GOOGLE_APPLICATION_CREDENTIALS=/app/gcs-key.json
```

## Step 6: Setup Authentication

Cloud SQL Proxy memerlukan credentials untuk connect ke Cloud SQL.

### Option A: Using Service Account Key (Recommended)

```bash
# Create service account key
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=system-llm-storage@system-llm.iam.gserviceaccount.com

# Or if you need Cloud SQL specific service account:
gcloud iam service-accounts create cloud-sql-proxy \
  --display-name="Cloud SQL Proxy"

# Grant Cloud SQL permissions
gcloud projects add-iam-policy-binding system-llm \
  --member=serviceAccount:cloud-sql-proxy@system-llm.iam.gserviceaccount.com \
  --role=roles/cloudsql.client

# Create and download key
gcloud iam service-accounts keys create gcs-key.json \
  --iam-account=cloud-sql-proxy@system-llm.iam.gserviceaccount.com
```

Simpan file `gcs-key.json` di root backend directory.

### Option B: Using Application Default Credentials

Jika running di GCP (Cloud Run, Compute Engine):
```bash
# ADC sudah tersedia otomatis
# Tidak perlu konfigurasi tambahan
```

## Step 7: Verify Cloud SQL Permissions

Service account perlu role `roles/cloudsql.client`:

```bash
# Check current permissions
gcloud projects get-iam-policy system-llm \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*" \
  --format="table(bindings.role)"

# Grant if missing
gcloud projects add-iam-policy-binding system-llm \
  --member=serviceAccount:system-llm-storage@system-llm.iam.gserviceaccount.com \
  --role=roles/cloudsql.client
```

## Step 8: Build & Run

```bash
# Build Docker image
docker-compose build

# Run containers (tanpa postgres service)
docker-compose up -d api pgadmin

# Check logs
docker-compose logs -f api
```

## Step 9: Verify Connection

```bash
# Check if Cloud SQL Proxy started
docker-compose logs api | grep -i "cloud sql\|proxy"

# Expected output:
# → Starting Cloud SQL Proxy for: system-llm:asia-southeast2:system-llm-db
# ✓ Cloud SQL Proxy started with PID: XXX
# ✓ Cloud SQL Proxy is healthy

# Test database connection
docker-compose logs api | grep -i "database\|connection"

# Access API
curl http://localhost:8000/health
```

## Troubleshooting

### Issue: "Cloud SQL Proxy failed to start"

**Symptoms:**
```
Error: Cloud SQL Proxy failed to start
```

**Solutions:**
1. Verify CLOUD_SQL_INSTANCES format:
```bash
gcloud sql instances describe system-llm-db --format='value(connectionName)'
```

2. Check if service account has Cloud SQL permission:
```bash
gcloud projects get-iam-policy system-llm \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:system-llm-storage@system-llm.iam.gserviceaccount.com"
```

3. Check if gcs-key.json valid:
```bash
cat gcs-key.json | head -10
```

### Issue: "Connection refused" when connecting to database

**Symptoms:**
```
postgresql.errors.OperationalError: could not connect to server
```

**Solutions:**
1. Verify DATABASE_URL format with Cloud SQL instance name:
```env
DATABASE_URL=postgresql://user:pass@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE
```

2. Check if proxy socket created:
```bash
docker-compose exec api ls -la /cloudsql/
```

3. Verify database name in Cloud SQL:
```bash
gcloud sql databases list --instance=system-llm-db
```

### Issue: "Permission denied" error

**Symptoms:**
```
google.auth.exceptions.DefaultCredentialsError
Authentication failed. Unable to acquire credential
```

**Solutions:**
1. Verify gcs-key.json path in docker-compose.yml
2. Check file permissions: `ls -la gcs-key.json`
3. Verify service account key is still valid:
```bash
gcloud iam service-accounts keys list
```

### Issue: "Cloud SQL instance not found"

**Symptoms:**
```
Error: There is no Cloud SQL instance named 'system-llm-db'
```

**Solutions:**
1. List available instances:
```bash
gcloud sql instances list
```

2. Update CLOUD_SQL_INSTANCES with correct instance name

3. Verify project is set:
```bash
gcloud config get-value project
```

## Performance Tips

1. **Connection Pooling**: PgBouncer or SQLAlchemy connection pooling
2. **Network**: Cloud SQL Proxy adds ~50ms latency
3. **Scaling**: Use Cloud SQL replicas untuk read-heavy workloads

## Security Best Practices

1. ✅ Use Cloud SQL Proxy (encrypted tunnel)
2. ✅ Never expose Cloud SQL directly to internet
3. ✅ Rotate database passwords regularly
4. ✅ Use strong database passwords (min 20 chars)
5. ✅ Enable Cloud SQL automatic backups
6. ✅ Enable Cloud SQL activity logs

## Monitoring

```bash
# View Cloud SQL activity
gcloud sql operations list --instance=system-llm-db

# View backups
gcloud sql backups list --instance=system-llm-db

# Enable slow query logs
gcloud sql instances patch system-llm-db \
  --database-flags=log_min_duration_statement=1000
```

## Maintenance

### Backup

```bash
# Create backup
gcloud sql backups create \
  --instance=system-llm-db \
  --description="Pre-deployment backup"

# List backups
gcloud sql backups list --instance=system-llm-db
```

### Update Password

```bash
# Set new password
gcloud sql users set-password postgres \
  --instance=system-llm-db \
  --password=new-secure-password

# Update .env
# POSTGRES_PASSWORD=new-secure-password

# Restart container
docker-compose restart api
```

## Migration dari Local PostgreSQL

Jika sebelumnya pakai local PostgreSQL:

```bash
# 1. Backup dari local
pg_dump -U postgres -h localhost system_llm > backup.sql

# 2. Restore ke Cloud SQL
gcloud sql import sql system-llm-db backup.sql \
  --database=system_llm

# 3. Verify
gcloud sql connect system-llm-db --user=postgres
```

---

## Reference

- [Cloud SQL Proxy Documentation](https://cloud.google.com/sql/docs/postgres/cloud-sql-proxy)
- [Cloud SQL Connection Names](https://cloud.google.com/sql/docs/postgres/instance-connection-name)
- [PostgreSQL Driver for Python](https://www.psycopg.org/)
- [SQLAlchemy Cloud SQL](https://github.com/googleapis/cloud-sql-python-connector)
