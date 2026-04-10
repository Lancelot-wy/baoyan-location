"""
Student profile builder: converts raw UserProfile DB objects into normalized
feature tags used downstream by the ranker and case retriever.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import date

from app.models.user import (
    UserProfile, ResearchExperience, Paper, Competition, Internship,
    PreferenceProfile, VenueLevel, CompetitionLevel, CompetitionAward,
    SchoolTier, CareerGoal, RiskAppetite, UserRole,
)
from app.core.constants import SCHOOL_TIER_ORDER, CURRENT_YEAR


@dataclass
class StudentTags:
    """Normalized, comparable representation of a student's profile."""

    # ── Identity ──────────────────────────────────────────────────────────────
    session_id: str
    undergraduate_school: str
    school_tier: str              # "985" / "211" / "双非" / "其他"
    school_tier_score: int        # 3/2/1/0

    # ── Academic ─────────────────────────────────────────────────────────────
    gpa_normalized: float         # gpa / gpa_full ∈ [0, 1]
    rank_percentile: float        # rank / total ∈ [0, 1], lower=better
    has_disciplinary_issues: bool

    # ── Research ─────────────────────────────────────────────────────────────
    research_strength: str        # "strong" / "moderate" / "weak" / "none"
    research_months: int          # total months across all experiences
    has_advisor_endorsement: bool
    max_research_role: str        # highest role across all experiences

    # ── Papers ──────────────────────────────────────────────────────────────
    paper_strength: str           # "top" / "good" / "basic" / "none"
    best_paper_level: Optional[str]   # e.g. "CCF-A"
    has_first_author_paper: bool
    paper_count: int

    # ── Competitions ────────────────────────────────────────────────────────
    competition_strength: str     # "top" / "good" / "basic" / "none"
    best_competition_level: Optional[str]  # "国际" / "国家" / "省级" / "校级"
    best_competition_award: Optional[str]

    # ── Engineering ─────────────────────────────────────────────────────────
    has_internship: bool
    has_research_internship: bool
    internship_company_tier: str  # "top" / "good" / "other" / "none"
    internship_months: int

    # ── English ─────────────────────────────────────────────────────────────
    cet6_score: Optional[int]
    english_level: str            # "high" / "medium" / "basic"

    # ── Preferences ─────────────────────────────────────────────────────────
    career_goal: str
    risk_appetite: str
    preferred_cities: List[str]
    excluded_cities: List[str]
    target_directions: List[str]
    prioritize_school_brand: bool
    prioritize_city: bool
    prioritize_internship_resources: bool
    prioritize_phd_track: bool
    accept_high_pressure_advisor: bool
    accept_cross_direction: bool

    # ── Composite scores ─────────────────────────────────────────────────────
    overall_strength: float       # 0-100 composite score


# ─── Scoring helpers ──────────────────────────────────────────────────────────

PAPER_LEVEL_SCORE: Dict[str, int] = {
    "CCF-A": 10, "顶会": 9, "CCF-B": 7, "SCI": 6,
    "CCF-C": 5, "EI": 4, "普通期刊": 3, "在投": 2, "其他": 1,
}

COMPETITION_LEVEL_SCORE: Dict[str, int] = {
    "国际": 4, "国家": 3, "省级": 2, "校级": 1,
}

COMPETITION_AWARD_SCORE: Dict[str, int] = {
    "金": 5, "一等": 4, "银": 3, "二等": 3,
    "铜": 2, "三等": 2, "优秀": 1, "参与": 0,
}

TOP_INTERNSHIP_COMPANIES = {
    "google", "microsoft", "apple", "meta", "amazon", "bytedance", "字节跳动",
    "tencent", "腾讯", "alibaba", "阿里", "huawei", "华为", "baidu", "百度",
    "didi", "滴滴", "meituan", "美团", "jd", "京东", "netease", "网易",
    "microsoft research", "deepmind", "openai",
}

GOOD_INTERNSHIP_COMPANIES = {
    "ant", "蚂蚁", "xiaomi", "小米", "oppo", "vivo", "kuaishou", "快手",
    "bilibili", "b站", "zhihu", "知乎", "sina", "新浪", "sohu", "搜狐",
    "ctrip", "携程", "pinduoduo", "拼多多", "海康威视", "中兴", "联想",
}


def _compute_research_months(experiences: List[ResearchExperience]) -> int:
    total = 0
    today = date.today()
    for exp in experiences:
        end = exp.end_date or today
        delta = (end - exp.start_date).days
        total += max(0, delta // 30)
    return total


def _compute_paper_strength(papers: List[Paper]) -> tuple:
    """Returns (strength_label, best_level, has_first_author, count)."""
    if not papers:
        return "none", None, False, 0

    published = [p for p in papers if p.status.value == "已发表"]
    under_review = [p for p in papers if p.status.value == "在投"]
    all_papers = published + under_review

    if not all_papers:
        return "none", None, False, 0

    best_score = 0
    best_level = None
    has_first = any(p.is_first_author and p.status.value == "已发表" for p in papers)

    for p in all_papers:
        s = PAPER_LEVEL_SCORE.get(p.venue_level.value, 1)
        if s > best_score:
            best_score = s
            best_level = p.venue_level.value

    if best_score >= 9:  # CCF-A or 顶会
        strength = "top"
    elif best_score >= 6:  # CCF-B or SCI
        strength = "good"
    elif best_score >= 3:
        strength = "basic"
    else:
        strength = "basic"

    return strength, best_level, has_first, len(all_papers)


def _compute_competition_strength(competitions: List[Competition]) -> tuple:
    """Returns (strength_label, best_level, best_award)."""
    if not competitions:
        return "none", None, None

    best_composite = 0
    best_level = None
    best_award = None

    for c in competitions:
        level_score = COMPETITION_LEVEL_SCORE.get(c.level.value, 0)
        award_score = COMPETITION_AWARD_SCORE.get(c.award.value, 0)
        composite = level_score * 2 + award_score

        if composite > best_composite:
            best_composite = composite
            best_level = c.level.value
            best_award = c.award.value

    if best_composite >= 11:  # e.g. 国际金
        strength = "top"
    elif best_composite >= 7:  # e.g. 国家一等
        strength = "good"
    elif best_composite >= 4:
        strength = "basic"
    else:
        strength = "basic"

    return strength, best_level, best_award


def _compute_internship_tier(internships: List[Internship]) -> str:
    if not internships:
        return "none"
    for intern in internships:
        company_lower = intern.company.lower()
        if any(top in company_lower for top in TOP_INTERNSHIP_COMPANIES):
            return "top"
    for intern in internships:
        company_lower = intern.company.lower()
        if any(good in company_lower for good in GOOD_INTERNSHIP_COMPANIES):
            return "good"
    return "other"


def _compute_internship_months(internships: List[Internship]) -> int:
    total = 0
    today = date.today()
    for intern in internships:
        end = intern.end_date or today
        delta = (end - intern.start_date).days
        total += max(0, delta // 30)
    return total


def _compute_english_level(profile: UserProfile) -> str:
    if profile.ielts_score and profile.ielts_score >= 6.5:
        return "high"
    if profile.toefl_score and profile.toefl_score >= 90:
        return "high"
    if profile.cet6_score and profile.cet6_score >= 500:
        return "high"
    if profile.cet6_score and profile.cet6_score >= 425:
        return "medium"
    if profile.cet4_score and profile.cet4_score >= 500:
        return "medium"
    return "basic"


def _compute_max_role(experiences: List[ResearchExperience]) -> str:
    role_order = {"旁观": 0, "辅助": 1, "独立模块": 2, "主负责": 3}
    if not experiences:
        return "none"
    max_role = max(experiences, key=lambda e: role_order.get(e.user_role.value, 0))
    return max_role.user_role.value


def _compute_research_strength(months: int, has_endorsement: bool, max_role: str) -> str:
    role_score = {"主负责": 3, "独立模块": 2, "辅助": 1, "旁观": 0, "none": 0}
    role_val = role_score.get(max_role, 0)

    if months >= 12 and role_val >= 2:
        return "strong"
    elif months >= 6 and role_val >= 1:
        return "moderate"
    elif months >= 3:
        return "weak"
    elif months > 0:
        return "weak"
    return "none"


def _compute_overall_strength(tags: "StudentTags") -> float:
    """
    Compute a 0-100 composite score for overall academic strength.
    Weights: school(15) + rank(25) + research(20) + paper(20) + competition(10) + english(5) + internship(5)
    """
    score = 0.0

    # School tier (15 pts)
    school_map = {3: 15, 2: 10, 1: 5, 0: 2}
    score += school_map.get(tags.school_tier_score, 2)

    # Rank percentile (25 pts) — lower percentile = better rank = higher score
    # rank_percentile=0.05 → top 5% → 25 pts; rank_percentile=0.50 → top 50% → 12 pts
    score += max(0, 25 * (1 - tags.rank_percentile))

    # Research (20 pts)
    research_map = {"strong": 20, "moderate": 13, "weak": 7, "none": 0}
    score += research_map.get(tags.research_strength, 0)

    # Paper (20 pts)
    paper_map = {"top": 20, "good": 14, "basic": 8, "none": 0}
    score += paper_map.get(tags.paper_strength, 0)

    # Competition (10 pts)
    comp_map = {"top": 10, "good": 7, "basic": 4, "none": 0}
    score += comp_map.get(tags.competition_strength, 0)

    # English (5 pts)
    eng_map = {"high": 5, "medium": 3, "basic": 1}
    score += eng_map.get(tags.english_level, 1)

    # Internship (5 pts)
    intern_map = {"top": 5, "good": 3, "other": 2, "none": 0}
    score += intern_map.get(tags.internship_company_tier, 0)

    return round(min(100.0, score), 2)


def build_student_tags(
    profile: UserProfile,
    research_experiences: List[ResearchExperience],
    papers: List[Paper],
    competitions: List[Competition],
    internships: List[Internship],
    preferences: Optional[PreferenceProfile],
) -> StudentTags:
    """Convert raw ORM objects into a normalized StudentTags object."""

    paper_strength, best_paper_level, has_first_author, paper_count = _compute_paper_strength(papers)
    comp_strength, best_comp_level, best_comp_award = _compute_competition_strength(competitions)
    research_months = _compute_research_months(research_experiences)
    max_role = _compute_max_role(research_experiences)
    has_endorsement = any(e.has_advisor_endorsement for e in research_experiences)
    research_strength = _compute_research_strength(research_months, has_endorsement, max_role)
    intern_tier = _compute_internship_tier(internships)
    intern_months = _compute_internship_months(internships)
    english_level = _compute_english_level(profile)

    tags = StudentTags(
        session_id=profile.session_id,
        undergraduate_school=profile.undergraduate_school,
        school_tier=profile.school_tier.value,
        school_tier_score=SCHOOL_TIER_ORDER.get(profile.school_tier.value, 0),
        gpa_normalized=profile.gpa / max(profile.gpa_full, 1.0),
        rank_percentile=profile.rank_percentile,
        has_disciplinary_issues=profile.has_disciplinary_issues,
        research_strength=research_strength,
        research_months=research_months,
        has_advisor_endorsement=has_endorsement,
        max_research_role=max_role,
        paper_strength=paper_strength,
        best_paper_level=best_paper_level,
        has_first_author_paper=has_first_author,
        paper_count=paper_count,
        competition_strength=comp_strength,
        best_competition_level=best_comp_level,
        best_competition_award=best_comp_award,
        has_internship=len(internships) > 0,
        has_research_internship=any(i.is_research_type for i in internships),
        internship_company_tier=intern_tier,
        internship_months=intern_months,
        cet6_score=profile.cet6_score,
        english_level=english_level,
        career_goal=preferences.career_goal.value if preferences else "未定",
        risk_appetite=preferences.risk_appetite.value if preferences else "稳健",
        preferred_cities=preferences.preferred_cities or [] if preferences else [],
        excluded_cities=preferences.excluded_cities or [] if preferences else [],
        target_directions=preferences.target_directions or [] if preferences else [],
        prioritize_school_brand=preferences.prioritize_school_brand if preferences else False,
        prioritize_city=preferences.prioritize_city if preferences else False,
        prioritize_internship_resources=preferences.prioritize_internship_resources if preferences else False,
        prioritize_phd_track=preferences.prioritize_phd_track if preferences else False,
        accept_high_pressure_advisor=preferences.accept_high_pressure_advisor if preferences else False,
        accept_cross_direction=preferences.accept_cross_direction if preferences else False,
        overall_strength=0.0,  # computed below
    )

    tags.overall_strength = _compute_overall_strength(tags)
    return tags
