# RAG Implementation with Tool Calling - Quick Reference

**Date:** November 8, 2025
**Status:** ✅ Complete and Ready to Test

---

## 🎯 What Was Implemented

### 1. **RAG Service** (`app/services/rag/`)
- `rag_service.py` - Core RAG functionality
  - `generate_embedding(text)` - OpenAI text-embedding-3-small (1536 dims)
  - `semantic_search(query, top_k, threshold)` - pgvector cosine similarity
  - `extract_sources(chunks)` - Source metadata extraction
  - `health_check()` - System health monitoring

### 2. **Langchain Tool Definition** (`app/services/rag/tools.py`)
- `semantic_search_tool()` - Callable tool for LLM
- `RAGToolFactory` - Tool creation with proper descriptions
- Tool automatically integrated into LLM context

### 3. **LLM Tool Calling Support**
**Modified providers:**
- `openai_provider.py` - `agenerate_stream_with_tools()`
- `anthropic_provider.py` - `agenerate_stream_with_tools()`
- `base.py` - Abstract method definition

**Features:**
- Agentic loop: LLM → tool call → result → response
- Max iterations protection (default 10)
- Proper error handling
- Full async/await support

### 4. **Chat Service Integration** (`app/services/chat/chat_service.py`)
- Updated `send_message_stream()` with RAG support
- Parameter: `use_rag=True` (default)
- **LLM decides** whether to call semantic_search tool
- Automatic source extraction and inclusion

### 5. **API Endpoints** (`app/api/v1/endpoints/rag.py`)
- `GET /rag/health` - Health check
- `GET /rag/config` - RAG configuration
- `POST /rag/search` - Direct search (for testing)

### 6. **Chat Endpoint Updates**
- Added RAG event handling: `event: rag_search`
- SSE streaming with RAG context visibility
- Sources included in final response

---

## 🔄 Request/Response Flow

```
User Query
    ↓
[ChatService.send_message_stream]
    ↓
Create RAG Tools + Bind to LLM
    ↓
LLM receives: system_prompt + history + user_msg + tools
    ↓
LLM decides: "Do I need documents?"
    ├─ NO  → Skip to Response
    └─ YES → Call semantic_search tool
         ↓
      [RAGService.semantic_search]
      - Generate embedding
      - Query pgvector
      - Return results + sources
         ↓
      LLM sees results → Generate response
    ↓
Stream to Client:
- event: user_message
- event: rag_search (optional)
- event: chunk (tokens)
- event: done (final + sources)
    ↓
Save to DB:
- User message
- Assistant message + content + sources
```

---

## 📊 Event Stream Format

### RAG Search Event
```json
{
  "type": "rag_search",
  "content": {
    "query": "what is a loop?",
    "status": "searching"  // or "completed"
  }
}
```

When completed:
```json
{
  "type": "rag_search",
  "content": {
    "query": "what is a loop?",
    "results_count": 3,
    "status": "completed"
  }
}
```

### Done Event (with Sources)
```json
{
  "type": "done",
  "content": {
    "role": "assistant",
    "content": "A loop is a control structure...",
    "sources": [
      {
        "document_id": "uuid",
        "filename": "python-basics.pdf",
        "page": 5,
        "similarity_score": 0.92
      }
    ],
    "created_at": "2025-11-08T..."
  }
}
```

---

## 🚀 Testing the Implementation

### 1. Check RAG Health
```bash
curl http://localhost:8000/api/v1/rag/health
```

### 2. Direct Search Test
```bash
curl -X POST "http://localhost:8000/api/v1/rag/search?query=NAT" \
  -H "Authorization: Bearer {token}"
```

### 3. Chat with RAG
```bash
# Create session
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "gpt-4-turbo", "title": "RAG Test"}'

# Send message (streaming)
curl -N -X POST http://localhost:8000/api/v1/chat/sessions/{session_id}/messages \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"message": "Apa itu NAT?"}' | grep "event:"
```

---

## 📁 Files Created/Modified

### Created
- ✨ `app/services/rag/rag_service.py` (270 lines)
- ✨ `app/services/rag/tools.py` (140 lines)
- ✨ `app/services/rag/__init__.py`
- ✨ `app/api/v1/endpoints/rag.py` (150 lines)

### Modified
- 📝 `app/services/llm/base.py` - Added `agenerate_stream_with_tools()`
- 📝 `app/services/llm/openai_provider.py` - Tool calling implementation (130 lines added)
- 📝 `app/services/llm/anthropic_provider.py` - Tool calling implementation (130 lines added)
- 📝 `app/services/llm/llm_service.py` - Added `stream_response_with_tools()`
- 📝 `app/services/chat/chat_service.py` - RAG integration (150 lines modified)
- 📝 `app/api/v1/endpoints/chat.py` - RAG event handling
- 📝 `app/main.py` - Register RAG router
- 📝 `CLAUDE.md` - Comprehensive documentation

**Total:** 1000+ lines of code

---

## 🎓 Key Architecture Decisions

### 1. **Tool Calling vs Direct RAG**
- ✅ Tool calling: LLM intelligently decides when to search
- ❌ Direct RAG: Always search (wasteful, increases latency)

### 2. **Langchain Integration**
- Used Langchain `Tool` for standardized interface
- Provider-native tool calling (OpenAI/Anthropic native support)
- Clean abstraction for future providers (Google, local models, etc.)

### 3. **Global Document Scope**
- All documents searchable by all users
- No per-user filtering (design choice for learning system)
- Easy to modify if per-user RAG is needed

### 4. **Sources in Response**
- Stored in chat message JSONB
- Returned in done event
- Frontend can display document sources

### 5. **Embedding Model**
- OpenAI text-embedding-3-small
- 1536 dimensions (cost-effective, good quality)
- Same model used for query + chunks
- pgvector cosine similarity: 1 - distance

---

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=sk-...          # Required for embeddings + tool-capable models
ANTHROPIC_API_KEY=sk-ant-...   # Optional (for Claude models)
```

### Default Settings
- RAG: **Enabled by default** in chat
- Top-K: **5 documents**
- Similarity threshold: **0.7** (tool calling), **0.65** (direct search)
- Max tool iterations: **10**

---

## 📈 Performance Notes

### Latency
- Embedding generation: ~200-300ms (OpenAI API)
- Vector search: ~10-50ms (pgvector with index)
- Tool call decision: ~500ms (LLM decision)
- **Total RAG overhead**: ~700ms-1s per query

### Optimization Opportunities
1. Cache embeddings for repeated queries
2. Add pgvector index (HNSW for large datasets)
3. Batch embedding requests
4. Implement semantic cache

---

## 🧪 Next Steps

1. **Test with Real Data**
   - Use `ingest_docs_for_rag.ipynb` to add test documents
   - Send various queries to test LLM tool calling
   - Verify sources are correct

2. **Frontend Integration**
   - Handle `rag_search` events in UI
   - Show search progress/results to user
   - Display source documents

3. **Production Deployment**
   - Set up pgvector indexes
   - Configure embedding cache (Redis)
   - Monitor tool calling success rates

4. **Analytics**
   - Track when LLM uses RAG vs not
   - Measure retrieval quality
   - Identify edge cases

---

## 📚 Documentation Links

- **Main:** `CLAUDE.md` - Complete system documentation
- **Chat:** Lines 514-563 - Chat with RAG example
- **RAG Endpoints:** Lines 808-901 - All RAG endpoints
- **Implementation Details:** Lines 1456-1512 - Technical flows

---

**Created by:** Claude Code Assistant
**Last Updated:** November 8, 2025
