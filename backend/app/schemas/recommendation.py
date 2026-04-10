from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel

from app.models.recommendation import RecommendationTier, SessionStatus, ReasonType


class RecommendationRequest(BaseModel):
    session_id: str


class GenerateRecommendationRequest(BaseModel):
    session_id: str  # alias


class RecommendationReasonOut(BaseModel):
    id: int
    reason_type: ReasonType
    reason_text: str
    confidence: float

    class Config:
        from_attributes = True


class RecommendationResultOut(BaseModel):
    id: int
    school: str
    department: str
    direction: str
    program_type: str
    advisor_name: Optional[str] = None
    tier: RecommendationTier
    compatibility_score: float
    admission_probability_low: float
    admission_probability_high: float
    career_fit_score: Optional[float] = None
    phd_fit_score: Optional[float] = None
    rank: int
    evidence_summary: str
    risk_summary: str
    preparation_advice: str
    is_suitable_for_reach: bool
    is_suitable_for_safe: bool
    employment_pros: Optional[str] = None
    employment_cons: Optional[str] = None
    phd_pros: Optional[str] = None
    phd_cons: Optional[str] = None
    reasons: List[RecommendationReasonOut] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_reasons(cls, result: Any, reasons: list) -> "RecommendationResultOut":
        obj = cls.model_validate(result)
        obj.reasons = [RecommendationReasonOut.model_validate(r) for r in reasons]
        return obj


class RecommendationSessionOut(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    status: SessionStatus
    error_message: Optional[str] = None
    results: List[RecommendationResultOut] = []

    class Config:
        from_attributes = True


class FullRecommendationResponse(BaseModel):
    session_id: str
    status: str  # "processing" / "done" / "failed"
    results: List[RecommendationResultOut]
    profile_summary: Optional[dict] = None
    error: Optional[str] = None


class GenerateRecommendationResponse(BaseModel):
    recommendation_session_id: int
    status: SessionStatus
    message: str
