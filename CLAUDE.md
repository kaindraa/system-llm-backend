# Rencana Pengembangan Sistem LLM untuk Pembelajaran

> **⚠️ CATATAN PENTING:** Ini adalah rencana pengembangan awal yang disusun berdasarkan Work Breakdown Structure (WBS) proyek. Rencana ini bersifat dinamis dan dapat berubah setelah diskusi kritis, evaluasi teknis, dan feedback selama proses pengembangan.

---

## 📋 Ringkasan Eksekutif

Dokumen ini menjelaskan rencana pengembangan sistem pembelajaran berbasis Large Language Model (LLM) dengan teknologi Retrieval-Augmented Generation (RAG). Sistem ini dirancang untuk memberikan pengalaman belajar yang dipersonalisasi bagi mahasiswa dengan memanfaatkan multiple LLM models (Llama, Qwen, Phi) dan kemampuan untuk memproses materi pembelajaran dari dokumen PDF.

---

## 🗓️ Rencana Pengembangan

### **Stage 1: Design**
**Tujuan:** Menyusun foundation teknis sebelum coding dimulai.

**Aktivitas:**
- Merancang Entity Relationship Diagram (ERD) untuk database
- Merancang arsitektur sistem secara keseluruhan
- Mendefinisikan struktur data dan relasi antar komponen

**Output:** Dokumentasi design yang menjadi acuan untuk semua stage berikutnya.

---

### **Stage 2: Setup**
**Tujuan:** Menyiapkan infrastruktur dan environment development.

**Aktivitas:**
- Setup repository dan version control
- Konfigurasi Docker untuk containerization
- Setup CI/CD pipeline untuk automated testing dan deployment
- Instalasi dan konfigurasi PostgreSQL dengan pgvector extension
- Setup admin database dashboard untuk monitoring
- Membuat skeleton FastAPI dengan struktur project yang proper
- Setup FastAPI automatic documentation
- Provisioning backend VM
- Setup file hosting solution
- Konfigurasi environment variables management
- Setup Alembic untuk database migration
- Konfigurasi logging system
- Setup pgvector index untuk vector database

**Output:** Development environment yang siap digunakan untuk coding.

---

### **Stage 3: Auth**
**Tujuan:** Implementasi sistem autentikasi dan autorisasi untuk memisahkan akses antara pengguna (mahasiswa) dan admin (peneliti).

**Fitur yang diimplementasikan:**
- Sistem login dengan kredensial terdaftar
- Registrasi user baru
- Role-based access control untuk Student (akses ke fitur pembelajaran)
- Role-based access control untuk Admin (akses penuh termasuk manajemen prompt dan analytics)
- JWT token management untuk session handling

**Aktivitas:**
- Implementasi endpoint login
- Implementasi endpoint register
- Setup role management
- Implementasi JWT generation dan validation

**Output:** Sistem autentikasi yang aman dengan pemisahan role yang jelas antara student dan admin.

---

### **Stage 4: LLM Integration**
**Tujuan:** Integrasi dengan multiple LLM models untuk memberikan variasi model yang dapat dipilih user.

**Fitur yang diimplementasikan:**
- Koneksi ke multiple LLM models (Llama, Qwen, Phi)
- Mechanism untuk switching antar model
- Basic inference capability untuk testing

**Aktivitas:**
- Setup koneksi ke LLM API (Llama, Qwen, Phi)
- Implementasi mechanism untuk switching antar model
- Membuat inference endpoint untuk testing LLM integration

**Output:** Backend yang dapat berkomunikasi dengan berbagai LLM models dan switch antar model sesuai kebutuhan.

---

### **Stage 5: Chat MVP**
**Tujuan:** Implementasi core chat functionality dengan LLM, termasuk manajemen konteks percakapan dan logging interaksi.

**Fitur yang diimplementasikan:**
- Chat interface dimana mahasiswa dapat bertanya
- Pemilihan model LLM (Llama, Qwen, atau Phi)
- Output jawaban LLM
- Penyimpanan konteks sesi untuk conversation continuity (Short-term Memory)
- Reset sesi pembelajaran untuk memulai topik baru
- Logging percakapan untuk keperluan analisis

**Aktivitas:**
- Implementasi CRUD untuk chat session (list of roles, messages, metadata)
- Implementasi basic chat flow (User → LLM → Response)
- Implementasi penyimpanan konteks sesi
- Implementasi reset sesi pembelajaran
- Implementasi logging setiap percakapan

**Output:** Working chat system yang dapat maintain conversation context dan logging interaksi.

**Catatan:** Pada stage ini menggunakan hardcoded system prompt (belum dinamis dari database) dan belum ada RAG integration. Multi-language support di-handle otomatis oleh LLM.

---

### **Stage 6: Prompt Management**
**Tujuan:** Enable admin untuk mengelola system prompts yang mengatur gaya komunikasi dan kedalaman jawaban LLM.

**Fitur yang diimplementasikan:**
- Input dan simpan system prompt sebagai template
- Pemilihan prompt aktif yang akan digunakan untuk sesi pembelajaran
- Integrasi prompt dengan chat flow

**Aktivitas:**
- Implementasi CRUD operations untuk system prompt
- Implementasi pemilihan prompt aktif untuk sesi chat
- Modifikasi chat flow (Stage 5) untuk menggunakan prompt dari database

**Output:** Flexible prompt management system yang memungkinkan peneliti bereksperimen dengan berbagai strategi instruksi dan membandingkan efektivitasnya.

---

### **Stage 7: File Management**
**Tujuan:** Enable users untuk upload dan manage PDF files sebagai materi pembelajaran.

**Fitur yang diimplementasikan:**
- Upload file PDF oleh user
- List dan detail file yang sudah diupload
- Download/preview file PDF
- Delete file

**Aktivitas:**
- Implementasi CRUD operations untuk file metadata
- Implementasi file storage service untuk menyimpan PDF
- Implementasi file serving API untuk download/preview PDF

**Output:** Sistem pengelolaan file yang aman dan terorganisir, siap untuk diproses oleh RAG pipeline.

---

### **Stage 8: RAG Pipeline**
**Tujuan:** Implement Retrieval-Augmented Generation untuk enable chat berdasarkan konten PDF yang diunggah.

**Fitur yang diimplementasikan:**
- Ingestion dan preprocessing PDF (ekstraksi teks)
- Chunking dokumen menjadi potongan optimal
- Embedding chunks ke vector database
- Retrieval data relevan saat user mengajukan pertanyaan
- Integrasi RAG dengan chat flow
- Menampilkan sumber jawaban (referensi dan transparansi)
- Navigasi ke sumber asli (judul PDF, halaman, potongan teks)
- Sinkronisasi data agar file baru langsung tersedia untuk query

**Aktivitas:**
- Implementasi text preprocessing dari PDF
- Implementasi chunking strategy
- Implementasi embedding generation dan penyimpanan ke vector database
- Implementasi retrieval logic
- Modifikasi chat flow (Stage 5) untuk mengintegrasikan RAG retrieval
- Implementasi reference dan navigation ke file sources

**Output:** Full RAG pipeline yang memungkinkan chat berdasarkan dokumen yang diunggah user. LLM dapat menjawab berdasarkan materi spesifik, bukan hanya pengetahuan umum model. Sistem menampilkan sumber referensi untuk meningkatkan kredibilitas dan memungkinkan verifikasi.

**Catatan:** Stage ini akan memodifikasi chat flow dari Stage 5 untuk menambahkan RAG capabilities.

---

### **Stage 9: After Chat Session Analytics**
**Tujuan:** Analyze chat logs untuk memahami tingkat pemahaman mahasiswa dan menghasilkan ringkasan pembelajaran.

**Fitur yang diimplementasikan:**
- Analisis pemahaman mahasiswa berdasarkan pola interaksi
- Klasifikasi tingkat pemahaman (Dasar, Menengah, Lanjut)
- Ringkasan akhir sesi otomatis
- Rekomendasi pembelajaran lanjutan

**Aktivitas:**
- Implementasi log processing service untuk extract insights
- Implementasi algoritma klasifikasi tingkat pemahaman (berdasarkan jenis pertanyaan, kompleksitas diskusi, pola pembelajaran)
- Implementasi generation ringkasan sesi chat otomatis (topik yang dibahas, konsep yang dikuasai, area yang perlu diperdalam)
- Membuat API endpoints untuk mengakses analytics data

**Output:** Comprehensive analytics system untuk research insights dan student progress tracking. Membantu mahasiswa merefleksikan pembelajaran mereka dan memberikan insight kepada peneliti tentang efektivitas sistem.

---

### **Stage 10: User Interface**
**Tujuan:** Build frontend aplikasi untuk semua fitur backend yang sudah dibangun.

**Fitur yang diimplementasikan:**
- Authentication pages (login, register)
- Chat interface dengan model selection dropdown
- File management interface (upload, list, preview PDF)
- Display referensi sumber dalam chat
- Session history dan progress overview
- User profile
- Admin dashboard dengan statistics dan charts
- Prompt management interface untuk admin
- Interaction logs viewer untuk admin
- Responsive design untuk berbagai device

**Aktivitas:**
- Membangun authentication pages
- Membangun chat interface dengan model selection dan source references
- Membangun file management interface
- Membangun session history interface
- Membangun user profile dan progress overview
- Membangun admin dashboard (daftar interaksi pengguna, statistik aktivitas sistem dengan grafik)
- Membangun prompt management interface untuk admin
- Membangun interaction logs viewer untuk admin
- Implementasi responsive design
- Implementasi error handling dan loading states

**Output:** Full-featured web application yang user-friendly untuk students dan admins, mengintegrasikan semua fitur backend.

---

### **Stage 11: Deployment**
**Tujuan:** Deploy aplikasi ke production environment yang stable, secure, dan monitored.

**Aktivitas:**
- Setup production server dan security hardening
- Konfigurasi production database dengan backup strategy
- Deploy aplikasi dengan containerization
- Setup reverse proxy dan SSL certificates
- Deploy frontend ke hosting platform
- Konfigurasi domain dan DNS
- Setup monitoring dan logging untuk production
- Implementasi backup strategy untuk database dan files
- Load testing untuk verify performance
- Setup CI/CD pipeline untuk automated deployment
- Dokumentasi deployment process dan troubleshooting

**Output:** Production-ready application yang dapat diakses oleh users dengan performa yang baik, keamanan yang terjaga, dan monitoring yang comprehensive.

---

## 📊 Alur Dependency Antar Stage

```
Stage 1 (Design)
  ↓
Stage 2 (Setup)
  ↓
Stage 3 (Auth) ────────────────────────┐
  ↓                                     ↓
Stage 4 (LLM) ──────────┐              ↓
  ↓                      ↓              ↓
Stage 5 (Chat MVP) ←────┴──────────────┘
  ↓
Stage 6 (Prompt) → Memodifikasi Chat
  ↓
Stage 7 (Files) ────────┐
  ↓                      ↓
Stage 8 (RAG) ─────→ Memodifikasi Chat
  ↓
Stage 9 (Analytics) ← Menggunakan logs dari Chat
  ↓
Stage 10 (UI) ← Menggunakan semua backend APIs
  ↓
Stage 11 (Deploy)
```

**Catatan Penting:**
- Stage 6 akan memodifikasi kode dari Stage 5 untuk menggunakan dynamic prompts
- Stage 8 akan memodifikasi kode dari Stage 5 untuk mengintegrasikan RAG
- Stage 9 membaca data logs yang dihasilkan oleh Stage 5

---

## 🔄 Pendekatan Development

### Incremental Development
Rencana ini menggunakan pendekatan incremental di mana sistem dibangun secara bertahap dengan fitur yang semakin kompleks:

1. **Foundation dulu:** Auth, LLM integration, basic chat
2. **Core features:** Prompt management, file management, RAG
3. **Advanced features:** Analytics, comprehensive UI
4. **Production ready:** Deployment dan monitoring

### Vertical Slice Approach
Chat MVP dibangun lebih awal (Stage 5) untuk:
- Validasi early integration LLM
- Feedback loop cepat
- Risk mitigation
- Demo-able product untuk stakeholders

Kemudian fitur-fitur advanced (prompt management, RAG) ditambahkan secara incremental.

### Modular Design
Setiap stage menghasilkan modul yang independent namun dapat diintegrasikan:
- Prompt management terpisah dari chat logic
- RAG pipeline terpisah dari chat logic
- Analytics terpisah dari core functionality

Ini memungkinkan parallel development dan easier maintenance.

---

## ⚠️ Area yang Memerlukan Perhatian Khusus

### 1. RAG Pipeline (Stage 8)
Area paling kompleks dalam project ini. Melibatkan banyak komponen yang perlu bekerja bersama dengan baik: text extraction, chunking, embedding, vector search, dan integration dengan chat.

### 2. Integration Points
Beberapa stage akan memodifikasi kode dari stage sebelumnya:
- Stage 6 memodifikasi Stage 5 (chat + prompts)
- Stage 8 memodifikasi Stage 5 (chat + RAG)

Perlu desain modular yang baik agar modifikasi tidak break existing functionality.

### 3. LLM Reliability
Sistem bergantung pada external LLM APIs yang mungkin memiliki downtime atau rate limits. Perlu error handling yang robust.

### 4. Vector Database Performance
Dengan dataset yang besar, retrieval speed bisa menjadi bottleneck. Perlu optimasi indexing dan query strategy.

### 5. Analytics Accuracy
Algoritma untuk mengklasifikasikan tingkat pemahaman mahasiswa perlu divalidasi dengan real data. Mungkin perlu iterasi beberapa kali.

---

## 📋 Keputusan Teknis yang Perlu Diambil

Beberapa keputusan teknis akan diambil di **Stage 1 (Design)** sebelum implementation:

### 1. LLM Integration
- Self-hosted models atau API-based service?
- Strategi untuk handle downtime dan fallback

### 2. Vector Database
- Menggunakan pgvector (integrated dengan PostgreSQL) atau dedicated vector DB?
- Index type (HNSW vs IVFFlat)

### 3. Embedding Model
- Model mana yang akan digunakan untuk embedding?
- Trade-off antara size, speed, dan accuracy

### 4. Chunking Strategy
- Fixed-size, semantic, atau recursive chunking?
- Optimal chunk size dan overlap

### 5. File Storage
- S3-compatible cloud storage atau local filesystem?
- Backup dan retention policy

### 6. Analytics Algorithm
- Rule-based, machine learning, atau LLM-based assessment?
- Metrics yang digunakan untuk classification

### 7. Frontend Framework
- React, Vue, atau Svelte?
- UI component library

Keputusan ini akan didiskusikan dan didokumentasikan sebelum implementation dimulai.

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Users dapat chat dengan 3 LLM models berbeda
- ✅ Users dapat upload PDF dan bertanya berdasarkan konten PDF
- ✅ System menampilkan sumber referensi untuk setiap jawaban
- ✅ System maintain context dalam satu sesi chat
- ✅ Admin dapat create dan manage system prompts
- ✅ System generate analytics dan summary otomatis
- ✅ Multi-language support (ID/EN) otomatis

### Non-Functional Requirements
- ⚡ Response time reasonable untuk user experience yang baik
- 🔒 Security: authentication, authorization, data privacy
- 📈 Scalability: dapat handle multiple concurrent users
- 🛡️ Reliability: error handling dan graceful degradation
- 📊 Observability: logging dan monitoring untuk troubleshooting

### Research Requirements
- 📝 Comprehensive logging untuk analisis penelitian
- 🔬 Flexible prompt management untuk eksperimen
- 📊 Analytics dashboard untuk insight penelitian
- 🎓 Student comprehension tracking

---

## 📝 Catatan Revisi

**Dokumen ini adalah living document** yang akan berkembang seiring berjalannya project.

### Hal yang Mungkin Berubah:
- **Technical stack:** Pilihan teknologi bisa berubah setelah proof of concept
- **Feature scope:** Penambahan atau pengurangan fitur berdasarkan feedback
- **Timeline:** Adjustments berdasarkan actual development speed
- **Implementation approach:** Refinements berdasarkan learnings

### Proses Perubahan:
Setiap perubahan signifikan akan:
1. Didiskusikan dengan stakeholders
2. Didokumentasikan dengan reasoning
3. Diupdate di dokumen ini dengan version tracking

---

## 🚀 Next Steps

1. **Review dokumen ini** dan pastikan semua pihak memahami scope dan approach
2. **Diskusi kritis** untuk:
   - Clarify ambiguities
   - Challenge assumptions
   - Identify potential issues
   - Align on priorities
3. **Finalize technical decisions** yang listed di section "Keputusan Teknis"
4. **Kickoff Stage 1 (Design)** dengan ERD dan architecture design

---

**Dokumen dibuat:** 2025-01-23
**Versi:** 1.0 (Draft Awal)
**Status:** Menunggu Review dan Diskusi Kritis
