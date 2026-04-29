from __future__ import annotations

from pathlib import Path

import pytest

from getmycar.config import Config, ConfigError, default_config_path, load_config


def test_load_missing_file_returns_defaults(tmp_path: Path) -> None:
    cfg = load_config(tmp_path / "missing.toml")
    assert cfg == Config()
    assert cfg.cache_ttl_seconds == 1800
    assert cfg.request_interval_seconds == 1.0
    assert cfg.max_retries == 3
    assert cfg.default_per_page == 20
    assert cfg.user_agent.startswith("getmycar/")


def test_load_partial_file_overrides_only_present_keys(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(
        """
[cache]
ttl_seconds = 60

[search]
default_per_page = 5
""".strip(),
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.cache_ttl_seconds == 60
    assert cfg.default_per_page == 5
    # untouched keys keep defaults
    assert cfg.request_interval_seconds == 1.0
    assert cfg.max_retries == 3


def test_load_rejects_negative_ttl(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[cache]\nttl_seconds = -1\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_rejects_negative_interval(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[scraper]\nrequest_interval_seconds = -0.5\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_rejects_invalid_toml(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("not = [valid", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_data_dir_resolves_relative_to_cwd(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[data]\ndir = './my-data'\n", encoding="utf-8")
    cfg = load_config(path)
    assert cfg.data_dir == Path("./my-data")


def test_default_config_path_uses_appdata_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setenv("APPDATA", r"C:\Users\u\AppData\Roaming")
    p = default_config_path()
    assert "getmycar" in str(p)
    assert p.name == "config.toml"


def test_default_config_path_uses_xdg_on_linux(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setenv("HOME", str(tmp_path))
    p = default_config_path()
    assert p.name == "config.toml"
    assert "getmycar" in str(p)
