"""Advisor profile updater: aggregates advisor-related facts into AdvisorProfile."""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import AdvisorProfile, AdvisorStyle
from app.models.document import ExtractedFact, FactType

logger = logging.getLogger(__name__)


async def get_or_create_advisor(
    db: AsyncSession,
    name: str,
    institution: str,
    department: str,
) -> AdvisorProfile:
    stmt = select(AdvisorProfile).where(
        AdvisorProfile.name == name,
        AdvisorProfile.institution == institution,
    )
    result = await db.execute(stmt)
    advisor = result.scalar_one_or_none()

    if not advisor:
        advisor = AdvisorProfile(
            name=name,
            institution=institution,
            department=department,
            evidence_count=0,
            profile_confidence=0.3,
        )
        db.add(advisor)
        await db.flush()

    return advisor


async def update_advisor_from_fact(
    db: AsyncSession,
    fact: ExtractedFact,
) -> Optional[AdvisorProfile]:
    """Apply a single extracted fact to the corresponding AdvisorProfile."""
    if not fact.subject_advisor or not fact.subject_school:
        return None

    if fact.fact_type != FactType.ADVISOR_PREFERENCE:
        return None

    advisor = await get_or_create_advisor(
        db=db,
        name=fact.subject_advisor,
        institution=fact.subject_school,
        department=fact.subject_department or "未知",
    )

    updated = False
    structured = fact.fact_value_structured or {}

    # Update from structured data if available
    if structured:
        if structured.get("title") and not advisor.title:
            advisor.title = structured["title"]
            updated = True

        if structured.get("research_directions"):
            advisor.research_directions = structured["research_directions"]
            updated = True

        if structured.get("lab_name") and not advisor.lab_name:
            advisor.lab_name = structured["lab_name"]
            updated = True

        if structured.get("is_recruiting") is not None:
            advisor.is_recruiting = bool(structured["is_recruiting"])
            updated = True

        if structured.get("quota_hint") is not None:
            try:
                advisor.quota_hint = int(structured["quota_hint"])
                updated = True
            except (ValueError, TypeError):
                pass

        if structured.get("preferred_background"):
            advisor.preferred_background = structured["preferred_background"]
            updated = True

    # Update from key-value pair
    key = fact.fact_key.lower()
    val = fact.fact_value

    if key == "is_recruiting":
        advisor.is_recruiting = val.lower() in ("true", "yes", "是", "招生中")
        updated = True
    elif key == "advisor_style":
        style_map = {"宽松": "宽松", "严格": "严格", "均衡": "均衡",
                     "relaxed": "宽松", "strict": "严格", "balanced": "均衡"}
        mapped = style_map.get(val.lower(), val)
        try:
            advisor.advisor_style = AdvisorStyle(mapped)
            updated = True
        except ValueError:
            pass
    elif key == "phd_track_ratio":
        try:
            advisor.phd_track_ratio = float(val)
            updated = True
        except ValueError:
            pass
    elif key == "homepage_url" and not advisor.homepage_url:
        advisor.homepage_url = val[:500]
        updated = True
    elif key in ("lab_name", "research_group") and not advisor.lab_name:
        advisor.lab_name = val[:200]
        updated = True
    elif key == "research_directions":
        # val might be comma-separated
        dirs = [d.strip() for d in val.split(",") if d.strip()]
        if dirs:
            advisor.research_directions = dirs
            updated = True
    elif key == "title" and not advisor.title:
        advisor.title = val[:100]
        updated = True

    if updated:
        advisor.evidence_count = (advisor.evidence_count or 0) + 1
        advisor.profile_confidence = min(0.95, 0.3 + advisor.evidence_count * 0.065)
        await db.flush()

    return advisor
