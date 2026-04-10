"""Web crawler using httpx + BeautifulSoup4."""
import re
import logging
from datetime import datetime
from typing import Optional, List
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.ingestion.base import WebPageResult

logger = logging.getLogger(__name__)

# Common Chinese date patterns
DATE_PATTERNS = [
    r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})[日号]?',
    r'(\d{4})-(\d{2})-(\d{2})',
    r'(\d{4})\.(\d{2})\.(\d{2})',
]

EXPERIENCE_POST_SIGNALS = [
    "经验贴", "经历分享", "申请总结", "上岸", "录取", "夏令营经历",
    "预推免", "保研", "推免", "offer", "拿到offer", "入营"
]

OFFICIAL_NOTICE_SIGNALS = [
    "招生简章", "招生通知", "接收推免生", "接收免试", "夏令营通知",
    "预推免通知", "招生公告", "录取名单"
]

ADVISOR_PAGE_SIGNALS = [
    "导师", "研究方向", "课题组", "实验室", "lab", "professor",
    "招生意向", "招收"
]


def _detect_page_type(url: str, title: str, text: str) -> str:
    """Heuristically detect page type."""
    text_lower = text.lower()
    title_lower = (title or "").lower()
    combined = (title_lower + " " + text_lower[:2000])

    # Check for experience posts (forum/blog style)
    experience_score = sum(1 for s in EXPERIENCE_POST_SIGNALS if s in combined)
    official_score = sum(1 for s in OFFICIAL_NOTICE_SIGNALS if s in combined)
    advisor_score = sum(1 for s in ADVISOR_PAGE_SIGNALS if s in combined)

    # URL-based hints
    url_lower = url.lower()
    if any(d in url_lower for d in ["bbs", "forum", "zhihu", "tieba", "post", "thread"]):
        experience_score += 3
    if any(d in url_lower for d in ["faculty", "teacher", "people", "profile"]):
        advisor_score += 3
    if any(d in url_lower for d in ["notice", "news", "announce", "zhaosheng", "推免"]):
        official_score += 3

    if experience_score >= 2:
        return "experience_post"
    if official_score >= 2:
        return "official"
    if advisor_score >= 2:
        return "advisor_page"

    # Domain-based detection
    domain = urlparse(url).netloc
    if any(d in domain for d in ["edu.cn"]):
        return "department_page"

    return "unknown"


def _detect_language(text: str) -> str:
    """Detect language based on character ratio."""
    if not text:
        return "zh"
    zh_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    en_count = len(re.findall(r'[a-zA-Z]', text))
    total = zh_count + en_count
    if total == 0:
        return "zh"
    zh_ratio = zh_count / total
    if zh_ratio > 0.7:
        return "zh"
    elif zh_ratio < 0.3:
        return "en"
    return "mixed"


def _extract_date(text: str) -> Optional[datetime]:
    """Extract publication date from text."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text[:500])
        if match:
            try:
                year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if 2015 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                    return datetime(year, month, day)
            except (ValueError, AttributeError):
                continue
    return None


def _extract_institution(url: str, soup: BeautifulSoup) -> Optional[str]:
    """Try to extract institution name from URL or page content."""
    # Try meta tags
    for meta in soup.find_all("meta"):
        name = meta.get("name", "").lower()
        if "author" in name or "copyright" in name or "organization" in name:
            content = meta.get("content", "")
            if content:
                return content[:100]

    # Try page title for school name
    title_tag = soup.find("title")
    if title_tag:
        title_text = title_tag.get_text()
        # Look for known school name patterns
        school_match = re.search(
            r'(清华大学|北京大学|浙江大学|上海交通大学|复旦大学|中国科学院|'
            r'北京航空航天大学|哈尔滨工业大学|南京大学|同济大学|中国科学技术大学|'
            r'北京理工大学|华中科技大学|武汉大学|中山大学|东南大学|西安交通大学|'
            r'天津大学|电子科技大学|国防科技大学)',
            title_text
        )
        if school_match:
            return school_match.group(1)

    # Try from URL domain
    domain = urlparse(url).netloc
    domain_school_map = {
        "tsinghua.edu.cn": "清华大学",
        "pku.edu.cn": "北京大学",
        "zju.edu.cn": "浙江大学",
        "sjtu.edu.cn": "上海交通大学",
        "fudan.edu.cn": "复旦大学",
        "ucas.ac.cn": "中国科学院大学",
        "buaa.edu.cn": "北京航空航天大学",
        "hit.edu.cn": "哈尔滨工业大学",
        "nju.edu.cn": "南京大学",
        "tongji.edu.cn": "同济大学",
        "ustc.edu.cn": "中国科学技术大学",
        "bit.edu.cn": "北京理工大学",
        "hust.edu.cn": "华中科技大学",
        "whu.edu.cn": "武汉大学",
        "sysu.edu.cn": "中山大学",
        "seu.edu.cn": "东南大学",
        "xjtu.edu.cn": "西安交通大学",
        "tju.edu.cn": "天津大学",
        "uestc.edu.cn": "电子科技大学",
        "nudt.edu.cn": "国防科技大学",
    }
    for domain_part, school in domain_school_map.items():
        if domain_part in domain:
            return school

    return None


def _extract_main_content(soup: BeautifulSoup) -> str:
    """Extract main content from HTML soup."""
    # Remove scripts, styles, nav, footer
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # Try common content containers
    for selector in ["article", "main", ".content", "#content", ".article", ".post-content",
                     ".entry-content", "#main", ".main-content"]:
        try:
            container = soup.select_one(selector)
            if container and len(container.get_text(strip=True)) > 200:
                return container.get_text(separator="\n", strip=True)
        except Exception:
            continue

    # Fallback: find largest text block
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


def _extract_links(url: str, soup: BeautifulSoup) -> List[str]:
    """Extract absolute links from page."""
    links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        absolute = urljoin(url, href)
        if absolute.startswith("http"):
            links.append(absolute)
    return list(set(links))[:50]  # deduplicate, limit to 50


async def crawl_url(url: str, timeout: int = 30) -> WebPageResult:
    """
    Crawl a URL and return structured WebPageResult.
    Uses httpx for HTTP requests and BeautifulSoup4 for parsing.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=httpx.Timeout(timeout),
        headers=headers,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    # Detect encoding
    content_type = response.headers.get("content-type", "")
    encoding = "utf-8"
    if "charset=" in content_type:
        encoding = content_type.split("charset=")[-1].strip()

    try:
        html_text = response.content.decode(encoding, errors="replace")
    except (UnicodeDecodeError, LookupError):
        html_text = response.text

    soup = BeautifulSoup(html_text, "lxml")

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # Extract H1 if title is missing
    if not title:
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

    # Extract main content
    main_content = _extract_main_content(soup)

    # Extract publication date
    published_date = _extract_date(main_content)

    # Extract institution
    institution = _extract_institution(url, soup)

    # Detect page type
    page_type = _detect_page_type(url, title or "", main_content)

    # Map page_type to source_type vocabulary
    source_type_map = {
        "official": "official_notice",
        "experience_post": "experience_post",
        "advisor_page": "advisor_page",
        "department_page": "department_page",
        "unknown": "unknown",
    }
    mapped_type = source_type_map.get(page_type, "unknown")

    # Detect language
    language = _detect_language(main_content)

    # Extract links
    links = _extract_links(url, soup)

    return WebPageResult(
        url=url,
        title=title,
        main_content=main_content[:50000],  # limit to 50k chars
        published_date=published_date,
        author=None,
        institution=institution,
        page_type=mapped_type,
        language=language,
        links=links,
        metadata={
            "status_code": response.status_code,
            "content_length": len(html_text),
        },
    )
