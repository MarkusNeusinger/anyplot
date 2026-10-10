"""The runtime tests' fixtures, shared: a hermetic development environment, fake services, scripted models.

The matrix harness drives the real `/v1` app, so its tests need exactly what
`tests/unit/agents/runtime/conftest.py` provides; the redundant aliases re-export
those fixtures here instead of copying them.
"""

from html.parser import HTMLParser

from ..runtime.conftest import backend as backend
from ..runtime.conftest import development_env as development_env
from ..runtime.conftest import judge as judge
from ..runtime.conftest import services as services
from ..runtime.conftest import swap_models as swap_models


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
