"""System-wide constants for the Baoyan recommendation system."""

# Source type credibility weights
SOURCE_TYPE_WEIGHTS = {
    "official_notice": 1.0,
    "department_page": 0.9,
    "advisor_page": 0.8,
    "experience_post": 0.5,
    "offer_screenshot": 0.6,
    "qq_group": 0.3,
    "unknown": 0.2,
}

# Time decay factors by year offset
# current_year offset=0 → 1.0, offset=1 → 0.8, offset=2 → 0.6, offset>=3 → 0.4
def get_time_decay(application_year: int, current_year: int = 2026) -> float:
    offset = current_year - application_year
    if offset <= 0:
        return 1.0
    elif offset == 1:
        return 0.8
    elif offset == 2:
        return 0.6
    else:
        return 0.4


# Recommendation tier thresholds (based on similar-case success rate)
TIER_REACH_MAX_SUCCESS_RATE = 0.40      # < 40% → 冲刺
TIER_MAIN_MIN_SUCCESS_RATE = 0.40       # 40-70% → 主申
TIER_MAIN_MAX_SUCCESS_RATE = 0.70
TIER_SAFE_MIN_SUCCESS_RATE = 0.70       # > 70% → 保底

# School tier ordering (higher = more prestigious)
SCHOOL_TIER_ORDER = {
    "985": 3,
    "211": 2,
    "双非": 1,
    "其他": 0,
}

# Minimum cases required to compute statistics
MIN_CASES_FOR_STATS = 3

# Embedding dimension for pgvector
EMBEDDING_DIM = 1536

# Number of similar cases to retrieve
TOP_K_SIMILAR_CASES = 20

# Number of top programs to return in recommendations
TOP_N_PROGRAMS = 30

# Current application year
CURRENT_YEAR = 2026

# Schools with well-known CS programs
TOP_CS_SCHOOLS = [
    "清华大学", "北京大学", "浙江大学", "上海交通大学",
    "中国科学院大学", "北京航空航天大学", "哈尔滨工业大学",
    "南京大学", "复旦大学", "同济大学", "中国科学技术大学",
    "北京理工大学", "华中科技大学", "武汉大学", "中山大学",
    "东南大学", "西安交通大学", "天津大学", "电子科技大学",
    "国防科技大学",
]
