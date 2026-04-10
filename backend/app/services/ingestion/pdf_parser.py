"""PDF parsing using pdfminer.six and tabula-py."""
import io
import logging
import re
from typing import List, Optional, Dict, Any

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTAnon, LTChar

from app.services.ingestion.base import PDFResult, PDFPageResult

logger = logging.getLogger(__name__)

RECRUITMENT_SIGNALS = [
    "招生简章", "招生通知", "接收推免生", "接收免试生", "招收推免",
    "夏令营", "预推免", "冬令营", "接收保研"
]

PROGRAM_GUIDE_SIGNALS = [
    "培养方案", "专业目录", "考试科目", "专业介绍", "学制", "学费"
]


def _classify_pdf_type(full_text: str) -> str:
    """Classify PDF document type based on content."""
    text_lower = full_text[:3000].lower()

    recruitment_count = sum(1 for s in RECRUITMENT_SIGNALS if s in full_text[:3000])
    guide_count = sum(1 for s in PROGRAM_GUIDE_SIGNALS if s in full_text[:3000])

    if recruitment_count >= 2:
        return "recruitment_notice"
    if guide_count >= 2:
        return "program_guide"

    # Check for transcript patterns
    if re.search(r'成绩单|学业成绩|transcript', full_text[:3000], re.IGNORECASE):
        return "transcript"

    return "other"


def _extract_page_text(page_layout) -> str:
    """Extract text from a pdfminer page layout object."""
    text_parts = []
    for element in page_layout:
        if isinstance(element, LTTextContainer):
            text_parts.append(element.get_text())
    return "".join(text_parts)


def _extract_tables_tabula(file_path: str, page_number: int) -> List[List[List[str]]]:
    """Extract tables from a specific page using tabula-py."""
    try:
        import tabula
        dfs = tabula.read_pdf(
            file_path,
            pages=page_number,
            multiple_tables=True,
            pandas_options={"header": None},
            silent=True,
        )
        tables = []
        for df in dfs:
            if df is not None and not df.empty:
                # Convert to list of rows
                rows = []
                for _, row in df.iterrows():
                    cells = [str(cell) if str(cell) != "nan" else "" for cell in row]
                    rows.append(cells)
                if rows:
                    tables.append(rows)
        return tables
    except Exception as e:
        logger.debug(f"Tabula extraction failed for page {page_number}: {e}")
        return []


def parse_pdf(file_path: str, extract_tables: bool = True) -> PDFResult:
    """
    Parse a PDF file and return structured PDFResult.
    Uses pdfminer.six for text extraction and tabula-py for tables.
    """
    pages_results: List[PDFPageResult] = []
    full_text_parts = []

    try:
        page_layouts = list(extract_pages(file_path))
    except Exception as e:
        logger.error(f"Failed to parse PDF {file_path}: {e}")
        return PDFResult(
            file_path=file_path,
            total_pages=0,
            doc_type="other",
            pages=[],
            full_text="",
            metadata={"error": str(e)},
        )

    total_pages = len(page_layouts)

    for page_num, page_layout in enumerate(page_layouts, start=1):
        page_text = _extract_page_text(page_layout)
        full_text_parts.append(page_text)

        # Extract tables (only for first 10 pages to avoid performance issues)
        tables = []
        if extract_tables and page_num <= 10:
            tables = _extract_tables_tabula(file_path, page_num)

        pages_results.append(PDFPageResult(
            page_number=page_num,
            text=page_text.strip(),
            tables=tables,
        ))

    full_text = "\n".join(full_text_parts)
    doc_type = _classify_pdf_type(full_text)

    return PDFResult(
        file_path=file_path,
        total_pages=total_pages,
        doc_type=doc_type,
        pages=pages_results,
        full_text=full_text.strip(),
        metadata={
            "total_chars": len(full_text),
            "pages_with_tables": sum(1 for p in pages_results if p.tables),
        },
    )
