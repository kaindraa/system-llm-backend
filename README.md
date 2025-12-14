# System LLM - Setup Pengembangan LOCAL

Panduan ini mencakup instalasi lengkap Backend dan Frontend dengan database PostgreSQL dan file storage lokal.

## Daftar Isi
1. [Requirements](#requirements)
2. [Instalasi](#instalasi)
   - Step 0: Install Prerequisites
   - Step 1: Clone Repository
   - Step 2: Setup Backend Environment
   - Step 3: Mulai Docker Services
   - Step 4: Setup Database
   - Step 5: Setup Frontend
   - Step 6: Jalankan Frontend
3. [Memulai](#memulai)

---

## Requirements

**PENTING: Install tools berikut DULU sebelum mulai setup!**

### Step 0: Install Prerequisites

Sebelum memulai, pastikan sudah terinstall:

1. **VSCode** (Text Editor) → [Download](https://code.visualstudio.com/)
   - Gunakan untuk edit file `.env.local` dan kode lainnya

2. **Docker Desktop** → [Download](https://www.docker.com/products/docker-desktop)
   - **PENTING: Buka aplikasi Docker Desktop sebelum menjalankan docker-compose!**
   - Docker harus running di background saat setup
   - Verifikasi dengan: `docker --version`

3. **Git** → [Download](https://git-scm.com/)
   - Untuk clone repository
   - Verifikasi dengan: `git --version`

4. **Node.js** (untuk frontend) → [Download](https://nodejs.org/)
   - Verifikasi dengan: `node --version`
   - **PENTING: Setelah install Node.js, install pnpm dengan:**
     ```bash
     npm install -g pnpm
     ```
   - Verifikasi dengan: `pnpm --version`

5. **Python 3.x** (untuk backend) → [Download](https://www.python.org/)
   - Verifikasi dengan: `python --version`

**API Keys yang diperlukan (minimal):**
- OpenAI API Key → [Dapatkan](https://platform.openai.com/api-keys) (untuk embedding dan chat)

### Verifikasi Prerequisites

Setelah install semua requirements, buka terminal/PowerShell **BARU** dan check versi:

```bash
git --version
docker --version
node --version
npm --version
pnpm --version
python --version
```

**Semua harus menampilkan versi, bukan "command not found".**

**Jika `pnpm --version` error:**
Jalankan: `npm install -g pnpm` (pastikan Node.js sudah ter-install dulu)

---

## Instalasi

### Step 1: Buat Folder Project dan Clone Repository

**PENTING: Tentukan satu folder untuk project dan gunakan konsisten!**

Buat folder baru untuk project (pilih SATU tempat):

```bash
mkdir system-llm
cd system-llm
```

**Gunakan folder ini untuk semua step selanjutnya.** Jangan ganti-ganti folder!

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

#### 2a. Buat File `.env.local`

**PENTING: Buat file dengan nama `.env.local` (untuk local development)**

Salin file environment example:

```bash
# Windows (PowerShell)
Copy-Item .env.example -Destination .env.local

# Mac/Linux
cp .env.example .env.local
```

**Verify file sudah dibuat:**
```bash
# Windows (PowerShell)
Get-Item .env.local

# Mac/Linux
ls -la .env.local
```

Harus menampilkan file `.env.local`.

#### 2b. Edit File `.env.local`

Buka file `.env.local` dengan text editor (Notepad, VSCode, dll) dan ganti isi dengan berikut:

**BAGIAN 1: Database & Security Configuration (WAJIB DIISI)**

```env
# Database
POSTGRES_USER=llm_user
POSTGRES_PASSWORD=llm_password_local
POSTGRES_DB=system_llm
DATABASE_URL=postgresql://llm_user:llm_password_local@postgres:5432/system_llm

# Security
# Untuk LOCAL development: gunakan value di bawah (tidak perlu generate)
# Untuk PRODUCTION: generate dengan: openssl rand -base64 32
SECRET_KEY=your-secret-key-local-development-only

# Storage
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=/app/storage

# Debug Mode
DEBUG=true
LOG_LEVEL=INFO
```

**Penjelasan BAGIAN 1:**

- **DATABASE_URL:** Jangan diubah (sudah benar untuk LOCAL)
- **SECRET_KEY:** Untuk LOCAL development, biarkan seperti itu. Hanya perlu di-generate untuk PRODUCTION
- **STORAGE_TYPE:** Untuk LOCAL, harus `local` (bukan `gcs`)
- **DEBUG:** Untuk development, harus `true`

---

**BAGIAN 2: LLM Provider Configuration (PILIH MINIMAL SATU)** 

di `.env.local`

Hanya isi API key dari provider yang Anda ingin gunakan. **Jika tidak ada key untuk provider, cukup hapus baris tersebut atau biarkan kosong.**

```env
# ===== PILIH MINIMAL SATU, SISA BISA DIHAPUS =====

# OpenAI (untuk GPT-4, GPT-3.5, embedding)
# Dapatkan API Key di: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY_HERE

# Anthropic Claude (untuk Claude 3.5, Claude 3)
# Dapatkan API Key di: https://console.anthropic.com/
# ANTHROPIC_API_KEY=sk-ant-YOUR_CLAUDE_KEY_HERE

# OpenRouter (akses semua model: GPT-4, Claude, Llama, Mistral, dll)
# Dapatkan API Key di: https://openrouter.ai/keys
# OPENROUTER_API_KEY=sk-or-YOUR_OPENROUTER_KEY_HERE

# Google Gemini
# Dapatkan API Key di: https://makersuite.google.com/app/apikey
# GOOGLE_API_KEY=YOUR_GOOGLE_KEY_HERE

# ===== OPTIONAL: Model Default =====
DEFAULT_LLM_MODEL=gpt-4-mini
```

**PENJELASAN BAGIAN 2:**

Untuk LOCAL development, **hanya perlu SATU API Key** saja. Pilih salah satu:

**OPSI 1: OpenAI (Recommended untuk mulai)**
- Buat akun: https://platform.openai.com/api-keys
- Isi: `OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE`
- Hapus/comment baris lain dengan `#`

**OPSI 2: Claude (Anthropic)**
- Buat akun: https://console.anthropic.com/
- Isi: `ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE`
- Hapus/comment baris lain

**OPSI 3: OpenRouter (Akses semua model)**
- Buat akun: https://openrouter.ai/keys
- Isi: `OPENROUTER_API_KEY=sk-or-YOUR_KEY_HERE`
- Hapus/comment baris lain


### Step 3: Mulai Docker Services (Backend)

**⚠️ PENTING: Sebelum jalankan command ini:**
1. **Pastikan Docker Desktop sudah dibuka** (aplikasi Docker Desktop harus running)
2. **Pastikan file `.env.local` sudah dibuat dan dikonfigurasi** (Step 2a & 2b)
3. **Verify file `.env.local` ada** di folder `system-llm-backend`
4. **Verify file `init-pgvector.sql` ada** di root folder `system-llm-backend` (diperlukan untuk PostgreSQL setup)


Pastikan Anda masih di folder `system-llm-backend`, kemudian jalankan:

**Windows (PowerShell):**
```bash
docker-compose --env-file .env.local -f docker-compose.local.yml up -d
```

**Mac/Linux:**
```bash
docker-compose -f docker-compose.local.yml up -d
```

Flag `--env-file .env.local` **penting untuk Windows** agar docker-compose membaca `.env.local` dengan benar.

**Apa yang terjadi:**
- Docker akan download dan build semua service
- Ini memulai 3 container:
  - **PostgreSQL** (database, port 5432)
  - **PgAdmin** (admin database, port 5050)
  - **Backend API** (FastAPI, port 8000)

**Tunggu 30-60 detik** sampai semua service selesai starting.

**Cara check apakah running:**
```bash
docker-compose -f docker-compose.local.yml ps
```

Semua container harus status `Up` (bukan `Exited` atau `Error`).

**Jika ada error**, check log dengan:
```bash
docker-compose -f docker-compose.local.yml logs
```

### Step 4: Setup Database

Import data awal ke database (struktur tabel dan admin user):

**Windows (PowerShell) - RECOMMENDED METHOD:**
```powershell
# Method 1: Copy file ke container dulu (paling reliable)
docker cp scripts/init.sql system-llm-postgres-local:/init.sql
docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm -f /init.sql
```

**Windows (PowerShell) - Alternative Method:**
```powershell
# Method 2: Gunakan Get-Content (jika Method 1 tidak work)
Get-Content scripts/init.sql | docker-compose -f docker-compose.local.yml exec -T postgres psql -U llm_user -d system_llm
```

**Mac/Linux:**
```bash
cat scripts/init.sql | docker-compose -f docker-compose.local.yml exec -T postgres psql -U llm_user -d system_llm
```

**Apa yang diimport:**
- Struktur database lengkap (semua tabel)
- Admin user: `admin@example.com` / Password: `admin123`
- AI models: GPT-4, Claude, Gemini, dll
- Chat config dan settings

**Verifikasi berhasil:**
```bash
docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
```

Harus menampilkan angka > 5 (minimal 5 tabel).

### Step 5: Setup Frontend

Frontend adalah aplikasi yang user lihat di browser (interface).

**PENTING: Pastikan Anda di folder yang SAMA seperti Step 1!**

Jika Anda di folder yang berbeda (misal `install-system-llm` vs `system-llm`), file `.env.example` tidak akan ditemukan.

#### 5a. Buka Terminal Baru

Buka terminal/PowerShell **BARU** (jangan tutup terminal sebelumnya yang menjalankan Docker).

Masuk ke folder frontend (dari parent `system-llm` folder yang sama seperti Step 1):

```bash
cd ../system-llm-frontend
```

#### 5b. Install Dependencies

Frontend menggunakan package manager `pnpm`. Install semua dependencies:

```bash
pnpm install
```

**Apa yang terjadi:**
- pnpm akan download ~500MB dependencies (pertama kali akan lama)
- Ini membuat folder `node_modules/` yang berisi semua library yang dibutuhkan
- Tunggu sampai selesai (tidak ada error di akhir)

#### 5c. Konfigurasi Environment Frontend

Buat file `.env.local`:

```bash
# Windows (PowerShell)
Copy-Item .env.example -Destination .env.local

# Mac/Linux
cp .env.example .env.local
```

Edit file `.env.local` (buka dengan text editor) dan ganti isi dengan (Jika belum ada):

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=System LLM
```

**Penjelasan:**
- `NEXT_PUBLIC_API_BASE_URL`: Alamat backend API (harus sama seperti Step 3)
- `NEXT_PUBLIC_APP_NAME`: Nama aplikasi yang muncul di tab browser

### Step 6: Jalankan Frontend

Di terminal yang sama (masih di folder `system-llm-frontend`), jalankan:

```bash
pnpm run dev
```

**Apa yang terjadi:**
- Frontend development server akan start
- Anda akan melihat log seperti:
  ```
  ▲ Next.js 15.x.x
  - ready started server on 0.0.0.0:3000
  ```
- Server jalan di port 3000

**Akses aplikasi:**
Buka browser dan masuk ke: http://localhost:3000

**Expected:**
- Halaman login muncul
- Jika tidak muncul, check terminal untuk error
- Jangan tutup terminal ini (development server harus tetap running)

**Cara stop:**
Tekan `Ctrl + C` di terminal untuk stop frontend dev server

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

---

## Verifikasi Instalasi

Setelah semua 6 step selesai, pastikan semuanya jalan dengan baik.

### ✓ Step 1: Check Backend API

Backend harus running di port 8000. Buka di browser:
```
http://localhost:8000/docs
```

**Expected:**
- Halaman Swagger API documentation muncul
- Tidak ada error di halaman
- Anda bisa melihat berbagai API endpoint

**Jika error:**
Cek log backend:
```bash
docker-compose -f docker-compose.local.yml logs api
```

### ✓ Step 2: Check Frontend

Frontend harus running di port 3000. Buka di browser:
```
http://localhost:3000
```

**Expected:**
- Halaman login muncul
- Ada field email dan password
- Tidak ada error di halaman

**Jika blank/error:**
- Check terminal frontend untuk error message
- Pastikan backend API URL benar di `.env.local`

### ✓ Step 3: Check Database (PgAdmin)

Akses admin database di:
```
http://localhost:5050
```

**Login:**
- Email: `admin@admin.com`
- Password: `admin`

**Check tabel:**
1. Di kiri, klik **Databases** > **system_llm**
2. Klik **Schemas** > **public**
3. Klik **Tables**

**Harus ada tabel:**
- `document` (untuk upload file)
- `document_chunk` (untuk RAG embeddings)
- `chat_session` (untuk chat history)
- `user` (untuk user account)
- `ai_model` (untuk LLM models)

Jika tidak ada, berarti migration atau init.sql gagal.

### ✓ Step 4: Login ke Aplikasi

Buka http://localhost:3000 dan login dengan:
```
Email: admin@example.com
Password: admin123
```

**Expected:**
- Login berhasil
- Dashboard atau main page muncul
- Tidak ada error

**Jika login gagal:**
- Pastikan database migration selesai
- Check apakah init.sql berhasil import

---

## Perintah Umum

**CATATAN: Untuk Windows, tambahkan `--env-file .env.local` di awal command agar docker-compose membaca environment variables dengan benar.**

**Backend (docker-compose) - Windows:**
```bash
# Lihat log
docker-compose --env-file .env.local -f docker-compose.local.yml logs api

# Hentikan services
docker-compose -f docker-compose.local.yml down

# Restart services
docker-compose --env-file .env.local -f docker-compose.local.yml up -d

# Akses database
docker-compose --env-file .env.local -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm

# Akses backend shell
docker-compose --env-file .env.local -f docker-compose.local.yml exec api bash
```

**Backend (docker-compose) - Mac/Linux:**
```bash
# Lihat log
docker-compose -f docker-compose.local.yml logs api

# Hentikan services
docker-compose -f docker-compose.local.yml down

# Restart services
docker-compose -f docker-compose.local.yml up -d

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
pnpm run build

# Start development server
pnpm run dev
```

---

## Troubleshooting

### Error: "env file .env.local not found"

**Penyebab:** File `.env.local` belum dibuat di Step 2a

**Solusi:**
```bash
# Cek file apa yang ada
dir .env*

# Jika belum ada .env.local, buat dari .env.example
Copy-Item .env.example -Destination .env.local

# Edit .env.local sesuai Step 2b, lalu coba lagi
docker-compose -f docker-compose.local.yml up -d
```

### Error: "Cannot find path '.env.example'"

**Penyebab:** Anda tidak di folder `system-llm-backend`

**Solusi:**
```bash
cd system-llm-backend
```

Verify Anda di folder yang benar dengan melihat di terminal. Harus ada list file (termasuk `.env.example`).

### Error: "docker: command not found" atau "docker-compose not found"

**Penyebab:** Docker tidak terinstall atau tidak di PATH

**Solusi:**
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop
2. Install dan restart komputer
3. Verify dengan: `docker --version`

### Error: "port 5432 already in use" atau "port 8000 already in use"

**Penyebab:** Ada proses lain yang pakai port yang sama

**Solusi:**
```bash
# Stop semua Docker container
docker-compose -f docker-compose.local.yml down

# Coba start lagi
docker-compose -f docker-compose.local.yml up -d
```

### Error: "UnicodeDecodeError" atau "invalid character in .env"

**Penyebab:** File `.env` ada karakter yang tidak valid

**Solusi:**
1. Hapus file `.env`
2. Buat ulang dari `.env.example`:
   ```bash
   Copy-Item .env.example -Destination .env
   ```
3. Edit dengan text editor yang benar (gunakan UTF-8 encoding)

### Error: "type \"vector\" does not exist" saat migration

**Penyebab:** Custom PostgreSQL image dengan pgvector belum selesai build, atau build error

**Solusi:**

1. **Stop semua container:**
   ```bash
   docker-compose -f docker-compose.local.yml down -v
   ```

2. **Rebuild dan start lagi:**
   ```bash
   docker-compose --env-file .env.local -f docker-compose.local.yml up -d
   ```

   Tunggu 3-5 menit sampai PostgreSQL image selesai build (pertama kali akan lama)

3. **Lihat build log untuk debug:**
   ```bash
   docker-compose -f docker-compose.local.yml logs postgres
   ```

4. **Setelah build selesai, run migration:**
   ```bash
   docker-compose -f docker-compose.local.yml exec api python -m alembic upgrade head
   ```

### Error: "pnpm: command not found"

**Penyebab:** pnpm tidak terinstall globally

**Solusi:**
```bash
npm install -g pnpm
```

Verify dengan: `pnpm --version`

### Backend jalan tapi frontend tidak bisa connect

**Penyebab:** `NEXT_PUBLIC_API_BASE_URL` di `.env.local` salah

**Solusi:**
1. Check `.env.local` di folder frontend
2. Pastikan `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` (sesuai dengan backend port)
3. Save file dan restart frontend:
   ```bash
   # Ctrl + C untuk stop
   pnpm run dev  # start lagi
   ```

### Database tidak ada tabel setelah migration

**Penyebab:** Migration atau init.sql gagal

**Solusi:**
1. Check error:
   ```bash
   docker-compose -f docker-compose.local.yml logs api
   ```
2. Manual check database:
   ```bash
   docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm -c "\dt"
   ```
3. Re-run migration:
   ```bash
   docker-compose -f docker-compose.local.yml exec api python -m alembic upgrade head
   docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm < scripts/init.sql
   ```

### Login gagal (email/password tidak work)

**Penyebab:** init.sql tidak diimport dengan benar

**Solusi:**
1. Check apakah user ada:
   ```bash
   docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm -c "SELECT * FROM user LIMIT 1;"
   ```
2. Jika tidak ada, re-import:
   ```bash
   docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm < scripts/init.sql
   ```

### Error: "FATAL: password authentication failed for user"

**Penyebab:** Database credentials di `.env.local` tidak sesuai dengan docker-compose config

**Solusi:**

1. Stop semua container:
   ```bash
   docker-compose -f docker-compose.local.yml down -v
   ```
   (Flag `-v` menghapus volume, termasuk database lama)

2. Edit `.env.local` dan **PASTIKAN** database credentials **TEPAT**:
   ```env
   POSTGRES_USER=llm_user
   POSTGRES_PASSWORD=llm_password_local
   POSTGRES_DB=system_llm
   DATABASE_URL=postgresql://llm_user:llm_password_local@postgres:5432/system_llm
   ```

3. Start lagi:
   ```bash
   docker-compose -f docker-compose.local.yml up -d
   ```

**Penting:** Username harus `llm_user` (bukan `postgres`) untuk LOCAL setup.

### Error: "CORS policy: Response to preflight request doesn't pass access control check"

**Penyebab:** Docker container sudah running dengan config lama. Perubahan di `.env.local` belum terbaca container.

**Solusi:**

Docker **membaca `.env.local` saat startup**. Jika sudah running, config lama tetap dipakai. Harus restart.

**Windows (PowerShell):**
```bash
# Stop semua container
docker-compose -f docker-compose.local.yml down

# Start lagi dengan --env-file flag (penting untuk Windows)
docker-compose --env-file .env.local -f docker-compose.local.yml up -d

# Jalankan migration dan import data lagi
docker-compose --env-file .env.local -f docker-compose.local.yml exec api python -m alembic upgrade head
docker-compose --env-file .env.local -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm < scripts/init.sql
```

**Mac/Linux:**
```bash
# Stop semua container
docker-compose -f docker-compose.local.yml down

# Start lagi
docker-compose -f docker-compose.local.yml up -d

# Jalankan migration dan import data lagi
docker-compose -f docker-compose.local.yml exec api python -m alembic upgrade head
docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm < scripts/init.sql
```

**Verifikasi CORS sudah aktif:**

Windows (PowerShell):
```bash
docker-compose -f docker-compose.local.yml logs api | Select-String -Pattern "CORS"
```

Mac/Linux:
```bash
docker-compose -f docker-compose.local.yml logs api | grep -i cors
```

Harus menampilkan CORS origins yang benar (termasuk frontend port yang digunakan).

### Still having issues?

Collect info untuk debugging:
```bash
# 1. Docker status
docker-compose -f docker-compose.local.yml ps

# 2. Backend log
docker-compose -f docker-compose.local.yml logs api --tail=50

# 3. Check database connection
docker-compose -f docker-compose.local.yml exec postgres psql -U llm_user -d system_llm -c "SELECT version();"
```

Kirimkan output ini ketika minta help.
