#!/usr/bin/env python3
"""Write the ``//`` header of a JavaScript implementation (impl-review).

impl-review's "Update metadata and implementation header" step stores the
review's score in a four-line comment header at the top of every
implementation file. For JavaScript the header is::

    // anyplot.ai
    // {spec_id}: {title}
    // Library: {library} {version} | JavaScript {node version}
    // Quality: {score}/100 | Created: {date}

A JavaScript file can also carry ``//#`` directive lines that the render
harness reads (``//# anyplot-orientation: square``). They are not header
lines and always survive the rewrite. ``replace_js_header`` writes one shape
whatever the file looked like before:

1. the new header on line 1, as in the Python, R and Julia headers;
2. directly below it, every directive that sat above the old header, in order;
3. the rest of the file as it was, minus any further ``// anyplot.ai`` header
   block among the leading lines.

A *header block* is a run of ``//`` comment lines that ends with its first
``// Quality:`` line, or the whole run when it has none. Comment lines after
the ``Quality:`` line are code comments and stay.

The leading lines are blank lines, directive lines and header blocks up to
the first other line. A ``// anyplot.ai`` block there below the header is a
stale copy: until 2026-10 the writer stopped at a directive on line 1,
prepended the new header above it and left the old header below the
directive, with its old score and date. It is dropped together with the
blank lines directly above it, so a file comes out with exactly one header
however often it is rewritten. Directives and blank lines below the header
keep their place.

``impl-review.yml`` imports this file from the copy its "Checkout PR code"
step saves at the workflow's own ref, so a PR branched off an older ``main``
gets the current writer. Stdlib only.
"""

from __future__ import annotations

import re


HEADER_START_RE = re.compile(r"//[ \t]*anyplot\.ai[ \t]*")
QUALITY_LINE_RE = re.compile(r"//[ \t]*Quality:.*")


def _body(line: str) -> str:
    return line.rstrip("\r\n")


def is_directive(line: str) -> bool:
    """A ``//#`` line: an anyplot directive the render harness reads."""
    return line.startswith("//#")


def _is_comment(line: str) -> bool:
    return line.startswith("//") and not is_directive(line)


def _is_blank(line: str) -> bool:
    return not line.strip()


def _header_block_end(lines: list[str], start: int) -> int:
    """Index after the header block at ``start``; ``start`` without one.

    The block runs over ``//`` comment lines to its first ``// Quality:``
    line, or over the whole run when the run has no such line.
    """
    end = start
    while end < len(lines) and _is_comment(lines[end]):
        end += 1
        if QUALITY_LINE_RE.fullmatch(_body(lines[end - 1])):
            break
    return end


def replace_js_header(content: str, new_header: str) -> str:
    """Return ``content`` with ``new_header`` as its only header block.

    ``new_header`` is the four header lines without a final newline. See the
    module docstring for the shape; a file without a header gets the header
    prepended, and running the function twice gives the same text.
    """
    lines = content.splitlines(keepends=True)
    i = 0
    above: list[str] = []
    while i < len(lines) and is_directive(lines[i]):
        above.append(lines[i])
        i += 1
    i = _header_block_end(lines, i)

    kept: list[str] = []
    blanks: list[str] = []
    while i < len(lines):
        line = lines[i]
        if _is_blank(line):
            blanks.append(line)
            i += 1
        elif is_directive(line):
            kept += blanks
            blanks = []
            kept.append(line)
            i += 1
        elif HEADER_START_RE.fullmatch(_body(line)):
            blanks = []
            i = _header_block_end(lines, i)
        else:
            break
    return new_header + "\n" + "".join(above) + "".join(kept) + "".join(blanks) + "".join(lines[i:])
