"""Carsensor HTML parser.

Selectors are encoded as module constants so they can be tweaked centrally
when Carsensor's markup changes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from bs4 import BeautifulSoup, Tag

from getmycar.exceptions import ParseError
from getmycar.logging import get_logger

_log = get_logger(__name__)

_SEARCH_ITEM_SELECTOR: Final = "div.casseteMain__wrap"
_DETAIL_ROOT_SELECTOR: Final = "div.detailMain"


@dataclass(frozen=True)
class Vehicle:
    id: str
    title: str
    url: str
    price_man: int | None = None
    year: int | None = None
    mileage_km: int | None = None
    location: str | None = None
    image_url: str | None = None


def parse_search_results(html: str) -> list[Vehicle]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(_SEARCH_ITEM_SELECTOR)
    if not items:
        raise ParseError("no vehicle items found in search results HTML")
    return [_vehicle_from_search_item(item) for item in items]


def parse_detail(html: str) -> Vehicle:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one(_DETAIL_ROOT_SELECTOR)
    if root is None:
        raise ParseError("detail root not found")
    vehicle_id = root.get("data-vehicle-id")
    title = _text(root.select_one("h1.detailTitle"))
    if not vehicle_id or not title:
        raise ParseError("detail page missing id or title")
    return Vehicle(
        id=str(vehicle_id),
        title=title,
        url="",
        price_man=_parse_price(_text(root.select_one("p.detailPrice .totalPrice"))),
        year=_parse_int(_text(root.select_one(".js-modelYear"))),
        mileage_km=_parse_mileage(_text(root.select_one(".js-mileage"))),
        location=_text(root.select_one(".js-shopArea")) or None,
        image_url=_attr(root.select_one("img.hero"), "src"),
    )


# --- helpers ---------------------------------------------------------


def _vehicle_from_search_item(item: Tag) -> Vehicle:
    title_el = item.select_one("a.title")
    if title_el is None:
        raise ParseError("search item missing title link")
    return Vehicle(
        id=str(item.get("data-vehicle-id", "")),
        title=_text(title_el),
        url=_attr(title_el, "href") or "",
        price_man=_parse_price(_text(item.select_one(".basePrice .totalPrice"))),
        year=_parse_int(_text(item.select_one(".js-modelYear"))),
        mileage_km=_parse_mileage(_text(item.select_one(".js-mileage"))),
        location=_text(item.select_one(".js-shopArea")) or None,
        image_url=_attr(item.select_one("img.thumb"), "src"),
    )


def _text(tag: Tag | None) -> str:
    return tag.get_text(strip=True) if tag is not None else ""


def _attr(tag: Tag | None, name: str) -> str | None:
    if tag is None:
        return None
    value = tag.get(name)
    if value is None:
        return None
    return value if isinstance(value, str) else " ".join(value)


def _parse_int(text: str) -> int | None:
    m = re.search(r"\d+", text)
    return int(m.group()) if m else None


def _parse_price(text: str) -> int | None:
    if not text or "応談" in text:
        return None
    return _parse_int(text)


def _parse_mileage(text: str) -> int | None:
    """Convert e.g. '5.2万km' to 52000. Returns None if unparseable."""
    if not text or "不明" in text:
        return None
    m = re.search(r"([\d.]+)\s*万", text)
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"([\d,]+)", text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:  # pragma: no cover - defensive
            return None
    return None
