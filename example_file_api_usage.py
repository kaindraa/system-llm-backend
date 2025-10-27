"""
Example: File Management API Usage

Script ini mendemonstrasikan cara menggunakan File Management API.
Jalankan dengan: python example_file_api_usage.py

Prerequisites:
1. Backend sudah running: python -m uvicorn app.main:app --reload
2. Pastikan ada user yang sudah registered
"""

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "student@example.com"  # Change to your test user
PASSWORD = "password123"

# Global variables to store token dan file_id
jwt_token = None
file_id = None


def log_step(step_num: int, description: str):
    """Log step execution"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*60}")


def log_result(status: str, data: dict = None, error: str = None):
    """Log result"""
    if status == "success":
        print(f"✅ SUCCESS")
        if data:
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
    else:
        print(f"❌ FAILED")
        if error:
            print(f"Error: {error}")


def step_1_register_user():
    """Step 1: Register user (skip if already exists)"""
    global jwt_token

    log_step(1, "Register User (if needed)")

    payload = {
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": "Test Student",
        "role": "student"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=payload
        )

        if response.status_code in [201, 400]:  # 400 = already exists (ok)
            print(f"✅ User registration done (status: {response.status_code})")
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def step_2_login():
    """Step 2: Login and get JWT token"""
    global jwt_token

    log_step(2, "Login and Get JWT Token")

    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            jwt_token = data.get("access_token")
            log_result("success", data=data)
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def get_headers():
    """Get headers with JWT token"""
    return {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }


def step_3_upload_file():
    """Step 3: Upload PDF file"""
    global file_id

    log_step(3, "Upload PDF File")

    # Create sample PDF file
    pdf_path = Path("sample.pdf")

    if not pdf_path.exists():
        # Create minimal PDF file for testing
        pdf_content = b"%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\nxref\n0 2\n0000000000 65535 f\n0000000010 00000 n\ntrailer\n<</Size 2 /Root 1 0 R>>\nstartxref\n73\n%%EOF"
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f"Created sample PDF file: {pdf_path}")

    try:
        with open(pdf_path, 'rb') as f:
            files = {"file": (pdf_path.name, f, "application/pdf")}
            response = requests.post(
                f"{BASE_URL}/files/upload",
                files=files,
                headers={"Authorization": f"Bearer {jwt_token}"}
            )

        if response.status_code == 201:
            data = response.json()
            file_id = data.get("id")
            log_result("success", data=data)
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False
    finally:
        # Cleanup
        if pdf_path.exists():
            pdf_path.unlink()


def step_4_list_files():
    """Step 4: List all files"""
    log_step(4, "List All Files")

    try:
        response = requests.get(
            f"{BASE_URL}/files",
            headers=get_headers(),
            params={
                "skip": 0,
                "limit": 10
            }
        )

        if response.status_code == 200:
            data = response.json()
            log_result("success", data=data)
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def step_5_get_file_detail():
    """Step 5: Get file detail"""
    log_step(5, "Get File Detail")

    if not file_id:
        print("❌ No file_id available (upload file first)")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/files/{file_id}",
            headers=get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            log_result("success", data=data)
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def step_6_update_file_status():
    """Step 6: Update file status to 'processing'"""
    log_step(6, "Update File Status to 'processing'")

    if not file_id:
        print("❌ No file_id available (upload file first)")
        return False

    payload = {"status": "processing"}

    try:
        response = requests.patch(
            f"{BASE_URL}/files/{file_id}/status",
            json=payload,
            headers=get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            log_result("success", data=data)
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def step_7_update_file_status_processed():
    """Step 7: Update file status to 'processed'"""
    log_step(7, "Update File Status to 'processed'")

    if not file_id:
        print("❌ No file_id available (upload file first)")
        return False

    payload = {"status": "processed"}

    try:
        response = requests.patch(
            f"{BASE_URL}/files/{file_id}/status",
            json=payload,
            headers=get_headers()
        )

        if response.status_code == 200:
            data = response.json()
            log_result("success", data=data)
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def step_8_download_file():
    """Step 8: Download file"""
    log_step(8, "Download File")

    if not file_id:
        print("❌ No file_id available (upload file first)")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/files/{file_id}/download",
            headers={"Authorization": f"Bearer {jwt_token}"}
        )

        if response.status_code == 200:
            # Save downloaded file
            output_path = Path("downloaded.pdf")
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ File downloaded successfully")
            print(f"File size: {len(response.content)} bytes")
            print(f"Saved to: {output_path}")
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def step_9_delete_file():
    """Step 9: Delete file"""
    log_step(9, "Delete File")

    if not file_id:
        print("❌ No file_id available (upload file first)")
        return False

    try:
        response = requests.delete(
            f"{BASE_URL}/files/{file_id}",
            headers=get_headers()
        )

        if response.status_code == 204:
            print(f"✅ File deleted successfully (status: {response.status_code})")
            return True
        else:
            log_result("failed", error=response.text)
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def step_10_verify_deletion():
    """Step 10: Verify file was deleted"""
    log_step(10, "Verify File Was Deleted")

    if not file_id:
        print("❌ No file_id available")
        return False

    try:
        response = requests.get(
            f"{BASE_URL}/files/{file_id}",
            headers=get_headers()
        )

        if response.status_code == 404:
            print(f"✅ File not found (as expected after deletion)")
            return True
        else:
            log_result("failed", error="File still exists!")
            return False

    except Exception as e:
        log_result("failed", error=str(e))
        return False


def main():
    """Run all steps"""
    print("\n" + "="*60)
    print("FILE MANAGEMENT API - TEST SUITE")
    print("="*60)

    steps = [
        ("Register User", step_1_register_user),
        ("Login", step_2_login),
        ("Upload File", step_3_upload_file),
        ("List Files", step_4_list_files),
        ("Get File Detail", step_5_get_file_detail),
        ("Update Status to Processing", step_6_update_file_status),
        ("Update Status to Processed", step_7_update_file_status_processed),
        ("Download File", step_8_download_file),
        ("Delete File", step_9_delete_file),
        ("Verify Deletion", step_10_verify_deletion),
    ]

    results = []

    for i, (description, step_func) in enumerate(steps, 1):
        try:
            success = step_func()
            results.append((description, success))

            if not success:
                print(f"\n⚠️  Stopping test suite due to failure")
                break

        except KeyboardInterrupt:
            print(f"\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            results.append((description, False))
            break

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")

    print(f"\nTotal: {passed}/{total} passed")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
