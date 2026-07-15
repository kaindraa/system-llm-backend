"""Verify the admin cancel and process controls against the local HTTP API.

Run inside the local API container while the worker is stopped:
    python scripts/verify_ingestion_controls.py

The script creates and removes its own admin and documents. It verifies the
same endpoints used by the frontend, then confirms a queued document can be
claimed by a worker.
"""

import json
from urllib.request import Request, urlopen
from uuid import uuid4

from jose import jwt
from sqlalchemy import text as sql_text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.user import User, UserRole
from app.services.rag.ingestion_runner import claim_next_document


API_ROOT = "http://localhost:8000/api/v1"


def _post(path: str, token: str) -> dict:
    request = Request(
        f"{API_ROOT}{path}",
        data=b"",
        method="POST",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urlopen(request, timeout=10) as response:
        assert response.status == 200, response.status
        return json.loads(response.read())


def _document(user_id, suffix: str, status: DocumentStatus) -> Document:
    return Document(
        user_id=user_id,
        filename=f"control-test-{suffix}",
        original_filename=f"control-test-{suffix}.pdf",
        file_path=f"control-test-{suffix}",
        file_size=1,
        mime_type="application/pdf",
        status=status,
        processing_owner="control-test-worker" if status == DocumentStatus.PROCESSING else None,
    )


def main() -> None:
    suffix = uuid4().hex
    user_id = None
    document_ids: list[str] = []

    try:
        db = SessionLocal()
        try:
            user = User(
                email=f"control-test-{suffix}@example.invalid",
                password_hash="not-used",
                full_name="Control Test",
                role=UserRole.ADMIN,
            )
            db.add(user)
            db.flush()
            user_id = user.id

            cancelling = _document(user.id, f"{suffix}-cancel", DocumentStatus.PROCESSING)
            queued = _document(user.id, f"{suffix}-process", DocumentStatus.CANCELLED)
            db.add_all([cancelling, queued])
            db.commit()
            document_ids = [str(cancelling.id), str(queued.id)]
        finally:
            db.close()

        token = jwt.encode(
            {"user_id": str(user_id)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        cancelled = _post(f"/files/{document_ids[0]}/cancel", token)
        assert cancelled["status"].lower() == "cancelled", cancelled
        assert cancelled["current_stage"] is None, cancelled

        requeued = _post(f"/files/{document_ids[1]}/ingest", token)
        assert requeued["status"].lower() == "uploaded", requeued
        assert requeued["current_stage"] is None, requeued

        claimed = claim_next_document("control-test-worker", lease_seconds=60)
        assert claimed == document_ids[1], (claimed, document_ids[1])
        print("PASS: admin cancel is immediate and process queues a claimable document")
    finally:
        if user_id is not None:
            db = SessionLocal()
            try:
                db.execute(
                    sql_text("DELETE FROM document WHERE user_id = :user_id"),
                    {"user_id": str(user_id)},
                )
                db.execute(
                    sql_text('DELETE FROM "user" WHERE id = :user_id'),
                    {"user_id": str(user_id)},
                )
                db.commit()
            finally:
                db.close()


if __name__ == "__main__":
    main()
