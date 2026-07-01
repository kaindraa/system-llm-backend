import signal
import sys
import time

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.services.file_service import initialize_storage_provider
from app.services.rag.ingestion_runner import (
    get_next_pending_document_id,
    requeue_orphans,
)
from app.services.rag.ingestion_service import ingestion_service

setup_logging()
logger = get_logger(__name__)

_running = True


def _handle_signal(signum, _frame):
    global _running
    logger.info("[worker] received signal %s, shutting down", signum)
    _running = False


def main() -> int:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info("[worker] starting ingestion worker")
    initialize_storage_provider(settings)
    recovery = requeue_orphans(reenqueue=False)
    logger.info(
        "[worker] recovery complete (reset=%s cancelled=%s requeued=%s)",
        recovery["reset"],
        recovery["cancelled"],
        recovery["requeued"],
    )

    idle_sleep = max(0.5, settings.INGESTION_POLL_INTERVAL_SECONDS)

    while _running:
        try:
            document_id = get_next_pending_document_id()
            if not document_id:
                time.sleep(idle_sleep)
                continue

            logger.info("[worker] picked pending document %s", document_id)
            ingestion_service.ingest_document(document_id)
        except Exception as exc:
            logger.error("[worker] loop error: %s", exc, exc_info=True)
            time.sleep(idle_sleep)

    logger.info("[worker] stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
