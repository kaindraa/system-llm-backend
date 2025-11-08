# Tool Calling Testing Guide

**Last Updated:** November 8, 2025
**Status:** ✅ Ready to Test

---

## 🚀 Quick Start

### Prerequisites
1. ✅ Documents ingested (from `ingest_docs_for_rag.ipynb`)
2. ✅ Database running with pgvector
3. ✅ API server running on `localhost:8000`
4. ✅ Auth token from registered user
5. ✅ LLM API keys in `.env` (OPENAI_API_KEY at minimum)

### Already Have Data?
Check if documents exist:
```bash
curl http://localhost:8000/api/v1/rag/health
```

If `total_documents: 0`, run the notebook first to ingest test documents.

---

## 📊 Step 1: Health Check

Verify RAG system is healthy:

```bash
curl http://localhost:8000/api/v1/rag/health
```

**Expected Response:**
```json
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

**If not healthy:**
- ❌ `embeddings.available: false` → Check `OPENAI_API_KEY`
- ❌ `pgvector.available: false` → Check database connection
- ❌ `total_documents: 0` → Run `ingest_docs_for_rag.ipynb`

---

## 🔐 Step 2: Get Auth Token

Register or login to get token:

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# Or Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Save token:**
```bash
export TOKEN="eyJhbGc..."
```

---

## 🔍 Step 3: Test Direct Search (Optional)

Test RAG search before tool calling:

```bash
curl -X POST "http://localhost:8000/api/v1/rag/search?query=what%20is%20NAT&top_k=3" \
  -H "Authorization: Bearer $TOKEN"
```

**Response should show:**
- ✅ Documents found
- ✅ Similarity scores > 0.65
- ✅ Relevant content chunks

---

## 💬 Step 4: Create Chat Session

Create session for tool calling test:

```bash
curl -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-4-turbo",
    "title": "Tool Calling Test"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "...",
  "model_id": "...",
  "title": "Tool Calling Test",
  "status": "ACTIVE",
  "total_messages": 0,
  "started_at": "2025-11-08T..."
}
```

**Save session ID:**
```bash
export SESSION_ID="550e8400-e29b-41d4-a716-446655440000"
```

---

## 🤖 Step 5: Send Message with Tool Calling

Send query that might trigger RAG:

```bash
curl -N -X POST \
  "http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Apa itu NAT dan OSPF?"}' | head -50
```

**Expected Event Stream:**

```
event: user_message
data: {"role":"user","content":"Apa itu NAT dan OSPF?","created_at":"2025-11-08T...","sources":null}

event: rag_search
data: {"query":"NAT OSPF definition","status":"searching"}

event: rag_search
data: {"query":"NAT OSPF definition","results_count":3,"status":"completed"}

event: chunk
data: {"content":"NAT "}

event: chunk
data: {"content":"(Network Address"}

event: chunk
data: {"content":" Translation)"}

...more chunks...

event: done
data: {"role":"assistant","content":"NAT (Network Address Translation) adalah...[full response]...","sources":[{"document_id":"...","filename":"H03 - NAT & OSPF.pdf","page":5,"similarity_score":0.92}],"created_at":"2025-11-08T..."}
```

---

## 🔍 What to Look For

### ✅ SUCCESS Indicators

1. **RAG Search Triggered:**
   - ✅ `event: rag_search` appears with `status: searching`
   - ✅ Followed by `status: completed` with `results_count > 0`

2. **Proper Response:**
   - ✅ Multiple `event: chunk` events with text
   - ✅ Final `event: done` with complete response

3. **Sources Included:**
   - ✅ `sources` array in done event
   - ✅ Contains `document_id`, `filename`, `page`, `similarity_score`

4. **Relevant Content:**
   - ✅ Response mentions documents/sources
   - ✅ Page numbers match indexed documents

### ❌ Issues to Debug

| Problem | Cause | Solution |
|---------|-------|----------|
| No `rag_search` events | LLM didn't decide to search | Try more document-specific query |
| `rag_search` but `count: 0` | No relevant documents found | Check documents are indexed (health check) |
| Empty response | Tool call failed | Check server logs for errors |
| `sources: null` | RAG didn't trigger | Send query requiring document context |
| Streaming stops | Connection issue | Check network/firewall |

---

## 📝 Test Scenarios

### Scenario 1: Query Needs Documents
**Query:** "Apa itu NAT?"
**Expected:** ✅ RAG search triggered
**Why:** Specific technical term in documents

```bash
curl -N -X POST "http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Apa itu NAT?"}'
```

### Scenario 2: Query Without Documents
**Query:** "Berapa 2 + 2?"
**Expected:** ❓ Depends on LLM - might skip RAG
**Why:** Math question, documents probably irrelevant

```bash
curl -N -X POST "http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Berapa 2 + 2?"}'
```

### Scenario 3: Multiple Documents
**Query:** "Jelaskan perbedaan NAT dan routing protocol OSPF"
**Expected:** ✅ RAG search finds multiple docs
**Why:** Complex query requiring document synthesis

```bash
curl -N -X POST "http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Jelaskan perbedaan NAT dan routing protocol OSPF"}'
```

---

## 🔧 Troubleshooting

### Issue: "Tool not found"
```
event: error
data: {"error":"Tool 'semantic_search' not found"}
```

**Solution:**
- Restart API server
- Check RAG module imported correctly
- Verify `create_rag_tools()` returns tools

### Issue: "Embeddings API error"
```json
{"error":"Failed to generate embedding: ..."}
```

**Solution:**
- Verify `OPENAI_API_KEY` in `.env`
- Check OpenAI account has credits
- Check API key is valid (test with `/rag/search`)

### Issue: "pgvector error"
```json
{"error":"Vector search failed: ..."}
```

**Solution:**
- Verify `ingest_docs_for_rag.ipynb` completed successfully
- Check database has documents: `SELECT COUNT(*) FROM document_chunk`
- Verify pgvector extension installed

### Issue: Streaming stops mid-response
**Solution:**
- Check server logs: `docker-compose logs api`
- Try shorter query
- Check LLM API limits
- Restart server and try again

---

## 📊 Full Integration Test

Complete test flow:

```bash
#!/bin/bash

# 1. Check health
echo "1. Checking RAG health..."
curl http://localhost:8000/api/v1/rag/health | jq .

# 2. Register user
echo -e "\n2. Registering user..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}' | jq -r .access_token)
echo "Token: $TOKEN"

# 3. Create session
echo -e "\n3. Creating chat session..."
SESSION=$(curl -s -X POST http://localhost:8000/api/v1/chat/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model_id":"gpt-4-turbo","title":"Test"}' | jq -r .id)
echo "Session: $SESSION"

# 4. Send message with tool calling
echo -e "\n4. Sending message with tool calling..."
curl -N -X POST "http://localhost:8000/api/v1/chat/sessions/$SESSION/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Apa itu NAT?"}'
```

Save as `test_rag.sh` and run:
```bash
chmod +x test_rag.sh
./test_rag.sh
```

---

## 📈 Performance Metrics

Expected timing:
- **Health check:** <100ms
- **Authentication:** 200-500ms
- **Create session:** 100-200ms
- **RAG search:** 700-1500ms (includes embedding generation)
- **LLM response:** 3-10s depending on response length

Total end-to-end: **3-15 seconds** with RAG

---

## ✅ Success Checklist

- [ ] Health check returns `status: healthy`
- [ ] Auth token obtained successfully
- [ ] Chat session created
- [ ] Message sent without errors
- [ ] `rag_search` events appear in stream
- [ ] Response chunks received
- [ ] Final response includes sources
- [ ] Sources match indexed documents
- [ ] Document pages are correct

---

## 📚 Next Steps

Once tool calling works:

1. **Monitor Logs**
   - Check `logs/app.log` for detailed flow
   - Look for "Tool called" messages
   - Verify embeddings are generated

2. **Test Edge Cases**
   - Very long queries
   - Non-English text
   - Queries with special characters
   - Rapid successive messages

3. **Measure Quality**
   - How often does LLM trigger RAG?
   - Are retrieved documents relevant?
   - Source accuracy

4. **Optimize**
   - Add caching for repeated queries
   - Adjust similarity threshold
   - Tweak chunk size in ingestion

---

## 🆘 Getting Help

**Check logs:**
```bash
docker-compose logs api | tail -100
```

**Test RAG directly:**
```bash
curl -X POST "http://localhost:8000/api/v1/rag/search?query=test&top_k=3" \
  -H "Authorization: Bearer $TOKEN"
```

**Verify documents:**
```bash
# In database
SELECT COUNT(*) as chunk_count FROM document_chunk;
SELECT DISTINCT original_filename FROM document;
```

---

**Selamat testing! 🚀**
