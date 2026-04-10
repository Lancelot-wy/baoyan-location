from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.models.knowledge import (
    ProgramType, EmploymentQuality, IndustryResources, AdvisorStyle, CaseType, CampResult, FinalDecision
)


class ProgramProfileOut(BaseModel):
    id: int
    school: str
    department: str
    direction: str
    program_type: ProgramType
    canonical_name: str
    gpa_threshold_hint: Optional[float] = None
    rank_threshold_hint: Optional[float] = None
    school_tier_preference: Optional[List[str]] = None
    research_weight: Optional[float] = None
    competition_weight: Optional[float] = None
    internship_weight: Optional[float] = None
    paper_requirement_hint: Optional[str] = None
    has_written_exam: Optional[bool] = None
    has_machine_test: Optional[bool] = None
    has_group_interview: Optional[bool] = None
    phd_track_available: Optional[bool] = None
    avg_employment_quality: Optional[EmploymentQuality] = None
    industry_resources: Optional[IndustryResources] = None
    city: Optional[str] = None
    last_updated: datetime
    evidence_count: int
    profile_confidence: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ProgramProfileCreate(BaseModel):
    school: str
    department: str
    direction: str
    program_type: str
    gpa_threshold_hint: Optional[float] = None
    rank_threshold_hint: Optional[float] = None
    school_tier_preference: Optional[List[str]] = None
    research_weight: Optional[float] = None
    competition_weight: Optional[float] = None
    internship_weight: Optional[float] = None
    paper_requirement_hint: Optional[str] = None
    has_written_exam: Optional[bool] = None
    has_machine_test: Optional[bool] = None
    has_group_interview: Optional[bool] = None
    phd_track_available: Optional[bool] = None
    avg_employment_quality: Optional[EmploymentQuality] = None
    industry_resources: Optional[IndustryResources] = None
    city: Optional[str] = None
    notes: Optional[str] = None
    profile_confidence: Optional[float] = None


class AdvisorProfileOut(BaseModel):
    id: int
    name: str
    institution: str
    department: str
    title: Optional[str] = None
    research_directions: Optional[List[str]] = None
    lab_name: Optional[str] = None
    homepage_url: Optional[str] = None
    is_recruiting: Optional[bool] = None
    quota_hint: Optional[int] = None
    preferred_background: Optional[List[str]] = None
    advisor_style: Optional[AdvisorStyle] = None
    phd_track_ratio: Optional[float] = None
    last_updated: datetime
    evidence_count: int
    profile_confidence: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class AdvisorProfileCreate(BaseModel):
    name: str
    institution: str
    department: str
    title: Optional[str] = None
    research_directions: Optional[List[str]] = None
    lab_name: Optional[str] = None
    homepage_url: Optional[str] = None
    is_recruiting: Optional[bool] = None
    quota_hint: Optional[int] = None
    preferred_background: Optional[List[str]] = None
    advisor_style: Optional[str] = None
    phd_track_ratio: Optional[float] = None
    notes: Optional[str] = None


class ApplicationCaseOut(BaseModel):
    id: int
    applicant_school: str
    applicant_school_tier: str
    applicant_major: str
    applicant_gpa_percentile: Optional[float] = None
    applicant_rank_percentile: Optional[float] = None
    applicant_has_paper: bool
    applicant_paper_level: Optional[str] = None
    applicant_competition_level: Optional[str] = None
    applicant_has_internship: bool
    applicant_research_months: Optional[int] = None
    target_school: str
    target_department: str
    target_direction: Optional[str] = None
    target_program_type: Optional[str] = None
    target_advisor: Optional[str] = None
    application_year: int
    got_camp_invite: Optional[bool] = None
    camp_result: Optional[CampResult] = None
    final_offer: Optional[bool] = None
    final_decision: Optional[FinalDecision] = None
    case_type: CaseType
    credibility: float
    is_verified: bool
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationCaseCreate(BaseModel):
    applicant_school: str
    applicant_school_tier: str
    applicant_major: str
    applicant_gpa_percentile: Optional[float] = None
    applicant_rank_percentile: Optional[float] = None
    applicant_has_paper: bool = False
    applicant_paper_level: Optional[str] = None
    applicant_competition_level: Optional[str] = None
    applicant_has_internship: bool = False
    applicant_research_months: Optional[int] = None
    target_school: str
    target_department: str
    target_direction: Optional[str] = None
    target_program_type: Optional[str] = None
    target_advisor: Optional[str] = None
    application_year: int
    got_camp_invite: Optional[bool] = None
    camp_result: Optional[str] = None
    final_offer: Optional[bool] = None
    final_decision: Optional[str] = None
    case_type: str
    credibility: float = 0.5
    is_verified: bool = False
    notes: Optional[str] = None
