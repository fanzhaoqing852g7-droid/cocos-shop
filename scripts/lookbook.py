"""Shared paths and item codes for the Coco's Shop lookbook."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PHOTOS = ROOT / "photos"
CONFIG_PATH = DATA / "config.json"
ITEMS_PATH = DATA / "items.json"


def load_config() -> dict:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing {CONFIG_PATH.relative_to(ROOT)}. Restore data/config.json.")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{CONFIG_PATH.relative_to(ROOT)} is not valid JSON: {exc}") from exc
    if not isinstance(config, dict):
        raise SystemExit("data/config.json must be an object.")
    return config


def load_items() -> list[dict]:
    if not ITEMS_PATH.exists():
        return []
    try:
        items = json.loads(ITEMS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"data/items.json is not valid JSON: {exc}") from exc
    if not isinstance(items, list):
        raise SystemExit("data/items.json must be a list.")
    return items


def _code_key(item: dict) -> tuple:
    code = str(item.get("code", ""))
    head, _, tail = code.rpartition("-")
    if tail.isdigit():
        return (head, int(tail))
    return (code, 0)


def save_items(items: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    ordered = sorted(items, key=_code_key)
    ordered.sort(key=lambda item: str(item.get("date", "")), reverse=True)
    ITEMS_PATH.write_text(
        json.dumps(ordered, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Date must be YYYY-MM-DD, got {value!r}.") from exc


def categories_from(config: dict) -> list[str]:
    categories = config.get("categories") or []
    if not categories or not all(isinstance(cat, str) and cat.strip() for cat in categories):
        raise SystemExit("data/config.json needs a non-empty categories list.")
    return list(categories)


def canonical_category(name: str, categories: list[str]) -> str | None:
    for category in categories:
        if category.lower() == name.strip().lower():
            return category
    return None


def tidy_title(text: str) -> str:
    words = re.split(r"[\s_\-]+", text.strip())
    small = {"and", "of", "the", "a", "an", "with", "for"}
    titled: list[str] = []
    for index, word in enumerate(words):
        if not word:
            continue
        lower = word.lower()
        if index and lower in small:
            titled.append(lower)
        elif word.isupper() and len(word) <= 4:
            titled.append(word)
        else:
            titled.append(word[:1].upper() + word[1:])
    return " ".join(titled)


def category_from_stem(stem: str, categories: list[str], default: str) -> tuple[str, str]:
    """Read a leading category from a filename stem, such as dresses-ivory-slip."""
    for category in sorted(categories, key=len, reverse=True):
        match = re.match(
            rf"^{re.escape(category)}(?:[\s_\-]+(.*))?$",
            stem,
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        rest = match.group(1) or ""
        return category, tidy_title(rest) or category
    return default, tidy_title(stem) or stem


def make_code(prefix: str, date_str: str, seq: int) -> str:
    stamp = parse_date(date_str)
    width = 2 if seq < 100 else len(str(seq))
    return f"{prefix}-{stamp.month:02d}{stamp.day:02d}-{seq:0{width}d}"


def next_sequence(items: list[dict], prefix: str, date_str: str) -> int:
    stamp = parse_date(date_str)
    stem = f"{prefix}-{stamp.month:02d}{stamp.day:02d}-"
    best = 0
    for item in items:
        code = str(item.get("code", ""))
        if not code.startswith(stem):
            continue
        tail = code[len(stem) :]
        if tail.isdigit():
            best = max(best, int(tail))
    return best + 1


def rel_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()
