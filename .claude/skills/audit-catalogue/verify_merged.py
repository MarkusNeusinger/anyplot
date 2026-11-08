"""Verify an audit round's merged pairs end to end, read-only: the code, the metadata, the database row, the renders
and the API.

Run it from the repository root after `git fetch origin main`, once `pkg_status.sh` shows a package's PRs merged and
the `Sync: PostgreSQL` run that followed the last merge has completed:

    uv run --extra agents python .claude/skills/audit-catalogue/verify_merged.py --round "$ROUND" --env "$ENV" \
        [--key <line key> ...] [--no-db]

It reads `<round>/dispatch.state` (each dispatched line's kind, library, adopted SHA, dispatch time and specs) and
`<round>/queue.txt` (each line's source_model, matched by the line key `dispatch.sh` computes). Per pair:

- `merged`: the metadata at `--ref` was updated at or after the dispatch. Otherwise the pair is `pending`, or `closed`
  when its newest PR titled `feat(<library>): implement <spec>` since the dispatch closed without a merge: the fix did
  not pass the pipeline, and its finding returns to the plan.
- `code` (adopt lines): the implementation at `--ref` equals the fix at its SHA below the header block, which
  impl-review rewrites. When a repair commit or a later merge changed it since, the pair passes with a note as long
  as every line the fix added (against the commit it was cut from) is still there. Once one is gone, the pair is
  `marked`: the merged code is not the fix the owner saw, so a skeptic re-audits the merged production renders and
  the merged review (`<round>/reaudit-<time>.json` holds the audit workflow's args). Clean, it passes; otherwise its
  finding goes back on the page. A marked pair never passes silently.
- `metadata`: `quality_score`, `updated` and `generated_by` are set, `generated_by` is the line's source_model for
  adopt and rerender lines, and `library_version` is not an API level behind the pinned version.
- `database` (unless `--no-db`): the `impls` row, read in a transaction PostgreSQL holds read-only, carries the
  metadata's quality_score, updated and generated_by. While a `Sync: PostgreSQL` run created since the pair's update
  is queued or in progress, a database or API difference leaves the pair `pending`: impl-merge triggers one sync per
  merge and the workflow queues them. Once none is active, a difference means the sync did not land.
- `renders`: both production PNGs and both `_800.webp` variants the site shows answer 200 with a `Last-Modified` no
  older than the metadata's `updated`, fetched with a cache-buster (the bucket serves `max-age=604800`).
- `api`: `GET https://api.anyplot.ai/specs/<spec>`, with a cache-buster past Cloudflare's 300 s, returns the
  metadata's three values for the pair.

It prints one line per pair and a route for each that did not pass, writes `<round>/verify-<time>.json`, and writes
the site paths of the passing and the marked pairs (their renders, rows and API entries matched) to
`<round>/verify-pages.txt` for `scripts/site-smoke.mjs`, which checks that their pages render. Nothing here writes
anywhere but the round directory. Exit codes: 0 every pair passed, 1 a pair is pending, marked, closed or failed, 2
bad arguments, a round inside a checkout, nothing dispatched, or no `DATABASE_URL` without `--no-db`.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

import catalogue
import check_fix
import select_candidates
from catalogue import Pair


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


API = "https://api.anyplot.ai"
USER_AGENT = "anyplot-audit-catalogue/1 (read-only)"
"""Cloudflare answers the default Python user agent with 403."""
KINDS = ("adopt", "rerender", "regen")
"""The dispatch.state kinds that sent something; `refused` and `failed` lines sent nothing."""
ADOPTABLE = ("python", "javascript")
STATUSES = ("ok", "pending", "marked", "closed", "failed")
MARKED = "marked:"
"""The prefix of the one problem that marks a pair instead of failing it: lines the fix added are gone from main."""
SYNC_SLACK = timedelta(seconds=60)
"""Clock slack between the runner that stamps `updated` and the creation time GitHub gives the sync run."""
FINDING_KEYS = ("pair", "severity", "defect_class", "cause", "what", "evidence", "fix", "pr")

REAUDIT = (
    "re-audit: a skeptic checks the merged production renders (with ?cb=) and the merged review against the pair's "
    "finding (audit_workflow.js with the reaudit file's args); clean, the pair passes; otherwise the finding goes back "
    "on the page. Never pass it silently, never merge by hand"
)
CLOSED = (
    "the fix did not pass the pipeline: the finding returns to the plan (a new fix, or the owner's call); "
    "never a hand merge"
)
SYNC_WAIT = "run this again once the Sync: PostgreSQL run that followed the merge has completed"


@dataclass(frozen=True)
class Dispatched:
    """One line of dispatch.state that went out."""

    key: str
    kind: str
    library: str
    sha: str | None
    when: datetime
    specs: tuple[str, ...]
    model: str | None = None


@dataclass
class PairResult:
    pair: str
    key: str
    kind: str
    status: str = "ok"
    """One of `STATUSES`: `pending` (not merged since the dispatch, or the sync still running), `marked` (lines the
    fix added are gone: a re-audit decides), `closed` (the PR closed unmerged) or `failed`."""
    problems: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    route: str = ""


# --- the round's files ------------------------------------------------------------------------------------------


def line_fields(line: str) -> list[str]:
    """A queue line's fields as dispatch.sh reads them: the text before `#`, split on blanks and tabs."""
    return [part for part in re.split(r"[ \t]+", line.split("#", 1)[0]) if part]


def line_key(fields: list[str]) -> str:
    """dispatch.sh's key: the first 12 hex digits of the SHA-1 of the fields joined by single blanks."""
    return hashlib.sha1(" ".join(fields).encode(), usedforsecurity=False).hexdigest()[:12]


def queue_models(text: str) -> dict[str, str]:
    """The source_model of every adopt and rerender line, by line key."""
    models: dict[str, str] = {}
    for line in text.split("\n"):
        fields = line_fields(line)
        if len(fields) >= 5 and fields[0] == "adopt":
            models[line_key(fields)] = fields[3]
        elif len(fields) == 4 and fields[0] == "rerender":
            models[line_key(fields)] = fields[2]
    return models


def read_state(text: str, models: dict[str, str]) -> list[Dispatched]:
    """The lines of dispatch.state that sent something, in the order they went out."""
    sent: list[Dispatched] = []
    for line in text.split("\n"):
        parts = line.split()
        if len(parts) < 7 or parts[1] not in KINDS:
            continue
        when = catalogue.parse_time(parts[4])
        if when is None:
            continue
        sha = parts[3] if parts[3] != "-" else None
        sent.append(Dispatched(parts[0], parts[1], parts[2], sha, when, tuple(parts[6:]), models.get(parts[0])))
    return sent


# --- the checks -------------------------------------------------------------------------------------------------


def body(text: str) -> str:
    """The code below the header block (through its `Quality:` line), which impl-review rewrites."""
    lines = text.splitlines()
    block = check_fix.header_block(text)
    return "\n".join(lines[len(block) :] if block else lines)


def code_check(on_main: str | None, fix: str | None, start: str | None) -> tuple[list[str], list[str]]:
    """`(problems, notes)` for the code on main against the fix and the commit the fix was cut from (`start`).

    Equal below the header is the plain case. A repair commit in the PR, or a later merge, can change the code after
    the fix; that passes with a note while every line the fix added is still on main. Once one is gone, the one
    problem starts with `MARKED`: the pair goes to a re-audit instead of failing or passing."""
    if on_main is None:
        return ["code: the implementation is missing on main"], []
    if fix is None:
        return ["code: the fix SHA has no such file, or the SHA is not in the local store (git fetch origin <ref>)"], []
    merged, fixed = body(on_main), body(fix)
    if merged == fixed:
        return [], []
    before = set(body(start).splitlines()) if start else set()
    added = [line for line in dict.fromkeys(fixed.splitlines()) if line.strip() and line not in before]
    present = set(merged.splitlines())
    missing = [line for line in added if line not in present]
    if missing:
        problem = (
            f"{MARKED} {len(missing)} of the {len(added)} line(s) the fix added are not on main "
            f"(a repair or a later merge changed or removed them), first: {missing[0].strip()[:100]}"
        )
        return [problem], []
    return [], [f"code: changed after the fix (a repair or a later merge); all {len(added)} line(s) it added are in"]


def metadata_problems(metadata: dict[str, Any], *, model: str | None, pinned: str | None = None) -> list[str]:
    problems: list[str] = []
    if not isinstance(metadata.get("quality_score"), int | float):
        problems.append("metadata: no quality_score")
    generated_by = metadata.get("generated_by")
    if not generated_by:
        problems.append("metadata: no generated_by")
    elif model and generated_by != model:
        problems.append(f"metadata: generated_by {generated_by}, the line's source_model is {model}")
    stored = metadata.get("library_version")
    if select_candidates.library_behind(stored, pinned):
        problems.append(f"metadata: library_version {stored}, pinned {pinned} (an older API level)")
    return problems


def _same_time(left: object, right: object) -> bool:
    a, b = catalogue.parse_time(left), catalogue.parse_time(right)
    return a is not None and b is not None and abs((a - b).total_seconds()) < 1


def _same_score(left: object, right: object) -> bool:
    return isinstance(left, int | float) and isinstance(right, int | float) and abs(left - right) < 1e-6


def stored_problems(where: str, stored: dict[str, Any] | None, metadata: dict[str, Any]) -> list[str]:
    """A stored copy of the pair (the database row, the API's entry) against the metadata it was synced from."""
    if stored is None:
        return [f"{where}: no entry for the pair"]
    problems: list[str] = []
    for name, same in (("quality_score", _same_score), ("updated", _same_time)):
        if not same(stored.get(name), metadata.get(name)):
            problems.append(f"{where}: {name} {stored.get(name)}, the metadata has {metadata.get(name)}")
    if stored.get("generated_by") != metadata.get("generated_by"):
        problems.append(
            f"{where}: generated_by {stored.get('generated_by')}, the metadata has {metadata.get('generated_by')}"
        )
    return problems


def render_problems(heads: dict[str, tuple[int | None, datetime | None]], updated: datetime | None) -> list[str]:
    return [f"renders: {reason.detail}" for reason in select_candidates.gcs_reasons(heads, updated)]


def sync_pending(runs: list[dict[str, Any]] | None, since: datetime) -> bool:
    """True while a `Sync: PostgreSQL` run created since `since` (the pair's `updated`, less the clock slack) is
    queued or in progress. `runs` is `gh run list --json status,createdAt`; None (gh failed) counts as no such run."""
    for run in runs or []:
        created = catalogue.parse_time(run.get("createdAt"))
        if run.get("status") != "completed" and created is not None and created + SYNC_SLACK >= since:
            return True
    return False


def pr_outcome(prs: list[dict[str, Any]] | None, *, library: str, spec: str, since: datetime) -> str | None:
    """The state of the pair's newest PR titled `feat(<library>): implement <spec>` created since the dispatch, in
    lower case (`open`, `merged`, `closed`), as pkg_status.sh finds it; None when there is none or gh failed."""
    title = f"feat({library}): implement {spec}"
    mine = []
    for pr in prs or []:
        created = catalogue.parse_time(pr.get("createdAt"))
        if pr.get("title") == title and created is not None and created >= since:
            mine.append(pr)
    if not mine:
        return None
    state = str(max(mine, key=lambda pr: int(pr.get("number") or 0)).get("state") or "")
    return state.lower() or None


NO_ANSWER = "api: no answer"


def route(pair: Pair, problems: list[str], metadata: dict[str, Any]) -> str:
    """What to do about a pair that did not pass, most specific first. A queue line still needs the owner's OK."""
    rest = [problem for problem in problems if not problem.startswith(MARKED)]
    if not rest:
        return REAUDIT
    then = "; then the re-audit of its marked lines" if len(rest) < len(problems) else ""
    if any(problem.startswith(("code:", "metadata:")) for problem in rest):
        return "read the merged PR and its impl-merge run before anything is re-dispatched" + then
    if any(problem.startswith("renders:") for problem in rest):
        if pair.language in ADOPTABLE:
            model = metadata.get("generated_by") or "<source_model>"
            return f"queue line: rerender {pair.library} {model} {pair.spec}" + then
        return (
            f"queue line: regen {pair.library} {pair.spec} Keep the merged plot as it is; its production renders are "
            f"stale.{then}"
        )
    if rest == [NO_ANSWER]:
        return "the API gave no answer: run this again in a few minutes" + then
    return "the sync did not land: read the last sync-postgres.yml run; a re-run is the owner's call" + then


def evaluate(
    entry: Dispatched,
    pair: Pair,
    *,
    metadata: dict[str, Any],
    on_main: str | None,
    fix: str | None,
    start: str | None,
    row: dict[str, Any] | None,
    api_entry: dict[str, Any] | None,
    heads: dict[str, tuple[int | None, datetime | None]],
    check_db: bool,
    api_answered: bool = True,
    pinned: str | None = None,
    sync_active: bool = False,
    pr_state: str | None = None,
) -> PairResult:
    """One pair's verdict. `fix` and `start` are the adopted file and the one it was cut from (adopt lines only);
    `row` and `api_entry` are None when the store has no entry for the pair; `api_answered` is False when the API gave
    no answer at all; `pinned` is the library's pinned version; `sync_active` says a sync run created since the pair's
    update is still running; `pr_state` is `pr_outcome` for a pair not merged yet."""
    result = PairResult(pair.key, entry.key, entry.kind)
    updated = catalogue.parse_time(metadata.get("updated"))
    if updated is None:
        result.status, result.problems = "failed", ["metadata: no updated"]
        result.route = route(pair, result.problems, metadata)
        return result
    if updated < entry.when:
        if pr_state == "closed":
            result.status, result.route = "closed", CLOSED
            result.problems = ["closed: the pair's newest PR since the dispatch closed without a merge"]
            return result
        result.status = "pending"
        result.problems = [
            f"not merged yet: the metadata was updated {updated:%Y-%m-%dT%H:%M:%SZ}, before the dispatch"
        ]
        return result
    problems, result.notes = code_check(on_main, fix, start) if entry.kind == "adopt" else ([], [])
    model = entry.model if entry.kind in ("adopt", "rerender") else None
    problems += metadata_problems(metadata, model=model, pinned=pinned)
    if check_db:
        problems += stored_problems("database", row, metadata)
    problems += render_problems(heads, updated)
    problems += stored_problems("api", api_entry, metadata) if api_answered else [NO_ANSWER]
    result.problems = problems
    synced = [problem for problem in problems if problem.startswith(("database:", "api:"))]
    others = [problem for problem in problems if problem not in synced and not problem.startswith(MARKED)]
    if synced and not others and sync_active:
        result.status, result.route = "pending", SYNC_WAIT
        result.notes.append("sync: a Sync: PostgreSQL run created since the pair's update is queued or in progress")
    elif synced or others:
        result.status, result.route = "failed", route(pair, problems, metadata)
    elif problems:
        result.status, result.route = "marked", REAUDIT
    return result


def reaudit_claims(results: list[PairResult], findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The re-audit's claims for the marked pairs, in the audit workflow's finding shape: each finding of the pair
    the round's page held (refuted ones aside), with the mark; a marked pair without one gets a claim of its own, so
    none passes unexamined."""
    claims: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for result in results:
        if result.status != "marked":
            continue
        mark = "; ".join(problem for problem in result.problems if problem.startswith(MARKED))
        own = [f for f in findings if f.get("pair") == result.pair and f.get("status") != "refuted"]
        for finding in own:
            if (result.pair, finding.get("id")) in seen:
                continue
            seen.add((result.pair, finding.get("id")))
            claims.append(
                {**{key: finding.get(key) for key in FINDING_KEYS}, "finding_id": finding.get("id"), "mark": mark}
            )
        if not own and (result.pair, None) not in seen:
            seen.add((result.pair, None))
            claims.append(
                {
                    "pair": result.pair,
                    "severity": "medium",
                    "defect_class": "reworked-fix",
                    "cause": "implementation",
                    "what": "a pipeline repair or a later merge changed lines the fix added; the merged plot may show "
                    "the defect the fix removed, or a new one",
                    "evidence": mark,
                    "fix": "",
                    "pr": 0,
                    "finding_id": None,
                    "mark": mark,
                }
            )
    return claims


# --- the reads --------------------------------------------------------------------------------------------------


async def impl_rows(session: AsyncSession, specs: set[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    """The `impls` rows of these specs as `(spec, language, library) -> {quality_score, updated, generated_by}`."""
    from sqlalchemy import select

    from core.database import Impl

    result = await session.execute(
        select(
            Impl.spec_id, Impl.language_id, Impl.library_id, Impl.quality_score, Impl.updated, Impl.generated_by
        ).where(Impl.spec_id.in_(sorted(specs)))
    )
    return {
        (row.spec_id, row.language_id, row.library_id): {
            "quality_score": row.quality_score,
            "updated": row.updated,
            "generated_by": row.generated_by,
        }
        for row in result.all()
    }


async def read_rows(specs: set[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    from core.database import close_db, get_db_context

    try:
        async with get_db_context() as session:
            await select_candidates.read_only(session)
            return await impl_rows(session, specs)
    finally:
        await close_db()


def api_entries(spec: str, cache_buster: int, *, attempts: int = 3) -> dict[tuple[str, str], dict[str, Any]] | None:
    """The API's implementations of a spec as `(language, library) -> entry`; None when it gave no answer."""
    url = f"{API}/specs/{spec}?cb={cache_buster}"
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {}
            time.sleep(2 * (attempt + 1))
            continue
        except urllib.error.URLError, TimeoutError, OSError, ValueError:
            time.sleep(2 * (attempt + 1))
            continue
        return {
            (str(impl.get("language")), str(impl.get("library_id"))): impl
            for impl in data.get("implementations", [])
            if isinstance(impl, dict)
        }
    return None


def gh_list(*args: str) -> list[dict[str, Any]] | None:
    """A `gh … --json` listing of the repository, read-only; None when gh fails or answers with anything else."""
    try:
        run = subprocess.run(
            ["gh", "-R", catalogue.REPOSITORY, *args], capture_output=True, text=True, timeout=60, check=False
        )
    except OSError, subprocess.TimeoutExpired:
        return None
    if run.returncode != 0:
        return None
    try:
        data = json.loads(run.stdout)
    except ValueError:
        return None
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else None


def line_prs(entry: Dispatched) -> list[dict[str, Any]] | None:
    """The PRs of the line's library created since its dispatch day, as pkg_status.sh lists them."""
    search = f"{entry.library} in:title created:>={entry.when:%Y-%m-%d}"
    fields = "number,title,state,createdAt"
    return gh_list("pr", "list", "--state", "all", "--limit", "500", "--search", search, "--json", fields)


def read_findings(path: Path) -> list[dict[str, Any]]:
    """The round's findings (build_page.py's `findings.json`), empty when the file is missing or unreadable."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return []
    findings = data.get("findings") if isinstance(data, dict) else None
    return [f for f in findings if isinstance(f, dict)] if isinstance(findings, list) else []


# --- the round --------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify an audit round's merged pairs end to end, read-only.")
    parser.add_argument("--round", type=Path, required=True, help="the round directory")
    parser.add_argument("--key", action="append", default=[], help="only this dispatch line (repeatable)")
    parser.add_argument("--ref", default="origin/main", help="the commit the merged state is read from")
    parser.add_argument("--repo", type=Path, default=catalogue.REPO_ROOT, help="the checkout whose git store holds it")
    parser.add_argument("--env", type=Path, default=catalogue.REPO_ROOT / ".env", help="the .env with DATABASE_URL")
    parser.add_argument("--no-db", action="store_true", help="skip the database row")
    args = parser.parse_args(argv)
    if not catalogue.outside_repository(args.round):
        print(f"verify_merged: {args.round} is inside a git checkout; a round's files stay outside", file=sys.stderr)
        return 2
    state_path, queue_path = args.round / "dispatch.state", args.round / "queue.txt"
    if not state_path.is_file():
        print(f"verify_merged: no {state_path}; nothing was dispatched", file=sys.stderr)
        return 2
    if not args.no_db and not select_candidates.use_database_url(args.env):
        print(
            f"verify_merged: DATABASE_URL is not set and {args.env} does not define it (or pass --no-db)",
            file=sys.stderr,
        )
        return 2
    models = queue_models(queue_path.read_text(encoding="utf-8")) if queue_path.is_file() else {}
    sent = [e for e in read_state(state_path.read_text(encoding="utf-8"), models) if not args.key or e.key in args.key]
    jobs: list[tuple[Dispatched, Pair]] = []
    for entry in sent:
        language = catalogue.library_language(entry.library)
        if language is None:
            print(
                f"verify_merged: line {entry.key} names the unknown library {entry.library}, skipped", file=sys.stderr
            )
            continue
        jobs += [(entry, Pair(spec, language, entry.library)) for spec in entry.specs]
    if not jobs:
        print("verify_merged: no dispatched pair to verify", file=sys.stderr)
        return 2

    from core.library_versions import pinned_versions

    pins = pinned_versions(catalogue.REPO_ROOT).libraries
    tree = catalogue.GitTree(args.repo, args.ref)
    metadata_text = tree.read_many(sorted({pair.metadata_path for _, pair in jobs}))
    main_code = tree.read_many(sorted({pair.impl_path for _, pair in jobs}))
    fixes: dict[tuple[str, str], tuple[str | None, str | None]] = {}
    for sha in sorted({entry.sha for entry, _ in jobs if entry.kind == "adopt" and entry.sha}):
        mine = [(entry, pair) for entry, pair in jobs if entry.sha == sha]
        paths = sorted({pair.impl_path for _, pair in mine})
        try:
            fix_tree = catalogue.GitTree(args.repo, sha)
            fixed_code = fix_tree.read_many(paths)
            start_code = catalogue.GitTree(args.repo, fix_tree.merge_base(tree.sha)).read_many(paths)
        except ValueError, RuntimeError:
            fixed_code, start_code = {}, {}
        for entry, pair in mine:
            fixes[(entry.key, pair.key)] = (fixed_code.get(pair.impl_path), start_code.get(pair.impl_path))
    metadata = {pair.key: catalogue.load_metadata(metadata_text[pair.metadata_path]) for _, pair in jobs}

    def is_merged(entry: Dispatched, pair: Pair) -> bool:
        updated = catalogue.parse_time(metadata[pair.key].get("updated"))
        return updated is not None and updated >= entry.when

    merged = [pair for entry, pair in jobs if is_merged(entry, pair)]
    cache_buster = int(time.time())
    heads = select_candidates.check_renders(sorted(set(merged)), cache_buster)
    api = {spec: api_entries(spec, cache_buster) for spec in sorted({pair.spec for pair in merged})}
    rows = asyncio.run(read_rows({pair.spec for pair in merged})) if merged and not args.no_db else {}
    syncs = gh_list("run", "list", "--workflow", "sync-postgres.yml", "--limit", "20", "--json", "status,createdAt")
    waiting = {entry for entry, pair in jobs if not is_merged(entry, pair)}
    prs = {entry.key: line_prs(entry) for entry in waiting}

    results: list[PairResult] = []
    for entry, pair in jobs:
        spec_api = api.get(pair.spec)
        fix, start = fixes.get((entry.key, pair.key), (None, None))
        updated = catalogue.parse_time(metadata[pair.key].get("updated"))
        results.append(
            evaluate(
                entry,
                pair,
                metadata=metadata[pair.key],
                on_main=main_code[pair.impl_path],
                fix=fix,
                start=start,
                row=rows.get((pair.spec, pair.language, pair.library)),
                api_entry=(spec_api or {}).get((pair.language, pair.library)),
                heads=heads.get(pair, {}),
                check_db=not args.no_db,
                api_answered=spec_api is not None,
                pinned=pins.get(pair.library),
                sync_active=updated is not None and sync_pending(syncs, updated),
                pr_state=pr_outcome(prs.get(entry.key), library=pair.library, spec=pair.spec, since=entry.when),
            )
        )

    for result in results:
        print(f"{result.status:<8} {result.pair} (line {result.key}, {result.kind})")
        for problem in result.problems:
            print(f"  {problem}")
        for note in result.notes:
            print(f"  note: {note}")
        if result.route:
            print(f"  route: {result.route}")
    counts = {status: sum(r.status == status for r in results) for status in STATUSES}
    print(f"{len(results)} pair(s): " + ", ".join(f"{counts[status]} {status}" for status in STATUSES))
    if syncs is None:
        print("note: gh could not list the Sync: PostgreSQL runs; a database difference counts as a failure")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    payload = {"verified_at": stamp, "ref": args.ref, "sha": tree.sha, "results": [asdict(r) for r in results]}
    catalogue.write_private(args.round / f"verify-{stamp}.json", json.dumps(payload, indent=2) + "\n")
    shown = {"ok", "marked"}
    passed = sorted({Pair.parse(r.pair).site_url.removeprefix(catalogue.SITE) for r in results if r.status in shown})
    catalogue.write_private(args.round / "verify-pages.txt", "".join(f"{path}\n" for path in passed))
    print(f"wrote {args.round / f'verify-{stamp}.json'} and {args.round / 'verify-pages.txt'} ({len(passed)} page(s))")
    claims = reaudit_claims(results, read_findings(args.round / "findings.json"))
    if claims:
        reaudit = args.round / f"reaudit-{stamp}.json"
        workflow_args = {
            "round": str(args.round.expanduser().resolve()),
            "repo": str(args.repo.expanduser().resolve()),
            "ref": args.ref,
            "label": f"reaudit-{stamp}",
            "reaudit": claims,
        }
        catalogue.write_private(reaudit, json.dumps(workflow_args, indent=2) + "\n")
        print(f"wrote {reaudit}: {len(claims)} claim(s) of {counts['marked']} marked pair(s) for the re-audit")
    return 0 if counts["ok"] == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
