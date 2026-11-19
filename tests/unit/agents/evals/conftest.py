"""The runtime tests' fixtures, shared: a hermetic development environment, fake services, scripted models.

The matrix harness drives the real `/v1` app, so its tests need exactly what
`tests/unit/agents/runtime/conftest.py` provides; the redundant aliases re-export
those fixtures here instead of copying them.

Every eval test also gets an empty promoted directory (`no_promoted_cases`): the real
`agents/evals/.cases/` holds visitors' data, and a test that reached it without the
fixture fails in `import_case.promoted_cases_dir` before anything reads it.
"""

from html.parser import HTMLParser
from pathlib import Path

import pytest

from agents.evals import import_case

from ..runtime.conftest import backend as backend
from ..runtime.conftest import development_env as development_env
from ..runtime.conftest import judge as judge
from ..runtime.conftest import services as services
from ..runtime.conftest import swap_models as swap_models


@pytest.fixture(autouse=True)
def no_promoted_cases(tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Points the harness's promoted directory at an empty temporary one for every eval test.

    Every default use of the directory reads `import_case.PROMOTED_DIR` when it runs (`promoted_cases_dir`), so this
    one attribute covers `load_cases()`, the matrix's selection and preflight, the static stage, `write_case` and the
    sync. A test that wants promoted cases names its own directory or patches the attribute again.
    """
    directory = tmp_path_factory.mktemp("promoted")
    monkeypatch.setattr(import_case, "PROMOTED_DIR", directory)
    return directory


VOID_ELEMENTS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"})


class HtmlChecker(HTMLParser):
    """A strict-enough HTML check: a doctype, a title, and every non-void element closed in order."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.doctype = False
        self.titles = 0
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_decl(self, decl: str) -> None:
        self.doctype = self.doctype or decl.lower() == "doctype html"

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append((tag, dict(attrs)))
        self.titles += tag == "title"
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}> with open {self.stack[-3:]}")
            return
        self.stack.pop()


def check_html(text: str) -> HtmlChecker:
    """Parse `text` and return the checker; the caller asserts on it."""
    checker = HtmlChecker()
    checker.feed(text)
    checker.close()
    return checker
