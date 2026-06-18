"""
Ingestion Runner — background execution for the document ingestion pipeline.

Responsibilities:
  - Serial execution: a single worker thread drains a queue, so only ONE
    document is parsed/embedded at a time (keeps RAM low on the 1GB machine).
  - Keep-alive: while there is work in flight, a heartbeat thread pings the
    app's own public URL so Fly's scale-to-zero proxy keeps the machine up
    ("still running -> still alive"). When the queue drains, pinging stops and
    the machine may scale to zero again. No-op when not running on Fly.
  - Crash recovery: `requeue_orphans()` (called at startup) re-queues any
    document left mid-flight (status PROCESSING) by a previous crash/deploy.

This is intentionally infra-free (no Redis). The `document` table's status
column is the source of truth; this runner is just the in-process dispatcher.
"""

import os
import queue
import threading
import urllib.request

from app.core.logging import get_logger
from app.core.database import SessionLocal
from sqlalchemy import text as sql_text
from app.services.rag.ingestion_service import ingestion_service

logger = get_logger(__name__)

# Job queue + single worker
_job_queue: "queue.Queue[str]" = queue.Queue()
_worker_thread: threading.Thread | None = None
_worker_lock = threading.Lock()

# Heartbeat state
_inflight = 0
_inflight_lock = threading.Lock()
_heartbeat_thread: threading.Thread | None = None
_heartbeat_stop = threading.Event()

HEARTBEAT_INTERVAL_SECONDS = 20


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def enqueue(document_id: str) -> None:
    """Queue a document for ingestion and ensure the worker is running."""
    _ensure_worker()
    with _inflight_lock:
        global _inflight
        _inflight += 1
        _ensure_heartbeat()
    _job_queue.put(str(document_id))
    logger.info(f"[runner] enqueued {document_id} (queue size ~{_job_queue.qsize()})")


def requeue_orphans() -> int:
    """
    Reset documents stuck in PROCESSING (left by a crash/deploy) back to
    UPLOADED and re-enqueue them. Returns count requeued. Call at startup.
    """
    db = SessionLocal()
    try:
        rows = db.execute(
            sql_text("SELECT id FROM document WHERE status = 'PROCESSING'")
        ).fetchall()
        ids = [str(r[0]) for r in rows]
        if ids:
            db.execute(
                sql_text("""UPDATE document
                               SET status = 'UPLOADED', current_stage = NULL
                             WHERE status = 'PROCESSING'""")
            )
            db.commit()
    finally:
        db.close()

    for doc_id in ids:
        enqueue(doc_id)
    if ids:
        logger.info(f"[runner] requeued {len(ids)} orphaned document(s) after startup")
    return len(ids)


# --------------------------------------------------------------------------- #
# Worker
# --------------------------------------------------------------------------- #
def _ensure_worker() -> None:
    global _worker_thread
    with _worker_lock:
        if _worker_thread is None or not _worker_thread.is_alive():
            _worker_thread = threading.Thread(
                target=_worker_loop, name="ingestion-worker", daemon=True
            )
            _worker_thread.start()
            logger.info("[runner] worker thread started")


def _worker_loop() -> None:
    while True:
        document_id = _job_queue.get()  # blocks until work arrives
        try:
            ingestion_service.ingest_document(document_id)
        except Exception as e:  # ingest_document already records failures; this is a backstop
            logger.error(f"[runner] unexpected error ingesting {document_id}: {e}", exc_info=True)
        finally:
            _job_queue.task_done()
            with _inflight_lock:
                global _inflight
                _inflight = max(0, _inflight - 1)


# --------------------------------------------------------------------------- #
# Heartbeat (keep machine alive while busy)
# --------------------------------------------------------------------------- #
def _self_url() -> str | None:
    explicit = os.getenv("APP_PUBLIC_URL")
    if explicit:
        return explicit.rstrip("/") + "/health"
    fly_app = os.getenv("FLY_APP_NAME")
    if fly_app:
        return f"https://{fly_app}.fly.dev/health"
    return None  # local / non-Fly -> no heartbeat needed


def _ensure_heartbeat() -> None:
    global _heartbeat_thread
    if _heartbeat_thread is not None and _heartbeat_thread.is_alive():
        return
    url = _self_url()
    if not url:
        return  # nothing to keep alive (local dev)
    _heartbeat_stop.clear()
    _heartbeat_thread = threading.Thread(
        target=_heartbeat_loop, args=(url,), name="ingestion-heartbeat", daemon=True
    )
    _heartbeat_thread.start()
    logger.info(f"[runner] heartbeat started -> {url}")


def _heartbeat_loop(url: str) -> None:
    while True:
        with _inflight_lock:
            busy = _inflight > 0
        if not busy:
            logger.info("[runner] heartbeat stopping (idle)")
            return
        try:
            urllib.request.urlopen(url, timeout=10).read(1)
        except Exception as e:
            logger.debug(f"[runner] heartbeat ping failed: {e}")
        _heartbeat_stop.wait(HEARTBEAT_INTERVAL_SECONDS)
