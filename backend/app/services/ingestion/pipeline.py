"""Ingestion pipeline: orchestrates parsing, extraction, and storage."""
import hashlib
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import RawDocument, DocType, SourceType, ParseStatus, Language, ExtractedFact, Evidence
from app.services.ingestion.base import WebPageResult, PDFResult, OCRResult
from app.services.ingestion.web_crawler import crawl_url
from app.services.ingestion.pdf_parser import parse_pdf
from app.services.ingestion.image_ocr import ocr_image
from app.services.extraction.entity_extractor import extract_facts_from_text
from app.services.extraction.document_classifier import classify_document
from app.core.constants import SOURCE_TYPE_WEIGHTS, get_time_decay, CURRENT_YEAR

logger = logging.getLogger(__name__)


def _compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def _source_type_to_credibility(source_type: str) -> float:
    return SOURCE_TYPE_WEIGHTS.get(source_type, 0.2)


async def ingest_url(
    url: str,
    db: AsyncSession,
    source_type_hint: Optional[str] = None,
    application_year: Optional[int] = None,
    tags: Optional[list] = None,
    institution_hint: Optional[str] = None,
) -> RawDocument:
    """
    Crawl a URL, store as RawDocument, trigger extraction.
    Returns the created/updated RawDocument.
    """
    # Check if URL already exists
    existing = await db.execute(
        select(RawDocument).where(RawDocument.url == url)
    )
    existing_doc = existing.scalar_one_or_none()

    try:
        result: WebPageResult = await crawl_url(url)
    except Exception as e:
        logger.error(f"Crawl failed for {url}: {e}")
        if existing_doc:
            existing_doc.parse_status = ParseStatus.FAILED
            existing_doc.parse_error = str(e)
            await db.flush()
            return existing_doc

        content_hash = _compute_hash(url)
        doc = RawDocument(
            url=url,
            file_hash=content_hash,
            doc_type=DocType.WEBPAGE,
            source_type=SourceType(source_type_hint or "unknown"),
            content_hash=content_hash,
            parse_status=ParseStatus.FAILED,
            parse_error=str(e),
            credibility_score=_source_type_to_credibility(source_type_hint or "unknown"),
            application_year=application_year,
            tags=tags,
            institution_hint=institution_hint,
        )
        db.add(doc)
        await db.flush()
        return doc

    content_hash = _compute_hash(result.main_content)
    file_hash = _compute_hash(url + result.main_content[:500])

    # Determine source type
    source_type_str = source_type_hint or result.page_type
    # Map page_type to SourceType enum values
    source_type_map = {
        "official": "official_notice",
        "official_notice": "official_notice",
        "experience_post": "experience_post",
        "advisor_page": "advisor_page",
        "department_page": "department_page",
        "lab_page": "lab_page",
        "unknown": "unknown",
    }
    source_type_str = source_type_map.get(source_type_str, "unknown")

    try:
        source_type_enum = SourceType(source_type_str)
    except ValueError:
        source_type_enum = SourceType.UNKNOWN

    credibility = _source_type_to_credibility(source_type_str)

    if existing_doc:
        if existing_doc.content_hash == content_hash:
            logger.info(f"URL {url} content unchanged, skipping re-ingestion")
            return existing_doc
        # Update existing
        existing_doc.raw_content = result.main_content
        existing_doc.content_hash = content_hash
        existing_doc.title = result.title
        existing_doc.published_at = result.published_at
        existing_doc.language = Language(result.language)
        existing_doc.source_type = source_type_enum
        existing_doc.credibility_score = credibility
        existing_doc.parse_status = ParseStatus.PROCESSING
        existing_doc.institution_hint = result.institution or institution_hint
        await db.flush()
        doc = existing_doc
    else:
        doc = RawDocument(
            url=url,
            file_hash=file_hash,
            doc_type=DocType.WEBPAGE,
            source_type=source_type_enum,
            title=result.title,
            published_at=result.published_at,
            raw_content=result.main_content,
            content_hash=content_hash,
            parse_status=ParseStatus.PROCESSING,
            language=Language(result.language),
            application_year=application_year,
            credibility_score=credibility,
            tags=tags,
            institution_hint=result.institution or institution_hint,
        )
        db.add(doc)
        await db.flush()

    # Extract facts
    await _extract_and_store_facts(doc, result.main_content, db)

    doc.parse_status = ParseStatus.DONE
    await db.flush()
    return doc


async def ingest_pdf(
    file_path: str,
    db: AsyncSession,
    source_type_hint: Optional[str] = None,
    application_year: Optional[int] = None,
    tags: Optional[list] = None,
    institution_hint: Optional[str] = None,
) -> RawDocument:
    """Parse a PDF file, store as RawDocument, trigger extraction."""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Check duplicate
    existing = await db.execute(
        select(RawDocument).where(RawDocument.file_hash == file_hash)
    )
    existing_doc = existing.scalar_one_or_none()
    if existing_doc:
        logger.info(f"PDF {file_path} already ingested (hash match)")
        return existing_doc

    try:
        result: PDFResult = parse_pdf(file_path)
    except Exception as e:
        logger.error(f"PDF parse failed for {file_path}: {e}")
        doc = RawDocument(
            file_path=file_path,
            file_hash=file_hash,
            doc_type=DocType.PDF,
            source_type=SourceType(source_type_hint or "unknown"),
            content_hash=file_hash,
            parse_status=ParseStatus.FAILED,
            parse_error=str(e),
            credibility_score=_source_type_to_credibility(source_type_hint or "unknown"),
            application_year=application_year,
            tags=tags,
            institution_hint=institution_hint,
        )
        db.add(doc)
        await db.flush()
        return doc

    content_hash = _compute_hash(result.full_text)
    source_type_str = source_type_hint or "unknown"
    try:
        source_type_enum = SourceType(source_type_str)
    except ValueError:
        source_type_enum = SourceType.UNKNOWN

    # Infer source type from PDF doc_type
    if result.doc_type == "recruitment_notice" and source_type_enum == SourceType.UNKNOWN:
        source_type_enum = SourceType.OFFICIAL_NOTICE

    credibility = _source_type_to_credibility(source_type_enum.value)

    # Classify document for institution_hint
    if not institution_hint:
        classification = classify_document(result.full_text[:3000], "pdf")
        institution_hint = classification.get("institution_hint")

    doc = RawDocument(
        file_path=file_path,
        file_hash=file_hash,
        doc_type=DocType.PDF,
        source_type=source_type_enum,
        raw_content=result.full_text,
        content_hash=content_hash,
        parse_status=ParseStatus.PROCESSING,
        application_year=application_year,
        credibility_score=credibility,
        tags=tags,
        institution_hint=institution_hint,
    )
    db.add(doc)
    await db.flush()

    await _extract_and_store_facts(doc, result.full_text, db)

    doc.parse_status = ParseStatus.DONE
    await db.flush()
    return doc


async def ingest_image(
    file_path: str,
    db: AsyncSession,
    source_type_hint: Optional[str] = None,
    application_year: Optional[int] = None,
    tags: Optional[list] = None,
    institution_hint: Optional[str] = None,
) -> RawDocument:
    """OCR an image, store as RawDocument, trigger extraction."""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    existing = await db.execute(
        select(RawDocument).where(RawDocument.file_hash == file_hash)
    )
    existing_doc = existing.scalar_one_or_none()
    if existing_doc:
        return existing_doc

    result: OCRResult = ocr_image(file_path)

    content_hash = _compute_hash(result.raw_text)

    # Determine source type from image classification
    image_source_map = {
        "offer_letter": "offer_screenshot",
        "announcement": "official_notice",
        "list": "official_notice",
        "experience_screenshot": "experience_post",
        "unknown": "unknown",
    }
    source_type_str = source_type_hint or image_source_map.get(result.image_type, "unknown")
    try:
        source_type_enum = SourceType(source_type_str)
    except ValueError:
        source_type_enum = SourceType.UNKNOWN

    credibility = _source_type_to_credibility(source_type_enum.value)

    parse_status = ParseStatus.NEEDS_REVIEW if result.needs_review else ParseStatus.PROCESSING

    doc = RawDocument(
        file_path=file_path,
        file_hash=file_hash,
        doc_type=DocType.IMAGE,
        source_type=source_type_enum,
        raw_content=result.raw_text,
        content_hash=content_hash,
        parse_status=parse_status,
        application_year=application_year,
        credibility_score=credibility,
        tags=tags,
        institution_hint=institution_hint,
    )
    db.add(doc)
    await db.flush()

    if not result.needs_review and result.raw_text.strip():
        await _extract_and_store_facts(doc, result.raw_text, db)
        doc.parse_status = ParseStatus.DONE

    await db.flush()
    return doc


async def _extract_and_store_facts(doc: RawDocument, text: str, db: AsyncSession):
    """Extract facts from text and store them with evidence weights."""
    try:
        facts_data = await extract_facts_from_text(
            text=text,
            source_type=doc.source_type.value,
            institution_hint=doc.institution_hint,
            application_year=doc.application_year,
        )

        year = doc.application_year or CURRENT_YEAR
        time_decay = get_time_decay(year)
        source_weight = SOURCE_TYPE_WEIGHTS.get(doc.source_type.value, 0.2)

        for fact_data in facts_data:
            fact = ExtractedFact(
                document_id=doc.id,
                fact_type=fact_data["fact_type"],
                subject_school=fact_data.get("subject_school"),
                subject_department=fact_data.get("subject_department"),
                subject_program=fact_data.get("subject_program"),
                subject_advisor=fact_data.get("subject_advisor"),
                fact_key=fact_data["fact_key"],
                fact_value=fact_data["fact_value"],
                fact_value_structured=fact_data.get("fact_value_structured"),
                confidence=fact_data.get("confidence", 0.7),
                effective_year=doc.application_year,
                extraction_method=fact_data.get("extraction_method", "llm"),
                raw_excerpt=fact_data.get("raw_excerpt", text[:500]),
            )
            db.add(fact)
            await db.flush()

            # Create evidence record
            weight = source_weight * time_decay * fact.confidence
            evidence = Evidence(
                fact_id=fact.id,
                document_id=doc.id,
                weight=weight,
                time_decay_factor=time_decay,
                source_type_weight=source_weight,
                credibility_score=doc.credibility_score,
            )
            db.add(evidence)

        await db.flush()
        logger.info(f"Extracted {len(facts_data)} facts from document {doc.id}")

    except Exception as e:
        logger.error(f"Fact extraction failed for document {doc.id}: {e}")
        doc.parse_error = f"Extraction error: {str(e)[:500]}"
