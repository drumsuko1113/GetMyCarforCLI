"""HTTP scraping foundation: rate limiting, retries, robots.txt, cache integration."""

from __future__ import annotations

import time
import urllib.parse
import urllib.robotparser
from typing import Protocol

import requests

from getmycar.cache import CacheProtocol
from getmycar.exceptions import RateLimitedError, RobotsDisallowedError, ScraperError
from getmycar.logging import get_logger

_log = get_logger(__name__)
_DEFAULT_UA = "getmycar (+https://github.com/drumsuko1113/GetMyCarforCLI)"


class ScraperProtocol(Protocol):
    def get(self, url: str) -> bytes: ...


class Scraper:
    """Polite HTTP fetcher with retry, rate limiting, robots.txt, and cache.

    The robots.txt for each origin is fetched lazily on first request and
    memoized per-instance.
    """

    def __init__(
        self,
        cache: CacheProtocol,
        *,
        user_agent: str = _DEFAULT_UA,
        request_interval: float = 1.0,
        max_retries: int = 3,
        timeout: float = 10.0,
        session: requests.Session | None = None,
    ) -> None:
        self._cache = cache
        self._ua = user_agent
        self._interval = request_interval
        self._max_retries = max_retries
        self._timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.setdefault("User-Agent", user_agent)
        self._last_call: float = 0.0
        self._robots: dict[str, urllib.robotparser.RobotFileParser] = {}

    def get(self, url: str) -> bytes:
        cached = self._cache.get(url)
        if cached is not None:
            _log.debug("cache hit: %s", url)
            return cached
        self._enforce_robots(url)
        body = self._fetch_with_retries(url)
        self._cache.set(url, body)
        return body

    # --- internals -----------------------------------------------------

    def _enforce_robots(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots.get(origin)
        if rp is None:
            rp = urllib.robotparser.RobotFileParser()
            try:
                resp = self._session.get(f"{origin}/robots.txt", timeout=self._timeout)
                rp.parse(resp.text.splitlines())
            except requests.RequestException:
                # absent/unreachable robots.txt is treated as permissive
                rp.parse([])
            self._robots[origin] = rp
        if not rp.can_fetch(self._ua, url):
            raise RobotsDisallowedError(f"robots.txt disallows {url}")

    def _wait_for_rate_limit(self) -> None:
        if self._interval <= 0:
            return
        elapsed = time.time() - self._last_call
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)

    def _fetch_with_retries(self, url: str) -> bytes:
        attempt = 0
        backoff = 0.5
        last_error: Exception | None = None
        while attempt <= self._max_retries:
            self._wait_for_rate_limit()
            try:
                resp = self._session.get(url, timeout=self._timeout)
                self._last_call = time.time()
            except requests.RequestException as e:
                last_error = e
                _log.info("request failed (%s); retry %d", e, attempt)
                attempt += 1
                time.sleep(backoff)
                backoff *= 2
                continue

            if resp.status_code == 429:
                raise RateLimitedError(f"rate limited by {url}")
            if 500 <= resp.status_code < 600:
                last_error = ScraperError(f"HTTP {resp.status_code} from {url}")
                attempt += 1
                time.sleep(backoff)
                backoff *= 2
                continue
            if resp.status_code >= 400:
                raise ScraperError(f"HTTP {resp.status_code} from {url}")
            return resp.content
        raise ScraperError(f"giving up on {url} after {self._max_retries} retries") from last_error
