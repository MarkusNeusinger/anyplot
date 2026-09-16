#!/usr/bin/env python3
"""
Generate ``app/src/styles/fonts.css`` from the MonoLisa webfont builder output.

The MonoLisa order page (https://www.monolisa.dev/orders/<family>/web) builds a
zip per family: one woff2 per Unicode range and style
(``woff2/<n>-MonoLisaCode-normal.woff2`` …) plus a ``monolisa.css`` whose
``@font-face`` blocks carry the ``unicode-range`` for each file. The woff2 files
are uploaded to GCS (never committed: proprietary, © FaceType Foundry); this
script turns the builder CSS into the committed stylesheet, so a font update is
a re-run and not 700 hand-edited lines.

Usage::

    uv run python automation/scripts/monolisa_fonts_css.py \\
        --code-css <unzipped code zip>/monolisa.css \\
        --text-css <unzipped text zip>/monolisa.css \\
        --gcs-prefix https://storage.googleapis.com/anyplot-static/fonts/v3 \\
        --version 3.000 \\
        --out app/src/styles/fonts.css

Policy baked in (see docs/reference/style-guide.md §5.1):

- Family names in CSS are ``'MonoLisa Code'`` and ``'MonoLisa Text'``.
- The Basic Latin pair of each family uses ``font-display: swap``; every other
  subset uses ``optional`` (fine to miss on a slow first paint).
- ``font-weight: 100 900`` — the files carry 1–1000 but nothing on the site
  asks for more.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


FONT_FACE_RE = re.compile(r"@font-face\s*\{(?P<body>.*?)\}", re.DOTALL)
SRC_RE = re.compile(r"url\((?P<url>[^)]+)\)")
STYLE_RE = re.compile(r"font-style:\s*(?P<style>\w+)")
RANGE_RE = re.compile(r"unicode-range:\s*(?P<range>[^;]+);")

BASIC_LATIN = "U+0020-007F"

# Human-readable names for the Unicode ranges the builder offers (its own CSS
# carries only the codepoints). Unknown ranges fall back to the raw range.
RANGE_NAMES: dict[str, str] = {
    "U+0020-007F": "Basic Latin",
    "U+0080-00FF": "Latin-1 Supplement",
    "U+0100-017F": "Latin Extended-A",
    "U+1E00-1EFF": "Latin Extended Additional",
    "U+0180-024F": "Latin Extended-B",
    "U+2C60-2C7F": "Latin Extended-C",
    "U+A720-A7FF": "Latin Extended-D",
    "U+0250-02AF": "IPA Extensions",
    "U+FB00-FB4F": "Alphabetic Presentation Forms",
    "U+0400-04FF": "Cyrillic",
    "U+0500-052F": "Cyrillic Supplement",
    "U+0370-03FF": "Greek and Coptic",
    "U+0530-058F": "Armenian",
    "U+0590-05FF": "Hebrew",
    "U+2000-206F": "General Punctuation",
    "U+2150-218F": "Number Forms",
    "U+2070-209F": "Superscripts and Subscripts",
    "U+3000-303F": "CJK Symbols and Punctuation",
    "U+0980-09FF": "Bengali",
    "U+2800-28FF": "Braille Patterns",
    "U+1780-17FF": "Khmer",
    "U+0E00-0E7F": "Thai",
    "U+2600-26FF": "Miscellaneous Symbols",
    "U+2700-27BF": "Dingbats",
    "U+2300-23FF": "Miscellaneous Technical",
    "U+2100-214F": "Letterlike Symbols",
    "U+2190-21FF": "Arrows",
    "U+2B00-2BFF": "Miscellaneous Symbols and Arrows",
    "U+20A0-20CF": "Currency Symbols",
    "U+2200-22FF": "Mathematical Operators",
    "U+2580-259F": "Block Elements",
    "U+25A0-25FF": "Geometric Shapes",
    "U+2500-257F": "Box Drawing",
    "U+0300-036F": "Combining Diacritical Marks",
    "U+02B0-02FF": "Spacing Modifier Letters",
    "U+E000-F8FF": "Private Use Area (Powerline, Nerd Fonts)",
}


@dataclass(frozen=True)
class Subset:
    """One builder ``@font-face`` block: a file, its style and its Unicode range."""

    filename: str
    style: str  # "normal" | "italic"
    unicode_range: str


def parse_builder_css(css: str) -> list[Subset]:
    """Extract the (file, style, range) triples from a builder ``monolisa.css``."""
    subsets: list[Subset] = []
    for match in FONT_FACE_RE.finditer(css):
        body = match.group("body")
        src = SRC_RE.search(body)
        style = STYLE_RE.search(body)
        rng = RANGE_RE.search(body)
        if not (src and style and rng):
            raise ValueError(f"Unparseable @font-face block:\n{body}")
        filename = src.group("url").strip("'\"").rsplit("/", 1)[-1]
        subsets.append(Subset(filename, style.group("style"), rng.group("range").strip()))
    if not subsets:
        raise ValueError("No @font-face blocks found — is this the builder's monolisa.css?")
    return subsets


def render_family(
    family: str, folder: str, subsets: list[Subset], gcs_prefix: str, swap_comment: dict[str, str]
) -> str:
    """Render every subset of one family as ``@font-face`` blocks, grouped by range."""
    out: list[str] = []
    seen_ranges: list[str] = []
    for s in subsets:
        if s.unicode_range not in seen_ranges:
            seen_ranges.append(s.unicode_range)
            out.append(f"\n/* {RANGE_NAMES.get(s.unicode_range, s.unicode_range)} */")
        display = "swap" if s.unicode_range == BASIC_LATIN else "optional"
        out.append("@font-face {")
        out.append(f"  font-family: '{family}';")
        out.append(f"  src: url('{gcs_prefix}/{folder}/{s.filename}')")
        out.append("    format('woff2');")
        out.append("  font-weight: 100 900;")
        out.append(f"  font-style: {s.style};")
        if display == "swap" and s.style in swap_comment:
            out.append(f"  /* {swap_comment[s.style]} */")
        out.append(f"  font-display: {display};")
        out.append(f"  unicode-range: {s.unicode_range};")
        out.append("}")
    return "\n".join(out)


HEADER = """/*!
 * MonoLisa {version} — Code + Text webfonts ({n_code} + {n_text} Unicode subsets)
 * Hosted on GCS: {gcs_prefix}/{{code,text}}/
 * CORS restricted to anyplot.ai
 *
 * GENERATED by automation/scripts/monolisa_fonts_css.py from the order page's
 * builder CSS — edit the script, not this file.
 *
 * © 2026 FaceType Foundry. All Rights Reserved.
 * License: https://www.monolisa.dev/license
 */

/* ==========================================================================
   Fallback Fonts (prevent CLS while web fonts load)
   ========================================================================== */

@font-face {{
  font-family: 'MonoLisa Fallback';
  src: local('Consolas'), local('Menlo'), local('Monaco'), local('DejaVu Sans Mono');
  size-adjust: 106.5%;
  ascent-override: 105%;
  descent-override: 25%;
  line-gap-override: 0%;
}}
"""

CODE_SECTION = """
/* ==========================================================================
   MonoLisa Code — the monospaced family, used everywhere (style-guide §5.1).
   Variable: wght 100–900 (file carries 1–1000) + GRAD −50…50.
   Script italic is `ss01` (v3; it was `ss02` in v2). Coding ligatures are
   `dlig` (off by default, enabled on code surfaces in tokens.css).
   The browser only downloads the subsets it needs for visible glyphs.
   ========================================================================== */
"""

TEXT_SECTION = """
/* ==========================================================================
   MonoLisa Text — the proportional sibling, registered for experiments
   (`--text` in tokens.css). Nothing is fetched until a rule uses the family.
   ========================================================================== */
"""

SWAP_COMMENTS_CODE = {
    "normal": (
        "`swap` (not `optional`) — the Basic Latin normal carries branded glyphs\n"
        "     whose shape differs from the fallback (notably the logo dot `.`, which\n"
        "     is a bold square block in MonoLisa vs. a round dot in Consolas/Menlo).\n"
        "     `optional` locks in the fallback for the session on slow first loads;\n"
        "     `swap` accepts a brief FOUT but guarantees MonoLisa renders eventually."
    ),
    "italic": (
        "`swap` for the same reason — the Basic Latin italic carries the editorial\n"
        "     script emphasis (`<em>` + ss01)."
    ),
}


def build(code_css: str, text_css: str, gcs_prefix: str, version: str) -> str:
    """Assemble the full stylesheet text."""
    code = parse_builder_css(code_css)
    text = parse_builder_css(text_css)
    parts = [
        HEADER.format(version=version, n_code=len(code), n_text=len(text), gcs_prefix=gcs_prefix),
        CODE_SECTION,
        render_family("MonoLisa Code", "code", code, gcs_prefix, SWAP_COMMENTS_CODE),
        "",
        TEXT_SECTION,
        render_family("MonoLisa Text", "text", text, gcs_prefix, {}),
        "",
    ]
    # Collapse the seams between the templates to one blank line (prettier-clean).
    return re.sub(r"\n{3,}", "\n\n", "\n".join(parts))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--code-css", type=Path, required=True, help="builder monolisa.css of the Code zip")
    parser.add_argument("--text-css", type=Path, required=True, help="builder monolisa.css of the Text zip")
    parser.add_argument("--gcs-prefix", required=True, help="public URL prefix holding code/ and text/")
    parser.add_argument("--version", required=True, help="font version, e.g. 3.000")
    parser.add_argument("--out", type=Path, default=Path("app/src/styles/fonts.css"))
    args = parser.parse_args()

    css = build(args.code_css.read_text(), args.text_css.read_text(), args.gcs_prefix.rstrip("/"), args.version)
    args.out.write_text(css)
    print(f"wrote {args.out} ({css.count('@font-face')} @font-face blocks)")


if __name__ == "__main__":
    main()
