"""
Case retriever: finds similar historical application cases for a student profile.
Similarity is computed on: school_tier, rank_percentile, paper_level,
competition_level, research_months — all numeric, no embeddings required for MVP.
"""
import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.models.knowledge import ApplicationCase, CaseType
from app.services.recommendation.profile_builder import StudentTags
from app.core.constants import TOP_K_SIMILAR_CASES, SCHOOL_TIER_ORDER

logger = logging.getLogger(__name__)

PAPER_LEVEL_RANK = {
    "CCF-A": 6, "顶会": 5, "CCF-B": 4, "SCI": 3,
    "CCF-C": 2, "EI": 2, "普通期刊": 1, "在投": 1, "其他": 1,
}

COMP_LEVEL_RANK = {"国际": 4, "国家": 3, "省级": 2, "校级": 1}


def _case_similarity(tags: StudentTags, case: ApplicationCase) -> float:
    """
    Compute a similarity score [0, 1] between a student and a historical case.
    Higher = more similar background.
    """
    score = 0.0
    total_weight = 0.0

    # School tier match (weight 0.25)
    w = 0.25
    case_tier_score = SCHOOL_TIER_ORDER.get(case.applicant_school_tier, 0)
    tier_diff = abs(tags.school_tier_score - case_tier_score)
    tier_sim = max(0.0, 1.0 - tier_diff / 3.0)
    score += w * tier_sim
    total_weight += w

    # Rank percentile similarity (weight 0.30) — both lower = better
    w = 0.30
    if case.applicant_rank_percentile is not None:
        rank_diff = abs(tags.rank_percentile - case.applicant_rank_percentile)
        rank_sim = max(0.0, 1.0 - rank_diff / 0.5)  # within 50% is meaningful
        score += w * rank_sim
        total_weight += w

    # Paper level similarity (weight 0.20)
    w = 0.20
    student_paper_rank = PAPER_LEVEL_RANK.get(tags.best_paper_level or "", 0)
    if tags.paper_strength == "none":
        student_paper_rank = 0
    case_paper_rank = PAPER_LEVEL_RANK.get(case.applicant_paper_level or "", 0)
    if not case.applicant_has_paper:
        case_paper_rank = 0
    paper_diff = abs(student_paper_rank - case_paper_rank)
    paper_sim = max(0.0, 1.0 - paper_diff / 6.0)
    score += w * paper_sim
    total_weight += w

    # Competition level similarity (weight 0.15)
    w = 0.15
    student_comp_rank = COMP_LEVEL_RANK.get(tags.best_competition_level or "", 0)
    case_comp_rank = COMP_LEVEL_RANK.get(case.applicant_competition_level or "", 0)
    comp_diff = abs(student_comp_rank - case_comp_rank)
    comp_sim = max(0.0, 1.0 - comp_diff / 4.0)
    score += w * comp_sim
    total_weight += w

    # Research months similarity (weight 0.10)
    w = 0.10
    if case.applicant_research_months is not None:
        res_diff = abs(tags.research_months - case.applicant_research_months)
        res_sim = max(0.0, 1.0 - res_diff / 24.0)  # normalize over 24 months
        score += w * res_sim
        total_weight += w

    if total_weight == 0:
        return 0.0
    return score / total_weight


async def retrieve_similar_cases(
    db: AsyncSession,
    tags: StudentTags,
    target_school: str = None,
    target_department: str = None,
    top_k: int = TOP_K_SIMILAR_CASES,
) -> List[Tuple[ApplicationCase, float]]:
    """
    Retrieve top-K most similar ApplicationCases, optionally filtered by target.
    Returns list of (case, similarity_score) tuples, sorted desc by similarity.
    """
    stmt = select(ApplicationCase)

    if target_school:
        stmt = stmt.where(ApplicationCase.target_school == target_school)
    if target_department:
        stmt = stmt.where(ApplicationCase.target_department == target_department)

    result = await db.execute(stmt)
    all_cases = result.scalars().all()

    if not all_cases:
        return []

    scored = [(case, _case_similarity(tags, case)) for case in all_cases]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


async def compute_success_rate(
    db: AsyncSession,
    tags: StudentTags,
    target_school: str,
    target_department: str,
    min_similarity: float = 0.4,
) -> Tuple[float, int]:
    """
    Compute admission success rate from similar historical cases for a specific program.
    Returns (success_rate, num_cases_considered).
    """
    cases_with_scores = await retrieve_similar_cases(
        db, tags, target_school=target_school,
        target_department=target_department, top_k=50
    )

    # Filter by minimum similarity
    relevant = [(c, s) for c, s in cases_with_scores if s >= min_similarity]

    if not relevant:
        return 0.5, 0  # Unknown — return neutral prior

    total = len(relevant)
    successes = sum(
        1 for c, _ in relevant
        if c.final_offer is True or c.case_type.value == "success"
    )

    success_rate = successes / total
    return success_rate, total
