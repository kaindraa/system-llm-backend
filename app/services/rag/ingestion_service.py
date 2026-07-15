"""
Document Ingestion Service

In-app port of `ingest_docs_for_rag.ipynb`: turns an uploaded PDF into
chunked + embedded `document_chunk` rows for RAG.

Design (see processing dashboard PRD):
  - Runs as a background task, processing ONE document at a time (serial) to
    keep RAM low on the small Fly machine.
  - Tracks fine-grained progress via `document.current_stage` (parsing →
    chunking → embedding → inserting → done) — one small DB write per stage,
    no per-chunk percentage.
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
import time
from typing import List, Dict, Tuple

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


class IngestionService:
    """Processes a single uploaded PDF document into RAG chunks."""

    EMBED_MODEL = "text-embedding-3-small"
    EMBED_BATCH_SIZE = 64          # OpenAI accepts arrays; batch to cut latency/cost
    EMBED_MAX_RETRIES = 3          # Level A: transient error retries
    CHUNK_SIZE = 500               # words per chunk (matches notebook)
    CHUNK_OVERLAP = 50             # word overlap (matches notebook)
    MAX_PDF_PAGES = 1000           # guard against runaway RAM on the 1GB machine

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
            self._set_stage(document_id, worker_id, IngestionStage.PARSING)
            self._check_cancel(document_id, worker_id)
            pages_text = self._extract_text_from_pdf(document_id, worker_id, pdf_bytes)
            if not pages_text:
                raise ValueError("No extractable text found in PDF")

            # 3. Chunk (stage=chunking)
            self._set_stage(document_id, worker_id, IngestionStage.CHUNKING)
            self._check_cancel(document_id, worker_id)
            chunks = self._chunk_text_with_pages(document_id, worker_id, pages_text)
            if not chunks:
                raise ValueError("PDF produced zero chunks")
            full_text = "\n\n".join(pages_text[p] for p in sorted(pages_text))

            # 4. Embed (stage=embedding) — slow, network bound, no DB tx held
            self._set_stage(document_id, worker_id, IngestionStage.EMBEDDING)
            embeddings = self._embed_chunks(document_id, worker_id, [c[0] for c in chunks])

            # 5. Insert (stage=inserting) — idempotent
            self._set_stage(document_id, worker_id, IngestionStage.INSERTING)
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
    ) -> Dict[int, str]:
        """Extract text per page: {page_number: text}. (notebook cell 8)"""
        import pdfplumber

        pages_text: Dict[int, str] = {}
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if len(pdf.pages) > self.MAX_PDF_PAGES:
                raise ValueError(
                    f"PDF has {len(pdf.pages)} pages, exceeds limit of {self.MAX_PDF_PAGES}"
                )
            for page_num, page in enumerate(pdf.pages, 1):
                self._check_cancel(document_id, worker_id)
                extracted = page.extract_text()
                if extracted:
                    pages_text[page_num] = extracted
        return pages_text

    def _chunk_text_with_pages(
        self,
        document_id: str,
        worker_id: str,
        pages_text: Dict[int, str]
    ) -> List[Tuple[str, int]]:
        """Sentence-aware, word-counted chunking with page tracking. (notebook cell 10)"""
        chunk_size = self.CHUNK_SIZE
        overlap = self.CHUNK_OVERLAP
        chunks_with_pages: List[Tuple[str, int]] = []

        for page_num in sorted(pages_text.keys()):
            self._check_cancel(document_id, worker_id)
            page_content = pages_text[page_num]
            sentences = re.split(r'(?<=[.!?])\s+', page_content)

            current_chunk: List[str] = []
            current_size = 0

            for sentence in sentences:
                words = sentence.split()
                if current_size + len(words) > chunk_size and current_chunk:
                    chunk_content = ' '.join(current_chunk)
                    chunks_with_pages.append((chunk_content, page_num))
                    # keep a small word overlap for context continuity
                    current_chunk = current_chunk[-int(overlap / 10):]
                    current_size = len(' '.join(current_chunk).split())

                current_chunk.extend(words)
                current_size += len(words)

            # flush remainder of the page
            if current_chunk:
                chunk_content = ' '.join(current_chunk)
                chunks_with_pages.append((chunk_content, page_num))

        return chunks_with_pages

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

        for start in range(0, len(texts), self.EMBED_BATCH_SIZE):
            self._check_cancel(document_id, worker_id)
            batch = texts[start:start + self.EMBED_BATCH_SIZE]
            embeddings.extend(self._embed_batch_with_retry(client, batch))

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
        chunks: List[Tuple[str, int]],
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

            for idx, ((content, page_number), embedding) in enumerate(zip(chunks, embeddings)):
                self._check_cancel(document_id, worker_id)
                db.add(DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    content=content,
                    page_number=page_number,
                    embedding=embedding,  # SQLAlchemy/pgvector handles list -> vector
                    chunk_metadata={"page": page_number, "chunk_sequence": idx},
                ))

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
    def _set_stage(self, document_id: str, worker_id: str, stage: IngestionStage) -> None:
        self._exec_owned(
            """UPDATE document
                  SET current_stage = :stage
                WHERE id = :id
                  AND status = 'PROCESSING'
                  AND processing_owner = :worker_id""",
            {"stage": stage.value, "id": document_id, "worker_id": worker_id},
        )

    def _finalize(self, document_id: str, worker_id: str) -> None:
        self._exec_owned(
            """UPDATE document
                  SET status = 'PROCESSED',
                      current_stage = :stage,
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
