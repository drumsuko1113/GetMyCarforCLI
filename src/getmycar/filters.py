"""Search criteria, query construction, and the Filter strategy hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Protocol
from urllib.parse import urlencode

_BASE_URL: Final = "https://www.carsensor.net/usedcar/search.php"


class Sort(str, Enum):
    NEWEST = "newest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


@dataclass(frozen=True)
class SearchCriteria:
    keyword: str | None = None
    maker: str | None = None
    model: str | None = None
    price_min: int | None = None
    price_max: int | None = None
    year_min: int | None = None
    year_max: int | None = None
    mileage_max: int | None = None
    prefecture: str | None = None
    sort: Sort = Sort.NEWEST
    page: int = 1
    per_page: int = 20


class Filter(Protocol):
    def apply(self, params: dict[str, str]) -> None: ...


@dataclass(frozen=True)
class PriceFilter:
    min_man: int | None
    max_man: int | None

    def apply(self, params: dict[str, str]) -> None:
        if self.min_man is not None:
            params["PRICE_MIN"] = str(self.min_man)
        if self.max_man is not None:
            params["PRICE_MAX"] = str(self.max_man)


@dataclass(frozen=True)
class YearFilter:
    min_year: int | None
    max_year: int | None

    def apply(self, params: dict[str, str]) -> None:
        if self.min_year is not None:
            params["YEAR_MIN"] = str(self.min_year)
        if self.max_year is not None:
            params["YEAR_MAX"] = str(self.max_year)


@dataclass(frozen=True)
class MileageFilter:
    max_km: int | None

    def apply(self, params: dict[str, str]) -> None:
        if self.max_km is not None:
            params["MILEAGE_MAX"] = str(self.max_km)


@dataclass(frozen=True)
class LocationFilter:
    prefecture: str | None

    def apply(self, params: dict[str, str]) -> None:
        if self.prefecture:
            params["AREA"] = self.prefecture


@dataclass(frozen=True)
class MakerFilter:
    maker: str | None
    model: str | None

    def apply(self, params: dict[str, str]) -> None:
        if self.maker:
            params["MAKER"] = self.maker
        if self.model:
            params["MODEL"] = self.model


def build_query(criteria: SearchCriteria) -> str:
    """Compose the Carsensor search URL for *criteria*."""
    params: dict[str, str] = {}
    if criteria.keyword:
        params["FREEWORD"] = criteria.keyword
    filters: list[Filter] = [
        MakerFilter(criteria.maker, criteria.model),
        PriceFilter(criteria.price_min, criteria.price_max),
        YearFilter(criteria.year_min, criteria.year_max),
        MileageFilter(criteria.mileage_max),
        LocationFilter(criteria.prefecture),
    ]
    for f in filters:
        f.apply(params)
    params["SORT"] = criteria.sort.value
    params["PAGE"] = str(criteria.page)
    params["PER_PAGE"] = str(criteria.per_page)
    return f"{_BASE_URL}?{urlencode(params)}"
