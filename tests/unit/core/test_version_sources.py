"""
Library and runtime versions come from the files that pin them, never from a hand-written number.

core/library_versions.py reads uv.lock, the root package-lock.json, Manifest.toml,
.python-version, the setup actions and the R snapshot note; the database sync
writes what it reads. These tests check that every pin source parses and every
library and language resolves, so a broken or ambiguous pin file fails a PR
instead of a sync. A Dependabot bump changes a pinned version and nothing here.

The library prompts state no version in their example headers (impl-review
rewrites the header from the versions it measures). Every prompt of a locked
library (Python, JavaScript, Makie) states the API level the generator writes
against, and that level must match the lock's major; it moves only in a
deliberate bump PR, because Dependabot groups minor and patch updates only.
"""

from __future__ import annotations

import re
import tomllib
from collections import Counter
from pathlib import Path

import pytest

from core.constants import LANGUAGES_METADATA, LIBRARIES_METADATA, LIBRARY_LANGUAGES, SUPPORTED_LANGUAGES
from core.library_versions import PINNED_PACKAGES, PinError, api_level, pinned_versions, snapshot_pinned, uv_locked


REPO_ROOT = Path(__file__).resolve().parents[3]
LIBRARY_PROMPTS_DIR = REPO_ROOT / "prompts" / "library"
VERSION_RE = re.compile(r"^\d+(?:\.\d+)*$")
DOTTED_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)+\b|\b\d{2,}\b")
# `// Library:` (JavaScript), `# Library:` (Julia), `#' Library:` (R) and a bare
# `Library:` line (a Python docstring).
HEADER_RE = re.compile(r"^(?:(?://|#'?) )?Library: (?P<rest>.+)$", re.MULTILINE)
API_LEVEL_RE = re.compile(r"^\*\*API level:\*\* (?P<name>.+?) (?P<level>\d+(?:\.\d+)?)\. ", re.MULTILINE)

# The prompts that state the API level the generator writes against: every
# library with a lock file (ggplot2 has none, its snapshot moves by hand).
PROMPTS_WITH_API_LEVEL = set(LIBRARY_LANGUAGES) - {"ggplot2"}


@pytest.fixture(scope="module")
def pins():
    return pinned_versions()


def test_every_library_and_runtime_resolves(pins) -> None:
    assert pins.errors == []
    assert set(pins.libraries) == set(LIBRARY_LANGUAGES)
    assert set(pins.runtimes) == SUPPORTED_LANGUAGES


def test_resolved_values_are_versions(pins) -> None:
    for name, version in {**pins.libraries, **pins.runtimes}.items():
        assert VERSION_RE.match(version), f"{name}: {version!r}"


def test_every_library_has_a_pin_source() -> None:
    mapped = {library: language for language, packages in PINNED_PACKAGES.items() for library in packages}
    assert mapped == LIBRARY_LANGUAGES


def test_constants_carry_no_hand_written_versions() -> None:
    """A version in core/constants.py would drift again; the sync writes the pinned one."""
    assert not [lib["id"] for lib in LIBRARIES_METADATA if "version" in lib]
    assert not [lang["id"] for lang in LANGUAGES_METADATA if "runtime_version" in lang]


def test_a_broken_checkout_reports_errors_instead_of_raising(tmp_path: Path) -> None:
    pins = pinned_versions(tmp_path)
    assert pins.libraries == {}
    assert pins.runtimes == {}
    assert len(pins.errors) == len(LIBRARY_LANGUAGES) + len(SUPPORTED_LANGUAGES)


UV_LOCK_FORKS = """
version = 1
requires-python = ">=3.13"

[[package]]
name = "plotnine"
version = "0.15.7"
resolution-markers = [
    "python_full_version < '3.14' and sys_platform != 'emscripten' and sys_platform != 'win32'",
    "python_full_version == '3.14.*' and sys_platform != 'emscripten' and sys_platform != 'win32'",
]

[[package]]
name = "plotnine"
version = "0.15.8"
resolution-markers = ["python_full_version == '3.14.*' and sys_platform == 'emscripten'"]

[[package]]
name = "plotnine"
version = "0.16.0a12"
resolution-markers = ["python_full_version < '3.14' and sys_platform == 'emscripten'"]

[[package]]
name = "seaborn"
version = "0.13.2"

[[package]]
name = "seaborn"
version = "0.13.2"
"""


@pytest.mark.parametrize("interpreter", ["3.13.12", "3.14.0"])
def test_uv_lock_resolves_the_linux_fork_for_the_pinned_interpreter(tmp_path: Path, interpreter: str) -> None:
    (tmp_path / "uv.lock").write_text(UV_LOCK_FORKS, encoding="utf-8")
    (tmp_path / ".python-version").write_text(f"{interpreter}\n", encoding="utf-8")
    assert uv_locked(tmp_path, "plotnine") == "0.15.7"


def test_uv_lock_has_no_duplicated_package_blocks() -> None:
    """Several Dependabot PRs squash-merged within a minute have duplicated package
    blocks in uv.lock before. The sync keeps the stored version of a library whose
    block is duplicated and only warns; this makes the corruption fail CI, wherever
    in the lock it sits. Forks of one package carry different versions."""
    lock = tomllib.loads((REPO_ROOT / "uv.lock").read_text(encoding="utf-8"))
    blocks = Counter((entry["name"], entry["version"]) for entry in lock["package"])
    assert [block for block, count in blocks.items() if count > 1] == []


def test_uv_lock_with_a_duplicated_block_does_not_resolve(tmp_path: Path) -> None:
    """Dependabot PRs merged close together have duplicated package blocks in uv.lock before."""
    (tmp_path / "uv.lock").write_text(UV_LOCK_FORKS, encoding="utf-8")
    (tmp_path / ".python-version").write_text("3.13.12\n", encoding="utf-8")
    with pytest.raises(PinError):
        uv_locked(tmp_path, "seaborn")


SETUP_R = """
      # Snapshot {note} ships ggplot2 3.5.1. The repository has no R lock file.
      run: |
        Rscript -e 'options(repos = c(CRAN = "https://packagemanager.posit.co/cran/__linux__/noble/{url}"))'
"""


def _setup_r(root: Path, note: str, url: str) -> None:
    action = root / ".github" / "actions" / "setup-r" / "action.yml"
    action.parent.mkdir(parents=True)
    action.write_text(SETUP_R.format(note=note, url=url), encoding="utf-8")


def test_r_snapshot_note_resolves_when_its_date_is_the_snapshot(tmp_path: Path) -> None:
    _setup_r(tmp_path, "2025-01-15", "2025-01-15")
    assert snapshot_pinned(tmp_path, "ggplot2") == "3.5.1"


def test_a_stale_r_snapshot_note_does_not_resolve(tmp_path: Path) -> None:
    """A new snapshot date without a new note would show the old ggplot2 version."""
    _setup_r(tmp_path, "2025-01-15", "2026-04-01")
    with pytest.raises(PinError, match="2026-04-01"):
        snapshot_pinned(tmp_path, "ggplot2")


@pytest.mark.parametrize(("version", "level"), [("6.1.0", "6"), ("12.6.0", "12"), ("0.21.9", "0.21"), ("22", "22")])
def test_api_level(version: str, level: str) -> None:
    assert api_level(version) == level


def _prompt(library: str) -> str:
    return (LIBRARY_PROMPTS_DIR / f"{library}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("library", sorted(LIBRARY_LANGUAGES))
def test_prompt_header_examples_carry_no_version(library: str) -> None:
    for match in HEADER_RE.finditer(_prompt(library)):
        assert not DOTTED_NUMBER_RE.search(match.group("rest")), (
            f"prompts/library/{library}.md: 'Library: {match.group('rest')}' names a version; "
            "impl-review writes the measured one into the header"
        )


LIBRARIES_WITH_API_LEVEL = sorted(library for library in LIBRARY_LANGUAGES if API_LEVEL_RE.search(_prompt(library)))


def test_api_level_lines_are_found() -> None:
    """Guards the next test against passing vacuously after a format change."""
    assert PROMPTS_WITH_API_LEVEL <= set(LIBRARIES_WITH_API_LEVEL)


@pytest.mark.parametrize("library", LIBRARIES_WITH_API_LEVEL)
def test_prompt_api_level_is_the_locked_major(library: str, pins) -> None:
    (statement,) = API_LEVEL_RE.finditer(_prompt(library))
    locked = api_level(pins.libraries[library])
    assert statement.group("level") == locked, (
        f"prompts/library/{library}.md writes for {statement.group('name')} {statement.group('level')}, "
        f"the lock pins {pins.libraries[library]} (API level {locked}): a major bump updates the prompt"
    )
