from __future__ import annotations

from rich.console import Console

from getmycar.display import (
    display_comparison,
    display_favorites,
    display_search_results,
    display_vehicle_detail,
)
from getmycar.parser import Vehicle


def _vehicle(vid: str = "V1", title: str = "プリウス", price: int = 120) -> Vehicle:
    return Vehicle(
        id=vid,
        title=title,
        url=f"https://example.com/{vid}",
        price_man=price,
        year=2018,
        mileage_km=50000,
        location="東京都",
    )


def _capture(fn, *args, **kwargs) -> str:  # type: ignore[no-untyped-def]
    console = Console(record=True, width=120)
    fn(*args, console=console, **kwargs)
    return console.export_text()


def test_search_results_show_titles_and_prices() -> None:
    out = _capture(
        display_search_results, [_vehicle("V1", "プリウス", 120), _vehicle("V2", "フィット", 85)]
    )
    assert "プリウス" in out
    assert "フィット" in out
    assert "120" in out
    assert "85" in out


def test_search_results_show_empty_state() -> None:
    out = _capture(display_search_results, [])
    assert "0" in out or "no" in out.lower() or "該当" in out


def test_vehicle_detail_renders_all_fields() -> None:
    out = _capture(display_vehicle_detail, _vehicle())
    assert "プリウス" in out
    assert "120" in out
    assert "2018" in out
    assert "東京都" in out


def test_comparison_lists_each_vehicle_id() -> None:
    out = _capture(display_comparison, [_vehicle("V1"), _vehicle("V2"), _vehicle("V3")])
    assert "V1" in out
    assert "V2" in out
    assert "V3" in out


def test_favorites_view_uses_search_layout() -> None:
    out = _capture(display_favorites, [_vehicle("V1")])
    assert "プリウス" in out
