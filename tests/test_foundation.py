from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "getmycar.main",
        "getmycar.scraper",
        "getmycar.parser",
        "getmycar.filters",
        "getmycar.favorites",
        "getmycar.display",
        "getmycar.cache",
        "getmycar.utils",
    ],
)
def test_module_importable(module_name: str) -> None:
    importlib.import_module(module_name)


def test_ensure_dir(tmp_path: object) -> None:
    from getmycar.utils import ensure_dir

    target = tmp_path / "a" / "b"  # type: ignore[operator]
    result = ensure_dir(target)
    assert result.is_dir()
    # idempotent
    ensure_dir(target)
    assert result.is_dir()
