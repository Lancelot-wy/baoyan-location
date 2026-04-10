"""Recommendation generation (SSE streaming) and retrieval endpoints."""
import json
import logging
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.models.user import UserProfile, ResearchExperience, Paper, Competition, Internship, PreferenceProfile
from app.models.recommendation import (
    RecommendationSession, RecommendationResult, RecommendationReason,
    SessionStatus, RecommendationTier, ReasonType,
)
from app.schemas.recommendation import RecommendationRequest
from app.services.recommendation.profile_builder import build_student_tags
from app.services.recommendation.program_ranker import rank_programs
from app.services.recommendation.evidence_aggregator import aggregate_evidence_for_program
from app.services.recommendation.explanation_generator import generate_explanation, generate_profile_summary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _to_str(val):
    if val is None:
        return ""
    if isinstance(val, list):
        return "\n".join(str(v) for v in val)
    return str(val)


def _sse_event(data: dict) -> str:
    """Format a dict as an SSE event line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/generate-stream")
async def generate_recommendations_stream(request: RecommendationRequest):
    """
    SSE endpoint: streams progress events as recommendations are generated.
    Events: {step, message, progress (0-100), ?school, ?result}
    Final event: {step: "done", session_id}
    """
    return StreamingResponse(
        _pipeline_stream(request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _pipeline_stream(student_session_id: str) -> AsyncGenerator[str, None]:
    """Run pipeline and yield SSE progress events."""
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            # ── Step 1: Load profile ─────────────────────────────────────
            yield _sse_event({"step": "loading", "message": "正在加载学生档案...", "progress": 5})

            profile_result = await db.execute(
                select(UserProfile).where(UserProfile.session_id == student_session_id)
            )
            profile = profile_result.scalar_one_or_none()
            if not profile:
                yield _sse_event({"step": "error", "message": "未找到学生档案"})
                return

            research = (await db.execute(select(ResearchExperience).where(ResearchExperience.user_id == profile.id))).scalars().all()
            papers = (await db.execute(select(Paper).where(Paper.user_id == profile.id))).scalars().all()
            competitions = (await db.execute(select(Competition).where(Competition.user_id == profile.id))).scalars().all()
            internships = (await db.execute(select(Internship).where(Internship.user_id == profile.id))).scalars().all()
            preferences = (await db.execute(select(PreferenceProfile).where(PreferenceProfile.user_id == profile.id))).scalar_one_or_none()

            yield _sse_event({"step": "profile", "message": "正在构建学生画像...", "progress": 10})

            tags = build_student_tags(
                profile=profile, research_experiences=list(research),
                papers=list(papers), competitions=list(competitions),
                internships=list(internships), preferences=preferences,
            )

            yield _sse_event({
                "step": "profile_done",
                "message": f"画像构建完成：综合实力 {tags.overall_strength:.0f}/100",
                "progress": 15,
            })

            # ── Step 2: Rank programs ───────────────────────────────────
            yield _sse_event({"step": "ranking", "message": "正在检索匹配院校项目...", "progress": 18})

            scored_programs = await rank_programs(db=db, tags=tags)
            total = len(scored_programs)

            yield _sse_event({
                "step": "ranking_done",
                "message": f"筛选出 {total} 个匹配项目，开始逐项分析...",
                "progress": 22,
            })

            # ── Step 3: Profile summary ─────────────────────────────────
            yield _sse_event({"step": "summary", "message": "正在生成个人画像分析（AI分析中）...", "progress": 25})
            profile_summary = await generate_profile_summary(tags)

            yield _sse_event({
                "step": "summary_done",
                "message": f"画像分析完成：{profile_summary.get('overall_assessment', '')[:50]}",
                "progress": 30,
            })

            # ── Step 4: Create session ──────────────────────────────────
            session = RecommendationSession(user_id=profile.id, status=SessionStatus.PROCESSING)
            db.add(session)
            await db.flush()
            rec_session_id = session.id

            # ── Step 5: Generate explanations per program ──────────────
            rank = 1
            for i, scored in enumerate(scored_programs):
                progress = 30 + int((i / max(total, 1)) * 60)  # 30% → 90%

                yield _sse_event({
                    "step": "analyzing",
                    "message": f"分析第 {i+1}/{total} 个：{scored.program.school} · {scored.program.department}",
                    "progress": progress,
                    "school": scored.program.school,
                    "department": scored.program.department,
                    "tier": scored.tier,
                })

                evidence = await aggregate_evidence_for_program(
                    db=db, school=scored.program.school,
                    department=scored.program.department,
                    direction=scored.program.direction,
                )
                explanation = await generate_explanation(tags, scored, evidence)

                result_record = RecommendationResult(
                    session_id=rec_session_id,
                    program_id=scored.program.id,
                    school=scored.program.school,
                    department=scored.program.department,
                    direction=scored.program.direction,
                    program_type=scored.program.program_type.value,
                    tier=RecommendationTier(scored.tier),
                    compatibility_score=scored.compatibility_score,
                    admission_probability_low=scored.admission_prob_low,
                    admission_probability_high=scored.admission_prob_high,
                    career_fit_score=scored.career_fit_score,
                    phd_fit_score=scored.phd_fit_score,
                    rank=rank,
                    evidence_summary=_to_str(explanation.get("evidence_summary", "")),
                    risk_summary=_to_str(explanation.get("risk_summary", "")),
                    preparation_advice=_to_str(explanation.get("preparation_advice", "")),
                    is_suitable_for_reach=scored.is_suitable_for_reach,
                    is_suitable_for_safe=scored.is_suitable_for_safe,
                    employment_pros=_to_str(explanation.get("employment_pros")),
                    employment_cons=_to_str(explanation.get("employment_cons")),
                    phd_pros=_to_str(explanation.get("phd_pros")),
                    phd_cons=_to_str(explanation.get("phd_cons")),
                )
                db.add(result_record)
                await db.flush()

                for key, reason_type in {"strengths": ReasonType.STRENGTH, "weaknesses": ReasonType.WEAKNESS, "risks": ReasonType.RISK, "opportunities": ReasonType.OPPORTUNITY}.items():
                    for item in (explanation.get(key, []) or [])[:4]:
                        db.add(RecommendationReason(
                            result_id=result_record.id, reason_type=reason_type,
                            reason_text=str(item), confidence=0.75,
                        ))

                rank += 1

            # ── Step 6: Finalize ───────────────────────────────────────
            yield _sse_event({"step": "finalizing", "message": "正在保存结果...", "progress": 95})

            sess_result = await db.execute(
                select(RecommendationSession).where(RecommendationSession.id == rec_session_id)
            )
            rec_session = sess_result.scalar_one()
            rec_session.status = SessionStatus.DONE
            rec_session.error_message = json.dumps(profile_summary, ensure_ascii=False)
            await db.commit()

            yield _sse_event({
                "step": "done",
                "message": f"分析完成！共 {total} 个推荐项目",
                "progress": 100,
                "session_id": student_session_id,
                "total_results": total,
            })

        except Exception as e:
            logger.error(f"Pipeline stream failed: {e}", exc_info=True)
            yield _sse_event({"step": "error", "message": f"生成失败：{str(e)[:200]}"})


# ── Keep old POST endpoint as fallback ──────────────────────────────────────

@router.post("/generate", status_code=200)
async def generate_recommendations(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Non-streaming fallback. Prefer /generate-stream for progress updates."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.session_id == request.session_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, f"Student profile not found: {request.session_id}")

    session = RecommendationSession(user_id=profile.id, status=SessionStatus.PROCESSING)
    db.add(session)
    await db.flush()
    rec_session_id = session.id
    await db.commit()

    await _run_recommendation_pipeline(request.session_id, rec_session_id)

    return {"id": rec_session_id, "status": "done", "session_id": request.session_id}


# ── GET results ─────────────────────────────────────────────────────────────

@router.get("/{session_id}")
async def get_recommendations(session_id: str, db: AsyncSession = Depends(get_db)):
    student_result = await db.execute(
        select(UserProfile).where(UserProfile.session_id == session_id)
    )
    profile = student_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(404, "Student profile not found")

    sess_result = await db.execute(
        select(RecommendationSession)
        .where(RecommendationSession.user_id == profile.id)
        .order_by(RecommendationSession.created_at.desc())
        .limit(1)
    )
    rec_session = sess_result.scalar_one_or_none()
    if not rec_session:
        raise HTTPException(404, "No recommendation session found.")

    if rec_session.status == SessionStatus.PROCESSING:
        return {"session_id": session_id, "status": "processing", "results": [], "profile_summary": None, "error": None}

    if rec_session.status == SessionStatus.FAILED:
        return {"session_id": session_id, "status": "failed", "results": [], "profile_summary": None, "error": rec_session.error_message}

    results_q = await db.execute(
        select(RecommendationResult).where(RecommendationResult.session_id == rec_session.id).order_by(RecommendationResult.rank)
    )
    results = results_q.scalars().all()

    result_ids = [r.id for r in results]
    reasons_by_result = {}
    if result_ids:
        reasons_q = await db.execute(select(RecommendationReason).where(RecommendationReason.result_id.in_(result_ids)))
        for reason in reasons_q.scalars().all():
            reasons_by_result.setdefault(reason.result_id, []).append(reason)

    result_outs = []
    for r in results:
        reasons_data = [
            {"id": rr.id, "reason_type": rr.reason_type.value, "reason_text": rr.reason_text, "confidence": rr.confidence}
            for rr in reasons_by_result.get(r.id, [])
        ]
        result_outs.append({
            "id": r.id, "school": r.school, "department": r.department,
            "direction": r.direction, "program_type": r.program_type,
            "advisor_name": r.advisor_name, "tier": r.tier.value,
            "compatibility_score": r.compatibility_score,
            "admission_probability_low": r.admission_probability_low,
            "admission_probability_high": r.admission_probability_high,
            "career_fit_score": r.career_fit_score, "phd_fit_score": r.phd_fit_score,
            "rank": r.rank, "evidence_summary": r.evidence_summary,
            "risk_summary": r.risk_summary, "preparation_advice": r.preparation_advice,
            "is_suitable_for_reach": r.is_suitable_for_reach,
            "is_suitable_for_safe": r.is_suitable_for_safe,
            "employment_pros": r.employment_pros, "employment_cons": r.employment_cons,
            "phd_pros": r.phd_pros, "phd_cons": r.phd_cons,
            "reasons": reasons_data,
        })

    profile_summary = None
    if rec_session.error_message and rec_session.error_message.startswith("{"):
        try:
            profile_summary = json.loads(rec_session.error_message)
        except Exception:
            pass

    return {"session_id": session_id, "status": "done", "results": result_outs, "profile_summary": profile_summary, "error": None}


# ── Internal pipeline (used by non-streaming fallback) ─────────────────────

async def _run_recommendation_pipeline(student_session_id: str, rec_session_id: int):
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            profile = (await db.execute(select(UserProfile).where(UserProfile.session_id == student_session_id))).scalar_one()
            research = (await db.execute(select(ResearchExperience).where(ResearchExperience.user_id == profile.id))).scalars().all()
            papers = (await db.execute(select(Paper).where(Paper.user_id == profile.id))).scalars().all()
            competitions = (await db.execute(select(Competition).where(Competition.user_id == profile.id))).scalars().all()
            internships_list = (await db.execute(select(Internship).where(Internship.user_id == profile.id))).scalars().all()
            preferences = (await db.execute(select(PreferenceProfile).where(PreferenceProfile.user_id == profile.id))).scalar_one_or_none()

            tags = build_student_tags(profile=profile, research_experiences=list(research), papers=list(papers), competitions=list(competitions), internships=list(internships_list), preferences=preferences)
            scored_programs = await rank_programs(db=db, tags=tags)
            profile_summary = await generate_profile_summary(tags)

            rank = 1
            for scored in scored_programs:
                evidence = await aggregate_evidence_for_program(db=db, school=scored.program.school, department=scored.program.department, direction=scored.program.direction)
                explanation = await generate_explanation(tags, scored, evidence)
                result_record = RecommendationResult(
                    session_id=rec_session_id, program_id=scored.program.id,
                    school=scored.program.school, department=scored.program.department,
                    direction=scored.program.direction, program_type=scored.program.program_type.value,
                    tier=RecommendationTier(scored.tier), compatibility_score=scored.compatibility_score,
                    admission_probability_low=scored.admission_prob_low, admission_probability_high=scored.admission_prob_high,
                    career_fit_score=scored.career_fit_score, phd_fit_score=scored.phd_fit_score, rank=rank,
                    evidence_summary=_to_str(explanation.get("evidence_summary", "")),
                    risk_summary=_to_str(explanation.get("risk_summary", "")),
                    preparation_advice=_to_str(explanation.get("preparation_advice", "")),
                    is_suitable_for_reach=scored.is_suitable_for_reach, is_suitable_for_safe=scored.is_suitable_for_safe,
                    employment_pros=_to_str(explanation.get("employment_pros")), employment_cons=_to_str(explanation.get("employment_cons")),
                    phd_pros=_to_str(explanation.get("phd_pros")), phd_cons=_to_str(explanation.get("phd_cons")),
                )
                db.add(result_record)
                await db.flush()
                for key, reason_type in {"strengths": ReasonType.STRENGTH, "weaknesses": ReasonType.WEAKNESS, "risks": ReasonType.RISK, "opportunities": ReasonType.OPPORTUNITY}.items():
                    for item in (explanation.get(key, []) or [])[:4]:
                        db.add(RecommendationReason(result_id=result_record.id, reason_type=reason_type, reason_text=str(item), confidence=0.75))
                rank += 1

            rec_session = (await db.execute(select(RecommendationSession).where(RecommendationSession.id == rec_session_id))).scalar_one()
            rec_session.status = SessionStatus.DONE
            rec_session.error_message = json.dumps(profile_summary, ensure_ascii=False)
            await db.commit()
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            async with AsyncSessionLocal() as error_db:
                rec_session = (await error_db.execute(select(RecommendationSession).where(RecommendationSession.id == rec_session_id))).scalar_one_or_none()
                if rec_session:
                    rec_session.status = SessionStatus.FAILED
                    rec_session.error_message = str(e)[:1000]
                    await error_db.commit()
