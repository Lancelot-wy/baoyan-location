from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base


class SessionStatus(str, enum.Enum):
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class RecommendationTier(str, enum.Enum):
    REACH = "冲刺"
    MAIN = "主申"
    SAFE = "保底"


class ReasonType(str, enum.Enum):
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class RecommendationSession(Base):
    __tablename__ = "recommendation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus), nullable=False, default=SessionStatus.PROCESSING
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="recommendation_sessions")
    results: Mapped[List["RecommendationResult"]] = relationship(
        "RecommendationResult", back_populates="session", cascade="all, delete-orphan"
    )


class RecommendationResult(Base):
    __tablename__ = "recommendation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("recommendation_sessions.id"), nullable=False)
    program_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("program_profiles.id"), nullable=True)
    advisor_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("advisor_profiles.id"), nullable=True)

    school: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(200), nullable=False)
    direction: Mapped[str] = mapped_column(String(200), nullable=False)
    program_type: Mapped[str] = mapped_column(String(50), nullable=False)
    advisor_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    tier: Mapped[RecommendationTier] = mapped_column(SAEnum(RecommendationTier), nullable=False)
    compatibility_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    admission_probability_low: Mapped[float] = mapped_column(Float, nullable=False)
    admission_probability_high: Mapped[float] = mapped_column(Float, nullable=False)
    career_fit_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phd_fit_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_summary: Mapped[str] = mapped_column(Text, nullable=False)
    preparation_advice: Mapped[str] = mapped_column(Text, nullable=False)
    is_suitable_for_reach: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_suitable_for_safe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    employment_pros: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employment_cons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phd_pros: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phd_cons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    session: Mapped["RecommendationSession"] = relationship("RecommendationSession", back_populates="results")
    program: Mapped[Optional["ProgramProfile"]] = relationship("ProgramProfile", back_populates="results")
    advisor: Mapped[Optional["AdvisorProfile"]] = relationship("AdvisorProfile", back_populates="results")
    reasons: Mapped[List["RecommendationReason"]] = relationship(
        "RecommendationReason", back_populates="result", cascade="all, delete-orphan"
    )


class RecommendationReason(Base):
    __tablename__ = "recommendation_reasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    result_id: Mapped[int] = mapped_column(Integer, ForeignKey("recommendation_results.id"), nullable=False)
    reason_type: Mapped[ReasonType] = mapped_column(SAEnum(ReasonType), nullable=False)
    reason_text: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("evidences.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)

    result: Mapped["RecommendationResult"] = relationship("RecommendationResult", back_populates="reasons")
