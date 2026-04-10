"""Conflict detection: identify contradicting facts and resolve them."""
import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import ExtractedFact

logger = logging.getLogger(__name__)


async def detect_conflicts(
    db: AsyncSession,
    new_fact: ExtractedFact,
) -> List[ExtractedFact]:
    """
    Find existing facts that potentially conflict with the new fact.
    Conflict: same subject (school+dept+program+advisor) + same fact_key, different value.
    """
    if not new_fact.subject_school:
        return []

    stmt = select(ExtractedFact).where(
        ExtractedFact.id != new_fact.id,
        ExtractedFact.subject_school == new_fact.subject_school,
        ExtractedFact.fact_key == new_fact.fact_key,
        ExtractedFact.is_superseded == False,
    )

    if new_fact.subject_department:
        stmt = stmt.where(ExtractedFact.subject_department == new_fact.subject_department)
    if new_fact.subject_program:
        stmt = stmt.where(ExtractedFact.subject_program == new_fact.subject_program)

    result = await db.execute(stmt)
    candidates = result.scalars().all()

    conflicts = []
    for existing in candidates:
        if existing.fact_value.strip() != new_fact.fact_value.strip():
            conflicts.append(existing)

    return conflicts


async def resolve_conflict(
    db: AsyncSession,
    old_fact: ExtractedFact,
    new_fact: ExtractedFact,
) -> None:
    """
    Resolve a conflict between two facts.
    Strategy: newer effective_year wins; if same year, higher confidence wins.
    The loser is marked as superseded.
    """
    old_year = old_fact.effective_year or 0
    new_year = new_fact.effective_year or 0

    if new_year > old_year:
        # New fact supersedes old
        old_fact.is_superseded = True
        old_fact.superseded_by = new_fact.id
        logger.info(
            f"Fact {old_fact.id} superseded by {new_fact.id} "
            f"(year {old_year} → {new_year})"
        )
    elif new_year < old_year:
        # Old fact is more recent; mark new as superseded
        new_fact.is_superseded = True
        new_fact.superseded_by = old_fact.id
        logger.info(
            f"New fact {new_fact.id} superseded by older {old_fact.id} "
            f"(year {new_year} < {old_year})"
        )
    else:
        # Same year: higher confidence wins
        if new_fact.confidence >= old_fact.confidence:
            old_fact.is_superseded = True
            old_fact.superseded_by = new_fact.id
        else:
            new_fact.is_superseded = True
            new_fact.superseded_by = old_fact.id

    await db.flush()


async def process_new_fact_conflicts(
    db: AsyncSession,
    new_fact: ExtractedFact,
) -> int:
    """Detect and resolve all conflicts for a new fact. Returns number of conflicts resolved."""
    conflicts = await detect_conflicts(db, new_fact)
    for conflicting_fact in conflicts:
        await resolve_conflict(db, conflicting_fact, new_fact)
    return len(conflicts)
