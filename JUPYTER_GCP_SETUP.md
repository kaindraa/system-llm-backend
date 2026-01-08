# 📓 Jupyter Setup untuk GCP - ingest_docs_for_rag_gcp.ipynb

## ⚠️ Important: Local Jupyter vs Docker Network

Ketika menjalankan Jupyter notebook dari **local machine** (bukan dalam docker), ada perbedaan penting dalam hostname:

### ❌ TIDAK BISA
```python
# Hostname "cloud-sql-proxy" hanya accessible dalam docker network
DATABASE_URL = "postgresql://...@cloud-sql-proxy:5432/system_llm"  # ❌ Won't work
```

### ✅ BISA
```python
# docker-compose.yml expose port ke localhost:5432
DATABASE_URL = "postgresql://...@localhost:5432/system_llm"  # ✅ Works
```

---

## 🚀 Setup Jupyter untuk GCP

### Prerequisite
1. Docker Desktop running
2. GCP docker-compose services running
3. Python environment dengan dependencies

### Step 1: Start GCP Services

```bash
cd system-llm-backend

# Start docker-compose (dengan Cloud SQL Proxy)
docker-compose -f docker-compose.yml up -d

# Verify services running
docker ps
# Should show:
# - system-llm-cloud-sql-proxy (running)
# - system-llm-api (running)
# - system-llm-pgadmin (running)
```

### Step 2: Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Additional for Jupyter
pip install jupyter jupyter-lab ipykernel
pip install -e .
```

### Step 3: Start Jupyter

```bash
# Start Jupyter from backend directory
jupyter notebook

# Or use JupyterLab
jupyter lab
```

### Step 4: Open Notebook

1. Open `ingest_docs_for_rag_gcp.ipynb`
2. Make sure using correct kernel (if needed):
   - Click Kernel → Change kernel → select your venv
3. Run cells from top to bottom

---

## 🔧 Database Connection Logic

File `ingest_docs_for_rag_gcp.ipynb` sudah menghandle connection string conversion:

```python
# DATABASE_URL dari .env (GCP production format)
DATABASE_URL = "postgresql://llm_user:anLLMUser123123@cloud-sql-proxy:5432/system_llm"

# Automatic conversion untuk Jupyter lokal
if "cloud-sql-proxy" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("cloud-sql-proxy", "localhost")
    # Result: "postgresql://llm_user:anLLMUser123123@localhost:5432/system_llm"
```

**Benefit:** Menggunakan `.env` yang sama untuk production & local development

---

## 📊 Port Mapping

Ketika `docker-compose -f docker-compose.yml up -d` berjalan:

```
Docker Container Network:
┌─────────────────────────────────────┐
│ cloud-sql-proxy:5432                │  ← Inside docker network
│ (running container)                 │
└──────────┬──────────────────────────┘
           │
           │ Port forward (from docker-compose.yml)
           │
           ▼
Host Machine (Local):
localhost:5432  ← Accessible from Jupyter
```

---

## ✅ Verification Checklist

### Before Running Notebook

- [ ] Docker Desktop running
- [ ] Services started: `docker-compose -f docker-compose.yml up -d`
- [ ] Containers healthy: `docker ps` shows 3+ services up
- [ ] Port 5432 not in conflict: `netstat -an | grep 5432`
- [ ] Python venv activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Jupyter installed: `jupyter --version`

### First Cell Should Output

```
ℹ️  Converted cloud-sql-proxy hostname to localhost for local Jupyter access
✅ Database engine created
   URL: postgresql://llm_user:anLLMUser123123@localhost:5432/sy...
✅ Connected to: system_llm
✅ PostgreSQL: PostgreSQL 15.14
```

If you see database connection error:
1. Verify docker services: `docker ps`
2. Check if Cloud SQL Proxy is running
3. Verify port 5432 not already used
4. Run: `docker logs system-llm-cloud-sql-proxy` untuk melihat error

---

## 🔐 GCP Credentials Setup

### For GCS (Google Cloud Storage)

Notebook akan load credentials dari environment variables:

```python
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")           # from .env
GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID")             # from .env
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH") # from .env
```

**Setup GCS Credentials:**

```bash
# Option 1: Using Application Default Credentials (ADC)
gcloud auth application-default login

# Option 2: Using service account key file
# Place service account key in: system-llm-storage-key.json
# Update .env:
# GCS_CREDENTIALS_PATH=/path/to/system-llm-storage-key.json
```

### For OpenAI API

```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # from .env
```

**Setup OpenAI:**
- Ensure `.env` has valid `OPENAI_API_KEY`
- Get key from: https://platform.openai.com/api-keys

---

## 📝 Notebook Workflow

### Cell 0: Imports
- Load all required libraries
- Load `.env` configuration

### Cell 1: Database Connection
- ✅ Auto-converts `cloud-sql-proxy` → `localhost`
- ✅ Tests connection
- ✅ Shows version info

### Cell 2: GCS Storage Setup
- Initialize GCS bucket connection
- Verify bucket accessibility
- Show bucket info

### Cell 3-4: File Discovery
- Scan `file_to_ingest/` folder
- List available PDFs
- Select files to process

### Cell 5: Upload to GCS
- Upload PDF files to GCS bucket
- Create database records
- Show upload progress

### Cell 6: Extract Text
- Download PDFs from GCS
- Extract text with page tracking
- Show extraction stats

### Cell 7: Chunk Text
- Split text into chunks (~500 words)
- Add overlap for context
- Track page numbers

### Cell 8: Generate Embeddings
- Load OpenAI client
- Test embedding generation
- Show embedding dimensions

### Cell 9: Cost Estimation
- Estimate tokens per document
- Calculate OpenAI costs
- Show breakdown

### Cell 10: Insert to Database
- Generate embeddings for all chunks
- Insert chunks to PostgreSQL
- Update document status

### Cell 11: Verification
- Query total chunks in database
- Show document status
- Verify data integrity

### Cell 12: Semantic Search Test
- Generate query embedding
- Search using pgvector <=>
- Show top 5 results

---

## 🐛 Troubleshooting

### Error: "could not translate host name \"localhost\" to address"

**Solution:**
```bash
# Make sure docker services running
docker-compose -f docker-compose.yml up -d

# Verify
docker ps | grep system-llm
```

### Error: "could not connect to server: No such file or directory"

**Solution:**
```bash
# Check if port 5432 is in use
netstat -an | grep 5432

# If already in use, stop conflicting container
docker stop system-llm-postgres-local  # if exists

# Restart
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml up -d
```

### Error: "OPENAI_API_KEY not set"

**Solution:**
```bash
# Check .env file has key
grep OPENAI_API_KEY .env

# Add if missing:
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

### Error: "GCS bucket access denied"

**Solution:**
```bash
# Setup GCS credentials
gcloud auth application-default login

# Or use service account key
# Update .env: GCS_CREDENTIALS_PATH=/path/to/key.json
```

### Error: "No PDF files found in file_to_ingest"

**Solution:**
```bash
# Create folder if missing
mkdir -p file_to_ingest

# Add PDF files to folder
cp /path/to/documents/*.pdf file_to_ingest/

# Verify
ls file_to_ingest/
```

---

## 🚀 Common Workflows

### Upload & Process Documents

1. Copy PDF files to `file_to_ingest/` folder
2. Run all notebook cells from top
3. Check results in PostgreSQL (via pgAdmin)
4. Test search in final cell

### Just Test Search on Existing Data

1. Skip cells 5-10 (upload/processing)
2. Jump to cell 12 (semantic search test)
3. Run search test

### Check What's in Database

```bash
# Via Docker
docker exec system-llm-api psql -h localhost -U llm_user -d system_llm -c "SELECT COUNT(*) FROM document_chunk;"

# Via pgAdmin
# Open: http://localhost:5050
# Login: admin@admin.com / admin
# Query documents & chunks
```

---

## 📚 Additional Resources

| Resource | Link | Purpose |
|----------|------|---------|
| GCP Configuration | [GCP_CONFIGURATION.md](./GCP_CONFIGURATION.md) | Full GCP setup guide |
| Docker Compose | [docker-compose.yml](./docker-compose.yml) | Service orchestration |
| OpenAI Docs | https://platform.openai.com/docs | Embedding API docs |
| pgvector Docs | https://github.com/pgvector/pgvector | Vector database extension |
| Jupyter Docs | https://jupyter.org | Notebook documentation |

---

## 💡 Tips & Tricks

1. **Save notebook state:** Always run `docker-compose down` before shutting down
2. **Keep services fresh:** Restart with `docker-compose -f docker-compose.yml restart`
3. **View logs:** `docker logs system-llm-api -f` untuk real-time logs
4. **Test queries:** Use pgAdmin (localhost:5050) untuk interactive SQL
5. **Cost management:** Always run cost estimation before processing large batches

---

## ✅ Status

- ✅ Notebook ready for local Jupyter execution
- ✅ Automatic hostname conversion implemented
- ✅ GCP services properly containerized
- ✅ All dependencies documented
- ✅ Troubleshooting guide included

---

**Last Updated:** 2025-01-08
**Status:** Ready for Use
**Tested With:** Python 3.11+, Jupyter Lab, Docker Desktop
