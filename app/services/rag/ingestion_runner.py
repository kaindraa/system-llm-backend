"""Database-backed ingestion queue helpers.

The web process never runs heavy ingestion work. Instead, web requests mark
documents as `UPLOADED`, and a dedicated worker process polls the database for
pending jobs. This keeps user-facing HTTP traffic isolated from PDF parsing and
embedding workloads.
"""

from app.core.logging import get_logger
from app.core.database import SessionLocal
from sqlalchemy import text as sql_text

logger = get_logger(__name__)

def requeue_orphans(reenqueue: bool = False) -> dict[str, int]:
    """
    Recover documents stuck in PROCESSING (left by a crash/deploy).

    - If cancellation had already been requested, mark the document CANCELLED.
    - Otherwise reset it back to UPLOADED.
    - Re-enqueueing is no longer needed because the worker polls `UPLOADED`
      documents directly from the database.

    Returns a small summary dict. Call at startup.
    """
    db = SessionLocal()
    try:
        rows = db.execute(
            sql_text("""
                SELECT id, cancel_requested
                  FROM document
                 WHERE status = 'PROCESSING'
            """)
        ).fetchall()
        cancelled_ids = [str(row[0]) for row in rows if bool(row[1])]
        reset_ids = [str(row[0]) for row in rows if not bool(row[1])]

        if cancelled_ids:
            db.execute(
                sql_text("""
                    UPDATE document
                       SET status = 'CANCELLED',
                           current_stage = NULL,
                           cancel_requested = false
                     WHERE status = 'PROCESSING'
                       AND cancel_requested = true
                """)
            )
        if reset_ids:
            db.execute(
                sql_text("""
                    UPDATE document
                       SET status = 'UPLOADED',
                           current_stage = NULL
                     WHERE status = 'PROCESSING'
                       AND (cancel_requested = false OR cancel_requested IS NULL)
                """)
            )
        if cancelled_ids or reset_ids:
            db.commit()
    finally:
        db.close()

    requeued = 0
    if reenqueue:
        requeued = len(reset_ids)

    if cancelled_ids or reset_ids:
        logger.info(
            "[runner] recovered orphaned documents after startup "
            "(reset=%s cancelled=%s requeued=%s)",
            len(reset_ids),
            len(cancelled_ids),
            requeued,
        )

    return {
        "reset": len(reset_ids),
        "cancelled": len(cancelled_ids),
        "requeued": requeued,
    }

def get_next_pending_document_id() -> str | None:
    """Return the oldest pending document id, or None if the queue is empty."""
    db = SessionLocal()
    try:
        row = db.execute(
            sql_text("""
                SELECT id
                  FROM document
                 WHERE status = 'UPLOADED'
                 ORDER BY uploaded_at ASC
                 LIMIT 1
            """)
        ).first()
        if not row:
            return None
        return str(row[0])
    finally:
        db.close()
