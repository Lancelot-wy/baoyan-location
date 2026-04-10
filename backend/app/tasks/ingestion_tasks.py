"""Celery tasks for async document ingestion."""
import asyncio
import logging
from typing import Optional, List

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="ingest_url", bind=True, max_retries=3)
def ingest_url_task(
    self,
    url: str,
    source_type: Optional[str] = None,
    application_year: Optional[int] = None,
    institution_hint: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    """Celery task to ingest a URL."""
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion.pipeline import ingest_url

    async def _run():
        async with AsyncSessionLocal() as db:
            doc = await ingest_url(
                url=url, db=db,
                source_type_hint=source_type,
                application_year=application_year,
                institution_hint=institution_hint,
                tags=tags,
            )
            await db.commit()
            return doc.id

    try:
        doc_id = _run_async(_run())
        logger.info(f"Successfully ingested URL {url} → document {doc_id}")
        return {"doc_id": doc_id, "url": url}
    except Exception as exc:
        logger.error(f"URL ingestion failed: {url} — {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="ingest_file", bind=True, max_retries=3)
def ingest_file_task(
    self,
    file_path: str,
    file_category: str,  # "pdf" or "image"
    source_type: Optional[str] = None,
    application_year: Optional[int] = None,
    institution_hint: Optional[str] = None,
    tags: Optional[List[str]] = None,
):
    """Celery task to ingest a file (PDF or image)."""
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion.pipeline import ingest_pdf, ingest_image

    async def _run():
        async with AsyncSessionLocal() as db:
            if file_category == "pdf":
                doc = await ingest_pdf(
                    file_path=file_path, db=db,
                    source_type_hint=source_type,
                    application_year=application_year,
                    institution_hint=institution_hint,
                    tags=tags,
                )
            else:
                doc = await ingest_image(
                    file_path=file_path, db=db,
                    source_type_hint=source_type,
                    application_year=application_year,
                    institution_hint=institution_hint,
                    tags=tags,
                )
            await db.commit()
            return doc.id

    try:
        doc_id = _run_async(_run())
        logger.info(f"Successfully ingested file {file_path} → document {doc_id}")
        return {"doc_id": doc_id, "file_path": file_path}
    except Exception as exc:
        logger.error(f"File ingestion failed: {file_path} — {exc}")
        raise self.retry(exc=exc, countdown=60)
