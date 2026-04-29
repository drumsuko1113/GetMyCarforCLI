from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from getmycar.filters import (
    KeywordFilter,
    MileageFilter,
    PriceFilter,
    SearchCriteria,
    Sort,
    TotalPriceFilter,
    YearFilter,
    build_query,
)


def test_keyword_filter_sets_kw() -> None:
    params: dict[str, str] = {}
    KeywordFilter("プリウス").apply(params)
    assert params["KW"] == "プリウス"


def test_keyword_filter_no_op_when_empty() -> None:
    params: dict[str, str] = {}
    KeywordFilter(None).apply(params)
    assert params == {}


def test_price_filter_sets_pmin_pmax() -> None:
    params: dict[str, str] = {}
    PriceFilter(min_man=100, max_man=300).apply(params)
    assert params["PMIN"] == "100"
    assert params["PMAX"] == "300"


def test_price_filter_skips_unset_bounds() -> None:
    params: dict[str, str] = {}
    PriceFilter(min_man=None, max_man=200).apply(params)
    assert "PMIN" not in params
    assert params["PMAX"] == "200"


def test_total_price_filter_sets_lmmin_lmmax() -> None:
    params: dict[str, str] = {}
    TotalPriceFilter(min_man=50, max_man=150).apply(params)
    assert params["LMMIN"] == "50"
    assert params["LMMAX"] == "150"


def test_year_filter_only_min() -> None:
    params: dict[str, str] = {}
    YearFilter(min_year=2018, max_year=None).apply(params)
    assert params["YMIN"] == "2018"
    assert "YMAX" not in params


def test_mileage_filter_converts_km_to_man_km() -> None:
    params: dict[str, str] = {}
    MileageFilter(max_km=80000).apply(params)
    assert params["SMAX"] == "8"


def test_mileage_filter_no_op_when_unset() -> None:
    params: dict[str, str] = {}
    MileageFilter(max_km=None).apply(params)
    assert params == {}


def test_build_query_uses_keyword_and_price() -> None:
    url = build_query(SearchCriteria(keyword="プリウス", price_max=200, year_min=2018))
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    assert "carsensor.net" in parsed.netloc
    assert parsed.path.endswith("/usedcar/index.html")
    assert qs["KW"] == ["プリウス"]
    assert qs["PMAX"] == ["200"]
    assert qs["YMIN"] == ["2018"]


def test_build_query_uses_path_for_maker_and_model() -> None:
    url = build_query(SearchCriteria(maker="TO", model="s122"))
    parsed = urlparse(url)
    assert parsed.path == "/usedcar/bTO/s122/index.html"


def test_build_query_uses_path_for_prefecture() -> None:
    url = build_query(SearchCriteria(prefecture="tokyo"))
    assert urlparse(url).path == "/usedcar/tokyo/index.html"


def test_build_query_emits_page_segment_when_paginating() -> None:
    url = build_query(SearchCriteria(page=3))
    assert urlparse(url).path == "/usedcar/index3.html"


def test_build_query_emits_low_total_price_segment() -> None:
    url = build_query(SearchCriteria(sort=Sort.PRICE_ASC))
    assert urlparse(url).path == "/usedcar/low_totalPrice/index.html"


def test_build_query_default_path_no_segments() -> None:
    url = build_query(SearchCriteria())
    parsed = urlparse(url)
    assert parsed.path == "/usedcar/index.html"
    assert parsed.query == ""


@pytest.mark.parametrize(
    "sort,expected_segment",
    [(Sort.NEWEST, "index.html"), (Sort.PRICE_ASC, "low_totalPrice/index.html")],
)
def test_sort_segments(sort: Sort, expected_segment: str) -> None:
    url = build_query(SearchCriteria(sort=sort))
    assert urlparse(url).path.endswith(expected_segment)


def test_open_for_extension_with_custom_filter() -> None:
    """Adding a Filter does not require modifying build_query."""
    from getmycar.filters import Filter

    class TagFilter:
        def __init__(self, tag: str) -> None:
            self.tag = tag

        def apply(self, params: dict[str, str]) -> None:
            params["TAG"] = self.tag

    f: Filter = TagFilter("hybrid")
    params: dict[str, str] = {}
    f.apply(params)
    assert params["TAG"] == "hybrid"
