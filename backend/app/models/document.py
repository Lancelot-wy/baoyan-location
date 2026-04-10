from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Enum as SAEnum, ARRAY, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class DocType(str, enum.Enum):
    WEBPAGE = "webpage"
    PDF = "pdf"
    IMAGE = "image"
    SCREENSHOT = "screenshot"
    QQ_MESSAGE = "qq_message"
    MANUAL = "manual"


class SourceType(str, enum.Enum):
    OFFICIAL_NOTICE = "official_notice"
    DEPARTMENT_PAGE = "department_page"
    ADVISOR_PAGE = "advisor_page"
    LAB_PAGE = "lab_page"
    EXPERIENCE_POST = "experience_post"
    OFFER_SCREENSHOT = "offer_screenshot"
    QQ_GROUP = "qq_group"
    UNKNOWN = "unknown"


class ParseStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class Language(str, enum.Enum):
    ZH = "zh"
    EN = "en"
    MIXED = "mixed"


class FactType(str, enum.Enum):
    RANK_REQUIREMENT = "rank_requirement"
    RESEARCH_PREFERENCE = "research_preference"
    INTERVIEW_FORMAT = "interview_format"
    QUOTA = "quota"
    DEADLINE = "deadline"
    ADVISOR_PREFERENCE = "advisor_preference"
    PROGRAM_DETAIL = "program_detail"
    OFFER_RESULT = "offer_result"
    OTHER = "other"


class ExtractionMethod(str, enum.Enum):
    LLM = "llm"
    RULE = "rule"
    OCR_LLM = "ocr_llm"
    MANUAL = "manual"


class RawDocument(Base):
    __tablename__ = "raw_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True, index=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    doc_type: Mapped[DocType] = mapped_column(SAEnum(DocType), nullable=False, index=True)
    source_type: Mapped[SourceType] = mapped_column(SAEnum(SourceType), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    parse_status: Mapped[ParseStatus] = mapped_column(
        SAEnum(ParseStatus), nullable=False, default=ParseStatus.PENDING, index=True
    )
    parse_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Language] = mapped_column(SAEnum(Language), nullable=False, default=Language.ZH)
    application_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    is_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_hint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    institution_hint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    facts: Mapped[List["ExtractedFact"]] = relationship(
        "ExtractedFact", back_populates="document", cascade="all, delete-orphan"
    )
    evidences: Mapped[List["Evidence"]] = relationship(
        "Evidence", back_populates="document"
    )


class ExtractedFact(Base):
    __tablename__ = "extracted_facts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_documents.id"), nullable=False)
    fact_type: Mapped[FactType] = mapped_column(SAEnum(FactType), nullable=False)
    subject_school: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    subject_department: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    subject_program: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)
    subject_advisor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fact_key: Mapped[str] = mapped_column(String(200), nullable=False)
    fact_value: Mapped[str] = mapped_column(Text, nullable=False)
    fact_value_structured: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    effective_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    extraction_method: Mapped[ExtractionMethod] = mapped_column(SAEnum(ExtractionMethod), nullable=False)
    raw_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    is_superseded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    superseded_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("extracted_facts.id"), nullable=True)

    document: Mapped["RawDocument"] = relationship("RawDocument", back_populates="facts")
    evidences: Mapped[List["Evidence"]] = relationship(
        "Evidence", back_populates="fact", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact_id: Mapped[int] = mapped_column(Integer, ForeignKey("extracted_facts.id"), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_documents.id"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)  # source_weight * time_decay * confidence
    time_decay_factor: Mapped[float] = mapped_column(Float, nullable=False)
    source_type_weight: Mapped[float] = mapped_column(Float, nullable=False)
    credibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    fact: Mapped["ExtractedFact"] = relationship("ExtractedFact", back_populates="evidences")
    document: Mapped["RawDocument"] = relationship("RawDocument", back_populates="evidences")
