"""
Program ranker: scores and categorizes each ProgramProfile for a given student.
Uses structured profile comparison (NOT black-box LLM) for the core ranking.
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import ProgramProfile
from app.services.recommendation.profile_builder import StudentTags
from app.services.recommendation.case_retriever import compute_success_rate
from app.core.constants import (
    SCHOOL_TIER_ORDER, TIER_REACH_MAX_SUCCESS_RATE,
    TIER_MAIN_MIN_SUCCESS_RATE, TIER_MAIN_MAX_SUCCESS_RATE,
    TIER_SAFE_MIN_SUCCESS_RATE, TOP_N_PROGRAMS, MIN_CASES_FOR_STATS,
)

logger = logging.getLogger(__name__)


@dataclass
class ScoredProgram:
    program: ProgramProfile
    compatibility_score: float        # 0-100
    admission_prob_low: float         # 0-1
    admission_prob_high: float        # 0-1
    tier: str                         # "冲刺" / "主申" / "保底"
    is_suitable_for_reach: bool
    is_suitable_for_safe: bool
    num_cases: int
    filter_reason: Optional[str]      # if filtered out, why
    career_fit_score: Optional[float]
    phd_fit_score: Optional[float]


def _passes_hard_filters(tags: StudentTags, program: ProgramProfile) -> Optional[str]:
    """
    Check hard disqualifying conditions.
    Returns None if passes, or a string reason if filtered.
    """
    # Disciplinary issue is a hard stop for almost all programs
    if tags.has_disciplinary_issues:
        return "申请人有纪律处分记录，可能影响所有院校的推免资格"

    # School tier preference — never hard-block, only affect scoring.
    # Even 双非 students CAN apply to 985 programs (just lower chance).
    # Hard-blocking would hide valid options.

    # Rank threshold hard filter (only apply if we have strong evidence)
    if program.rank_threshold_hint is not None and program.profile_confidence > 0.7:
        if tags.rank_percentile > program.rank_threshold_hint * 1.5:
            # Student rank is significantly worse than threshold
            return f"该项目排名要求约前{program.rank_threshold_hint*100:.0f}%，申请人约前{tags.rank_percentile*100:.0f}%，差距较大"

    # City exclusion
    if program.city and tags.excluded_cities:
        for city in tags.excluded_cities:
            if city in (program.city or ""):
                return f"申请人不接受{program.city}城市"

    return None


def _compute_compatibility(tags: StudentTags, program: ProgramProfile) -> float:
    """
    Compute compatibility score (0-100) between student and program.
    This is a transparent, rule-based computation.
    """
    score = 0.0

    # ─── Base: rank proximity (30 pts) ────────────────────────────────────────
    if program.rank_threshold_hint is not None:
        # How much better is the student than the threshold?
        # student percentile lower (better rank) than threshold → positive
        diff = program.rank_threshold_hint - tags.rank_percentile
        if diff >= 0.10:      # clearly above threshold
            score += 30
        elif diff >= 0:       # at threshold
            score += 20
        elif diff >= -0.10:   # slightly below
            score += 10
        else:                 # significantly below
            score += 3
    else:
        # No clear threshold: use overall strength as proxy
        score += min(30, tags.overall_strength * 0.30)

    # ─── School tier match (15 pts) ───────────────────────────────────────────
    if program.school_tier_preference:
        if tags.school_tier in program.school_tier_preference:
            score += 15
        else:
            # Partial credit if close
            student_score = SCHOOL_TIER_ORDER.get(tags.school_tier, 0)
            pref_scores = [SCHOOL_TIER_ORDER.get(t, 0) for t in program.school_tier_preference]
            min_pref = min(pref_scores)
            if student_score >= min_pref - 1:
                score += 7
    else:
        # No preference stated → give baseline
        score += 8

    # ─── Research fit (20 pts) ────────────────────────────────────────────────
    research_weight = program.research_weight or 0.5  # default moderate
    research_map = {"strong": 20, "moderate": 13, "weak": 7, "none": 0}
    research_pts = research_map.get(tags.research_strength, 0)
    score += research_pts * research_weight * (20 / max(research_map["strong"], 1))
    # Normalize so max is 20 pts
    score_from_research = research_pts * research_weight
    score += min(20, score_from_research)

    # ─── Paper fit (15 pts) ───────────────────────────────────────────────────
    paper_map = {"top": 15, "good": 10, "basic": 5, "none": 0}
    if program.paper_requirement_hint:
        # Program explicitly mentions paper requirement → weight higher
        score += paper_map.get(tags.paper_strength, 0)
    else:
        # Still gives partial credit
        score += paper_map.get(tags.paper_strength, 0) * 0.6

    # ─── Competition fit (10 pts) ─────────────────────────────────────────────
    comp_weight = program.competition_weight or 0.3
    comp_map = {"top": 10, "good": 7, "basic": 3, "none": 0}
    score += comp_map.get(tags.competition_strength, 0) * comp_weight

    # ─── Career fit bonus (5 pts) ─────────────────────────────────────────────
    if tags.career_goal == "读博" and program.phd_track_available:
        score += 5
    elif tags.career_goal == "就业" and program.avg_employment_quality in ("顶级", "优秀"):
        score += 5
    elif tags.career_goal == "就业" and program.industry_resources in ("丰富",):
        score += 3

    # ─── City preference bonus (5 pts) ────────────────────────────────────────
    if tags.prioritize_city and program.city:
        if program.city in tags.preferred_cities:
            score += 5

    return round(min(100.0, max(0.0, score)), 2)


def _compute_probability(
    compatibility: float,
    success_rate: float,
    num_cases: int,
) -> Tuple[float, float]:
    """
    Compute (low, high) admission probability range.
    Blends compatibility-based estimate with empirical success rate.
    """
    # Compatibility-based prior
    compat_prob = compatibility / 100.0

    if num_cases >= MIN_CASES_FOR_STATS:
        # Weight empirical data more as sample size grows
        empirical_weight = min(0.7, num_cases / 30)
        blended = success_rate * empirical_weight + compat_prob * (1 - empirical_weight)
    else:
        blended = compat_prob

    # Uncertainty band: wider when fewer cases or lower evidence confidence
    uncertainty = 0.15 if num_cases >= 10 else 0.25

    low = max(0.0, blended - uncertainty)
    high = min(1.0, blended + uncertainty)
    return round(low, 2), round(high, 2)


def _assign_tier(
    success_rate: float,
    num_cases: int,
    compatibility: float,
    risk_appetite: str,
) -> str:
    """Assign 冲刺/主申/保底 based on success rate and compatibility."""
    if num_cases < MIN_CASES_FOR_STATS:
        # Fall back to compatibility-based tier
        if compatibility >= 75:
            return "保底"
        elif compatibility >= 50:
            return "主申"
        else:
            return "冲刺"

    if success_rate < TIER_REACH_MAX_SUCCESS_RATE:
        return "冲刺"
    elif success_rate <= TIER_MAIN_MAX_SUCCESS_RATE:
        return "主申"
    else:
        return "保底"


def _compute_career_fit(tags: StudentTags, program: ProgramProfile) -> Optional[float]:
    """Employment career fit score 0-100."""
    if tags.career_goal not in ("就业",):
        return None

    score = 50.0
    quality_map = {"顶级": 30, "优秀": 20, "良好": 10, "一般": 0}
    score += quality_map.get(getattr(program.avg_employment_quality, "value", ""), 0)
    resource_map = {"丰富": 20, "一般": 10, "较少": 0}
    score += resource_map.get(getattr(program.industry_resources, "value", ""), 0)

    # City relevance
    if tags.preferred_cities and program.city:
        if program.city in tags.preferred_cities:
            score += 15
    return round(min(100, score), 1)


def _compute_phd_fit(tags: StudentTags, program: ProgramProfile) -> Optional[float]:
    """PhD track fit score 0-100."""
    if tags.career_goal not in ("读博",):
        return None

    score = 40.0
    if program.phd_track_available:
        score += 30
    research_map = {"strong": 30, "moderate": 20, "weak": 10, "none": 0}
    score += research_map.get(tags.research_strength, 0)
    return round(min(100, score), 1)


async def rank_programs(
    db: AsyncSession,
    tags: StudentTags,
    top_n: int = TOP_N_PROGRAMS,
) -> List[ScoredProgram]:
    """
    Score all programs against student tags, filter and sort.
    Returns top-N scored programs across all tiers.
    """
    stmt = select(ProgramProfile)
    result = await db.execute(stmt)
    all_programs = result.scalars().all()

    if not all_programs:
        logger.warning("No program profiles found in database. Seed data first.")
        return []

    scored: List[ScoredProgram] = []

    for program in all_programs:
        filter_reason = _passes_hard_filters(tags, program)
        if filter_reason:
            # Still include with low score so user can see why filtered
            scored.append(ScoredProgram(
                program=program,
                compatibility_score=0.0,
                admission_prob_low=0.0,
                admission_prob_high=0.1,
                tier="冲刺",
                is_suitable_for_reach=False,
                is_suitable_for_safe=False,
                num_cases=0,
                filter_reason=filter_reason,
                career_fit_score=None,
                phd_fit_score=None,
            ))
            continue

        compatibility = _compute_compatibility(tags, program)

        success_rate, num_cases = await compute_success_rate(
            db, tags,
            target_school=program.school,
            target_department=program.department,
        )

        prob_low, prob_high = _compute_probability(compatibility, success_rate, num_cases)

        tier = _assign_tier(
            success_rate=success_rate,
            num_cases=num_cases,
            compatibility=compatibility,
            risk_appetite=tags.risk_appetite,
        )

        scored.append(ScoredProgram(
            program=program,
            compatibility_score=compatibility,
            admission_prob_low=prob_low,
            admission_prob_high=prob_high,
            tier=tier,
            is_suitable_for_reach=(tier in ("冲刺",) and compatibility >= 35),
            is_suitable_for_safe=(tier in ("保底",) and compatibility >= 60),
            num_cases=num_cases,
            filter_reason=None,
            career_fit_score=_compute_career_fit(tags, program),
            phd_fit_score=_compute_phd_fit(tags, program),
        ))

    # Filter out filtered programs from main results, but keep track
    valid = [s for s in scored if s.filter_reason is None]
    # Sort: primary by tier priority, secondary by compatibility
    tier_order = {"冲刺": 0, "主申": 1, "保底": 2}
    valid.sort(key=lambda s: (tier_order.get(s.tier, 1), -s.compatibility_score))

    return valid[:top_n]
