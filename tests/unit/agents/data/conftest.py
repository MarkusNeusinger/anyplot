"""Every warning the data tests make the parser write has a closed telemetry code.

The usage telemetry logs warning codes, never sentences (`agents/anyplot/data/warning_codes.py`);
a reworded or new warning without its rule would silently become `other`. This fixture wraps
`ParsedDataset.__init__` for every test in this package, so each parse the parser test corpus
runs is checked, and fails the test that produced a sentence no rule knows.
"""

from collections.abc import Iterator
from typing import Any

import pytest

from agents.anyplot.data.parse import ParsedDataset
from agents.anyplot.data.warning_codes import warning_code


@pytest.fixture(autouse=True)
def warnings_have_codes(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    unknown: list[str] = []
    original = ParsedDataset.__init__

    def checked(self: ParsedDataset, *args: Any, **kwargs: Any) -> None:
        original(self, *args, **kwargs)
        unknown.extend(line for line in self.warnings if warning_code(line) == "other")

    monkeypatch.setattr(ParsedDataset, "__init__", checked)
    yield
    assert unknown == [], f"warning sentences without a telemetry code (add a rule in warning_codes.py): {unknown}"
