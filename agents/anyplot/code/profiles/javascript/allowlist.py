"""The MUI X import allowlist, as the agents service reads it: a copy of the renderer image's file.

The renderer image derives the bare module specifiers a MUI X snippet may import from the
`exports` maps of the installed `react`, `react-dom`, `@mui/material` and `@mui/x-charts`
(`agents/renderer/toolchain/import_allowlist.py`, JS-1) into
`/opt/anyplot/js-render/import-allowlist.json`, which the harness's bundle step enforces
(JS-2). The agents image has no `node_modules`, so this package carries a copy of that file,
`import-allowlist.json` next to this module, and the validator and the readiness scan read
the copy. Two checks keep it equal to the generated file (JS-3, 2026-10-30):

* a unit test (`tests/unit/agents/code/test_profile_javascript_allowlist.py`) regenerates
  the allowlist from the repository's `node_modules` with the image's own script and
  compares it with the copy; it skips where `node_modules` is not installed;
* the `renderer-image` job of `.github/workflows/ci-image.yml` compares the built image's
  file with the copy, so a lock bump that changes the packages' exports fails CI until the
  copy is regenerated (`python3 agents/renderer/toolchain/import_allowlist.py node_modules >
  agents/anyplot/code/profiles/javascript/import-allowlist.json` after `npm ci`).

`REMOVED_EXPORTS` names the MUI X 7 exports that MUI X 9 no longer has
(`prompts/library/muix.md`, "MUI X v9 API"): an allowlisted specifier can still fail to
bundle when a file imports one of them by name (`import { ChartContainer } from
"@mui/x-charts"`, 1 catalogue file; the other 51 failures of JS-1's sweep import the
removed path `@mui/x-charts/ChartContainer`). The allowlist names modules, not their
exports, so this short list stands beside it; a test checks it against the installed
package where Node and `node_modules` are present.
"""

import functools
import json
from pathlib import Path
from typing import Any


ALLOWLIST_FILE = Path(__file__).with_name("import-allowlist.json")
SCHEMA = 1
"""The file's shape (`import_allowlist.SCHEMA`); a copy of another schema is refused at load."""
MUI_PACKAGE = "@mui/x-charts"
REMOVED_EXPORTS: dict[str, str] = {
    "ChartContainer": "ChartsContainer from @mui/x-charts/ChartsContainer",
    "ResponsiveChartContainer": "ChartsContainer from @mui/x-charts/ChartsContainer",
    "DefaultChartsLegend": "ChartsLegend from @mui/x-charts/ChartsLegend",
}
"""MUI X 7 names that MUI X 9 does not export, each with its replacement (`prompts/library/muix.md`)."""


@functools.cache
def allowlist() -> dict[str, Any]:
    """The parsed copy: `{"schema": 1, "packages": {name: version}, "specifiers": [...]}`."""
    parsed: dict[str, Any] = json.loads(ALLOWLIST_FILE.read_text(encoding="utf-8"))
    if parsed.get("schema") != SCHEMA or not isinstance(parsed.get("specifiers"), list):
        raise ValueError(f"{ALLOWLIST_FILE.name} is not an import allowlist of schema {SCHEMA}")
    return parsed


@functools.cache
def specifiers() -> frozenset[str]:
    """The bare specifiers a MUI X snippet may import."""
    return frozenset(allowlist()["specifiers"])


@functools.cache
def packages() -> dict[str, str]:
    """The packages the specifiers come from, with the versions the image installed."""
    return dict(allowlist()["packages"])


def package_of(specifier: str) -> str | None:
    """The allowlisted package a bare specifier names (`@mui/x-charts/BarChart` is `@mui/x-charts`), else None."""
    for name in packages():
        if specifier == name or specifier.startswith(f"{name}/"):
            return name
    return None


def mui_version() -> str:
    """The MUI X version the image bundles (`9.16.0` on 2026-10-30), for the readiness hint."""
    return packages().get(MUI_PACKAGE, "?")
