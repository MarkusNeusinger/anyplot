"""Utility functions for code processing."""

import re
from difflib import SequenceMatcher


def line_map(original: str, rewritten: str) -> dict[int, int]:
    """Each 1-based line of `rewritten` mapped to a line of `original`.

    `rewritten` is `original` after a tool changed parts of it: the smoke run replaces the
    Data block and its column constants, the agent chat's normaliser drops the header,
    rewrites the save and hoists the imports out of a guard. A message about a line of the
    rewritten text is only useful to whoever edits the original.

    Unchanged lines map to themselves. Inside a region the tool replaced, a line whose text
    only moved or changed its indentation (an import hoisted out of a `try:` or `if` guard)
    maps to that line of the region, in order; any other line maps by its position in the
    region. A line the tool inserted maps to the original line after it.
    """
    rewritten_lines, original_lines = rewritten.splitlines(), original.splitlines()
    mapping: dict[int, int] = {}
    if not original_lines:
        return mapping
    matcher = SequenceMatcher(None, rewritten_lines, original_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                mapping[i + 1] = j1 + (i - i1) + 1
        elif j2 > j1:
            cursor = j1
            for i in range(i1, i2):
                text = rewritten_lines[i].strip()
                same = next((j for j in range(cursor, j2) if text and original_lines[j].strip() == text), None)
                if same is not None:
                    cursor = same + 1
                mapping[i + 1] = (same if same is not None else j1 + min(i - i1, j2 - j1 - 1)) + 1
        else:
            for i in range(i1, i2):
                mapping[i + 1] = min(j1, len(original_lines) - 1) + 1
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
