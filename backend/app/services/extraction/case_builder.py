"""Build ApplicationCase objects from extracted facts of experience posts."""
import logging
from typing import Dict, Any, Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge import ApplicationCase, CaseType, CampResult, FinalDecision
from app.models.document import ExtractedFact, RawDocument
from app.services.extraction.fact_normalizer import normalize_school_name, normalize_program_type

logger = logging.getLogger(__name__)

CAMP_RESULT_MAP = {
    "优营": CampResult.EXCELLENT,
    "录取": CampResult.ADMITTED,
    "候补": CampResult.WAITLIST,
    "淘汰": CampResult.ELIMINATED,
    "未参加": CampResult.NOT_ATTENDED,
}

FINAL_DECISION_MAP = {
    "接受": FinalDecision.ACCEPTED,
    "放弃": FinalDecision.DECLINED,
    "未定": FinalDecision.UNDECIDED,
}


def _determine_case_type(got_offer: Optional[bool], camp_result: Optional[str]) -> CaseType:
    if got_offer is True:
        return CaseType.SUCCESS
    if got_offer is False:
        return CaseType.FAILURE
    if camp_result in ("优营", "录取"):
        return CaseType.SUCCESS
    if camp_result in ("淘汰",):
        return CaseType.FAILURE
    return CaseType.PARTIAL


def _parse_school_tier(tier_str: Optional[str]) -> str:
    if not tier_str:
        return "其他"
    tier_lower = tier_str.lower()
    if "985" in tier_lower:
        return "985"
    if "211" in tier_lower:
        return "211"
    if "双非" in tier_lower:
        return "双非"
    return "其他"


async def build_cases_from_facts(
    document: RawDocument,
    facts: List[Dict[str, Any]],
    db: AsyncSession,
) -> List[ApplicationCase]:
    """
    Build ApplicationCase objects from extracted facts of experience posts.
    Facts that have _applicant_background and _result data can be turned into cases.
    """
    cases = []

    # Group facts with applicant background + result data
    case_facts = [f for f in facts if f.get("_applicant_background") and f.get("_result")]

    if not case_facts:
        # Try to construct from offer_result facts
        offer_facts = [f for f in facts if f.get("fact_type") == "offer_result"]
        if not offer_facts:
            return []

        # Build a single aggregate case
        target_school = None
        target_dept = None
        target_advisor = None
        target_program_type = None
        target_direction = None
        got_offer = None
        camp_result_str = None

        for fact in offer_facts:
            if fact.get("subject_school"):
                target_school = normalize_school_name(fact["subject_school"])
            if fact.get("subject_department"):
                target_dept = fact["subject_department"]
            if fact.get("subject_advisor"):
                target_advisor = fact["subject_advisor"]
            if fact.get("subject_program"):
                target_program_type = normalize_program_type(fact["subject_program"])

            fk = fact.get("fact_key", "").lower()
            fv = fact.get("fact_value", "")
            if "offer" in fk or "录取" in fk:
                got_offer = "是" in fv or "true" in fv.lower() or "已录取" in fv
            if "camp_result" in fk or "营员" in fk:
                camp_result_str = fv

        if not target_school:
            return []

        case_type = _determine_case_type(got_offer, camp_result_str)
        camp_result_enum = CAMP_RESULT_MAP.get(camp_result_str)

        case = ApplicationCase(
            source_document_id=document.id,
            applicant_school=document.institution_hint or "未知",
            applicant_school_tier="其他",
            applicant_major="计算机相关",
            target_school=target_school,
            target_department=target_dept or "计算机学院",
            target_direction=target_direction,
            target_program_type=target_program_type,
            target_advisor=target_advisor,
            application_year=document.application_year or 2025,
            got_camp_invite=True if camp_result_enum else None,
            camp_result=camp_result_enum,
            final_offer=got_offer,
            case_type=case_type,
            credibility=document.credibility_score,
        )
        db.add(case)
        cases.append(case)
        return cases

    # Process each fact with background info
    for fact in case_facts:
        bg = fact["_applicant_background"]
        result = fact["_result"]

        applicant_school = bg.get("school") or "未知"
        applicant_tier = _parse_school_tier(bg.get("school_tier"))
        applicant_major = bg.get("major") or "计算机相关"

        try:
            rank_pct = float(bg["rank_percentile"]) if bg.get("rank_percentile") is not None else None
        except (ValueError, TypeError):
            rank_pct = None

        try:
            gpa_pct = float(bg["gpa_percentile"]) if bg.get("gpa_percentile") is not None else None
        except (ValueError, TypeError):
            gpa_pct = None

        target_school = normalize_school_name(fact.get("subject_school")) or "未知"
        target_dept = fact.get("subject_department") or "计算机学院"
        target_advisor = fact.get("subject_advisor")
        target_program_type = normalize_program_type(fact.get("subject_program"))

        got_offer_raw = result.get("final_offer")
        if isinstance(got_offer_raw, bool):
            got_offer = got_offer_raw
        elif isinstance(got_offer_raw, str):
            got_offer = got_offer_raw.lower() in ("true", "是", "yes")
        else:
            got_offer = None

        camp_result_str = result.get("camp_result")
        camp_result_enum = CAMP_RESULT_MAP.get(camp_result_str)

        got_camp_invite = result.get("got_camp_invite")
        if isinstance(got_camp_invite, str):
            got_camp_invite = got_camp_invite.lower() in ("true", "是", "yes")

        case_type = _determine_case_type(got_offer, camp_result_str)

        research_months = bg.get("research_months")
        try:
            research_months = int(research_months) if research_months else None
        except (ValueError, TypeError):
            research_months = None

        case = ApplicationCase(
            source_document_id=document.id,
            applicant_school=applicant_school,
            applicant_school_tier=applicant_tier,
            applicant_major=applicant_major,
            applicant_gpa_percentile=gpa_pct,
            applicant_rank_percentile=rank_pct,
            applicant_has_paper=bool(bg.get("has_paper")),
            applicant_paper_level=bg.get("paper_level"),
            applicant_competition_level=bg.get("competition_level"),
            applicant_has_internship=bool(bg.get("has_internship")),
            applicant_research_months=research_months,
            target_school=target_school,
            target_department=target_dept,
            target_direction=fact.get("subject_department"),  # direction fallback
            target_program_type=target_program_type,
            target_advisor=target_advisor,
            application_year=document.application_year or 2025,
            got_camp_invite=got_camp_invite,
            camp_result=camp_result_enum,
            final_offer=got_offer,
            case_type=case_type,
            credibility=document.credibility_score,
        )
        db.add(case)
        cases.append(case)

    await db.flush()
    return cases
