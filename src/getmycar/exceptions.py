"""Domain exception hierarchy for getmycar.

All custom exceptions derive from :class:`GetMyCarError` so call sites can
catch the whole family with a single ``except``.
"""
from __future__ import annotations


class GetMyCarError(Exception):
    """Base class for all getmycar errors."""


class ScraperError(GetMyCarError):
    """Raised when HTTP fetching or robots.txt enforcement fails."""


class RobotsDisallowedError(ScraperError):
    """Raised when a URL is disallowed by robots.txt."""


class RateLimitedError(ScraperError):
    """Raised when the upstream signals rate limiting (HTTP 429)."""


class ParseError(GetMyCarError):
    """Raised when HTML parsing produces no usable result."""


class CacheError(GetMyCarError):
    """Raised when the on-disk cache cannot satisfy a read/write."""


class RepositoryError(GetMyCarError):
    """Raised when the favorites/presets repository is corrupt or unwritable."""
