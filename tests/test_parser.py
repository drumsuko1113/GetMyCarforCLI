from __future__ import annotations

from pathlib import Path

import pytest

from getmycar.exceptions import ParseError
from getmycar.parser import Vehicle, parse_detail, parse_search_results

_FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def search_html() -> str:
    return (_FIXTURES / "search_results.html").read_text(encoding="utf-8")


@pytest.fixture
def detail_html() -> str:
    return (_FIXTURES / "detail.html").read_text(encoding="utf-8")


def test_parse_search_results_extracts_all_vehicles(search_html: str) -> None:
    vehicles = parse_search_results(search_html)
    assert len(vehicles) == 3
    ids = [v.id for v in vehicles]
    assert ids == ["V001", "V002", "V003"]


def test_parse_search_results_populates_fields(search_html: str) -> None:
    v = parse_search_results(search_html)[0]
    assert v.id == "V001"
    assert v.title == "トヨタ プリウス S"
    assert v.price_man == 120
    assert v.year == 2018
    assert v.mileage_km == 52000
    assert v.location == "東京都"
    assert v.url.endswith("V001/index.html")
    assert v.image_url == "https://example.com/img/v001.jpg"


def test_parse_search_results_handles_missing_price_and_mileage(search_html: str) -> None:
    v = parse_search_results(search_html)[2]
    assert v.id == "V003"
    assert v.price_man is None
    assert v.mileage_km is None
    assert v.image_url is None


def test_parse_detail_returns_vehicle(detail_html: str) -> None:
    v = parse_detail(detail_html)
    assert v.id == "V001"
    assert v.title == "トヨタ プリウス S"
    assert v.price_man == 120
    assert v.year == 2018
    assert v.mileage_km == 52000
    assert v.location == "東京都"
    assert v.image_url == "https://example.com/img/v001-hero.jpg"


def test_parse_search_results_raises_on_unrecognised_html() -> None:
    with pytest.raises(ParseError):
        parse_search_results("<html><body>nothing useful</body></html>")


def test_parse_detail_raises_on_unrecognised_html() -> None:
    with pytest.raises(ParseError):
        parse_detail("<html></html>")


def test_vehicle_is_frozen() -> None:
    v = Vehicle(id="x", title="t", url="u")
    with pytest.raises(Exception):
        v.title = "y"  # type: ignore[misc]
