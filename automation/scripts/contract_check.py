#!/usr/bin/env python3
"""Static contract check of one implementation file (record-only).

The generator prompt mandates a few things that show in the source without
running it. The catalogue audit of 2026-11-08 found legacy files that miss
them behind compliant staged renders, so ``impl-review.yml`` checks the file at
the PR head, and on a regeneration its predecessor, with this script (rule
step P2b). Record-only for now: it writes a job-summary line and a notice and
always exits 0; nothing reads the result yet.

Each rule is a text pattern over the code, named by its key in the record. A
rule says what the code contains, not what the render shows:

- ``title``: the code lacks the mandated title tail
  ``{language} · {library} · anyplot.ai``, or never names the spec id outside
  the header (``prompts/plot-generator.md``, "Title format").
- ``theme``: the code never names ``ANYPLOT_THEME``; in JavaScript, neither
  ``ANYPLOT_THEME`` nor ``ANYPLOT_TOKENS``, the two globals of the render
  harness.
- ``save``: the code builds no file name from ``plot-`` and a theme value, or
  it names a bare ``plot.png``, ``plot.html`` or ``plot.svg``. JavaScript is
  exempt, because the harness saves.
- ``legacy-colour``: the code holds a brand hex of an earlier palette: Python
  blue and yellow of the pyplots.ai era, or the variant-D palette
  (``prompts/quality-criteria.md``, VQ-07, lists all but the yellow).
- ``colormap``: a named library colormap sits in a colormap position
  (``prompts/default-style-guide.md``, "Continuous Data": only the two
  Imprint colormaps are allowed).
- ``palette``: the code holds a six-digit hex that is neither an Imprint
  colour, nor an anchor, nor a theme token of the style guide. The owner's
  rule (2026-11-11): use the Imprint colours unless there is a very good
  reason, so this rule records a deviation; whether the reason is good is
  for a reader to judge, never for this script.

Comments and the generated header never count. The patterns are deliberately
narrow: a rule that flags a compliant file is worse than no rule, so a
colormap name counts only where a colormap goes, never as a data label such
as ``"Oranges"``.

Stdlib only: ``impl-review.yml`` runs a copy taken at the workflow's own ref
with the job's pinned ``python3``, so a PR head cannot choose its own rules.

Subcommand::

    contract_check.py check --source NEW --spec-id S --language L --library B \
        [--prev PREV] [--out RECORD.json]

``--source`` and ``--prev`` may name files that do not exist: a missing new
file reads as ``unreadable``, a missing predecessor as a first generation.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tokenize
from pathlib import Path


RECORD_VERSION = 1
RULES = ("title", "theme", "save", "legacy-colour", "colormap", "palette")
LANGUAGES = ("python", "r", "julia", "javascript")

# Python blue and yellow, then the variant-D palette. An alpha suffix (#RRGGBBAA) counts too.
LEGACY_HEXES = ("306998", "FFD43B", "9418DB", "B71D27", "16B8F3", "D359A7", "BA843E")
LEGACY_RE = re.compile(r"#(?:" + "|".join(LEGACY_HEXES) + r")(?:[0-9A-Fa-f]{2})?\b", re.IGNORECASE)

# prompts/default-style-guide.md: the eight Imprint hues, the amber anchor, the
# ink and muted pairs, and the page, elevated and soft-ink tokens of both
# themes. tests/unit/automation/scripts/test_contract_check.py keeps this set
# equal to core/palette.py and inside the style guide.
PALETTE_HEXES = frozenset(
    {
        "#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314",  # Imprint
        "#DDCC77",  # amber
        "#1A1A17", "#F0EFE8",  # ink (and the dark page)
        "#6B6A63", "#A8A79F",  # muted
        "#FAF8F1", "#FFFDF6", "#242420",  # light page, elevated light, elevated dark
        "#4A4A44", "#B8B7B0",  # soft ink
    }
)  # fmt: skip
HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")
PALETTE_DETAIL_CAP = 8

# Named colormaps of the libraries' own registries (matplotlib, seaborn, plotly, bokeh, ColorBrewer).
_NAMED = (
    r"(?:viridis|cividis|plasma|inferno|magma|turbo|jet|hsv|rainbow|gist_\w+|nipy_spectral|Spectral|BrBG|RdBu"
    r"|RdYlGn|RdYlBu|RdGy|PuOr|PiYG|PRGn|coolwarm|bwr|seismic|Blues|Greens|Reds|Oranges|Purples|Greys|YlOrRd"
    r"|YlOrBr|YlGnBu|YlGn|GnBu|BuGn|BuPu|PuBu|PuRd|RdPu|OrRd|hot|cool|copper|bone|gray|grey|binary|terrain"
    r"|ocean|twilight\w*|cubehelix|mako|rocket|flare|crest|icefire|vlag|Portland|Jet|Hot|Electric|Bluered"
    r"|Picnic|Rainbow|Viridis|Cividis|Plasma|Inferno|Magma|Turbo|Blackbody|Earth)(?:_r|256|\d{1,2})?"
)
# A keyword may be the tail of a longer name (`coloraxis_colorscale`, `mpl_cm`), never of a word.
_KW = r"(?<![A-Za-z0-9])"
COLORMAP_RES: dict[str, tuple[re.Pattern[str], ...]] = {
    "python": tuple(
        re.compile(pattern)
        for pattern in (
            rf"{_KW}(?:cmap|cmap_name|colorscale|color_continuous_scale|continuous_scale|palette)\s*=\s*[\"']{_NAMED}[\"']",
            # Vega schemes are always names (Altair builds an Imprint scale from a `range`).
            rf"{_KW}scheme\s*=\s*[\"'][A-Za-z][\w-]*[\"']",
            rf"(?:color_palette|get_cmap|scale_\w+_cmap)\(\s*[\"']{_NAMED}[\"']",
            rf"colormaps\[\s*[\"']{_NAMED}[\"']\s*\]",
            rf"{_KW}cm\.{_NAMED}\b",
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
            r"\bbrewer\.pal\(|\bRColorBrewer::|\bviridisLite::|\bviridis::",
        )
    ),
    "julia": tuple(
        re.compile(pattern) for pattern in (rf"colou?rmap\s*=\s*(?::|\"){_NAMED}\b", rf"cgrad\(\s*(?::|\"){_NAMED}\b")
    ),
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

THEME_RES = {
    "python": re.compile(r"[\"']ANYPLOT_THEME[\"']"),
    "r": re.compile(r"[\"']ANYPLOT_THEME[\"']"),
    "julia": re.compile(r"\"ANYPLOT_THEME\""),
    "javascript": re.compile(r"\bANYPLOT_(?:TOKENS|THEME)\b"),
}
# `plot-` followed by a value: an f-string or glue field, a %s, a Julia $ interpolation, or the
# end of the string and a `+`, `*` or `,` (concatenation, paste0, string).
SAVE_RE = re.compile(r"plot-(?:\{|%s|\$|[\"']\s*[+*,])")
BARE_SAVE_RE = re.compile(r"[\"'](?:\./)?plot\.(?:png|html|svg)[\"']")


def strip_header(language: str, source: str) -> str:
    """The source without its generated header: the leading comment lines and, in Python, the docstring.

    The header is whatever the file starts with, however long: the run of
    comment lines (R's ``#'``, JavaScript's ``//#`` directives, a Python
    ``# ruff: noqa`` line), then a Python docstring.
    """
    lines = source.lstrip("﻿").split("\n")
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
    rest = "\n".join(lines[first_code:])
    if language == "python":
        for quote in ('"""', "'''"):
            if rest.startswith(quote):
                end = rest.find(quote, len(quote))
                return rest[end + len(quote) :] if end != -1 else ""
    return rest


# Per language: the line-comment marker, the block-comment delimiters, and the string quotes.
_COMMENT_SYNTAX: dict[str, tuple[str, tuple[str, str] | None, str]] = {
    "python": ("#", None, "\"'"),
    "r": ("#", None, "\"'"),
    "julia": ("#", ("#=", "=#"), '"'),
    "javascript": ("//", ("/*", "*/"), "\"'`"),
}


def _scan_out_comments(code: str, marker: str, block: tuple[str, str] | None, quotes: str) -> str:
    """``code`` without line comments and block comments, read character by character.

    A marker inside a string literal is text, not a comment. A quote that is
    still open at the end of its line closes there (an apostrophe in JSX text,
    Julia's transpose), except a backtick: a template literal spans lines.
    """
    out: list[str] = []
    quote = ""
    index = 0
    size = len(code)
    while index < size:
        char = code[index]
        if quote:
            out.append(char)
            if char == "\\" and index + 1 < size:
                out.append(code[index + 1])
                index += 2
                continue
            if char == quote or (char == "\n" and quote != "`"):
                quote = ""
            index += 1
            continue
        if block and code.startswith(block[0], index):
            end = code.find(block[1], index + len(block[0]))
            index = size if end == -1 else end + len(block[1])
            continue
        if code.startswith(marker, index):
            end = code.find("\n", index)
            index = size if end == -1 else end
            continue
        if char in quotes:
            quote = char
        out.append(char)
        index += 1
    return "".join(out)


def _python_comment_columns(code: str) -> dict[int, int] | None:
    """Row to column of every comment token, or None when the code does not tokenize."""
    columns: dict[int, int] = {}
    try:
        for token in tokenize.generate_tokens(io.StringIO(code).readline):
            if token.type == tokenize.COMMENT:
                columns[token.start[0]] = token.start[1]
    except tokenize.TokenError, SyntaxError:
        return None
    return columns


def strip_comments(language: str, code: str) -> str:
    """The code without comments: Python by its tokens, the others by a scan that knows strings.

    A ``#`` or ``//`` inside a string stays (a hex colour, a URL, ``"Issue # 42"``).
    Line comments and whole block comments go (JavaScript ``/* */``, Julia
    ``#= =#``), over as many lines as they span, and so do the lines they leave empty.
    """
    columns = _python_comment_columns(code) if language == "python" else None
    if columns is not None:
        lines = code.split("\n")
        for row, column in columns.items():
            lines[row - 1] = lines[row - 1][:column]
    else:
        lines = _scan_out_comments(code, *_COMMENT_SYNTAX[language]).split("\n")
    return "\n".join(line for line in lines if line.strip())


def custom_hexes(code: str) -> list[str]:
    """The six-digit hexes of ``code`` outside the style guide's set, upper case, in order of appearance."""
    seen: list[str] = []
    for match in HEX_RE.findall(code):
        value = match.upper()
        if value not in PALETTE_HEXES and value not in seen:
            seen.append(value)
    return seen


def check(source: str, *, spec_id: str, language: str, library: str) -> tuple[list[str], dict[str, list[str]]]:
    """The rules ``source`` breaks, in ``RULES`` order, and per rule what it found (the palette rule's hexes)."""
    code = strip_comments(language, strip_header(language, source))
    found = []
    details: dict[str, list[str]] = {}
    if f"{language} · {library} · anyplot.ai" not in code or spec_id not in code:
        found.append("title")
    if not THEME_RES[language].search(code):
        found.append("theme")
    if language != "javascript" and (not SAVE_RE.search(code) or BARE_SAVE_RE.search(code)):
        found.append("save")
    if LEGACY_RE.search(code):
        found.append("legacy-colour")
    if any(pattern.search(code) for pattern in COLORMAP_RES[language]):
        found.append("colormap")
    hexes = custom_hexes(code)
    if hexes:
        found.append("palette")
        details["palette"] = hexes[:PALETTE_DETAIL_CAP]
    return found, details


def violations(source: str, *, spec_id: str, language: str, library: str) -> list[str]:
    """The rules ``source`` breaks, in ``RULES`` order."""
    return check(source, spec_id=spec_id, language=language, library=library)[0]


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
        return {
            **record,
            "status": "unreadable",
            "violations": [],
            "prev_violations": None,
            "new_only": [],
            "details": {},
        }
    now, details = check(new, spec_id=spec_id, language=language, library=library)
    before = None if prev is None else violations(prev, spec_id=spec_id, language=language, library=library)
    new_only = now if before is None else [rule for rule in now if rule not in before]
    return {
        **record,
        "status": "clean" if not now else "violations",
        "violations": now,
        "prev_violations": before,
        "new_only": new_only,
        "details": details,
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
    if record["details"].get("palette"):
        line += "; outside the palette: " + ", ".join(f"`{value}`" for value in record["details"]["palette"])
    return line


def notice_line(record: dict) -> str:
    """One log line, the same shape as ``canvas_gate`` and ``render_hash``."""
    prev = "n/a" if record["prev_violations"] is None else (",".join(record["prev_violations"]) or "none")
    line = (
        f"::notice::contract_check library={record['library']} status={record['status']} "
        f"violations={','.join(record['violations']) or 'none'} prev={prev} "
        f"new_only={','.join(record['new_only']) or 'none'}"
    )
    if record["details"].get("palette"):
        line += " palette_hexes=" + ",".join(record["details"]["palette"])
    return line


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
    check_parser = sub.add_parser("check", help="check one implementation file, record-only")
    check_parser.add_argument("--source", required=True, help="the implementation at the PR head")
    check_parser.add_argument(
        "--prev", help="the predecessor from main (a regeneration); a missing file is a first generation"
    )
    check_parser.add_argument("--spec-id", required=True)
    check_parser.add_argument("--language", required=True, choices=LANGUAGES)
    check_parser.add_argument("--library", required=True)
    check_parser.add_argument("--out", help="write the record as one JSON line")
    check_parser.set_defaults(func=cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
