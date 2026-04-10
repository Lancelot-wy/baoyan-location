import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, Date,
    ForeignKey, Enum as SAEnum, ARRAY, UniqueConstraint, event
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class SchoolTier(str, enum.Enum):
    S985 = "985"
    S211 = "211"
    SHUANGFEI = "双非"
    OTHER = "其他"


class MajorCategory(str, enum.Enum):
    CS = "计算机科学与技术"
    SE = "软件工程"
    AI = "人工智能"
    DS = "数据科学"
    EE = "电子信息"
    MATH = "数学"
    PHYSICS = "物理"
    OTHER = "其他"


class CurrentYear(str, enum.Enum):
    THIRD = "大三"
    FOURTH = "大四"
    GRADUATED = "已毕业"


class EnglishReadingLevel(str, enum.Enum):
    BASIC = "基础"
    CAN_READ = "可阅读英文文献"
    FLUENT = "流利"


class ResearchOrientation(str, enum.Enum):
    RESEARCH = "偏科研"
    ENGINEERING = "偏工程"
    BALANCED = "均衡"


class UserRole(str, enum.Enum):
    OBSERVER = "旁观"
    ASSISTANT = "辅助"
    MODULE = "独立模块"
    LEAD = "主负责"


class VenueLevel(str, enum.Enum):
    CCF_A = "CCF-A"
    CCF_B = "CCF-B"
    CCF_C = "CCF-C"
    SCI = "SCI"
    EI = "EI"
    TOP_CONF = "顶会"
    JOURNAL = "普通期刊"
    UNDER_REVIEW = "在投"
    OTHER = "其他"


class PaperStatus(str, enum.Enum):
    PUBLISHED = "已发表"
    UNDER_REVIEW = "在投"
    IN_PROGRESS = "在写"


class CompetitionCategory(str, enum.Enum):
    ACM = "ACM"
    MATH_MODEL = "数学建模"
    INFO_SECURITY = "信息安全"
    ML = "机器学习"
    DATA_MINING = "数据挖掘"
    OTHER = "其他"


class CompetitionLevel(str, enum.Enum):
    INTERNATIONAL = "国际"
    NATIONAL = "国家"
    PROVINCIAL = "省级"
    SCHOOL = "校级"


class CompetitionAward(str, enum.Enum):
    GOLD = "金"
    SILVER = "银"
    BRONZE = "铜"
    FIRST = "一等"
    SECOND = "二等"
    THIRD = "三等"
    EXCELLENT = "优秀"
    PARTICIPATED = "参与"


class Relevance(str, enum.Enum):
    HIGH = "高度相关"
    PARTIAL = "部分相关"
    LOW = "不相关"


class CareerGoal(str, enum.Enum):
    EMPLOYMENT = "就业"
    PHD = "读博"
    GOVERNMENT = "考公"
    SELECTION = "选调"
    ABROAD = "出国"
    UNDECIDED = "未定"


class RiskAppetite(str, enum.Enum):
    REACH = "冲刺"
    BALANCED = "稳健"
    SAFE = "保守"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True,
                                             default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                  onupdate=func.now())

    # School info
    undergraduate_school: Mapped[str] = mapped_column(String(100), nullable=False)
    school_tier: Mapped[SchoolTier] = mapped_column(SAEnum(SchoolTier), nullable=False)
    major_name: Mapped[str] = mapped_column(String(100), nullable=False)
    major_category: Mapped[MajorCategory] = mapped_column(SAEnum(MajorCategory), nullable=False)
    current_year: Mapped[CurrentYear] = mapped_column(SAEnum(CurrentYear), nullable=False)
    has_guaranteed_admission: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Academic performance
    gpa: Mapped[float] = mapped_column(Float, nullable=False)
    gpa_full: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    major_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    major_rank_total: Mapped[int] = mapped_column(Integer, nullable=False)
    rank_percentile: Mapped[float] = mapped_column(Float, nullable=False)  # computed: rank/total
    comprehensive_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comprehensive_rank_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Disciplinary
    has_disciplinary_issues: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disciplinary_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # English
    cet4_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cet6_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ielts_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    toefl_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    english_reading_level: Mapped[EnglishReadingLevel] = mapped_column(
        SAEnum(EnglishReadingLevel), nullable=False, default=EnglishReadingLevel.BASIC
    )

    # Orientation
    research_orientation: Mapped[ResearchOrientation] = mapped_column(
        SAEnum(ResearchOrientation), nullable=False, default=ResearchOrientation.BALANCED
    )

    # Relationships
    research_experiences: Mapped[List["ResearchExperience"]] = relationship(
        "ResearchExperience", back_populates="user", cascade="all, delete-orphan"
    )
    papers: Mapped[List["Paper"]] = relationship(
        "Paper", back_populates="user", cascade="all, delete-orphan"
    )
    competitions: Mapped[List["Competition"]] = relationship(
        "Competition", back_populates="user", cascade="all, delete-orphan"
    )
    internships: Mapped[List["Internship"]] = relationship(
        "Internship", back_populates="user", cascade="all, delete-orphan"
    )
    preference: Mapped[Optional["PreferenceProfile"]] = relationship(
        "PreferenceProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    recommendation_sessions: Mapped[List["RecommendationSession"]] = relationship(
        "RecommendationSession", back_populates="user", cascade="all, delete-orphan"
    )


class ResearchExperience(Base):
    __tablename__ = "research_experiences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    advisor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    advisor_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    advisor_institution: Mapped[str] = mapped_column(String(100), nullable=False)
    research_direction: Mapped[str] = mapped_column(String(200), nullable=False)
    is_long_term: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    user_role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False)
    has_advisor_endorsement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="research_experiences")


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    venue: Mapped[str] = mapped_column(String(200), nullable=False)
    venue_level: Mapped[VenueLevel] = mapped_column(SAEnum(VenueLevel), nullable=False)
    status: Mapped[PaperStatus] = mapped_column(SAEnum(PaperStatus), nullable=False)
    author_position: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_authors: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_first_author: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # computed
    research_direction: Mapped[str] = mapped_column(String(200), nullable=False)
    actual_contribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    has_open_source: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paper_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="papers")


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[CompetitionCategory] = mapped_column(SAEnum(CompetitionCategory), nullable=False)
    level: Mapped[CompetitionLevel] = mapped_column(SAEnum(CompetitionLevel), nullable=False)
    award: Mapped[CompetitionAward] = mapped_column(SAEnum(CompetitionAward), nullable=False)
    is_team: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    team_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    relevance_to_application: Mapped[Relevance] = mapped_column(SAEnum(Relevance), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="competitions")


class Internship(Base):
    __tablename__ = "internships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_ongoing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    relevance: Mapped[Relevance] = mapped_column(SAEnum(Relevance), nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # computed
    is_research_type: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="internships")


class PreferenceProfile(Base):
    __tablename__ = "preference_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), nullable=False, unique=True)

    career_goal: Mapped[CareerGoal] = mapped_column(SAEnum(CareerGoal), nullable=False)
    risk_appetite: Mapped[RiskAppetite] = mapped_column(SAEnum(RiskAppetite), nullable=False)
    accept_high_pressure_advisor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prioritize_city: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prioritize_school_brand: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prioritize_internship_resources: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    prioritize_phd_track: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    accept_cross_direction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    preferred_cities: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    excluded_cities: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    care_about_living_cost: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    care_about_internet_industry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    accept_remote_study: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    target_directions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="preference")
