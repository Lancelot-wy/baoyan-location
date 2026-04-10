"""Text processing utilities."""
import re
from typing import Optional


# School name normalization map
SCHOOL_NAME_MAP = {
    "清华": "清华大学", "北大": "北京大学", "浙大": "浙江大学",
    "上交": "上海交通大学", "交大": "上海交通大学", "复旦": "复旦大学",
    "中科大": "中国科学技术大学", "科大": "中国科学技术大学",
    "国科大": "中国科学院大学", "中科院": "中国科学院大学",
    "北航": "北京航空航天大学", "哈工大": "哈尔滨工业大学",
    "南大": "南京大学", "同济": "同济大学", "北理工": "北京理工大学",
    "华科": "华中科技大学", "武大": "武汉大学", "中山大学": "中山大学",
    "东南大学": "东南大学", "西交": "西安交通大学", "天大": "天津大学",
    "电子科大": "电子科技大学", "成电": "电子科技大学",
    "国防科大": "国防科技大学",
}


def normalize_school_name(name: str) -> str:
    """Normalize informal school name abbreviations to full names."""
    if not name:
        return name
    name = name.strip()
    return SCHOOL_NAME_MAP.get(name, name)


def clean_text(text: str, max_length: Optional[int] = None) -> str:
    """Clean and normalize text content."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common OCR artifacts
    text = re.sub(r'[□■●○◎]', '', text)
    if max_length:
        text = text[:max_length]
    return text


def detect_language(text: str) -> str:
    """Detect if text is primarily Chinese, English, or mixed."""
    if not text:
        return "zh"
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.replace(' ', ''))
    if total_chars == 0:
        return "zh"
    ratio = chinese_chars / total_chars
    if ratio > 0.6:
        return "zh"
    elif ratio < 0.2:
        return "en"
    return "mixed"


def extract_year_from_text(text: str) -> Optional[int]:
    """Try to extract a 4-digit year (2020-2026) from text."""
    matches = re.findall(r'20(2[0-6])', text)
    if matches:
        return 2000 + int(matches[0])
    return None


def truncate_for_llm(text: str, max_chars: int = 8000) -> str:
    """Truncate text for LLM input, appending a note if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + f"\n...[内容已截断，原文共{len(text)}字符]"
