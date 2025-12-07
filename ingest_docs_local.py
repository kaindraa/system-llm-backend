#!/usr/bin/env python3
"""
🚀 RAG Document Ingestion for LOCAL Development
Pipeline: PDF (local storage) → Text → Chunks → Embeddings → PostgreSQL
All database queries via subprocess (docker-compose exec) - No SQLAlchemy connection issues
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import pdfplumber
import io
import re
import numpy as np
from openai import OpenAI

# ============================================================================
# 1️⃣ SETUP - Database Connection & Storage
# ============================================================================

def execute_sql(query: str, fetch: bool = False):
    """Execute SQL query via Docker PostgreSQL"""
    cmd = [
        "docker-compose", "-f", "docker-compose.local.yml", "exec",
        "postgres", "psql", "-U", "llm_user", "-d", "system_llm",
        "-t", "-c", query
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd="."
    )

    if result.returncode != 0:
        error_msg = result.stderr if result.stderr else "Unknown error"
        raise Exception(f"SQL Error: {error_msg}")

    output = result.stdout.strip() if result.stdout else ""
    return output if fetch else output

# Test connection
print("📌 Testing Docker PostgreSQL connection...\n")
try:
    db_version = execute_sql("SELECT version();", fetch=True)
    print(f"✅ Connected to database")
    print(f"✅ PostgreSQL: {db_version.split(',')[0]}\n")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Setup LOCAL file storage
class LocalFileStorage:
    def __init__(self, base_path="storage/uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get(self, file_id: str) -> bytes:
        path = self.base_path / f"{file_id}.pdf"
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return path.read_bytes()

storage = LocalFileStorage()
print(f"✅ Local storage: {storage.base_path.absolute()}")
print(f"✅ Files available: {len(list(storage.base_path.glob('*.pdf')))}\n")

# ============================================================================
# 2️⃣ GET DOCUMENTS FROM DATABASE
# ============================================================================

print("📚 Available documents in database:\n")

sql_query = "SELECT id, original_filename, filename, file_size, status FROM document ORDER BY uploaded_at DESC;"
doc_list = []
result_text = execute_sql(sql_query, fetch=True)

if result_text and result_text.strip():
    for line in result_text.split('\n'):
        if line.strip():
            parts = line.split('|')
            if len(parts) >= 5:
                doc_id = parts[0].strip()
                original_filename = parts[1].strip()
                storage_filename = parts[2].strip().replace('.pdf', '')
                file_size = parts[3].strip()
                status = parts[4].strip()

                doc_list.append({
                    "id": doc_id,
                    "storage_filename": storage_filename,
                    "original_filename": original_filename,
                    "file_size": file_size,
                    "status": status
                })

                print(f"  {original_filename}")
                print(f"    Status: {status} | Size: {file_size} bytes")
                print(f"    ID: {doc_id}\n")

if not doc_list:
    print("  ⚠️  No documents found.\n")
    sys.exit(0)
else:
    print(f"✅ Total: {len(doc_list)} document(s) found\n")

# ============================================================================
# 3️⃣ SELECT DOCUMENTS TO INGEST
# ============================================================================

# CHANGE THIS: Select which documents to process
doc_indices = [1]  # Process first document - CHANGE THIS

selected_documents = []
print(f"📋 Selected documents to ingest:\n")
for idx, doc in enumerate(doc_list, 1):
    if idx in doc_indices:
        selected_documents.append(doc)
        print(f"  ✅ [{idx}] {doc['original_filename']}")

if not selected_documents:
    print("❌ No documents selected\n")
    sys.exit(0)

print(f"\n✅ Total: {len(selected_documents)} document(s) selected\n")

# ============================================================================
# 4️⃣ EXTRACT TEXT FROM PDF
# ============================================================================

def extract_text_from_pdf(pdf_bytes: bytes) -> dict:
    """Extract text from PDF with page tracking"""
    pages_text = {}
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    extracted = page.extract_text()
                    if extracted:
                        extracted = extracted.encode('utf-8', errors='replace').decode('utf-8')
                        if extracted.strip():
                            pages_text[page_num] = extracted
                except Exception as e:
                    print(f"  ⚠️  Warning: Could not extract page {page_num}: {e}")
    except Exception as e:
        print(f"❌ Error opening PDF: {e}")
        raise
    return pages_text

# Extract text
extracted_texts = {}
print(f"📄 Extracting text from {len(selected_documents)} document(s)...\n")

for doc in selected_documents:
    try:
        pdf_bytes = storage.get(doc["storage_filename"])
        pages_text = extract_text_from_pdf(pdf_bytes)

        if pages_text:
            extracted_texts[doc["id"]] = pages_text
            total_chars = sum(len(t) for t in pages_text.values())
            print(f"  ✅ {doc['original_filename']}")
            print(f"     Pages: {len(pages_text)}, Characters: {total_chars:,}\n")
    except Exception as e:
        print(f"  ❌ {doc['original_filename']}: {e}\n")

if not extracted_texts:
    print("❌ No documents extracted successfully\n")
    sys.exit(0)

print(f"✅ Extracted {len(extracted_texts)} document(s)\n")

# ============================================================================
# 5️⃣ CHUNK TEXT
# ============================================================================

def chunk_text_with_pages(pages_text: Dict[int, str], chunk_size: int = 500, overlap: int = 50) -> List[Tuple[str, int]]:
    """Chunk text while tracking page numbers"""
    chunks_with_pages = []

    for page_num in sorted(pages_text.keys()):
        page_content = pages_text[page_num]
        sentences = re.split(r'(?<=[.!?])\s+', page_content)

        current_chunk = []
        current_size = 0

        for sentence in sentences:
            words = sentence.split()
            if not words:
                continue

            if current_size + len(words) > chunk_size and current_chunk:
                chunk_content = ' '.join(current_chunk)
                chunks_with_pages.append((chunk_content, page_num))
                current_chunk = current_chunk[-max(1, int(len(current_chunk) * 0.1)):]
                current_size = len(' '.join(current_chunk).split())

            current_chunk.extend(words)
            current_size += len(words)

        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunks_with_pages.append((chunk_content, page_num))

    return chunks_with_pages

# Create chunks
chunks_by_document = {}
print(f"📦 Creating chunks for {len(extracted_texts)} document(s)...\n")

for doc_id, pages_text in extracted_texts.items():
    chunks_with_pages = chunk_text_with_pages(pages_text, chunk_size=500, overlap=50)
    chunks_by_document[doc_id] = chunks_with_pages

    doc = next(d for d in selected_documents if d["id"] == doc_id)
    print(f"  ✅ {doc['original_filename']}: {len(chunks_with_pages)} chunks\n")

total_chunks = sum(len(c) for c in chunks_by_document.values())
print(f"✅ Total chunks created: {total_chunks}\n")

# ============================================================================
# 6️⃣ SETUP OPENAI EMBEDDINGS
# ============================================================================

OPENAI_API_KEY = "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"
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY not set")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_embedding(text: str) -> List[float]:
    """Generate 1536-dimensional embedding"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

print("✅ OpenAI embedding function loaded (1536 dimensions)")

# Test embedding
first_doc_id = list(chunks_by_document.keys())[0]
first_chunk = chunks_by_document[first_doc_id][0][0]

print("\n🧪 Testing embedding generation...")
embedding = generate_embedding(first_chunk)
print(f"  ✅ Embedding generated: {len(embedding)} dimensions")
print(f"  First 5 values: {embedding[:5]}\n")

# ============================================================================
# 🚀 INGEST - INSERT CHUNKS INTO DATABASE
# ============================================================================

# Clean up old embeddings
print("🧹 Cleaning up old embeddings...\n")
print("=" * 80)

for doc in selected_documents:
    doc_id = doc["id"]
    execute_sql(f"DELETE FROM document_chunk WHERE document_id = '{doc_id}';")
    execute_sql(f"UPDATE document SET status = 'UPLOADED', processed_at = NULL WHERE id = '{doc_id}';")

print(f"✅ Cleaned {len(selected_documents)} document(s)")
print("=" * 80)

# Insert chunks
print("\n" + "=" * 80)
print("🚀 STARTING INGESTION PIPELINE")
print("=" * 80 + "\n")

for doc_id, chunks in chunks_by_document.items():
    doc = next(d for d in selected_documents if d["id"] == doc_id)
    print(f"📄 Processing: {doc['original_filename']}")

    # Set status to PROCESSING
    execute_sql(f"UPDATE document SET status = 'PROCESSING' WHERE id = '{doc_id}';")

    print(f"  Inserting {len(chunks)} chunks...")

    for idx, (chunk_content, page_number) in enumerate(chunks):
        # Generate embedding
        embedding = generate_embedding(chunk_content)
        embedding_json = json.dumps(embedding)

        # Escape quotes for SQL
        safe_content = chunk_content.replace("'", "''")
        safe_embedding = embedding_json.replace("'", "''")

        # Insert chunk
        insert_query = f"""INSERT INTO document_chunk
        (id, document_id, chunk_index, content, page_number, embedding, chunk_metadata, created_at)
        VALUES
        (gen_random_uuid(), '{doc_id}', {idx}, '{safe_content}', {page_number}, '{safe_embedding}', '{{}}'::jsonb, now());"""

        execute_sql(insert_query)

        if (idx + 1) % 5 == 0:
            print(f"    ✓ {idx + 1}/{len(chunks)}")

    # Mark as PROCESSED
    now_str = datetime.utcnow().isoformat()
    execute_sql(f"UPDATE document SET status = 'PROCESSED', processed_at = '{now_str}' WHERE id = '{doc_id}';")
    print(f"  ✅ Document marked as PROCESSED\n")

print("=" * 80)
print("✅ INGESTION COMPLETE!")
print("=" * 80)

# ============================================================================
# 7️⃣ VERIFY RESULTS
# ============================================================================

print("\n✅ VERIFICATION - Database Contents\n")
print("=" * 80)

# Total chunks
count_result = execute_sql("SELECT COUNT(*) as total FROM document_chunk;", fetch=True).strip()
total_chunks = int(count_result) if count_result else 0
print(f"Total chunks in database: {total_chunks:,}\n")

# Document status
status_query = """SELECT d.original_filename, d.status, COUNT(dc.id)
                 FROM document d LEFT JOIN document_chunk dc ON d.id = dc.document_id
                 GROUP BY d.id, d.original_filename, d.status ORDER BY d.uploaded_at DESC;"""
result_text = execute_sql(status_query, fetch=True)

print("Document Status:")
if result_text and result_text.strip():
    for line in result_text.split('\n'):
        if line.strip() and '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                filename = parts[0].strip()
                status = parts[1].strip()
                chunk_count = parts[2].strip()
                print(f"  • {filename}")
                print(f"    Status: {status}, Chunks: {chunk_count}\n")

# Sample embedding
embed_result = execute_sql("SELECT embedding FROM document_chunk LIMIT 1;", fetch=True).strip()
if embed_result:
    embedding_data = json.loads(embed_result)
    print(f"Sample Embedding:")
    print(f"  Dimensions: {len(embedding_data)}")
    print(f"  First 5 values: {embedding_data[:5]}")
    print(f"  ✅ Correct!" if len(embedding_data) == 1536 else f"  ❌ Wrong dimensions")

print("\n" + "=" * 80)

# ============================================================================
# 8️⃣ TEST SEMANTIC SEARCH
# ============================================================================

def semantic_search_local(query_text: str, top_k: int = 5) -> list:
    """Semantic search using cosine similarity"""
    # Generate query embedding
    query_embedding = np.array(generate_embedding(query_text))

    # Get chunks
    search_query = """SELECT dc.content, d.original_filename, dc.page_number, dc.embedding
                      FROM document_chunk dc JOIN document d ON dc.document_id = d.id
                      WHERE d.status = 'PROCESSED' LIMIT 100;"""
    result_text = execute_sql(search_query, fetch=True)

    similarities = []
    if result_text and result_text.strip():
        lines = result_text.split('\n')
        for line in lines:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    content = parts[0].strip()
                    filename = parts[1].strip()
                    page_num = int(parts[2].strip())
                    embedding_json = parts[3].strip()

                    try:
                        chunk_embedding = np.array(json.loads(embedding_json))
                        similarity = np.dot(query_embedding, chunk_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                        )
                        similarities.append((content, filename, page_num, float(similarity)))
                    except:
                        pass

    similarities.sort(key=lambda x: x[3], reverse=True)
    return [{
        "content": content,
        "filename": filename,
        "page": page_num,
        "similarity": similarity
    } for content, filename, page_num, similarity in similarities[:top_k]]

print("\n🎯 Testing Semantic Search\n")
print("=" * 80)

QUERY = "machine learning"  # CHANGE THIS

print(f"Query: \"{QUERY}\"\n")
results = semantic_search_local(QUERY, top_k=5)

if results:
    print(f"Found {len(results)} relevant chunks:\n")
    for i, result in enumerate(results, 1):
        print(f"  [{i}] 📄 {result['filename']}")
        print(f"      📍 Page {result['page']}")
        print(f"      ⭐ Similarity: {result['similarity']:.4f}")
        print(f"      📝 {result['content'][:150]}...\n")
else:
    print("❌ No results found")

print("=" * 80)
print("\n✅ Script completed successfully!\n")
