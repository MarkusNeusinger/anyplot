"""The Python plotting libraries a test needs: skipped where they do not import, a failure where CI requires them.

Most of the suite runs without the plotting libraries (`pyproject.toml`'s `lib-*` extras), so a test that needs one
imports it through `import_library`, which skips the test on a developer machine without it. CI's test job installs
every `lib-*` extra and sets `ANYPLOT_REQUIRE_LIBRARIES=1` (`.github/workflows/ci-tests.yml`): there a library that
does not import fails the test instead, so a dropped extra or a broken wheel can never turn the validator's walks
and the harness's library cases into silent skips again (on 2026-11-02 they hid `pygal.config.callable`, an alias
of `types.FunctionType` the validator admitted).
"""

import importlib
import os
from types import ModuleType

import pytest


REQUIRE_LIBRARIES_ENV = "ANYPLOT_REQUIRE_LIBRARIES"


def libraries_required() -> bool:
    """Whether a library that does not import fails the test (CI's test job) rather than skipping it."""
    return os.environ.get(REQUIRE_LIBRARIES_ENV) == "1"


def import_library(name: str) -> ModuleType:
    """Import `name` for a test: skip the test when it does not import here, fail it when CI requires the libraries.

    `pytest.importorskip` skips only an ImportError, but cairosvg's import raises OSError when cairocffi finds no
    libcairo on the machine, so both count as "does not import".
    """
    try:
        return importlib.import_module(name)
    except (ImportError, OSError) as exc:
        reason = f"{name} does not import here: {type(exc).__name__}: {exc}"
        if libraries_required():
            pytest.fail(f"{reason} ({REQUIRE_LIBRARIES_ENV}=1: this job installs every lib-* extra)")
        pytest.skip(reason)
