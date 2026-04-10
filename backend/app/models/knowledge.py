from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Enum as SAEnum, ARRAY, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum

from app.db.base import Base
from app.core.constants import EMBEDDING_DIM


class ProgramType(str, enum.Enum):
    XUESHU = "学硕"
    ZHUANSHU = "专硕"
    ZHIBO = "直博"
    SUMMER_CAMP = "夏令营"
    PRE_ADMISSION = "预推免"
    WINTER_CAMP = "冬令营"


class EmploymentQuality(str, enum.Enum):
    TOP = "顶级"
    EXCELLENT = "优秀"
    GOOD = "良好"
    AVERAGE = "一般"


class IndustryResources(str, enum.Enum):
    RICH = "丰富"
    AVERAGE = "一般"
    FEW = "较少"


class AdvisorStyle(str, enum.Enum):
    RELAXED = "宽松"
    BALANCED = "均衡"
    STRICT = "严格"


class CampResult(str, enum.Enum):
    EXCELLENT = "优营"
    ADMITTED = "录取"
    WAITLIST = "候补"
    ELIMINATED = "淘汰"
    NOT_ATTENDED = "未参加"


class FinalDecision(str, enum.Enum):
    ACCEPTED = "接受"
    DECLINED = "放弃"
    UNDECIDED = "未定"


class CaseType(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class ProgramProfile(Base):
    __tablename__ = "program_profiles"
    __table_args__ = (
        UniqueConstraint("school", "department", "direction", "program_type", name="uq_program_canonical"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(200), nullable=False)
    direction: Mapped[str] = mapped_column(String(200), nullable=False)
    program_type: Mapped[ProgramType] = mapped_column(SAEnum(ProgramType), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(500), nullable=False)

    # Thresholds from evidence
    gpa_threshold_hint: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank_threshold_hint: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # percentile 0-1
    school_tier_preference: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Preferences
    research_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    competition_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    internship_weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    paper_requirement_hint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    has_written_exam: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_machine_test: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    has_group_interview: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Outcomes
    phd_track_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    avg_employment_quality: Mapped[Optional[EmploymentQuality]] = mapped_column(
        SAEnum(EmploymentQuality), nullable=True
    )
    industry_resources: Mapped[Optional[IndustryResources]] = mapped_column(
        SAEnum(IndustryResources), nullable=True
    )
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 强com/弱com标识
    # 强com: 主要看硬指标（排名、绩点、院校层次），海选式筛选
    # 弱com: 更看综合素质（科研、论文、陶瓷），导师话语权大
    admission_style: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "强com" / "弱com" / "混合"
    admission_style_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 具体说明

    # Meta
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    profile_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    profile_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    results: Mapped[List["RecommendationResult"]] = relationship(
        "RecommendationResult", back_populates="program"
    )


class AdvisorProfile(Base):
    __tablename__ = "advisor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    institution: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    research_directions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    lab_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Recruitment signals
    is_recruiting: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    quota_hint: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preferred_background: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    advisor_style: Mapped[Optional[AdvisorStyle]] = mapped_column(SAEnum(AdvisorStyle), nullable=True)
    phd_track_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Meta
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    profile_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    results: Mapped[List["RecommendationResult"]] = relationship(
        "RecommendationResult", back_populates="advisor"
    )


class ApplicationCase(Base):
    __tablename__ = "application_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_document_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("raw_documents.id"), nullable=True
    )

    # Applicant profile (anonymized)
    applicant_school: Mapped[str] = mapped_column(String(100), nullable=False)
    applicant_school_tier: Mapped[str] = mapped_column(String(20), nullable=False)
    applicant_major: Mapped[str] = mapped_column(String(100), nullable=False)
    applicant_gpa_percentile: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    applicant_rank_percentile: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    applicant_has_paper: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    applicant_paper_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    applicant_competition_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    applicant_has_internship: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    applicant_research_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Application result
    target_school: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_department: Mapped[str] = mapped_column(String(200), nullable=False)
    target_direction: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    target_program_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_advisor: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    application_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    got_camp_invite: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    camp_result: Mapped[Optional[CampResult]] = mapped_column(SAEnum(CampResult), nullable=True)
    final_offer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    final_decision: Mapped[Optional[FinalDecision]] = mapped_column(SAEnum(FinalDecision), nullable=True)

    # Meta
    case_type: Mapped[CaseType] = mapped_column(SAEnum(CaseType), nullable=False)
    credibility: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    case_embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
