import os
import signal
import sys
import threading
import time
import uuid

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.services.file_service import initialize_storage_provider
from app.services.rag.ingestion_runner import (
    claim_next_document,
    recover_expired_documents,
    renew_document_lease,
)
from app.services.rag.ingestion_service import ingestion_service

setup_logging()
logger = get_logger(__name__)

_running = True


def _handle_signal(signum, _frame):
    global _running
    logger.info("[worker] received signal %s, shutting down", signum)
    _running = False


class LeaseHeartbeat:
    """Renew ownership while PDF parsing or an embedding call is in flight."""

    def __init__(self, document_id: str, worker_id: str):
        self.document_id = document_id
        self.worker_id = worker_id
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=2)

    def _run(self) -> None:
        interval = max(
            1,
            min(
                settings.INGESTION_HEARTBEAT_INTERVAL_SECONDS,
                settings.INGESTION_LEASE_SECONDS // 2,
            ),
        )
        while not self._stop.wait(interval):
            try:
                if not renew_document_lease(
                    self.document_id,
                    self.worker_id,
                    settings.INGESTION_LEASE_SECONDS,
                ):
                    logger.warning(
                        "[worker] lease lost for document %s; ingestion will stop at its next checkpoint",
                        self.document_id,
                    )
                    return
            except Exception as exc:
                # Do not relinquish ownership after one transient DB error.
                # The next heartbeat and the service checkpoints will retry.
                logger.warning("[worker] lease heartbeat failed: %s", exc)


def main() -> int:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("[worker] starting ingestion worker")
    initialize_storage_provider(settings)
    worker_id = os.getenv("FLY_MACHINE_ID") or f"local-{uuid.uuid4()}"
    recovery = recover_expired_documents()
    logger.info(
        "[worker] recovery complete (worker=%s reset=%s cancelled=%s)",
        worker_id,
        recovery["reset"],
        recovery["cancelled"],
    )

    idle_sleep = max(0.5, settings.INGESTION_POLL_INTERVAL_SECONDS)
    recovery_interval = max(30.0, min(float(settings.INGESTION_LEASE_SECONDS), 300.0))
    next_recovery_at = time.monotonic() + recovery_interval

    while _running:
        try:
            # Periodic recovery is the fallback when a worker died without a
            # graceful shutdown. It never touches an unexpired active lease.
            if time.monotonic() >= next_recovery_at:
                recover_expired_documents()
                next_recovery_at = time.monotonic() + recovery_interval
            document_id = claim_next_document(
                worker_id,
                settings.INGESTION_LEASE_SECONDS,
            )
            if not document_id:
                time.sleep(idle_sleep)
                continue

            logger.info("[worker] picked pending document %s", document_id)
            heartbeat = LeaseHeartbeat(document_id, worker_id)
            heartbeat.start()
            try:
                ingestion_service.ingest_document(document_id, worker_id)
            finally:
                heartbeat.stop()
        except Exception as exc:
            logger.error("[worker] loop error: %s", exc, exc_info=True)
            time.sleep(idle_sleep)

    logger.info("[worker] stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
