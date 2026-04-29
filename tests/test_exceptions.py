from __future__ import annotations

import pytest

from getmycar.exceptions import (
    CacheError,
    GetMyCarError,
    ParseError,
    RateLimitedError,
    RepositoryError,
    RobotsDisallowedError,
    ScraperError,
)


@pytest.mark.parametrize(
    "exc_cls",
    [
        ScraperError,
        RobotsDisallowedError,
        RateLimitedError,
        ParseError,
        CacheError,
        RepositoryError,
    ],
)
def test_all_derive_from_base(exc_cls: type[GetMyCarError]) -> None:
    assert issubclass(exc_cls, GetMyCarError)
    assert issubclass(exc_cls, Exception)


def test_robots_and_ratelimit_derive_from_scraper_error() -> None:
    assert issubclass(RobotsDisallowedError, ScraperError)
    assert issubclass(RateLimitedError, ScraperError)


def test_chained_cause_is_preserved() -> None:
    root = ValueError("root")
    try:
        try:
            raise root
        except ValueError as e:
            raise ParseError("failed to parse") from e
    except ParseError as caught:
        assert caught.__cause__ is root
