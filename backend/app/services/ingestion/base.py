from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class WebPageResult:
    url: str
    title: Optional[str]
    main_content: str
    published_date: Optional[datetime]
    author: Optional[str]
    institution: Optional[str]
    page_type: str  # "official" | "experience_post" | "advisor_page" | "department_page" | "lab_page" | "unknown"
    language: str   # "zh" | "en" | "mixed"
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PDFPageResult:
    page_number: int
    text: str
    tables: List[List[List[str]]] = field(default_factory=list)  # list of tables, each table is rows of cells


@dataclass
class PDFResult:
    file_path: str
    total_pages: int
    doc_type: str  # "recruitment_notice" | "program_guide" | "transcript" | "other"
    pages: List[PDFPageResult] = field(default_factory=list)
    full_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OCRResult:
    file_path: str
    raw_text: str
    confidence: float  # 0.0 - 1.0
    image_type: str    # "offer_letter" | "announcement" | "list" | "experience_screenshot" | "unknown"
    needs_review: bool = False
    language: str = "zh"
    blocks: List[Dict[str, Any]] = field(default_factory=list)  # word-level OCR blocks
