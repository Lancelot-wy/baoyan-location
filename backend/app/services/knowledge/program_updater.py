"""Program profile updater: aggregates extracted facts into ProgramProfile."""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.knowledge import ProgramProfile, ProgramType
from app.models.document import ExtractedFact, FactType
from app.core.constants import SCHOOL_TIER_ORDER

logger = logging.getLogger(__name__)


async def get_or_create_program(
    db: AsyncSession,
    school: str,
    department: str,
    direction: str,
    program_type: str,
) -> ProgramProfile:
    """Get existing program profile or create a new one."""
    try:
        pt = ProgramType(program_type)
    except ValueError:
        pt = ProgramType.SUMMER_CAMP

    stmt = select(ProgramProfile).where(
        ProgramProfile.school == school,
        ProgramProfile.department == department,
        ProgramProfile.direction == direction,
        ProgramProfile.program_type == pt,
    )
    result = await db.execute(stmt)
    program = result.scalar_one_or_none()

    if not program:
        canonical = f"{school}-{department}-{direction}-{pt.value}"
        program = ProgramProfile(
            school=school,
            department=department,
            direction=direction,
            program_type=pt,
            canonical_name=canonical,
            evidence_count=0,
            profile_confidence=0.3,
        )
        db.add(program)
        await db.flush()

    return program


async def update_program_from_fact(
    db: AsyncSession,
    fact: ExtractedFact,
) -> Optional[ProgramProfile]:
    """
    Apply a single extracted fact to the corresponding ProgramProfile.
    Returns the updated profile, or None if not applicable.
    """
    if not fact.subject_school or not fact.subject_department:
        return None

    program = await get_or_create_program(
        db=db,
        school=fact.subject_school,
        department=fact.subject_department,
        direction=fact.subject_program or "通用",
        program_type=fact.subject_program or "夏令营",
    )

    updated = False

    if fact.fact_type == FactType.RANK_REQUIREMENT:
        if fact.fact_key in ("rank_top_percent", "rank_percentile") and fact.fact_value_structured:
            val = fact.fact_value_structured.get("rank_top_percent")
            if val is not None:
                # Convert top-N% to 0-1 percentile threshold
                threshold = float(val) / 100.0
                if program.rank_threshold_hint is None or fact.confidence > 0.7:
                    program.rank_threshold_hint = threshold
                    updated = True

        if fact.fact_key in ("school_tier", "school_tier_preference") and fact.fact_value_structured:
            tiers = fact.fact_value_structured.get("accepted_tiers", [])
            if tiers:
                program.school_tier_preference = tiers
                updated = True

    elif fact.fact_type == FactType.QUOTA:
        if fact.fact_value_structured:
            quota = fact.fact_value_structured.get("quota")
            if quota:
                # Store in notes since quota isn't a direct field
                existing_notes = program.notes or ""
                program.notes = f"{existing_notes}\n[招生名额:{quota}]".strip()
                updated = True

    elif fact.fact_type == FactType.DEADLINE:
        if fact.fact_value_structured:
            deadline = fact.fact_value_structured.get("deadline")
            if deadline:
                existing_notes = program.notes or ""
                program.notes = f"{existing_notes}\n[截止日期:{deadline}]".strip()
                updated = True

    elif fact.fact_type == FactType.INTERVIEW_FORMAT:
        if "笔试" in fact.fact_value or "written" in fact.fact_value.lower():
            program.has_written_exam = True
            updated = True
        if "机试" in fact.fact_value or "programming" in fact.fact_value.lower():
            program.has_machine_test = True
            updated = True
        if "群面" in fact.fact_value or "小组" in fact.fact_value:
            program.has_group_interview = True
            updated = True

    elif fact.fact_type == FactType.RESEARCH_PREFERENCE:
        if fact.fact_key == "research_weight":
            try:
                w = float(fact.fact_value)
                if 0 <= w <= 1:
                    program.research_weight = w
                    updated = True
            except ValueError:
                pass
        elif "论文" in fact.fact_key or "paper" in fact.fact_key.lower():
            program.paper_requirement_hint = fact.fact_value[:500]
            updated = True

    elif fact.fact_type == FactType.PROGRAM_DETAIL:
        if fact.fact_key == "phd_track":
            program.phd_track_available = fact.fact_value.lower() in ("true", "yes", "是", "有")
            updated = True
        elif fact.fact_key == "city":
            program.city = fact.fact_value[:50]
            updated = True
        elif "就业" in fact.fact_key or "employment" in fact.fact_key.lower():
            program.notes = f"{program.notes or ''}\n[就业:{fact.fact_value}]".strip()
            updated = True

    if updated:
        program.evidence_count = (program.evidence_count or 0) + 1
        # Increase confidence as more evidence accumulates (cap at 0.95)
        program.profile_confidence = min(0.95, 0.3 + program.evidence_count * 0.05)
        await db.flush()

    return program


async def bulk_update_programs_from_facts(
    db: AsyncSession,
    document_id: int,
) -> int:
    """Process all facts from a document and update program profiles. Returns count updated."""
    stmt = select(ExtractedFact).where(
        ExtractedFact.document_id == document_id,
        ExtractedFact.is_superseded == False,
    )
    result = await db.execute(stmt)
    facts = result.scalars().all()

    updated_count = 0
    for fact in facts:
        prog = await update_program_from_fact(db, fact)
        if prog:
            updated_count += 1

    return updated_count
