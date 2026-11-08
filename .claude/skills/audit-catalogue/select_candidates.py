"""Select the catalogue pairs an audit round looks at; read-only everywhere it reads.

Run it from the repository root. In a worktree, name the main checkout's `.env` as `$ENV` for `--votes`
(see SKILL.md, step 1):

    uv run --extra agents python .claude/skills/audit-catalogue/select_candidates.py \
        --out "$ROUND/candidates.json" --votes --env "$ENV" --scores --stale --gcs [--readiness] \
        [--library muix] [--spec scatter-basic] [--sweep]

Sources, any combination, each adding reasons to a pair:

- `--votes`: the 👍/👎 per image from the production `feedback` table, split at the metadata's `updated`
  (`core.plot_votes`): votes before it were cast on an older version, and count only while this version has drawn
  no more thumbs up than down. On each side one vote counts per visitor session, the newest (the rule of
  `FeedbackRepository.reaction_counts` with `since` and `before`). The query runs in a transaction PostgreSQL holds
  read-only and returns reactions and times only; no message, contact or session id leaves it.
- `--scores`: the stored review in `metadata/*.yaml`: no score, a score below `--below`, a total lowered by a score
  cap, spec-compliance or other technical items below their maximum, and defect lines the merge kept on such an item.
- `--stale`: a stored `library_version` an API level behind the one `--ref` pins (`core.library_versions`, read from
  the ref's pin files), and with `--older-than DAYS` an `updated` older than that.
- `--gcs`: a HEAD on both production PNGs and both `_800.webp` variants the site shows, with a cache-busting query;
  a render that is missing, or older than the metadata's `updated`, is stale (a silent promote, as on 2026-11-08).
- `--readiness`: the agent validator's scan of each file (`uv run --extra agents`); a refusal for anything but a
  map spec means the agent chat refuses the file.
- `--sweep`: every pair of the filtered universe, with no other condition.

`--library`, `--language`, `--spec` and `--specs-file` narrow the universe first. The catalogue comes from
`--ref` (default `origin/main`; run `git fetch origin main` first). The output must lie outside every git
checkout. It prints one line per candidate, ranked; the rank only orders the list.

Exit codes: 0 written, 2 bad arguments, an output inside a checkout, or no `DATABASE_URL` for `--votes`.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import catalogue
from catalogue import Pair
from dotenv import dotenv_values


if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


SOURCES = ("votes", "scores", "stale", "gcs", "readiness", "sweep")
THUMBS = ("thumbs_up", "thumbs_down")
GCS_SLACK = timedelta(seconds=60)
"""Clock slack between the runner that stamps `updated` and the bucket's `Last-Modified`."""
RENDER_NAMES = tuple(catalogue.render_name(*render) for render in catalogue.RENDERS)
ITEM_ID = re.compile(r"\b[A-Z]{2}-\d{2}\b")
"""A checklist item id (`VQ-02`, `SC-01`) anywhere in a stored defect line."""
WEIGHTS = {
    "thumbs_down": 3,
    "thumbs_down_old_version": 1,
    "no_score": 3,
    "below_threshold": 2,
    "capped": 3,
    "checklist_mismatch": 1,
    "spec_compliance_below_max": 3,
    "plot_type_below_max": 4,
    "technical_below_max": 1,
    "residual_defects": 1,
    "library_behind": 1,
    "old_update": 1,
    "render_missing": 5,
    "render_stale": 5,
    "render_unchecked": 0,
    "validator_refusal": 4,
    "validator_error": 1,
    "sweep": 0,
}
"""How much each reason moves a pair up the list. A heuristic for the reading order, never a verdict."""


@dataclass(frozen=True)
class Reason:
    source: str
    code: str
    detail: str

    @property
    def weight(self) -> int:
        return WEIGHTS.get(self.code, 1)


@dataclass
class VoteCounts:
    """A pair's counted votes: `up` and `down` on every version, the `*_since_update` part on the current one."""

    up: int = 0
    down: int = 0
    up_since_update: int = 0
    down_since_update: int = 0


@dataclass
class Candidate:
    pair: Pair
    metadata: dict[str, Any] = field(default_factory=dict)
    reasons: list[Reason] = field(default_factory=list)
    votes: VoteCounts | None = None

    @property
    def rank(self) -> int:
        return sum(reason.weight for reason in self.reasons)

    def to_json(self) -> dict[str, Any]:
        meta = self.metadata
        return {
            "pair": self.pair.key,
            "spec": self.pair.spec,
            "language": self.pair.language,
            "library": self.pair.library,
            "rank": self.rank,
            "quality_score": meta.get("quality_score"),
            "updated": _iso(catalogue.parse_time(meta.get("updated"))),
            "library_version": meta.get("library_version"),
            "generated_by": meta.get("generated_by"),
            "votes": asdict(self.votes) if self.votes else None,
            "reasons": [asdict(reason) for reason in self.reasons],
        }


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if value else None


# --- scores -----------------------------------------------------------------------------------------------------


def score_reasons(metadata: dict[str, Any], *, below: float) -> list[Reason]:
    """What the stored review says about a pair: its score, a cap, items below their maximum, kept defect lines."""
    score = metadata.get("quality_score")
    if not isinstance(score, int | float):
        return [Reason("scores", "no_score", "no quality_score in the metadata")]
    reasons: list[Reason] = []
    if score < below:
        reasons.append(Reason("scores", "below_threshold", f"quality {score:g} < {below:g}"))
    items = catalogue.checklist_items(metadata)
    if items:
        total = sum(item["score"] for item in items)
        if score < total:
            zero = ", ".join(item["id"] for item in items if item["score"] == 0) or "no item at 0"
            reasons.append(Reason("scores", "capped", f"quality {score:g} below the item sum {total:g} ({zero})"))
        elif score > total:
            reasons.append(Reason("scores", "checklist_mismatch", f"quality {score:g} above the item sum {total:g}"))
    short = [item for item in items if item["score"] < item["max"]]
    plot_type = [item for item in short if item["id"] == "SC-01"]
    spec = [item for item in short if item["id"].startswith("SC") and item["id"] != "SC-01"]
    other = [
        item for item in short if item["id"][:2] in catalogue.TECHNICAL_PREFIXES and not item["id"].startswith("SC")
    ]
    if plot_type:
        reasons.append(Reason("scores", "plot_type_below_max", _items(plot_type)))
    if spec:
        reasons.append(Reason("scores", "spec_compliance_below_max", _items(spec)))
    if other:
        reasons.append(Reason("scores", "technical_below_max", _items(other)))
    # Nearly every stored review has defect lines, so only a line on an item that also lost points counts.
    lost = {item["id"] for item in short}
    kept = [line for line in catalogue.defect_lines(metadata) if lost & set(ITEM_ID.findall(line))]
    if kept:
        detail = f"{len(kept)} defect line(s) on an item below its maximum: {kept[0][:120]}"
        reasons.append(Reason("scores", "residual_defects", detail))
    return reasons


def _items(items: list[dict[str, Any]]) -> str:
    return ", ".join(f"{item['id']} {item['score']:g}/{item['max']:g}" for item in items)


# --- stale ------------------------------------------------------------------------------------------------------


def _version_key(version: str) -> tuple[int, ...] | None:
    parts: list[int] = []
    for part in version.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        if not digits:
            return None
        parts.append(int(digits))
    return tuple(parts)


def library_behind(stored: object, pinned: str | None) -> bool:
    """True when the stored version is at an older API level than the pinned one (`core.library_versions.api_level`:
    the major, or `0.minor` before 1.0)."""
    if not isinstance(stored, str) or not pinned:
        return False
    from core.library_versions import api_level

    old, new = _version_key(api_level(stored)), _version_key(api_level(pinned))
    return old is not None and new is not None and old < new


def stale_reasons(
    metadata: dict[str, Any], *, pinned: str | None, now: datetime, older_than: timedelta | None
) -> list[Reason]:
    reasons: list[Reason] = []
    stored = metadata.get("library_version")
    if library_behind(stored, pinned):
        reasons.append(Reason("stale", "library_behind", f"library_version {stored}, pinned {pinned}"))
    updated = catalogue.parse_time(metadata.get("updated") or metadata.get("created"))
    if older_than is not None and updated is not None and now - updated > older_than:
        reasons.append(Reason("stale", "old_update", f"updated {_iso(updated)}, {(now - updated).days} days ago"))
    return reasons


# --- GCS --------------------------------------------------------------------------------------------------------


def gcs_reasons(heads: dict[str, tuple[int | None, datetime | None]], updated: datetime | None) -> list[Reason]:
    """`heads` maps a render's file name (`catalogue.RENDERS`: `plot-light.png`, `plot-light_800.webp`, …) to the
    HEAD's status (None: no answer) and `Last-Modified`."""
    reasons: list[Reason] = []
    for name in RENDER_NAMES:
        status, modified = heads.get(name, (None, None))
        if status is None:
            reasons.append(Reason("gcs", "render_unchecked", f"{name}: no answer"))
        elif status != 200:
            reasons.append(Reason("gcs", "render_missing", f"{name}: HTTP {status}"))
        elif modified is None:
            reasons.append(Reason("gcs", "render_unchecked", f"{name}: no Last-Modified, freshness unknown"))
        elif updated is not None and modified + GCS_SLACK < updated:
            reasons.append(
                Reason("gcs", "render_stale", f"{name} modified {_iso(modified)}, metadata updated {_iso(updated)}")
            )
    return reasons


def head(url: str, *, attempts: int = 3) -> tuple[int | None, datetime | None]:
    """One HEAD request: the status and `Last-Modified`, or `(None, None)` when no attempt got an answer."""
    for attempt in range(attempts):
        request = urllib.request.Request(url, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                modified = response.headers.get("Last-Modified")
                return response.status, parsedate_to_datetime(modified) if modified else None
        except urllib.error.HTTPError as exc:
            return exc.code, None
        except urllib.error.URLError, TimeoutError, OSError:
            time.sleep(2 * (attempt + 1))
    return None, None


def check_renders(pairs: list[Pair], cache_buster: int) -> dict[Pair, dict[str, tuple[int | None, datetime | None]]]:
    """A HEAD on every render of `catalogue.RENDERS` per pair, keyed by the render's file name."""
    jobs = [(pair, render) for pair in pairs for render in catalogue.RENDERS]
    with ThreadPoolExecutor(max_workers=16) as pool:
        answers = list(
            pool.map(
                lambda job: head(
                    job[0].render_url(job[1][0], size=job[1][1], ext=job[1][2], cache_buster=cache_buster)
                ),
                jobs,
            )
        )
    out: dict[Pair, dict[str, tuple[int | None, datetime | None]]] = defaultdict(dict)
    for (pair, render), answer in zip(jobs, answers, strict=True):
        out[pair][catalogue.render_name(*render)] = answer
    return out


# --- votes ------------------------------------------------------------------------------------------------------


def use_database_url(env_file: Path) -> bool:
    """Export `DATABASE_URL` from the shell, else from `env_file` (that key only); False when neither has it.

    The value is never printed. `ENVIRONMENT` is set to `script`, because `core.database` echoes every statement
    with its parameters under `development`, its default.
    """
    if not os.environ.get("DATABASE_URL"):
        url = dotenv_values(env_file).get("DATABASE_URL") if env_file.is_file() else None
        if not url:
            return False
        os.environ["DATABASE_URL"] = url
    os.environ["ENVIRONMENT"] = "script"
    return True


async def read_only(session: AsyncSession) -> None:
    """Make the transaction read-only before its first query, and check that PostgreSQL agrees (SQLite: no-op)."""
    from sqlalchemy import text

    if session.get_bind().dialect.name != "postgresql":
        return
    await session.execute(text("SET TRANSACTION READ ONLY"))
    state = (await session.execute(text("SHOW transaction_read_only"))).scalar_one()
    if state != "on":
        raise RuntimeError(f"the transaction is not read-only (transaction_read_only = {state})")


VoteRow = tuple[str, str, str | None, str, datetime, datetime | None]
"""`(spec, library, language, reaction, created_at, newer_at)`: one plot vote, and when the same visitor session next
voted on the same image (None: never again)."""


async def vote_rows(session: AsyncSession) -> list[VoteRow]:
    """Every plot vote as a `VoteRow`, so `aggregate_votes` can keep the newest row per visitor session on each side of
    a pair's `updated`, as `FeedbackRepository.reaction_counts(spec, library, since=…)` and `(…, before=…)` count. A
    row without a session is its own voter. `newer_at` stands in for the session id, which never leaves the query. The
    language stays out of the partition: library ids are unique across languages, and a row without one
    (`aggregate_votes` gives it the library's) must not count a second time for the same session."""
    from sqlalchemy import String, cast, func, select

    from core.database import Feedback

    voter = func.coalesce(Feedback.session_id, cast(Feedback.id, String))
    result = await session.execute(
        select(
            Feedback.spec_id,
            Feedback.library_id,
            Feedback.language,
            Feedback.reaction,
            Feedback.created_at,
            # Newest first, so the previous row of the window is the voter's next newer vote on the image; the id
            # breaks a tie of `created_at` the way `reaction_counts` does.
            # `type_`: SQLAlchemy knows no return type for `lag`, and SQLite would hand back the timestamp as text.
            func.lag(Feedback.created_at, type_=Feedback.created_at.type).over(
                partition_by=(voter, Feedback.spec_id, Feedback.library_id),
                order_by=(Feedback.created_at.desc(), Feedback.id.desc()),
            ),
        ).where(Feedback.reaction.in_(THUMBS), Feedback.spec_id.is_not(None), Feedback.library_id.is_not(None))
    )
    return [tuple(row) for row in result.all()]


async def read_votes() -> list[VoteRow]:
    from core.database import close_db, get_db_context

    try:
        async with get_db_context() as session:
            await read_only(session)
            return await vote_rows(session)
    finally:
        await close_db()


def aggregate_votes(rows: Iterable[VoteRow], updated: dict[Pair, datetime | None]) -> dict[Pair, VoteCounts]:
    """Count the votes per pair, and separately those on the version that began at the pair's `updated`
    (`core.plot_votes`). On each side a session's newest vote counts: on the current version a row no newer one
    follows, on the earlier ones a row whose next newer one, if any, is on the current version. A vote without a
    language belongs to its library's language; a vote on a pair the catalogue lacks is dropped."""
    from core.plot_votes import on_current_version

    counts: dict[Pair, VoteCounts] = {}
    for spec, library, language, reaction, created, newer in rows:
        language = language or catalogue.library_language(library)
        if language is None:
            continue
        pair = Pair(spec, language, library)
        if pair not in updated:
            continue
        since = updated[pair]
        fresh = on_current_version(created, since)
        newest_on_its_side = newer is None or (not fresh and on_current_version(newer, since))
        if not newest_on_its_side:
            continue
        count = counts.setdefault(pair, VoteCounts())
        if reaction == "thumbs_up":
            count.up += 1
            count.up_since_update += fresh
        elif reaction == "thumbs_down":
            count.down += 1
            count.down_since_update += fresh
    return counts


def vote_reasons(count: VoteCounts | None, *, min_down: int) -> list[Reason]:
    """Thumbs down that outweigh the thumbs up: on this version first, else on the versions before it, as long as
    this version has drawn no more thumbs up than down (then the update may have fixed what the votes saw)."""
    if count is None:
        return []
    down_now, up_now = count.down_since_update, count.up_since_update
    if down_now >= min_down and down_now > up_now:
        detail = f"{down_now} down, {up_now} up since the last update ({count.down} down, {count.up} up in all)"
        return [Reason("votes", "thumbs_down", detail)]
    down_before, up_before = count.down - down_now, count.up - up_now
    if down_before >= min_down and down_before > up_before and up_now <= down_now:
        detail = (
            f"{down_before} down, {up_before} up before the last update (an older version); "
            f"{down_now} down, {up_now} up since"
        )
        return [Reason("votes", "thumbs_down_old_version", detail)]
    return []


# --- readiness --------------------------------------------------------------------------------------------------


def readiness_reasons(pair: Pair, code: str | None) -> list[Reason]:
    if code is None:
        return [Reason("readiness", "validator_error", f"{pair.impl_path} is missing")]
    status, reasons, _ = catalogue.readiness_of(pair, code)
    if status == "error":
        return [Reason("readiness", "validator_error", reasons[0] if reasons else "the profile failed")]
    refused = catalogue.refusals(reasons) if status == "blocked" else []
    return [Reason("readiness", "validator_refusal", refused[0][:200])] if refused else []


# --- the round --------------------------------------------------------------------------------------------------


def in_universe(pair: Pair, *, libraries: set[str], languages: set[str], specs: set[str]) -> bool:
    return (
        (not libraries or pair.library in libraries)
        and (not languages or pair.language in languages)
        and (not specs or pair.spec in specs)
    )


def ranked(candidates: Iterable[Candidate]) -> list[Candidate]:
    """The pairs with at least one reason, most reasons' weight first, then by pair."""
    return sorted((c for c in candidates if c.reasons), key=lambda c: (-c.rank, c.pair))


def table(candidates: list[Candidate], *, dropped: int) -> str:
    lines = [f"{'rank':>4}  {'pair':<52}  {'score':>5}  reasons"]
    for candidate in candidates:
        score = candidate.metadata.get("quality_score")
        codes = ",".join(dict.fromkeys(reason.code for reason in candidate.reasons))
        lines.append(
            f"{candidate.rank:>4}  {candidate.pair.key:<52}  {score if score is not None else '-':>5}  {codes}"
        )
    lines.append(
        f"{len(candidates)} candidate(s)" + (f"; {dropped} more below --limit, not written" if dropped else "")
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select the catalogue pairs an audit round looks at, read-only.")
    parser.add_argument("--out", type=Path, required=True, help="candidates.json, outside every git checkout")
    parser.add_argument("--ref", default="origin/main", help="the commit the catalogue is read from")
    parser.add_argument(
        "--repo", type=Path, default=catalogue.REPO_ROOT, help="the checkout whose git store holds --ref"
    )
    for source in SOURCES:
        parser.add_argument(f"--{source}", action="store_true", help=f"add the {source} source")
    parser.add_argument("--env", type=Path, default=catalogue.REPO_ROOT / ".env", help="the .env with DATABASE_URL")
    parser.add_argument("--min-down", type=int, default=1, help="thumbs down a pair needs (default 1)")
    parser.add_argument(
        "--below", type=float, default=85, help="flag a stored score below this (default 85; Opus reviews score lower)"
    )
    parser.add_argument("--older-than", type=int, metavar="DAYS", help="with --stale: flag an update older than this")
    parser.add_argument("--library", action="append", default=[], help="only this library (repeatable)")
    parser.add_argument("--language", action="append", default=[], help="only this language (repeatable)")
    parser.add_argument("--spec", action="append", default=[], help="only this spec (repeatable)")
    parser.add_argument("--specs-file", type=Path, help="only the specs listed in this file, one per line")
    parser.add_argument("--all", action="store_true", help="allow --sweep over the whole catalogue")
    parser.add_argument("--min-rank", type=int, default=1, help="leave out candidates ranked below this")
    parser.add_argument("--limit", type=int, help="write at most this many candidates (the rest are counted)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sources = [source for source in SOURCES if getattr(args, source)]
    if not sources:
        print("select_candidates: name at least one source: " + ", ".join(f"--{s}" for s in SOURCES), file=sys.stderr)
        return 2
    if not catalogue.outside_repository(args.out):
        print(f"select_candidates: {args.out} is inside a git checkout; a round's files stay outside", file=sys.stderr)
        return 2
    specs = set(args.spec)
    if args.specs_file:
        specs |= {line.strip() for line in args.specs_file.read_text(encoding="utf-8").splitlines() if line.strip()}
    if args.sweep and not (args.library or args.language or specs or args.all):
        print("select_candidates: --sweep needs --library, --language or --spec (or --all)", file=sys.stderr)
        return 2
    if args.votes and not use_database_url(args.env):
        print(f"select_candidates: DATABASE_URL is not set and {args.env} does not define it", file=sys.stderr)
        return 2

    tree = catalogue.GitTree(args.repo, args.ref)
    universe = [
        pair
        for pair in catalogue.pairs_from_paths(tree.paths())
        if in_universe(pair, libraries=set(args.library), languages=set(args.language), specs=specs)
    ]
    texts = tree.read_many([pair.metadata_path for pair in universe])
    candidates = {pair: Candidate(pair, catalogue.load_metadata(texts[pair.metadata_path])) for pair in universe}
    updated = {
        pair: catalogue.parse_time(c.metadata.get("updated") or c.metadata.get("created"))
        for pair, c in candidates.items()
    }
    now = datetime.now(UTC)
    print(
        f"universe: {len(universe)} pair(s) at {args.ref} ({tree.sha[:9]}); sources: {', '.join(sources)}",
        file=sys.stderr,
    )

    if args.votes:
        # The version boundary is `updated` alone, as `impls.updated` is for the API: without one, the pair has a
        # single version and every vote is on it. `created` stays the fallback of the render and age checks only.
        version_start = {pair: catalogue.parse_time(c.metadata.get("updated")) for pair, c in candidates.items()}
        counts = aggregate_votes(asyncio.run(read_votes()), version_start)
        for pair, count in counts.items():
            candidates[pair].votes = count
            candidates[pair].reasons += vote_reasons(count, min_down=args.min_down)
    if args.scores:
        for candidate in candidates.values():
            candidate.reasons += score_reasons(candidate.metadata, below=args.below)
    if args.stale:
        pinned, pin_errors = catalogue.pinned_libraries(tree)
        for error in pin_errors:
            print(f"select_candidates: no pin at {args.ref}: {error}", file=sys.stderr)
        older = timedelta(days=args.older_than) if args.older_than else None
        for pair, candidate in candidates.items():
            candidate.reasons += stale_reasons(
                candidate.metadata, pinned=pinned.get(pair.library), now=now, older_than=older
            )
    if args.gcs:
        heads = check_renders(universe, int(now.timestamp()))
        for pair, candidate in candidates.items():
            candidate.reasons += gcs_reasons(heads[pair], updated[pair])
    if args.readiness:
        code = tree.read_many([pair.impl_path for pair in universe])
        for pair, candidate in candidates.items():
            candidate.reasons += readiness_reasons(pair, code[pair.impl_path])
    if args.sweep:
        for candidate in candidates.values():
            candidate.reasons.append(Reason("sweep", "sweep", "in the swept universe"))

    chosen = [c for c in ranked(candidates.values()) if c.rank >= args.min_rank or args.sweep]
    dropped = max(0, len(chosen) - args.limit) if args.limit is not None else 0
    chosen = chosen[: args.limit] if args.limit is not None else chosen
    print(table(chosen, dropped=dropped))
    payload = {
        "selected_at": _iso(now),
        "ref": args.ref,
        "sha": tree.sha,
        "sources": sources,
        "options": {
            "below": args.below,
            "min_down": args.min_down,
            "older_than_days": args.older_than,
            "libraries": sorted(args.library),
            "languages": sorted(args.language),
            "specs": sorted(specs),
            "min_rank": args.min_rank,
            "limit": args.limit,
        },
        "universe": len(universe),
        "dropped_by_limit": dropped,
        "candidates": [candidate.to_json() for candidate in chosen],
    }
    catalogue.write_private(args.out, json.dumps(payload, indent=2) + "\n")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
