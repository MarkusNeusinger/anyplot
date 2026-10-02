#!/usr/bin/env python3
"""Review write-back: a kept regeneration stores its re-score of the live implementation.

A gated regeneration re-scores the live implementation in the same review
session that scores the new render (``prompts/workflow-prompts/
ai-quality-review.md`` step 8b), and step 8b step 5 writes that re-score as a
full review, ``review_prev.json``. When the regen gate keeps the live
implementation, this script turns that file into the implementation's stored
review — score, image description, criteria checklist, strengths, weaknesses,
verdict, review model and rules version — and puts the score into the
``Quality: N/100`` header (owner decision O9). ``updated``, ``rendered_at``,
``impl_tags``, the previews and every other key stay: the code did not change.

``main`` takes changes only through a merged pull request, so the write-back
travels as one:

- ``impl-review.yml`` "Write back the re-score (regen keep)" runs ``check`` and
  ``apply`` from its workflow-ref copy, commits the two files on
  ``review-writeback/{spec}/{library}/{kept PR}`` (label ``review-writeback``,
  ``GITHUB_TOKEN`` only) and dispatches ``impl-merge.yml``.
- ``impl-merge.yml``'s ``writeback`` job runs ``check-pr`` (the pull request is
  the bot's, it targets ``main``, and its score, review model and rules version
  are the ones the kept PR's gate record holds),
  ``verify-diff`` (only the pair's review keys and header number change) and,
  before every merge attempt, ``check-fresh`` (it still targets ``main``, and
  ``main`` did not change the pair's files since the branch was cut), then
  merges with the admin token.

Subcommands::

    regen_writeback.py check --prev-review review_prev.json --regen-json review_regen.json

    regen_writeback.py apply --metadata META.yaml --prev-review review_prev.json --score N \\
        [--model ID] [--criteria-version V] [--impl IMPL_FILE]

    regen_writeback.py verify-diff --base REF --head REF --spec S --library B \\
        [--language L --ext E] [--repo DIR]

    regen_writeback.py check-pr --pr N [--wait SECONDS] [--repo DIR]

    regen_writeback.py check-fresh --pr N [--head SHA] [--repo DIR]

``check-pr`` writes ``key=value`` outputs to ``$GITHUB_OUTPUT`` when it is set.
Stdlib and PyYAML; ``regen_gate`` is imported from this file's own directory
when it runs as a script, so a workflow's copy never reads the checkout's.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


if __package__:  # imported as automation.scripts.regen_writeback (tests, local tools)
    from automation.scripts import regen_gate
else:  # run as a script: the regen_gate.py next to this file (the workflow-ref copy)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import regen_gate


BRANCH_PREFIX = "review-writeback"
BRANCH_RE = re.compile(r"^review-writeback/(?P<spec>[a-z0-9-]+)/(?P<library>[a-z0-9]+)/(?P<pr>[0-9]+)$")
LABEL = "review-writeback"
KEPT_LABEL = "regen:kept"
# verify-diff and check-fresh compare against origin/main, and `gh pr merge`
# merges into the PR's own base, so a write-back PR must target main.
BASE_BRANCH = "main"
# The author of a pull request GITHUB_TOKEN opened, as `gh pr view --json
# author` names it, and the login of its comments in the REST API.
BOT_AUTHOR = "app/github-actions"
BOT_LOGIN = "github-actions[bot]"

# The review keys a write-back takes from review_prev.json, the verdict it
# sets itself and the provenance keys it sets or removes; nothing else in the
# metadata moves.
REVIEW_FIELDS = ("image_description", "criteria_checklist", "strengths", "weaknesses")
PROVENANCE_FIELDS = ("model", "criteria_version")
WRITABLE_REVIEW_KEYS = frozenset(REVIEW_FIELDS + ("verdict",) + PROVENANCE_FIELDS)
# A kept implementation stays live, which is what the stored verdict says (the
# website's `review_verdict`). The reviewer writes no verdict: the bar it would
# need is not in its prompts, and a kept review_prev.json that still carries
# one is ignored.
KEPT_VERDICT = "APPROVED"

# Mirrors core/constants.py LIBRARIES_METADATA and the workflows' case
# statements (tests/unit/automation/scripts/test_regen_writeback.py ties them).
LIBRARY_LANGUAGE = {
    "matplotlib": "python",
    "seaborn": "python",
    "plotly": "python",
    "bokeh": "python",
    "altair": "python",
    "plotnine": "python",
    "pygal": "python",
    "highcharts": "javascript",
    "letsplot": "python",
    "ggplot2": "r",
    "makie": "julia",
    "chartjs": "javascript",
    "d3": "javascript",
    "echarts": "javascript",
    "muix": "javascript",
}
LANGUAGE_EXT = {"python": ".py", "r": ".R", "julia": ".jl", "javascript": ".js"}
LIBRARY_EXT_OVERRIDES = {"muix": ".tsx"}


class WritebackError(RuntimeError):
    """A broken input or a failed command; the CLI prints it and exits non-zero."""


def language_of(library: str) -> str:
    if library not in LIBRARY_LANGUAGE:
        raise WritebackError(f"unknown library {library!r}")
    return LIBRARY_LANGUAGE[library]


def ext_of(library: str) -> str:
    return LIBRARY_EXT_OVERRIDES.get(library, LANGUAGE_EXT[language_of(library)])


def pair_paths(spec: str, library: str, language: str = "", ext: str = "") -> tuple[str, str]:
    """``(metadata, implementation)`` repository paths of one (spec, library) pair."""
    language = language or language_of(library)
    ext = ext or ext_of(library)
    return (
        f"plots/{spec}/metadata/{language}/{library}.yaml",
        f"plots/{spec}/implementations/{language}/{library}{ext}",
    )


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------


def _str_representer(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    """impl-review.yml's metadata writer: timestamps quoted, multi-line text as a literal block."""
    if value.endswith("Z") and "T" in value:
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="'")
    if "\n" in value:
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", value)


class _WriterDumper(yaml.SafeDumper):
    """The metadata writer's YAML settings, without touching PyYAML's global Dumper."""


_WriterDumper.add_representer(str, _str_representer)


def dump_metadata(data: Mapping[str, Any]) -> str:
    """YAML text as impl-review.yml's metadata writer produces it (key order kept)."""
    return yaml.dump(dict(data), Dumper=_WriterDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)


def apply_review(
    data: Mapping[str, Any], prev_review: Mapping[str, Any], score: int, model: str = "", criteria_version: str = ""
) -> dict[str, Any]:
    """The metadata with the re-score as its stored review.

    Sets ``quality_score``, the four review fields of ``review_prev.json`` and
    ``review.verdict`` (``KEPT_VERDICT``, whatever the file says); sets
    ``review.model`` and ``review.criteria_version`` or, when the session
    could not resolve one, removes it (as the metadata writer does). Every
    other key keeps its value and its place.
    """
    missing = [key for key in REVIEW_FIELDS if key not in prev_review]
    if missing:
        raise WritebackError(f"review_prev.json lacks {', '.join(missing)} (run `check` first)")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise WritebackError(f"score must be an integer 0-100 (got {score!r})")
    out = dict(data)
    out["quality_score"] = score
    raw = out.get("review")
    review: dict[str, Any] = dict(raw) if isinstance(raw, Mapping) else {}
    review["image_description"] = str(prev_review["image_description"]).strip()
    review["criteria_checklist"] = prev_review["criteria_checklist"]
    review["strengths"] = [str(s).strip() for s in prev_review["strengths"]]
    review["weaknesses"] = [str(w).strip() for w in prev_review["weaknesses"]]
    review["verdict"] = KEPT_VERDICT
    for key, value in (("model", model), ("criteria_version", criteria_version)):
        value = (value or "").strip()
        if value and value != "n/a":
            review[key] = value
        else:
            review.pop(key, None)
    out["review"] = review
    return out


def cmd_apply(args: argparse.Namespace) -> int:
    score = regen_gate.parse_score(args.score)
    if score is None:
        raise WritebackError(f"--score must be an integer 0-100 (got {args.score!r})")
    prev_review = json.loads(Path(args.prev_review).read_text(encoding="utf-8"))
    if not isinstance(prev_review, Mapping):
        raise WritebackError(f"{args.prev_review} is not a JSON object")
    meta = Path(args.metadata)
    original = meta.read_text(encoding="utf-8")
    data = yaml.safe_load(original) or {}
    if not isinstance(data, Mapping):
        raise WritebackError(f"{meta} is not a YAML mapping")
    changed: list[str] = []
    text = dump_metadata(apply_review(data, prev_review, score, args.model, args.criteria_version))
    if text != original:
        meta.write_text(text, encoding="utf-8")
        changed.append(str(meta))
    if args.impl and Path(args.impl).is_file():
        impl = Path(args.impl)
        source = impl.read_text(encoding="utf-8")
        rewritten = regen_gate.set_header_score(source, score)
        if rewritten != source:
            impl.write_text(rewritten, encoding="utf-8")
            changed.append(str(impl))
    print(f"apply: {', '.join(changed) if changed else 'nothing changed'}")
    return 0


# ---------------------------------------------------------------------------
# verify-diff
# ---------------------------------------------------------------------------


def _load_yaml(text: str, where: str) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [f"{where} is not valid YAML: {regen_gate._one_line(str(exc))[:200]}"]
    if not isinstance(data, dict):
        return None, [f"{where} is not a YAML mapping"]
    return data, []


def metadata_diff_problems(old_text: str, new_text: str) -> list[str]:
    """Parsed-YAML comparison: only ``quality_score`` and the writable review keys may differ."""
    old, problems = _load_yaml(old_text, "the metadata at the merge base")
    new, more = _load_yaml(new_text, "the metadata at the head")
    problems += more
    if old is None or new is None:
        return problems
    for key in sorted(set(old) | set(new), key=str):
        if key in ("quality_score", "review"):
            continue
        if old.get(key) != new.get(key) or (key in old) != (key in new):
            problems.append(f"metadata key {key!r} changed; a write-back changes quality_score and review only")
    score = new.get("quality_score")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        problems.append(f"quality_score at the head must be an integer 0-100 (got {score!r})")
    old_review = old.get("review") if isinstance(old.get("review"), dict) else {}
    new_review = new.get("review")
    if not isinstance(new_review, dict):
        problems.append("review at the head is not a mapping")
        return problems
    for key in sorted(set(old_review) | set(new_review), key=str):
        if key in WRITABLE_REVIEW_KEYS:
            continue
        if old_review.get(key) != new_review.get(key) or (key in old_review) != (key in new_review):
            problems.append(
                f"review key {key!r} changed; a write-back changes {', '.join(sorted(WRITABLE_REVIEW_KEYS))}"
            )
    return problems


def header_diff_problems(old_text: str, new_text: str) -> list[str]:
    """Only the number of the ``Quality: N/100`` header line may change."""
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    if len(old_lines) != len(new_lines):
        return [
            f"the implementation file went from {len(old_lines)} to {len(new_lines)} lines; only its header may change"
        ]
    changed = [i for i, (a, b) in enumerate(zip(old_lines, new_lines, strict=True)) if a != b]
    if len(changed) != 1:
        return [f"{len(changed)} lines of the implementation file changed; only its Quality header line may change"]
    i = changed[0]
    old_match = regen_gate.QUALITY_HEADER_RE.fullmatch(old_lines[i].rstrip("\r\n"))
    new_match = regen_gate.QUALITY_HEADER_RE.fullmatch(new_lines[i].rstrip("\r\n"))
    if i >= regen_gate.HEADER_LINES or old_match is None or new_match is None:
        return [f"line {i + 1} of the implementation file changed and is not its Quality header line"]
    same_frame = all(old_match.group(g) == new_match.group(g) for g in ("head", "scale", "tail"))
    same_ending = old_lines[i][len(old_lines[i].rstrip("\r\n")) :] == new_lines[i][len(new_lines[i].rstrip("\r\n")) :]
    if not (same_frame and same_ending):
        return [f"line {i + 1}: only the number of the Quality header may change"]
    return []


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise WritebackError(f"git {' '.join(args)} failed: {regen_gate._one_line(result.stderr)[:300]}")
    return result.stdout


def _git_show(repo: Path, ref: str, path: str) -> str | None:
    result = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{path}"], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def _blob(repo: Path, ref: str, path: str) -> str:
    """The blob id of ``ref:path``; empty when the path does not exist there."""
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "-q", "--verify", f"{ref}:{path}"], capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def verify_diff(
    repo: Path, base: str, head: str, spec: str, library: str, language: str = "", ext: str = ""
) -> list[str]:
    """Problems of the change ``head`` makes against its merge base with ``base``."""
    meta, impl = pair_paths(spec, library, language, ext)
    merge_base = _git(repo, "merge-base", base, head).strip()
    raw = _git(repo, "diff", "--name-status", "--no-renames", "-z", merge_base, head)
    fields = [f for f in raw.split("\0") if f]
    entries = list(zip(fields[0::2], fields[1::2], strict=True))
    problems: list[str] = []
    changed: set[str] = set()
    for status, path in entries:
        if path not in (meta, impl):
            problems.append(f"{path} changed; a write-back touches {meta} and {impl} only")
        elif status != "M":
            problems.append(f"{path} has status {status}; a write-back only modifies it")
        else:
            changed.add(path)
    if meta not in changed:
        problems.append(f"{meta} did not change; there is nothing to write back")
        return problems
    old_meta, new_meta = _git_show(repo, merge_base, meta), _git_show(repo, head, meta)
    problems += metadata_diff_problems(old_meta or "", new_meta or "")
    if impl in changed:
        problems += header_diff_problems(_git_show(repo, merge_base, impl) or "", _git_show(repo, head, impl) or "")
    return problems


def cmd_verify_diff(args: argparse.Namespace) -> int:
    problems = verify_diff(
        Path(args.repo), args.base, args.head, args.spec, args.library, args.language or "", args.ext or ""
    )
    for problem in problems:
        print(f"::error::{problem}")
    if not problems:
        print("verify-diff: only the pair's review keys, quality_score and the header number change")
    return 1 if problems else 0


# ---------------------------------------------------------------------------
# check-pr: the pull request is the bot's, and its score is the gate record's
# ---------------------------------------------------------------------------

GhRunner = Callable[[list[str]], str]


def run_gh(args: list[str]) -> str:
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise WritebackError(f"gh {' '.join(args[:3])} failed: {regen_gate._one_line(result.stderr)[:300]}")
    return result.stdout


def _gh_retry(gh: GhRunner, args: list[str], sleep: Callable[[float], None], tries: int = 3) -> str:
    for attempt in range(1, tries + 1):
        try:
            return gh(args)
        except WritebackError as exc:
            if attempt == tries:
                raise
            print(f"::warning::{exc} (attempt {attempt}/{tries})")
            sleep(attempt * 5)
    raise AssertionError("unreachable")


@dataclass
class PrCheck:
    """``noop`` (not a write-back PR), ``ok`` or ``fail``; ``pending`` only between polls."""

    status: str
    reason: str = ""
    outputs: dict[str, str] = field(default_factory=dict)


def writeback_pr_identity(data: Mapping[str, Any]) -> str:
    """Empty when the PR is an open write-back PR the bot opened; otherwise why not."""
    labels = {str(label.get("name")) for label in data.get("labels") or [] if isinstance(label, Mapping)}
    author = (data.get("author") or {}).get("login") if isinstance(data.get("author"), Mapping) else None
    if data.get("state") != "OPEN":
        return f"state {data.get('state')!r} is not OPEN"
    if not BRANCH_RE.match(str(data.get("headRefName") or "")):
        return f"head {data.get('headRefName')!r} is not {BRANCH_PREFIX}/<spec>/<library>/<PR>"
    if LABEL not in labels:
        return f"no {LABEL} label"
    if author != BOT_AUTHOR:
        return f"author {author!r} is not {BOT_AUTHOR}"
    if data.get("isCrossRepository"):
        return "the head is in another repository"
    return ""


def base_problem(data: Mapping[str, Any]) -> str:
    """Empty when the PR targets ``main``; otherwise why it must not merge."""
    base = data.get("baseRefName")
    if base != BASE_BRANCH:
        return f"its base {base!r} is not {BASE_BRANCH}"
    return ""


def _json_lines(text: str) -> list[Any]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def anchor_to_gate_record(
    kept: Mapping[str, Any],
    comments: list[Mapping[str, Any]],
    *,
    spec: str,
    library: str,
    kept_pr: int,
    since: str,
    score: int | None,
    header: int | None,
    provenance: Mapping[str, Any] | None = None,
) -> tuple[str, str]:
    """``("ok"|"pending"|"fail", reason)`` for the kept PR and its gate record.

    The record is the first ``regen-gate-record`` marker in a comment by
    ``github-actions[bot]`` posted at or after ``since`` (the write-back PR's
    creation): the verdict step of the run that opened the write-back posts
    it right after. It must say keep, for this pair and PR, with
    ``writeback: opened``, a ``prev_rescored`` equal to the metadata's new
    ``quality_score`` and to the header number when the file has a header, and
    the ``model`` and ``criteria_version`` of the metadata's new ``review``
    (``provenance``; an absent key is the record's ``n/a``).
    """
    provenance = provenance or {}
    if kept.get("headRefName") != f"implementation/{spec}/{library}":
        return "fail", f"kept PR #{kept_pr} has head {kept.get('headRefName')!r}, not implementation/{spec}/{library}"
    if kept.get("state") == "MERGED" or kept.get("mergedAt"):
        return "fail", f"kept PR #{kept_pr} was merged, so it kept nothing"
    if kept.get("state") != "CLOSED":
        return "pending", f"kept PR #{kept_pr} is still {kept.get('state')!r}"
    labels = {str(label.get("name")) for label in kept.get("labels") or [] if isinstance(label, Mapping)}
    if KEPT_LABEL not in labels:
        return "fail", f"kept PR #{kept_pr} has no {KEPT_LABEL} label"
    record: dict[str, Any] | None = None
    for comment in comments:
        if comment.get("user") != BOT_LOGIN or str(comment.get("created_at") or "") < since:
            continue
        found = regen_gate.parse_record_markers(str(comment.get("body") or ""))
        if found:
            record = found[0]
            break
    if record is None:
        return "pending", f"no gate record by {BOT_LOGIN} on #{kept_pr} since {since}"
    rescored = record.get("prev_rescored")
    checks = (
        (record.get("verdict") == regen_gate.KEEP, f"verdict {record.get('verdict')!r} is not keep"),
        (record.get("spec") == spec and record.get("lib") == library, "it names another pair"),
        (record.get("pr") == kept_pr, f"it names PR {record.get('pr')!r}"),
        (record.get("writeback") == "opened", f"writeback {record.get('writeback')!r} is not 'opened'"),
        (isinstance(rescored, int) and not isinstance(rescored, bool), f"prev_rescored {rescored!r} is no score"),
        (rescored == score, f"prev_rescored {rescored!r} differs from the metadata's new quality_score {score!r}"),
        (header is None or rescored == header, f"prev_rescored {rescored!r} differs from the header number {header!r}"),
        *(
            (
                regen_gate.record_token(record.get(key), limit) == regen_gate.record_token(provenance.get(key), limit),
                f"{key} {record.get(key)!r} differs from the metadata's review.{key} {provenance.get(key)!r}",
            )
            for key, limit in (("model", 100), ("criteria_version", 200))
        ),
    )
    for ok, why in checks:
        if not ok:
            return "fail", f"the gate record on #{kept_pr}: {why}"
    return "ok", f"gate record on #{kept_pr}: keep, prev_rescored {rescored}"


def check_pr(
    pr: int,
    *,
    gh: GhRunner,
    read_head: Callable[[str, str], str | None],
    fetch: Callable[[str], None] = lambda branch: None,
    wait: float = 0,
    interval: float = 20,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> PrCheck:
    """The write-back PR's identity (else a no-op) and its anchor to the kept PR's gate record.

    Once the PR is a write-back PR, ``fetch(branch)`` makes its head readable
    and ``read_head(sha, path)`` returns a file there. A kept PR that is still
    open, or a gate record that is not posted yet, is polled every
    ``interval`` seconds for up to ``wait`` seconds: impl-review dispatches the
    merge before its verdict step comments on and closes the kept PR.
    """
    data = json.loads(
        _gh_retry(
            gh,
            [
                "pr",
                "view",
                str(pr),
                "--json",
                "number,state,headRefName,headRefOid,baseRefName,labels,author,createdAt,isCrossRepository",
            ],
            sleep,
        )
    )
    why = writeback_pr_identity(data)
    if why:
        return PrCheck("noop", f"PR #{pr} is no review write-back: {why}", {"writeback_pr": "false"})
    outputs = {"writeback_pr": "true", "branch": data["headRefName"], "head_sha": str(data.get("headRefOid") or "")}
    # From here on the PR is a write-back PR: every failure, a broken command
    # included, is a `fail` with the outputs, so the job's failure step closes it.
    try:
        status, reason = _anchor_pr(data, outputs, gh, read_head, fetch, wait, interval, sleep, clock)
    except (WritebackError, ValueError) as exc:
        status, reason = "fail", regen_gate._one_line(str(exc))[:300]
    return PrCheck(status, reason, outputs)


def _anchor_pr(
    data: Mapping[str, Any],
    outputs: dict[str, str],
    gh: GhRunner,
    read_head: Callable[[str, str], str | None],
    fetch: Callable[[str], None],
    wait: float,
    interval: float,
    sleep: Callable[[float], None],
    clock: Callable[[], float],
) -> tuple[str, str]:
    match = BRANCH_RE.match(str(data["headRefName"]))
    assert match is not None  # writeback_pr_identity checked it
    # The bot's PR, retargeted: a fail, so the job's failure step closes it.
    why = base_problem(data)
    if why:
        return "fail", f"PR #{data.get('number')}: {why}"
    spec, library, kept_pr = match["spec"], match["library"], int(match["pr"])
    if library not in LIBRARY_LANGUAGE:
        return "fail", f"unknown library {library!r}"
    meta, impl = pair_paths(spec, library)
    head = outputs["head_sha"]
    fetch(str(data["headRefName"]))
    meta_text = read_head(head, meta)
    if meta_text is None:
        return "fail", f"{meta} is not at the head {head or '(none)'}"
    meta_data, problems = _load_yaml(meta_text, meta)
    raw_score = meta_data.get("quality_score") if meta_data else None
    score = raw_score if isinstance(raw_score, int) and not isinstance(raw_score, bool) else None
    if problems or score is None:
        return "fail", "; ".join(problems) or f"{meta} has no integer quality_score"
    impl_text = read_head(head, impl)
    header = regen_gate.header_score(impl_text) if impl_text is not None else None
    raw_review = meta_data.get("review") if meta_data else None
    provenance = raw_review if isinstance(raw_review, Mapping) else {}
    outputs.update(
        {
            "spec": spec,
            "library": library,
            "language": language_of(library),
            "ext": ext_of(library),
            "kept_pr": str(kept_pr),
            "score": str(score),
            "metadata": meta,
            "implementation": impl,
        }
    )

    deadline = clock() + wait
    since = str(data.get("createdAt") or "")
    comments_api = [
        "api",
        "--paginate",
        f"repos/{{owner}}/{{repo}}/issues/{kept_pr}/comments?per_page=100",
        "--jq",
        ".[] | {user: .user.login, created_at: .created_at, body: .body} | @json",
    ]
    while True:
        kept = json.loads(
            _gh_retry(gh, ["pr", "view", str(kept_pr), "--json", "number,state,mergedAt,labels,headRefName"], sleep)
        )
        comments = _json_lines(_gh_retry(gh, comments_api, sleep))
        status, reason = anchor_to_gate_record(
            kept,
            comments,
            spec=spec,
            library=library,
            kept_pr=kept_pr,
            since=since,
            score=score,
            header=header,
            provenance=provenance,
        )
        if status != "pending":
            return status, reason
        if clock() >= deadline:
            return "fail", f"{reason} after waiting {int(wait)} s"
        print(f"::notice::check-pr: {reason}; polling again in {int(interval)} s")
        sleep(interval)


def _git_fetch(repo: Path, *refspecs: str) -> None:
    last = ""
    for attempt in range(1, 4):
        result = subprocess.run(
            ["git", "-C", str(repo), "fetch", "-q", "origin", *refspecs], capture_output=True, text=True
        )
        if result.returncode == 0:
            return
        last = regen_gate._one_line(result.stderr)[:300]
        print(f"::warning::git fetch failed (attempt {attempt}/3): {last}")
        if attempt < 3:
            time.sleep(attempt * 5)
    raise WritebackError(f"git fetch {' '.join(refspecs)} failed: {last}")


def cmd_check_pr(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    try:
        result = check_pr(
            int(args.pr),
            gh=run_gh,
            read_head=lambda sha, path: _git_show(repo, sha, path),
            fetch=lambda branch: _git_fetch(repo, "main", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"),
            wait=float(args.wait),
        )
    except WritebackError as exc:
        # Unknown whether it is a write-back PR: close nothing, fail loudly.
        print(f"::error::check-pr: {exc}")
        return 2
    regen_gate._write_outputs(result.outputs)
    if result.status == "noop":
        print(f"::notice::{result.reason} — nothing to merge")
        return 0
    if result.status == "fail":
        print(f"::error::check-pr: {result.reason}")
        return 1
    print(f"::notice::check-pr: {result.reason}")
    return 0


# ---------------------------------------------------------------------------
# check-fresh: main did not change the pair's files since the branch was cut
# ---------------------------------------------------------------------------


def fresh_problems(repo: Path, main_ref: str, head: str, spec: str, library: str) -> list[str]:
    """Why merging ``head`` now would land the re-score on files it did not judge.

    A squash merge is three-way: a change ``main`` made to the pair's files
    after the branch was cut merges without a conflict and would carry the
    re-score of the old code. So the head changes the pair's files only, and
    ``main`` still holds the merge base's blobs of both.
    """
    meta, impl = pair_paths(spec, library)
    merge_base = _git(repo, "merge-base", main_ref, head).strip()
    names = [n for n in _git(repo, "diff", "--name-only", "--no-renames", "-z", merge_base, head).split("\0") if n]
    problems = [
        f"{name} changed on the branch; a write-back touches {meta} and {impl} only"
        for name in names
        if name not in (meta, impl)
    ]
    for path in (meta, impl):
        on_main, at_base = _blob(repo, main_ref, path), _blob(repo, merge_base, path)
        if on_main != at_base:
            problems.append(
                f"main changed {path} after the write-back branch was cut "
                f"({at_base[:12] or 'absent'} -> {on_main[:12] or 'absent'})"
            )
    return problems


def cmd_check_fresh(args: argparse.Namespace) -> int:
    repo = Path(args.repo)
    try:
        data = json.loads(
            _gh_retry(
                run_gh, ["pr", "view", str(args.pr), "--json", "state,headRefName,headRefOid,baseRefName"], time.sleep
            )
        )
        match = BRANCH_RE.match(str(data.get("headRefName") or ""))
        if match is None:
            print(f"::error::check-fresh: PR #{args.pr} is no review write-back")
            return 2
        why = base_problem(data)
        if why:
            print(f"::error::check-fresh: PR #{args.pr}: {why}")
            return 2
        branch = match.group(0)
        _git_fetch(repo, "main", f"+refs/heads/{branch}:refs/remotes/origin/{branch}")
        head = str(data.get("headRefOid") or "")
        if args.head and head != args.head:
            print(
                f"::warning::check-fresh: the head of #{args.pr} moved from {args.head[:12]} to {head[:12]} since it was verified"
            )
            return 1
        problems = fresh_problems(repo, "origin/main", head, match["spec"], match["library"])
    except WritebackError as exc:
        print(f"::error::check-fresh: {exc}")
        return 2
    for problem in problems:
        print(f"::warning::stale: {problem}")
    if not problems:
        print("check-fresh: main still holds the pair's files the re-score judged")
    return 1 if problems else 0


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------


def cmd_check(args: argparse.Namespace) -> int:
    prev_review, error = regen_gate.load_regen_json(Path(args.prev_review))
    regen, regen_error = regen_gate.load_regen_json(Path(args.regen_json))
    problems: list[str] = []
    if error:
        problems.append(f"{args.prev_review} {error}")
    if regen_error:
        problems.append(f"{args.regen_json} {regen_error}")
    if not error:
        problems += regen_gate.check_prev_review(prev_review, None if regen_error else regen)
    for problem in problems:
        print(regen_gate._one_line(problem))
    if not problems:
        print("check: review_prev.json can be stored")
    return 1 if problems else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    chk = sub.add_parser("check", help="Check review_prev.json against review_regen.json's prev_checklist")
    chk.add_argument("--prev-review", default="review_prev.json")
    chk.add_argument("--regen-json", default="review_regen.json")
    chk.set_defaults(func=cmd_check)

    app = sub.add_parser("apply", help="Write review_prev.json into the metadata and the score into the header")
    app.add_argument("--metadata", required=True)
    app.add_argument("--prev-review", required=True)
    app.add_argument("--score", required=True, help="the gate's prev_rescored")
    app.add_argument("--model", default="", help="resolved model id of the review session (empty removes the key)")
    app.add_argument("--criteria-version", default="", help="rules version of the session (empty removes the key)")
    app.add_argument("--impl", default="", help="the implementation file whose Quality header gets the score")
    app.set_defaults(func=cmd_apply)

    ver = sub.add_parser("verify-diff", help="Only the pair's review keys, quality_score and header number change")
    ver.add_argument("--base", required=True, help="compared from the merge base of --base and --head")
    ver.add_argument("--head", required=True)
    ver.add_argument("--spec", required=True)
    ver.add_argument("--library", required=True)
    ver.add_argument("--language", default="")
    ver.add_argument("--ext", default="")
    ver.add_argument("--repo", default=".")
    ver.set_defaults(func=cmd_verify_diff)

    cpr = sub.add_parser("check-pr", help="The PR is the bot's write-back, anchored to the kept PR's gate record")
    cpr.add_argument("--pr", required=True)
    cpr.add_argument("--wait", default="300", help="seconds to wait for the kept PR's close and gate record")
    cpr.add_argument("--repo", default=".")
    cpr.set_defaults(func=cmd_check_pr)

    cfr = sub.add_parser("check-fresh", help="main did not change the pair's files since the branch was cut")
    cfr.add_argument("--pr", required=True)
    cfr.add_argument("--head", default="", help="the head sha check-pr and verify-diff saw")
    cfr.add_argument("--repo", default=".")
    cfr.set_defaults(func=cmd_check_fresh)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except (WritebackError, OSError, ValueError, yaml.YAMLError) as exc:
        print(f"::error::regen_writeback {args.command}: {regen_gate._one_line(str(exc))[:300]}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
