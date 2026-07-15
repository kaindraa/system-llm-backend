"""Database-backed ingestion queue helpers.

The document table is a durable queue. Workers claim rows atomically and hold
a renewable lease, so a replacement worker only retries work after the former
worker has actually stopped renewing ownership.
"""

from app.core.logging import get_logger
from app.core.database import SessionLocal
from sqlalchemy import text as sql_text

logger = get_logger(__name__)

def recover_expired_documents() -> dict[str, int]:
    """Return only genuinely abandoned jobs to the queue.

    Jobs with a live lease are never touched. The rollout migration gives
    legacy jobs a one-time grace lease before this worker version starts.
    """
    db = SessionLocal()
    try:
        cancelled = db.execute(
            sql_text("""
                UPDATE document
                   SET status = 'CANCELLED',
                       current_stage = NULL,
                       cancel_requested = false,
                       processing_owner = NULL,
                       lease_expires_at = NULL,
                       last_heartbeat_at = NULL
                 WHERE status = 'PROCESSING'
                   AND cancel_requested = true
                   AND lease_expires_at < now()
            """)
        ).rowcount
        reset = db.execute(
            sql_text("""
                UPDATE document
                   SET status = 'UPLOADED',
                       current_stage = NULL,
                       processing_owner = NULL,
                       lease_expires_at = NULL,
                       last_heartbeat_at = NULL
                 WHERE status = 'PROCESSING'
                   AND (cancel_requested = false OR cancel_requested IS NULL)
                   AND lease_expires_at < now()
            """)
        ).rowcount
        db.commit()
    finally:
        db.close()

    if cancelled or reset:
        logger.info(
            "[runner] recovered expired document leases (reset=%s cancelled=%s)",
            reset,
            cancelled,
        )

    return {
        "reset": reset,
        "cancelled": cancelled,
    }

def claim_next_document(worker_id: str, lease_seconds: int) -> str | None:
    """Atomically claim the oldest queued document for one worker.

    `SKIP LOCKED` lets future worker replicas pull different rows without
    waiting on each other. Expired jobs are recovered separately before this
    function is called, keeping the claim transition intentionally simple.
    """
    db = SessionLocal()
    try:
        row = db.execute(
            sql_text("""
                WITH candidate AS (
                    SELECT id
                      FROM document
                     WHERE status = 'UPLOADED'
                     ORDER BY uploaded_at ASC
                     FOR UPDATE SKIP LOCKED
                     LIMIT 1
                )
                UPDATE document AS d
                   SET status = 'PROCESSING',
                       current_stage = 'queued',
                       cancel_requested = false,
                       last_error = NULL,
                       processing_owner = :worker_id,
                       lease_expires_at = now() + (:lease_seconds * interval '1 second'),
                       last_heartbeat_at = now(),
                       attempt_count = attempt_count + 1
                  FROM candidate
                 WHERE d.id = candidate.id
             RETURNING d.id
            """),
            {"worker_id": worker_id, "lease_seconds": lease_seconds},
        ).first()
        db.commit()
        if not row:
            return None
        return str(row[0])
    finally:
        db.close()


def renew_document_lease(document_id: str, worker_id: str, lease_seconds: int) -> bool:
    """Extend a lease only when this worker still owns the document."""
    db = SessionLocal()
    try:
        result = db.execute(
            sql_text("""
                UPDATE document
                   SET lease_expires_at = now() + (:lease_seconds * interval '1 second'),
                       last_heartbeat_at = now()
                 WHERE id = :document_id
                   AND status = 'PROCESSING'
                   AND processing_owner = :worker_id
            """),
            {
                "document_id": document_id,
                "worker_id": worker_id,
                "lease_seconds": lease_seconds,
            },
        )
        db.commit()
        return result.rowcount == 1
    finally:
        db.close()


def cancel_document(document_id: str) -> bool:
    """Atomically cancel an owned job without waiting for a parser checkpoint.

    A worker may be inside a slow native PDF extraction call. Clearing its
    ownership makes every later checkpoint fail closed with IngestionLeaseLost,
    so it cannot write chunks or overwrite this final cancellation state.
    """
    db = SessionLocal()
    try:
        result = db.execute(
            sql_text("""
                UPDATE document
                   SET status = 'CANCELLED',
                       current_stage = NULL,
                       cancel_requested = false,
                       processing_owner = NULL,
                       lease_expires_at = NULL,
                       last_heartbeat_at = NULL
                 WHERE id = :document_id
                   AND status = 'PROCESSING'
            """),
            {"document_id": document_id},
        )
        if result.rowcount != 1:
            db.rollback()
            return False

        # A cancelled re-ingest must never leave stale partial chunks behind.
        db.execute(
            sql_text("DELETE FROM document_chunk WHERE document_id = :document_id"),
            {"document_id": document_id},
        )
        db.commit()
        return True
    finally:
        db.close()
