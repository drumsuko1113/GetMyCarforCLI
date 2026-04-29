"""User-facing configuration loaded from a TOML file."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found, unused-ignore]
from pathlib import Path
from typing import Any

from getmycar import __version__
from getmycar.exceptions import GetMyCarError


class ConfigError(GetMyCarError):
    """Raised when the configuration file is malformed or contains invalid values."""


@dataclass(frozen=True)
class Config:
    cache_ttl_seconds: int = 1800
    request_interval_seconds: float = 1.0
    max_retries: int = 3
    user_agent: str = f"getmycar/{__version__}"
    default_per_page: int = 20
    data_dir: Path = field(default_factory=lambda: Path("./data"))


def default_config_path() -> Path:
    """Return the OS-appropriate default location for ``config.toml``."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "getmycar" / "config.toml"


def load_config(path: Path | None = None) -> Config:
    """Load configuration from *path*, falling back to defaults when absent.

    Missing files are not an error — they yield an all-default :class:`Config`.
    Malformed TOML or out-of-range values raise :class:`ConfigError`.
    """
    target = path if path is not None else default_config_path()
    if not target.is_file():
        return Config()
    try:
        raw = tomllib.loads(target.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"invalid TOML at {target}: {e}") from e
    return _from_mapping(raw)


def _from_mapping(raw: dict[str, Any]) -> Config:
    cache = raw.get("cache", {})
    scraper = raw.get("scraper", {})
    search = raw.get("search", {})
    data = raw.get("data", {})
    defaults = Config()

    cfg = Config(
        cache_ttl_seconds=int(cache.get("ttl_seconds", defaults.cache_ttl_seconds)),
        request_interval_seconds=float(
            scraper.get("request_interval_seconds", defaults.request_interval_seconds)
        ),
        max_retries=int(scraper.get("max_retries", defaults.max_retries)),
        user_agent=str(scraper.get("user_agent", defaults.user_agent)),
        default_per_page=int(search.get("default_per_page", defaults.default_per_page)),
        data_dir=Path(data.get("dir", defaults.data_dir)),
    )
    _validate(cfg)
    return cfg


def _validate(cfg: Config) -> None:
    if cfg.cache_ttl_seconds < 0:
        raise ConfigError("cache.ttl_seconds must be >= 0")
    if cfg.request_interval_seconds < 0:
        raise ConfigError("scraper.request_interval_seconds must be >= 0")
    if cfg.max_retries < 0:
        raise ConfigError("scraper.max_retries must be >= 0")
    if cfg.default_per_page <= 0:
        raise ConfigError("search.default_per_page must be > 0")
