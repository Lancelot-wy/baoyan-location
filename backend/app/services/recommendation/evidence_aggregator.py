"""
Evidence aggregator: gathers and summarizes evidence for a specific program recommendation.
"""
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import ExtractedFact, Evidence, RawDocument
from app.models.knowledge import ProgramProfile, ApplicationCase

logger = logging.getLogger(__name__)


@dataclass
class EvidenceItem:
    fact_id: int
    fact_key: str
    fact_value: str
    raw_excerpt: str
    source_type: str
    credibility_score: float
    weight: float
    effective_year: Optional[int]
    document_url: Optional[str]
    document_title: Optional[str]


@dataclass
class AggregatedEvidence:
    program_key: str
    items: List[EvidenceItem]
    overall_evidence_strength: float   # 0-1
    strongest_item: Optional[EvidenceItem]
    num_sources: int
    years_covered: List[int]
    conflicts_detected: bool


async def aggregate_evidence_for_program(
    db: AsyncSession,
    school: str,
    department: str,
    direction: Optional[str] = None,
) -> AggregatedEvidence:
    """
    Gather all evidence relevant to a school/department/direction combination.
    """
    # Query facts for this program
    stmt = (
        select(ExtractedFact, Evidence, RawDocument)
        .join(Evidence, Evidence.fact_id == ExtractedFact.id)
        .join(RawDocument, RawDocument.id == ExtractedFact.document_id)
        .where(
            ExtractedFact.subject_school == school,
            ExtractedFact.subject_department == department,
            ExtractedFact.is_superseded == False,
        )
        .order_by(Evidence.weight.desc())
        .limit(50)
    )

    if direction:
        stmt = stmt.where(
            (ExtractedFact.subject_program == direction) |
            (ExtractedFact.subject_program == None)
        )

    result = await db.execute(stmt)
    rows = result.all()

    items: List[EvidenceItem] = []
    seen_fact_ids = set()
    years = set()

    for fact, evidence, doc in rows:
        if fact.id in seen_fact_ids:
            continue
        seen_fact_ids.add(fact.id)

        if fact.effective_year:
            years.add(fact.effective_year)

        items.append(EvidenceItem(
            fact_id=fact.id,
            fact_key=fact.fact_key,
            fact_value=fact.fact_value[:300],
            raw_excerpt=fact.raw_excerpt[:500],
            source_type=doc.source_type.value,
            credibility_score=evidence.credibility_score,
            weight=evidence.weight,
            effective_year=fact.effective_year,
            document_url=doc.url,
            document_title=doc.title,
        ))

    # Compute overall strength: weighted average of evidence weights
    if items:
        overall = sum(i.weight for i in items) / len(items)
        overall = min(1.0, overall)
        strongest = max(items, key=lambda i: i.weight)
    else:
        overall = 0.0
        strongest = None

    # Conflict detection: same fact_key with very different values
    conflicts = False
    key_values: dict = {}
    for item in items:
        if item.fact_key not in key_values:
            key_values[item.fact_key] = []
        key_values[item.fact_key].append(item.fact_value)

    for key, values in key_values.items():
        if len(set(values)) > 1:
            conflicts = True
            break

    # Count unique source documents
    unique_urls = {i.document_url for i in items if i.document_url}
    num_sources = len(unique_urls)

    program_key = f"{school}-{department}"
    if direction:
        program_key += f"-{direction}"

    return AggregatedEvidence(
        program_key=program_key,
        items=items,
        overall_evidence_strength=round(overall, 3),
        strongest_item=strongest,
        num_sources=num_sources,
        years_covered=sorted(years, reverse=True),
        conflicts_detected=conflicts,
    )


async def get_similar_cases_for_display(
    db: AsyncSession,
    school: str,
    department: str,
    limit: int = 5,
) -> List[ApplicationCase]:
    """Retrieve a sample of relevant historical cases for display."""
    stmt = (
        select(ApplicationCase)
        .where(
            ApplicationCase.target_school == school,
            ApplicationCase.target_department == department,
        )
        .order_by(ApplicationCase.application_year.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


def format_evidence_summary(evidence: AggregatedEvidence) -> str:
    """Format aggregated evidence into a human-readable summary."""
    if not evidence.items:
        return "暂无该项目的直接证据，建议参考官方网站获取最新信息。"

    parts = []

    # Report time coverage
    if evidence.years_covered:
        latest = evidence.years_covered[0]
        parts.append(f"最新证据来自 {latest} 年申请季")

    # Report source quality
    source_types = [i.source_type for i in evidence.items]
    has_official = "official_notice" in source_types or "department_page" in source_types
    has_experience = "experience_post" in source_types
    has_screenshot = "offer_screenshot" in source_types

    source_desc = []
    if has_official:
        source_desc.append("官方招生通知")
    if has_experience:
        source_desc.append("经验帖")
    if has_screenshot:
        source_desc.append("offer截图")

    if source_desc:
        parts.append(f"证据来源：{'/'.join(source_desc)}")

    # Key facts
    key_facts = []
    for item in evidence.items[:5]:
        key_facts.append(f"• {item.fact_key}：{item.fact_value[:100]}")

    if key_facts:
        parts.append("关键信息：\n" + "\n".join(key_facts))

    if evidence.conflicts_detected:
        parts.append("⚠️ 注意：不同来源存在矛盾信息，请以最新官方通知为准")

    strength_labels = {
        (0.0, 0.3): "证据较少，参考价值有限",
        (0.3, 0.6): "有一定证据支撑",
        (0.6, 0.8): "证据较充分",
        (0.8, 1.1): "证据充分，参考价值高",
    }
    for (low, high), label in strength_labels.items():
        if low <= evidence.overall_evidence_strength < high:
            parts.append(label)
            break

    return "；".join(parts) + "。" if parts else "无有效证据"
