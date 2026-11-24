#!/usr/bin/env python3
"""Follow-up regenerations: whether one may be dispatched, the dispatch, and the marks that bound it.

After a gated regeneration, the pipeline may run one more regeneration of
the same (spec, library) pair, a *follow-up*, which goes through
impl-generate and the regen gate like any other and is judged against the
file that is live by then (``docs/workflows/overview.md``, "Follow-up
regenerations"; the two decisions are in ``docs/decisions/``):

- ``repair`` (a repair round): the gate merged the regeneration (code
  ``merge`` or ``adapt_identity``) and the review that ran still names at
  least one defect line. impl-merge dispatches the follow-up after the merge
  and the promotion. The winner is then live, so the follow-up reads the
  winner's review the normal way and its defect lines reach the generator as
  ``W`` lines.
- ``retry``: the gate kept the live implementation for a regression (code
  ``regression``). impl-review dispatches the follow-up after the kept
  attempt's write-back has merged or closed. It carries the regression as a
  note (``regen_gate.py retry-note``), never as a change request, so the
  gate's ``-basic`` waiver for a change request stays shut.

Both are behind repository variables, off unless set to exactly ``true``:
``REGEN_REPAIR_ROUND`` and ``REGEN_RETRY``.

A follow-up is never followed up, and a pair gets at most one per streak. The
bound reads durable state only, never a label, and fails closed:

1. The follow-up's PR body carries ``**Follow-up of:** #N (kind)``
   (``regen_gate.FOLLOW_UP_LINE_RE``), which impl-generate writes from its
   ``follow_up`` input and forwards on its own crash retry. Its gate record
   then carries ``follow_up_of``, and ``regen_gate.follow_up_trigger``
   returns ``none`` for it.
2. ``dispatch`` posts a marker comment on the predecessor PR
   (``<!-- regen-follow-up:v1 {...} -->``, by ``github-actions[bot]``) before
   it dispatches. A comment that cannot be posted means no dispatch, and a
   dispatch that fails afterwards leaves the marker standing (and a note that
   says so): the pair has spent its follow-up either way.
3. ``plan`` refuses when the predecessor already carries the marker, when
   another PR of the pair is open (impl-generate would delete its branch),
   or when a PR of the pair updated in the last ``WINDOW_DAYS`` days carries
   the body line or a marker posted in the window. That covers a follow-up
   whose body line was lost, because a rescue re-dispatched its generation
   without the input: its predecessor's marker is still inside the window.
4. Anything that cannot be read (the PR, its comments, the pair's PRs, the
   run list a retried dispatch checks) means no dispatch.

The gate record is the first valid record by ``github-actions[bot]`` on the
predecessor PR, read with ``regen_gate.parse_record_markers``. Only a record
that carries ``follow_up_trigger`` can trigger, so a record written before
the follow-up keys triggers nothing, and eligibility is also recomputed from
its verdict, code and ``defect_lines`` (``regen_gate.follow_up_trigger``): the
two must agree.

Subcommands::

    regen_follow_up.py plan --kind repair|retry --pr N --spec-id S --library B [--repo OWNER/NAME] \
        [--window-days 7]
    regen_follow_up.py dispatch --kind repair|retry --pr N --spec-id S --library B [--repo OWNER/NAME] \
        --ref REF [--model auto] [--issue N] [--change-request TEXT] [--note TEXT]
    regen_follow_up.py marker --kind repair|retry --pr N --spec-id S --library B
    regen_follow_up.py parse-body < PR_BODY

``plan`` prints ``dispatch=true|false`` and ``reason=<code>`` (``REASONS``);
``dispatch`` prints ``dispatched=true|false`` and ``reason=<code>``
(``DISPATCH_REASONS``). Both also write to ``$GITHUB_OUTPUT`` when it is set
and exit 0; 2 is a usage error. ``marker`` prints the comment body.
``parse-body`` prints ``follow_up_of=`` and ``follow_up_kind=`` (empty when
the body names no predecessor).

``dispatch`` never dispatches twice for one call that it can see: before it
repeats a failed ``gh workflow run`` it lists impl-generate's runs since its
first attempt, and a run for the pair there means the earlier call was
accepted. A call GitHub took whose run is not in that list yet is the one
double this side cannot rule out, and impl-generate closes it on the
receiving side: its ``follow_up_check`` job ends a run whose pair already has
an open PR with the same ``**Follow-up of:**`` line.

Stdlib only. ``regen_gate`` is imported from this file's own directory, so a
workflow's copy of the two files never reads the checkout's.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any


# The type checker reads the package import; at run time the script branch
# loads the workflow-ref copy next to this file.
if TYPE_CHECKING or __package__:  # imported as automation.scripts.regen_follow_up (tests, local tools)
    from automation.scripts import regen_gate
else:  # run as a script: the regen_gate.py next to this file (the workflow-ref copy)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import regen_gate


BOT = "github-actions[bot]"
WINDOW_DAYS = 7
KINDS = regen_gate.FOLLOW_UP_KINDS
BODY_LINE_RE = regen_gate.FOLLOW_UP_LINE_RE
MARKER_RE = re.compile(r"<!-- regen-follow-up:v1 (\{[^\n]*?\}) -->")
TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")
REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
MODELS = ("auto", "haiku", "sonnet", "opus")
GENERATE = "impl-generate.yml"
# How far before the first dispatch attempt a run in impl-generate's list may
# start and still count as this call's (the runner's clock against GitHub's).
CLOCK_SLACK = timedelta(minutes=2)

DISPATCH = "dispatch"
REASONS = (
    DISPATCH,
    "is_follow_up",  # the PR is itself a follow-up (body line or record)
    "no_record",  # no gate record by the workflow on the PR
    "not_eligible",  # the record carries no trigger, or its decision triggers no follow-up of this kind
    "already",  # the PR already carries a follow-up marker
    "open_pr",  # another PR of the pair is open
    "recent_follow_up",  # a PR of the pair updated in the window is a follow-up or has a marker posted in it
    "unreadable",  # the PR, its comments or the pair's PRs could not be read
)
DISPATCH_REASONS = (
    DISPATCH,
    "marker_not_posted",  # no dispatch: the marker could not be posted first
    "dispatch_failed",  # the marker stands; impl-generate did not take the dispatch
    "dispatch_unknown",  # the marker stands; a failed call left it unknown, so no second call was made
)

SENTENCES = {
    regen_gate.FOLLOW_UP_REPAIR: (
        "**Follow-up regeneration (repair round).** This regeneration replaced the live implementation, "
        "and its review still names defect lines. One more regeneration of this pair is being dispatched "
        "to fix them; the same regen gate judges it against this version, which stays live unless the "
        "follow-up beats it. A follow-up is never followed up."
    ),
    regen_gate.FOLLOW_UP_RETRY: (
        "**Follow-up regeneration (retry).** The regen gate kept the live implementation for a regression. "
        "One more regeneration of this pair is being dispatched, with that regression named in a note; "
        "the same regen gate judges it against the live version. A retry is never retried."
    ),
}
NOT_DISPATCHED = {
    "dispatch_failed": (
        "not dispatched.** impl-generate did not take the dispatch, so no follow-up runs for this pair."
    ),
    # The call may have been taken: the note must not say that nothing runs.
    "dispatch_unknown": (
        "dispatch state unknown.** A dispatch call reported a failure, and whether GitHub took it anyway "
        "could not be read, so no second call was made. If GitHub took it, the follow-up runs; "
        "impl-generate refuses a duplicate of it."
    ),
}


class ReadError(Exception):
    """A ``gh`` read failed; the plan then refuses (``unreadable``)."""


@dataclass(frozen=True)
class Plan:
    dispatch: bool
    reason: str


def body_follow_up(body: Any) -> tuple[int, str] | None:
    """``(predecessor PR, kind)`` from a PR body's ``**Follow-up of:**`` line, else ``None``."""
    return regen_gate.body_follow_up(body)


def render_marker(kind: str, pr: int, spec_id: str, library: str) -> str:
    """The comment body: one sentence for people, then the marker for the bound."""
    if kind not in KINDS or not (isinstance(pr, int) and pr > 0):
        raise ValueError("a follow-up marker needs a kind and a PR number")
    if not (TOKEN_RE.fullmatch(spec_id) and TOKEN_RE.fullmatch(library)):
        raise ValueError("spec id and library must be plain tokens")
    payload = json.dumps({"kind": kind, "pr": pr, "spec": spec_id, "lib": library}, separators=(",", ":"))
    return f"{SENTENCES[kind]}\n\n<!-- regen-follow-up:v1 {payload} -->"


def render_not_dispatched(kind: str, reason: str) -> str:
    """The note posted after the marker when the dispatch did not go through, or may not have."""
    return (
        f"**Follow-up regeneration ({'repair round' if kind == regen_gate.FOLLOW_UP_REPAIR else kind}), "
        f"{NOT_DISPATCHED[reason]} The marker above still counts as the pair's one follow-up."
    )


def _time(value: Any) -> datetime | None:
    try:
        then = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return then if then.tzinfo else then.replace(tzinfo=timezone.utc)


def _within(value: Any, now: datetime, window_days: int) -> bool:
    """Inside the window; an unreadable time counts as inside (fail closed)."""
    then = _time(value)
    return then is None or now - then <= timedelta(days=window_days)


def has_marker(
    comments: Sequence[Mapping[str, Any]], *, now: datetime | None = None, window_days: int = WINDOW_DAYS
) -> bool:
    """Whether the workflow posted a follow-up marker among these comments (anyone can paste one).

    With ``now``, only a marker posted in the window counts.
    """
    for comment in comments:
        if comment.get("login") != BOT or not MARKER_RE.search(str(comment.get("body") or "")):
            continue
        if now is None or _within(comment.get("created_at"), now, window_days):
            return True
    return False


def first_gate_record(comments: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """The first valid gate record the workflow posted (``collect_week.gate_record``'s rule)."""
    for comment in sorted(comments, key=lambda c: str(c.get("created_at") or "")):
        if comment.get("login") != BOT:
            continue
        records = regen_gate.parse_record_markers(str(comment.get("body") or ""))
        if records:
            return records[0]
    return None


def plan_follow_up(
    kind: str,
    pr: int,
    body: str,
    comments: Sequence[Mapping[str, Any]],
    history: Sequence[Mapping[str, Any]],
    now: datetime,
    window_days: int = WINDOW_DAYS,
) -> Plan:
    """Whether a follow-up of ``kind`` may be dispatched for ``pr``.

    ``comments`` are the PR's own (``login``, ``body``, ``created_at``);
    ``history`` the pair's PRs (``number``, ``state``, ``updated_at``,
    ``body``, ``comments``; the PR itself is skipped). Any open one refuses;
    of the others only those updated in the window count.
    """
    if kind not in KINDS:
        raise ValueError(f"unknown follow-up kind {kind!r}")
    record = first_gate_record(comments)
    if body_follow_up(body) is not None or (record is not None and "follow_up_of" in record):
        return Plan(False, "is_follow_up")
    if record is None:
        return Plan(False, "no_record")
    trigger = regen_gate.follow_up_trigger(
        record.get("verdict"), record.get("code"), record.get("defect_lines"), record.get("follow_up_of")
    )
    if record.get("follow_up_trigger") != kind or trigger != kind:
        return Plan(False, "not_eligible")
    if has_marker(comments):
        return Plan(False, "already")
    others = [other for other in history if other.get("number") != pr]
    if any(other.get("state") == "OPEN" for other in others):
        return Plan(False, "open_pr")
    for other in others:
        if not _within(other.get("updated_at"), now, window_days):
            continue
        if body_follow_up(other.get("body")) is not None:
            return Plan(False, "recent_follow_up")
        if has_marker(other.get("comments") or [], now=now, window_days=window_days):
            return Plan(False, "recent_follow_up")
    return Plan(True, DISPATCH)


# ---------------------------------------------------------------------------
# gh (the only I/O; tests replace ``_gh`` and ``_gh_ok``)
# ---------------------------------------------------------------------------


def _gh(args: list[str]) -> str:
    """Run a ``gh`` read and return stdout; three attempts, then ``ReadError``."""
    error = ""
    for attempt in range(1, 4):
        proc = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            return proc.stdout
        error = (proc.stderr or "").strip().replace("\n", " ")[:300]
        if attempt < 3:
            time.sleep(attempt * 5)
    raise ReadError(f"gh {args[0]} failed: {error}")


def _gh_ok(args: list[str]) -> bool:
    """Run a ``gh`` write once; whether it exited 0."""
    proc = subprocess.run(["gh", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        error = (proc.stderr or "").strip().replace("\n", " ")[:300]
        print(f"::warning::gh {' '.join(args[:2])} failed: {error}", file=sys.stderr)
    return proc.returncode == 0


def _comments(repo: str, number: int) -> list[dict[str, Any]]:
    out = _gh(
        [
            "api",
            "--paginate",
            f"repos/{repo}/issues/{number}/comments?per_page=100",
            "--jq",
            ".[] | {login: .user.login, body: .body, created_at: .created_at} | @json",
        ]
    )
    try:
        return [json.loads(line) for line in out.splitlines() if line.strip()]
    except ValueError as exc:
        raise ReadError(f"comments of #{number} unreadable") from exc


def read_inputs(
    repo: str, pr: int, spec_id: str, library: str, now: datetime, window_days: int
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """``(body, comments, history)`` for ``plan_follow_up``; ``ReadError`` on any failed read."""
    head = f"implementation/{spec_id}/{library}"
    try:
        pulls = json.loads(
            _gh(
                [
                    "pr",
                    "list",
                    "--repo",
                    repo,
                    "--state",
                    "all",
                    "--head",
                    head,
                    "--limit",
                    "50",
                    "--json",
                    "number,body,state,createdAt,updatedAt,isCrossRepository",
                ]
            )
            or "[]"
        )
        view = json.loads(_gh(["pr", "view", str(pr), "--repo", repo, "--json", "number,body,headRefName"]))
    except ValueError as exc:
        raise ReadError("the pair's pull requests are unreadable") from exc
    if not isinstance(pulls, list) or not isinstance(view, dict):
        raise ReadError("the pair's pull requests are unreadable")
    if view.get("headRefName") != head:
        raise ReadError(f"#{pr} is not a pull request of {head}")
    history = []
    for pull in pulls:
        number = pull.get("number")
        if not isinstance(number, int) or number == pr:
            continue
        # A fork's PR with the pair's branch name is not the pipeline's, so it
        # neither holds the pair open nor marks a follow-up. Only a PR that
        # says it is cross-repository is dropped: these guards only refuse, so
        # a missing field counts as this repository's PR.
        if pull.get("isCrossRepository") is True:
            continue
        entry = {
            "number": number,
            "state": pull.get("state"),
            "updated_at": pull.get("updatedAt"),
            "body": pull.get("body") or "",
            "comments": [],
        }
        # A marker comment moves updatedAt, so a PR updated before the window
        # holds no marker posted in it.
        if entry["state"] != "OPEN" and _within(entry["updated_at"], now, window_days):
            entry["comments"] = _comments(repo, number)
        history.append(entry)
    return str(view.get("body") or ""), _comments(repo, pr), history


def accepted_since(repo: str, spec_id: str, library: str, since: datetime) -> bool:
    """Whether impl-generate has a dispatched run for the pair that started after ``since`` (``ReadError``)."""
    out = _gh(
        [
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            GENERATE,
            "--event",
            "workflow_dispatch",
            "--limit",
            "30",
            "--json",
            "displayTitle,createdAt",
        ]
    )
    try:
        runs = json.loads(out or "[]")
    except ValueError as exc:
        raise ReadError("impl-generate's runs are unreadable") from exc
    title = f"Generate: {library} for {spec_id}"
    for run in runs if isinstance(runs, list) else []:
        started = _time(run.get("createdAt"))
        if run.get("displayTitle") == title and started is not None and started >= since - CLOCK_SLACK:
            return True
    return False


def dispatch_follow_up(
    kind: str,
    pr: int,
    spec_id: str,
    library: str,
    repo: str,
    ref: str,
    model: str,
    issue: str,
    change_request: str = "",
    note: str = "",
) -> str:
    """Post the marker, then dispatch impl-generate once; returns a ``DISPATCH_REASONS`` code."""
    marker = render_marker(kind, pr, spec_id, library)
    posted = False
    for attempt in range(1, 4):
        if _gh_ok(["pr", "comment", str(pr), "--repo", repo, "--body", marker]):
            posted = True
            break
        if attempt < 3:
            time.sleep(attempt * 10)
    if not posted:
        return "marker_not_posted"

    # A repair round carries neither: the winner applied its own change
    # request, and a repair goes after the named defects only.
    retry = kind == regen_gate.FOLLOW_UP_RETRY
    fields = {
        "specification_id": spec_id,
        "library": library,
        "issue_number": issue,
        "model": model,
        "change_request": change_request if retry else "",
        "regen_gate": "true",
        "source_ref": "",
        "source_model": "",
        "follow_up": f"{kind}:{pr}",
        "follow_up_note": note if retry else "",
    }
    command = ["workflow", "run", GENERATE, "--repo", repo, "--ref", ref]
    for key, value in fields.items():
        command += ["-f", f"{key}={value}"]
    since = datetime.now(timezone.utc)
    reason = "dispatch_failed"
    for attempt in range(1, 4):
        if attempt > 1:
            try:
                if accepted_since(repo, spec_id, library, since):
                    return DISPATCH
            except ReadError:
                reason = "dispatch_unknown"
                break
        if _gh_ok(command):
            return DISPATCH
        time.sleep(attempt * 10)
    else:
        # The last call may have been taken although it reported a failure.
        try:
            if accepted_since(repo, spec_id, library, since):
                return DISPATCH
        except ReadError:
            reason = "dispatch_unknown"
    _gh_ok(["pr", "comment", str(pr), "--repo", repo, "--body", render_not_dispatched(kind, reason)])
    return reason


def _write_outputs(values: Mapping[str, str]) -> None:
    lines = "".join(f"{key}={value}\n" for key, value in values.items())
    sys.stdout.write(lines)
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(lines)


def _repo(args: argparse.Namespace) -> str | None:
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        print("::error::bad_input: --repo (or GITHUB_REPOSITORY) is not OWNER/NAME", file=sys.stderr)
        return None
    if not (TOKEN_RE.fullmatch(args.spec_id) and TOKEN_RE.fullmatch(args.library)):
        print("::error::bad_input: spec id or library is not a plain token", file=sys.stderr)
        return None
    return repo


def cmd_plan(args: argparse.Namespace) -> int:
    repo = _repo(args)
    if repo is None:
        return 2
    now = datetime.now(timezone.utc)
    try:
        body, comments, history = read_inputs(repo, args.pr, args.spec_id, args.library, now, args.window_days)
    except ReadError as exc:
        print(f"::warning::no follow-up for #{args.pr}: {exc}", file=sys.stderr)
        plan = Plan(False, "unreadable")
    else:
        plan = plan_follow_up(args.kind, args.pr, body, comments, history, now, args.window_days)
    print(
        f"::notice::regen_follow_up kind={args.kind} pr={args.pr} spec={args.spec_id} lib={args.library} "
        f"dispatch={'true' if plan.dispatch else 'false'} reason={plan.reason}",
        file=sys.stderr,
    )
    _write_outputs({"dispatch": "true" if plan.dispatch else "false", "reason": plan.reason})
    return 0


def cmd_dispatch(args: argparse.Namespace) -> int:
    repo = _repo(args)
    if repo is None:
        return 2
    if not REF_RE.fullmatch(args.ref) or args.model not in MODELS or not re.fullmatch(r"\d{0,10}", args.issue):
        print("::error::bad_input: --ref, --model or --issue does not have its expected shape", file=sys.stderr)
        return 2
    # One line each, as impl-generate writes them into the PR body.
    change_request = " ".join(args.change_request.split())
    note = " ".join(args.note.split())
    reason = dispatch_follow_up(
        args.kind, args.pr, args.spec_id, args.library, repo, args.ref, args.model, args.issue, change_request, note
    )
    print(
        f"::notice::regen_follow_up dispatch kind={args.kind} pr={args.pr} spec={args.spec_id} "
        f"lib={args.library} reason={reason}",
        file=sys.stderr,
    )
    _write_outputs({"dispatched": "true" if reason == DISPATCH else "false", "reason": reason})
    return 0


def cmd_marker(args: argparse.Namespace) -> int:
    try:
        print(render_marker(args.kind, args.pr, args.spec_id, args.library))
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    return 0


def cmd_parse_body(_args: argparse.Namespace) -> int:
    found = body_follow_up(sys.stdin.read())
    _write_outputs({"follow_up_of": str(found[0]) if found else "", "follow_up_kind": found[1] if found else ""})
    return 0


def _pr_number(raw: str) -> int:
    if not re.fullmatch(r"[1-9]\d{0,9}", raw):
        raise argparse.ArgumentTypeError("not a PR number")
    return int(raw)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan", help="Whether a follow-up may be dispatched (prints dispatch= and reason=)")
    dispatch = sub.add_parser("dispatch", help="Post the marker, then dispatch impl-generate once")
    marker = sub.add_parser("marker", help="Print the marker comment posted before a dispatch")
    for p in (plan, dispatch, marker):
        p.add_argument("--kind", required=True, choices=KINDS)
        p.add_argument("--pr", required=True, type=_pr_number)
        p.add_argument("--spec-id", required=True)
        p.add_argument("--library", required=True)
    for p in (plan, dispatch):
        p.add_argument("--repo", default="", help="OWNER/NAME (default: $GITHUB_REPOSITORY)")
    plan.add_argument("--window-days", type=int, default=WINDOW_DAYS)
    plan.set_defaults(func=cmd_plan)
    dispatch.add_argument("--ref", required=True, help="the ref impl-generate runs on")
    dispatch.add_argument("--model", default="auto", help=f"one of {', '.join(MODELS)}")
    dispatch.add_argument("--issue", default="", help="the spec issue, or empty")
    dispatch.add_argument("--change-request", default="", help="the predecessor's own change request (retry only)")
    dispatch.add_argument("--note", default="", help="the regression note (retry only)")
    dispatch.set_defaults(func=cmd_dispatch)
    marker.set_defaults(func=cmd_marker)

    body = sub.add_parser("parse-body", help="The predecessor a PR body names (stdin)")
    body.set_defaults(func=cmd_parse_body)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
