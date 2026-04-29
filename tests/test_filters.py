from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from getmycar.filters import (
    LocationFilter,
    MileageFilter,
    PriceFilter,
    SearchCriteria,
    Sort,
    YearFilter,
    build_query,
)


def test_price_filter_sets_min_and_max() -> None:
    params: dict[str, str] = {}
    PriceFilter(min_man=100, max_man=300).apply(params)
    assert params["PRICE_MIN"] == "100"
    assert params["PRICE_MAX"] == "300"


def test_price_filter_skips_unset_bounds() -> None:
    params: dict[str, str] = {}
    PriceFilter(min_man=None, max_man=200).apply(params)
    assert "PRICE_MIN" not in params
    assert params["PRICE_MAX"] == "200"


def test_year_filter_only_min() -> None:
    params: dict[str, str] = {}
    YearFilter(min_year=2018, max_year=None).apply(params)
    assert params["YEAR_MIN"] == "2018"
    assert "YEAR_MAX" not in params


def test_mileage_filter_max_km() -> None:
    params: dict[str, str] = {}
    MileageFilter(max_km=80000).apply(params)
    assert params["MILEAGE_MAX"] == "80000"


def test_mileage_filter_no_op_when_unset() -> None:
    params: dict[str, str] = {}
    MileageFilter(max_km=None).apply(params)
    assert params == {}


def test_location_filter_sets_prefecture() -> None:
    params: dict[str, str] = {}
    LocationFilter(prefecture="東京都").apply(params)
    assert params["AREA"] == "東京都"


def test_build_query_includes_keyword_and_filters() -> None:
    criteria = SearchCriteria(
        keyword="プリウス",
        price_max=200,
        year_min=2018,
        sort=Sort.PRICE_ASC,
        page=2,
        per_page=30,
    )
    url = build_query(criteria)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    assert "carsensor.net" in parsed.netloc
    assert qs["FREEWORD"] == ["プリウス"]
    assert qs["PRICE_MAX"] == ["200"]
    assert qs["YEAR_MIN"] == ["2018"]
    assert qs["SORT"] == ["price_asc"]
    assert qs["PAGE"] == ["2"]
    assert qs["PER_PAGE"] == ["30"]


def test_build_query_omits_unset_keyword() -> None:
    url = build_query(SearchCriteria())
    qs = parse_qs(urlparse(url).query)
    assert "FREEWORD" not in qs


@pytest.mark.parametrize(
    "sort,expected",
    [
        (Sort.NEWEST, "newest"),
        (Sort.PRICE_ASC, "price_asc"),
        (Sort.PRICE_DESC, "price_desc"),
    ],
)
def test_sort_serialization(sort: Sort, expected: str) -> None:
    qs = parse_qs(urlparse(build_query(SearchCriteria(sort=sort))).query)
    assert qs["SORT"] == [expected]


def test_open_for_extension_with_custom_filter() -> None:
    """Adding a new Filter subclass must not require modifying build_query."""
    from getmycar.filters import Filter

    class TagFilter:
        tag: str

        def __init__(self, tag: str) -> None:
            self.tag = tag

        def apply(self, params: dict[str, str]) -> None:
            params["TAG"] = self.tag

    f: Filter = TagFilter("hybrid")  # structural typing via Protocol
    params: dict[str, str] = {}
    f.apply(params)
    assert params["TAG"] == "hybrid"
