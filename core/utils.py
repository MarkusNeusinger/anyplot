"""Utility functions for code processing."""

import re
from difflib import SequenceMatcher


def line_map(original: str, rewritten: str) -> dict[int, int]:
    """Each 1-based line of `rewritten` mapped to a line of `original`.

    `rewritten` is `original` after a tool changed parts of it: the smoke run replaces the
    Data block and its column constants, the agent chat's normaliser drops the header and
    rewrites the save. A message about a line of the rewritten text is only useful to whoever
    edits the original. A line that has no counterpart maps to the first original line of
    the region it replaced.
    """
    rewritten_lines, original_lines = rewritten.splitlines(), original.splitlines()
    mapping: dict[int, int] = {}
    if not original_lines:
        return mapping
    matcher = SequenceMatcher(None, rewritten_lines, original_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        for i in range(i1, i2):
            if tag == "equal":
                j = j1 + (i - i1)
            elif j2 > j1:
                j = j1 + min(i - i1, j2 - j1 - 1)
            else:
                j = min(j1, len(original_lines) - 1)
            mapping[i + 1] = j + 1
    return mapping


def strip_noqa_comments(code: str | None) -> str | None:
    """Remove # noqa: comments from code for cleaner user display.

    Note:
        Uses regex-based matching, which will also remove noqa patterns inside
        string literals. This is acceptable for plot implementation code where
        noqa comments in strings are extremely rare.
    """
    if not code:
        return code
    return re.sub(r"\s*# noqa:[^\n]*", "", code)
