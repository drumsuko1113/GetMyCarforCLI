"""Carsensor HTML parser.

Selectors are encoded as module constants so they can be tweaked centrally
when Carsensor's markup changes. They were calibrated against live
``/usedcar/bXX/sYYY/index.html`` and ``/usedcar/detail/AU<id>/index.html``
pages — see tests/fixtures/carsensor_*.html.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from bs4 import BeautifulSoup, Tag

from getmycar.exceptions import ParseError
from getmycar.logging import get_logger

_log = get_logger(__name__)

# Search results: each car listing is a `cassette js_listTableCassette` wrapper
# whose id is `<vehicle_id>_cas`. It contains a `cassetteMain` (price, year,
# mileage, etc.) and a sibling `cassetteSub` (shop area).
_RESULT_WRAPPER: Final = "div.cassette.js_listTableCassette"

_BASE_HOST: Final = "https://www.carsensor.net"


@dataclass(frozen=True)
class Vehicle:
    id: str
    title: str
    url: str
    price_man: int | None = None  # 支払総額(万円)
    base_price_man: int | None = None  # 車両本体価格(万円)
    year: int | None = None
    mileage_km: int | None = None
    location: str | None = None
    image_url: str | None = None


def parse_search_results(html: str) -> list[Vehicle]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(_RESULT_WRAPPER)
    if not items:
        raise ParseError("no vehicle items found in search results HTML")
    return [_vehicle_from_cassette(item) for item in items]


def parse_detail(html: str) -> Vehicle:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.select_one("h1.title1")
    if h1 is None:
        raise ParseError("detail page missing h1.title1")
    title = h1.get_text(" ", strip=True)
    vehicle_id = _extract_id_from_anywhere(html)
    if not vehicle_id:
        raise ParseError("could not extract vehicle id from detail page")
    return Vehicle(
        id=vehicle_id,
        title=title,
        url=f"{_BASE_HOST}/usedcar/detail/{vehicle_id}/index.html",
        year=_parse_int(_spec_value(soup, "年式")),
        mileage_km=_parse_mileage(_spec_value(soup, "走行距離") + "万km"),
    )


# --- helpers ---------------------------------------------------------


def _vehicle_from_cassette(item: Tag) -> Vehicle:
    raw_id = item.get("id", "")
    vehicle_id = (
        str(raw_id)[:-4] if isinstance(raw_id, str) and raw_id.endswith("_cas") else str(raw_id)
    )
    title_link = item.select_one("h3.cassetteMain__title a")
    if title_link is None:
        raise ParseError(f"cassette {vehicle_id} missing title link")
    title = title_link.get_text(" ", strip=True)
    href = _attr(title_link, "href") or ""
    return Vehicle(
        id=vehicle_id,
        title=title,
        url=f"{_BASE_HOST}{href}" if href.startswith("/") else href,
        price_man=_parse_combined_price(
            item.select_one(".totalPrice__mainPriceNum"),
            item.select_one(".totalPrice__subPriceNum"),
        ),
        base_price_man=_parse_combined_price(
            item.select_one(".basePrice__mainPriceNum"),
            item.select_one(".basePrice__subPriceNum"),
        ),
        year=_parse_int(_text(_spec_box_value(item, "年式"))),
        mileage_km=_parse_mileage_from_spec_box(item, "走行距離"),
        location=_text(item.select_one(".cassetteSub__area p")) or None,
        image_url=_first_noscript_img(item),
    )


def _spec_box_value(item: Tag, label: str) -> Tag | None:
    """Find the ``specList__data`` block whose preceding title equals *label*."""
    for box in item.select(".specList__detailBox"):
        title = box.select_one(".specList__title")
        if title and label in title.get_text(strip=True):
            data = box.select_one(".specList__emphasisData")
            return data if data is not None else box.select_one(".specList__data")
    return None


def _parse_mileage_from_spec_box(item: Tag, label: str) -> int | None:
    """The spec box renders e.g. ``<emphasis>2</emphasis>万km``."""
    for box in item.select(".specList__detailBox"):
        title = box.select_one(".specList__title")
        if title and label in title.get_text(strip=True):
            data = box.select_one(".specList__data")
            if data is not None:
                return _parse_mileage(data.get_text(strip=True))
    return None


def _spec_value(soup: BeautifulSoup, label: str) -> str:
    """For the detail page's specWrap__box layout."""
    for box in soup.select(".specWrap__box"):
        title = box.select_one(".specWrap__box__title")
        if title and label in title.get_text(strip=True):
            num = box.select_one(".specWrap__box__num")
            if num is not None:
                return num.get_text(strip=True)
    return ""


def _parse_combined_price(main: Tag | None, sub: Tag | None) -> int | None:
    """``<span main>323</span><span sub>.9</span>`` → 324 (rounded)."""
    if main is None:
        return None
    main_text = main.get_text(strip=True)
    sub_text = sub.get_text(strip=True) if sub is not None else ""
    try:
        value = float(main_text + (sub_text if sub_text.startswith(".") else ""))
    except ValueError:
        return None
    return round(value)


def _first_noscript_img(item: Tag) -> str | None:
    ns = item.find("noscript")
    if ns is None:
        return None
    img = BeautifulSoup(ns.decode_contents(), "html.parser").find("img")
    if img is None:
        return None
    src = img.get("src")
    if src is None:
        return None
    if isinstance(src, list):
        src = " ".join(src)
    if src.startswith("//"):
        return f"https:{src}"
    return src


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


def _parse_mileage(text: str) -> int | None:
    """Convert e.g. '2万km' or '5.2万km' to km. Returns None if unparseable."""
    if not text or "不明" in text:
        return None
    m = re.search(r"([\d.]+)\s*万", text)
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"([\d,]+)", text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:  # pragma: no cover
            return None
    return None


def _extract_id_from_anywhere(html: str) -> str:
    m = re.search(r"/usedcar/detail/(AU\d+)/", html)
    if m:
        return m.group(1)
    m = re.search(r'data-vehicle-id="(AU\d+)"', html)
    if m:
        return m.group(1)
    m = re.search(r"\bAU\d{8,}\b", html)
    return m.group(0) if m else ""
