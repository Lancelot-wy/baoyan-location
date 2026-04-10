"""Classify document type using heuristics."""
import re
from typing import Dict, Any, Optional


SCHOOL_PATTERNS = [
    (r'清华大学', "清华大学"),
    (r'北京大学', "北京大学"),
    (r'浙江大学', "浙江大学"),
    (r'上海交通大学', "上海交通大学"),
    (r'复旦大学', "复旦大学"),
    (r'中国科学院大学|国科大', "中国科学院大学"),
    (r'北京航空航天大学|北航', "北京航空航天大学"),
    (r'哈尔滨工业大学|哈工大', "哈尔滨工业大学"),
    (r'南京大学', "南京大学"),
    (r'同济大学', "同济大学"),
    (r'中国科学技术大学|中科大', "中国科学技术大学"),
    (r'北京理工大学|北理工', "北京理工大学"),
    (r'华中科技大学|华科', "华中科技大学"),
    (r'武汉大学', "武汉大学"),
    (r'中山大学', "中山大学"),
    (r'东南大学', "东南大学"),
    (r'西安交通大学|西交大', "西安交通大学"),
    (r'天津大学', "天津大学"),
    (r'电子科技大学|成电', "电子科技大学"),
    (r'国防科技大学|国防科大', "国防科技大学"),
]

YEAR_PATTERN = re.compile(r'20(2[3-9]|3[0-5])\s*年')

SOURCE_TYPE_SIGNALS = {
    "official_notice": [
        "招生简章", "招生通知", "接收推免生通知", "夏令营通知", "预推免通知", "招收推免", "招生公告"
    ],
    "experience_post": [
        "经验帖", "上岸", "经历分享", "申请总结", "保研之路", "保研经历", "我的保研"
    ],
    "advisor_page": [
        "研究方向", "课题组招生", "招收研究生", "lab members", "导师简介"
    ],
    "department_page": [
        "院系介绍", "学院简介", "培养方案", "专业介绍"
    ],
    "offer_screenshot": [
        "恭喜您", "已录取", "优秀营员", "offer"
    ],
}


def classify_document(text: str, doc_type: str = "webpage") -> Dict[str, Any]:
    """
    Classify a document based on its content.
    Returns: {source_type, application_year, institution_hint}
    """
    result = {
        "source_type": "unknown",
        "application_year": None,
        "institution_hint": None,
    }

    # Detect institution
    for pattern, school in SCHOOL_PATTERNS:
        if re.search(pattern, text):
            result["institution_hint"] = school
            break

    # Detect application year
    year_matches = YEAR_PATTERN.findall(text[:2000])
    if year_matches:
        years = [2000 + int(y) for y in year_matches]
        # Take the most recent year mentioned
        result["application_year"] = max(years)

    # Detect source type
    best_type = "unknown"
    best_score = 0
    for src_type, signals in SOURCE_TYPE_SIGNALS.items():
        score = sum(1 for s in signals if s in text[:3000])
        if score > best_score:
            best_score = score
            best_type = src_type

    if best_score > 0:
        result["source_type"] = best_type

    return result
