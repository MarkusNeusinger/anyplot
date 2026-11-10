#!/usr/bin/env python3
"""Static contract check of one implementation file (record-only).

The generator prompt mandates a few things that show in the source without
running it. The catalogue audit of 2026-11-08 found legacy files that miss
them behind compliant staged renders, so ``impl-review.yml`` checks the file at
the PR head, and on a regeneration its predecessor, with this script (rule
step P2b). Record-only for now: it writes a job-summary line and a notice and
always exits 0; nothing reads the result yet.

Rules, each named by its key in the record:

- ``title``: the code carries the mandated title tail
  ``{language} · {library} · anyplot.ai`` and names the spec id outside the
  header (``prompts/plot-generator.md``, "Title format").
- ``theme``: the code reads ``ANYPLOT_THEME``; a JavaScript file reads
  ``ANYPLOT_TOKENS``, which the render harness derives from the theme.
- ``save``: the code writes ``plot-{theme}.png`` and no bare ``plot.png``.
  JavaScript is exempt, because the harness saves.
- ``legacy-colour``: none of the legacy brand hexes
  (``prompts/quality-criteria.md``, VQ-07, score 0).
- ``colormap``: no named library colormap in a colormap position
  (``prompts/default-style-guide.md``, "Continuous Data": only the two
  Imprint colormaps are allowed).

Comments and the generated header never count: a rule looks at code only.
The patterns are deliberately narrow. A rule that flags a compliant file is
worse than no rule, so a pattern matches a colormap name only where a
colormap goes, never a data label such as ``"Oranges"``.

Stdlib only: ``impl-review.yml`` runs a copy taken at the workflow's own ref
with the runner's ``python3``, so a PR head cannot choose its own rules.

Subcommand::

    contract_check.py check --source NEW --spec-id S --language L --library B \
        [--prev PREV] [--out RECORD.json]

``--source`` and ``--prev`` may name files that do not exist: a missing new
file reads as ``unreadable``, a missing predecessor as a first generation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


RECORD_VERSION = 1
RULES = ("title", "theme", "save", "legacy-colour", "colormap")
LANGUAGES = ("python", "r", "julia", "javascript")

# quality-criteria.md, VQ-07 score 0: Python Blue, its yellow, and the variant-D palette.
LEGACY_HEXES = ("306998", "FFD43B", "9418DB", "B71D27", "16B8F3", "D359A7", "BA843E")
LEGACY_RE = re.compile(r"#(?:" + "|".join(LEGACY_HEXES) + r")\b", re.IGNORECASE)

# Named colormaps of the libraries' own registries (matplotlib, seaborn, plotly, bokeh, ColorBrewer).
_NAMED = (
    r"(?:viridis|cividis|plasma|inferno|magma|turbo|jet|hsv|rainbow|gist_\w+|nipy_spectral|Spectral|BrBG|RdBu"
    r"|RdYlGn|RdYlBu|RdGy|PuOr|PiYG|PRGn|coolwarm|bwr|seismic|Blues|Greens|Reds|Oranges|Purples|Greys|YlOrRd"
    r"|YlOrBr|YlGnBu|YlGn|GnBu|BuGn|BuPu|PuBu|PuRd|RdPu|OrRd|hot|cool|copper|bone|gray|grey|twilight\w*"
    r"|cubehelix|mako|rocket|flare|crest|icefire|vlag|Portland|Jet|Hot|Electric|Bluered|Picnic|Rainbow|Viridis"
    r"|Cividis|Plasma|Inferno|Magma|Turbo|Blackbody|Earth)(?:_r|256|\d{1,2})?"
)
COLORMAP_RES: dict[str, tuple[re.Pattern[str], ...]] = {
    "python": tuple(
        re.compile(pattern)
        for pattern in (
            rf"\b(?:cmap|cmap_name|colorscale|color_continuous_scale|continuous_scale|scheme|palette)\s*=\s*[\"']{_NAMED}[\"']",
            rf"(?:color_palette|get_cmap|scale_\w+_cmap)\(\s*[\"']{_NAMED}[\"']",
            rf"colormaps\[\s*[\"']{_NAMED}[\"']\s*\]",
            rf"\bcm\.{_NAMED}\b",
            r"\bscale_\w+_(?:viridis\w*|brewer|distiller)\b",
            r"\b(?:Viridis|Inferno|Magma|Plasma|Cividis|Turbo)256\b",
            r"\bbokeh\.palettes\b[^\n]*\b(?:Spectral|RdBu|BrBG|Blues|Greens|Reds)\d+",
        )
    ),
    "r": tuple(
        re.compile(pattern)
        for pattern in (
            r"\bscale_\w+_(?:viridis\w*|brewer|distiller|fermenter)\(",
            r"\b(?:rainbow|heat\.colors|terrain\.colors|topo\.colors|cm\.colors|hsv|hcl\.colors)\(",
            r"\bbrewer\.pal\(|\bRColorBrewer::|\bviridisLite::",
        )
    ),
    "julia": tuple(re.compile(pattern) for pattern in (rf"colou?rmap\s*=\s*:{_NAMED}\b", rf"cgrad\(\s*:{_NAMED}\b")),
    "javascript": tuple(
        re.compile(pattern)
        for pattern in (
            r"\b(?:d3\.)?interpolate(?:Viridis|Turbo|Rainbow|Sinebow|Plasma|Inferno|Magma|Cividis|Cool|Warm"
            r"|Cubehelix\w*|Spectral|RdBu|RdYlGn|RdYlBu|BrBG|PuOr|PiYG|PRGn|Blues|Greens|Reds|Oranges|Purples"
            r"|Greys|YlOrRd|YlGnBu)\b",
            r"\b(?:d3\.)?scheme(?:Category10|Tableau10|Set[123]|Paired|Pastel[12]|Dark2|Accent|Spectral|RdBu"
            r"|BrBG|Blues|Greens|Reds)\b",
        )
    ),
}

# What reading the theme looks like: the variable's name as a string (JavaScript: the tokens object).
THEME_RES = {
    "python": re.compile(r"[\"']ANYPLOT_THEME[\"']"),
    "r": re.compile(r"[\"']ANYPLOT_THEME[\"']"),
    "julia": re.compile(r"\"ANYPLOT_THEME\""),
    "javascript": re.compile(r"\bANYPLOT_TOKENS\b"),
}
# A themed save target: the file name is built from the theme, in any of the usual ways.
SAVE_RES = {
    "python": re.compile(r"plot-\{[^{}\n]*\}|plot-%s|[\"']plot-[\"']\s*\+"),
    "r": re.compile(r"plot-%s|paste0?\(\s*[\"']plot-[\"']\s*,|plot-\{[^{}\n]*\}"),
    "julia": re.compile(r"plot-\$\(?[A-Za-z_]\w*\)?"),
}
BARE_SAVE_RE = re.compile(r"[\"'](?:\./)?plot\.(?:png|html|svg)[\"']")


def strip_header(language: str, source: str) -> str:
    """The source without its generated header: the leading docstring or the leading comment lines.

    The header is whatever the file starts with, however long: a Python
    docstring, or the run of comment lines of the other languages (which
    includes JavaScript's ``//#`` directives).
    """
    text = source.lstrip("﻿")
    if language == "python":
        stripped = text.lstrip()
        for quote in ('"""', "'''"):
            if stripped.startswith(quote):
                end = stripped.find(quote, len(quote))
                return stripped[end + len(quote) :] if end != -1 else ""
        return text
    lines = text.split("\n")
    marker = "//" if language == "javascript" else "#"
    first_code = 0
    in_block = False
    for index, line in enumerate(lines):
        bare = line.strip()
        if language == "javascript" and (in_block or bare.startswith("/*")):
            in_block = "*/" not in bare
            first_code = index + 1
            continue
        if not bare or bare.startswith(marker):
            first_code = index + 1
            continue
        break
    return "\n".join(lines[first_code:])


def strip_comments(language: str, code: str) -> str:
    """Drop whole-line comments and trailing ``␣#␣…`` / ``␣//␣…`` comments (a hex colour keeps its ``#``)."""
    out = []
    for line in code.split("\n"):
        if language == "javascript":
            if re.match(r"\s*(?://|\*|/\*)", line):
                continue
            line = re.sub(r"\s//\s.*$", "", line)
        else:
            if re.match(r"\s*#", line):
                continue
            line = re.sub(r"\s#\s.*$", "", line)
        out.append(line)
    return "\n".join(out)


def violations(source: str, *, spec_id: str, language: str, library: str) -> list[str]:
    """The rules ``source`` breaks, in ``RULES`` order."""
    code = strip_comments(language, strip_header(language, source))
    found = []
    if f"{language} · {library} · anyplot.ai" not in code or spec_id not in code:
        found.append("title")
    if not THEME_RES[language].search(code):
        found.append("theme")
    if language != "javascript" and (not SAVE_RES[language].search(code) or BARE_SAVE_RE.search(code)):
        found.append("save")
    if LEGACY_RE.search(code):
        found.append("legacy-colour")
    if any(pattern.search(code) for pattern in COLORMAP_RES[language]):
        found.append("colormap")
    return found


def _read(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return None


def build_record(new: str | None, prev: str | None, *, spec_id: str, language: str, library: str) -> dict:
    """The record of one check: the new file's violations, the predecessor's, and the ones only the new file has."""
    record: dict = {"version": RECORD_VERSION, "spec_id": spec_id, "language": language, "library": library}
    if new is None:
        return {**record, "status": "unreadable", "violations": [], "prev_violations": None, "new_only": []}
    now = violations(new, spec_id=spec_id, language=language, library=library)
    before = None if prev is None else violations(prev, spec_id=spec_id, language=language, library=library)
    new_only = now if before is None else [rule for rule in now if rule not in before]
    return {
        **record,
        "status": "clean" if not now else "violations",
        "violations": now,
        "prev_violations": before,
        "new_only": new_only,
    }


def summary_line(record: dict) -> str:
    """One Markdown line for the job summary."""
    if record["status"] == "unreadable":
        return "**Contract check (record-only):** unreadable (no implementation file at the PR head)"
    if record["status"] == "clean":
        return "**Contract check (record-only):** clean"
    line = "**Contract check (record-only):** " + ", ".join(record["violations"])
    if record["prev_violations"] is not None:
        line += " (new in this version: " + (", ".join(record["new_only"]) or "none") + ")"
    return line


def notice_line(record: dict) -> str:
    """One log line, the same shape as ``canvas_gate`` and ``render_hash``."""
    prev = "n/a" if record["prev_violations"] is None else (",".join(record["prev_violations"]) or "none")
    return (
        f"::notice::contract_check library={record['library']} status={record['status']} "
        f"violations={','.join(record['violations']) or 'none'} prev={prev} "
        f"new_only={','.join(record['new_only']) or 'none'}"
    )


def cmd_check(args: argparse.Namespace) -> int:
    record = build_record(
        _read(args.source), _read(args.prev), spec_id=args.spec_id, language=args.language, library=args.library
    )
    print(notice_line(record))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(summary_line(record) + "\n")
    if args.out:
        Path(args.out).write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check one implementation file, record-only")
    check.add_argument("--source", required=True, help="the implementation at the PR head")
    check.add_argument(
        "--prev", help="the predecessor from main (a regeneration); a missing file is a first generation"
    )
    check.add_argument("--spec-id", required=True)
    check.add_argument("--language", required=True, choices=LANGUAGES)
    check.add_argument("--library", required=True)
    check.add_argument("--out", help="write the record as one JSON line")
    check.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
