#!/usr/bin/env python3
"""
Test script untuk GCS integration

Usage:
    python test_gcs_integration.py --mode=test-credentials
    python test_gcs_integration.py --mode=test-storage
    python test_gcs_integration.py --mode=test-upload
"""

import argparse
import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.file_service import GCSStorageProvider, LocalFileStorage, initialize_storage_provider


def test_credentials():
    """Test GCS credentials file accessibility"""
    print("\n=== Testing GCS Credentials ===")

    if not settings.GCS_CREDENTIALS_PATH:
        print("❌ GCS_CREDENTIALS_PATH not configured")
        return False

    creds_path = settings.GCS_CREDENTIALS_PATH
    print(f"Checking credentials at: {creds_path}")

    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return False

    print(f"✅ Credentials file found")

    try:
        with open(creds_path, 'r') as f:
            import json
            creds_json = json.load(f)

            required_fields = ['type', 'project_id', 'private_key_id', 'private_key']
            missing_fields = [f for f in required_fields if f not in creds_json]

            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False

            print(f"✅ Valid GCP service account JSON")
            print(f"  Project ID: {creds_json.get('project_id')}")
            print(f"  Service Account: {creds_json.get('client_email')}")
            return True

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in credentials file: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials: {str(e)}")
        return False


def test_gcs_connection():
    """Test GCS bucket connection"""
    print("\n=== Testing GCS Connection ===")

    if not settings.GCS_BUCKET_NAME:
        print("❌ GCS_BUCKET_NAME not configured")
        return False

    try:
        provider = GCSStorageProvider(
            bucket_name=settings.GCS_BUCKET_NAME,
            credentials_path=settings.GCS_CREDENTIALS_PATH,
            project_id=settings.GCS_PROJECT_ID
        )
        print(f"✅ Connected to GCS bucket: {settings.GCS_BUCKET_NAME}")
        print(f"✅ GCS Provider initialized successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to connect to GCS: {str(e)}")
        return False


def test_storage_operations():
    """Test basic storage operations"""
    print("\n=== Testing Storage Operations ===")

    if settings.STORAGE_TYPE.lower() != "gcs":
        print("⚠️  STORAGE_TYPE is not 'gcs', using local storage for test")
        provider = LocalFileStorage()
    else:
        try:
            provider = GCSStorageProvider(
                bucket_name=settings.GCS_BUCKET_NAME,
                credentials_path=settings.GCS_CREDENTIALS_PATH,
                project_id=settings.GCS_PROJECT_ID
            )
        except Exception as e:
            print(f"❌ Failed to initialize GCS provider: {str(e)}")
            return False

    test_file_id = "test-gcs-integration-12345"
    test_content = b"This is a test file for GCS integration"

    try:
        # Test SAVE
        print(f"\nTesting SAVE operation...")
        saved_path = provider.save(test_file_id, test_content)
        print(f"✅ File saved successfully")
        print(f"  Path: {saved_path}")

        # Test EXISTS
        print(f"\nTesting EXISTS operation...")
        exists = provider.exists(test_file_id)
        if exists:
            print(f"✅ File exists check passed")
        else:
            print(f"❌ File should exist but doesn't")
            return False

        # Test GET
        print(f"\nTesting GET operation...")
        retrieved_content = provider.get(test_file_id)
        if retrieved_content == test_content:
            print(f"✅ File retrieved successfully with matching content")
        else:
            print(f"❌ Retrieved content doesn't match original")
            return False

        # Test DELETE
        print(f"\nTesting DELETE operation...")
        provider.delete(test_file_id)

        # Verify deletion
        if not provider.exists(test_file_id):
            print(f"✅ File deleted successfully")
        else:
            print(f"❌ File should be deleted but still exists")
            return False

        return True

    except Exception as e:
        print(f"❌ Storage operation failed: {str(e)}")
        return False


def test_initialize_provider():
    """Test provider initialization based on config"""
    print("\n=== Testing Provider Initialization ===")

    try:
        provider = initialize_storage_provider(settings)

        storage_type = settings.STORAGE_TYPE.lower()
        print(f"✅ Storage provider initialized")
        print(f"  Type: {storage_type}")
        print(f"  Class: {provider.__class__.__name__}")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize storage provider: {str(e)}")
        return False


def main():
    """Run selected tests"""
    parser = argparse.ArgumentParser(description="Test GCS integration")
    parser.add_argument(
        "--mode",
        choices=["test-credentials", "test-connection", "test-storage", "test-init", "all"],
        default="all",
        help="Test mode to run"
    )

    args = parser.parse_args()

    print(f"\n{'='*50}")
    print(f"GCS Integration Test Suite")
    print(f"{'='*50}")
    print(f"\nConfiguration:")
    print(f"  STORAGE_TYPE: {settings.STORAGE_TYPE}")
    print(f"  GCS_BUCKET_NAME: {settings.GCS_BUCKET_NAME}")
    print(f"  GCS_PROJECT_ID: {settings.GCS_PROJECT_ID}")
    print(f"  GCS_CREDENTIALS_PATH: {settings.GCS_CREDENTIALS_PATH}")

    results = {}

    if args.mode in ["test-credentials", "all"]:
        results["credentials"] = test_credentials()

    if args.mode in ["test-connection", "all"]:
        results["connection"] = test_gcs_connection()

    if args.mode in ["test-storage", "all"]:
        results["storage"] = test_storage_operations()

    if args.mode in ["test-init", "all"]:
        results["initialization"] = test_initialize_provider()

    # Summary
    print(f"\n{'='*50}")
    print(f"Test Summary")
    print(f"{'='*50}")

    if results:
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:20} {status}")

        all_passed = all(results.values())
        print(f"\n{'Overall':<20} {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

        return 0 if all_passed else 1
    else:
        print("No tests executed")
        return 2


if __name__ == "__main__":
    sys.exit(main())
