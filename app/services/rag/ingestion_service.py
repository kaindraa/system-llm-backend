"""
Document Ingestion Service

In-app port of `ingest_docs_for_rag.ipynb`: turns an uploaded PDF into
chunked + embedded `document_chunk` rows for RAG.

Design (see processing dashboard PRD):
  - Runs as a background task, processing ONE document at a time (serial) to
    keep RAM low on the small Fly machine.
  - Tracks stage plus bounded progress updates for the processing dashboard.
  - Cooperative cancellation: `document.cancel_requested` is checked between
    stages and between embedding batches.
  - Idempotent: existing chunks for the document are deleted before insert,
    so re-ingest never duplicates.
  - Retry: transient embedding errors retried with backoff (Level A); a fully
    failed job increments `retry_count` and is left FAILED (Level B retry is
    triggered externally by re-queue / admin re-process).

Sessions are kept short: status/stage updates open-commit-close immediately,
and the slow embedding step holds no DB transaction.
"""

import io
import re
import signal
import threading
import time
from contextlib import contextmanager
from typing import Any, Dict, List

from sqlalchemy import text as sql_text

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.logging import get_logger
from app.models.document import IngestionStage
from app.models.document_chunk import DocumentChunk
from app.services.file_service import FileService

logger = get_logger(__name__)


class IngestionCancelled(Exception):
    """Raised internally when cancel_requested is observed mid-pipeline."""
    pass


class IngestionLeaseLost(Exception):
    """Raised when a replacement worker has taken ownership of a document."""
    pass


class PDFParseTimeout(Exception):
    """Raised when PDF extraction exceeds the configured safety deadline."""
    pass


@contextmanager
def _pdf_parse_deadline(seconds: int):
    """Interrupt a hung parser on Unix worker processes.

    The dedicated worker executes this on its main thread. Other environments
    without SIGALRM simply retain the page and memory limits.
    """
    if (
        seconds <= 0
        or not hasattr(signal, "SIGALRM")
        or threading.current_thread() is not threading.main_thread()
    ):
        yield
        return

    def _timeout(_signum, _frame):
        raise PDFParseTimeout(f"PDF parsing exceeded {seconds} seconds")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


class IngestionService:
    """Processes a single uploaded PDF document into RAG chunks."""

    EMBED_MODEL = "text-embedding-3-small"
    EMBED_BATCH_SIZE = 64          # OpenAI accepts arrays; batch to cut latency/cost
    EMBED_MAX_RETRIES = 3          # Level A: transient error retries
    CHUNK_SIZE = 500               # words per chunk (matches notebook)
    CHUNK_OVERLAP = 50             # word overlap (matches notebook)
    MAX_PDF_PAGES = settings.INGESTION_MAX_PDF_PAGES

    def __init__(self):
        self._embeddings_client = None

    # ------------------------------------------------------------------ #
    # Public entrypoint
    # ------------------------------------------------------------------ #
    def ingest_document(self, document_id: str, worker_id: str) -> None:
        """
        Run the full ingestion pipeline for one document.

        Safe to call from a background task. Never raises to the caller — all
        outcomes are recorded on the document row (PROCESSED / FAILED /
        CANCELLED).
        """
        logger.info(f"[ingest] start document={document_id}")
        try:
            # 1. Fetch PDF bytes
            self._check_cancel(document_id, worker_id)
            pdf_bytes, original_filename = self._fetch_pdf(document_id)

            # 2. Parse (stage=parsing)
            self._set_stage(document_id, worker_id, IngestionStage.PARSING, 1, "Opening PDF")
            self._check_cancel(document_id, worker_id)
            pages_text = self._extract_text_from_pdf(document_id, worker_id, pdf_bytes)
            if not pages_text:
                raise ValueError("No extractable text found in PDF")

            # 3. Chunk (stage=chunking)
            self._set_stage(document_id, worker_id, IngestionStage.CHUNKING, 40, "Preparing text chunks")
            self._check_cancel(document_id, worker_id)
            chunks = self._chunk_text_with_pages(document_id, worker_id, pages_text)
            if not chunks:
                raise ValueError("PDF produced zero chunks")
            full_text = "\n\n".join(
                pages_text[p]["text"] for p in sorted(pages_text)
            )

            # 4. Embed (stage=embedding) — slow, network bound, no DB tx held
            self._set_stage(document_id, worker_id, IngestionStage.EMBEDDING, 55, "Creating embeddings")
            embeddings = self._embed_chunks(
                document_id,
                worker_id,
                [chunk["content"] for chunk in chunks],
            )

            # 5. Insert (stage=inserting) — idempotent
            self._set_stage(document_id, worker_id, IngestionStage.INSERTING, 85, "Indexing chunks")
            self._replace_chunks(document_id, worker_id, chunks, embeddings, full_text)

            # 6. Finalize
            self._finalize(document_id, worker_id)
            logger.info(f"[ingest] done document={document_id} chunks={len(chunks)}")

        except IngestionCancelled:
            logger.info(f"[ingest] cancelled document={document_id}")
            try:
                self._mark_cancelled(document_id, worker_id)
            except IngestionLeaseLost:
                logger.warning(f"[ingest] lease lost while cancelling document={document_id}")
        except IngestionLeaseLost:
            logger.warning(f"[ingest] lease lost document={document_id}; replacement worker owns it")
        except Exception as e:
            logger.error(f"[ingest] failed document={document_id}: {e}", exc_info=True)
            try:
                self._mark_failed(document_id, worker_id, str(e))
            except IngestionLeaseLost:
                logger.warning(f"[ingest] lease lost while failing document={document_id}")

    # ------------------------------------------------------------------ #
    # Pipeline stages (ported from the notebook)
    # ------------------------------------------------------------------ #
    def _extract_text_from_pdf(
        self,
        document_id: str,
        worker_id: str,
        pdf_bytes: bytes,
    ) -> Dict[int, Dict[str, Any]]:
        """Extract text and native PDF word coordinates for every page.

        We store the coordinates at ingestion time because PDF.js and
        pdfplumber do not always produce byte-for-byte equivalent text. A
        citation can therefore be highlighted from its source geometry instead
        of depending on brittle browser-side text matching.
        """
        import pdfplumber

        pages_text: Dict[int, Dict[str, Any]] = {}
        with _pdf_parse_deadline(settings.INGESTION_PDF_PARSE_TIMEOUT_SECONDS):
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                page_count = len(pdf.pages)
                if page_count > self.MAX_PDF_PAGES:
                    raise ValueError(
                        f"PDF has {page_count} pages, exceeds limit of {self.MAX_PDF_PAGES}"
                    )
                self._set_progress(document_id, worker_id, 2, 0, page_count, f"Extracting page 0/{page_count}")
                update_every = max(1, page_count // 20)
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        self._check_cancel(document_id, worker_id)
                        words = page.extract_words(
                            x_tolerance=3,
                            y_tolerance=3,
                            use_text_flow=True,
                        )
                        if words:
                            pages_text[page_num] = {
                                "text": " ".join(str(word["text"]) for word in words),
                                "words": words,
                                "width": float(page.width),
                                "height": float(page.height),
                            }
                        if page_num % update_every == 0 or page_num == page_count:
                            progress = 2 + int((page_num / page_count) * 38)
                            self._set_progress(
                                document_id,
                                worker_id,
                                progress,
                                page_num,
                                page_count,
                                f"Extracting page {page_num}/{page_count}",
                            )
                    finally:
                        # pdfplumber caches page layouts, characters, and images.
                        # Releasing each page bounds memory for large PDFs instead
                        # of accumulating hundreds of page object graphs.
                        page.close()
                pdf.flush_cache()
        return pages_text

    def _chunk_text_with_pages(
        self,
        document_id: str,
        worker_id: str,
        pages_text: Dict[int, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Word-counted chunks with page tracking and highlight rectangles.

        Chunks remain page-local. The overlap is represented by the same source
        words in adjacent chunks, which makes their stored highlight geometry
        precise even when a browser PDF renderer extracts text differently.
        """
        chunk_size = self.CHUNK_SIZE
        overlap = self.CHUNK_OVERLAP
        chunks_with_pages: List[Dict[str, Any]] = []

        page_numbers = sorted(pages_text.keys())
        total_pages = len(page_numbers)
        update_every = max(1, total_pages // 20)
        for position, page_num in enumerate(page_numbers, 1):
            self._check_cancel(document_id, worker_id)
            page = pages_text[page_num]
            words = page["words"]
            start = 0
            while start < len(words):
                proposed_end = min(start + chunk_size, len(words))
                end = proposed_end

                # Prefer a nearby sentence boundary without sacrificing a
                # predictable maximum chunk size. Looking back 20% keeps very
                # long sentences from producing tiny chunks.
                minimum_end = start + max(1, int(chunk_size * 0.8))
                if proposed_end < len(words):
                    for index in range(proposed_end - 1, minimum_end - 1, -1):
                        if re.search(r'[.!?][\]"\')]*$', str(words[index]["text"])):
                            end = index + 1
                            break

                chunk_words = words[start:end]
                chunks_with_pages.append({
                    "content": " ".join(str(word["text"]) for word in chunk_words),
                    "page_number": page_num,
                    "highlight": {
                        "version": 1,
                        "page_width": round(page["width"], 3),
                        "page_height": round(page["height"], 3),
                        "rects": self._build_highlight_rects(chunk_words),
                    },
                })

                if end >= len(words):
                    break
                start = max(end - overlap, start + 1)
            if position % update_every == 0 or position == total_pages:
                progress = 40 + int((position / total_pages) * 15)
                self._set_progress(
                    document_id,
                    worker_id,
                    progress,
                    position,
                    total_pages,
                    f"Chunking page {position}/{total_pages}",
                )

        return chunks_with_pages

    @staticmethod
    def _build_highlight_rects(words: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """Return compact line rectangles in the PDF's native coordinate space."""
        rects: List[Dict[str, float]] = []
        current: Dict[str, float] | None = None

        for word in words:
            try:
                x0 = float(word["x0"])
                top = float(word["top"])
                x1 = float(word["x1"])
                bottom = float(word["bottom"])
            except (KeyError, TypeError, ValueError):
                continue

            # A large horizontal gap is a new region even if another column
            # happens to share the same baseline.
            same_line = (
                current is not None
                and abs(top - current["top"]) <= 2
                and x0 <= current["x1"] + 24
            )
            if not same_line:
                if current is not None:
                    rects.append(current)
                current = {"x0": x0, "top": top, "x1": x1, "bottom": bottom}
                continue

            current["x0"] = min(current["x0"], x0)
            current["top"] = min(current["top"], top)
            current["x1"] = max(current["x1"], x1)
            current["bottom"] = max(current["bottom"], bottom)

        if current is not None:
            rects.append(current)

        return [
            {
                "x": round(rect["x0"], 3),
                "y": round(rect["top"], 3),
                "width": round(rect["x1"] - rect["x0"], 3),
                "height": round(rect["bottom"] - rect["top"], 3),
            }
            for rect in rects
            if rect["x1"] > rect["x0"] and rect["bottom"] > rect["top"]
        ]

    def _embed_chunks(
        self,
        document_id: str,
        worker_id: str,
        texts: List[str],
    ) -> List[List[float]]:
        """
        Generate embeddings in batches with retry/backoff.
        Checks cancellation between batches.
        """
        client = self._get_embeddings_client()
        embeddings: List[List[float]] = []

        total_batches = max(1, (len(texts) + self.EMBED_BATCH_SIZE - 1) // self.EMBED_BATCH_SIZE)
        for batch_index, start in enumerate(range(0, len(texts), self.EMBED_BATCH_SIZE), 1):
            self._check_cancel(document_id, worker_id)
            batch = texts[start:start + self.EMBED_BATCH_SIZE]
            embeddings.extend(self._embed_batch_with_retry(client, batch))
            progress = 55 + int((batch_index / total_batches) * 30)
            self._set_progress(
                document_id,
                worker_id,
                progress,
                detail=f"Embedding batch {batch_index}/{total_batches}",
            )

        return embeddings

    def _embed_batch_with_retry(self, client, batch: List[str]) -> List[List[float]]:
        last_err = None
        for attempt in range(self.EMBED_MAX_RETRIES):
            try:
                resp = client.embeddings.create(input=batch, model=self.EMBED_MODEL)
                # API preserves input order
                return [item.embedding for item in resp.data]
            except Exception as e:
                last_err = e
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"[ingest] embedding batch failed (attempt {attempt + 1}): {e}; retry in {wait}s")
                time.sleep(wait)
        raise RuntimeError(f"Embedding failed after {self.EMBED_MAX_RETRIES} attempts: {last_err}")

    def _replace_chunks(
        self,
        document_id: str,
        worker_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        full_text: str,
    ) -> None:
        """Delete existing chunks then insert new ones (idempotent). Single transaction."""
        db = SessionLocal()
        try:
            owned = db.execute(
                sql_text("""
                    SELECT 1
                      FROM document
                     WHERE id = :id
                       AND status = 'PROCESSING'
                       AND processing_owner = :worker_id
                       AND lease_expires_at >= now()
                """),
                {"id": document_id, "worker_id": worker_id},
            ).scalar()
            if not owned:
                raise IngestionLeaseLost()

            # idempotency: clear previous chunks for this document
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete(synchronize_session=False)

            total_chunks = len(chunks)
            update_every = max(1, total_chunks // 10)
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                self._check_cancel(document_id, worker_id)
                content = chunk["content"]
                page_number = chunk["page_number"]
                db.add(DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    content=content,
                    page_number=page_number,
                    embedding=embedding,  # SQLAlchemy/pgvector handles list -> vector
                    chunk_metadata={
                        "page": page_number,
                        "chunk_sequence": idx,
                        "highlight": chunk["highlight"],
                    },
                ))
                if (idx + 1) % update_every == 0 or idx + 1 == total_chunks:
                    progress = 85 + int(((idx + 1) / total_chunks) * 14)
                    self._set_progress(
                        document_id,
                        worker_id,
                        progress,
                        detail=f"Indexing chunk {idx + 1}/{total_chunks}",
                    )

            # store raw extracted text on the document (content column)
            db.execute(
                sql_text("UPDATE document SET content = :c WHERE id = :id"),
                {"c": full_text, "id": document_id},
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # State transitions (short-lived sessions)
    # ------------------------------------------------------------------ #
    def _set_stage(
        self,
        document_id: str,
        worker_id: str,
        stage: IngestionStage,
        progress_percent: int,
        detail: str,
    ) -> None:
        self._exec_owned(
            """UPDATE document
                  SET current_stage = :stage,
                      progress_percent = :progress_percent,
                      processing_detail = :detail
                WHERE id = :id
                  AND status = 'PROCESSING'
                  AND processing_owner = :worker_id""",
            {
                "stage": stage.value,
                "progress_percent": progress_percent,
                "detail": detail,
                "id": document_id,
                "worker_id": worker_id,
            },
        )

    def _set_progress(
        self,
        document_id: str,
        worker_id: str,
        progress_percent: int,
        processed_pages: int | None = None,
        total_pages: int | None = None,
        detail: str | None = None,
    ) -> None:
        self._exec_owned(
            """UPDATE document
                  SET progress_percent = :progress_percent,
                      processed_pages = COALESCE(:processed_pages, processed_pages),
                      total_pages = COALESCE(:total_pages, total_pages),
                      processing_detail = COALESCE(:detail, processing_detail)
                WHERE id = :id
                  AND status = 'PROCESSING'
                  AND processing_owner = :worker_id""",
            {
                "progress_percent": min(99, max(0, progress_percent)),
                "processed_pages": processed_pages,
                "total_pages": total_pages,
                "detail": detail,
                "id": document_id,
                "worker_id": worker_id,
            },
        )

    def _finalize(self, document_id: str, worker_id: str) -> None:
        self._exec_owned(
            """UPDATE document
                  SET status = 'PROCESSED',
                      current_stage = :stage,
                      progress_percent = 100,
                      processing_detail = 'Ready',
                      processed_at = now(),
                      last_error = NULL,
                      processing_owner = NULL,
                      lease_expires_at = NULL,
                      last_heartbeat_at = NULL
                WHERE id = :id
                  AND status = 'PROCESSING'
                  AND processing_owner = :worker_id""",
            {
                "stage": IngestionStage.DONE.value,
                "id": document_id,
                "worker_id": worker_id,
            },
        )

    def _mark_failed(self, document_id: str, worker_id: str, error: str) -> None:
        self._exec_owned(
            """UPDATE document
                  SET status = 'FAILED',
                      current_stage = NULL,
                      last_error = :err,
                      retry_count = retry_count + 1,
                      processing_owner = NULL,
                      lease_expires_at = NULL,
                      last_heartbeat_at = NULL
                WHERE id = :id
                  AND status = 'PROCESSING'
                  AND processing_owner = :worker_id""",
            {"err": error[:2000], "id": document_id, "worker_id": worker_id},
        )

    def _mark_cancelled(self, document_id: str, worker_id: str) -> None:
        # remove any partial chunks written before cancellation
        db = SessionLocal()
        try:
            owned = db.execute(
                sql_text("""
                    SELECT 1
                      FROM document
                     WHERE id = :id
                       AND status = 'PROCESSING'
                       AND processing_owner = :worker_id
                """),
                {"id": document_id, "worker_id": worker_id},
            ).scalar()
            if not owned:
                raise IngestionLeaseLost()
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete(synchronize_session=False)
            db.execute(
                sql_text("""UPDATE document
                               SET status = 'CANCELLED',
                                   current_stage = NULL,
                                   cancel_requested = false,
                                   processing_owner = NULL,
                                   lease_expires_at = NULL,
                                   last_heartbeat_at = NULL
                             WHERE id = :id
                               AND status = 'PROCESSING'
                               AND processing_owner = :worker_id"""),
                {"id": document_id, "worker_id": worker_id},
            )
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _check_cancel(self, document_id: str, worker_id: str) -> None:
        db = SessionLocal()
        try:
            row = db.execute(
                sql_text("""
                    SELECT cancel_requested
                      FROM document
                     WHERE id = :id
                       AND status = 'PROCESSING'
                       AND processing_owner = :worker_id
                       AND lease_expires_at >= now()
                """),
                {"id": document_id, "worker_id": worker_id},
            ).first()
        finally:
            db.close()
        if not row:
            raise IngestionLeaseLost()
        if row[0]:
            raise IngestionCancelled()

    def _fetch_pdf(self, document_id: str) -> Tuple[bytes, str]:
        db = SessionLocal()
        try:
            fs = FileService(db)
            doc = fs.get_file(document_id)
            content = fs.get_file_content(document_id)
            return content, doc.original_filename
        finally:
            db.close()

    def _exec_owned(self, statement: str, params: dict) -> None:
        db = SessionLocal()
        try:
            result = db.execute(sql_text(statement), params)
            db.commit()
            if result.rowcount != 1:
                raise IngestionLeaseLost()
        finally:
            db.close()

    def _get_embeddings_client(self):
        if self._embeddings_client is None:
            from openai import OpenAI
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not configured")
            self._embeddings_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._embeddings_client


# Module-level singleton (stateless apart from the cached OpenAI client)
ingestion_service = IngestionService()
