"""The import allowlist of the JavaScript row: every module specifier a MUI X snippet may import.

esbuild inlines whatever a `.tsx` snippet imports, image files included (`import x from
"/etc/os-release"` bundles), so the bundle step admits only bare specifiers that the installed
packages export (second opinion on step 3 of agentic/specs/261024-agent-all-libraries.md, Fable,
2026-10-30). This script derives that list from the `exports` maps of the packages in `PACKAGES`
as the toolchain image installed them, and writes one JSON file that the bundle step's resolve
plugin (`automation/js-render/render.mjs`, JS-2) and the code profile's validator (JS-3) both read:

    {
      "schema": 1,
      "packages": {"@mui/material": "9.5.0", "@mui/x-charts": "9.16.0", "react": "19.3.1", "react-dom": "19.3.1"},
      "specifiers": ["@mui/material", "@mui/material/Accordion", ..., "react", "react/jsx-runtime", ...]
    }

A specifier is the package name for the export key `.` and the name joined with the key's path
for `./<path>`; `./package.json` is data, not a module, and a key mapped to null is a blocked
path, so neither is listed. A pattern key (`./*`) would admit paths nobody listed, so it fails
the build instead of being expanded or skipped, and so does a package without an `exports` map.

The toolchain build runs it with the base image's interpreter (standard library only):

    python3 import_allowlist.py /opt/anyplot/node_modules > /opt/anyplot/js-render/import-allowlist.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


SCHEMA = 1
"""The file's shape; a consumer refuses a schema it does not know."""
PACKAGES = ("@mui/material", "@mui/x-charts", "react", "react-dom")
"""The packages a MUI X snippet may import from: the React stack and MUI's community packages."""


class AllowlistError(ValueError):
    """A package whose `exports` map cannot be turned into a closed list of specifiers."""


def specifiers(name: str, manifest: dict) -> list[str]:
    """The bare specifiers one package's `exports` map admits, sorted."""
    exports = manifest.get("exports")
    if exports is None:
        raise AllowlistError(f"{name} has no exports map, so every file in it would be importable")
    if isinstance(exports, str | list) or (isinstance(exports, dict) and not any(k.startswith(".") for k in exports)):
        return [name]  # one entry point, given directly or by conditions
    if not isinstance(exports, dict):
        raise AllowlistError(f"{name} has an exports value of type {type(exports).__name__}")
    found: list[str] = []
    for key, target in exports.items():
        if not key.startswith("."):
            raise AllowlistError(f"{name} mixes conditions and paths in its exports map ({key!r})")
        if "*" in key:
            raise AllowlistError(f"{name} exports the pattern {key!r}, which a list cannot close")
        if target is None or key == "./package.json":
            continue
        if key == ".":
            found.append(name)
        elif key.startswith("./"):
            found.append(f"{name}/{key[2:]}")
        else:
            raise AllowlistError(f"{name} has the malformed export key {key!r}")
    return sorted(found)


def allowlist(node_modules: Path, packages: tuple[str, ...] = PACKAGES) -> dict:
    """The allowlist of the packages installed under `node_modules`; `AllowlistError` for a missing package."""
    versions: dict[str, str] = {}
    admitted: list[str] = []
    for name in packages:
        path = node_modules / name / "package.json"
        if not path.is_file():
            raise AllowlistError(f"{name} is not installed under {node_modules}")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        versions[name] = manifest["version"]
        admitted.extend(specifiers(name, manifest))
    return {"schema": SCHEMA, "packages": dict(sorted(versions.items())), "specifiers": sorted(admitted)}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: import_allowlist.py <node_modules>", file=sys.stderr)
        return 2
    try:
        result = allowlist(Path(argv[0]))
    except AllowlistError as exc:
        print(f"import allowlist: {exc}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, indent=1)
    sys.stdout.write("\n")
    counts = {name: sum(1 for s in result["specifiers"] if s == name or s.startswith(f"{name}/")) for name in PACKAGES}
    print(f"import allowlist: {len(result['specifiers'])} specifiers {counts}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
