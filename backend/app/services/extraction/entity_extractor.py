"""Entity extraction using OpenRouter / OpenAI-compatible API."""
import json
import logging
import re
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def get_llm_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
    return _client


EXTRACTION_PROMPTS = {
    "experience_post": """你是一个专业的信息提取助手。从以下保研/推免经验帖中提取结构化信息。

文本内容：
{text}

请提取以下信息并以JSON格式返回：
{{
  "facts": [
    {{
      "fact_type": "offer_result",
      "subject_school": "目标学校名称",
      "subject_department": "目标院系名称",
      "subject_program": "项目类型(夏令营/预推免/直博等)",
      "subject_advisor": "导师名字(如有)",
      "fact_key": "具体信息的键名",
      "fact_value": "具体信息的值",
      "fact_value_structured": null,
      "confidence": 0.85,
      "raw_excerpt": "原文中支持此信息的关键片段(50字以内)",
      "applicant_background": {{
        "school": "申请者所在学校",
        "school_tier": "985/211/双非/其他",
        "major": "专业",
        "gpa_percentile": null,
        "rank_percentile": null,
        "has_paper": false,
        "paper_level": null,
        "competition_level": null,
        "research_months": null
      }},
      "result": {{
        "got_camp_invite": null,
        "camp_result": null,
        "final_offer": null
      }}
    }}
  ]
}}

只提取文中明确提到的信息，不要推测。如果某个字段没有信息，设为null。
必须返回有效的JSON格式。""",

    "official_notice": """你是一个专业的信息提取助手。从以下高校招生通知/官方文件中提取结构化信息。

文本内容：
{text}

请提取以下信息并以JSON格式返回：
{{
  "facts": [
    {{
      "fact_type": "program_detail",
      "subject_school": "学校名称",
      "subject_department": "院系名称",
      "subject_program": "项目类型",
      "subject_advisor": null,
      "fact_key": "具体信息的键名(如: gpa_requirement, rank_requirement, quota, deadline, interview_type等)",
      "fact_value": "具体信息的值",
      "fact_value_structured": null,
      "confidence": 0.9,
      "raw_excerpt": "原文中支持此信息的关键片段(100字以内)"
    }}
  ]
}}

重点提取：名额/招生人数、GPA要求、排名要求、院校层次要求、截止日期、面试形式、研究方向偏好、是否有笔试/机试。
必须返回有效的JSON格式。""",

    "advisor_page": """你是一个专业的信息提取助手。从以下导师主页内容中提取结构化信息。

文本内容：
{text}

请提取以下信息并以JSON格式返回：
{{
  "facts": [
    {{
      "fact_type": "advisor_preference",
      "subject_school": "学校名称",
      "subject_department": "院系名称",
      "subject_program": null,
      "subject_advisor": "导师姓名",
      "fact_key": "具体信息的键名",
      "fact_value": "具体信息的值",
      "fact_value_structured": {{
        "name": "导师姓名",
        "title": "职称",
        "research_directions": ["方向1", "方向2"],
        "lab_name": "课题组名称",
        "is_recruiting": null,
        "quota_hint": null,
        "preferred_background": []
      }},
      "confidence": 0.85,
      "raw_excerpt": "原文中支持此信息的关键片段"
    }}
  ]
}}

必须返回有效的JSON格式。""",

    "default": """你是一个专业的信息提取助手。从以下文本中提取与高校CS研究生招生相关的结构化信息。

文本内容：
{text}

请提取以下信息并以JSON格式返回：
{{
  "facts": [
    {{
      "fact_type": "other",
      "subject_school": "学校名称(如有)",
      "subject_department": "院系名称(如有)",
      "subject_program": "项目类型(如有)",
      "subject_advisor": "导师姓名(如有)",
      "fact_key": "信息的键名",
      "fact_value": "信息的值",
      "fact_value_structured": null,
      "confidence": 0.7,
      "raw_excerpt": "原文关键片段"
    }}
  ]
}}

必须返回有效的JSON格式。"""
}

FACT_TYPE_MAP = {
    "rank_requirement": "rank_requirement",
    "research_preference": "research_preference",
    "interview_format": "interview_format",
    "quota": "quota",
    "deadline": "deadline",
    "advisor_preference": "advisor_preference",
    "program_detail": "program_detail",
    "offer_result": "offer_result",
    "other": "other",
}


def _get_prompt_template(source_type: str) -> str:
    if source_type in ("experience_post", "offer_screenshot", "qq_group"):
        return EXTRACTION_PROMPTS["experience_post"]
    elif source_type in ("official_notice",):
        return EXTRACTION_PROMPTS["official_notice"]
    elif source_type in ("advisor_page",):
        return EXTRACTION_PROMPTS["advisor_page"]
    else:
        return EXTRACTION_PROMPTS["default"]


def _parse_llm_response(response_text: str) -> List[Dict[str, Any]]:
    """Parse LLM JSON response, handle common formatting issues."""
    text = response_text.strip()

    # Try to find JSON block (might be wrapped in ```json ... ```)
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if code_block:
        text = code_block.group(1).strip()

    json_match = re.search(r'\{[\s\S]*\}', text)
    if not json_match:
        logger.warning("No JSON found in LLM response")
        return []

    json_str = json_match.group(0)
    try:
        data = json.loads(json_str)
        return data.get("facts", [])
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error: {e}. Trying to fix...")
        cleaned = re.sub(r',\s*([}\]])', r'\1', json_str)
        try:
            data = json.loads(cleaned)
            return data.get("facts", [])
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON")
            return []


async def extract_facts_from_text(
    text: str,
    source_type: str,
    institution_hint: Optional[str] = None,
    application_year: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Use LLM API to extract structured facts from document text.
    Returns list of fact dicts ready for ExtractedFact creation.
    """
    if not text or not text.strip():
        return []

    if not settings.LLM_API_KEY:
        logger.warning("LLM_API_KEY not set; returning empty facts")
        return []

    max_chars = 8000
    truncated_text = text[:max_chars]
    if len(text) > max_chars:
        truncated_text += f"\n...[文本已截断，共{len(text)}字符]"

    prompt_template = _get_prompt_template(source_type)
    prompt = prompt_template.format(text=truncated_text)

    client = get_llm_client()

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        response_text = response.choices[0].message.content
        raw_facts = _parse_llm_response(response_text)

    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        return []

    # Normalize and validate facts
    normalized_facts = []
    for raw in raw_facts:
        fact_type_raw = raw.get("fact_type", "other")
        fact_type = FACT_TYPE_MAP.get(fact_type_raw, "other")

        fact_key = raw.get("fact_key")
        fact_value = raw.get("fact_value")

        if not fact_key or not fact_value:
            continue

        subject_school = raw.get("subject_school") or institution_hint

        normalized_facts.append({
            "fact_type": fact_type,
            "subject_school": subject_school,
            "subject_department": raw.get("subject_department"),
            "subject_program": raw.get("subject_program"),
            "subject_advisor": raw.get("subject_advisor"),
            "fact_key": str(fact_key)[:200],
            "fact_value": str(fact_value)[:2000],
            "fact_value_structured": raw.get("fact_value_structured"),
            "confidence": float(raw.get("confidence", 0.7)),
            "raw_excerpt": str(raw.get("raw_excerpt", text[:200]))[:1000],
            "extraction_method": "llm",
        })

        applicant_bg = raw.get("applicant_background")
        result_data = raw.get("result")
        if applicant_bg and result_data:
            normalized_facts[-1]["_applicant_background"] = applicant_bg
            normalized_facts[-1]["_result"] = result_data

    return normalized_facts
