#!/usr/bin/env python3
"""Lint the "What a good version looks like" section of plot specifications.

The section closes ``plots/{spec-id}/specification.md``. The AI review scores
every implementation against it, and the regen gate numbers its bullets
``C1..Cn`` (``regen_gate.parse_characteristics``). This lint imports that
parser, so the lint and the gate always read the same bullets. Standard
library only: CI runs it with the runner's own ``python3`` before any
dependency is installed.

Run it from the repository root::

    python3 -m automation.scripts.spec_characteristics_lint contract [--all] [--require-section] [FILE ...]
    python3 -m automation.scripts.spec_characteristics_lint style [--strict] FILE ...

``contract`` checks the shape the gate relies on. It prints ``::error``
annotations and exits 1 on any violation:

- K1: the exact heading ``## What a good version looks like`` appears at most
  once, and no other spelling of it appears;
- K2: the section is the last one and has no sub-headings;
- K3: its body holds only blank lines, column-0 ``- `` bullets and indented
  continuation lines of a bullet;
- K4: 2-8 bullets;
- K5: no duplicate bullets;
- K6: every bullet starts with exactly ``A good version shows: `` or
  ``Expected, not a defect: `` and carries one kind;
- K7: the gate's parser reads as many bullets as the lint does;
- K8: LF line endings.

``--require-section`` also fails a spec without the section (unused until
every spec has one).

``style`` checks house style and prints ``::warning`` annotations (exit 0).
With ``--strict``, its hard rules print ``::error`` and exit 1: the mode the
one-time backfill uses.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from automation.scripts.regen_gate import (
    CHARACTERISTICS_HEADING_RE,
    EXPECTED_PREFIX,
    KIND_EXPECTED,
    KIND_SHOWS,
    NEXT_SECTION_RE,
    SHOWS_PREFIX,
    characteristic_kind,
    parse_characteristics,
)


HEADING = "## What a good version looks like"
PREFIXES = {KIND_SHOWS: SHOWS_PREFIX, KIND_EXPECTED: EXPECTED_PREFIX}

CONTRACT_BULLETS = (2, 8)
STYLE_BULLETS = (3, 6)
HARD_MAX_CHARS = 400
SOFT_MAX_CHARS = 320

ERROR = "error"
WARNING = "warning"

# Any heading level, any case, any spacing: every spelling the gate would miss
# or read only by luck. The exact heading is the one spelling that passes.
NEAR_MISS_HEADING_RE = re.compile(r"^\s*#+\s*what\s+a\s+good\s+version\s+looks\s+like", re.IGNORECASE)
OTHER_SECTION_RE = re.compile(r"^##\s+(?P<name>\S.*?)\s*$")
# A kind prefix after the first one, spelled as leniently as the gate reads the
# first (any case, optional comma and bold markers). The gate reads only the
# opening prefix, so a second one would change nothing it does. Mentioning the
# phrase without its colon is fine.
SECOND_PREFIX_RE = re.compile(r"\b(?:a good version shows|expected,?\s*not a defect)\s*[*_]{0,2}\s*:", re.IGNORECASE)

GENERIC_PHRASES = (
    "no overlap",
    "clean design",
    "clean look",
    "visually appealing",
    "aesthetically pleasing",
    "professional",
    "publication quality",
    "easy to read",
    "clear and readable",
    "well labeled",
    "well labelled",
    "everything is labeled",
    "everything is labelled",
    "modern",
    "beautiful",
    "polished",
)
# Domain terms that contain a generic word but are not a generic ideal.
GENERIC_ALLOWLIST = ("modern portfolio theory", "professional sports", "professional services")

LIBRARY_NAMES = (
    "matplotlib",
    "pyplot",
    "seaborn",
    "plotly",
    "bokeh",
    "altair",
    "plotnine",
    "pygal",
    "lets-plot",
    "letsplot",
    "ggplot2",
    "ggplot",
    "makie",
    "cairomakie",
    "chart.js",
    "chartjs",
    "d3.js",
    "d3",
    "echarts",
    "highcharts",
    "mui x",
    "muix",
    "vega-lite",
    "numpy",
    "pandas",
    "scipy",
    "networkx",
    "scikit-learn",
    "sklearn",
    "statsmodels",
)


def _phrase_re(phrase: str) -> str:
    return r"\b" + r"[\s-]+".join(re.escape(word) for word in phrase.split()) + r"\b"


GENERIC_RE = re.compile("|".join(_phrase_re(p) for p in GENERIC_PHRASES), re.IGNORECASE)
GENERIC_ALLOW_RE = re.compile("|".join(_phrase_re(p) for p in GENERIC_ALLOWLIST), re.IGNORECASE)
UNIT_RE = re.compile(r"\d(?:[\d.,]*\d)?\s*(?:(?:px|pt|dpi)\b|%)", re.IGNORECASE)
COMPARATOR_RE = re.compile(r"(?:\b(?:at least|at most|under|over|max|min)\b|[≥≤<>~])\s*\d", re.IGNORECASE)
VISUAL_VALUE_RE = re.compile(
    r"\b(?:alpha|opacity|line[\s-]?width|font[\s-]?size)\b\s*(?:=|:|of|at|to|around|about)?\s*~?\s*\d"
    r"|\d(?:\.\d+)?\s*(?:alpha|opacity)\b",
    re.IGNORECASE,
)
LIBRARY_RE = re.compile(
    r"(?<![\w.])(?:" + "|".join(re.escape(n).replace(r"\ ", r"\s+") for n in LIBRARY_NAMES) + r")(?!\w)", re.IGNORECASE
)
# name( or obj.method( — call syntax; "value(s)" is prose, not a call.
CALL_RE = re.compile(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*\((?!s\))")
HEX_RE = re.compile(r"(?<![\w&])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?!\w)")
NUMERAL_RE = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?(?!\w)")

NEGATION_RE = re.compile(r"\b(?:adds no|no|never|without)\b", re.IGNORECASE)
TRIGGER_RE = re.compile(
    r"\b(?:includ(?:e|es|ed|ing)|add(?:s|ed|ing)?|show(?:s|n|ed|ing)?|us(?:e|es|ed|ing)"
    r"|consider(?:s|ed|ing)?|optional(?:ly)?)\b",
    re.IGNORECASE,
)
OPTIONAL_RE = re.compile(r"\boptional(?:ly)?\b", re.IGNORECASE)
REQUIRED_RE = re.compile(r"\b(?:must|includ(?:e|es|ed|ing))\b", re.IGNORECASE)
WORD_RE = re.compile(r"[A-Za-z][\w-]*")
CLAUSE_END_RE = re.compile(r"[,;:.()]")
STOPWORDS = frozenset(
    "a an the or and nor for of to in on at by with from than that which who when where while if as is are be "
    "been being was were it its their this these those more less other others one any some each every all only "
    "also but so not".split()
)

# One kind per bullet: words that suggest the other kind slipped in.
REQUIREMENT_WORDS_RE = re.compile(r"\b(?:never|must|should|keeps?|stays?|so that|instead)\b", re.IGNORECASE)
PERMISSION_WORDS_RE = re.compile(
    r"not a defect|\b(?:is|are) expected\b|\bis fine\b|\bis correct\b|\blegitimate\b|not an imbalance", re.IGNORECASE
)


@dataclass(frozen=True)
class Finding:
    rule: str
    message: str
    line: int | None = None
    severity: str = ERROR


@dataclass
class Bullet:
    line: int  # 1-based line of the "- " marker
    text: str  # the marker line's text
    continuation_lines: list[int] = field(default_factory=list)


@dataclass
class Section:
    heading_line: int  # 1-based
    bullets: list[Bullet]
    stray: list[tuple[int, str]]  # K3 violations: (1-based line, text)


# ---------------------------------------------------------------------------
# Reading the section
# ---------------------------------------------------------------------------


def locate_section(lines: list[str]) -> Section | None:
    """The section as the gate's parser sees it, or None when it has none.

    Mirrors ``parse_characteristics``: the first line the parser's heading
    regex matches opens the section, a repeated heading does not end it, and
    the next ``#``/``##`` heading does.
    """
    start = next((i for i, line in enumerate(lines) if CHARACTERISTICS_HEADING_RE.match(line)), None)
    if start is None:
        return None
    bullets: list[Bullet] = []
    stray: list[tuple[int, str]] = []
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if CHARACTERISTICS_HEADING_RE.match(line):
            continue  # a repeated heading (K1); the parser reads on
        if NEXT_SECTION_RE.match(line):
            break
        if not line.strip() or line.startswith("#"):
            continue  # blank, or a sub-heading (K2)
        if line.startswith("- ") and line[2:].strip():
            bullets.append(Bullet(i + 1, line[2:].strip()))
        elif line[:1].isspace() and bullets:
            bullets[-1].continuation_lines.append(i + 1)
        else:
            stray.append((i + 1, line))
    return Section(start + 1, bullets, stray)


def has_section(text: str) -> bool:
    return locate_section(text.splitlines()) is not None


def _bullet_texts(text: str, section: Section) -> list[tuple[int, str]]:
    """(line, text) per bullet, with the text the gate reads (wrapped lines joined).

    Falls back to the marker lines when the parser and the lint disagree on
    the count (K7 reports that).
    """
    items = parse_characteristics(text)
    if len(items) == len(section.bullets):
        return [(b.line, item) for b, item in zip(section.bullets, items, strict=True)]
    return [(b.line, b.text) for b in section.bullets]


def exact_kind(text: str) -> str | None:
    """The bullet's kind when it opens with an exact prefix and a space, else None."""
    for kind, prefix in PREFIXES.items():
        if text == prefix or text.startswith(prefix + " "):
            return kind
    return None


def _body(text: str) -> str:
    """The bullet text after its kind prefix (the whole text when it has none)."""
    if characteristic_kind(text) is None:
        return text
    return text.split(":", 1)[1].lstrip("*_ ").strip()


def _collapse(text: str) -> str:
    return " ".join(text.casefold().split())


# ---------------------------------------------------------------------------
# Contract (blocking)
# ---------------------------------------------------------------------------


def check_contract(text: str, require_section: bool = False) -> list[Finding]:
    """Parser-contract violations of one spec; an empty list means it passes."""
    findings: list[Finding] = []
    lines = text.splitlines()

    headings = [i + 1 for i, line in enumerate(lines) if line == HEADING]
    for i, line in enumerate(lines):
        if line != HEADING and NEAR_MISS_HEADING_RE.match(line):
            findings.append(Finding("K1", f"write the heading exactly as '{HEADING}' (found '{line.strip()}')", i + 1))
    for number in headings[1:]:
        findings.append(Finding("K1", "the heading appears more than once", number))

    section = locate_section(lines)
    if section is None:
        if require_section:
            findings.append(Finding("K0", f"the spec has no '{HEADING}' section"))
        return findings

    if "\r" in text:
        number = text[: text.index("\r")].count("\n") + 1
        findings.append(Finding("K8", "use LF line endings (found a carriage return)", number))

    for i in range(section.heading_line, len(lines)):
        line = lines[i]
        if line.startswith("#") and not (line == HEADING or NEAR_MISS_HEADING_RE.match(line)):
            findings.append(
                Finding("K2", f"the section must be the last one, with no sub-headings (found '{line.strip()}')", i + 1)
            )

    for number, line in section.stray:
        if line.startswith("- "):
            message = "empty bullet"
        else:
            message = f"only column-0 '- ' bullets and indented continuation lines are allowed (found '{line.strip()}')"
        findings.append(Finding("K3", message, number))

    low, high = CONTRACT_BULLETS
    if not low <= len(section.bullets) <= high:
        findings.append(
            Finding(
                "K4", f"the section needs {low}-{high} bullets (found {len(section.bullets)})", section.heading_line
            )
        )

    parsed = len(parse_characteristics(text))
    if not section.stray and parsed != len(section.bullets):
        findings.append(
            Finding(
                "K7",
                f"the regen gate's parser reads {parsed} bullet(s), the lint {len(section.bullets)}",
                section.heading_line,
            )
        )

    seen: dict[str, int] = {}
    for number, item in _bullet_texts(text, section):
        key = _collapse(item)
        if key in seen:
            findings.append(Finding("K5", f"duplicate of the bullet on line {seen[key]}", number))
        else:
            seen[key] = number

        kind = exact_kind(item)
        if kind is None:
            lenient = characteristic_kind(item)
            if lenient is None:
                message = f"start the bullet with '{SHOWS_PREFIX} ' or '{EXPECTED_PREFIX} '"
            else:
                message = f"write the kind prefix exactly as '{PREFIXES[lenient]} '"
            findings.append(Finding("K6", message, number))
            continue
        rest = item[len(PREFIXES[kind]) :].strip()
        if not rest:
            findings.append(Finding("K6", "the bullet has no text after its kind prefix", number))
        elif SECOND_PREFIX_RE.search(rest):
            findings.append(
                Finding("K6", "the bullet carries a second kind prefix; split it, one kind per bullet", number)
            )

    return findings


# ---------------------------------------------------------------------------
# Style (warnings; hard rules fail under --strict)
# ---------------------------------------------------------------------------


def _section_lines(lines: list[str], name: str) -> list[tuple[int, str]]:
    """(1-based line, text) of the body of the ``## {name}`` section."""
    out: list[tuple[int, str]] = []
    inside = False
    for i, line in enumerate(lines):
        m = OTHER_SECTION_RE.match(line)
        if m:
            inside = m.group("name").casefold() == name.casefold()
            continue
        if inside and line.strip():
            out.append((i + 1, line))
    return out


def _stem(word: str) -> str:
    """Regex for a word with or without a plural s."""
    base = word[:-1] if len(word) > 3 and word.lower().endswith("s") else word
    return re.escape(base) + "s?"


def _phrase_in(phrase: str, line: str) -> bool:
    words = phrase.split()
    pattern = r"\s+".join([re.escape(w) for w in words[:-1]] + [_stem(words[-1])])
    return re.search(r"\b" + pattern + r"\b", line, re.IGNORECASE) is not None


def _phrase_after(text: str, end: int) -> str | None:
    """The first content word after ``end`` (plus the next one when it is a content word too)."""
    clause = CLAUSE_END_RE.split(text[end:], maxsplit=1)[0]
    words: list[str] = WORD_RE.findall(clause)
    while words and words[0].lower() in STOPWORDS:
        words.pop(0)
    if not words:
        return None
    if len(words) > 1 and words[1].lower() not in STOPWORDS:
        return f"{words[0]} {words[1]}"
    return words[0]


def _content_words_after(text: str, end: int, window: int = 3) -> list[str]:
    clause = CLAUSE_END_RE.split(text[end:], maxsplit=1)[0]
    words: list[str] = WORD_RE.findall(clause)[:window]
    return [w for w in words if w.lower() not in STOPWORDS and len(w) > 2]


def _contradictions(text: str, lines: list[str], bullets: list[tuple[int, str]]) -> list[Finding]:
    """Heuristic: a section statement that may contradict a Notes or Data line."""
    notes = _section_lines(lines, "Notes")
    notes_and_data = notes + _section_lines(lines, "Data")
    findings: list[Finding] = []
    for number, item in bullets:
        body = _body(item)
        for m in NEGATION_RE.finditer(body):
            phrase = _phrase_after(body, m.end())
            if phrase is None:
                continue
            for other_number, line in notes_and_data:
                if TRIGGER_RE.search(line) and _phrase_in(phrase, line):
                    findings.append(
                        Finding(
                            "W5",
                            f"'{m.group(0)} {phrase}' may contradict line {other_number}: '{line.strip()}'",
                            number,
                            WARNING,
                        )
                    )
        # "optional" in the section against "must"/"include" in Notes, and the reverse.
        for source_re, other_re in ((OPTIONAL_RE, REQUIRED_RE), (REQUIRED_RE, OPTIONAL_RE)):
            for m in source_re.finditer(body):
                words = _content_words_after(body, m.end())
                for other_number, line in notes:
                    if other_re.search(line) and any(_phrase_in(w, line) for w in words):
                        findings.append(
                            Finding(
                                "W5",
                                f"'{m.group(0)} {' '.join(words)}' may contradict line {other_number}: '{line.strip()}'",
                                number,
                                WARNING,
                            )
                        )
    return findings


def check_style(text: str, spec_id: str, strict: bool = False) -> list[Finding]:
    """House-style findings for one spec. Hard rules are errors only when ``strict``."""
    lines = text.splitlines()
    section = locate_section(lines)
    if section is None:
        return []
    hard = ERROR if strict else WARNING
    findings: list[Finding] = []
    bullets = _bullet_texts(text, section)

    low, high = STYLE_BULLETS
    if not low <= len(bullets) <= high:
        findings.append(Finding("S1", f"write {low}-{high} bullets (found {len(bullets)})", section.heading_line, hard))

    for bullet in section.bullets:
        if bullet.continuation_lines:
            findings.append(
                Finding(
                    "S2", "write each bullet on one line (no continuation lines)", bullet.continuation_lines[0], hard
                )
            )

    if not text.endswith("\n") or text.endswith("\n\n"):
        findings.append(Finding("S3", "end the file with exactly one newline", len(lines) or None, hard))

    kinds = [characteristic_kind(item) for _, item in bullets]
    if KIND_SHOWS not in kinds:
        findings.append(Finding("S4", f"add at least one '{SHOWS_PREFIX}' bullet", section.heading_line, hard))
    if KIND_EXPECTED not in kinds:
        findings.append(Finding("S4", f"add at least one '{EXPECTED_PREFIX}' bullet", section.heading_line, hard))

    rest_of_spec = "\n".join(lines[: section.heading_line - 1])
    spec_numerals = set(NUMERAL_RE.findall(rest_of_spec))

    for number, item in bullets:
        body = _body(item)
        generic = GENERIC_RE.search(GENERIC_ALLOW_RE.sub(" ", body))
        if generic:
            findings.append(Finding("S5", f"generic ideal '{generic.group(0)}': describe this plot type", number, hard))
        for pattern, what in ((UNIT_RE, "a unit"), (COMPARATOR_RE, "a comparator")):
            m = pattern.search(body)
            if m:
                findings.append(
                    Finding("S6", f"numeric threshold '{m.group(0)}' ({what}): no thresholds", number, hard)
                )
        m = VISUAL_VALUE_RE.search(body)
        if m:
            findings.append(
                Finding("S7", f"styling value '{m.group(0)}': describe the effect, not the value", number, hard)
            )
        m = LIBRARY_RE.search(body) or CALL_RE.search(body)
        if m:
            findings.append(
                Finding("S8", f"library or API name '{m.group(0)}': the section is library-agnostic", number, hard)
            )
        m = HEX_RE.search(body)
        if m:
            findings.append(
                Finding("S9", f"hex color '{m.group(0)}': the palette lives in the style guide", number, hard)
            )
        if len(item) > HARD_MAX_CHARS:
            findings.append(Finding("S10", f"bullet has {len(item)} characters (max {HARD_MAX_CHARS})", number, hard))
        elif len(item) > SOFT_MAX_CHARS:
            findings.append(
                Finding("W3", f"bullet has {len(item)} characters (aim for {SOFT_MAX_CHARS} or fewer)", number, WARNING)
            )

        unknown = sorted({n for n in NUMERAL_RE.findall(body) if n not in spec_numerals})
        if unknown:
            findings.append(
                Finding("W1", f"numeral(s) {', '.join(unknown)} appear nowhere else in the spec", number, WARNING)
            )
        if "`" in body:
            findings.append(Finding("W2", "backticks in the section", number, WARNING))

        kind = characteristic_kind(item)
        if kind == KIND_EXPECTED:
            m = REQUIREMENT_WORDS_RE.search(body)
            if m:
                findings.append(
                    Finding(
                        "W6",
                        f"'{EXPECTED_PREFIX}' bullet may carry a requirement ('{m.group(0)}'): "
                        f"put how a good version handles it in its own '{SHOWS_PREFIX}' bullet",
                        number,
                        WARNING,
                    )
                )
        elif kind == KIND_SHOWS:
            m = PERMISSION_WORDS_RE.search(body)
            if m:
                findings.append(
                    Finding(
                        "W6",
                        f"'{SHOWS_PREFIX}' bullet may carry a permission ('{m.group(0)}'): "
                        f"move it to an '{EXPECTED_PREFIX}' bullet",
                        number,
                        WARNING,
                    )
                )

    if spec_id.endswith("-basic") and not any(
        characteristic_kind(item) == KIND_SHOWS and "basic variant" in item.casefold() for _, item in bullets
    ):
        findings.append(
            Finding(
                "W4",
                f"a -basic spec needs an '{SHOWS_PREFIX}' bullet naming the basic variant's scope ('the basic variant's …')",
                section.heading_line,
                WARNING,
            )
        )

    findings += _contradictions(text, lines, bullets)
    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _escape(message: str) -> str:
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def annotation(path: str, finding: Finding) -> str:
    """One GitHub Actions workflow-command line for a finding."""
    location = f"file={path}" + (f",line={finding.line}" if finding.line else "")
    return f"::{finding.severity} {location},title={finding.rule}::{_escape(finding.message)}"


def _read(path: str) -> str | Finding:
    # Decode the raw bytes: read_text() translates CRLF to LF, which would hide
    # exactly the line endings K8 exists to catch.
    try:
        return Path(path).read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return Finding("K0", f"cannot read the file: {exc}")


def _collect(files: list[str], all_specs: bool) -> list[str]:
    paths = set(files)
    if all_specs:
        paths |= {path.as_posix() for path in Path("plots").glob("*/specification.md")}
    return sorted(paths)


def cmd_contract(args: argparse.Namespace) -> int:
    paths = _collect(args.files, args.all)
    if not paths:
        print("spec_characteristics_lint contract: no files (pass FILE... or --all)", file=sys.stderr)
        return 2
    errors = with_section = 0
    for path in paths:
        text = _read(path)
        if isinstance(text, Finding):
            findings = [text]
        else:
            findings = check_contract(text, args.require_section)
            with_section += has_section(text)
        for finding in findings:
            print(annotation(path, finding))
        errors += len(findings)
    print(
        f"spec_characteristics_lint contract: {len(paths)} file(s), {with_section} with the section, {errors} error(s)"
    )
    return 1 if errors else 0


def cmd_style(args: argparse.Namespace) -> int:
    errors = warnings = with_section = 0
    for path in args.files:
        text = _read(path)
        if isinstance(text, Finding):
            findings = [text]
        else:
            with_section += has_section(text)
            findings = check_style(text, Path(path).parent.name, args.strict)
        for finding in findings:
            print(annotation(path, finding))
            if finding.severity == ERROR:
                errors += 1
            else:
                warnings += 1
    print(
        f"spec_characteristics_lint style: {len(args.files)} file(s), {with_section} with the section, "
        f"{warnings} warning(s), {errors} error(s)"
    )
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    contract = sub.add_parser("contract", help="Parser contract of the section (blocking)")
    contract.add_argument("--all", action="store_true", help="check every plots/*/specification.md")
    contract.add_argument("--require-section", action="store_true", help="fail a spec without the section")
    contract.add_argument("files", nargs="*", metavar="FILE")
    contract.set_defaults(func=cmd_contract)

    style = sub.add_parser("style", help="House style of the section (warnings)")
    style.add_argument("--strict", action="store_true", help="hard rules fail (exit 1)")
    style.add_argument("files", nargs="+", metavar="FILE")
    style.set_defaults(func=cmd_style)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
