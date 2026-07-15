"""Exercise durable document-queue behaviour against a real PostgreSQL DB.

Run inside the local API container after migrations:
    python scripts/verify_ingestion_queue.py

It does not call an LLM or touch object storage. Test rows are cleaned up when
the script finishes.
"""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from sqlalchemy import text as sql_text

from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
from app.models.user import User, UserRole
from app.services.rag.ingestion_runner import (
    claim_next_document,
    recover_expired_documents,
    renew_document_lease,
)


def _document(user_id, suffix: str) -> Document:
    return Document(
        user_id=user_id,
        filename=f"queue-test-{suffix}",
        original_filename=f"queue-test-{suffix}.pdf",
        file_path=f"queue-test-{suffix}",
        file_size=1,
        mime_type="application/pdf",
        status=DocumentStatus.UPLOADED,
    )


def main() -> None:
    suffix = uuid4().hex
    user_id = None
    document_ids: list[str] = []

    try:
        db = SessionLocal()
        try:
            user = User(
                email=f"queue-test-{suffix}@example.invalid",
                password_hash="not-used",
                full_name="Queue Test",
                role=UserRole.ADMIN,
            )
            db.add(user)
            db.flush()
            user_id = user.id

            first = _document(user.id, f"{suffix}-one")
            second = _document(user.id, f"{suffix}-two")
            db.add_all([first, second])
            db.commit()
            document_ids = [str(first.id), str(second.id)]
        finally:
            db.close()

        # Two independent worker sessions must claim distinct pending rows.
        with ThreadPoolExecutor(max_workers=2) as executor:
            claimed = list(
                executor.map(
                    lambda worker: claim_next_document(worker, lease_seconds=60),
                    ["queue-test-worker-a", "queue-test-worker-b"],
                )
            )
        assert None not in claimed, "both workers should receive a job"
        assert len(set(claimed)) == 2, "one document was claimed twice"
        assert set(claimed) == set(document_ids), "unexpected document claimed"

        claims = dict(zip(["queue-test-worker-a", "queue-test-worker-b"], claimed))
        assert renew_document_lease(
            claims["queue-test-worker-a"],
            "queue-test-worker-a",
            60,
        ), "current owner should renew its own lease"
        assert not renew_document_lease(claimed[0], "wrong-worker", 60), "wrong owner renewed a lease"

        db = SessionLocal()
        try:
            # Simulate a hard crash: lease expires and the job is requeued.
            db.execute(
                sql_text("""
                    UPDATE document
                       SET lease_expires_at = now() - interval '1 second'
                     WHERE id = :id
                """),
                {"id": claimed[0]},
            )
            # Simulate a cancel request that outlives a crashed worker.
            db.execute(
                sql_text("""
                    UPDATE document
                       SET lease_expires_at = now() - interval '1 second',
                           cancel_requested = true
                     WHERE id = :id
                """),
                {"id": claimed[1]},
            )
            db.commit()
        finally:
            db.close()

        recovered = recover_expired_documents()
        assert recovered == {"reset": 1, "cancelled": 1}, recovered

        db = SessionLocal()
        try:
            rows = db.execute(
                sql_text("""
                    SELECT id, status, processing_owner, lease_expires_at
                      FROM document
                     WHERE id = ANY(CAST(:ids AS uuid[]))
                """),
                {"ids": document_ids},
            ).fetchall()
        finally:
            db.close()

        status_by_id = {str(row[0]): row for row in rows}
        assert status_by_id[claimed[0]][1] == "UPLOADED"
        assert status_by_id[claimed[1]][1] == "CANCELLED"
        assert all(row[2] is None and row[3] is None for row in rows)
        print("PASS: durable ingestion queue claim, lease recovery, and cancellation")
    finally:
        if user_id is not None:
            db = SessionLocal()
            try:
                db.execute(
                    sql_text("DELETE FROM document WHERE user_id = :user_id"),
                    {"user_id": str(user_id)},
                )
                db.execute(
                    sql_text("DELETE FROM \"user\" WHERE id = :user_id"),
                    {"user_id": str(user_id)},
                )
                db.commit()
            finally:
                db.close()


if __name__ == "__main__":
    main()
