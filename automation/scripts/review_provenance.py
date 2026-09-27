#!/usr/bin/env python3
"""Review provenance: which rules and which model produced a review.

Standard library only. ``impl-review.yml`` runs it from the copy it takes at
its own ref (``$RUNNER_TEMP/regen-tools/``); the review retest harness imports
it. Two facts are recorded next to every review:

- ``criteria_version`` -- the git blob ids of the files the reviewer scores
  against, as ``qc-<10 hex>.aqr-<10 hex>.sg-<10 hex>[.lib-<10 hex>]``:
  ``prompts/quality-criteria.md``, ``prompts/workflow-prompts/ai-quality-review.md``,
  ``prompts/default-style-guide.md`` and ``prompts/library/<library>.md``. A git
  blob id is ``sha1(b"blob <size>\\0" + content)``, so each part can be looked up
  with ``git log --all --find-object=<id>`` and compared on its own. The
  ``prompts/`` tree id (``prompts_tree``) is the catch-all for every other
  prompt file and goes into records only.
- the resolved model -- the ``model`` of the first ``system``/``init`` message
  in the claude-code-action execution file (for example ``claude-sonnet-5``).
  Only that message counts: helper sessions in the same file name other
  models (a ``claude-haiku-…`` sub-agent, for example).

CLI (both write ``key=value`` lines to ``$GITHUB_OUTPUT`` when it is set)::

    review_provenance.py criteria-version --root . [--library matplotlib]
    review_provenance.py model --execution-file FILE --fallback claude-sonnet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any


CRITERIA_FILES: tuple[tuple[str, str], ...] = (
    ("qc", "prompts/quality-criteria.md"),
    ("aqr", "prompts/workflow-prompts/ai-quality-review.md"),
    ("sg", "prompts/default-style-guide.md"),
)
LIBRARY_PROMPT = "prompts/library/{library}.md"
SHORT = 10
MISSING = "missing"

# What a model id may look like before it is written to outputs, metadata and
# records. Anything else falls back to the alias.
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/\[\]-]{0,99}$")
QUOTA_RE = re.compile(
    r"usage limit|rate[ _-]?limit|quota|too many requests|\b429\b|overloaded|credit balance", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Rules version
# ---------------------------------------------------------------------------


def git_blob_id(content: bytes) -> str:
    """The id git gives a file with this content (``git hash-object``)."""
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def _part(label: str, path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return f"{label}-{MISSING}"
    return f"{label}-{git_blob_id(data)[:SHORT]}"


def criteria_version(root: Path, library: str | None = None) -> str:
    """``qc-….aqr-….sg-…`` plus ``.lib-…`` when a library is given."""
    parts = [_part(label, root / rel) for label, rel in CRITERIA_FILES]
    if library:
        parts.append(_part("lib", root / LIBRARY_PROMPT.format(library=library)))
    return ".".join(parts)


def parse_criteria_version(value: str | None) -> dict[str, str]:
    """``{"qc": "<10 hex>", ...}`` from a criteria version; unknown shapes give ``{}``."""
    parts: dict[str, str] = {}
    for chunk in (value or "").split("."):
        label, sep, digest = chunk.partition("-")
        if sep and label and digest:
            parts[label] = digest
    return parts


def same_rules(a: str | None, b: str | None, components: tuple[str, ...] = ("qc", "aqr")) -> bool:
    """Whether two criteria versions agree on every named component (all present)."""
    pa, pb = parse_criteria_version(a), parse_criteria_version(b)
    return all(pa.get(c) and pb.get(c) and pa[c] == pb[c] and pa[c] != MISSING for c in components)


def tree_id(path: Path) -> str | None:
    """Git tree id of a directory as it is on disk, or ``None`` when it holds no file.

    For a clean checkout this equals ``git rev-parse <ref>:<dir>``. It is
    computed from the files rather than asked of git because the reviewer
    reads the working tree, which the workflows overlay without committing.
    """
    entries: list[tuple[bytes, bytes, str]] = []
    try:
        children = list(path.iterdir())
    except OSError:
        return None
    for child in children:
        if child.name == ".git":
            continue
        name = os.fsencode(child.name)
        if child.is_symlink():
            entries.append((name, b"120000", git_blob_id(os.fsencode(os.readlink(child)))))
        elif child.is_dir():
            sub = tree_id(child)
            if sub is not None:  # git does not track empty directories
                entries.append((name, b"40000", sub))
        elif child.is_file():
            executable = child.stat().st_mode & stat.S_IXUSR
            entries.append((name, b"100755" if executable else b"100644", git_blob_id(child.read_bytes())))
    if not entries:
        return None
    # Git orders tree entries by name, comparing a directory as "<name>/".
    entries.sort(key=lambda e: e[0] + (b"/" if e[1] == b"40000" else b""))
    body = b"".join(mode + b" " + name + b"\0" + bytes.fromhex(sha) for name, mode, sha in entries)
    return hashlib.sha1(b"tree %d\0" % len(body) + body).hexdigest()


# ---------------------------------------------------------------------------
# Execution file (claude-code-action output)
# ---------------------------------------------------------------------------


def load_messages(path: Path) -> list[dict[str, Any]]:
    """Messages of an execution file: a JSON array, ``{"messages": [...]}`` or JSONL."""
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except ValueError:
        messages = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict):
                messages.append(obj)
        return messages
    if isinstance(data, dict):
        inner = data.get("messages")
        data = inner if isinstance(inner, list) else [data]
    if not isinstance(data, list):
        return []
    return [m for m in data if isinstance(m, dict)]


def _messages_or_empty(path: str | Path | None) -> list[dict[str, Any]]:
    if not path or not str(path).strip():
        return []
    try:
        return load_messages(Path(path))
    except (OSError, UnicodeDecodeError):
        return []


def model_from_messages(messages: list[dict[str, Any]]) -> str | None:
    """``model`` of the first ``system``/``init`` message, when it is a plausible id."""
    for message in messages:
        if message.get("type") == "system" and message.get("subtype") == "init":
            model = message.get("model")
            if isinstance(model, str) and MODEL_ID_RE.fullmatch(model.strip()):
                return model.strip()
            return None  # the first init message decides
    return None


def resolved_model(execution_file: str | Path | None, fallback: str) -> str:
    """The model that ran the session, or ``fallback`` when the file cannot tell."""
    return model_from_messages(_messages_or_empty(execution_file)) or fallback


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def execution_summary(execution_file: str | Path | None, fallback_model: str) -> dict[str, Any]:
    """Model, cost, turns, duration and error class of a session — never its transcript.

    ``error_class`` is ``""`` for a successful session, ``quota`` when the
    result names a usage or rate limit, ``other`` for any other error result,
    and ``no_result`` when the file holds no result message (a crash, a
    timeout, or no file at all).
    """
    messages = _messages_or_empty(execution_file)
    result = next((m for m in reversed(messages) if m.get("type") == "result"), None)
    summary: dict[str, Any] = {
        "model": model_from_messages(messages) or fallback_model,
        "cost_usd": None,
        "turns": None,
        "duration_ms": None,
        "is_error": None,
        "result_subtype": None,
        "error_class": "no_result",
    }
    if result is None:
        return summary
    cost = _number(result.get("total_cost_usd"))
    turns = _number(result.get("num_turns"))
    duration = _number(result.get("duration_ms"))
    subtype = result.get("subtype")
    is_error = bool(result.get("is_error")) or (isinstance(subtype, str) and subtype != "success")
    summary.update(
        {
            "cost_usd": round(cost, 4) if cost is not None else None,
            "turns": int(turns) if turns is not None else None,
            "duration_ms": int(duration) if duration is not None else None,
            "is_error": is_error,
            "result_subtype": subtype if isinstance(subtype, str) else None,
            "error_class": "",
        }
    )
    if is_error:
        text = " ".join(str(result.get(key) or "") for key in ("result", "error", "errors", "subtype"))
        summary["error_class"] = "quota" if QUOTA_RE.search(text) else "other"
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _write_outputs(values: dict[str, str]) -> None:
    for key, value in values.items():
        print(f"{key}={value}")
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            for key, value in values.items():
                f.write(f"{key}={value}\n")


def cmd_criteria_version(args: argparse.Namespace) -> int:
    root = Path(args.root)
    _write_outputs(
        {
            "criteria_version": criteria_version(root, args.library or None),
            "prompts_tree": tree_id(root / "prompts") or MISSING,
        }
    )
    return 0


def cmd_model(args: argparse.Namespace) -> int:
    _write_outputs({"model_id": resolved_model(args.execution_file, args.fallback)})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    cv = sub.add_parser("criteria-version", help="Blob ids of the rubric files (and the library prompt)")
    cv.add_argument("--root", default=".")
    cv.add_argument("--library", default="")
    cv.set_defaults(func=cmd_criteria_version)

    model = sub.add_parser("model", help="Resolved model id from a claude-code-action execution file")
    model.add_argument("--execution-file", default="")
    model.add_argument("--fallback", required=True)
    model.set_defaults(func=cmd_model)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
