"""CLI entry point. Wires Model and View; contains no business logic."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Optional

import click

from getmycar import __version__
from getmycar.cache import FileCache
from getmycar.config import Config, load_config
from getmycar.display import (
    display_comparison,
    display_favorites,
    display_search_results,
    display_vehicle_detail,
)
from getmycar.exceptions import GetMyCarError
from getmycar.favorites import FavoritesRepository, PresetsRepository
from getmycar.filters import SearchCriteria, Sort, build_query
from getmycar.logging import configure_logging
from getmycar.parser import parse_search_results
from getmycar.scraper import Scraper, ScraperProtocol
from getmycar.session import LastSearchStore

ScraperFactory = Callable[[Config, Path], ScraperProtocol]


def _default_scraper_factory(cfg: Config, data_dir: Path) -> ScraperProtocol:
    cache = FileCache(data_dir / "cache", ttl=timedelta(seconds=cfg.cache_ttl_seconds))
    return Scraper(
        cache=cache,
        user_agent=cfg.user_agent,
        request_interval=cfg.request_interval_seconds,
        max_retries=cfg.max_retries,
    )


def _favorites_repo(ctx: click.Context) -> FavoritesRepository:
    return FavoritesRepository(ctx.obj["data_dir"] / "favorites.json")


def _presets_repo(ctx: click.Context) -> PresetsRepository:
    return PresetsRepository(ctx.obj["data_dir"] / "presets.json")


def _last_search_store(ctx: click.Context) -> LastSearchStore:
    return LastSearchStore(ctx.obj["data_dir"] / "last_search.json")


@click.group()
@click.version_option(__version__)
@click.option("--config", "config_path", type=click.Path(path_type=Path), default=None)
@click.option("--data-dir", type=click.Path(path_type=Path), default=None)
@click.option("-v", "--verbose", count=True, help="Increase logging verbosity.")
@click.pass_context
def cli(
    ctx: click.Context,
    config_path: Optional[Path],
    data_dir: Optional[Path],
    verbose: int,
) -> None:
    """getmycar - Carsensor scraping CLI."""
    configure_logging(verbose)
    cfg = load_config(config_path)
    if ctx.obj is None:
        ctx.obj = {}
    ctx.obj.setdefault("config", cfg)
    ctx.obj.setdefault("data_dir", data_dir or cfg.data_dir)
    ctx.obj.setdefault("scraper_factory", _default_scraper_factory)


# --- search ----------------------------------------------------------


_search_options = [
    click.option("--maker"),
    click.option("--model", "model"),
    click.option("--price-min", type=int),
    click.option("--price-max", type=int),
    click.option("--year-min", type=int),
    click.option("--year-max", type=int),
    click.option("--mileage-max", type=int),
    click.option("--prefecture"),
    click.option(
        "--sort",
        type=click.Choice([s.value for s in Sort]),
        default=Sort.NEWEST.value,
    ),
    click.option("--page", type=int, default=1),
    click.option("--per-page", type=int, default=None),
]


def _add_search_options(f: Callable[..., Any]) -> Callable[..., Any]:
    for opt in reversed(_search_options):
        f = opt(f)
    return f


def _criteria_from_kwargs(
    keyword: Optional[str], cfg: Config, **kw: Any
) -> SearchCriteria:
    return SearchCriteria(
        keyword=keyword,
        maker=kw.get("maker"),
        model=kw.get("model"),
        price_min=kw.get("price_min"),
        price_max=kw.get("price_max"),
        year_min=kw.get("year_min"),
        year_max=kw.get("year_max"),
        mileage_max=kw.get("mileage_max"),
        prefecture=kw.get("prefecture"),
        sort=Sort(kw.get("sort", Sort.NEWEST.value)),
        page=kw.get("page", 1),
        per_page=kw.get("per_page") or cfg.default_per_page,
    )


@cli.command()
@click.argument("keyword", required=False)
@_add_search_options
@click.pass_context
def search(ctx: click.Context, /, keyword: Optional[str], **kw: Any) -> None:
    """Search Carsensor and display matching vehicles."""
    cfg: Config = ctx.obj["config"]
    criteria = _criteria_from_kwargs(keyword, cfg, **kw)
    scraper = ctx.obj["scraper_factory"](cfg, ctx.obj["data_dir"])
    url = build_query(criteria)
    try:
        body = scraper.get(url)
        vehicles = parse_search_results(body.decode("utf-8"))
    except GetMyCarError as e:
        raise click.ClickException(str(e)) from e
    _last_search_store(ctx).save(vehicles)
    display_search_results(vehicles)


# --- favorites -------------------------------------------------------


@cli.group()
def favorites() -> None:
    """Manage the favorites list."""


@favorites.command("add")
@click.argument("vehicle_id")
@click.pass_context
def favorites_add(ctx: click.Context, vehicle_id: str) -> None:
    vehicle = _last_search_store(ctx).find(vehicle_id)
    if vehicle is None:
        raise click.ClickException(
            f"vehicle id {vehicle_id} not found in last search results"
        )
    _favorites_repo(ctx).add(vehicle)
    click.echo(f"added {vehicle_id}")


@favorites.command("remove")
@click.argument("vehicle_id")
@click.pass_context
def favorites_remove(ctx: click.Context, vehicle_id: str) -> None:
    _favorites_repo(ctx).remove(vehicle_id)
    click.echo(f"removed {vehicle_id}")


@favorites.command("list")
@click.pass_context
def favorites_list(ctx: click.Context) -> None:
    display_favorites(_favorites_repo(ctx).list())


@favorites.command("compare")
@click.argument("vehicle_ids", nargs=-1, required=True)
@click.pass_context
def favorites_compare(ctx: click.Context, vehicle_ids: tuple[str, ...]) -> None:
    items = _favorites_repo(ctx).list()
    by_id = {v.id: v for v in items}
    selected = [by_id[i] for i in vehicle_ids if i in by_id]
    if len(selected) != len(vehicle_ids):
        missing = [i for i in vehicle_ids if i not in by_id]
        raise click.ClickException(f"unknown ids: {', '.join(missing)}")
    display_comparison(selected)


@favorites.command("show")
@click.argument("vehicle_id")
@click.pass_context
def favorites_show(ctx: click.Context, vehicle_id: str) -> None:
    for v in _favorites_repo(ctx).list():
        if v.id == vehicle_id:
            display_vehicle_detail(v)
            return
    raise click.ClickException(f"unknown id: {vehicle_id}")


# --- presets ---------------------------------------------------------


@cli.group()
def preset() -> None:
    """Manage saved search presets."""


@preset.command("save")
@click.argument("name")
@click.argument("keyword", required=False)
@_add_search_options
@click.pass_context
def preset_save(
    ctx: click.Context, /, name: str, keyword: Optional[str], **kw: Any
) -> None:
    cfg: Config = ctx.obj["config"]
    criteria = _criteria_from_kwargs(keyword, cfg, **kw)
    _presets_repo(ctx).save(name, criteria)
    click.echo(f"saved preset {name}")


@preset.command("load")
@click.argument("name")
@click.pass_context
def preset_load(ctx: click.Context, name: str) -> None:
    criteria = _presets_repo(ctx).load(name)
    click.echo(build_query(criteria))


@preset.command("list")
@click.pass_context
def preset_list(ctx: click.Context) -> None:
    for n in _presets_repo(ctx).list():
        click.echo(n)


# --- cache -----------------------------------------------------------


@cli.group()
def cache() -> None:
    """Manage the on-disk response cache."""


@cache.command("clear")
@click.pass_context
def cache_clear(ctx: click.Context) -> None:
    cfg: Config = ctx.obj["config"]
    file_cache = FileCache(
        ctx.obj["data_dir"] / "cache",
        ttl=timedelta(seconds=cfg.cache_ttl_seconds),
    )
    file_cache.clear()
    click.echo("cache cleared")


if __name__ == "__main__":
    cli()
