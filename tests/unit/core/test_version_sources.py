"""
The versions anyplot writes down by hand match the files that pin them.

Two places state versions by hand: core/constants.py (each library's `version`,
shown on the Libraries page, and each language's `runtime_version`) and the
example header line in prompts/library/*.md, which tells the generator the API
level it writes for. Both drifted for months: the Libraries page showed
matplotlib 3.9.0 while uv.lock pinned 3.11.2, and the ECharts prompt said 5.5.1
while the render harness shipped 6.1.0.

The pinned versions are the truth:

- Python: uv.lock, the entry that applies on the Linux runner for the
  interpreter in .python-version (plotnine forks per platform).
- JavaScript: the root package-lock.json, which `npm ci` in
  .github/actions/setup-node restores.
- Julia: Manifest.toml, which `Pkg.instantiate()` in .github/actions/setup-julia
  restores.
- R: the repository has no lock file. .github/actions/setup-r installs from a
  dated Posit snapshot, and a comment next to it names the ggplot2 version that
  snapshot ships. The test holds the comment's date to the snapshot URL, so a
  new date cannot land without a new version. Reading the version from the
  snapshot itself would need the network.
"""

from __future__ import annotations

import json
import re
import tomllib
from functools import cache
from pathlib import Path
from typing import Any

import pytest
import yaml
from packaging.markers import Marker

from core.constants import LANGUAGES_METADATA, LIBRARIES_METADATA, LIBRARY_LANGUAGES


REPO_ROOT = Path(__file__).resolve().parents[3]
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"
LIBRARY_PROMPTS_DIR = REPO_ROOT / "prompts" / "library"

LIBRARY_VERSIONS = {str(lib["id"]): str(lib["version"]) for lib in LIBRARIES_METADATA}
RUNTIME_VERSIONS = {str(lang["id"]): str(lang["runtime_version"]) for lang in LANGUAGES_METADATA}

# The package each library is pinned under, per language.
PINNED_PACKAGES = {
    "python": {
        "altair": "altair",
        "bokeh": "bokeh",
        "letsplot": "lets-plot",
        "matplotlib": "matplotlib",
        "plotly": "plotly",
        "plotnine": "plotnine",
        "pygal": "pygal",
        "seaborn": "seaborn",
    },
    "javascript": {
        "chartjs": "chart.js",
        "d3": "d3",
        "echarts": "echarts",
        "highcharts": "highcharts",
        "muix": "@mui/x-charts",
    },
    "julia": {"makie": "Makie"},
    "r": {"ggplot2": "ggplot2"},
}

# The library prompts that show the generator an example header with a version.
PROMPTS_WITH_HEADER_EXAMPLES = {"chartjs", "d3", "echarts", "highcharts", "makie", "muix"}

SNAPSHOT_URL_RE = re.compile(r"packagemanager\.posit\.co/cran/__linux__/[a-z]+/(\d{4}-\d{2}-\d{2})")
SNAPSHOT_NOTE_RE = re.compile(r"# Snapshot (\d{4}-\d{2}-\d{2}) ships ggplot2 (\d+(?:\.\d+)+)\.")
# `// Library:` (JavaScript), `# Library:` (Julia), `#' Library:` (R) and a bare
# `Library:` line (a Python docstring).
HEADER_RE = re.compile(r"^(?:(?://|#'?) )?Library: (?P<label>[^|\n]*)\|", re.MULTILINE)
VERSION_RE = re.compile(r"\b\d+(?:\.\d+)+\b")


def _major_minor(version: str) -> str:
    return ".".join(version.split(".")[:2])


def _python_version() -> str:
    """The interpreter the repository pins, for example "3.13.12"."""
    return (REPO_ROOT / ".python-version").read_text().strip()


def _action_default(action: str, name: str) -> str:
    """The default of input `name` of the composite action `.github/actions/<action>`."""
    action_yaml = yaml.safe_load((ACTIONS_DIR / action / "action.yml").read_text())
    return str(action_yaml["inputs"][name]["default"])


@cache
def _uv_lock() -> dict[str, Any]:
    return tomllib.loads((REPO_ROOT / "uv.lock").read_text())


def uv_locked(package: str) -> str:
    """The version uv.lock pins for `package` on the Linux runner."""
    environment = {
        "python_full_version": _python_version(),
        "python_version": _major_minor(_python_version()),
        "sys_platform": "linux",
        "platform_system": "Linux",
    }
    versions = [
        entry["version"]
        for entry in _uv_lock()["package"]
        if entry["name"] == package
        and (
            "resolution-markers" not in entry
            or any(Marker(marker).evaluate(environment) for marker in entry["resolution-markers"])
        )
    ]
    assert len(versions) == 1, f"uv.lock pins {package} as {versions} on Linux; expected exactly one version"
    return str(versions[0])


def npm_locked(package: str) -> str:
    """The version the root package-lock.json pins for `package`."""
    lock = json.loads((REPO_ROOT / "package-lock.json").read_text())
    return str(lock["packages"][f"node_modules/{package}"]["version"])


def manifest_locked(package: str) -> str:
    """The version Manifest.toml pins for `package`."""
    manifest = tomllib.loads((REPO_ROOT / "Manifest.toml").read_text())
    (entry,) = manifest["deps"][package]
    return str(entry["version"])


def snapshot_pinned(package: str) -> str:
    """The ggplot2 version the setup-r action's snapshot note names."""
    assert package == "ggplot2", "only ggplot2 has a snapshot note in .github/actions/setup-r/action.yml"
    text = (ACTIONS_DIR / "setup-r" / "action.yml").read_text()
    note = SNAPSHOT_NOTE_RE.search(text)
    assert note, "the setup-r action lost its '# Snapshot <date> ships ggplot2 <version>.' note"
    return note.group(2)


PIN_READERS = {"python": uv_locked, "javascript": npm_locked, "julia": manifest_locked, "r": snapshot_pinned}
PIN_SOURCES = {
    "python": "uv.lock",
    "javascript": "package-lock.json",
    "julia": "Manifest.toml",
    "r": "the snapshot note in .github/actions/setup-r/action.yml",
}


def pinned_version(library: str) -> str:
    language = LIBRARY_LANGUAGES[library]
    return PIN_READERS[language](PINNED_PACKAGES[language][library])


def test_every_library_has_a_pin_source() -> None:
    mapped = {library: language for language, packages in PINNED_PACKAGES.items() for library in packages}
    assert mapped == LIBRARY_LANGUAGES


@pytest.mark.parametrize("library", sorted(LIBRARY_VERSIONS))
def test_constants_version_is_the_pinned_version(library: str) -> None:
    pinned = pinned_version(library)
    source = PIN_SOURCES[LIBRARY_LANGUAGES[library]]
    assert LIBRARY_VERSIONS[library] == pinned, (
        f"core/constants.py says {library} {LIBRARY_VERSIONS[library]}, {source} pins {pinned}: "
        "set its `version` to the pinned one in the same PR that moves the pin"
    )


def test_r_snapshot_note_names_the_installed_snapshot() -> None:
    text = (ACTIONS_DIR / "setup-r" / "action.yml").read_text()
    urls = set(SNAPSHOT_URL_RE.findall(text))
    note = SNAPSHOT_NOTE_RE.search(text)
    assert len(urls) == 1, f"expected one Posit snapshot date in setup-r, found {sorted(urls)}"
    assert note, "the setup-r action lost its '# Snapshot <date> ships ggplot2 <version>.' note"
    assert note.group(1) == next(iter(urls)), (
        f"setup-r installs snapshot {next(iter(urls))} but its note describes {note.group(1)}: "
        "write the ggplot2 version the new snapshot installs into the note and core/constants.py"
    )


def test_python_runtime_is_the_pinned_interpreter() -> None:
    assert RUNTIME_VERSIONS["python"] == _major_minor(_python_version())


def test_javascript_runtime_is_the_setup_node_default() -> None:
    assert RUNTIME_VERSIONS["javascript"] == _action_default("setup-node", "node-version")


def test_julia_runtime_is_the_setup_julia_default() -> None:
    assert RUNTIME_VERSIONS["julia"] == _action_default("setup-julia", "julia-version")


def test_r_runtime_is_the_setup_r_default() -> None:
    assert RUNTIME_VERSIONS["r"] == _major_minor(_action_default("setup-r", "r-version"))


def _prompt_header_labels(library: str) -> list[str]:
    """The library part of each example `Library: <label> | <runtime>` line in the prompt."""
    text = (LIBRARY_PROMPTS_DIR / f"{library}.md").read_text()
    return [match.group("label").strip() for match in HEADER_RE.finditer(text)]


LIBRARIES_WITH_HEADERS = sorted(library for library in LIBRARY_VERSIONS if _prompt_header_labels(library))


def test_header_examples_are_found() -> None:
    """Guards the next test against passing vacuously after a format change."""
    assert PROMPTS_WITH_HEADER_EXAMPLES <= set(LIBRARIES_WITH_HEADERS)


@pytest.mark.parametrize("library", LIBRARIES_WITH_HEADERS)
def test_prompt_header_names_the_pinned_version(library: str) -> None:
    pinned = pinned_version(library)
    for label in _prompt_header_labels(library):
        assert VERSION_RE.findall(label) == [pinned], (
            f"prompts/library/{library}.md shows 'Library: {label}', the pinned version is {pinned}"
        )
