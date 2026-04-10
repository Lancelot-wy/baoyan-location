"""Document ingestion API endpoints."""
import os
import logging
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models.document import RawDocument, ExtractedFact, Evidence
from app.schemas.document import RawDocumentOut, ExtractedFactOut, CrawlRequest
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "image/gif": "image",
}


@router.post("/upload", response_model=RawDocumentOut, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_type: Optional[str] = Form(None),
    application_year: Optional[int] = Form(None),
    institution_hint: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # comma-separated
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF or image file for ingestion."""
    content_type = file.content_type or ""

    # Validate file type
    file_category = None
    for mime, category in ALLOWED_MIME_TYPES.items():
        if content_type.startswith(mime.split("/")[0]) and mime.split("/")[1] in content_type:
            file_category = category
            break
    if not file_category:
        # Try by extension
        if file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext == "pdf":
                file_category = "pdf"
            elif ext in ("jpg", "jpeg", "png", "webp", "gif"):
                file_category = "image"
    if not file_category:
        raise HTTPException(400, f"Unsupported file type: {content_type}")

    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = file_hash[:16] + "." + (file.filename or "file").rsplit(".", 1)[-1]
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Parse tags
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    # Trigger async ingestion
    background_tasks.add_task(
        _ingest_file_background,
        file_path=file_path,
        file_category=file_category,
        source_type=source_type,
        application_year=application_year,
        institution_hint=institution_hint,
        tags=tag_list,
    )

    # Return a preliminary document record
    from app.models.document import DocType, SourceType, ParseStatus
    try:
        st = SourceType(source_type) if source_type else SourceType.UNKNOWN
    except ValueError:
        st = SourceType.UNKNOWN

    doc = RawDocument(
        file_path=file_path,
        file_hash=file_hash,
        doc_type=DocType(file_category),
        source_type=st,
        content_hash=file_hash,
        parse_status=ParseStatus.PENDING,
        application_year=application_year,
        institution_hint=institution_hint,
        tags=tag_list or None,
        credibility_score=0.5,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


@router.post("/crawl", response_model=RawDocumentOut, status_code=202)
async def crawl_url(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a URL for crawling and ingestion."""
    # Check if already ingested
    existing = await db.execute(
        select(RawDocument).where(RawDocument.url == request.url)
    )
    existing_doc = existing.scalar_one_or_none()
    if existing_doc and not request.force_recrawl:
        return existing_doc

    background_tasks.add_task(
        _ingest_url_background,
        url=request.url,
        source_type=request.source_type,
        application_year=request.application_year,
        institution_hint=request.institution_hint,
        tags=request.tags,
    )

    from app.models.document import DocType, SourceType, ParseStatus
    try:
        st = SourceType(request.source_type) if request.source_type else SourceType.UNKNOWN
    except ValueError:
        st = SourceType.UNKNOWN

    doc = RawDocument(
        url=request.url,
        file_hash=hashlib.sha256(request.url.encode()).hexdigest(),
        doc_type=DocType.WEBPAGE,
        source_type=st,
        content_hash=hashlib.sha256(request.url.encode()).hexdigest(),
        parse_status=ParseStatus.PENDING,
        application_year=request.application_year,
        institution_hint=request.institution_hint,
        tags=request.tags or None,
        credibility_score=0.5,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


@router.get("/", response_model=List[RawDocumentOut])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    source_type: Optional[str] = None,
    parse_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all documents (admin endpoint)."""
    from app.models.document import SourceType, ParseStatus
    stmt = select(RawDocument).offset(skip).limit(limit).order_by(RawDocument.crawled_at.desc())
    if source_type:
        try:
            stmt = stmt.where(RawDocument.source_type == SourceType(source_type))
        except ValueError:
            pass
    if parse_status:
        try:
            stmt = stmt.where(RawDocument.parse_status == ParseStatus(parse_status))
        except ValueError:
            pass
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{doc_id}", response_model=RawDocumentOut)
async def get_document(doc_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RawDocument).where(RawDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.get("/{doc_id}/facts", response_model=List[ExtractedFactOut])
async def get_document_facts(doc_id: int, db: AsyncSession = Depends(get_db)):
    """Get all extracted facts from a document."""
    result = await db.execute(
        select(ExtractedFact)
        .where(ExtractedFact.document_id == doc_id)
        .order_by(ExtractedFact.confidence.desc())
    )
    return result.scalars().all()


@router.post("/{doc_id}/reprocess", status_code=202)
async def reprocess_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Re-trigger processing for a document (useful after OCR review)."""
    result = await db.execute(select(RawDocument).where(RawDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    from app.models.document import ParseStatus
    doc.parse_status = ParseStatus.PENDING
    await db.flush()

    background_tasks.add_task(_reprocess_document_background, doc_id)
    return {"message": f"Reprocessing queued for document {doc_id}"}


# ── Background tasks ───────────────────────────────────────────────────────────

async def _ingest_file_background(
    file_path: str,
    file_category: str,
    source_type: Optional[str],
    application_year: Optional[int],
    institution_hint: Optional[str],
    tags: list,
):
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion.pipeline import ingest_pdf, ingest_image

    async with AsyncSessionLocal() as db:
        try:
            if file_category == "pdf":
                await ingest_pdf(
                    file_path=file_path, db=db, source_type_hint=source_type,
                    application_year=application_year, institution_hint=institution_hint, tags=tags,
                )
            else:
                await ingest_image(
                    file_path=file_path, db=db, source_type_hint=source_type,
                    application_year=application_year, institution_hint=institution_hint, tags=tags,
                )
            await db.commit()
        except Exception as e:
            logger.error(f"Background file ingestion failed: {e}", exc_info=True)
            await db.rollback()


async def _ingest_url_background(
    url: str,
    source_type: Optional[str],
    application_year: Optional[int],
    institution_hint: Optional[str],
    tags: Optional[list],
):
    from app.db.session import AsyncSessionLocal
    from app.services.ingestion.pipeline import ingest_url

    async with AsyncSessionLocal() as db:
        try:
            await ingest_url(
                url=url, db=db, source_type_hint=source_type,
                application_year=application_year, institution_hint=institution_hint, tags=tags,
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Background URL ingestion failed: {e}", exc_info=True)
            await db.rollback()


async def _reprocess_document_background(doc_id: int):
    from app.db.session import AsyncSessionLocal
    from app.models.document import ParseStatus

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(RawDocument).where(RawDocument.id == doc_id))
            doc = result.scalar_one_or_none()
            if not doc or not doc.raw_content:
                return

            from app.services.ingestion.pipeline import _extract_and_store_facts
            await _extract_and_store_facts(doc, doc.raw_content, db)
            doc.parse_status = ParseStatus.DONE
            await db.commit()
        except Exception as e:
            logger.error(f"Reprocess failed for doc {doc_id}: {e}")
            await db.rollback()
