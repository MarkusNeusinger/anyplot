"""Keep the frontend's version field in step with the project version.

The masthead on anyplot.ai shows the latest GitHub release tag, and falls back to
`CONFIG.appVersion` whenever that lookup has not answered yet or is unavailable
(offline, rate-limited). That fallback reads `app/package.json`, because the
frontend image is built with `docker build -f app/Dockerfile app` — the build
context is `app/` alone, so `pyproject.toml` is not readable at build time.

Two version fields therefore exist, and they must not drift: `app/package.json`
sat at 2.0.0 through the whole 3.x line, which is how the site came to advertise
a stale version. This test fails the moment a release bumps one and not the
other; the `Run Tests` CI job runs whenever `pyproject.toml` changes, so every
release PR is covered.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
APP_PACKAGE_JSON = REPO_ROOT / "app" / "package.json"

SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def _project_version() -> str:
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def _app_version() -> str:
    return json.loads(APP_PACKAGE_JSON.read_text(encoding="utf-8"))["version"]


def test_app_package_json_matches_project_version() -> None:
    project_version = _project_version()
    app_version = _app_version()

    assert app_version == project_version, (
        f"app/package.json is at {app_version} but pyproject.toml is at {project_version}. "
        "Bump both — the masthead falls back to the app/package.json version whenever the "
        "GitHub releases lookup is unavailable, so a stale value is shown to visitors. "
        "See step 4 of agentic/commands/release.md."
    )


def test_project_version_is_a_semver_triple() -> None:
    assert SEMVER.match(_project_version())
