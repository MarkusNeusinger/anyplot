"""Shared fixtures of the API unit tests."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any

import pytest

from api.machine_reads import LOGGER_NAME


class MachineLines(logging.Handler):
    """Collects what the machine-read logger writes during one test."""

    def __init__(self) -> None:
        super().__init__(level=logging.INFO)
        self.raw: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.raw.append(record.getMessage())

    @property
    def lines(self) -> list[dict[str, Any]]:
        return [json.loads(message) for message in self.raw]


@pytest.fixture
def machine_lines() -> Iterator[MachineLines]:
    """The machine-read lines of the test. The logger does not propagate (its lines must reach stdout bare), so
    `caplog` never sees them; this handler hangs on the logger itself."""
    handler = MachineLines()
    lines_logger = logging.getLogger(LOGGER_NAME)
    lines_logger.addHandler(handler)
    try:
        yield handler
    finally:
        lines_logger.removeHandler(handler)
