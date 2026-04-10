from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel

from app.models.document import DocType, SourceType, ParseStatus, Language, FactType, ExtractionMethod


class DocumentUploadResponse(BaseModel):
    document_id: int
    file_hash: str
    parse_status: ParseStatus
    message: str


class CrawlRequest(BaseModel):
    url: str
    source_type: Optional[str] = None   # SourceType value string
    application_year: Optional[int] = None
    tags: Optional[List[str]] = None
    institution_hint: Optional[str] = None
    force_recrawl: bool = False


class RawDocumentOut(BaseModel):
    id: int
    url: Optional[str]
    file_path: Optional[str]
    file_hash: str
    doc_type: DocType
    source_type: SourceType
    title: Optional[str]
    published_at: Optional[datetime]
    crawled_at: datetime
    parse_status: ParseStatus
    parse_error: Optional[str]
    language: Language
    application_year: Optional[int]
    credibility_score: float
    is_expired: bool
    tags: Optional[List[str]]
    institution_hint: Optional[str]

    class Config:
        from_attributes = True


class ExtractedFactOut(BaseModel):
    id: int
    document_id: int
    fact_type: FactType
    subject_school: Optional[str]
    subject_department: Optional[str]
    subject_program: Optional[str]
    subject_advisor: Optional[str]
    fact_key: str
    fact_value: str
    fact_value_structured: Optional[Any]
    confidence: float
    effective_year: Optional[int]
    extracted_at: datetime
    extraction_method: ExtractionMethod
    raw_excerpt: str
    is_superseded: bool

    class Config:
        from_attributes = True
