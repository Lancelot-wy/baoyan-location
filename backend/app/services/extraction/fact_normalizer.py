"""Normalize extracted facts: school names, departments, program types."""
import re
from typing import Optional, Dict

# Canonical school name mappings
SCHOOL_NAME_MAP = {
    "清华": "清华大学",
    "北大": "北京大学",
    "浙大": "浙江大学",
    "交大": "上海交通大学",
    "上交": "上海交通大学",
    "上海交大": "上海交通大学",
    "复旦": "复旦大学",
    "中科院": "中国科学院大学",
    "国科大": "中国科学院大学",
    "北航": "北京航空航天大学",
    "哈工大": "哈尔滨工业大学",
    "哈工": "哈尔滨工业大学",
    "南大": "南京大学",
    "同济": "同济大学",
    "中科大": "中国科学技术大学",
    "科大": "中国科学技术大学",
    "北理工": "北京理工大学",
    "华科": "华中科技大学",
    "武大": "武汉大学",
    "中山": "中山大学",
    "东南": "东南大学",
    "西交": "西安交通大学",
    "天大": "天津大学",
    "电子科大": "电子科技大学",
    "成电": "电子科技大学",
    "国防科大": "国防科技大学",
    "北师大": "北京师范大学",
    "人大": "中国人民大学",
    "北邮": "北京邮电大学",
    "北林": "北京林业大学",
    "华南理工": "华南理工大学",
    "华南": "华南理工大学",
    "川大": "四川大学",
    "重大": "重庆大学",
    "厦大": "厦门大学",
}

# Department normalization
DEPARTMENT_NAME_MAP = {
    "计算机系": "计算机科学与技术系",
    "软件学院": "软件学院",
    "计算机学院": "计算机学院",
    "计算机科学学院": "计算机科学与技术学院",
    "信息学院": "信息科学技术学院",
    "电子信息学院": "电子信息学院",
    "人工智能学院": "人工智能学院",
    "网络空间安全学院": "网络空间安全学院",
    "数据科学学院": "数据科学与工程学院",
}

# Program type normalization
PROGRAM_TYPE_MAP = {
    "学硕": "学硕",
    "学术型": "学硕",
    "学术学位": "学硕",
    "专硕": "专硕",
    "专业型": "专硕",
    "专业学位": "专硕",
    "直博": "直博",
    "直接攻博": "直博",
    "夏令营": "夏令营",
    "暑期学校": "夏令营",
    "预推免": "预推免",
    "九推": "预推免",
    "冬令营": "冬令营",
}


def normalize_school_name(name: Optional[str]) -> Optional[str]:
    """Normalize school name to canonical form."""
    if not name:
        return name
    name = name.strip()
    # Direct mapping
    if name in SCHOOL_NAME_MAP:
        return SCHOOL_NAME_MAP[name]
    # Check if it's already a full canonical name
    if name.endswith("大学") or name.endswith("学院") or name.endswith("大学院"):
        return name
    # Partial match
    for abbrev, canonical in SCHOOL_NAME_MAP.items():
        if abbrev in name:
            return canonical
    return name


def normalize_department_name(name: Optional[str]) -> Optional[str]:
    """Normalize department name to canonical form."""
    if not name:
        return name
    name = name.strip()
    return DEPARTMENT_NAME_MAP.get(name, name)


def normalize_program_type(name: Optional[str]) -> Optional[str]:
    """Normalize program type."""
    if not name:
        return name
    name = name.strip()
    return PROGRAM_TYPE_MAP.get(name, name)


def normalize_fact(fact_dict: Dict) -> Dict:
    """Apply all normalizations to a fact dict."""
    fact_dict = dict(fact_dict)
    fact_dict["subject_school"] = normalize_school_name(fact_dict.get("subject_school"))
    fact_dict["subject_department"] = normalize_department_name(fact_dict.get("subject_department"))
    fact_dict["subject_program"] = normalize_program_type(fact_dict.get("subject_program"))
    return fact_dict


def extract_gpa_threshold(fact_value: str) -> Optional[float]:
    """Extract GPA threshold from a fact value string."""
    patterns = [
        r'GPA[≥>=:：\s]+(\d+\.?\d*)',
        r'绩点[≥>=:：\s]+(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*[\/\s]?\s*4\.0',
    ]
    for p in patterns:
        m = re.search(p, fact_value, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                if 2.0 <= val <= 4.0:
                    return val
            except ValueError:
                pass
    return None


def extract_rank_threshold(fact_value: str) -> Optional[float]:
    """Extract rank threshold percentage from a fact value string."""
    patterns = [
        r'排名[前在]?\s*(\d+)\s*%',
        r'前\s*(\d+)\s*%',
        r'排名[前在]?\s*(\d+)\s*名',
        r'(\d+)\s*%\s*以内',
    ]
    for p in patterns:
        m = re.search(p, fact_value)
        if m:
            try:
                val = float(m.group(1))
                if 1 <= val <= 100:
                    return val / 100.0  # Convert to 0-1
            except ValueError:
                pass
    return None
