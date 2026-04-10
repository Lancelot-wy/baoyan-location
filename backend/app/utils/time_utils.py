"""Time and date utilities."""
from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def get_application_year(published_at: Optional[datetime] = None) -> int:
    """
    Infer which application season (年份) a document belongs to.
    Chinese grad school recruitment typically runs June-October.
    A document from Nov 2024 - May 2025 belongs to 2025 cycle.
    A document from June 2025 - Oct 2025 belongs to 2025 cycle.
    """
    ref = published_at or utcnow()
    year = ref.year
    month = ref.month
    # June–October is the active recruitment season for that year
    # Nov onwards is prep for next year
    if month >= 11:
        return year + 1
    return year


def format_date_cn(dt: Optional[datetime]) -> str:
    if not dt:
        return "未知"
    return dt.strftime("%Y年%m月%d日")
