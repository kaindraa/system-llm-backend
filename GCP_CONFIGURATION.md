# 🚀 GCP Configuration Guide - system-llm-backend

## Overview

Backend telah dikonfigurasi untuk menggunakan **Google Cloud Platform (GCP)** sebagai infrastruktur utama dengan:
- **Cloud SQL** untuk database PostgreSQL
- **Google Cloud Storage (GCS)** untuk file storage
- **Cloud SQL Proxy** untuk koneksi yang aman
- **Application Default Credentials** untuk autentikasi

---

## 📋 File Konfigurasi

### 1. `.env` (Active)
**Status:** ✅ Aktif untuk GCP
**Location:** `/system-llm-backend/.env`
**Konfigurasi:**
```bash
# Database - Cloud SQL via Proxy
DATABASE_URL=postgresql://llm_user:anLLMUser123123@cloud-sql-proxy:5432/system_llm

# Storage - Google Cloud Storage
STORAGE_TYPE=gcs
GCS_BUCKET_NAME=system-llm-storage
GCS_PROJECT_ID=system-llm
GCS_CREDENTIALS_PATH=/app/credentials/system-llm-storage-key.json
GOOGLE_APPLICATION_CREDENTIALS=/credentials.json

# API Keys
OPENAI_API_KEY=sk-proj-...
GOOGLE_API_KEY=AIzaSy...

# CORS Origins (includes production)
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:8000","https://system-llm-chat.fly.dev"]
```

### 2. `.env.remote` (Template)
**Status:** 📖 Reference template
**Location:** `/system-llm-backend/.env.remote`
**Gunakan:** Jika perlu reset konfigurasi GCP

### 3. `.env.local` (Local Development - Archive)
**Status:** 📁 Diarsipkan untuk local development
**Location:** `/system-llm-backend/.env.local`
**Gunakan:** Jika ingin switch kembali ke local

---

## 🔧 Konfigurasi Backend

### app/core/config.py
**Status:** ✅ Updated
**Perubahan:**
```python
# BEFORE
class Config:
    env_file = ".env.local"  # Hard-coded to local

# AFTER
class Config:
    env_file = ".env"  # Flexible - dapat dibaca dari .env apapun
```

**Keuntungan:** Sekarang backend dapat membaca dari file `.env` apapun, memberikan fleksibilitas untuk switching antara konfigurasi.

---

## 🐳 Docker Compose

### docker-compose.yml (GCP)
**Status:** ✅ Siap digunakan
**Services:**
1. **cloud-sql-proxy** - Koneksi ke GCP Cloud SQL
2. **pgadmin** - Database management UI (port 5050)
3. **api** - FastAPI backend dengan GCS integration (port 8000)

**Startup Command:**
```bash
docker-compose -f docker-compose.yml up -d
```

### docker-compose.local.yml (Local - Archive)
**Status:** 📁 Tersedia untuk local development
**Gunakan:** Jika ingin switch kembali ke local

---

## 📊 Perbandingan Konfigurasi

| Aspek | Local | GCP |
|-------|-------|-----|
| **Database** | PostgreSQL (local container) | Cloud SQL via Proxy |
| **Host** | postgres:5432 | cloud-sql-proxy:5432 |
| **Storage** | Local filesystem | Google Cloud Storage |
| **Credentials** | API keys dalam .env | GCP service account + ADC |
| **Docker Compose** | docker-compose.local.yml | docker-compose.yml |
| **Env File** | .env.local | .env |

---

## 🚀 Memulai dengan GCP

### Prerequisites
1. **GCP Account** dengan project yang sudah setup
2. **Google Cloud SQL** instance: `system-llm:asia-southeast2:system-llm-db`
3. **Google Cloud Storage** bucket: `system-llm-storage`
4. **GCP Credentials** ter-setup di local machine

### Setup Steps

#### Step 1: Setup GCP Credentials
```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Verify credentials
ls ~/.config/gcloud/application_default_credentials.json
```

#### Step 2: Prepare Credentials File
```bash
# Jika sudah ada service account key untuk GCS:
# Copy ke file: system-llm-storage-key.json

# Location dalam docker-compose:
# ./system-llm-storage-key.json → /app/credentials/system-llm-storage-key.json
```

#### Step 3: Start Backend
```bash
# Ensure .env file exists (sudah dibuat)
# Ensure docker-compose.yml sudah ada

# Start services
docker-compose -f docker-compose.yml up -d

# View logs
docker-compose logs -f api
```

#### Step 4: Verify Setup
```bash
# Check if API is running
curl http://localhost:8000/api/v1/health

# Check database connection via pgAdmin
# http://localhost:5050
# Email: admin@admin.com
# Password: admin

# Check if can connect to Cloud SQL
# Server: cloud-sql-proxy
# Port: 5432
# Database: system_llm
# User: llm_user
```

---

## 🔄 Switching Between Configurations

### Switch ke GCP (Current)
```bash
# File .env sudah berisi konfigurasi GCP ✅
# Jalankan:
docker-compose -f docker-compose.yml up -d
```

### Switch ke Local (Jika diperlukan)
```bash
# Copy local configuration ke .env
cp .env.local .env

# Update config.py (sudah flexible, tidak perlu perubahan)

# Jalankan:
docker-compose -f docker-compose.local.yml up -d
```

---

## 🔐 Security Notes

### Credentials Handling
- **GCP Credentials**: Mounted dari `~/.config/gcloud/` (tidak disimpan di repo)
- **GCS Service Account Key**: Mounted dari `./system-llm-storage-key.json` (local file, tidak di git)
- **Environment Variables**: Stored dalam `.env` (jangan commit ke git)

### Git Ignore
Pastikan `.gitignore` memiliki:
```bash
.env
.env.local
.env.remote
*.json  # untuk service account keys
credentials/
```

---

## 📚 Environment Variables

### Database
- `DATABASE_URL` - Full connection string
- `POSTGRES_USER` - Username
- `POSTGRES_PASSWORD` - Password
- `POSTGRES_DB` - Database name

### Storage
- `STORAGE_TYPE` - "gcs" untuk GCP
- `GCS_BUCKET_NAME` - Bucket name
- `GCS_PROJECT_ID` - GCP project ID
- `GCS_CREDENTIALS_PATH` - Path to service account key
- `GOOGLE_APPLICATION_CREDENTIALS` - Path untuk ADC

### API Keys
- `OPENAI_API_KEY` - OpenAI API key
- `OPENROUTER_API_KEY` - OpenRouter API key
- `GOOGLE_API_KEY` - Google API key
- `ANTHROPIC_API_KEY` - Anthropic API key (optional)

### Security
- `SECRET_KEY` - JWT secret key
- `ALGORITHM` - JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration

### Application
- `DEBUG` - Debug mode (true/false)
- `BACKEND_CORS_ORIGINS` - CORS allowed origins (JSON array)

---

## 🐛 Troubleshooting

### Issue: Connection to Cloud SQL timeout
**Solution:**
```bash
# Verify credentials path
ls C:\Users\pcgsa\AppData\Roaming\gcloud\application_default_credentials.json

# Check if cloud-sql-proxy is running
docker ps | grep cloud-sql-proxy

# View proxy logs
docker-compose logs cloud-sql-proxy
```

### Issue: GCS bucket access denied
**Solution:**
```bash
# Verify GCS credentials file exists
ls ./system-llm-storage-key.json

# Check GCP project has permissions
gcloud projects get-iam-policy system-llm
```

### Issue: Backend can't find GCS bucket
**Solution:**
```bash
# Verify GCS_BUCKET_NAME in .env
grep GCS_BUCKET_NAME .env

# Test GCS access
gsutil ls gs://system-llm-storage/
```

---

## 📝 Configuration Files Summary

```
system-llm-backend/
├── .env                          ✅ Active (GCP)
├── .env.local                    📁 Archive (Local)
├── .env.remote                   📖 Template (GCP)
├── .env.example                  📖 Reference
├── docker-compose.yml            ✅ Active (GCP)
├── docker-compose.local.yml      📁 Archive (Local)
├── Dockerfile                    ✅ GCP (with Cloud SQL Proxy)
├── Dockerfile.local              📁 Local (without Cloud SQL Proxy)
├── app/
│   └── core/
│       └── config.py             ✅ Updated (flexible env_file)
└── GCP_CONFIGURATION.md          📖 This file
```

---

## ✅ Configuration Status

- ✅ `.env` set to GCP
- ✅ `config.py` supports dynamic env file
- ✅ `docker-compose.yml` configured for GCP
- ✅ Cloud SQL Proxy ready
- ✅ GCS integration ready
- ✅ All API keys configured

---

## 📞 Next Steps

1. **Verify GCP Resources**
   - Cloud SQL instance running
   - GCS bucket accessible
   - Service accounts configured

2. **Start Services**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

3. **Test Connectivity**
   - Health check: `curl http://localhost:8000/api/v1/health`
   - Database: pgAdmin at `http://localhost:5050`
   - GCS: Via backend API

4. **Monitor Logs**
   ```bash
   docker-compose logs -f api
   docker-compose logs -f cloud-sql-proxy
   ```

---

**Last Updated:** 2025-01-08
**Configuration Status:** ✅ GCP Active
