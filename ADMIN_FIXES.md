# Admin Panel Fixes - System LLM Backend

## Overview

Fixed 3 major issues in the admin panel:
1. **User Creation** - NULL value in `password_hash`
2. **Prompt Creation** - NULL value in `created_by`
3. **Document Chunk Detail View** - Internal Server Error (500)

---

## Issue 1: User Creation - NULL password_hash

### Problem
When creating a STUDENT user via admin panel, got error:
```
(psycopg2.errors.NotNullViolation) null value in column "password_hash" of relation "user" violates not-null constraint
```

### Root Cause
- Column `password_hash` was excluded from admin form
- Admin couldn't input password, resulting in NULL value
- Database constraint requires password_hash to be NOT NULL

### Solution
Modified `UserAdmin` class in `app/admin/views.py`:

```python
# CHANGE 1: Remove password_hash from form_excluded_columns
form_excluded_columns = [User.created_at, User.updated_at, User.chat_sessions]
# (was: [User.password_hash, User.created_at, User.updated_at, User.chat_sessions])

# CHANGE 2: Add form_args for password field configuration
form_args = {
    "password_hash": {
        "label": "Password",
        "validators": [DataRequired()],
        "description": "Enter password for the user",
    },
}

# CHANGE 3: Add on_model_change hook to auto-hash password
async def on_model_change(self, data: dict, model: User, is_create: bool, request) -> None:
    """Handle password hashing before saving user."""
    if "password_hash" in data and data["password_hash"]:
        password = data["password_hash"]
        # Check if password is not already hashed (bcrypt format: $2a$, $2b$, $2y$)
        if not (password.startswith("$2a$") or password.startswith("$2b$") or password.startswith("$2y$")):
            # Hash password using bcrypt
            data["password_hash"] = get_password_hash(password)
    elif is_create:
        raise ValueError("Password is required when creating a new user")
```

### How It Works
1. Admin enters plaintext password in the form
2. `on_model_change()` hook is called before saving
3. Password is hashed using bcrypt (same as registration endpoint)
4. Hashed password is stored in database
5. Prevents double-hashing by checking bcrypt prefix

### Testing
```
Admin Panel > Users > Create User
- Email: student@example.com
- Full Name: John Doe
- Password: (NEW FIELD) your_password_123
- Role: student
```

---

## Issue 2: Prompt Creation - NULL created_by

### Problem
When creating a Prompt via admin panel, got error:
```
(psycopg2.errors.NotNullViolation) null value in column "created_by" of relation "prompt" violates not-null constraint
```

### Root Cause
- Column `created_by` is a required FK to User table
- Admin form didn't have mechanism to auto-set current user
- Form didn't exclude `created_by`, but also didn't require input
- Result: NULL value saved to database

### Solution
Modified `PromptAdmin` class in `app/admin/views.py`:

```python
# CHANGE 1: Exclude created_by from form
form_excluded_columns = [Prompt.created_at, Prompt.updated_at, Prompt.created_by]
# (was: [Prompt.created_at, Prompt.updated_at])

# CHANGE 2: Add on_model_change hook to auto-set created_by
async def on_model_change(self, data: dict, model: Prompt, is_create: bool, request) -> None:
    """Handle auto-setting created_by to current admin user before saving."""
    if is_create:
        # Get current admin user ID from session
        user_id = request.session.get("user_id")
        if user_id:
            # Convert user_id string to UUID
            data["created_by"] = UUID(user_id)
        else:
            # Fallback: raise error if no user_id in session
            raise ValueError("Cannot create prompt: No authenticated user found in session")
```

### How It Works
1. Admin user logs in, session stores `user_id`
2. When creating Prompt, admin doesn't see `created_by` field
3. `on_model_change()` hook gets user_id from session
4. Automatically sets `created_by` to current admin user
5. Prompt is created with correct creator attribution

### Testing
```
Admin Panel > Prompts > Create Prompt
- Name: "My Prompt"
- Content: "system prompt content..."
- Description: "Description"
- Active: true/false
(NOTE: created_by field is NOT shown - auto-set to current admin)
```

---

## Issue 3: Document Chunk Detail View - 500 Error

### Problem
When clicking a document chunk row to view details, got **Internal Server Error (500)**

### Root Cause
SQLAdmin has limitations with complex database types:
1. **Vector type** (pgvector) - Can't serialize 1536-dimensional vectors
2. **JSONB type** - Difficulty rendering complex JSON structures in admin interface

### Solution
Modified `DocumentChunkAdmin` class in `app/admin/views.py`:

```python
# CHANGE 1: Exclude embedding from detail view (already done)
column_details_exclude_list = [DocumentChunk.embedding, DocumentChunk.chunk_metadata, DocumentChunk.created_at]

# CHANGE 2: Exclude JSONB chunk_metadata from form and detail
form_excluded_columns = [DocumentChunk.created_at, DocumentChunk.embedding, DocumentChunk.chunk_metadata]

# CHANGE 3: Add type formatters for Vector type
column_type_formatters = {
    Vector: lambda m: "[Vector Embedding - Hidden for Performance]"
}

# CHANGE 4: Add model form converters to skip Vector in form conversion
model_form_converters = {
    Vector: None  # Skip Vector type in form conversion
}
```

### Also Fixed ChatSessionAdmin
Same issue affected ChatSessionAdmin with 3 JSONB message fields:

```python
# Exclude all JSONB message fields from detail view and form
column_details_exclude_list = [
    ChatSession.messages,
    ChatSession.interaction_messages,
    ChatSession.real_messages,
    ChatSession.started_at,
    ChatSession.ended_at,
    ChatSession.analyzed_at
]

form_excluded_columns = [
    ChatSession.started_at,
    ChatSession.ended_at,
    ChatSession.analyzed_at,
    ChatSession.messages,
    ChatSession.interaction_messages,
    ChatSession.real_messages
]
```

### How It Works
1. Vector/JSONB fields are excluded from detail view rendering
2. SQLAdmin doesn't try to serialize these complex types
3. Admin can still view other data (ID, Document ID, Chunk Index, Content, Page Number)
4. Backend still accesses these fields normally for API operations
5. Data is not deleted, just hidden from admin interface

### Testing
```
Admin Panel > Document Chunks > Click any row to view detail
(Should open without 500 error, showing: ID, Document, Chunk Index, Content, Page Number)
```

---

## Files Modified

### app/admin/views.py
- **UserAdmin class** (lines 16-76):
  - Added password field with validation
  - Added `on_model_change()` to hash passwords

- **PromptAdmin class** (lines 114-162):
  - Excluded `created_by` from form
  - Added `on_model_change()` to auto-set `created_by`

- **DocumentChunkAdmin class** (lines 210-263):
  - Added `column_details_exclude_list`
  - Added `column_type_formatters` for Vector type
  - Added `model_form_converters` to skip Vector in forms

- **ChatSessionAdmin class** (lines 266-320):
  - Added `column_details_exclude_list`
  - Excluded JSONB message fields from form

### New Imports
```python
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Length, Optional
from uuid import UUID
from pgvector.sqlalchemy import Vector
```

---

## Testing Document Chunk Admin Errors

If you still encounter 500 errors with document chunks, run the test script:

```bash
cd c:\Users\pcgsa\Downloads\system-llm\system-llm-backend
python test_document_chunk_admin.py
```

This will:
1. Test database connection
2. Verify document_chunk table exists
3. List all columns and their types
4. Load sample document chunks
5. Show any errors with full traceback

The error output will help identify the specific field causing issues.

---

## API vs Admin Panel

**Important Note:** These fixes only affect the **Admin Panel UI**. The actual data and API functionality are unaffected:

| Operation | Accessible Via |
|-----------|-----------------|
| Create User with Password | API `/api/v1/auth/register` & Admin Panel |
| Create Prompt | API `/api/v1/prompts` & Admin Panel |
| View Document Chunks | API `/api/v1/rag/chunks` & Admin Panel |

All API endpoints work independently of these admin UI fixes.

---

## Summary of Changes

| Issue | Fix Type | Location |
|-------|----------|----------|
| User password NULL | Add form field + password hashing hook | UserAdmin |
| Prompt created_by NULL | Exclude from form + auto-set hook | PromptAdmin |
| Document Chunk 500 error | Exclude Vector/JSONB + type formatters | DocumentChunkAdmin |
| Chat Session 500 error | Exclude JSONB message fields | ChatSessionAdmin |

All fixes follow SQLAdmin best practices for handling complex/unsupported types.
