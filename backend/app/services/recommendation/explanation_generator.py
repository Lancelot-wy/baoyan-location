"""
Explanation generator: uses OpenRouter/OpenAI-compatible API to produce
human-readable, evidence-backed recommendation explanations.
The LLM summarizes and explains; it does NOT make the core ranking decision.
"""
import json
import logging
from typing import List, Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.recommendation.profile_builder import StudentTags
from app.services.recommendation.program_ranker import ScoredProgram
from app.services.recommendation.evidence_aggregator import AggregatedEvidence

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
    return _client


def _build_student_summary(tags: StudentTags) -> str:
    """Build a concise student profile text for the LLM prompt."""
    parts = [
        f"院校背景：{tags.undergraduate_school}（{tags.school_tier}）",
        f"专业排名：前{tags.rank_percentile*100:.1f}%（综合实力评分：{tags.overall_strength:.1f}/100）",
        f"科研经历：{tags.research_strength}（{tags.research_months}个月，最高角色：{tags.max_research_role}）",
        f"论文情况：{tags.paper_strength}" + (f"，最高级别：{tags.best_paper_level}" if tags.best_paper_level else ""),
        f"竞赛情况：{tags.competition_strength}" + (f"，最高：{tags.best_competition_level}{tags.best_competition_award}" if tags.best_competition_level else ""),
        f"实习情况：{'有' if tags.has_internship else '无'}" + (f"（{tags.internship_company_tier}级别，{tags.internship_months}个月）" if tags.has_internship else ""),
        f"英语水平：{tags.english_level}",
        f"职业目标：{tags.career_goal}，风险偏好：{tags.risk_appetite}",
        f"城市偏好：{'、'.join(tags.preferred_cities) if tags.preferred_cities else '无特别要求'}",
    ]
    return "\n".join(parts)


def _build_program_summary(scored: ScoredProgram, evidence: AggregatedEvidence) -> str:
    """Build a concise program description for the LLM prompt."""
    prog = scored.program
    parts = [
        f"学校：{prog.school}，院系：{prog.department}",
        f"方向：{prog.direction}，项目类型：{prog.program_type.value}",
        f"城市：{prog.city or '未知'}",
        f"推荐层级：{scored.tier}，适配度：{scored.compatibility_score:.1f}/100",
        f"录取概率区间：{scored.admission_prob_low*100:.0f}%-{scored.admission_prob_high*100:.0f}%",
    ]

    if prog.rank_threshold_hint:
        parts.append(f"排名参考门槛：前{prog.rank_threshold_hint*100:.0f}%")
    if prog.school_tier_preference:
        parts.append(f"生源偏好：{'/'.join(prog.school_tier_preference)}")
    if prog.phd_track_available is not None:
        parts.append(f"转博机会：{'有' if prog.phd_track_available else '无'}")
    if prog.has_written_exam or prog.has_machine_test:
        exams = []
        if prog.has_written_exam:
            exams.append("笔试")
        if prog.has_machine_test:
            exams.append("机试")
        parts.append(f"考试形式：{'、'.join(exams)}")
    if prog.avg_employment_quality:
        parts.append(f"就业质量：{prog.avg_employment_quality.value}")
    if prog.industry_resources:
        parts.append(f"产业资源：{prog.industry_resources.value}")

    # Evidence summary
    parts.append(f"\n证据情况（共{scored.num_cases}个相似案例）：")
    parts.append(evidence.format_evidence_summary(evidence) if hasattr(evidence, 'format_evidence_summary') else "")
    # Use the module-level function
    from app.services.recommendation.evidence_aggregator import format_evidence_summary
    parts.append(format_evidence_summary(evidence))

    return "\n".join(parts)


EXPLANATION_PROMPT = """你是一个专业的计算机保研/推免申请顾问。以下是一位同学的背景信息和一个推荐项目的详情。

【学生背景】
{student_summary}

【推荐项目】
{program_summary}

请为这个推荐项生成结构化的解释，严格按以下JSON格式输出：
{{
  "evidence_summary": "2-4句话说明推荐依据，必须引用具体证据（年份、来源类型、关键数据）",
  "risk_summary": "2-3句话说明主要风险点，包括背景匹配度、证据不确定性、竞争情况等",
  "preparation_advice": "3-5条具体准备建议，针对这个项目的特点",
  "employment_pros": "就业方向的优势（1-2句话）",
  "employment_cons": "就业方向的劣势（1-2句话）",
  "phd_pros": "读博方向的优势（1-2句话）",
  "phd_cons": "读博方向的劣势（1-2句话）",
  "strengths": ["该学生背景与该项目匹配的具体优势点（列表，每条15字以内）"],
  "weaknesses": ["该学生背景与该项目不匹配的具体弱点（列表，每条15字以内）"],
  "opportunities": ["可以利用的机会或加分项（列表，每条15字以内）"],
  "risks": ["需要注意的风险（列表，每条15字以内）"]
}}

注意：
- 不要凭空捏造证据，只描述学生资料和项目信息中有明确说明的内容
- 对于不确定的信息，明确表达不确定性
- 建议必须具体可执行，不要泛泛而谈
- 必须返回有效JSON，不要有多余文字
"""


async def generate_explanation(
    tags: StudentTags,
    scored: ScoredProgram,
    evidence: AggregatedEvidence,
) -> dict:
    """
    Generate a structured explanation for a single recommendation item.
    Returns a dict with explanation fields.
    Falls back to rule-based text if API is unavailable.
    """
    if not settings.LLM_API_KEY:
        return _fallback_explanation(tags, scored)

    student_summary = _build_student_summary(tags)
    program_summary = _build_program_summary(scored, evidence)

    prompt = EXPLANATION_PROMPT.format(
        student_summary=student_summary,
        program_summary=program_summary,
    )

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()

        # Parse JSON (might be wrapped in ```json)
        import re
        code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block:
            text = code_block.group(1).strip()
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            result = json.loads(json_match.group(0))
            return result

    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")

    return _fallback_explanation(tags, scored)


def _fallback_explanation(tags: StudentTags, scored: ScoredProgram) -> dict:
    """Rule-based fallback explanation when LLM is unavailable."""
    prog = scored.program
    tier_desc = {"冲刺": "冲刺性质，有一定挑战", "主申": "主申方向，匹配度合理", "保底": "保底选择，录取把握较大"}

    strengths = []
    weaknesses = []

    if tags.school_tier == "985":
        strengths.append("985院校背景")
    if tags.rank_percentile <= 0.10:
        strengths.append("专业排名前10%")
    if tags.research_strength == "strong":
        strengths.append("科研经历扎实")
    if tags.paper_strength in ("top", "good"):
        strengths.append(f"有{tags.best_paper_level or ''}级别论文")
    if tags.competition_strength == "top":
        strengths.append("顶级竞赛奖项")

    if tags.rank_percentile > 0.30:
        weaknesses.append(f"排名（前{tags.rank_percentile*100:.0f}%）有提升空间")
    if tags.research_strength in ("none", "weak"):
        weaknesses.append("科研经历较少")
    if tags.paper_strength == "none":
        weaknesses.append("暂无论文发表")

    return {
        "evidence_summary": (
            f"该推荐基于系统评估：{prog.school}{prog.department}，"
            f"属于{tier_desc.get(scored.tier, '')}。"
            f"综合适配度{scored.compatibility_score:.1f}分，"
            f"历史案例数据显示录取概率区间约{scored.admission_prob_low*100:.0f}%-{scored.admission_prob_high*100:.0f}%。"
        ),
        "risk_summary": (
            "注意：当前推荐基于有限证据，请以官方最新招生通知为准。"
            f"{'建议优先关注排名要求，自身排名略低于参考线。' if tags.rank_percentile > 0.25 else ''}"
            "推免竞争激烈，建议尽早联系目标院系确认招生计划。"
        ),
        "preparation_advice": (
            "1. 尽早联系目标院系招生办或相关导师了解最新招生计划\n"
            "2. 准备个人陈述，突出与目标方向相关的科研/项目经历\n"
            "3. 准备专业面试，复习数据结构、算法等核心课程\n"
            "4. 关注官方夏令营/预推免通知，及时报名\n"
            "5. 准备英文自我介绍和专业英文问答"
        ),
        "employment_pros": f"{prog.city or '目标城市'}产业资源丰富，{prog.school}品牌加持就业竞争力强。" if prog.city else "具体就业情况请参考官方信息。",
        "employment_cons": "专硕学制较短，需充分利用实习机会。",
        "phd_pros": f"{'有转博通道，' if prog.phd_track_available else ''}科研氛围浓厚。" if prog.phd_track_available else "直接读博需提前与导师沟通。",
        "phd_cons": "读博竞争激烈，需提前与导师建立联系。",
        "strengths": strengths or ["具备基本申请条件"],
        "weaknesses": weaknesses or ["相关信息有限"],
        "opportunities": ["早联系导师可增加录取机会", "认真准备面试可弥补背景不足"],
        "risks": ["推免政策可能年度调整", "竞争激烈程度超出预期"],
    }


async def generate_profile_summary(tags: StudentTags) -> dict:
    """Generate overall student profile analysis and strategic advice."""
    if not settings.LLM_API_KEY:
        return _fallback_profile_summary(tags)

    prompt = f"""你是计算机保研/推免申请顾问。分析以下学生背景：

{_build_student_summary(tags)}

请返回JSON格式的综合分析：
{{
  "core_strengths": ["核心优势列表，每条20字以内，最多5条"],
  "core_weaknesses": ["核心短板列表，每条20字以内，最多4条"],
  "strategic_advice": "整体申请策略建议，100-150字",
  "timeline_advice": "申请时间安排建议，100字左右",
  "directions_to_avoid": ["不建议重点投入的方向，每条15字以内"],
  "overall_assessment": "整体评估一句话总结"
}}

必须返回有效JSON。"""

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
        import re
        code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if code_block:
            text = code_block.group(1).strip()
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        logger.error(f"Profile summary generation failed: {e}")

    return _fallback_profile_summary(tags)


def _fallback_profile_summary(tags: StudentTags) -> dict:
    strengths = []
    weaknesses = []

    if tags.school_tier == "985":
        strengths.append("985院校背景，基础竞争力强")
    elif tags.school_tier == "211":
        strengths.append("211院校背景，具备基本竞争力")

    if tags.rank_percentile <= 0.05:
        strengths.append("专业排名前5%，学业表现突出")
    elif tags.rank_percentile <= 0.15:
        strengths.append("专业排名前15%，学业表现良好")

    if tags.research_strength == "strong":
        strengths.append("科研经历丰富，具备独立科研能力")
    if tags.paper_strength in ("top", "good"):
        strengths.append(f"有高质量论文（{tags.best_paper_level}），竞争力显著")
    if tags.competition_strength in ("top", "good"):
        strengths.append("竞赛成绩优秀，综合能力强")

    if tags.rank_percentile > 0.30:
        weaknesses.append("排名偏后，需在其他方面补强")
    if tags.research_strength in ("none", "weak"):
        weaknesses.append("科研经历不足，建议尽快进组")
    if tags.paper_strength == "none":
        weaknesses.append("无论文发表，顶校竞争存在短板")
    if tags.competition_strength == "none":
        weaknesses.append("无突出竞赛奖项")

    return {
        "core_strengths": strengths or ["具备基本申请条件"],
        "core_weaknesses": weaknesses or ["需进一步了解目标院校要求"],
        "strategic_advice": (
            f"建议根据{'冲刺型' if tags.risk_appetite == '冲刺' else '稳健型' if tags.risk_appetite == '稳健' else '保守型'}策略，"
            "合理分配冲刺/主申/保底比例（建议2:4:2），优先确保保底院校，再冲刺目标院校。"
            "夏令营季（5-7月）是关键，建议广投优质项目，积累面试经验。"
        ),
        "timeline_advice": (
            "大三下：积极进科研组，准备简历；"
            "5-7月：大量投递夏令营；"
            "9月：预推免阶段重点出击；"
            "10月：确认保研去向"
        ),
        "directions_to_avoid": ["与自身科研方向完全无关的院系"],
        "overall_assessment": f"综合实力评分{tags.overall_strength:.1f}/100，属于{'较强' if tags.overall_strength >= 70 else '中等' if tags.overall_strength >= 50 else '有待提升'}水平",
    }
