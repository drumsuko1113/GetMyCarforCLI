from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from freezegun import freeze_time

from getmycar.cache import FileCache


def test_set_then_get_returns_value(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=60))
    cache.set("key", b"hello")
    assert cache.get("key") == b"hello"


def test_get_missing_returns_none(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=60))
    assert cache.get("missing") is None


def test_expired_entry_returns_none(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=30))
    with freeze_time("2026-01-01 00:00:00"):
        cache.set("k", b"v")
    with freeze_time("2026-01-01 00:00:31"):
        assert cache.get("k") is None


def test_fresh_entry_within_ttl_returns_value(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=30))
    with freeze_time("2026-01-01 00:00:00"):
        cache.set("k", b"v")
    with freeze_time("2026-01-01 00:00:29"):
        assert cache.get("k") == b"v"


def test_clear_removes_all_entries(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=60))
    cache.set("a", b"1")
    cache.set("b", b"2")
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None


def test_overwrite_replaces_value(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=60))
    cache.set("k", b"v1")
    cache.set("k", b"v2")
    assert cache.get("k") == b"v2"


def test_keys_with_unsafe_chars_are_hashed(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=60))
    cache.set("https://example.com/path?x=1&y=2", b"ok")
    assert cache.get("https://example.com/path?x=1&y=2") == b"ok"


def test_clear_is_safe_when_directory_empty(tmp_path: Path) -> None:
    cache = FileCache(tmp_path, ttl=timedelta(seconds=60))
    cache.clear()  # should not raise
