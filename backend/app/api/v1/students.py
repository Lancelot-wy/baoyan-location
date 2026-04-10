"""Student profile CRUD API endpoints."""
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.core.school_data import search_schools, get_school_tier, has_baoyan_qualification
from app.models.user import (
    UserProfile, ResearchExperience, Paper, Competition, Internship, PreferenceProfile
)
from app.schemas.student import (
    UserProfileCreate, UserProfileOut, UserProfileUpdate,
    ResearchExperienceCreate, ResearchExperienceOut,
    PaperCreate, PaperOut,
    CompetitionCreate, CompetitionOut,
    InternshipCreate, InternshipOut,
    PreferenceProfileCreate, PreferenceProfileOut,
)

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/schools/search")
async def search_school(q: str = "", limit: int = 10):
    """Search schools by name, returns tier and baoyan qualification."""
    results = search_schools(q, limit)
    return results


@router.get("/schools/check/{school_name}")
async def check_school(school_name: str):
    """Check a school's tier and baoyan qualification."""
    tier = get_school_tier(school_name)
    has_baoyan = has_baoyan_qualification(school_name)
    return {
        "name": school_name,
        "tier": tier,
        "has_baoyan": has_baoyan,
        "warning": None if has_baoyan else f"「{school_name}」可能不在教育部推免资格高校名单中，请确认您的学校是否具有保研推免资格。",
    }


def _compute_rank_percentile(rank: int, total: int) -> float:
    if total <= 0:
        return 0.5
    return round(rank / total, 4)


@router.post("/", response_model=UserProfileOut, status_code=status.HTTP_201_CREATED)
async def create_student_profile(
    data: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new student profile. Returns session_id for subsequent requests."""
    rank_percentile = _compute_rank_percentile(data.major_rank, data.major_rank_total)

    profile = UserProfile(
        session_id=str(uuid.uuid4()),
        undergraduate_school=data.undergraduate_school,
        school_tier=data.school_tier,
        major_name=data.major_name,
        major_category=data.major_category,
        current_year=data.current_year,
        has_guaranteed_admission=data.has_guaranteed_admission,
        gpa=data.gpa,
        gpa_full=data.gpa_full,
        major_rank=data.major_rank,
        major_rank_total=data.major_rank_total,
        rank_percentile=rank_percentile,
        comprehensive_rank=data.comprehensive_rank,
        comprehensive_rank_total=data.comprehensive_rank_total,
        has_disciplinary_issues=data.has_disciplinary_issues,
        disciplinary_notes=data.disciplinary_notes,
        cet4_score=data.cet4_score,
        cet6_score=data.cet6_score,
        ielts_score=data.ielts_score,
        toefl_score=data.toefl_score,
        english_reading_level=data.english_reading_level,
        research_orientation=data.research_orientation,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)
    return profile


@router.get("/{session_id}", response_model=UserProfileOut)
async def get_student_profile(session_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(session_id, db)
    return profile


@router.put("/{session_id}", response_model=UserProfileOut)
async def update_student_profile(
    session_id: str,
    data: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile_or_404(session_id, db)

    update_data = data.model_dump(exclude_unset=True)
    if "major_rank" in update_data or "major_rank_total" in update_data:
        rank = update_data.get("major_rank", profile.major_rank)
        total = update_data.get("major_rank_total", profile.major_rank_total)
        update_data["rank_percentile"] = _compute_rank_percentile(rank, total)

    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)
    return profile


@router.post("/{session_id}/research", response_model=ResearchExperienceOut, status_code=201)
async def add_research_experience(
    session_id: str,
    data: ResearchExperienceCreate,
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile_or_404(session_id, db)
    exp = ResearchExperience(user_id=profile.id, **data.model_dump())
    db.add(exp)
    await db.flush()
    await db.refresh(exp)
    return exp


@router.get("/{session_id}/research", response_model=List[ResearchExperienceOut])
async def list_research_experiences(session_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(ResearchExperience).where(ResearchExperience.user_id == profile.id)
    )
    return result.scalars().all()


@router.delete("/{session_id}/research/{exp_id}", status_code=204)
async def delete_research_experience(
    session_id: str, exp_id: int, db: AsyncSession = Depends(get_db)
):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(ResearchExperience).where(
            ResearchExperience.id == exp_id,
            ResearchExperience.user_id == profile.id,
        )
    )
    exp = result.scalar_one_or_none()
    if not exp:
        raise HTTPException(404, "Research experience not found")
    await db.delete(exp)


@router.post("/{session_id}/papers", response_model=PaperOut, status_code=201)
async def add_paper(
    session_id: str,
    data: PaperCreate,
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile_or_404(session_id, db)
    paper_data = data.model_dump()
    paper_data["is_first_author"] = paper_data["author_position"] == 1
    paper = Paper(user_id=profile.id, **paper_data)
    db.add(paper)
    await db.flush()
    await db.refresh(paper)
    return paper


@router.get("/{session_id}/papers", response_model=List[PaperOut])
async def list_papers(session_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(select(Paper).where(Paper.user_id == profile.id))
    return result.scalars().all()


@router.delete("/{session_id}/papers/{paper_id}", status_code=204)
async def delete_paper(session_id: str, paper_id: int, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(Paper).where(Paper.id == paper_id, Paper.user_id == profile.id)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(404, "Paper not found")
    await db.delete(paper)


@router.post("/{session_id}/competitions", response_model=CompetitionOut, status_code=201)
async def add_competition(
    session_id: str,
    data: CompetitionCreate,
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile_or_404(session_id, db)
    comp = Competition(user_id=profile.id, **data.model_dump())
    db.add(comp)
    await db.flush()
    await db.refresh(comp)
    return comp


@router.get("/{session_id}/competitions", response_model=List[CompetitionOut])
async def list_competitions(session_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(Competition).where(Competition.user_id == profile.id)
    )
    return result.scalars().all()


@router.delete("/{session_id}/competitions/{comp_id}", status_code=204)
async def delete_competition(
    session_id: str, comp_id: int, db: AsyncSession = Depends(get_db)
):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(Competition).where(Competition.id == comp_id, Competition.user_id == profile.id)
    )
    comp = result.scalar_one_or_none()
    if not comp:
        raise HTTPException(404, "Competition not found")
    await db.delete(comp)


@router.post("/{session_id}/internships", response_model=InternshipOut, status_code=201)
async def add_internship(
    session_id: str,
    data: InternshipCreate,
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile_or_404(session_id, db)
    internship_data = data.model_dump()
    # Compute duration
    from datetime import date
    start = internship_data["start_date"]
    end = internship_data.get("end_date") or date.today()
    internship_data["duration_months"] = max(0, (end - start).days // 30)
    internship = Internship(user_id=profile.id, **internship_data)
    db.add(internship)
    await db.flush()
    await db.refresh(internship)
    return internship


@router.get("/{session_id}/internships", response_model=List[InternshipOut])
async def list_internships(session_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(Internship).where(Internship.user_id == profile.id)
    )
    return result.scalars().all()


@router.put("/{session_id}/preferences", response_model=PreferenceProfileOut)
async def upsert_preferences(
    session_id: str,
    data: PreferenceProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create or update preference profile."""
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(PreferenceProfile).where(PreferenceProfile.user_id == profile.id)
    )
    pref = result.scalar_one_or_none()

    if pref:
        for field, value in data.model_dump().items():
            setattr(pref, field, value)
    else:
        pref = PreferenceProfile(user_id=profile.id, **data.model_dump())
        db.add(pref)

    await db.flush()
    await db.refresh(pref)
    return pref


@router.get("/{session_id}/preferences", response_model=PreferenceProfileOut)
async def get_preferences(session_id: str, db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(session_id, db)
    result = await db.execute(
        select(PreferenceProfile).where(PreferenceProfile.user_id == profile.id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(404, "Preferences not set yet")
    return pref


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_profile_or_404(session_id: str, db: AsyncSession) -> UserProfile:
    result = await db.execute(
        select(UserProfile).where(UserProfile.session_id == session_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, f"Student profile not found: {session_id}")
    return profile
