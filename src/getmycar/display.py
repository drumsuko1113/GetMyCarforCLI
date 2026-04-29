"""Rich-based TUI views. Pure presentation — no scraping or persistence."""
from __future__ import annotations

from typing import Iterable, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from getmycar.parser import Vehicle

_DEFAULT_CONSOLE = Console()


def _price_style(price_man: Optional[int]) -> str:
    if price_man is None:
        return "dim"
    if price_man < 100:
        return "green"
    if price_man < 200:
        return "yellow"
    return "red"


def _format_price(price_man: Optional[int]) -> str:
    return f"{price_man}万円" if price_man is not None else "-"


def _format_mileage(km: Optional[int]) -> str:
    if km is None:
        return "-"
    if km >= 10000:
        return f"{km / 10000:.1f}万km"
    return f"{km}km"


def _format_year(year: Optional[int]) -> str:
    return f"{year}" if year is not None else "-"


def _build_vehicle_table(vehicles: Iterable[Vehicle], title: str) -> Table:
    table = Table(title=title, show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("車種")
    table.add_column("年式", justify="right")
    table.add_column("走行距離", justify="right")
    table.add_column("価格", justify="right")
    table.add_column("地域")
    for v in vehicles:
        table.add_row(
            v.id,
            v.title,
            _format_year(v.year),
            _format_mileage(v.mileage_km),
            f"[{_price_style(v.price_man)}]{_format_price(v.price_man)}[/]",
            v.location or "-",
        )
    return table


def display_search_results(
    vehicles: list[Vehicle], *, console: Console = _DEFAULT_CONSOLE
) -> None:
    if not vehicles:
        console.print("[dim]該当 0 件[/]")
        return
    console.print(_build_vehicle_table(vehicles, title=f"検索結果 ({len(vehicles)} 件)"))


def display_favorites(
    vehicles: list[Vehicle], *, console: Console = _DEFAULT_CONSOLE
) -> None:
    if not vehicles:
        console.print("[dim]お気に入りはまだありません[/]")
        return
    console.print(_build_vehicle_table(vehicles, title=f"お気に入り ({len(vehicles)} 件)"))


def display_vehicle_detail(vehicle: Vehicle, *, console: Console = _DEFAULT_CONSOLE) -> None:
    body = (
        f"[bold]{vehicle.title}[/]\n"
        f"ID:       {vehicle.id}\n"
        f"年式:     {_format_year(vehicle.year)}\n"
        f"走行距離: {_format_mileage(vehicle.mileage_km)}\n"
        f"価格:     [{_price_style(vehicle.price_man)}]{_format_price(vehicle.price_man)}[/]\n"
        f"地域:     {vehicle.location or '-'}\n"
        f"URL:      {vehicle.url}"
    )
    console.print(Panel(body, title="詳細", border_style="blue"))


def display_comparison(
    vehicles: list[Vehicle], *, console: Console = _DEFAULT_CONSOLE
) -> None:
    table = Table(title="比較", show_lines=True)
    table.add_column("項目", style="bold", no_wrap=True)
    for v in vehicles:
        table.add_column(v.id, justify="left")
    fields: list[tuple[str, list[str]]] = [
        ("車種", [v.title for v in vehicles]),
        ("年式", [_format_year(v.year) for v in vehicles]),
        ("走行距離", [_format_mileage(v.mileage_km) for v in vehicles]),
        (
            "価格",
            [
                f"[{_price_style(v.price_man)}]{_format_price(v.price_man)}[/]"
                for v in vehicles
            ],
        ),
        ("地域", [v.location or "-" for v in vehicles]),
    ]
    for label, values in fields:
        table.add_row(label, *values)
    console.print(table)
