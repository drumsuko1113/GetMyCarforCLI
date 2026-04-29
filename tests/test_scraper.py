from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
import responses

from getmycar.cache import FileCache
from getmycar.exceptions import RateLimitedError, RobotsDisallowedError, ScraperError
from getmycar.scraper import Scraper

_ROBOTS_OK = "User-agent: *\nAllow: /\n"
_ROBOTS_DENY = "User-agent: *\nDisallow: /usedcar/\n"


@pytest.fixture
def cache(tmp_path: Path) -> FileCache:
    return FileCache(tmp_path / "cache", ttl=timedelta(seconds=60))


@pytest.fixture
def fast_sleep() -> Iterator[None]:
    with patch("getmycar.scraper.time.sleep"):
        yield


@responses.activate
def test_get_returns_body_and_caches_it(cache: FileCache, fast_sleep: None) -> None:
    responses.add(responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_OK)
    responses.add(responses.GET, "https://www.carsensor.net/usedcar/", body="<html>ok</html>")
    scraper = Scraper(cache=cache, request_interval=0, max_retries=2)
    body = scraper.get("https://www.carsensor.net/usedcar/")
    assert body == b"<html>ok</html>"
    # second call should be served from cache (no extra HTTP call)
    body2 = scraper.get("https://www.carsensor.net/usedcar/")
    assert body2 == b"<html>ok</html>"
    # 1 robots + 1 page = 2 calls total
    assert len(responses.calls) == 2


@responses.activate
def test_get_respects_robots_disallow(cache: FileCache, fast_sleep: None) -> None:
    responses.add(responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_DENY)
    scraper = Scraper(cache=cache, request_interval=0, max_retries=1)
    with pytest.raises(RobotsDisallowedError):
        scraper.get("https://www.carsensor.net/usedcar/foo")


@responses.activate
def test_get_retries_on_5xx_then_succeeds(cache: FileCache, fast_sleep: None) -> None:
    responses.add(responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_OK)
    responses.add(responses.GET, "https://www.carsensor.net/x", status=503)
    responses.add(responses.GET, "https://www.carsensor.net/x", status=503)
    responses.add(responses.GET, "https://www.carsensor.net/x", body="ok")
    scraper = Scraper(cache=cache, request_interval=0, max_retries=3)
    assert scraper.get("https://www.carsensor.net/x") == b"ok"


@responses.activate
def test_get_raises_after_exhausting_retries(cache: FileCache, fast_sleep: None) -> None:
    responses.add(responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_OK)
    for _ in range(5):
        responses.add(responses.GET, "https://www.carsensor.net/x", status=503)
    scraper = Scraper(cache=cache, request_interval=0, max_retries=2)
    with pytest.raises(ScraperError):
        scraper.get("https://www.carsensor.net/x")


@responses.activate
def test_get_raises_rate_limited_on_429(cache: FileCache, fast_sleep: None) -> None:
    responses.add(responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_OK)
    responses.add(responses.GET, "https://www.carsensor.net/x", status=429)
    scraper = Scraper(cache=cache, request_interval=0, max_retries=0)
    with pytest.raises(RateLimitedError):
        scraper.get("https://www.carsensor.net/x")


@responses.activate
def test_request_interval_is_enforced_between_calls(cache: FileCache) -> None:
    responses.add(responses.GET, "https://www.carsensor.net/robots.txt", body=_ROBOTS_OK)
    responses.add(responses.GET, "https://www.carsensor.net/a", body="a")
    responses.add(responses.GET, "https://www.carsensor.net/b", body="b")
    sleeps: list[float] = []
    with patch("getmycar.scraper.time.sleep", side_effect=sleeps.append):
        scraper = Scraper(cache=cache, request_interval=1.0, max_retries=0)
        scraper.get("https://www.carsensor.net/a")
        scraper.get("https://www.carsensor.net/b")
    # at least one sleep should have been requested between back-to-back calls
    assert any(s > 0 for s in sleeps)
