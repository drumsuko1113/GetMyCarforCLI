from __future__ import annotations

import logging

from getmycar.logging import configure_logging, get_logger


def test_get_logger_returns_named_logger() -> None:
    logger = get_logger("getmycar.test")
    assert logger.name == "getmycar.test"


def test_get_logger_is_idempotent() -> None:
    a = get_logger("getmycar.test")
    b = get_logger("getmycar.test")
    assert a is b


def test_configure_logging_levels() -> None:
    configure_logging(verbosity=0)
    assert logging.getLogger("getmycar").level == logging.WARNING
    configure_logging(verbosity=1)
    assert logging.getLogger("getmycar").level == logging.INFO
    configure_logging(verbosity=2)
    assert logging.getLogger("getmycar").level == logging.DEBUG


def test_configure_logging_attaches_handler_once() -> None:
    configure_logging(verbosity=0)
    configure_logging(verbosity=1)
    handlers = logging.getLogger("getmycar").handlers
    assert len(handlers) == 1
