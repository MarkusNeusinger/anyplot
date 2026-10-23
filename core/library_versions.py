"""
Pinned library and runtime versions, read from the files that pin them.

No version is written down by hand: the database sync
(automation/scripts/sync_to_postgres.py) fills `libraries.version` and
`languages.runtime_version` from here, so a Dependabot bump reaches the
Libraries page with the next sync and nothing else has to follow it.

The sources:

- Python libraries: uv.lock, the entry that applies on the Linux runner for the
  interpreter in .python-version. uv.lock forks a package per platform and
  Python version (plotnine: one release for Linux, another for emscripten).
- JavaScript libraries: the root package-lock.json, which `npm ci` in
  .github/actions/setup-node restores.
- Makie: Manifest.toml, which `Pkg.instantiate()` in .github/actions/setup-julia
  restores.
- ggplot2: the repository has no R lock file. .github/actions/setup-r installs
  from a dated Posit snapshot, and the comment `# Snapshot <date> ships ggplot2
  <version>.` next to it records what that snapshot installs. A note whose date
  is not the snapshot's is stale and does not resolve.
- Runtimes: .python-version for Python, and the defaults of the setup-r,
  setup-julia and setup-node actions.

This module reads repository files, so only code running in a checkout (the
sync job, tests) uses it; the API serves the stored values.
"""

from __future__ import annotations

import json
import re
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from packaging.markers import Marker

from core.constants import LANGUAGE_NAMES, LIBRARY_LANGUAGES


REPO_ROOT = Path(__file__).resolve().parent.parent

# The package each library is pinned under, per language.
PINNED_PACKAGES: dict[str, dict[str, str]] = {
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

SNAPSHOT_URL_RE = re.compile(r"packagemanager\.posit\.co/cran/__linux__/[a-z]+/(\d{4}-\d{2}-\d{2})")
SNAPSHOT_NOTE_RE = re.compile(r"# Snapshot (\d{4}-\d{2}-\d{2}) ships ggplot2 (\d+(?:\.\d+)+)\.")


class PinError(ValueError):
    """A pin file is missing, malformed, or does not name exactly one version."""


@dataclass(frozen=True)
class PinnedVersions:
    """Library id -> version, language id -> runtime version, and what did not resolve."""

    libraries: dict[str, str] = field(default_factory=dict)
    runtimes: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def major_minor(version: str) -> str:
    return ".".join(version.split(".")[:2])


def api_level(version: str) -> str:
    """The part of a version that marks API breaks: the major, or `0.minor` before 1.0."""
    parts = version.split(".")
    return ".".join(parts[:2]) if parts[0] == "0" else parts[0]


def _python_version(root: Path) -> str:
    return (root / ".python-version").read_text(encoding="utf-8").strip()


def _action_default(root: Path, action: str, name: str) -> str:
    data = yaml.safe_load((root / ".github" / "actions" / action / "action.yml").read_text(encoding="utf-8"))
    return str(data["inputs"][name]["default"])


def uv_locked(root: Path, package: str) -> str:
    """The version uv.lock pins for `package` on the Linux runner."""
    lock = tomllib.loads((root / "uv.lock").read_text(encoding="utf-8"))
    interpreter = _python_version(root)
    environment = {
        "python_full_version": interpreter,
        "python_version": major_minor(interpreter),
        "sys_platform": "linux",
        "platform_system": "Linux",
    }
    versions = [
        str(entry["version"])
        for entry in lock["package"]
        if entry["name"] == package
        and (
            "resolution-markers" not in entry
            or any(Marker(marker).evaluate(environment) for marker in entry["resolution-markers"])
        )
    ]
    if len(versions) != 1:
        raise PinError(f"uv.lock pins {package} as {versions} for Python {interpreter} on Linux, not one version")
    return versions[0]


def npm_locked(root: Path, package: str) -> str:
    """The version the root package-lock.json pins for `package`."""
    lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
    return str(lock["packages"][f"node_modules/{package}"]["version"])


def manifest_locked(root: Path, package: str) -> str:
    """The version Manifest.toml pins for `package`."""
    entries = tomllib.loads((root / "Manifest.toml").read_text(encoding="utf-8"))["deps"][package]
    if len(entries) != 1:
        raise PinError(f"Manifest.toml has {len(entries)} entries for {package}, not one")
    return str(entries[0]["version"])


def snapshot_pinned(root: Path, package: str) -> str:
    """The ggplot2 version the setup-r action's snapshot note names, if the note is current."""
    if package != "ggplot2":
        raise PinError(f"the setup-r snapshot note covers ggplot2 only, not {package}")
    text = (root / ".github" / "actions" / "setup-r" / "action.yml").read_text(encoding="utf-8")
    snapshots = set(SNAPSHOT_URL_RE.findall(text))
    note = SNAPSHOT_NOTE_RE.search(text)
    if len(snapshots) != 1:
        raise PinError(f"setup-r names {sorted(snapshots)} as Posit snapshots, not one")
    if not note:
        raise PinError("setup-r has no '# Snapshot <date> ships ggplot2 <version>.' note")
    (snapshot,) = snapshots
    if note.group(1) != snapshot:
        raise PinError(f"setup-r installs snapshot {snapshot} but its note describes {note.group(1)}")
    return note.group(2)


LIBRARY_READERS: dict[str, Callable[[Path, str], str]] = {
    "python": uv_locked,
    "javascript": npm_locked,
    "julia": manifest_locked,
    "r": snapshot_pinned,
}

RUNTIME_READERS: dict[str, Callable[[Path], str]] = {
    "python": lambda root: major_minor(_python_version(root)),
    "r": lambda root: major_minor(_action_default(root, "setup-r", "r-version")),
    "julia": lambda root: _action_default(root, "setup-julia", "julia-version"),
    "javascript": lambda root: _action_default(root, "setup-node", "node-version"),
}

# What a broken or missing pin file raises: OSError (missing file), KeyError and
# TypeError (unexpected structure), ValueError (TOML/JSON/marker parse errors and
# PinError), yaml.YAMLError (an action file).
_READ_ERRORS: tuple[type[Exception], ...] = (OSError, KeyError, TypeError, ValueError, yaml.YAMLError)


def pinned_versions(root: Path = REPO_ROOT) -> PinnedVersions:
    """Read every library's and runtime's pinned version; collect what fails instead of raising."""
    result = PinnedVersions()
    for library, language in sorted(LIBRARY_LANGUAGES.items()):
        package = PINNED_PACKAGES.get(language, {}).get(library)
        if package is None:
            result.errors.append(f"{library}: no pin source in core/library_versions.py PINNED_PACKAGES")
            continue
        try:
            result.libraries[library] = LIBRARY_READERS[language](root, package)
        except _READ_ERRORS as exc:
            result.errors.append(f"{library}: {type(exc).__name__}: {exc}")
    for language in sorted(LANGUAGE_NAMES):
        if language not in RUNTIME_READERS:
            result.errors.append(f"{language}: no runtime source in core/library_versions.py RUNTIME_READERS")
            continue
        try:
            result.runtimes[language] = RUNTIME_READERS[language](root)
        except _READ_ERRORS as exc:
            result.errors.append(f"{language} runtime: {type(exc).__name__}: {exc}")
    return result
