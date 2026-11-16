"""A Markdown file's headings as the anchors GitHub gives them.

A link into a Markdown file names a heading by its anchor, and a renamed heading leaves the link at the file's top
without an error. The tests that check such links read the headings here, so every one of them resolves an anchor
the same way.
"""

from __future__ import annotations

import re


_HEADING = re.compile(r"^#+\s+(.*)$", re.M)
_FENCE = re.compile(r"^```.*?^```", re.M | re.S)


def headings(text: str) -> set[str]:
    """The page's real headings, as GitHub anchors.

    Fenced blocks are stripped first. The repository's Markdown files are full
    of shell snippets, and a `# Install uv` comment inside one is not a
    heading — counting it would let a dead link pass by matching a line GitHub
    renders as code.
    """
    return {anchor(h) for h in _HEADING.findall(_FENCE.sub("", text))}


def anchor(heading: str) -> str:
    """GitHub's slug for a heading: lowercased, punctuation dropped, spaces to
    hyphens. Enough of the algorithm for the headings these files actually have.
    """
    slug = heading.strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    return re.sub(r"\s", "-", slug)
