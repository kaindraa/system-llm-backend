# System LLM Backend - Dokumentasi Komprehensif

> **Dokumentasi ini berfungsi sebagai konteks lengkap untuk LLM sessions berikutnya. Berisi arsitektur, database, API, struktur file, dan penjelasan detail setiap komponen.**

**Last Updated:** 2025-11-08
**Project Status:** Production Ready (Stages 1-9 Completed) - ✨ RAG with Tool Calling

---

## 📋 Ringkasan Eksekutif

Sistem LLM Backend adalah aplikasi FastAPI yang mengintegrasikan multiple LLM providers (OpenAI, Anthropic, Google) dengan Retrieval-Augmented Generation (RAG) untuk sistem pembelajaran interaktif. Sistem mendukung:

- ✅ Chat interaktif dengan 3+ LLM models
- ✅ Upload dan processing PDF untuk RAG
- ✅ Vector embeddings dengan pgvector untuk semantic search
- ✅ **LLM Tool Calling** - LLM intelligent decides when to search documents
- ✅ Manajemen sistem prompts dinamis
- ✅ Session management dengan JSONB messages + sources
- ✅ Role-based access control (Admin/Student)
- ✅ Admin panel untuk database management
- ✅ Streaming responses dengan Server-Sent Events (SSE) + RAG events

---

## 🏗️ TEKNOLOGI STACK

### Framework & Server
- **FastAPI 0.109.0** - Async Python web framework
- **Uvicorn 0.27.0** - ASGI server
- **Python 3.11** - Programming language

### Database & ORM
- **PostgreSQL** - Primary relational database
- **SQLAlchemy 2.0.25** - ORM dengan async support
- **Alembic 1.13.1** - Database migrations
- **pgvector 0.2.4** - Vector embedding storage dan semantic search
- **psycopg2-binary 2.9.9** - PostgreSQL adapter

### Authentication & Security
- **python-jose 3.3.0** - JWT token generation/verification
- **passlib 1.7.4** - Password hashing framework
- **bcrypt 4.1.2** - Cryptographic hashing algorithm
- **HTTPBearer** - Bearer token security scheme

### Admin & UI
- **SQLAdmin 0.21.0** - Auto-generated admin panel untuk CRUD operations
- **itsdangerous 2.1.2** - Secure session data signing

### LLM Integration
- **langchain-core >= 1.0.0** - Base LLM framework
- **langchain-openai** - OpenAI GPT models integration
- **langchain-anthropic** - Anthropic Claude integration
- **langchain-google-genai >= 3.0.0** - Google Gemini integration

### Cloud & Storage
- **google-cloud-storage 2.10.0** - GCS for file storage
- **Cloud SQL Proxy** - Secure database connection to GCP

### Configuration & Utilities
- **python-dotenv 1.0.0** - Environment variable management
- **pydantic >= 2.7.4** - Data validation dan serialization
- **pydantic-settings >= 2.1.0** - Configuration management
- **email-validator 2.1.0** - Email format validation
- **python-dateutil 2.8.2** - Date/time utilities
- **python-multipart 0.0.6** - Multipart form data parsing

---

## 📁 STRUKTUR PROYEK

```
system-llm-backend/
├── app/                              # Main application package
│   ├── main.py                      # FastAPI app initialization, route registration
│   ├── admin/
│   │   ├── auth.py                 # Admin authentication backend untuk SQLAdmin
│   │   └── views.py                # Admin ModelViews untuk database CRUD
│   ├── api/
│   │   ├── dependencies.py          # Shared dependencies: auth, db sessions
│   │   └── v1/
│   │       └── endpoints/           # API route handlers
│   │           ├── auth.py          # POST/GET endpoints: register, login, me
│   │           ├── chat.py          # Chat sessions: CRUD + streaming messages
│   │           ├── file.py          # File upload/download/management
│   │           ├── prompt.py        # System prompt management (admin only)
│   │           └── user.py          # User listing (admin only)
│   ├── core/
│   │   ├── config.py               # Pydantic Settings: database, LLM keys, security
│   │   ├── database.py             # SQLAlchemy engine + session factory
│   │   ├── logging.py              # Logger setup (console + file handlers)
│   │   └── security.py             # Password hashing + JWT utilities
│   ├── models/                      # SQLAlchemy ORM models (6 tables)
│   │   ├── user.py                 # User (ADMIN/STUDENT roles)
│   │   ├── chat_session.py          # Chat sessions (JSONB messages array)
│   │   ├── document.py              # PDF document metadata
│   │   ├── document_chunk.py        # Document chunks + pgvector embeddings
│   │   ├── model.py                # LLM model registry
│   │   └── prompt.py               # System prompts
│   ├── schemas/                     # Pydantic request/response schemas
│   │   ├── auth.py                 # Login/register/token schemas
│   │   ├── chat.py                 # Chat session/message schemas
│   │   ├── file.py                 # File metadata schemas
│   │   ├── prompt.py               # Prompt management schemas
│   │   ├── user.py                 # User response schemas
│   │   └── llm.py                  # LLM-related schemas
│   ├── services/                    # Business logic layer
│   │   ├── auth.py                 # Authentication service
│   │   ├── chat/
│   │   │   └── chat_service.py      # Chat session + message management with RAG
│   │   ├── file_service.py          # Pluggable file storage (local/GCS)
│   │   ├── prompt_service.py        # Prompt CRUD + active state management
│   │   ├── rag/
│   │   │   ├── rag_service.py      # Semantic search + embeddings
│   │   │   ├── tools.py            # Langchain RAG tool definitions
│   │   │   └── __init__.py
│   │   └── llm/
│   │       ├── base.py             # Abstract BaseLLMProvider class
│   │       ├── llm_service.py       # LLM provider factory + registry
│   │       ├── openai_provider.py   # OpenAI with tool calling support
│   │       ├── anthropic_provider.py # Anthropic with tool calling support
│   │       └── google_provider.py
│   ├── middleware/
│   │   └── logging.py              # Request/response logging middleware
│   └── scripts/
│       ├── seed_admin.py            # Create first admin user
│       └── seed_models.py           # Seed LLM model registry
├── alembic/                         # Database schema versioning
│   ├── versions/                   # Migration files
│   │   ├── 683738efbac7_initial_migration_create_6_tables.py
│   │   ├── b5ede45b7881_sync_models.py
│   │   ├── c82c550cf83d_add_order_column_to_model.py
│   │   ├── e7b67a707145_remove_config_and_is_active_from_model.py
│   │   └── f1a2b3c4d5e6_add_content_column_to_document.py
│   └── alembic.ini
├── Dockerfile                       # Docker image (Python 3.11 + dependencies)
├── docker-compose.yml               # Services: cloud-sql-proxy, pgadmin, api
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variable template
├── .env                            # Environment variables (NOT in git)
├── entrypoint.sh                   # Docker container startup script
└── alembic.ini                     # Alembic configuration
```

---

## 🗄️ DATABASE SCHEMA

### 6 Core Tables dengan Relasi

#### 1. **user** - User Accounts
```sql
CREATE TABLE "user" (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  password_hash VARCHAR NOT NULL,
  full_name VARCHAR NOT NULL,
  role VARCHAR DEFAULT 'STUDENT',  -- ENUM: STUDENT, ADMIN
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
-- Indexes: email (unique)
```

**Relationships:**
- One-to-Many: `chat_sessions` (user uploads chat sessions)

**Roles:**
- **STUDENT**: Akses chat, file upload, view prompts
- **ADMIN**: Full access + prompt management, user management, analytics

---

#### 2. **model** - LLM Model Registry
```sql
CREATE TABLE model (
  id UUID PRIMARY KEY,
  name VARCHAR UNIQUE NOT NULL,  -- e.g., "gpt-4-turbo", "claude-3-sonnet"
  display_name VARCHAR NOT NULL,
  provider VARCHAR NOT NULL,      -- ENUM: openai, anthropic, google
  api_endpoint VARCHAR,           -- Optional custom endpoint
  order INTEGER,                  -- Display priority in UI
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
-- Indexes: name (unique), order
```

**Providers Supported:**
- **openai** → GPT-4, GPT-4-turbo, GPT-3.5-turbo
- **anthropic** → Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **google** → Gemini-pro, Gemini-pro-vision

**Relationships:**
- One-to-Many: `chat_sessions` (model selection per session)

---

#### 3. **prompt** - System Prompts
```sql
CREATE TABLE prompt (
  id UUID PRIMARY KEY,
  name VARCHAR NOT NULL,
  content TEXT NOT NULL,          -- Prompt template
  description TEXT,
  is_active BOOLEAN DEFAULT FALSE, -- Only ONE prompt active at a time
  created_by UUID NOT NULL,       -- FK: user (admin)
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
-- Indexes: is_active, created_by
```

**Purpose:** Enable researchers to experiment dengan different system prompts dan compare effectiveness

**Example Prompts:**
- "Bantu sebagai guru yang sabar dan detail"
- "Jelaskan dengan cara yang sederhana untuk pemula"
- "Jawab dengan struktur formal dan scientifik"

---

#### 4. **chat_session** - Conversation Sessions
```sql
CREATE TABLE chat_session (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,          -- FK: user
  prompt_id UUID NOT NULL,        -- FK: prompt (system prompt saat dibuat)
  model_id UUID NOT NULL,         -- FK: model (LLM yang dipakai)
  title VARCHAR,                  -- Session title e.g., "Belajar Python Loops"
  messages JSONB DEFAULT '[]',    -- Array of message objects
  status VARCHAR DEFAULT 'ACTIVE', -- ENUM: ACTIVE, COMPLETED
  total_messages INTEGER DEFAULT 0,
  comprehension_level VARCHAR,    -- ENUM: BASIC, INTERMEDIATE, ADVANCED
  summary TEXT,                   -- Auto-generated session summary
  started_at DATETIME DEFAULT NOW(),
  ended_at DATETIME,
  analyzed_at DATETIME,
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
-- Indexes: user_id, model_id, status, created_at
```

**messages JSONB Structure:**
```json
[
  {
    "role": "user|assistant|system",
    "content": "Pertanyaan atau jawaban",
    "created_at": "2025-11-06T10:30:00",
    "sources": [
      {
        "document_id": "uuid",
        "document_name": "materi.pdf",
        "page_number": 5,
        "chunk_index": 3,
        "relevance_score": 0.95
      }
    ]
  }
]
```

**Relationships:**
- Many-to-One: `user` (session owner)
- Many-to-One: `model` (LLM choice)
- Many-to-One: `prompt` (system prompt)

---

#### 5. **document** - PDF Document Metadata
```sql
CREATE TABLE document (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,          -- FK: user (document owner)
  filename VARCHAR NOT NULL,      -- UUID-based system filename
  original_filename VARCHAR,      -- User's original filename
  file_path VARCHAR NOT NULL,     -- Storage path (local or GCS)
  file_size BIGINT,               -- File size in bytes
  mime_type VARCHAR,              -- File content type
  content TEXT,                   -- Extracted text from PDF
  status VARCHAR DEFAULT 'UPLOADED', -- ENUM: UPLOADED, PROCESSING, PROCESSED, FAILED
  uploaded_at DATETIME DEFAULT NOW(),
  processed_at DATETIME,
  created_at DATETIME DEFAULT NOW(),
  updated_at DATETIME DEFAULT NOW()
);
-- Indexes: user_id, status, created_at
```

**Status Flow:**
1. **UPLOADED** → User uploads file
2. **PROCESSING** → System extracting text and creating embeddings
3. **PROCESSED** → Ready for RAG queries
4. **FAILED** → Error during processing (retry available)

**Relationships:**
- One-to-Many: `document_chunks` (CASCADE delete)

---

#### 6. **document_chunk** - Vector Embeddings for RAG
```sql
CREATE TABLE document_chunk (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL,      -- FK: document (parent)
  chunk_index INTEGER NOT NULL,   -- Sequence number
  content TEXT NOT NULL,          -- Text content
  page_number INTEGER,            -- PDF page
  embedding vector(768),          -- pgvector embedding (768-dim)
  chunk_metadata JSONB,           -- Metadata: heading, context, etc.
  created_at DATETIME DEFAULT NOW()
);
-- Indexes: document_id, created_at
-- pgvector Indexes: HNSW atau IVFFlat untuk nearest neighbor search
```

**chunk_metadata Structure:**
```json
{
  "heading": "Section Title",
  "context_before": "Previous paragraph excerpt",
  "context_after": "Next paragraph excerpt",
  "section_type": "paragraph|heading|table"
}
```

**Purpose:** Enable semantic search untuk RAG retrieval

**Relationships:**
- Many-to-One: `document` (parent document)

---

## 🔌 API ENDPOINTS

### Base URL: `http://localhost:8000/api/v1`

### ✅ Health & Status
```
GET /                    - Root endpoint (200 OK status)
GET /health              - Health check (database, pgvector version)
GET /docs                - Swagger UI interactive documentation
GET /redoc               - ReDoc documentation
```

---

### 🔐 Authentication (`/auth`)

#### Register New Student
```http
POST /auth/register
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}

Response 201:
{
  "id": "uuid",
  "email": "student@example.com",
  "full_name": "John Doe",
  "role": "STUDENT",
  "created_at": "2025-11-06T10:30:00"
}
```

#### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "securepassword123"
}

Response 200:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /auth/me
Authorization: Bearer {access_token}

Response 200:
{
  "id": "uuid",
  "email": "student@example.com",
  "full_name": "John Doe",
  "role": "STUDENT"
}
```

---

### 💬 Chat Sessions (`/chat`)

#### Get Configuration (Models & Active Prompt)
```http
GET /chat/config

Response 200:
{
  "models": [
    {
      "id": "uuid",
      "name": "gpt-4-turbo",
      "display_name": "GPT-4 Turbo",
      "provider": "openai"
    },
    ...
  ],
  "active_prompt": {
    "id": "uuid",
    "name": "Guru Sabar",
    "content": "..."
  }
}
```

#### Create Chat Session
```http
POST /chat/sessions
Authorization: Bearer {token}
Content-Type: application/json

{
  "model_id": "uuid-of-gpt4",
  "title": "Belajar Python Loops",
  "prompt_id": "uuid-of-active-prompt"  // Optional, uses active prompt if not provided
}

Response 201:
{
  "id": "session-uuid",
  "user_id": "user-uuid",
  "model_id": "model-uuid",
  "title": "Belajar Python Loops",
  "status": "ACTIVE",
  "total_messages": 0,
  "started_at": "2025-11-06T10:30:00"
}
```

#### List User's Chat Sessions
```http
GET /chat/sessions?skip=0&limit=10&status=ACTIVE

Response 200:
{
  "total": 25,
  "sessions": [
    {
      "id": "uuid",
      "title": "Belajar Python Loops",
      "status": "ACTIVE",
      "total_messages": 12,
      "started_at": "2025-11-06T10:30:00"
    },
    ...
  ]
}
```

#### Get Chat Session Details (with Messages)
```http
GET /chat/sessions/{session_id}

Response 200:
{
  "id": "session-uuid",
  "title": "Belajar Python Loops",
  "model": {
    "id": "uuid",
    "name": "gpt-4-turbo"
  },
  "status": "ACTIVE",
  "total_messages": 12,
  "messages": [
    {
      "role": "system",
      "content": "Kamu adalah guru yang sabar...",
      "created_at": "2025-11-06T10:30:00"
    },
    {
      "role": "user",
      "content": "Apa itu loop?",
      "created_at": "2025-11-06T10:31:00"
    },
    {
      "role": "assistant",
      "content": "Loop adalah...",
      "created_at": "2025-11-06T10:31:30",
      "sources": [
        {
          "document_name": "python-basics.pdf",
          "page_number": 5
        }
      ]
    }
  ]
}
```

#### Send Message (Streaming SSE Response with RAG)
```http
POST /chat/sessions/{session_id}/messages
Authorization: Bearer {token}
Content-Type: application/json

{
  "message": "Apa bedanya while dan for loop?"
}

Response: 200 (text/event-stream)

// User message
event: user_message
data: {"role": "user", "content": "Apa bedanya...", "created_at": "..."}

// Optional: RAG tool call (if LLM decides to search)
event: rag_search
data: {"query": "while for loop perbedaan", "status": "searching"}

// RAG results returned
event: rag_search
data: {"query": "while for loop perbedaan", "results_count": 3, "status": "completed"}

// Response chunks as LLM generates
event: chunk
data: {"content": "While"}

event: chunk
data: {"content": " loop"}

// Final response with sources
event: done
data: {
  "role": "assistant",
  "content": "While loop...",
  "sources": [
    {
      "document_id": "uuid",
      "filename": "python-loops.pdf",
      "page": 5,
      "similarity_score": 0.92
    }
  ]
}

**Note:** RAG is automatic - LLM decides whether to call semantic_search tool.
If documents are relevant to query, LLM will search them. Sources are included
in final response if RAG was used.
```

#### Update Chat Session (Admin Only)
```http
PATCH /chat/sessions/{session_id}
Authorization: Bearer {token}  // Must be ADMIN
Content-Type: application/json

{
  "title": "New title",
  "status": "COMPLETED"
}

Response 200: Updated session
```

#### Delete Chat Session (Admin Only)
```http
DELETE /chat/sessions/{session_id}
Authorization: Bearer {token}  // Must be ADMIN

Response 204: No Content
```

---

### 📄 File Management (`/files`)

#### Upload PDF File
```http
POST /files/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <binary PDF data>

Response 201:
{
  "id": "file-uuid",
  "filename": "generated-uuid.pdf",
  "original_filename": "materi-python.pdf",
  "file_size": 2048576,
  "status": "PROCESSING",
  "uploaded_at": "2025-11-06T10:30:00"
}
```

#### List All Files (System-wide)
```http
GET /files?skip=0&limit=10&status=PROCESSED

Query Parameters:
- **skip**: Number of records to skip (for pagination)
- **limit**: Maximum number of records to return (1-100)
- **status**: Optional filter by document status (uploaded, processing, processed, failed)

Response 200:
{
  "total": 5,
  "files": [
    {
      "id": "uuid",
      "original_filename": "materi-python.pdf",
      "file_size": 2048576,
      "status": "PROCESSED",
      "uploaded_at": "2025-11-06T10:30:00"
    }
  ],
  "page": 1,
  "page_size": 10
}
```

**Notes:**
- Returns ALL files in the system (not just user's own files)
- All authenticated users can see all files
- Ordered by upload date (newest first)

#### Get File Details
```http
GET /files/{file_id}

Response 200:
{
  "id": "file-uuid",
  "original_filename": "materi-python.pdf",
  "file_size": 2048576,
  "status": "PROCESSED",
  "content": "Extracted text content of PDF...",
  "uploaded_at": "2025-11-06T10:30:00",
  "processed_at": "2025-11-06T10:35:00"
}
```

**Authorization:** All authenticated users can access any file's details.

#### Download File
```http
GET /files/{file_id}/download

Response 200: (application/pdf)
<binary PDF content>
```

**Authorization:** All authenticated users can download any file.

#### Delete File (Admin Only)
```http
DELETE /files/{file_id}
Authorization: Bearer {token}  // ADMIN required

Response 204: No Content
// Also deletes associated document_chunks
```

**Authorization:** Requires ADMIN role. Non-admin users will get 403 Forbidden.

#### Update File Status (Admin Only)
```http
PATCH /files/{file_id}/status
Authorization: Bearer {token}  // ADMIN required
Content-Type: application/json

{
  "status": "PROCESSED"  // or FAILED
}

Response 200: Updated file
```

**Authorization:** Requires ADMIN role. Non-admin users will get 403 Forbidden.

---

### 📌 System Prompts (`/prompts`) - Admin Only

#### Create Prompt
```http
POST /prompts
Authorization: Bearer {token}  // ADMIN required
Content-Type: application/json

{
  "name": "Guru Sabar",
  "content": "Kamu adalah guru yang sangat sabar...",
  "description": "Prompt untuk mengajar dengan cara yang friendly",
  "is_active": true  // Deactivates other prompts
}

Response 201: Created prompt
```

#### List Prompts
```http
GET /prompts?skip=0&limit=10&search=guru

Response 200:
{
  "total": 3,
  "prompts": [
    {
      "id": "uuid",
      "name": "Guru Sabar",
      "description": "...",
      "is_active": true,
      "created_at": "..."
    }
  ]
}
```

#### Get Specific Prompt
```http
GET /prompts/{prompt_id}

Response 200: Prompt details with full content
```

#### Update Prompt
```http
PUT /prompts/{prompt_id}
Content-Type: application/json

{
  "name": "Guru Sabar (Updated)",
  "content": "New content...",
  "description": "..."
}

Response 200: Updated prompt
```

#### Activate Prompt
```http
PATCH /prompts/{prompt_id}/activate

Response 200:
{
  "id": "prompt-uuid",
  "name": "Guru Sabar",
  "is_active": true  // Other prompts auto-deactivated
}
```

#### Delete Prompt
```http
DELETE /prompts/{prompt_id}

Response 204: No Content
```

---

### 👥 User Management (`/users`) - Admin Only

#### List All Users with Stats
```http
GET /users

Response 200:
[
  {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "STUDENT",
    "chat_count": 12,
    "created_at": "..."
  }
]
```

#### Get User's Chat History
```http
GET /users/{user_id}/chats

Response 200:
{
  "user": {...},
  "chats": [...]
}
```

---

### 🔍 RAG (Retrieval-Augmented Generation) (`/rag`)

#### RAG Health Check
```http
GET /rag/health

Response 200:
{
  "status": "healthy",
  "embeddings": {
    "available": true,
    "model": "text-embedding-3-small (1536 dimensions)"
  },
  "pgvector": {
    "available": true,
    "total_chunks": 42,
    "total_documents": 3,
    "processed_documents": 3
  },
  "errors": []
}
```

#### RAG Configuration
```http
GET /rag/config

Response 200:
{
  "embeddings": {
    "provider": "OpenAI",
    "model": "text-embedding-3-small",
    "dimensions": 1536,
    "available": true
  },
  "vector_database": {
    "system": "PostgreSQL with pgvector extension",
    "similarity_metric": "Cosine similarity (1 - distance)",
    "available": true
  },
  "documents": {
    "total": 3,
    "processed": 3,
    "pending": 0,
    "total_chunks": 42
  },
  "search_settings": {
    "default_top_k": 5,
    "min_similarity_threshold": 0.65,
    "max_results": 20
  }
}
```

#### Semantic Search (Direct API)
```http
POST /rag/search
Authorization: Bearer {token}
Content-Type: application/json

Query Parameters:
- query (string, required): Search query
- top_k (int, default 5): Number of results (max 20)
- similarity_threshold (float, default 0.7): Minimum relevance score

Example:
POST /rag/search?query=apa%20itu%20NAT&top_k=5&similarity_threshold=0.7

Response 200:
{
  "query": "apa itu NAT",
  "results": [
    {
      "chunk_id": "uuid",
      "content": "Network Address Translation (NAT) adalah...",
      "document_id": "uuid",
      "filename": "H03 - NAT & OSPF.pdf",
      "page": 5,
      "similarity_score": 0.92,
      "chunk_index": 2,
      "metadata": {"heading": "NAT Definition"}
    },
    ...
  ],
  "count": 5,
  "top_k": 5,
  "threshold": 0.7
}
```

**Note:** In normal chat flow, RAG is called automatically via tool calling.
This endpoint is primarily for testing/debugging purposes.

---

## 🔧 CORE SERVICES

### Authentication Service (`app/services/auth.py`)
```python
def create_access_token(data: dict, expires_delta: timedelta = None) -> str
    # Generate JWT token, default 24 hours expiration

def authenticate_user(email: str, password: str) -> User
    # Verify email exists and password matches hash

def create_user(email: str, password: str, full_name: str, role: str = "STUDENT") -> User
    # Create new user with bcrypt-hashed password

def get_user_by_email(email: str) -> User
    # Lookup user by email
```

**Key Details:**
- Token Algorithm: HS256 (HMAC SHA-256)
- Default Expiration: 24 hours
- Password Hashing: bcrypt via passlib

---

### Chat Service (`app/services/chat/chat_service.py`)
```python
async def create_session(user_id: str, model_id: str, title: str, prompt_id: str = None) -> ChatSession
    # Create new chat session, use active prompt if not specified

async def get_session(session_id: str) -> ChatSession
    # Retrieve session with all messages

async def list_sessions(user_id: str, skip: int, limit: int, status: str = None) -> List[ChatSession]
    # Paginated listing with optional status filter

async def update_session(session_id: str, title: str = None, status: str = None) -> ChatSession
    # Update session metadata (admin only)

async def delete_session(session_id: str)
    # Remove session and all messages

async def send_message_stream(session_id: str, user_message: str) -> AsyncGenerator
    # MAIN FEATURE: Streaming message handling
    # 1. Add user message to messages JSONB array
    # 2. Retrieve system prompt
    # 3. Get RAG context if documents exist
    # 4. Call LLM with streaming
    # 5. Yield response chunks in real-time (SSE)
    # 6. Add assistant message to database
    # 7. Extract and store source references
```

**Message Format in JSONB:**
```json
{
  "role": "user|assistant",
  "content": "Message text",
  "created_at": "ISO timestamp",
  "sources": [
    {
      "document_id": "uuid",
      "document_name": "filename.pdf",
      "page_number": 5
    }
  ]
}
```

---

### File Service (`app/services/file_service.py`)
**Pattern:** Abstract base class with pluggable implementations

```python
class FileStorageProvider(ABC):
    async def save_file(path: str, content: bytes) -> None
    async def get_file(path: str) -> bytes
    async def delete_file(path: str) -> None
    async def exists(path: str) -> bool

class LocalFileStorage(FileStorageProvider):
    # Store files in local directory: storage/uploads/{user_id}/{filename}

class GCSStorageProvider(FileStorageProvider):
    # Store files in Google Cloud Storage bucket
```

**File Service Methods:**
```python
async def create_file(user_id: str, filename: str, content: bytes, original_filename: str) -> Document
    # Save to storage provider and create DB record

async def get_file(file_id: str) -> Document
    # Retrieve file metadata

async def get_file_content(file_id: str) -> bytes
    # Get actual file binary content

async def list_files(user_id: str, skip: int, limit: int, status: str = None) -> List[Document]
    # Paginated file listing with filtering

async def delete_file(file_id: str)
    # Remove from storage and database

async def update_file_status(file_id: str, status: str) -> Document
    # Update processing status
```

**Supported Storage Types:**
- `local` - Filesystem storage (development)
- `gcs` - Google Cloud Storage (production)

---

### Prompt Service (`app/services/prompt_service.py`)
```python
async def create_prompt(name: str, content: str, description: str, is_active: bool, created_by: str) -> Prompt
    # Create prompt, deactivate others if is_active=true

async def get_prompt(prompt_id: str) -> Prompt

async def get_active_prompt() -> Prompt
    # Get currently active prompt for new sessions

async def list_prompts(skip: int, limit: int, search: str = None) -> List[Prompt]
    # Search by name/description

async def update_prompt(prompt_id: str, name: str = None, content: str = None, ...) -> Prompt

async def activate_prompt(prompt_id: str) -> Prompt
    # Set as active, deactivate others automatically

async def delete_prompt(prompt_id: str)
```

---

### LLM Service (`app/services/llm/llm_service.py`)
**Architecture:** Factory pattern dengan provider abstraction

```python
class BaseLLMProvider(ABC):
    async def generate(self, messages: List[Dict], **kwargs) -> str
        # Non-streaming response

    async def agenerate(self, messages: List[Dict], **kwargs) -> AsyncGenerator[str, None]
        # Streaming response, yields tokens

    def get_provider_name(self) -> str
    def get_model_info(self) -> Dict

class OpenAIProvider(BaseLLMProvider):
    # Uses langchain-openai, supports GPT-4, GPT-4-turbo, GPT-3.5-turbo

class AnthropicProvider(BaseLLMProvider):
    # Uses langchain-anthropic, supports Claude-3 family

class GoogleProvider(BaseLLMProvider):
    # Uses langchain-google-genai, supports Gemini models

class LLMService:
    def get_provider(model_id: str) -> BaseLLMProvider
        # Factory method: creates provider instance based on model config

    async def generate_response(model_id: str, messages: List[Dict]) -> str
        # Convenience method using provider

    async def stream_response(model_id: str, messages: List[Dict]) -> AsyncGenerator
        # Streaming convenience method
```

**Provider Selection Flow:**
1. Get model from database (name, provider type)
2. Initialize corresponding provider with API key from settings
3. Call provider's agenerate() method
4. Yield chunks in real-time to client

---

### RAG Service (`app/services/rag/rag_service.py`)
```python
class RAGService:
    def generate_embedding(text: str) -> List[float]
        # Generate 1536-dim embedding using OpenAI text-embedding-3-small

    def semantic_search(query: str, top_k: int = 5, threshold: float = 0.7) -> List[Dict]
        # 1. Generate embedding for query
        # 2. Perform pgvector cosine similarity search
        # 3. Return top-k chunks with similarity scores (1 - distance)

    def format_rag_context(chunks: List[Dict]) -> str
        # Format chunks as context string for LLM prompt

    def extract_sources(chunks: List[Dict]) -> List[Dict]
        # Extract unique sources (doc_id, page) from chunks

    def health_check() -> Dict
        # Check embeddings client + pgvector availability
```

### RAG Tool Calling (`app/services/rag/tools.py`)
```python
def semantic_search_tool():
    # Langchain Tool that LLM can call during generation
    # Takes: query (str), top_k (int)
    # Returns: {"results": [...], "sources": [...], "count": int}
```

**RAG Pipeline with Tool Calling:**
1. User sends message: "Apa itu loop?"
2. LLM receives message + system prompt + RAG tool definition
3. LLM decides: "Do I need documents to answer this?"
4. If YES → LLM calls `semantic_search` tool with query
5. Tool returns relevant chunks + sources
6. LLM sees search results and generates response
7. Final response includes sources from search results
8. If NO → LLM responds without searching (no sources)

**Key Advantage:** LLM intelligently decides when RAG is needed.
Unlike traditional RAG, document context only when relevant.

---

## 🔐 SECURITY & AUTHENTICATION

### Password Security
```python
# In app/core/security.py
def get_password_hash(password: str) -> str
    # Uses bcrypt (10 rounds) via passlib

def verify_password(plain_password: str, hashed_password: str) -> bool
    # Bcrypt constant-time comparison
```

### JWT Token Management
```python
def create_access_token(data: dict, expires_delta: timedelta = None) -> str
    payload = {
        "sub": user_id,  # subject
        "exp": expiration_time,
        "iat": issued_at_time
    }
    # Encoded with SECRET_KEY using HS256

def decode_access_token(token: str) -> dict
    # Verify signature and expiration
    # Raise HTTPException if invalid
```

### Role-Based Access Control
**In dependencies.py:**
```python
async def get_current_user(token: str) -> User
    # Extract user from JWT, returns User object

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User
    # Verify user.role == "ADMIN"
    # Raise 403 if not admin

async def get_current_student(current_user: User = Depends(get_current_user)) -> User
    # Verify user.role == "STUDENT"
```

**Endpoint Protection:**
- Public: `/health`, `/docs`
- Student: `/auth/register`, `/auth/login`, `/chat/*`, `/files/*`
- Admin: `/prompts/*`, `/users/*`, `/admin`

---

## 📊 DATABASE MIGRATIONS (Alembic)

### Running Migrations
```bash
# Apply all pending migrations to current database
alembic upgrade head

# Create new auto-generated migration
alembic revision --autogenerate -m "Describe changes"

# View migration history
alembic history

# Downgrade to specific revision
alembic downgrade <revision_id>
```

### Migration Files
1. **683738efbac7** - Initial schema (6 tables, pgvector support)
2. **b5ede45b7881** - Model table synchronization
3. **c82c550cf83d** - Add `order` column to model (priority sorting)
4. **e7b67a707145** - Remove `config` and `is_active` from model
5. **f1a2b3c4d5e6** - Add `content` column to document (extracted text)

### Database Setup
```bash
# First time setup
docker-compose up -d  # Starts PostgreSQL, pgAdmin, API
alembic upgrade head  # Apply migrations

# Seed initial data
python -m app.scripts.seed_admin    # Create admin user
python -m app.scripts.seed_models   # Create LLM model registry
```

---

## 🎛️ ADMIN PANEL (SQLAdmin)

**URL:** `http://localhost:8000/admin`

### Available Admin Views
1. **User Admin** - Manage all users, view roles
2. **Model Admin** - View/edit LLM model registry
3. **Prompt Admin** - Manage system prompts
4. **Document Admin** - View uploaded documents
5. **Document Chunk Admin** - View/debug embeddings
6. **Chat Session Admin** - View all chat sessions

### Admin Features
- ✅ Create/read/update/delete for each model
- ✅ Advanced filtering and searching
- ✅ Batch operations
- ✅ Export data to CSV
- ✅ Custom column selection
- ✅ Sort and pagination

---

## ⚙️ CONFIGURATION

### Environment Variables (`.env`)
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/system_llm
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=system_llm

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# File Storage
STORAGE_TYPE=local  # or 'gcs'
GCS_BUCKET_NAME=gs://system-llm-storage

# Application
DEBUG=true  # false in production
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### Pydantic Settings (`app/core/config.py`)
```python
class Settings:
    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # LLM
    OPENAI_API_KEY: str = None
    ANTHROPIC_API_KEY: str = None
    GOOGLE_API_KEY: str = None

    # Storage
    STORAGE_TYPE: str = "local"  # local or gcs
    GCS_BUCKET_NAME: str = None

    # App
    DEBUG: bool = False
    PROJECT_NAME: str = "System LLM"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = []
```

---

## 📝 LOGGING CONFIGURATION

### Setup (`app/core/logging.py`)
- **Console Handler:** Colored logs for development
- **File Handler:** `logs/app.log` (rotating, 10MB max)
- **Error Handler:** `logs/error.log` (errors only)

### Log Format
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Logging Examples
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Chat session created: %s", session_id)
logger.error("Failed to process file: %s", error)
logger.debug("LLM response: %s", response)
```

---

## 🚀 MIDDLEWARE

### Request Logging Middleware
- Logs all incoming requests with method, path, query params
- Logs response status code and processing time
- Adds `X-Process-Time` header to responses

### Error Logging Middleware
- Catches unhandled exceptions
- Logs full traceback
- Returns 500 error response

---

## 📚 SCHEMA DEFINITIONS

### Authentication Schemas (`app/schemas/auth.py`)
```python
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
```

### Chat Schemas (`app/schemas/chat.py`)
```python
class ChatSessionCreate(BaseModel):
    model_id: UUID
    title: str
    prompt_id: Optional[UUID]

class ChatSessionResponse(BaseModel):
    id: UUID
    title: str
    status: str
    total_messages: int

class ChatRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime
    sources: Optional[List[Dict]]
```

### File Schemas (`app/schemas/file.py`)
```python
class FileUploadResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    status: str

class FileDetailResponse(FileUploadResponse):
    content: Optional[str]
```

### Prompt Schemas (`app/schemas/prompt.py`)
```python
class PromptCreate(BaseModel):
    name: str
    content: str
    description: Optional[str]
    is_active: bool = False

class PromptResponse(PromptCreate):
    id: UUID
    created_by: UUID
    created_at: datetime
```

---

## 🎯 KEY DESIGN PATTERNS

### 1. **Dependency Injection**
FastAPI's dependency system for:
- Database session management
- Authentication verification
- Role-based access control

### 2. **Factory Pattern**
LLM service uses factory pattern for provider creation:
```python
def get_provider(model_id: str) -> BaseLLMProvider
    # Returns OpenAIProvider, AnthropicProvider, or GoogleProvider
```

### 3. **Storage Abstraction**
Pluggable file storage implementations:
```python
class FileStorageProvider(ABC):
    # Abstract interface

class LocalFileStorage(FileStorageProvider):
    # Development implementation

class GCSStorageProvider(FileStorageProvider):
    # Production implementation
```

### 4. **Async/Await Pattern**
Full async support for:
- Database queries
- LLM API calls
- File operations
- Streaming responses

### 5. **Server-Sent Events (SSE)**
Streaming LLM responses to client:
```python
@app.post("/chat/sessions/{id}/messages")
async def send_message(id: str, request: ChatRequest):
    async def event_generator():
        async for chunk in llm.stream_response(...):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 🔍 IMPORTANT IMPLEMENTATION DETAILS

### Chat Session Message Flow with RAG Tool Calling
```
1. User sends: POST /chat/sessions/{id}/messages

2. System extracts user message + builds context:
   - Retrieves chat session
   - Gets system prompt from database
   - Builds message history from previous messages

3. Create RAG tools (LLM-callable functions):
   - semantic_search(query: str, top_k: int) → {"results": [...], "sources": [...]}

4. Bind tools to LLM + start agentic loop:

   5a. LLM receives:
       - System prompt
       - Chat history
       - Current user message
       - Available tools (semantic_search)

   5b. LLM decides: "Do I need documents to answer?"
       - If NO → Return response directly (no sources)
       - If YES → Call semantic_search tool with query

   5c. If tool called:
       - Generate embedding for query
       - Search pgvector for relevant chunks
       - Return results to LLM
       - LLM sees search results + generates response

6. Stream response to client as SSE:
   - event: user_message (user input)
   - event: rag_search (optional, if tool called)
   - event: chunk (response text chunks)
   - event: done (final response with sources)

7. Save to database:
   - User message
   - Assistant message with full content
   - Sources (from RAG search if applicable)
```

### Vector Search Implementation
```
1. Query: "Apa itu loop?"
2. Generate embedding: OpenAI text-embedding-3-small(query) → 1536-dim vector
3. PostgreSQL pgvector query (cosine similarity):
   SELECT *
   FROM document_chunk dc
   JOIN document d ON dc.document_id = d.id
   WHERE d.status = 'PROCESSED'
   ORDER BY dc.embedding <=> query_vector DESC
   LIMIT 5
4. Calculate similarity: 1 - distance (range 0-1)
5. Filter by threshold (default 0.7)
6. Return top-k chunks with similarity scores
```

### File Processing Flow
```
1. User uploads PDF file
2. System generates UUID filename
3. Saves to storage (local or GCS)
4. Creates Document record with status=UPLOADED
5. Background job (should be implemented):
   - Extract text from PDF
   - Create document_chunks
   - Generate embeddings for each chunk
   - Store in pgvector
   - Update status to PROCESSED
```

---

## 🔧 USEFUL COMMANDS

### Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Execute command in container
docker exec system-llm-api python -m app.scripts.seed_admin

# Stop services
docker-compose down
```

### Alembic
```bash
# Apply migrations
alembic upgrade head

# Create migration
alembic revision --autogenerate -m "Add column X to table Y"

# View history
alembic history
```

### Testing
```bash
# Run tests
pytest

# With coverage
pytest --cov=app

# Specific test
pytest tests/test_auth.py::test_login
```

### Manual Database Queries
```bash
# Connect to PostgreSQL in Docker
docker exec -it system-llm-db psql -U postgres -d system_llm

# Useful queries
SELECT * FROM "user";
SELECT * FROM chat_session WHERE user_id = 'uuid';
SELECT * FROM document_chunk WHERE document_id = 'uuid' LIMIT 5;
```

---

## 📊 CURRENT IMPLEMENTATION STATUS

### ✅ Completed Stages
- **Stage 1: Design** - Architecture and ERD finalized
- **Stage 2: Setup** - Docker, PostgreSQL, Alembic configured
- **Stage 3: Auth** - JWT authentication with roles implemented
- **Stage 4: LLM Integration** - OpenAI, Anthropic, Google providers ready
- **Stage 5: Chat MVP** - Core chat with streaming and context
- **Stage 6: Prompt Management** - Dynamic system prompts
- **Stage 7: File Management** - PDF upload and storage
- **Stage 8: RAG Pipeline** - Vector embeddings with pgvector
- **Stage 9: Tool Calling** - ✨ NEW! LLM tool calling with semantic search
  - OpenAI & Anthropic providers support tool calling
  - LLM intelligently decides when to search documents
  - Automatic source attribution in responses
  - SSE streaming with `rag_search` events

### 🔄 In Progress / TODO
- **Stage 10: Analytics** - Session analysis and comprehension tracking
- **Stage 11: Frontend UI** - React application with RAG event handling
- **Stage 12: Deployment** - Production deployment

---

## 🎓 RESEARCH & ANALYTICS CAPABILITIES

### Data Available for Analysis
1. **Chat Logs** - Full conversation history with timestamps
2. **User Interactions** - Message frequency, response patterns
3. **Document References** - Which materials students rely on
4. **Session Metrics** - Duration, comprehension level, topic coverage
5. **LLM Performance** - Response quality by model and prompt

### Analysis Opportunities
- Compare effectiveness of different prompts
- Track student comprehension levels
- Identify common learning challenges
- Measure impact of RAG on response quality
- Analyze learning patterns across cohorts

---

## 🔗 IMPORTANT LINKS & REFERENCES

### Documentation
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- pgvector: https://github.com/pgvector/pgvector
- Alembic: https://alembic.sqlalchemy.org/

### LLM Documentation
- OpenAI: https://platform.openai.com/docs/
- Anthropic: https://docs.anthropic.com/
- Google Gemini: https://ai.google.dev/

### Admin Panel
- SQLAdmin: https://aminalaee.dev/sqladmin/

---

## 📞 TROUBLESHOOTING

### Common Issues

**1. Database Connection Failed**
```
Check if PostgreSQL is running
docker-compose ps
docker-compose logs db
```

**2. LLM API Error**
```
Verify API keys in .env file
Check internet connection
Check API rate limits
```

**3. Vector Search Not Working**
```
Verify pgvector extension installed:
  CREATE EXTENSION IF NOT EXISTS vector;
Check document chunks have embeddings
Verify embedding dimensions match
```

**4. File Upload Fails**
```
Check file size limits
Verify storage path permissions
Check disk space
```

---

## 📝 NOTES FOR FUTURE WORK

1. **Async File Processing**: Implement background task queue (Celery/RQ) for:
   - PDF text extraction
   - Chunk generation
   - Embedding calculation
   - Note: Currently handled in notebook; move to production task queue

2. **Caching**: Add Redis for:
   - LLM response caching
   - Session caching
   - Embedding cache (same query = same embedding)

3. **RAG Enhancements**:
   - Implement Hybrid Search (semantic + keyword search)
   - Add document summarization
   - Implement citation/footnote generation
   - Support multi-document reasoning

4. **Rate Limiting**: Per-user/endpoint rate limiting

5. **Monitoring & Observability**:
   - Sentry for error tracking
   - OpenTelemetry for distributed tracing
   - RAG quality metrics dashboard

6. **Performance**:
   - pgvector index optimization (HNSW vs IVFFlat)
   - Batch embedding generation
   - Query optimization for large document collections

7. **Testing**: Unit + integration tests for RAG pipeline

8. **Frontend**:
   - React application with SSE event handling
   - Real-time RAG search visualization
   - Source document viewer

9. **Deployment**: Kubernetes setup with proper scaling

10. **Analytics Dashboard**:
    - RAG retrieval quality metrics
    - Tool calling success rates
    - Document relevance analytics

---

---

## Session 3: Chat Session Prompt Fields Logging

### 3.1 Detailed Logging untuk Chat Session Creation

**Purpose**: Menampilkan semua prompt fields yang diberikan user ketika membuat chat session, agar mudah debug dan monitoring.

**Changes Made**:

#### 1. File: `app/api/v1/endpoints/chat.py` (create_chat_session)
```python
# Log all prompt fields in detail
logger.info("=" * 80)
logger.info("[CREATE_SESSION] PROMPT CONFIGURATION DETAILS:")
logger.info(f"  prompt_general: {request.prompt_general if request.prompt_general else '(not provided)'}")
logger.info(f"  task: {request.task if request.task else '(not provided)'}")
logger.info(f"  persona: {request.persona if request.persona else '(not provided)'}")
logger.info(f"  mission_objective: {request.mission_objective if request.mission_objective else '(not provided)'}")
logger.info("=" * 80)
```

#### 2. File: `app/services/chat/chat_service.py` (create_session)
```python
# Log session creation with all prompt fields
logger.info(f"[SERVICE] Created chat session {session.id} for user {user_id}")
logger.info("[SERVICE] Session Prompt Configuration:")
logger.info(f"  - prompt_id (from Prompt table): {session.prompt_id}")
logger.info(f"  - prompt_general: {session.prompt_general if session.prompt_general else '(not set)'}")
logger.info(f"  - task: {session.task if session.task else '(not set)'}")
logger.info(f"  - persona: {session.persona if session.persona else '(not set)'}")
logger.info(f"  - mission_objective: {session.mission_objective if session.mission_objective else '(not set)'}")
```

#### 3. File: `.env`
Changed `DEBUG=false` to `DEBUG=true` untuk memastikan semua log INFO ditampilkan.

**Logging Output Example**:

Ketika user membuat chat session dengan semua prompt fields:
```
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO - [CREATE_SESSION] Request received from user 660e8400-e29b-41d4-a716-446655440000
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO - [CREATE_SESSION] Request data: model_id=gpt-4.1-nano, title=ML Learning Session, prompt_id=None
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO - ================================================================================
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO - [CREATE_SESSION] PROMPT CONFIGURATION DETAILS:
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO -   prompt_general: You are an expert tutor in machine learning...
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO -   task: Teach the student about neural networks
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO -   persona: Expert ML instructor with 10 years experience
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO -   mission_objective: Student fully understands backpropagation
2025-11-09 20:30:15 - system_llm.app.api.v1.endpoints.chat - INFO - ================================================================================
2025-11-09 20:30:15 - system_llm.app.services.chat.chat_service - INFO - [SERVICE] Created chat session 550e8400-e29b-41d4-a716-446655440000 for user 660e8400-e29b-41d4-a716-446655440000
2025-11-09 20:30:15 - system_llm.app.services.chat.chat_service - INFO - [SERVICE] Session Prompt Configuration:
2025-11-09 20:30:15 - system_llm.app.services.chat.chat_service - INFO -   - prompt_id (from Prompt table): None
2025-11-09 20:30:15 - system_llm.app.services.chat.chat_service - INFO -   - prompt_general: You are an expert tutor in machine learning...
2025-11-09 20:30:15 - system_llm.app.services.chat.chat_service - INFO -   - task: Teach the student about neural networks
2025-11-09 20:30:15 - system_llm.app.services.chat.chat_service - INFO -   - persona: Expert ML instructor with 10 years experience
2025-11-09 20:30:15 - system_llm.app.services.chat.chat_service - INFO -   - mission_objective: Student fully understands backpropagation
```

**How to View Logs**:

1. **Console Output (Real-time)**:
   ```bash
   # Logs akan muncul di terminal/console ketika app berjalan
   docker-compose logs -f backend
   ```

2. **Log Files** (dalam folder `logs/`):
   - `logs/app.log` - Semua logs (INFO, WARNING, ERROR, DEBUG)
   - `logs/error.log` - Hanya ERROR level logs

3. **View specific session**:
   ```bash
   # Cari logs dari session ID tertentu
   grep "550e8400-e29b-41d4-a716-446655440000" logs/app.log
   ```

4. **Format Logging**:
   - Timestamp: `YYYY-MM-DD HH:MM:SS`
   - Logger name: `system_llm.module.name`
   - Level: `DEBUG|INFO|WARNING|ERROR|CRITICAL`
   - Message: Deskripsi log

**Files Modified**:
- `app/api/v1/endpoints/chat.py` - Added detailed prompt logging
- `app/services/chat/chat_service.py` - Added service-level logging
- `.env` - Set `DEBUG=true`

**Testing**:
```bash
# 1. Restart backend application
docker-compose restart backend

# 2. Create chat session via API
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "model_id": "gpt-4.1-nano",
    "title": "Test Session",
    "prompt_general": "You are a helpful assistant",
    "task": "Help with learning",
    "persona": "Expert tutor",
    "mission_objective": "Student understands concepts"
  }'

# 3. Check logs
docker-compose logs backend | grep CREATE_SESSION
# OR
tail -f logs/app.log | grep CREATE_SESSION
```

**Next Session Tasks**:
- Monitor logging for production issues
- Add request/response JSON logging for debugging
- Implement structured logging (JSON format) for log aggregation services

---

**Last Updated:** November 9, 2025
**Maintained By:** System LLM Team
**Version:** 2.2 (Chat Session Prompt Logging)
