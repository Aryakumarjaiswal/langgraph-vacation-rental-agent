
from __future__ import annotations

import math
import re
from html.parser import HTMLParser
from typing import Any

import pandas as pd

NAN_TOKENS = {"", "nan", "none", "null", "nat", "<na>"}

SECTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "identity": (
        "property_id",
        "listing_id",
        "listing_title",
        "unit_name",
        "id",
        "name",
        "title",
        "status",
        "property_status",
    ),
    "location": (
        "address",
        "city",
        "state",
        "province",
        "zip",
        "country",
        "latitude",
        "longitude",
        "building",
        "direction",
        "full_address",
    ),
    "access": (
        "wifi",
        "access",
        "guest_access",
        "lock",
        "code",
        "parking",
        "check_in",
        "checkin",
        "checkout",
        "check_out",
        "trash",
        "general",
    ),
    "amenities": (
        "about",
        "amenit",
        "bed",
        "bath",
        "kitchen",
        "guest",
        "sleep",
        "notes",
        "description",
        "house_rule",
    ),
    "pricing": (
        "price",
        "fee",
        "commission",
        "currency",
        "night",
        "tax",
        "deposit",
        "weekend",
        "monthly",
        "weekly",
    ),
}


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def get_text(self) -> str:
        return " ".join(self._chunks)


def strip_html(value: str) -> str:
    if "<" not in value:
        return value
    parser = _HTMLStripper()
    try:
        parser.feed(value)
        text = parser.get_text()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", text).strip()


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip()
    return text.lower() in NAN_TOKENS


def clean_value(value: Any) -> str:
    return strip_html(str(value).strip())


def feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c != "summary"]


def build_summary_row(row: pd.Series, columns: list[str]) -> str:
    parts: list[str] = []
    for col in columns:
        value = row[col]
        if is_empty(value):
            continue
        parts.append(f"{col}: {clean_value(value)}")
    return "; ".join(parts)


def build_summary_column(df: pd.DataFrame) -> pd.DataFrame:
    
    out = df.copy()
    cols = feature_columns(out)
    out["summary"] = out.apply(lambda row: build_summary_row(row, cols), axis=1)
    return out


def section_for(column: str) -> str:
    lowered = column.lower()
    for section, keys in SECTION_KEYWORDS.items():
        if any(key in lowered for key in keys):
            return section
    return "other"


def split_words(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if len(words) <= chunk_size:
        return [text] if text.strip() else []
    chunks: list[str] = []
    start = 0
    step = max(chunk_size - overlap, 1)
    while start < len(words):
        piece = " ".join(words[start : start + chunk_size]).strip()
        if piece:
            chunks.append(piece)
        start += step
    return chunks


def chunks_from_summary(
    summary: str,
    property_id: str,
    max_words: int = 180,
    overlap_words: int = 30,
) -> list[dict[str, Any]]:
    """Turn a programmatic summary into retrieval-optimized chunks with metadata."""
    fields: list[tuple[str, str]] = []
    for part in re.split(r"\s*;\s*", summary):
        if ": " not in part:
            continue
        col, val = part.split(": ", 1)
        if val.strip():
            fields.append((col.strip(), val.strip()))

    grouped: dict[str, list[tuple[str, str]]] = {}
    for col, val in fields:
        grouped.setdefault(section_for(col), []).append((col, val))

    chunks: list[dict[str, Any]] = []
    identity_bits = grouped.get("identity", [])[:8]
    location_bits = grouped.get("location", [])[:8]
    profile = "; ".join(f"{c}: {v}" for c, v in identity_bits + location_bits)
    if profile:
        chunks.append(
            {
                "text": f"Property profile for ID {property_id}. {profile}",
                "section": "profile",
                "property_id": property_id,
            }
        )

    for section, items in grouped.items():
        block = "; ".join(f"{c}: {v}" for c, v in items)
        for piece in split_words(block, max_words, overlap_words):
            chunks.append(
                {
                    "text": piece,
                    "section": section,
                    "property_id": property_id,
                }
            )
    return chunks


def resolve_property_id(row: pd.Series) -> str:
    for key in ("property_id", "id"):
        if key in row.index and not is_empty(row[key]):
            value = row[key]
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value).strip()
    raise ValueError("Row is missing property_id / id")



