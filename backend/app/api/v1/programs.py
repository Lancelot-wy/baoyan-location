"""Program and advisor profile endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.deps import get_db
from app.models.knowledge import ProgramProfile, AdvisorProfile, ApplicationCase
from app.schemas.knowledge import ProgramProfileOut, AdvisorProfileOut, ApplicationCaseOut, ProgramProfileCreate, AdvisorProfileCreate, ApplicationCaseCreate

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("/", response_model=List[ProgramProfileOut])
async def list_programs(
    school: Optional[str] = None,
    city: Optional[str] = None,
    program_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ProgramProfile).offset(skip).limit(limit).order_by(ProgramProfile.school)
    if school:
        stmt = stmt.where(ProgramProfile.school.ilike(f"%{school}%"))
    if city:
        stmt = stmt.where(ProgramProfile.city == city)
    if program_type:
        stmt = stmt.where(ProgramProfile.program_type == program_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ProgramProfileOut, status_code=201)
async def create_program(data: ProgramProfileCreate, db: AsyncSession = Depends(get_db)):
    from app.models.knowledge import ProgramType
    try:
        pt = ProgramType(data.program_type)
    except ValueError:
        raise HTTPException(400, f"Invalid program_type: {data.program_type}")

    canonical = f"{data.school}-{data.department}-{data.direction}-{pt.value}"
    program = ProgramProfile(
        school=data.school,
        department=data.department,
        direction=data.direction,
        program_type=pt,
        canonical_name=canonical,
        gpa_threshold_hint=data.gpa_threshold_hint,
        rank_threshold_hint=data.rank_threshold_hint,
        school_tier_preference=data.school_tier_preference,
        research_weight=data.research_weight,
        competition_weight=data.competition_weight,
        internship_weight=data.internship_weight,
        paper_requirement_hint=data.paper_requirement_hint,
        has_written_exam=data.has_written_exam,
        has_machine_test=data.has_machine_test,
        has_group_interview=data.has_group_interview,
        phd_track_available=data.phd_track_available,
        avg_employment_quality=data.avg_employment_quality,
        industry_resources=data.industry_resources,
        city=data.city,
        notes=data.notes,
        evidence_count=0,
        profile_confidence=data.profile_confidence or 0.5,
    )
    db.add(program)
    await db.flush()
    await db.refresh(program)
    return program


@router.get("/{program_id}", response_model=ProgramProfileOut)
async def get_program(program_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProgramProfile).where(ProgramProfile.id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(404, "Program not found")
    return program


# ── Advisors ───────────────────────────────────────────────────────────────────

advisor_router = APIRouter(prefix="/advisors", tags=["advisors"])


@advisor_router.get("/", response_model=List[AdvisorProfileOut])
async def list_advisors(
    institution: Optional[str] = None,
    is_recruiting: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AdvisorProfile).offset(skip).limit(limit)
    if institution:
        stmt = stmt.where(AdvisorProfile.institution.ilike(f"%{institution}%"))
    if is_recruiting is not None:
        stmt = stmt.where(AdvisorProfile.is_recruiting == is_recruiting)
    result = await db.execute(stmt)
    return result.scalars().all()


@advisor_router.post("/", response_model=AdvisorProfileOut, status_code=201)
async def create_advisor(data: AdvisorProfileCreate, db: AsyncSession = Depends(get_db)):
    from app.models.knowledge import AdvisorStyle
    advisor = AdvisorProfile(
        name=data.name,
        institution=data.institution,
        department=data.department,
        title=data.title,
        research_directions=data.research_directions,
        lab_name=data.lab_name,
        homepage_url=data.homepage_url,
        is_recruiting=data.is_recruiting,
        quota_hint=data.quota_hint,
        preferred_background=data.preferred_background,
        advisor_style=AdvisorStyle(data.advisor_style) if data.advisor_style else None,
        phd_track_ratio=data.phd_track_ratio,
        evidence_count=0,
        profile_confidence=0.5,
        notes=data.notes,
    )
    db.add(advisor)
    await db.flush()
    await db.refresh(advisor)
    return advisor


@advisor_router.get("/{advisor_id}", response_model=AdvisorProfileOut)
async def get_advisor(advisor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdvisorProfile).where(AdvisorProfile.id == advisor_id))
    advisor = result.scalar_one_or_none()
    if not advisor:
        raise HTTPException(404, "Advisor not found")
    return advisor


# ── Cases ──────────────────────────────────────────────────────────────────────

cases_router = APIRouter(prefix="/cases", tags=["cases"])


@cases_router.get("/", response_model=List[ApplicationCaseOut])
async def list_cases(
    school: Optional[str] = None,
    year: Optional[int] = None,
    case_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ApplicationCase)
        .offset(skip)
        .limit(limit)
        .order_by(ApplicationCase.application_year.desc())
    )
    if school:
        stmt = stmt.where(ApplicationCase.target_school.ilike(f"%{school}%"))
    if year:
        stmt = stmt.where(ApplicationCase.application_year == year)
    if case_type:
        stmt = stmt.where(ApplicationCase.case_type == case_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@cases_router.post("/", response_model=ApplicationCaseOut, status_code=201)
async def create_case(data: ApplicationCaseCreate, db: AsyncSession = Depends(get_db)):
    from app.models.knowledge import CaseType, CampResult, FinalDecision
    case = ApplicationCase(
        applicant_school=data.applicant_school,
        applicant_school_tier=data.applicant_school_tier,
        applicant_major=data.applicant_major,
        applicant_gpa_percentile=data.applicant_gpa_percentile,
        applicant_rank_percentile=data.applicant_rank_percentile,
        applicant_has_paper=data.applicant_has_paper,
        applicant_paper_level=data.applicant_paper_level,
        applicant_competition_level=data.applicant_competition_level,
        applicant_has_internship=data.applicant_has_internship,
        applicant_research_months=data.applicant_research_months,
        target_school=data.target_school,
        target_department=data.target_department,
        target_direction=data.target_direction,
        target_program_type=data.target_program_type,
        target_advisor=data.target_advisor,
        application_year=data.application_year,
        got_camp_invite=data.got_camp_invite,
        camp_result=CampResult(data.camp_result) if data.camp_result else None,
        final_offer=data.final_offer,
        final_decision=FinalDecision(data.final_decision) if data.final_decision else None,
        case_type=CaseType(data.case_type),
        credibility=data.credibility,
        is_verified=data.is_verified,
        notes=data.notes,
    )
    db.add(case)
    await db.flush()
    await db.refresh(case)
    return case


@cases_router.get("/{case_id}", response_model=ApplicationCaseOut)
async def get_case(case_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApplicationCase).where(ApplicationCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(404, "Case not found")
    return case
