# System LLM - Setup Pengembangan LOCAL

Panduan ini mencakup instalasi lengkap Backend dan Frontend dengan database PostgreSQL dan file storage lokal.

## Daftar Isi
1. [Requirements](#requirements)
2. [Instalasi](#instalasi)
3. [Memulai](#memulai)

---

## Requirements

Sebelum memulai, pastikan sudah terinstal:

- **Git** → [Download](https://git-scm.com/)
- **Docker & Docker Compose** → [Download](https://www.docker.com/products/docker-desktop)
- **Node.js** (untuk frontend) → [Download](https://nodejs.org/)
- **Python 3.x** (untuk backend) → [Download](https://www.python.org/)

**API Keys yang diperlukan:**
- OpenAI API Key → [Dapatkan](https://platform.openai.com/api-keys)
- Anthropic API Key → [Dapatkan](https://console.anthropic.com/)
- Google API Key → [Dapatkan](https://cloud.google.com/docs/authentication/api-keys)
- OpenRouter API Key → [Dapatkan](https://openrouter.ai/keys)

---

## Instalasi

### Step 1: Buat Folder Project dan Clone Repository

Buat folder baru untuk project:

```bash
mkdir system-llm
cd system-llm
```

Clone backend dan frontend di folder yang sama:

```bash
# Clone backend
git clone https://github.com/kaindraa/system-llm-backend system-llm-backend

# Clone frontend
git clone https://github.com/kaindraa/system-llm-frontend system-llm-frontend
```

Struktur folder akan seperti ini:
```
system-llm/
├── system-llm-backend/
└── system-llm-frontend/
```

### Step 2: Setup Backend - Konfigurasi Environment

Masuk ke folder backend:
```bash
cd system-llm-backend
```

Salin file environment lokal:

```bash
# Windows (PowerShell)
Copy-Item .env.local -Destination .env

# Mac/Linux
cp .env.local .env
```

Edit file `.env` dan tambahkan API keys:

```env
# Database
POSTGRES_USER=llm_user
POSTGRES_PASSWORD=llm_password_local
POSTGRES_DB=system_llm
DATABASE_URL=postgresql://llm_user:llm_password_local@postgres:5432/system_llm

# Storage
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=/app/storage

# API Keys (isi dengan keys yang sudah diperoleh)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=...

# Debug Mode
DEBUG=true
LOG_LEVEL=INFO
```

### Step 3: Mulai Docker Services (Backend)

```bash
docker-compose -f docker-compose.local.yml up -d
```

Ini akan memulai:
- PostgreSQL database (port 5432)
- PgAdmin (port 5050)
- Backend FastAPI (port 8000)

Tunggu 30-60 detik untuk semua services terinisialisasi.

### Step 4: Setup Database

Jalankan database migrations:

```bash
docker-compose -f docker-compose.local.yml exec api python -m alembic upgrade head
```

Import SQL dump yang berisi admin user dan AI models:

```bash
docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm < scripts/init.sql
```

Proses ini akan setup:
- Admin user: `admin@example.com` / `admin123`
- 6 AI models
- ChatConfig
- Struktur database lengkap

### Step 5: Setup Frontend

Buka terminal baru dan masuk ke folder frontend (dari parent directory):

```bash
cd ../system-llm-frontend
```

Install dependencies:

```bash
npm install
```

Setup environment file:

```bash
# Windows (PowerShell)
Copy-Item .env.local -Destination .env.local

# Mac/Linux
cp .env.local .env.local
```

Jika tidak ada file `.env.local`, buat file baru:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Step 6: Jalankan Frontend

```bash
npm run dev
```

Frontend akan berjalan di `http://localhost:3000`

---

## Memulai

### Akses Sistem

Setelah setup selesai, sistem dapat diakses melalui:

- **Frontend** → http://localhost:3000 (Tempat interface platform)
- **Backend Admin** http://localhost:8000/admin
- **API Documentation** → http://localhost:8000/docs (Swagger UI)
- **Admin Database** → http://localhost:5050 (PgAdmin)

### Login

Gunakan kredensial default:
- Email: `admin@example.com`
- Password: `admin123`

## Perintah Umum

**Backend (docker-compose):**
```bash
# Lihat log
docker-compose -f docker-compose.local.yml logs api

# Hentikan services
docker-compose -f docker-compose.local.yml down

# Restart services
docker-compose -f docker-compose.local.yml restart

# Akses database
docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm

# Akses backend shell
docker-compose -f docker-compose.local.yml exec api bash
```

**Frontend (development):**
```bash
# Hentikan dev server
Ctrl + C

# Build untuk production
npm run build

# Start development server
npm run dev
```
