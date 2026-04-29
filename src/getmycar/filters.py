"""Search criteria, query construction, and the Filter strategy hierarchy.

URL design follows the live Carsensor pattern (search.php is disallowed by
robots.txt, so we build path-based URLs against the SEO-friendly endpoints):

  https://www.carsensor.net/usedcar/<area>/<low_totalPrice>/index<N>.html?KW=...&PMIN=...

Query parameter names match the names emitted by Carsensor's own search form
(KW/PMIN/PMAX/YMIN/YMAX/SMAX/AR/...). Filter strategies remain Open/Closed:
adding a new filter type just requires a class that writes into ``params``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Protocol
from urllib.parse import urlencode

_BASE_HOST: Final = "https://www.carsensor.net"
_BASE_PATH: Final = "/usedcar"


class Sort(str, Enum):
    """Only sorts with stable URL paths are exposed.

    Carsensor's other sort orders (year, mileage, base-price) are JS-driven
    and not addressable by URL alone, so we keep them off the public API.
    """

    NEWEST = "newest"  # default — no path segment
    PRICE_ASC = "price_asc"  # /low_totalPrice/


_SORT_PATHS: Final = {
    Sort.NEWEST: "",
    Sort.PRICE_ASC: "low_totalPrice/",
}


@dataclass(frozen=True)
class SearchCriteria:
    keyword: str | None = None
    maker: str | None = None  # e.g. "TO" for Toyota -> /bTO/
    model: str | None = None  # e.g. "s122" for Prius -> /bTO/s122/
    price_min: int | None = None  # 万円 (車両本体価格)
    price_max: int | None = None
    total_price_min: int | None = None  # 万円 (支払総額)
    total_price_max: int | None = None
    year_min: int | None = None
    year_max: int | None = None
    mileage_max: int | None = None  # km (converted to 万km for Carsensor)
    prefecture: str | None = None  # area slug, e.g. "tokyo"
    sort: Sort = Sort.NEWEST
    page: int = 1
    per_page: int = 20  # informational; Carsensor controls actual page size


class Filter(Protocol):
    def apply(self, params: dict[str, str]) -> None: ...


@dataclass(frozen=True)
class KeywordFilter:
    keyword: str | None

    def apply(self, params: dict[str, str]) -> None:
        if self.keyword:
            params["KW"] = self.keyword


@dataclass(frozen=True)
class PriceFilter:
    """Filters on 車両本体価格 (PMIN/PMAX)."""

    min_man: int | None
    max_man: int | None

    def apply(self, params: dict[str, str]) -> None:
        if self.min_man is not None:
            params["PMIN"] = str(self.min_man)
        if self.max_man is not None:
            params["PMAX"] = str(self.max_man)


@dataclass(frozen=True)
class TotalPriceFilter:
    """Filters on 支払総額 (LMMIN/LMMAX)."""

    min_man: int | None
    max_man: int | None

    def apply(self, params: dict[str, str]) -> None:
        if self.min_man is not None:
            params["LMMIN"] = str(self.min_man)
        if self.max_man is not None:
            params["LMMAX"] = str(self.max_man)


@dataclass(frozen=True)
class YearFilter:
    min_year: int | None
    max_year: int | None

    def apply(self, params: dict[str, str]) -> None:
        if self.min_year is not None:
            params["YMIN"] = str(self.min_year)
        if self.max_year is not None:
            params["YMAX"] = str(self.max_year)


@dataclass(frozen=True)
class MileageFilter:
    """Carsensor's SMAX is expressed in 万km, so we divide by 10000."""

    max_km: int | None

    def apply(self, params: dict[str, str]) -> None:
        if self.max_km is not None:
            params["SMAX"] = str(max(1, self.max_km // 10000))


def build_query(criteria: SearchCriteria) -> str:
    """Compose the Carsensor list URL for *criteria*."""
    path = _build_path(criteria)
    params: dict[str, str] = {}
    filters: list[Filter] = [
        KeywordFilter(criteria.keyword),
        PriceFilter(criteria.price_min, criteria.price_max),
        TotalPriceFilter(criteria.total_price_min, criteria.total_price_max),
        YearFilter(criteria.year_min, criteria.year_max),
        MileageFilter(criteria.mileage_max),
    ]
    for f in filters:
        f.apply(params)
    suffix = f"?{urlencode(params)}" if params else ""
    return f"{_BASE_HOST}{path}{suffix}"


def _build_path(criteria: SearchCriteria) -> str:
    parts = [_BASE_PATH]
    if criteria.prefecture:
        parts.append(criteria.prefecture)
    if criteria.maker:
        parts.append(f"b{criteria.maker}")
        if criteria.model:
            parts.append(criteria.model)
    sort_segment = _SORT_PATHS[criteria.sort]
    if sort_segment:
        parts.append(sort_segment.rstrip("/"))
    page_filename = "index.html" if criteria.page <= 1 else f"index{criteria.page}.html"
    parts.append(page_filename)
    return "/".join(parts).replace("//", "/")
