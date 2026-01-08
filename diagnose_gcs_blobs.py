#!/usr/bin/env python3
"""
Diagnostic script to check GCS blobs and their sizes
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google.cloud import storage as gcs_storage
from google.oauth2 import service_account

# Load environment variables
load_dotenv(Path(".env"))

# Configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH")
GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID")

if not GCS_BUCKET_NAME:
    raise ValueError("GCS_BUCKET_NAME not set in .env")

print("=" * 80)
print("GCS BLOB DIAGNOSTIC")
print("=" * 80)
print(f"Bucket: {GCS_BUCKET_NAME}")
print(f"Credentials: {GCS_CREDENTIALS_PATH}")
print(f"Project: {GCS_PROJECT_ID}\n")

# Initialize GCS client
try:
    if GCS_CREDENTIALS_PATH and os.path.exists(GCS_CREDENTIALS_PATH):
        credentials = service_account.Credentials.from_service_account_file(GCS_CREDENTIALS_PATH)
        client = gcs_storage.Client(credentials=credentials, project=GCS_PROJECT_ID or credentials.project_id)
        print("✅ Using service account credentials\n")
    else:
        client = gcs_storage.Client(project=GCS_PROJECT_ID)
        print("✅ Using default application credentials\n")
except Exception as e:
    print(f"❌ Failed to initialize GCS client: {e}")
    sys.exit(1)

bucket = client.bucket(GCS_BUCKET_NAME)

# List blobs in uploads/ folder
print("=" * 80)
print("Listing blobs in gs://{}/{}/uploads/".format(GCS_BUCKET_NAME, ""))
print("=" * 80 + "\n")

try:
    blobs = list(bucket.list_blobs(prefix="uploads/", max_results=100))
    print(f"Found {len(blobs)} blob(s) in uploads/ folder:\n")

    total_size = 0
    empty_blobs = []

    for i, blob in enumerate(blobs, 1):
        blob_size = blob.size if blob.size else "Unknown"
        time_created = blob.time_created.isoformat() if blob.time_created else "Unknown"

        # Flag empty blobs
        is_empty = blob.size == 0 if blob.size else False
        empty_flag = " ⚠️  EMPTY!" if is_empty else ""

        print(f"[{i}] {blob.name}")
        print(f"    Size: {blob_size:,} bytes{empty_flag}")
        print(f"    Created: {time_created}")
        print(f"    Content-Type: {blob.content_type}")
        print()

        if is_empty:
            empty_blobs.append(blob.name)

        if isinstance(blob_size, int):
            total_size += blob_size

    print("=" * 80)
    print(f"SUMMARY")
    print("=" * 80)
    print(f"Total blobs: {len(blobs)}")
    print(f"Empty blobs: {len(empty_blobs)}")
    if empty_blobs:
        print(f"\nEmpty blob paths:")
        for blob_name in empty_blobs:
            print(f"  - {blob_name}")
    print(f"Total size: {total_size:,} bytes ({total_size / (1024*1024):.2f} MB)")
    print()

    # Test downloading one non-empty blob
    if blobs:
        test_blob = None
        for blob in blobs:
            if blob.size and blob.size > 0:
                test_blob = blob
                break

        if test_blob:
            print("=" * 80)
            print(f"TEST DOWNLOAD")
            print("=" * 80)
            print(f"Testing download of: {test_blob.name} ({test_blob.size} bytes)\n")

            try:
                content = test_blob.download_as_bytes()
                print(f"✅ Download successful!")
                print(f"   Downloaded size: {len(content)} bytes")
                print(f"   Expected size:   {test_blob.size} bytes")
                print(f"   Match: {len(content) == test_blob.size}\n")

                # Check if content looks like PDF
                if content[:4] == b'%PDF':
                    print(f"✅ Content looks like PDF (starts with %PDF)")
                else:
                    print(f"⚠️  Content doesn't look like PDF (first 4 bytes: {content[:4]})")

            except Exception as e:
                print(f"❌ Download failed: {e}\n")
        else:
            print("❌ No non-empty blobs found to test\n")

except Exception as e:
    print(f"❌ Error listing blobs: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
