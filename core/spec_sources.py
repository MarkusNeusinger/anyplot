"""The `sources` block of a spec's `specification.yaml`: where its idea came from, and the literature its values follow.

A spec names two relations, and only these two:

- `inspired_by`: a work that gave the idea for the plot.
- `references`: literature that the spec's domain values follow.

Code is never adopted from elsewhere, so there is no relation for it: every implementation in the catalogue is
written for it and stays under the MIT License. `data` says where the spec's example data comes from: `invented`,
`computed` from a method, or `real` measurements.

    sources:
      data: computed
      inspired_by:
        - title: "An example project"
          url: "https://example.org/project"
      references:
        - title: "A paper whose values the spec follows"
          url: "https://doi.org/10.1000/example.1"
          doi: "10.1000/example.1"

Every key is optional, and a missing or empty block means that no source is known. An entry has a `title` and an
http or https `url`, and optionally a `doi` and an `isbn`. Nothing else is allowed, in the block or in an entry, and a
key that is present holds a value: a key without one is left out, never written as `null`.

`sources_problems` is the check. It takes the parsed YAML and names every problem it finds; the unit test over every
spec file and the database sync (`automation/scripts/sync_to_postgres.py`) use it, and so can a later check of the
spec-create workflow. `normalized_sources` turns a block that passed into the JSON the database stores. Standard
library only, so a script on the workflow runner's system Python can use it too.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit


DATA_KINDS = ("invented", "computed", "real")
RELATIONS = ("inspired_by", "references")
BLOCK_KEYS = ("data", *RELATIONS)
ENTRY_REQUIRED = ("title", "url")
ENTRY_OPTIONAL = ("doi", "isbn")
ENTRY_KEYS = (*ENTRY_REQUIRED, *ENTRY_OPTIONAL)

# Crossref's recommended pattern, which matches all but a sliver of the DOIs in use. Its characters need no escaping in
# the path of `https://doi.org/<doi>`, so every writer of that link can use the DOI as it stands.
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
# An ISBN-10 (nine digits and a check digit or X) or an ISBN-13, with hyphens or spaces between the groups.
ISBN_PATTERN = re.compile(r"\d{9}[\dX]|\d{13}")


def _is_web_address(value: str) -> bool:
    if any(char.isspace() for char in value):
        return False
    try:
        parts = urlsplit(value)
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.hostname)


def _entry_problems(where: str, entry: object) -> list[str]:
    if not isinstance(entry, Mapping):
        return [f"{where}: an entry is a mapping with `title` and `url`, found {type(entry).__name__}"]
    problems = [f"{where}: unknown key {key!r}" for key in entry if key not in ENTRY_KEYS]
    for key in ENTRY_KEYS:
        if key not in entry:
            if key in ENTRY_REQUIRED:
                problems.append(f"{where}.{key}: missing")
            continue
        value = entry[key]
        if not isinstance(value, str):
            hint = " (quote it in the YAML)" if isinstance(value, int | float) else ""
            problems.append(f"{where}.{key}: a string{hint}, found {type(value).__name__}")
        elif not value.strip():
            problems.append(f"{where}.{key}: empty")
        elif key == "url" and not _is_web_address(value):
            problems.append(f"{where}.url: not an http or https address: {value!r}")
        elif key == "doi" and not DOI_PATTERN.fullmatch(value):
            problems.append(f"{where}.doi: not a DOI of the form 10.<prefix>/<suffix> (no resolver URL): {value!r}")
        elif key == "isbn" and not ISBN_PATTERN.fullmatch(re.sub(r"[- ]", "", value)):
            problems.append(f"{where}.isbn: not an ISBN-10 or ISBN-13: {value!r}")
    return problems


def sources_problems(block: object) -> list[str]:
    """Every problem of a parsed `sources` block, one line each; empty for a sound block or a missing one (`None`)."""
    if block is None:
        return []
    if not isinstance(block, Mapping):
        return [f"sources: a mapping of {', '.join(BLOCK_KEYS)}, found {type(block).__name__}"]
    problems = [f"sources: unknown key {key!r}" for key in block if key not in BLOCK_KEYS]
    if "data" in block and block["data"] not in DATA_KINDS:
        problems.append(f"sources.data: one of {', '.join(DATA_KINDS)}, found {block['data']!r}")
    for relation in RELATIONS:
        if relation not in block:
            continue
        entries = block[relation]
        if not isinstance(entries, list):
            problems.append(f"sources.{relation}: a list of entries, found {type(entries).__name__}")
            continue
        for index, entry in enumerate(entries):
            problems.extend(_entry_problems(f"sources.{relation}[{index}]", entry))
    return problems


def _normalized_entry(entry: Mapping[str, str]) -> dict[str, str]:
    normalized = {"title": " ".join(entry["title"].split()), "url": entry["url"]}
    for key in ENTRY_OPTIONAL:
        if key in entry:
            normalized[key] = entry[key].strip()
    return normalized


def normalized_sources(block: object) -> dict[str, Any] | None:
    """The JSON the database stores for a sound block: its keys in a fixed order, empty lists left out.

    `None` when the block is missing or holds nothing. Raises `ValueError` for a block with problems, so that
    a caller cannot store one by mistake; check it with `sources_problems` first.
    """
    problems = sources_problems(block)
    if problems:
        raise ValueError("; ".join(problems))
    if not isinstance(block, Mapping):
        return None
    normalized: dict[str, Any] = {}
    if "data" in block:
        normalized["data"] = block["data"]
    for relation in RELATIONS:
        entries = [_normalized_entry(entry) for entry in block.get(relation, [])]
        if entries:
            normalized[relation] = entries
    return normalized or None
