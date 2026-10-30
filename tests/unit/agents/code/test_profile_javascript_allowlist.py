"""The agents package's copy of the MUI X import allowlist (`profiles/javascript/import-allowlist.json`).

The renderer image generates the allowlist at build (`agents/renderer/toolchain/import_allowlist.py`, JS-1); the agents
image has no `node_modules`, so the JavaScript profile reads a copy. Where the repository's `node_modules` is installed
(`npm ci --ignore-scripts`), the copy is compared with a fresh run of the image's own script over it, and the test skips
elsewhere; the renderer image's CI job compares the built image's file with the copy (`.github/workflows/ci-image.yml`)
and skips nowhere. A lock bump that changes the packages' exports fails them until the copy is regenerated.
"""

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from agents.anyplot.code.profiles.javascript import allowlist as copy

from .conftest import JS_CATALOGUE_FILES, REPO_ROOT


BUILDER = REPO_ROOT / "agents" / "renderer" / "toolchain" / "import_allowlist.py"


def _node_modules() -> Path | None:
    root = Path(os.environ.get("ANYPLOT_NODE_MODULES", REPO_ROOT / "node_modules"))
    return root if all((root / name / "package.json").is_file() for name in copy.packages()) else None


def test_the_copy_is_an_allowlist_of_the_images_schema() -> None:
    parsed = copy.allowlist()

    assert parsed["schema"] == copy.SCHEMA == 1
    assert set(parsed["packages"]) == {"@mui/material", "@mui/x-charts", "react", "react-dom"}
    assert parsed["specifiers"] == sorted(parsed["specifiers"])
    assert "@mui/x-charts/ChartsContainer" in copy.specifiers()
    assert "@mui/x-charts/ChartContainer" not in copy.specifiers()
    assert copy.package_of("@mui/x-charts/BarChart") == "@mui/x-charts"
    assert copy.package_of("@mui/x-charts-pro") is None
    assert copy.package_of("react-dom/client") == "react-dom"


def test_the_copy_is_byte_for_byte_what_the_images_script_writes() -> None:
    """The file is the script's output (`json.dump(..., indent=1)` and a newline), so `cmp` in CI compares it too."""
    text = copy.ALLOWLIST_FILE.read_text(encoding="utf-8")

    assert text == json.dumps(copy.allowlist(), indent=1) + "\n"


def test_the_copy_equals_the_allowlist_of_the_installed_packages() -> None:
    modules = _node_modules()
    if modules is None:
        pytest.skip("needs the lock's node_modules (npm ci --ignore-scripts, or ANYPLOT_NODE_MODULES)")
    spec = importlib.util.spec_from_file_location("import_allowlist", BUILDER)
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    assert builder.allowlist(modules) == copy.allowlist(), (
        "regenerate the copy: python3 agents/renderer/toolchain/import_allowlist.py node_modules > "
        "agents/anyplot/code/profiles/javascript/import-allowlist.json"
    )


def test_the_removed_exports_are_not_exported_and_the_catalogue_imports_nothing_else_that_is_missing() -> None:
    """Every name a catalogue MUI X file imports from an allowlisted module exists in the installed MUI X, except the
    names of `REMOVED_EXPORTS`, which none of its modules exports (Node imports each module and lists its names)."""
    modules = _node_modules()
    node = shutil.which("node")
    if modules is None or node is None:
        pytest.skip("needs node on PATH and the lock's node_modules")
    from agents.anyplot.code.profiles.javascript.regions import find_regions

    wanted: dict[str, set[str]] = {}
    for path in JS_CATALOGUE_FILES:
        if path.suffix != ".tsx":
            continue
        for module in find_regions(path.read_text(encoding="utf-8"), library="muix").imports:
            if module.specifier in copy.specifiers() and module.specifier.startswith(copy.MUI_PACKAGE):
                wanted.setdefault(module.specifier, set()).update(
                    name for name in module.names if name not in ("default", "*")
                )
    mui = sorted(name for name in copy.specifiers() if name.startswith(copy.MUI_PACKAGE))
    script = (
        "const out = {};\n"
        f"for (const name of {json.dumps(mui)}) {{\n"
        "  try { out[name] = Object.keys(await import(name)); } catch (e) { out[name] = null; }\n"
        "}\n"
        "console.log(JSON.stringify(out));\n"
    )
    done = subprocess.run(
        [node, "--input-type=module", "-e", script],
        cwd=modules.parent,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if done.returncode != 0:
        pytest.skip(f"node could not import MUI X here: {done.stderr.strip()[-300:]}")
    exported: dict[str, list[str] | None] = json.loads(done.stdout.strip().splitlines()[-1])

    every = {name for names in exported.values() if names for name in names}
    assert not set(copy.REMOVED_EXPORTS) & every
    missing = {
        (specifier, name)
        for specifier, names in wanted.items()
        if exported.get(specifier) is not None
        for name in names
        if name not in (exported[specifier] or [])
    }
    assert {name for _, name in missing} <= set(copy.REMOVED_EXPORTS), missing
