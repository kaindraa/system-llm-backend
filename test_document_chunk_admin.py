#!/usr/bin/env python3
"""
Test script to debug document chunk admin view issues
Run this to see actual error messages when loading document chunks
"""

import sys
import traceback
from app.core.database import SessionLocal, engine
from app.models.document_chunk import DocumentChunk
from sqlalchemy import inspect

def test_document_chunk_loading():
    """Test loading document chunks from database"""
    print("=" * 80)
    print("Testing Document Chunk Loading")
    print("=" * 80)

    try:
        db = SessionLocal()

        # Check database connection
        print("\n1. Testing database connection...")
        try:
            result = db.execute("SELECT 1")
            print("✓ Database connection OK")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

        # Check if document_chunk table exists
        print("\n2. Checking if document_chunk table exists...")
        try:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if 'document_chunk' in tables:
                print("✓ document_chunk table exists")
            else:
                print(f"✗ document_chunk table not found. Available tables: {tables}")
                return False
        except Exception as e:
            print(f"✗ Error checking tables: {e}")
            return False

        # Check document chunk columns
        print("\n3. Checking document_chunk columns...")
        try:
            inspector = inspect(engine)
            columns = inspector.get_columns('document_chunk')
            print(f"   Found {len(columns)} columns:")
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
        except Exception as e:
            print(f"✗ Error checking columns: {e}")
            traceback.print_exc()
            return False

        # Try to load document chunks
        print("\n4. Trying to load document chunks...")
        try:
            chunks = db.query(DocumentChunk).limit(1).all()
            print(f"✓ Successfully loaded {len(chunks)} document chunk(s)")

            if chunks:
                chunk = chunks[0]
                print(f"\n   Sample chunk:")
                print(f"   - ID: {chunk.id}")
                print(f"   - Document ID: {chunk.document_id}")
                print(f"   - Chunk Index: {chunk.chunk_index}")
                print(f"   - Content length: {len(chunk.content) if chunk.content else 0}")
                print(f"   - Page Number: {chunk.page_number}")
                print(f"   - Has Metadata: {chunk.chunk_metadata is not None}")
                print(f"   - Has Embedding: {chunk.embedding is not None}")
        except Exception as e:
            print(f"✗ Error loading document chunks: {e}")
            traceback.print_exc()
            return False
        finally:
            db.close()

        print("\n" + "=" * 80)
        print("All tests passed! Document chunks are accessible.")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_document_chunk_loading()
    sys.exit(0 if success else 1)
