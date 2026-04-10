from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator

from app.models.user import (
    SchoolTier, MajorCategory, CurrentYear, EnglishReadingLevel,
    ResearchOrientation, UserRole, VenueLevel, PaperStatus,
    CompetitionCategory, CompetitionLevel, CompetitionAward, Relevance,
    CareerGoal, RiskAppetite
)


# ── ResearchExperience ──────────────────────────────────────────────────────

class ResearchExperienceCreate(BaseModel):
    start_date: date
    end_date: Optional[date] = None
    advisor_name: str
    advisor_title: Optional[str] = None
    advisor_institution: str
    research_direction: str
    is_long_term: bool = False
    user_role: UserRole
    has_advisor_endorsement: bool = False
    notes: Optional[str] = None


class ResearchExperienceOut(ResearchExperienceCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# ── Paper ──────────────────────────────────────────────────────────────────

class PaperCreate(BaseModel):
    title: str
    venue: str
    venue_level: VenueLevel
    status: PaperStatus
    author_position: int = Field(ge=1)
    total_authors: int = Field(ge=1)
    research_direction: str
    actual_contribution: Optional[str] = None
    has_open_source: bool = False
    paper_url: Optional[str] = None
    year: int


class PaperOut(PaperCreate):
    id: int
    user_id: int
    is_first_author: bool

    class Config:
        from_attributes = True


# ── Competition ────────────────────────────────────────────────────────────

class CompetitionCreate(BaseModel):
    name: str
    category: CompetitionCategory
    level: CompetitionLevel
    award: CompetitionAward
    is_team: bool = False
    team_size: Optional[int] = None
    user_role: Optional[str] = None
    relevance_to_application: Relevance
    year: int


class CompetitionOut(CompetitionCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# ── Internship ─────────────────────────────────────────────────────────────

class InternshipCreate(BaseModel):
    company: str
    position: str
    department: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    is_ongoing: bool = False
    relevance: Relevance
    is_research_type: bool = False
    notes: Optional[str] = None


class InternshipOut(InternshipCreate):
    id: int
    user_id: int
    duration_months: int

    class Config:
        from_attributes = True


# ── PreferenceProfile ──────────────────────────────────────────────────────

class PreferenceProfileCreate(BaseModel):
    career_goal: CareerGoal
    risk_appetite: RiskAppetite
    accept_high_pressure_advisor: bool = False
    prioritize_city: bool = False
    prioritize_school_brand: bool = False
    prioritize_internship_resources: bool = False
    prioritize_phd_track: bool = False
    accept_cross_direction: bool = False
    preferred_cities: Optional[List[str]] = None
    excluded_cities: Optional[List[str]] = None
    care_about_living_cost: bool = False
    care_about_internet_industry: bool = False
    accept_remote_study: bool = False
    target_directions: Optional[List[str]] = None
    notes: Optional[str] = None


class PreferenceProfileOut(PreferenceProfileCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# ── UserProfile ────────────────────────────────────────────────────────────

class UserProfileCreate(BaseModel):
    undergraduate_school: str
    school_tier: SchoolTier
    major_name: str
    major_category: MajorCategory
    current_year: CurrentYear
    has_guaranteed_admission: bool = False
    gpa: float = Field(ge=0)
    gpa_full: float = Field(ge=0, default=4.0)
    major_rank: int = Field(ge=1)
    major_rank_total: int = Field(ge=1)
    comprehensive_rank: Optional[int] = None
    comprehensive_rank_total: Optional[int] = None
    has_disciplinary_issues: bool = False
    disciplinary_notes: Optional[str] = None
    cet4_score: Optional[int] = None
    cet6_score: Optional[int] = None
    ielts_score: Optional[float] = None
    toefl_score: Optional[int] = None
    english_reading_level: EnglishReadingLevel = EnglishReadingLevel.BASIC
    research_orientation: ResearchOrientation = ResearchOrientation.BALANCED


class UserProfileUpdate(BaseModel):
    undergraduate_school: Optional[str] = None
    school_tier: Optional[SchoolTier] = None
    major_name: Optional[str] = None
    major_category: Optional[MajorCategory] = None
    current_year: Optional[CurrentYear] = None
    has_guaranteed_admission: Optional[bool] = None
    gpa: Optional[float] = None
    gpa_full: Optional[float] = None
    major_rank: Optional[int] = None
    major_rank_total: Optional[int] = None
    comprehensive_rank: Optional[int] = None
    comprehensive_rank_total: Optional[int] = None
    has_disciplinary_issues: Optional[bool] = None
    disciplinary_notes: Optional[str] = None
    cet4_score: Optional[int] = None
    cet6_score: Optional[int] = None
    ielts_score: Optional[float] = None
    toefl_score: Optional[int] = None
    english_reading_level: Optional[EnglishReadingLevel] = None
    research_orientation: Optional[ResearchOrientation] = None


class UserProfileOut(BaseModel):
    id: int
    session_id: str
    created_at: datetime
    updated_at: datetime
    undergraduate_school: str
    school_tier: SchoolTier
    major_name: str
    major_category: MajorCategory
    current_year: CurrentYear
    has_guaranteed_admission: bool
    gpa: float
    gpa_full: float
    major_rank: int
    major_rank_total: int
    rank_percentile: float
    comprehensive_rank: Optional[int]
    comprehensive_rank_total: Optional[int]
    has_disciplinary_issues: bool
    disciplinary_notes: Optional[str]
    cet4_score: Optional[int]
    cet6_score: Optional[int]
    ielts_score: Optional[float]
    toefl_score: Optional[int]
    english_reading_level: EnglishReadingLevel
    research_orientation: ResearchOrientation

    class Config:
        from_attributes = True
