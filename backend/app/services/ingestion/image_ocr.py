"""Image OCR using pytesseract + Pillow."""
import logging
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("pytesseract or Pillow not available. OCR will be disabled.")

from app.services.ingestion.base import OCRResult

logger = logging.getLogger(__name__)

# Confidence threshold below which we mark as needs_review
OCR_CONFIDENCE_THRESHOLD = 0.6

OFFER_SIGNALS = ["offer", "录取通知", "已录取", "恭喜", "优秀营员", "录取结果"]
ANNOUNCEMENT_SIGNALS = ["公告", "通知", "关于", "招生", "夏令营"]
LIST_SIGNALS = ["名单", "list", "序号", "编号", "学校"]
SCREENSHOT_SIGNALS = ["回复", "聊天", "已读", "发送", "微信", "QQ"]


def _classify_image_type(text: str) -> str:
    """Classify image type based on OCR text content."""
    text_lower = text.lower()

    offer_score = sum(1 for s in OFFER_SIGNALS if s in text_lower)
    announcement_score = sum(1 for s in ANNOUNCEMENT_SIGNALS if s in text_lower)
    list_score = sum(1 for s in LIST_SIGNALS if s in text_lower)
    screenshot_score = sum(1 for s in SCREENSHOT_SIGNALS if s in text_lower)

    scores = {
        "offer_letter": offer_score,
        "announcement": announcement_score,
        "list": list_score,
        "experience_screenshot": screenshot_score,
    }
    best_type = max(scores, key=scores.get)
    if scores[best_type] == 0:
        return "unknown"
    return best_type


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


def _compute_ocr_confidence(data: Dict) -> float:
    """Compute average OCR confidence from pytesseract data dict."""
    if not data:
        return 0.0
    confidences = [
        int(c) for c in data.get("conf", [])
        if c != -1 and str(c).strip() != "-1"
    ]
    if not confidences:
        return 0.0
    return sum(confidences) / (len(confidences) * 100.0)


def ocr_image(file_path: str) -> OCRResult:
    """
    Perform OCR on an image file.
    Returns OCRResult with text, confidence, image type classification.
    """
    if not OCR_AVAILABLE:
        return OCRResult(
            file_path=file_path,
            raw_text="[OCR not available - pytesseract not installed]",
            confidence=0.0,
            image_type="unknown",
            needs_review=True,
            language="zh",
            blocks=[],
        )

    try:
        img = Image.open(file_path)

        # Convert to RGB if needed
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Use Chinese + English language model
        lang = "chi_sim+eng"
        custom_config = r"--oem 3 --psm 3"

        # Extract text
        raw_text = pytesseract.image_to_string(img, lang=lang, config=custom_config)

        # Extract confidence data
        try:
            data = pytesseract.image_to_data(img, lang=lang, config=custom_config,
                                              output_type=pytesseract.Output.DICT)
            confidence = _compute_ocr_confidence(data)

            # Build word-level blocks
            blocks = []
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                if int(data["conf"][i]) > 0 and data["text"][i].strip():
                    blocks.append({
                        "text": data["text"][i],
                        "conf": int(data["conf"][i]),
                        "left": data["left"][i],
                        "top": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i],
                    })
        except Exception:
            confidence = 0.5  # Default when data extraction fails
            blocks = []

        image_type = _classify_image_type(raw_text)
        language = _detect_language(raw_text)
        needs_review = confidence < OCR_CONFIDENCE_THRESHOLD or len(raw_text.strip()) < 20

        return OCRResult(
            file_path=file_path,
            raw_text=raw_text.strip(),
            confidence=confidence,
            image_type=image_type,
            needs_review=needs_review,
            language=language,
            blocks=blocks,
        )

    except Exception as e:
        logger.error(f"OCR failed for {file_path}: {e}")
        return OCRResult(
            file_path=file_path,
            raw_text="",
            confidence=0.0,
            image_type="unknown",
            needs_review=True,
            language="zh",
            blocks=[],
        )
