#!/usr/bin/env python3
"""Review retest harness: re-run the AI quality review on a frozen set.

The review rubric (``prompts/quality-criteria.md``, ``ai-quality-review.md``,
``default-style-guide.md``, the library prompts) and the review model decide
what reaches the catalogue, yet a change to them was observable only on real
pipeline runs. This harness re-reviews a frozen set of implementations and
regen pairs several times per item, so a rubric change can be measured as an
arm against a baseline before it merges: score spread, verdict flips, weakness
agreement, named-defect misses, false alarms, gate accuracy and order bias.

``.github/workflows/review-retest.yml`` drives it (dispatch-only, read-only
job tokens, one fresh Claude session per cell); ``docs/workflows/review-retest.md``
is the how-to. Each frozen set lives in two files next to this repository's
copy of the harness (``v1`` is the default; ``--manifest``/``--lock`` or the
workflow's ``set`` input pick another):

- ``automation/retest/set-v<N>.yaml`` -- the hand-curated manifest: items, the
  commits that pin their sources, where their renders come from, and labels.
- ``automation/retest/set-v<N>.lock.json`` -- written by ``freeze``: sha256,
  dimensions and pair pixel statistics of every frozen render. The renders
  themselves are public objects under ``gs://anyplot-images/retest/sets/v<N>/``
  and are downloaded anonymously over HTTPS.

Subcommands::

    validate   check the manifest (with --check-git, every pinned file; with
               --check-renders, every render's canvas from its PNG header)
    plan       resolve a subset into the matrix of cells (prep job)
    bundle     pinned sources via git + renders over HTTPS, sha256-checked (prep job)
    materialize  lay out one cell exactly as impl-review does (review job)
    collect    gather one cell's outputs into record.json (review job)
    report     aggregate the records into the report and the PR snippet (aggregate job)
    gate-report  local: aggregate production regen-gate records from PR comments
    first-reviews  local: aggregate the live reviews of first-generation PRs
    freeze     local: build the frozen set; dry run unless --execute

``materialize`` and ``collect`` run from a copy of ``automation/`` outside
the workspace, because the review job overlays ``prompts/`` and
``automation/scripts/regen_gate.py`` from the rules under test. Anything the
harness takes from the rules under test (the gate's ``context``,
``sanitize-source`` and ``decide``) is called by path with the flags every
revision since ``02e1a7974`` understands; a later addition (``decide
--record-out``, the ``marker`` subcommand, ``sanitize-source --pending``) is
never passed to an overlay, so the baseline rules (``0674ab6b5``) run
unchanged. What the harness needs beyond that — the header reset, the
characteristic kinds, the improvement classes, record-marker parsing — comes
from its own copy of ``regen_gate.py``. ``decide`` reads the review's
``review_checklist.json`` next to ``--regen-json`` by itself, so the harness
passes no new flag for it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from automation.scripts import review_provenance
from automation.scripts import review_retest_metrics as metrics
from automation.scripts.regen_gate import (
    WRITEBACK_CODES,
    GateInput,
    classify_improvements,
    improvement_class_counts,
    load_checklist_scores,
    load_weakness_classes,
    normalize_regen,
    parse_characteristics,
    parse_record_markers,
    permission_refs,
    reset_header_score,
)


# Bump when a harness change alters what a session sees or what a record
# measures: resume (split_resume) and compare_arms treat another version as
# another arm, and neither compares the dispatch commit.
HARNESS_VERSION = "1"
MAX_SESSIONS = 240
# First commit whose regen_gate.py has `context --omit-scores` (the blind
# re-score the harness reproduces); regen cells need rules at least this new.
GATE_MIN_COMMIT = "02e1a7974"
PIPELINE_WORKFLOWS = ("impl-generate.yml", "impl-review.yml", "impl-repair.yml", "bulk-generate.yml", "daily-regen.yml")
STALE_RUN_HOURS = 6
PUBLIC_BASE = "https://storage.googleapis.com/anyplot-images"
BUCKET = "gs://anyplot-images"
CANVASES = ((3200, 1800), (2400, 2400))
CANVAS_TOLERANCE = 16
THEMES = ("light", "dark")
# Mirrors impl-review.yml's review_model default; test_model_routing.py keeps
# them equal.
PRODUCTION_MODELS = {"fresh": "opus", "regen": "opus"}
# API-equivalent USD per session, measured on set v1 core at rules 0674ab6b5:
# fresh opus and regen sonnet in run 36354452853, fresh sonnet in 36359464410,
# regen opus in 36389481950. Haiku is still the plan P6 §7 estimate.
COST_ESTIMATE = {
    ("fresh", "sonnet"): 0.76,
    ("regen", "sonnet"): 0.98,
    ("fresh", "opus"): 2.14,
    ("regen", "opus"): 2.64,
    ("fresh", "haiku"): 0.20,
    ("regen", "haiku"): 0.30,
}
# Mirror of core.constants (LIBRARY_LANGUAGES / library_file_extension): the
# harness runs from a bare copy of automation/ on the runner. A unit test
# keeps the two in sync.
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
# The keys impl-generate.yml writes into a fresh metadata file ("Create
# library metadata file"); the harness resets a pinned file to exactly these.
IMPL_GENERATE_METADATA_KEYS = (
    "library",
    "language",
    "specification_id",
    "created",
    "updated",
    "generated_by",
    "workflow_run",
    "issue",
    "language_version",
    "library_version",
    "preview_url_light",
    "preview_url_dark",
    "preview_html_light",
    "preview_html_dark",
    "quality_score",
    "review",
)

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
KINDS = ("fresh", "regen")
TIERS = ("core", "full")
ORDERS = ("forward", "reversed")
VERDICTS = ("keep", "merge")
PAIR_CLASSES = ("identity", "near-identical", "different")
SPEC_SOURCES = ("pinned", "rules_ref")
CHARACTERISTICS_HEADING_RE = re.compile(r"^##\s+what a good version looks like\b", re.IGNORECASE | re.MULTILINE)


class HarnessError(RuntimeError):
    """A refusal or a broken input; the CLI prints it and exits 1."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def language_of(library: str) -> str:
    return LIBRARY_LANGUAGE[library]


def ext_of(library: str) -> str:
    return LIBRARY_EXT_OVERRIDES.get(library, LANGUAGE_EXT[language_of(library)])


def impl_path(spec_id: str, library: str) -> str:
    return f"plots/{spec_id}/implementations/{language_of(library)}/{library}{ext_of(library)}"


def metadata_path(spec_id: str, library: str) -> str:
    return f"plots/{spec_id}/metadata/{language_of(library)}/{library}.yaml"


def roles_of(item: dict[str, Any]) -> tuple[str, ...]:
    return ("new", "prev") if item["kind"] == "regen" else ("new",)


def object_path(manifest: dict[str, Any], item_id: str, role: str, theme: str) -> str:
    return f"{manifest['gcs_prefix']}/{item_id}/{role}-{theme}.png"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def png_size(data: bytes) -> tuple[int, int]:
    """Width and height from a PNG's IHDR chunk (stdlib only)."""
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise HarnessError("not a PNG file")
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def canonical_canvas(size: tuple[int, int]) -> bool:
    w, h = size
    return any(abs(w - tw) <= CANVAS_TOLERANCE and abs(h - th) <= CANVAS_TOLERANCE for tw, th in CANVASES)


def forward_only(item: dict[str, Any]) -> bool:
    """A regen pair that runs in the forward order only (``orders: forward``)."""
    return item["kind"] == "regen" and item.get("orders") == "forward"


def canvas_problem(item: dict[str, Any], role: str, size: tuple[int, int], where: str) -> str | None:
    """Why a frozen render's canvas is refused, or None.

    Every render a session reviews must be on a canonical canvas, as the
    production canvas gate requires before a review. A predecessor is shown
    as production stores it (impl-review downloads it unchecked), so the
    ``prev`` render of a forward-only pair may be off-canvas: in the reversed
    order it would be the version under review, which production's canvas
    gate keeps without a review.
    """
    if canonical_canvas(size) or (role == "prev" and forward_only(item)):
        return None
    hint = " — an off-canvas predecessor needs `orders: forward` on its pair" if role == "prev" else ""
    return f"{size[0]}x{size[1]} is not a canonical canvas ({where}){hint}"


def write_outputs(values: dict[str, str]) -> None:
    for key, value in values.items():
        if "\n" in value:
            raise HarnessError(f"output {key} spans several lines")
        print(f"{key}={value}")
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            for key, value in values.items():
                f.write(f"{key}={value}\n")


def load_yaml(path: Path) -> Any:
    import yaml  # PyYAML — the workflow installs it; stdlib everywhere else

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(data: Any) -> str:
    import yaml

    text: str = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return text


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def git_show(repo: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], capture_output=True)
    if result.returncode != 0:
        raise HarnessError(f"{path} does not exist at {commit[:10]}")
    return result.stdout


def is_ancestor(repo: Path, ancestor: str, commit: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", ancestor, commit], capture_output=True
        ).returncode
        == 0
    )


def http_get(url: str, *, attempts: int = 3, timeout: int = 60, first_bytes: int | None = None) -> bytes | None:
    """GET a public object; ``None`` on 404. Retries transient failures.

    With ``first_bytes``, asks for only that many leading bytes (an HTTP Range
    request) and never reads more, even from a server that ignores the range.
    """
    last: Exception | None = None
    request = urllib.request.Request(url, headers={"Range": f"bytes=0-{first_bytes - 1}"} if first_bytes else {})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data: bytes = response.read(first_bytes) if first_bytes else response.read()
                return data
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            last = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
        if attempt < attempts:
            time.sleep(2 * attempt)
    raise HarnessError(f"GET {url} failed: {last}")


# ---------------------------------------------------------------------------
# Manifest and lock
# ---------------------------------------------------------------------------


def _label_errors(where: str, labels: Any, criteria: Iterable[str], allowed: str = "known criterion ids") -> list[str]:
    known = set(criteria)
    errors: list[str] = []
    if labels is None:
        return errors
    if not isinstance(labels, list):
        return [f"{where} must be a list"]
    seen: set[str] = set()
    for i, label in enumerate(labels, start=1):
        at = f"{where}[{i}]"
        if not isinstance(label, dict):
            errors.append(f"{at} is not a mapping")
            continue
        lid = label.get("id")
        if not isinstance(lid, str) or not lid:
            errors.append(f"{at}.id is missing")
        elif lid in seen:
            errors.append(f"{at}.id {lid} is duplicated")
        else:
            seen.add(lid)
        crit = label.get("criteria")
        if not isinstance(crit, list) or not crit or any(c not in known for c in crit):
            errors.append(f"{at}.criteria must name {allowed} (got {crit!r})")
        try:
            re.compile(str(label.get("match") or ""))
        except re.error as exc:
            errors.append(f"{at}.match does not compile: {exc}")
        if not label.get("match"):
            errors.append(f"{at}.match is missing")
        if "spec_source" in label and label["spec_source"] not in SPEC_SOURCES:
            errors.append(f"{at}.spec_source must be one of {', '.join(SPEC_SOURCES)}")
    return errors


def _role_errors(where: str, role: Any) -> list[str]:
    if not isinstance(role, dict):
        return [f"{where} is missing"]
    errors = []
    if not SHA_RE.match(str(role.get("commit") or "")):
        errors.append(f"{where}.commit must be a full 40-hex commit")
    render = role.get("render")
    if render != "production" and not (isinstance(render, dict) and isinstance(render.get("snapshot"), str)):
        errors.append(f"{where}.render must be 'production' or {{snapshot: <dir>}}")
    return errors


def validate_manifest(manifest: Any) -> list[str]:
    """Schema of the set manifest; returns every error found."""
    if not isinstance(manifest, dict):
        return ["manifest is not a mapping"]
    errors: list[str] = []
    if manifest.get("version") != 1:
        errors.append("version must be 1")
    set_name = str(manifest.get("set") or "")
    if not re.fullmatch(r"v\d+", set_name):
        errors.append("set must look like v1")
    if manifest.get("gcs_prefix") != f"retest/sets/{set_name}":
        errors.append(f"gcs_prefix must be retest/sets/{set_name}")
    for key in ("baseline_rules_sha", "spec_commit"):
        if not SHA_RE.match(str(manifest.get(key) or "")):
            errors.append(f"{key} must be a full 40-hex commit")
    labels_state = manifest.get("labels")
    if labels_state not in ("draft", "confirmed"):
        errors.append("labels must be draft or confirmed")
    items = manifest.get("items")
    if not isinstance(items, list) or not items:
        return [*errors, "items must be a non-empty list"]
    seen: set[str] = set()
    for i, item in enumerate(items, start=1):
        at = f"items[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{at} is not a mapping")
            continue
        iid = str(item.get("id") or "")
        at = f"item {iid or i}"
        if not ID_RE.match(iid):
            errors.append(f"{at}: id must match {ID_RE.pattern}")
        if iid in seen:
            errors.append(f"{at}: duplicate id")
        seen.add(iid)
        kind = item.get("kind")
        if kind not in KINDS:
            errors.append(f"{at}: kind must be fresh or regen")
            continue
        if item.get("tier") not in TIERS:
            errors.append(f"{at}: tier must be core or full")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(item.get("spec_id") or "")):
            errors.append(f"{at}: spec_id is missing or malformed")
        if item.get("library") not in LIBRARY_LANGUAGE:
            errors.append(f"{at}: unknown library {item.get('library')!r}")
        if "spec_commit" in item and not SHA_RE.match(str(item["spec_commit"])):
            errors.append(f"{at}: spec_commit must be a full 40-hex commit")
        for role in roles_of(item):
            errors += _role_errors(f"{at}: {role}", item.get(role))
        if kind == "fresh" and "prev" in item:
            errors.append(f"{at}: a fresh item has no prev")
        if "orders" in item and (kind != "regen" or item["orders"] not in ("both", "forward")):
            errors.append(f"{at}: orders is both or forward, on a regen pair only")
        if kind == "regen":
            cls = item.get("class")
            if cls not in PAIR_CLASSES:
                errors.append(f"{at}: class must be one of {', '.join(PAIR_CLASSES)}")
            elif cls == "identity" and item.get("new") != item.get("prev"):
                errors.append(f"{at}: an identity pair needs the same commit and render for new and prev")
            expected = item.get("expected")
            if expected is None:
                if labels_state == "confirmed":
                    errors.append(f"{at}: confirmed labels need expected verdicts for both orders")
            elif not isinstance(expected, dict) or any(expected.get(o) not in VERDICTS for o in ORDERS):
                errors.append(f"{at}: expected must give keep|merge for forward and reversed")
        errors += _label_errors(f"{at}: defects", item.get("defects"), metrics.CRITERIA_IDS)
        errors += _label_errors(f"{at}: permitted", item.get("permitted"), metrics.CRITERIA_IDS)
        if "fixes" in item:
            # Predecessor defects the forward new version fixes: regen pairs
            # only, and only criteria that can carry a merge (never DE or LM).
            if kind == "fresh":
                errors.append(f"{at}: a fresh item has no fixes")
            elif item["fixes"] is None:
                errors.append(f"{at}: fixes must be a list ([] when the new version fixes no defect)")
            errors += _label_errors(
                f"{at}: fixes", item["fixes"], metrics.CARRIER_CRITERIA, "carrier criterion ids (VQ, SC, DQ or CQ)"
            )
    return errors


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = load_yaml(path)
    errors = validate_manifest(manifest)
    if errors:
        raise HarnessError("invalid manifest:\n  " + "\n  ".join(errors))
    result: dict[str, Any] = manifest
    return result


def load_lock(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise HarnessError(
            f"{path} does not exist: set {manifest['set']} is not frozen yet "
            "(run `review_retest.py freeze`, see docs/workflows/review-retest.md)"
        )
    lock: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("set") != manifest["set"]:
        raise HarnessError(f"{path} belongs to set {lock.get('set')!r}, not {manifest['set']!r}")
    for obj, meta in (lock.get("objects") or {}).items():
        if not SHA256_RE.match(str((meta or {}).get("sha256") or "")):
            raise HarnessError(f"lock entry {obj} has no valid sha256")
    return lock


def item_labels(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Per-item labels the metrics apply at report time.

    Defects, permission probes, fixes and expected verdicts count only once
    the owner has confirmed them (``labels: confirmed``). Draft proposals are
    validated with the manifest but never reach a report, so no PR body quotes
    a miss rate against unconfirmed ground truth. ``fixes`` stays ``None`` for
    an item without the key, which leaves it out of ``merges_without_carrier``;
    ``[]`` labels a pair whose new version fixes no defect. The pair ``class``
    is measured (pixel statistics in the lock), not a label, and always
    applies.
    """
    confirmed = manifest.get("labels") == "confirmed"
    return {
        item["id"]: {
            "defects": (item.get("defects") or []) if confirmed else [],
            "permitted": (item.get("permitted") or []) if confirmed else [],
            "fixes": item.get("fixes") if confirmed and isinstance(item.get("fixes"), list) else None,
            "expected": (item.get("expected") or {}) if confirmed else {},
            "class": item.get("class"),
        }
        for item in manifest["items"]
    }


def check_git(manifest: dict[str, Any], repo: Path) -> list[str]:
    """Every pinned source exists at its commit."""
    missing = []
    for item in manifest["items"]:
        spec_commit = item.get("spec_commit") or manifest["spec_commit"]
        paths = [(spec_commit, f"plots/{item['spec_id']}/specification.md")]
        for role in roles_of(item):
            commit = item[role]["commit"]
            paths += [
                (commit, impl_path(item["spec_id"], item["library"])),
                (commit, metadata_path(item["spec_id"], item["library"])),
            ]
        for commit, path in paths:
            ok = subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{commit}:{path}"], capture_output=True)
            if ok.returncode != 0:
                missing.append(f"{item['id']}: {path} @ {commit[:10]}")
    return missing


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------


RunLister = Callable[[str, str], list[dict[str, Any]]]


def gh_run_lister(workflow: str, status: str) -> list[dict[str, Any]]:
    """Runs of one workflow in one status. A failed listing refuses the run: an
    idle check that cannot see the pipeline must not pass."""
    result = subprocess.run(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            workflow,
            "--status",
            status,
            "--limit",
            "50",
            "--json",
            "databaseId,createdAt",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HarnessError(f"cannot list {workflow} runs for the idle check: {result.stderr.strip()[-300:]}")
    runs: list[dict[str, Any]] = json.loads(result.stdout or "[]")
    return runs


def busy_pipeline_runs(lister: RunLister, now: datetime) -> list[str]:
    """Pipeline runs that are queued, or in progress for less than STALE_RUN_HOURS.

    Older in-progress runs are ignored: a run stuck for hours (GitHub keeps a
    few of those around indefinitely) does not use the review budget.
    """
    busy = []
    cutoff = now - timedelta(hours=STALE_RUN_HOURS)
    for workflow in PIPELINE_WORKFLOWS:
        for status in ("queued", "in_progress"):
            for run in lister(workflow, status):
                try:
                    created = datetime.fromisoformat(str(run.get("createdAt", "")).replace("Z", "+00:00"))
                except ValueError:
                    created = now  # unknown age counts as busy
                if status == "in_progress" and created < cutoff:
                    continue
                busy.append(f"{workflow} run {run.get('databaseId')} ({status} since {run.get('createdAt')})")
    return busy


def resolve_subset(manifest: dict[str, Any], subset: str) -> list[dict[str, Any]]:
    items = manifest["items"]
    subset = subset.strip()
    if subset == "core":
        return [i for i in items if i["tier"] == "core"]
    if subset == "full":
        return list(items)
    wanted = [s.strip() for s in subset.split(",") if s.strip()]
    by_id = {i["id"]: i for i in items}
    unknown = [w for w in wanted if w not in by_id]
    if unknown or not wanted:
        raise HarnessError(f"unknown item id(s) in subset: {', '.join(unknown) or '(empty)'}")
    return [by_id[w] for w in wanted]


def model_for(kind: str, models: str) -> str:
    if models == "production":
        return PRODUCTION_MODELS[kind]
    if models in ("sonnet", "opus", "haiku"):
        return models
    raise HarnessError(f"models must be production, sonnet, opus or haiku (got {models!r})")


def cell_id(item_id: str, order: str | None, run: int) -> str:
    parts = [item_id]
    if order:
        parts.append("fwd" if order == "forward" else "rev")
    parts.append(f"r{run}")
    return "__".join(parts)


def build_cells(
    manifest: dict[str, Any], items: Sequence[dict[str, Any]], models: str, runs: int, orders: str
) -> list[dict[str, Any]]:
    """Run-major: every item's run 1 comes before any run 2 (best effort — the
    matrix scheduler starts jobs roughly in list order). A forward-only pair
    (``orders: forward`` in the manifest) never gets a reversed cell."""
    if orders not in ("both", "forward"):
        raise HarnessError("orders must be both or forward")
    cells = []
    for run in range(1, runs + 1):
        for item in items:
            item_orders: tuple[str | None, ...]
            if item["kind"] != "regen":
                item_orders = (None,)
            elif orders == "both" and not forward_only(item):
                item_orders = ORDERS
            else:
                item_orders = ("forward",)
            for order in item_orders:
                cells.append(
                    {
                        "id": cell_id(item["id"], order, run),
                        "set": manifest["set"],
                        "item": item["id"],
                        "kind": item["kind"],
                        "tier": item["tier"],
                        "spec_id": item["spec_id"],
                        "library": item["library"],
                        "order": order or "",
                        "run": run,
                        "model": model_for(item["kind"], models),
                    }
                )
    return cells


def estimate_cost(cells: Sequence[dict[str, Any]]) -> float:
    return sum(COST_ESTIMATE.get((c["kind"], c["model"]), 1.0) for c in cells)


def load_records(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _provenance_text(value: Any) -> str:
    if value in (None, ""):
        return "missing"
    text = str(value)
    return text[:10] if re.fullmatch(r"[0-9a-f]{40}", text) else text


def split_resume(
    records: Sequence[dict[str, Any]], cells: Sequence[dict[str, Any]], arm: dict[str, str]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]], int]:
    """Which successful resumed records may stand in for a planned cell.

    A record fills its cell only when it was measured the way this arm
    measures: the same ``arm`` values (set, harness version, action pin,
    rules commit, spec source) and the cell's own model alias. The cell id
    already fixes the item, the order and the run, so ``orders`` and ``runs``
    change which cells exist, never what one means. The dispatch commit
    (``harness_sha``) is not compared: ``main`` moves with every merge, and
    ``HARNESS_VERSION`` plus the action pin are the harness's measurement
    identity, the same pair ``compare_arms`` flags as "harness changed". A
    missing or ``n/a`` value never matches.

    Returns the accepted records by cell id, the rejected ones with their
    reason, and how many successful records name a cell outside this plan.
    """
    by_id = {c["id"]: c for c in cells}
    accepted: dict[str, dict[str, Any]] = {}
    rejected: list[dict[str, str]] = []
    unused = 0
    for record in records:
        if not record.get("ok"):
            continue
        cell = by_id.get(str(record.get("cell")))
        if cell is None:
            unused += 1
            continue
        expected = {**arm, "model_alias": cell["model"]}
        diffs = [
            f"{field} {_provenance_text(record.get(field))} != {_provenance_text(value)}"
            for field, value in expected.items()
            if value in (None, "", "n/a") or record.get(field) != value
        ]
        if diffs:
            rejected.append({"cell": cell["id"], "reason": "; ".join(diffs)})
        else:
            accepted[cell["id"]] = record
    return accepted, rejected, unused


def plan(
    manifest: dict[str, Any],
    *,
    subset: str,
    models: str,
    runs: int,
    orders: str,
    rules_sha: str,
    repo: Path,
    lister: RunLister | None,
    resume_records: Sequence[dict[str, Any]] = (),
    action_sha: str = "n/a",
    spec_source: str = "pinned",
    now: datetime | None = None,
    ancestor: Callable[[Path, str, str], bool] | None = None,
) -> dict[str, Any]:
    """Resolve the subset into cells, or refuse (HarnessError) with the reason."""
    ancestor = ancestor or is_ancestor
    if not 1 <= runs <= 10:
        raise HarnessError("runs must be between 1 and 10")
    items = resolve_subset(manifest, subset)
    cells = build_cells(manifest, items, models, runs, orders)
    arm = {
        "set": manifest["set"],
        "harness_version": HARNESS_VERSION,
        "action_sha": action_sha,
        "rules_sha": rules_sha,
        "spec_source": spec_source,
    }
    resumed, rejected, unused = split_resume(resume_records, cells, arm)
    resumed_ids = [c["id"] for c in cells if c["id"] in resumed]
    cells = [c for c in cells if c["id"] not in resumed]
    if len(cells) > MAX_SESSIONS:
        raise HarnessError(f"{len(cells)} sessions exceed the cap of {MAX_SESSIONS}; narrow the subset or the runs")
    if any(c["kind"] == "regen" for c in cells) and not ancestor(repo, GATE_MIN_COMMIT, rules_sha):
        raise HarnessError(
            f"rules_ref {rules_sha[:10]} predates {GATE_MIN_COMMIT} (no regen_gate.py --omit-scores to reproduce "
            "the blind re-score): measure fresh items only"
        )
    if lister is not None and cells:
        busy = busy_pipeline_runs(lister, now or datetime.now(timezone.utc))
        if busy:
            raise HarnessError(
                "the production pipeline is busy and shares the Claude usage window — retry when it is idle:\n  "
                + "\n  ".join(busy)
            )
    needed = sorted({c["item"] for c in cells}, key=[i["id"] for i in manifest["items"]].index)
    return {
        "cells": cells,
        "items": needed,
        "resumed": len(resumed_ids),
        "resumed_cells": resumed_ids,
        "resume_rejected": rejected,
        "resume_unused": unused,
        "sessions": len(cells),
        "by_model": {
            f"{kind}/{model}": sum(1 for c in cells if (c["kind"], c["model"]) == (kind, model))
            for kind, model in sorted({(c["kind"], c["model"]) for c in cells})
        },
        "estimate_usd": round(estimate_cost(cells), 2),
    }


# ---------------------------------------------------------------------------
# bundle
# ---------------------------------------------------------------------------


def bundle_item(
    manifest: dict[str, Any],
    lock: dict[str, Any],
    item: dict[str, Any],
    out_dir: Path,
    repo: Path,
    fetch: Callable[[str], bytes | None] = http_get,
) -> Path:
    """One item's pinned sources and verified renders under ``out_dir/<id>/``."""
    target: Path = out_dir / str(item["id"])
    if target.exists():
        shutil.rmtree(target)
    spec_id, library = item["spec_id"], item["library"]
    spec_commit = item.get("spec_commit") or manifest["spec_commit"]
    (target / "spec").mkdir(parents=True)
    spec_md = git_show(repo, spec_commit, f"plots/{spec_id}/specification.md")
    (target / "spec" / "specification.md").write_bytes(spec_md)
    try:
        (target / "spec" / "specification.yaml").write_bytes(
            git_show(repo, spec_commit, f"plots/{spec_id}/specification.yaml")
        )
    except HarnessError:
        pass  # optional for the review
    canvas: dict[str, list[int]] = {}
    for role in roles_of(item):
        commit = item[role]["commit"]
        role_dir = target / role
        role_dir.mkdir()
        (role_dir / f"{library}{ext_of(library)}").write_bytes(git_show(repo, commit, impl_path(spec_id, library)))
        (role_dir / "metadata.yaml").write_bytes(git_show(repo, commit, metadata_path(spec_id, library)))
        for theme in THEMES:
            obj = object_path(manifest, item["id"], role, theme)
            expected = (lock.get("objects") or {}).get(obj)
            if not expected:
                raise HarnessError(f"{obj} is not in the lock — re-run freeze")
            data = fetch(f"{PUBLIC_BASE}/{obj}")
            if data is None:
                raise HarnessError(f"{obj} is missing from the bucket — upload the frozen set first")
            if sha256_bytes(data) != expected["sha256"]:
                raise HarnessError(f"{obj}: sha256 mismatch against the lock")
            size = png_size(data)
            problem = canvas_problem(item, role, size, "frozen object")
            if problem:
                raise HarnessError(f"{obj}: {problem}")
            (role_dir / f"plot-{theme}.png").write_bytes(data)
            canvas[f"{role}-{theme}"] = list(size)
    info = {
        "id": item["id"],
        "kind": item["kind"],
        "tier": item["tier"],
        "spec_id": spec_id,
        "library": library,
        "language": language_of(library),
        "ext": ext_of(library),
        "commits": {role: item[role]["commit"] for role in roles_of(item)},
        "spec_commit": spec_commit,
        "seeded": bool(CHARACTERISTICS_HEADING_RE.search(spec_md.decode("utf-8", "replace"))),
        "class": item.get("class"),
        "canvas": canvas,
    }
    (target / "item.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# materialize (review job)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TmpPaths:
    """The /tmp files impl-review writes for a regeneration (base parametrized for tests)."""

    base: Path

    @property
    def prev_light(self) -> Path:
        return self.base / "anyplot-prev-plot-light.png"

    @property
    def prev_dark(self) -> Path:
        return self.base / "anyplot-prev-plot-dark.png"

    @property
    def prev_metadata(self) -> Path:
        return self.base / "anyplot-prev-metadata.yaml"

    @property
    def prev_review(self) -> Path:
        return self.base / "anyplot-prev-review.md"

    @property
    def prev_weaknesses(self) -> Path:
        return self.base / "anyplot-prev-weaknesses.json"

    def prev_impl(self, ext: str) -> Path:
        return self.base / f"anyplot-prev-impl{ext}"

    @property
    def canvas_gate(self) -> Path:
        return self.base / "anyplot-canvas-gate.txt"

    @property
    def change_request(self) -> Path:
        return self.base / "anyplot-change-request.txt"

    @property
    def regen_gate(self) -> Path:
        """The gate copy the review prompt's step-10 self-check runs (impl-review "Checkout PR code")."""
        return self.base / "anyplot-regen-gate.py"


def reset_metadata(stored: dict[str, Any], spec_id: str, library: str) -> str:
    """The metadata file impl-generate.yml writes before a review: the stored
    identity and version fields, ``quality_score: None`` and an empty review."""
    data = {key: stored.get(key) for key in IMPL_GENERATE_METADATA_KEYS}
    data["library"] = library
    data["language"] = language_of(library)
    data["specification_id"] = spec_id
    data["quality_score"] = None
    data["review"] = {"strengths": [], "weaknesses": []}
    header = (
        f"# Per-library metadata for {library} implementation of {spec_id}\n# Auto-generated by impl-generate.yml\n\n"
    )
    return header + dump_yaml(data)


def _run_gate(gate_script: Path, args: Sequence[str], python: str = sys.executable) -> dict[str, str]:
    """Run the rules-under-test gate script; parse its ``key=value`` stdout lines."""
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_OUTPUT"}
    result = subprocess.run([python, str(gate_script), *args], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise HarnessError(f"regen_gate.py {args[0]} failed: {result.stderr.strip()[-500:]}")
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if line.startswith("::"):
            continue
        key, sep, value = line.partition("=")
        if sep and re.fullmatch(r"[a-z_]+", key):
            values[key] = value
    return values


def _line_count(path: Path) -> int:
    return path.read_bytes().count(b"\n")


def materialize(
    bundle_dir: Path,
    workspace: Path,
    cell: dict[str, Any],
    gate_script: Path,
    *,
    spec_source: str = "pinned",
    tmp: TmpPaths | None = None,
) -> dict[str, str]:
    """Lay the cell out exactly as impl-review sees a PR; returns the prompt variables.

    The file under review gets ``Quality: pending`` in every arm (the state
    impl-generate leaves since M3), and every cell gets the rules-under-test
    gate script at ``tmp.regen_gate`` for the review's self-check (an older
    arm's prompt never calls it). A regen cell also gets the predecessor's
    renders, stored review (``context --omit-scores``) and sanitized source
    under /tmp, produced by the same gate script.
    """
    tmp = tmp or TmpPaths(Path("/tmp"))
    info = json.loads((bundle_dir / "item.json").read_text(encoding="utf-8"))
    spec_id, library = info["spec_id"], info["library"]
    lang, ext = info["language"], info["ext"]
    regen = info["kind"] == "regen"
    order = cell.get("order") or ""
    if regen and order not in ORDERS:
        raise HarnessError(f"regen cell {cell.get('id')} has no order")
    subject, predecessor = ("prev", "new") if order == "reversed" else ("new", "prev")

    # A stale file must never stand in for this run's output.
    for stale in [*workspace.glob("review_*"), workspace / "quality_score.txt", workspace / "review_comment.md"]:
        if stale.is_file():
            stale.unlink()
    for path in (tmp.canvas_gate, tmp.change_request, tmp.prev_light, tmp.prev_dark, tmp.prev_impl(ext)):
        path.unlink(missing_ok=True)
    tmp.base.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(gate_script, tmp.regen_gate)

    plots = workspace / "plots" / spec_id
    if spec_source == "pinned":
        plots.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(bundle_dir / "spec" / "specification.md", plots / "specification.md")
        if (bundle_dir / "spec" / "specification.yaml").is_file():
            shutil.copyfile(bundle_dir / "spec" / "specification.yaml", plots / "specification.yaml")
    elif spec_source != "rules_ref":
        raise HarnessError("spec_source must be pinned or rules_ref")

    impl = workspace / impl_path(spec_id, library)
    impl.parent.mkdir(parents=True, exist_ok=True)
    source = (bundle_dir / subject / f"{library}{ext}").read_text(encoding="utf-8")
    impl.write_text(reset_header_score(source), encoding="utf-8")

    meta = workspace / metadata_path(spec_id, library)
    meta.parent.mkdir(parents=True, exist_ok=True)
    stored = load_yaml(bundle_dir / subject / "metadata.yaml") or {}
    meta.write_text(reset_metadata(stored, spec_id, library), encoding="utf-8")

    images = workspace / "plot_images"
    images.mkdir(exist_ok=True)
    for theme in THEMES:
        shutil.copyfile(bundle_dir / subject / f"plot-{theme}.png", images / f"plot-{theme}.png")

    outputs = {
        "spec_id": spec_id,
        "library": library,
        "language": lang,
        "ext": ext,
        "subject": subject,
        "is_regen": "true" if regen else "false",
        "prev_renders": "missing",
        "prev_light": "n/a",
        "prev_dark": "n/a",
        "prev_lines": "n/a",
        "new_lines": "n/a",
        "prev_stored": "n/a",
    }
    if not regen:
        return outputs

    shutil.copyfile(bundle_dir / predecessor / "plot-light.png", tmp.prev_light)
    shutil.copyfile(bundle_dir / predecessor / "plot-dark.png", tmp.prev_dark)
    shutil.copyfile(bundle_dir / predecessor / "metadata.yaml", tmp.prev_metadata)
    ctx = _run_gate(
        gate_script,
        [
            "context",
            "--metadata",
            str(tmp.prev_metadata),
            "--spec-id",
            spec_id,
            "--language",
            lang,
            "--library",
            library,
            "--spec-file",
            str(plots / "specification.md"),
            "--omit-scores",
            "--out-md",
            str(tmp.prev_review),
            "--out-weaknesses",
            str(tmp.prev_weaknesses),
        ],
    )
    raw = tmp.base / "anyplot-prev-impl-raw"
    shutil.copyfile(bundle_dir / predecessor / f"{library}{ext}", raw)
    try:
        _run_gate(gate_script, ["sanitize-source", "--source", str(raw), "--out", str(tmp.prev_impl(ext))])
    finally:
        raw.unlink(missing_ok=True)
    outputs.update(
        {
            "prev_renders": "available",
            "prev_light": str(tmp.prev_light),
            "prev_dark": str(tmp.prev_dark),
            "prev_lines": str(_line_count(tmp.prev_impl(ext))),
            "new_lines": str(_line_count(impl)),
            "prev_stored": ctx.get("prev_stored", "n/a"),
        }
    )
    return outputs


# ---------------------------------------------------------------------------
# collect (review job)
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> tuple[Any, str | None]:
    if not path.is_file():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as exc:
        return None, f"unreadable ({str(exc)[:120]})"


def _score(path: Path) -> int | None:
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return int(raw) if re.fullmatch(r"\d{1,3}", raw) and int(raw) <= 100 else None


def flatten_checklist(checklist: Any) -> dict[str, dict[str, Any]]:
    """``{criterion id: {"score", "max", "comment"}}`` from review_checklist.json."""
    flat: dict[str, dict[str, Any]] = {}
    if not isinstance(checklist, dict):
        return flat
    for category in checklist.values():
        items = category.get("items") if isinstance(category, dict) else None
        for item in items or []:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] in flat:
                continue
            score, top = item.get("score"), item.get("max")
            if isinstance(score, bool) or isinstance(top, bool):
                continue
            if isinstance(score, int | float) and isinstance(top, int | float):
                flat[item["id"]] = {"score": score, "max": top, "comment": str(item.get("comment") or "")}
    return flat


def checklist_sum(flat: dict[str, dict[str, Any]]) -> int | None:
    """Sum of the canonical items, each clamped to [0, max] and floored (the
    harness's stand-in until P1 exposes the workflow's own computation)."""
    items = [flat[c] for c in metrics.CRITERIA_IDS if c in flat]
    if not items:
        return None
    return int(sum(int(max(0, min(float(i["score"]), float(i["max"])))) for i in items))


def _strings(value: Any) -> list[str]:
    return [str(v) for v in value if str(v).strip()] if isinstance(value, list) else []


def improvement_counts(
    regen: Any, spec_text: str, prev_weaknesses: Path | None = None, checklist: Path | None = None
) -> dict[str, Any] | None:
    """The improvement counts a production gate record carries, for one cell.

    ``total`` is every listed improvement, ``permission`` those whose ref is an
    "Expected, not a defect" bullet of the spec the reviewer saw, ``obsolete``
    the previous weaknesses the review classed obsolete, and ``visible`` only
    the counted ones (neither of the two) with a non-empty ``where_visible``;
    ``carriers`` + ``suggestion`` == ``visible``; ``unverified``, ``de_lm``,
    ``addition``, ``polish`` and ``no_kind`` are disjoint subsets of
    ``suggestion``, ``carriers_pn`` a subset of ``carriers``, and ``by_kind``
    the kind histogram over every listed item — the gate record's
    ``improvements`` semantics (``improvement_class_counts``, the gate's own
    function, without the per-ref counts). Computed with the harness's own
    ``classify_improvements``, so it works under any rules_ref, from the
    cell's ``prev_weaknesses`` JSON (the stored classes) and the review's own
    ``checklist``. A review under older rules writes no classification, so
    every ``W`` counts as a suggestion there; a spec without kind prefixes has
    no permissions. ``None`` when ``review_regen.json`` lists no
    improvements. Refs are judged after the gate's own ``normalize_regen``
    (``c2`` counts as ``C2``). One divergence is deliberate: a payload the
    gate rejects as ``regen_json_invalid`` (its record zeroes the counts) is
    still counted here, item by item — mirroring ``validate_regen`` is not
    worth it.
    """
    if not isinstance(regen, dict) or not isinstance(regen.get("improvements"), list):
        return None
    normalized, _ = normalize_regen(regen)  # the gate judges the coerced payload (c2 -> C2)
    characteristics = parse_characteristics(spec_text)
    inp = GateInput(
        spec_id="",
        score=None,
        regen=None,
        characteristic_count=len(characteristics),
        permission_refs=permission_refs(characteristics),
        weakness_classes=load_weakness_classes(prev_weaknesses),
        new_checklist=load_checklist_scores(checklist),
    )
    return improvement_class_counts(classify_improvements(normalized, inp))


def characteristics_summary(spec_text: str) -> dict[str, Any] | None:
    """How many characteristic bullets the spec the reviewer saw has, and which
    are "Expected, not a defect" bullets — the rest are affirmative, as the
    gate reads them. The report needs it to tell an affirmative C id from a
    permission (``merges_without_carrier``) without the spec at hand. ``None``
    when the spec could not be read (empty text): the characteristics are then
    unknown, not absent, and ``carrier_claimed`` leaves the record out."""
    if not spec_text:
        return None
    items = parse_characteristics(spec_text)
    return {"count": len(items), "permission": sorted(permission_refs(items), key=lambda ref: int(ref[1:]))}


def collect(
    workspace: Path,
    cell: dict[str, Any],
    out_dir: Path,
    *,
    execution_file: str,
    review_outcome: str,
    materialize_ok: bool,
    gate_script: Path,
    prev_stored: str,
    tmp: TmpPaths | None = None,
    started_at: float = 0.0,
    timeout_minutes: float = 25,
    provenance: dict[str, str] | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Copy one cell's review files and write ``record.json`` (never the transcript)."""
    tmp = tmp or TmpPaths(Path("/tmp"))
    files = out_dir / "files"
    files.mkdir(parents=True, exist_ok=True)
    candidates = [*sorted(workspace.glob("review_*")), workspace / "quality_score.txt", workspace / "review_comment.md"]
    for path in candidates:
        if path.is_file() and path.stat().st_size <= 2_000_000:
            shutil.copyfile(path, files / path.name)

    # The alias the session was started with is kept apart as ``model_alias``;
    # ``model`` is the id the execution file resolved, or None. An alias moves
    # between releases and must never pass for a resolved id.
    alias = str(cell.get("model") or "")
    summary = review_provenance.execution_summary(execution_file or None)
    score = _score(workspace / "quality_score.txt")
    checklist_raw, _ = _read_json(workspace / "review_checklist.json")
    flat = flatten_checklist(checklist_raw)
    weaknesses_raw, _ = _read_json(workspace / "review_weaknesses.json")
    strengths_raw, _ = _read_json(workspace / "review_strengths.json")
    regen, regen_error = (None, None)
    gate = None
    counts = None
    spec_characteristics = None
    is_regen = cell.get("kind") == "regen"
    if is_regen:
        regen, regen_error = _read_json(workspace / "review_regen.json")
        spec_file = workspace / "plots" / str(cell["spec_id"]) / "specification.md"
        try:
            spec_text = spec_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            spec_text = ""
        counts = improvement_counts(regen, spec_text, tmp.prev_weaknesses, workspace / "review_checklist.json")
        spec_characteristics = characteristics_summary(spec_text)
        if score is not None and materialize_ok:
            try:
                out = _run_gate(
                    gate_script,
                    [
                        "decide",
                        "--spec-id",
                        str(cell["spec_id"]),
                        "--library",
                        str(cell["library"]),
                        "--score",
                        str(score),
                        "--prev-stored",
                        prev_stored or "n/a",
                        "--regen-json",
                        str(workspace / "review_regen.json"),
                        "--weaknesses-json",
                        str(tmp.prev_weaknesses),
                        "--spec-file",
                        str(spec_file),
                        "--prev-renders",
                        "available",
                    ],
                )
                rescored = out.get("prev_rescored", "n/a")
                gate = {
                    "verdict": out.get("verdict"),
                    "prev_rescored": int(rescored) if rescored.isdigit() else None,
                    "code": out.get("code"),
                    "reason": out.get("reason"),
                }
            except HarnessError as exc:
                gate = {"verdict": None, "prev_rescored": None, "code": "harness_error", "reason": str(exc)[:300]}

    elapsed = (now if now is not None else time.time()) - started_at if started_at else 0.0
    timed_out = elapsed >= 0.95 * timeout_minutes * 60 or review_outcome == "cancelled"
    if not materialize_ok:
        error_class = "harness"
    elif summary["error_class"] == "quota":
        error_class = "quota"
    elif summary["error_class"] == "no_result" and review_outcome != "success" and timed_out:
        error_class = "timeout"
    elif score is None:
        error_class = summary["error_class"] or "no_output"
    else:
        error_class = ""

    prov = provenance or {}
    record: dict[str, Any] = {
        "v": 1,
        "harness_version": HARNESS_VERSION,
        "set": cell.get("set"),
        "cell": cell["id"],
        "item": cell["item"],
        "kind": cell["kind"],
        "tier": cell.get("tier"),
        "order": cell.get("order") or None,
        "run": cell.get("run"),
        "spec_id": cell.get("spec_id"),
        "library": cell.get("library"),
        "model_alias": alias,
        "model": summary["model"],
        "criteria_version": prov.get("criteria_version", "n/a"),
        "prompts_tree": prov.get("prompts_tree", "n/a"),
        "harness_sha": prov.get("harness_sha", "n/a"),
        "rules_sha": prov.get("rules_sha", "n/a"),
        "action_sha": prov.get("action_sha", "n/a"),
        "spec_source": prov.get("spec_source", "n/a"),
        "ok": error_class == "",
        "error_class": error_class,
        "review_outcome": review_outcome,
        "cost_usd": summary["cost_usd"],
        "turns": summary["turns"],
        "duration_ms": summary["duration_ms"],
        "result_subtype": summary["result_subtype"],
        "score_typed": score,
        "checklist": flat,
        "checklist_sum": checklist_sum(flat),
        "auto_reject": score == 0,
        "weaknesses": _strings(weaknesses_raw),
        "strengths": _strings(strengths_raw),
        "regen": regen if isinstance(regen, dict) else None,
        "regen_error": regen_error if is_regen else None,
        "regen_counts": counts,
        "spec_characteristics": spec_characteristics,
        "gate": gate,
        "prev_stored": int(prev_stored) if (prev_stored or "").isdigit() else None,
        "comment_written": (workspace / "review_comment.md").is_file(),
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (out_dir / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


# ---------------------------------------------------------------------------
# report (aggregate job)
# ---------------------------------------------------------------------------


def load_cell_records(cells_dir: Path) -> list[dict[str, Any]]:
    paths = sorted(cells_dir.glob("*/record.json")) + sorted(cells_dir.glob("record.json"))
    records = []
    for path in paths:
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return records


def merge_records(resumed: Sequence[dict[str, Any]], fresh: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resumed cells first; a cell re-run in this arm replaces its resumed record."""
    by_cell: dict[str, dict[str, Any]] = {}
    for record in [*resumed, *fresh]:
        previous = by_cell.get(record["cell"])
        if previous is None or record.get("ok") or not previous.get("ok"):
            by_cell[record["cell"]] = record
    return sorted(by_cell.values(), key=lambda r: (r.get("run") or 0, str(r["cell"])))


def _fmt(value: Any, digits: int = 1) -> str:
    if value is None:
        return "–"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _pct(value: float | None) -> str:
    return "–" if value is None else f"{value:.0%}"


def _ci(ci: Any, digits: int = 1) -> str:
    return "" if not ci else f" ({ci[0]:+.{digits}f}…{ci[1]:+.{digits}f})"


def _kind_group(arm: dict[str, Any], kind: str) -> dict[str, Any] | None:
    groups = [g for g in arm["groups"].values() if g["kind"] == kind]
    return max(groups, key=lambda g: g["runs"]) if groups else None


def _uncarried(gate: dict[str, Any]) -> str:
    """``merges_without_carrier`` as ``k/n``, or why it has no value."""
    if not gate.get("carrier_units"):
        return "– (no labels)"
    if not gate.get("merges_without_carrier_n"):
        return "– (no forward merge)"
    return f"{gate['merges_without_carrier_count']}/{gate['merges_without_carrier_n']}"


def _silent(weaknesses: dict[str, Any]) -> str:
    """Silent deductions as ``k/n (share)``: ``0/0`` when no technical item is
    below its maximum, ``–`` for metrics built before the count existed."""
    if "silent_deductions_n" not in weaknesses:
        return "–"
    counts = f"{weaknesses['silent_deductions_count']}/{weaknesses['silent_deductions_n']}"
    return f"{counts} ({_pct(weaknesses['silent_deductions'])})" if weaknesses["silent_deductions_n"] else counts


def _arm_rows(arm: dict[str, Any]) -> dict[str, str]:
    """The snippet's metric cells for one arm."""
    fresh = _kind_group(arm, "fresh")
    regen = _kind_group(arm, "regen")
    rows: dict[str, str] = {}
    if fresh:
        typed = fresh["total"]["typed"]
        rows["Total mean / pooled within-item SD (typed)"] = f"{_fmt(typed['mean'])} / {_fmt(typed['sd'])}"
        v = fresh["verdicts"]["typed"]
        if v["straddle"] is not None:
            rows["Items with split verdict at 90"] = (
                f"{round(v['straddle'] * v['straddle_units'])}/{v['straddle_units']}"
            )
        rows["Noisiest criteria (SD)"] = (
            " · ".join(f"{c['id']} {c['sd']:.1f}" for c in fresh["noisiest_criteria"]) or "–"
        )
        rows["Weakness-topic Jaccard"] = _fmt(fresh["weaknesses"]["topic_jaccard"], 2)
        rows["Silent deductions (technical items, fresh)"] = _silent(fresh["weaknesses"])
    misses = sum(g["defects"]["defect_misses"] for g in arm["groups"].values())
    druns = sum(g["defects"]["defect_runs"] for g in arm["groups"].values())
    alarms = sum(g["defects"]["false_alarms"] for g in arm["groups"].values())
    probes = sum(g["defects"]["probe_runs"] for g in arm["groups"].values())
    rows["Named-defect miss rate"] = f"{misses}/{druns}" if druns else "– (no labels)"
    rows["False alarms on permitted features"] = f"{alarms}/{probes}" if probes else "– (no labels)"
    if regen:
        gate = regen["gate"]
        accuracy = (
            f"{round(gate['accuracy'] * gate['accuracy_n'])}/{gate['accuracy_n']}"
            if gate["accuracy"] is not None
            else "– (no labels)"
        )
        rows["Gate verdict = expected / order bias (pts)"] = f"{accuracy} / {_fmt(gate['order_bias'])}"
        rows["Gate verdict flip rate (regen items)"] = _pct(gate["verdict_flip"])
        rows["Forward merges without a labeled carrier"] = _uncarried(gate)
    rows["Sessions / API-equivalent cost"] = f"{arm['cells']['ok']}/{arm['cells']['total']} / ${arm['cost_usd']:.0f}"
    return rows


def _headline_title(records: Sequence[dict[str, Any]], set_name: str, subset_label: str) -> str:
    fresh_items = {r["item"] for r in records if r.get("kind") == "fresh"}
    pair_orders: dict[str, set[Any]] = {}
    for r in records:
        if r.get("kind") == "regen":
            pair_orders.setdefault(r["item"], set()).add(r.get("order"))
    runs = max((int(r.get("run") or 0) for r in records), default=0)

    def plural(n: int, word: str) -> str:
        return f"{n} {word}{'' if n == 1 else 's'}"

    parts = []
    if fresh_items:
        parts.append(f"{len(fresh_items)} fresh × {runs}")
    if pair_orders:
        # Forward-only pairs run one order, so group pairs by how many orders they ran.
        groups = Counter(len(orders) for orders in pair_orders.values())
        terms = [f"{plural(n, 'pair')} × {plural(k, 'order')}" for k, n in sorted(groups.items(), reverse=True)]
        parts.append(f"{terms[0]} × {runs}" if len(terms) == 1 else f"({' + '.join(terms)}) × {runs}")
    return f"### Review retest — set {set_name} {subset_label} ({', '.join(parts) or 'no cells'})"


def render_snippet(
    cand: dict[str, Any],
    records: Sequence[dict[str, Any]],
    *,
    set_name: str,
    subset_label: str,
    rules: str,
    base_rules: str | None,
    run_url: str,
    lock_sha: str,
    base: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
) -> str:
    models = []
    for kind, label in (("fresh", "Fresh"), ("regen", "Regen")):
        group = _kind_group(cand, kind)
        if group:
            models.append(f"{label}: {group['model']}")
    rules_part = f"rules {base_rules[:7]} → {rules[:7]}" if base_rules else f"rules {rules[:7]}"
    lines = [
        _headline_title(records, set_name, subset_label),
        f"{' · '.join(models) or 'no successful cells'} · {rules_part} · harness v{HARNESS_VERSION}",
        "",
    ]
    cand_rows = _arm_rows(cand)
    if base is not None:
        base_rows = _arm_rows(base)
        deltas: dict[str, str] = {}
        fresh_cmp = (comparison or {}).get("kinds", {}).get("fresh")
        if fresh_cmp:
            deltas["Total mean / pooled within-item SD (typed)"] = (
                f"{_fmt(fresh_cmp['delta_mean'])}{_ci(fresh_cmp['delta_mean_ci'])} / "
                f"{_fmt(fresh_cmp['delta_sd'])}{_ci(fresh_cmp['delta_sd_ci'])}"
            )
        lines += ["| Metric | Baseline | Candidate | Δ (95% CI) |", "|---|---|---|---|"]
        for key in dict.fromkeys([*base_rows, *cand_rows]):
            lines.append(f"| {key} | {base_rows.get(key, '–')} | {cand_rows.get(key, '–')} | {deltas.get(key, '')} |")
        flags = (comparison or {}).get("flags") or []
        if flags:
            lines += ["", f"Flags: {', '.join(flags)}"]
    else:
        lines += ["| Metric | This arm |", "|---|---|"]
        lines += [f"| {key} | {value} |" for key, value in cand_rows.items()]
    lines += ["", f"[run]({run_url}) · set {set_name} lock sha256 {lock_sha[:12]}"]
    return "\n".join(lines) + "\n"


def render_report(
    arm: dict[str, Any],
    snippet: str,
    *,
    label: str,
    set_name: str,
    labels_state: str,
    rules_sha: str,
    harness_sha: str,
    run_url: str,
) -> str:
    lines = [
        f"# Review retest — {label or 'unlabelled arm'}",
        "",
        f"Set {set_name} (labels: {labels_state}) · rules `{rules_sha[:10]}` · harness `{harness_sha[:10]}` "
        f"(v{HARNESS_VERSION}) · [run]({run_url})",
        "",
        "## Cells",
        "",
        f"- {arm['cells']['ok']} of {arm['cells']['total']} cells produced a review; "
        f"errors: {json.dumps(arm['cells']['errors']) if arm['cells']['errors'] else 'none'}",
        f"- API-equivalent cost: ${arm['cost_usd']:.2f}; resolved models: {', '.join(arm['models']) or '–'}",
        "",
    ]
    for key, group in arm["groups"].items():
        kind, model = key.split("|", 1)
        total = group["total"]
        lines += [
            f"## {kind} · {model}",
            "",
            f"{group['units']} units, {group['runs']} runs.",
            "",
            "| Metric | Value |",
            "|---|---|",
            f"| Total, typed: mean / pooled SD | {_fmt(total['typed']['mean'])} / {_fmt(total['typed']['sd'])} |",
            f"| Total, checklist sum: mean / pooled SD | {_fmt(total['sum']['mean'])} / {_fmt(total['sum']['sd'])} |",
            f"| Runs where typed ≠ sum | {_pct(total['typed_ne_sum'])} |",
            f"| Units with an auto-reject run (excluded above) | {', '.join(total['auto_reject_units']) or 'none'} |",
            f"| Weaknesses per review | {_fmt(group['weaknesses']['count_mean'])} |",
            f"| Weakness-topic Jaccard ({group['weaknesses']['taxonomy']}) | {_fmt(group['weaknesses']['topic_jaccard'], 2)} |",
            f"| Criterion-id Jaccard | {_fmt(group['weaknesses']['id_jaccard'], 2)} |",
            f"| “Add X” weaknesses | {_pct(group['weaknesses']['add_share'])} |",
            f"| Below-max comments without a limiting word | {_pct(group['weaknesses']['below_max_without_limiting_word'])} |",
            f"| Silent deductions (technical items below max no defect line names) / runs with one | "
            f"{_silent(group['weaknesses'])} / {_pct(group['weaknesses'].get('silent_deduction_runs'))} |",
        ]
        if "verdicts" in group:
            for field in ("typed", "sum"):
                v = group["verdicts"][field]
                lines.append(
                    f"| Verdict at 90 ({field}): straddling units / pairwise disagreement | "
                    f"{_pct(v['straddle'])} / {_pct(v['disagreement'])} |"
                )
        d = group["defects"]
        lines += [
            f"| Named defects: miss rate / detected every run | {_pct(d['miss_rate'])} ({d['defect_misses']}/{d['defect_runs']}) / {_pct(d['detected_every_run'])} |",
            f"| Never detected (label check) | {', '.join(d['never_detected']) or 'none'} |",
            f"| Permission probes: false alarms | {_pct(d['false_alarm_rate'])} ({d['false_alarms']}/{d['probe_runs']}) |",
        ]
        if "gate" in group:
            g = group["gate"]
            carrier = _uncarried(g)
            if g["merges_without_carrier"] is not None:
                carrier = f"{_pct(g['merges_without_carrier'])} ({carrier})"
            lines += [
                f"| Gate verdict flip rate / accuracy vs expected | {_pct(g['verdict_flip'])} / {_pct(g['accuracy'])} (n={g['accuracy_n']}) |",
                f"| Pooled SD: prev_rescored / new / new − prev_rescored | {_fmt(g['sd_prev_rescored'])} / {_fmt(g['sd_new'])} / {_fmt(g['sd_delta'])} |",
                f"| Order bias (pts, negative favours merge) | {_fmt(g['order_bias'])} over {g['order_bias_items']} pairs |",
                f"| Runs citing a permission as an improvement (not counted) | {_pct(g['permission_cited'])} (n={g['permission_cited_n']}) |",
                f"| Forward merges without a labeled carrier (no `fixes` match, no affirmative C id) | {carrier} |",
            ]
            for cls, cal in g["calibration"].items():
                lines.append(
                    f"| {cls} pairs: new − prev_rescored < −1 / counted visible improvement claimed | "
                    f"{_pct(cal['below_tolerance'])} / {_pct(cal['visible_claims'])} (n={cal['n']}) |"
                )
        lines += ["", "| Criterion | Mean | At max | Pooled SD | Flip |", "|---|---|---|---|---|"]
        for cid, c in group["criteria"].items():
            if c["mean"] is None:
                continue
            lines.append(
                f"| {cid} | {_fmt(c['mean'])} | {_pct(c['at_max'])} | {_fmt(c['sd'], 2)} | {_pct(c['flip'])} |"
            )
        lines.append("")
    lines += ["## Snippet for the PR body", "", "```markdown", snippet.rstrip(), "```", ""]
    return "\n".join(lines)


def report(
    records: Sequence[dict[str, Any]],
    manifest: dict[str, Any],
    out_dir: Path,
    *,
    label: str,
    subset_label: str,
    rules_sha: str,
    harness_sha: str,
    run_url: str,
    lock_sha: str,
    base_records: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    labels = item_labels(manifest)
    arm = metrics.arm_metrics(records, labels)
    base = metrics.arm_metrics(base_records, labels) if base_records else None
    comparison = metrics.compare_arms(base_records, records, labels) if base_records else None
    base_rules = next((str(r["rules_sha"]) for r in base_records if r.get("rules_sha")), None) if base_records else None
    snippet = render_snippet(
        arm,
        records,
        set_name=manifest["set"],
        subset_label=subset_label,
        rules=rules_sha,
        base_rules=base_rules,
        run_url=run_url,
        lock_sha=lock_sha,
        base=base,
        comparison=comparison,
    )
    text = render_report(
        arm,
        snippet,
        label=label,
        set_name=manifest["set"],
        labels_state=manifest["labels"],
        rules_sha=rules_sha,
        harness_sha=harness_sha,
        run_url=run_url,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "label": label,
        "set": manifest["set"],
        "labels": manifest["labels"],
        "harness_version": HARNESS_VERSION,
        "rules_sha": rules_sha,
        "harness_sha": harness_sha,
        "lock_sha256": lock_sha,
        "run_url": run_url,
        "metrics": arm,
        "comparison": comparison,
    }
    (out_dir / "retest-report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (out_dir / "retest-report.md").write_text(text, encoding="utf-8")
    (out_dir / "snippet.md").write_text(snippet, encoding="utf-8")
    with (out_dir / "records.jsonl").open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return payload


# ---------------------------------------------------------------------------
# gate-report (local)
# ---------------------------------------------------------------------------


def comparable_record(record: dict[str, Any]) -> bool:
    """The stored review ran under the same model and the same qc/aqr rules."""
    model, prev = record.get("model"), record.get("prev_model")
    return (
        bool(model)
        and model not in ("n/a", None)
        and model == prev
        and review_provenance.same_rules(record.get("criteria_version"), record.get("prev_criteria_version"))
    )


def gh_gate_records(limit: int) -> list[dict[str, Any]]:
    """Gate records from the comments of PRs labelled regen:kept or regen:improved."""
    numbers: set[int] = set()
    for label in ("regen:kept", "regen:improved"):
        out = subprocess.run(
            ["gh", "pr", "list", "--state", "all", "--label", label, "--limit", str(limit), "--json", "number"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        numbers |= {int(p["number"]) for p in json.loads(out or "[]")}
    records: list[dict[str, Any]] = []
    for number in sorted(numbers):
        out = subprocess.run(
            [
                "gh",
                "api",
                "--paginate",
                f"repos/{{owner}}/{{repo}}/issues/{number}/comments",
                "--jq",
                ".[].body | @json",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        seen = False
        for line in out.splitlines():
            if not line.strip():
                continue
            for record in parse_record_markers(json.loads(line)):
                if not seen:  # one decision per PR; the first marker wins
                    records.append(record)
                    seen = True
    return records


def render_gate_report(result: dict[str, Any]) -> str:
    def drift(summary: dict[str, Any]) -> str:
        return (
            f"n={summary['n']} mean {_fmt(summary['mean'])} median {_fmt(summary['median'])} "
            f"SD {_fmt(summary['sd'])}{_ci(summary['ci'])}"
        )

    imp = result["improvements"]
    # Reports built before P9b have no writeback block.
    writeback = result.get("writeback") or {"n": 0, "counts": {}}
    lines = [
        "# Regen gate report",
        "",
        f"- Decisions: {result['n']}; merge rate {_pct(result['merge_rate'])}",
        f"- Reason codes: {', '.join(f'{k} {v}' for k, v in result['codes'].items()) or 'none'}",
        f"- Counted visible improvements (never a permission or an obsolete weakness): mean "
        f"{_fmt(imp['visible_mean'])} per decision, at least one in {_pct(imp['with_visible'])} (n={imp['n']})",
        f"- Carriers (a verified defect or an affirmative characteristic): mean {_fmt(imp['carriers_mean'])} per "
        f"decision, at least one in {_pct(imp['with_carrier'])} (n={imp['carrier_n']}); "
        f"kept as no_defect_improvement: {imp['no_defect_improvement']}",
        f"- Permission cited as an improvement: {imp['permission_cited']}/{imp['permission_n']} decisions "
        f"({_pct(imp['permission_cited_share'])}); kept with nothing else counted: {imp['permission_only_keeps']}",
        f"- Obsolete weakness cited: {imp['obsolete_cited']}/{imp['carrier_n']} decisions "
        f"({_pct(imp['obsolete_cited_share'])}); unverified claim in {_pct(imp['unverified_share'])}, "
        f"design, library or coverage point in {_pct(imp['de_lm_share'])}",
        # Reports built before P3.1 have no kind keys.
        f"- Improvement kinds (n={imp.get('kind_n', 0)} decisions): named on "
        f"{_pct(imp.get('kind_valid_share'))} of the listed improvements; an addition in "
        f"{_pct(imp.get('addition_share'))}, polish in {_pct(imp.get('polish_share'))}, a would-be carrier "
        f"without a kind in {_pct(imp.get('no_kind_share'))}; merges carried only by P or new items: "
        f"{_pct(imp.get('pn_only_merge_share'))} (n={imp.get('pn_merge_n', 0)})",
        # Reports built before P8 have no code-path keys.
        f"- Code path (merged with no carrier, on a CQ-04 code fix): {imp.get('code_path_merges', 0)} "
        f"(n={imp.get('code_path_n', 0)} decisions)",
        f"- Stored review on a keep (writeback, n={writeback['n']} keeps): "
        + ", ".join(f"{code} {writeback['counts'].get(code, 0)}" for code in WRITEBACK_CODES),
        f"- prev_rescored − prev_stored, comparable: {drift(result['drift_comparable'])}",
        f"- prev_rescored − prev_stored, all: {drift(result['drift_all'])}",
        f"- new − prev_rescored: {drift(result['margin'])}; inside [−1, 0]: {_pct(result['margin_within_tolerance'])}",
        "",
        "| Model | Drift |",
        "|---|---|",
        *(f"| {k} | {drift(v)} |" for k, v in result["drift_by_model"].items()),
        "",
        "| Library | Drift |",
        "|---|---|",
        *(f"| {k} | {drift(v)} |" for k, v in result["drift_by_library"].items()),
        "",
        "| Week | Decisions | Merge rate | Mean drift |",
        "|---|---|---|---|",
        *(
            f"| {k} | {v['n']} | {_pct(v['merge_rate'])} | {_fmt(v['drift_mean'])} |"
            for k, v in result["weekly"].items()
        ),
        "",
        "## Alarms",
        "",
        *([f"- {a}" for a in result["alarms"]] or ["- none"]),
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# first-reviews (local)
# ---------------------------------------------------------------------------


FIRST_GENERATION_BRANCH_RE = re.compile(r"^implementation/(?P<spec_id>[a-z0-9][a-z0-9-]*)/(?P<library>[a-z0-9]+)$")


def first_generation_pull(pull: dict[str, Any]) -> dict[str, Any] | None:
    """``{number, spec_id, library}`` of a first-generation pull request, else None.

    A first generation runs on ``implementation/<spec>/<library>`` and carries
    no ``regen`` label (``regen``, ``regen:forced``, ``regen:kept``, …).
    """
    branch = FIRST_GENERATION_BRANCH_RE.match(str(pull.get("headRefName") or ""))
    labels = [str((label or {}).get("name") or "") for label in pull.get("labels") or []]
    if not branch or any(name.startswith("regen") for name in labels):
        return None
    return {"number": int(pull["number"]), "spec_id": branch.group("spec_id"), "library": branch.group("library")}


def pull_reviews(comments: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """The AI review comments of one pull request, parsed, in posting order."""
    reviews = []
    for comment in sorted(comments, key=lambda c: str(c.get("at") or "")):
        review = metrics.parse_review_comment(str(comment.get("body") or ""))
        if review is not None:
            reviews.append({**review, "at": str(comment.get("at") or "")})
    return reviews


def _gh_json(args: Sequence[str]) -> Any:
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out or "null")


def gh_first_generation_pulls(since: str, limit: int) -> list[dict[str, Any]]:
    """First-generation pull requests created since a date, with their reviews and commits (read-only)."""
    listed = _gh_json(
        [
            "pr",
            "list",
            "--state",
            "all",
            "--limit",
            str(limit),
            "--search",
            f"created:>={since}",
            "--json",
            "number,headRefName,labels",
        ]
    )
    if len(listed or []) >= limit:
        print(
            f"::warning::the listing stopped at --limit {limit}: older pull requests since {since} are missing",
            file=sys.stderr,
        )
    pulls = []
    for pull in sorted(filter(None, map(first_generation_pull, listed or [])), key=lambda p: p["number"]):
        out = subprocess.run(
            [
                "gh",
                "api",
                "--paginate",
                f"repos/{{owner}}/{{repo}}/issues/{pull['number']}/comments",
                "--jq",
                ".[] | {body, at: .created_at} | @json",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        comments = [json.loads(line) for line in out.splitlines() if line.strip()]
        commits = (_gh_json(["pr", "view", str(pull["number"]), "--json", "commits"]) or {}).get("commits") or []
        pull["reviews"] = pull_reviews(comments)
        pull["commits"] = [{"at": c.get("committedDate"), "headline": c.get("messageHeadline")} for c in commits]
        pulls.append(pull)
    return pulls


def render_first_reviews(result: dict[str, Any], since: str) -> str:
    def signed(value: int | None) -> str:
        return "–" if value is None else f"{value:+d}"

    histogram = " · ".join(f"{score}: {n}" for score, n in result["histogram"].items()) or "–"
    silent = (
        f"{result['silent_deductions_count']}/{result['silent_deductions_n']} ({_pct(result['silent_deductions'])})"
        if result["silent_deductions_n"]
        else "– (no technical item below its maximum)"
    )
    repairs = result["repairs"]
    lines = [
        f"# First reviews since {since}",
        "",
        f"- First-generation pull requests: {result['pulls']}; with an attempt-1 review: {result['first_reviews']}",
        f"- Attempt-1 scores: mean {_fmt(result['mean'])}, SD {_fmt(result['sd'])}; "
        f"{result['approved_first']} at {metrics.APPROVAL_LINE} or above; "
        f"at {metrics.NEAR_LINE[0]}–{metrics.NEAR_LINE[1]}: {_pct(result['near_line'])}",
        f"- Histogram: {histogram}",
        f"- Silent deductions (technical items below their maximum that no defect line names): {silent}, in "
        f"{len(result['silent_pulls'])} review(s)"
        + (
            ": " + ", ".join(f"#{p['number']} {' '.join(p['items'])}" for p in result["silent_pulls"])
            if result["silent_pulls"]
            else ""
        ),
        f"- Repairs: {len(repairs)}; gain on technical items {signed(result['repair_gain_technical'])}, on "
        f"judgment items {signed(result['repair_gain_judgment'])}; without a commit: "
        + (", ".join(f"#{n}" for n in result["repairs_without_commit"]) or "none"),
        "",
        "| Spec | Reviews | Mean | Between-library SD | Items no library differs on |",
        "|---|---|---|---|---|",
        *(
            f"| {spec_id} | {s['n']} | {_fmt(s['mean'])} | {_fmt(s['sd'])} | "
            f"{len(s['zero_variance'])}: {', '.join(s['zero_variance']) or '–'} |"
            for spec_id, s in result["specs"].items()
        ),
        "",
    ]
    if repairs:
        lines += [
            "| Pull request | Library | Score | Technical | Judgment | Repair committed |",
            "|---|---|---|---|---|---|",
            *(
                f"| #{r['number']} | {r['library']} | {r['from']} → {r['to']} | {signed(r['technical'])} | "
                f"{signed(r['judgment'])} | {'yes' if r['committed'] else 'no'} |"
                for r in repairs
            ),
            "",
        ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# freeze (local, owner-authorized upload)
# ---------------------------------------------------------------------------


def pixel_stats(a: Path, b: Path) -> dict[str, Any]:
    """Share of changed pixels and the largest channel delta between two renders."""
    import numpy as np
    from PIL import Image

    with Image.open(a) as ia, Image.open(b) as ib:
        x = np.asarray(ia.convert("RGBA"), dtype=np.int16)
        y = np.asarray(ib.convert("RGBA"), dtype=np.int16)
    if x.shape != y.shape:
        return {"changed_px_pct": None, "max_channel_delta": None, "shape_mismatch": True}
    diff = np.abs(x - y)
    changed = diff.max(axis=2) > 0
    return {"changed_px_pct": round(float(changed.mean()) * 100, 2), "max_channel_delta": int(diff.max())}


def production_url(spec_id: str, library: str, theme: str) -> str:
    return f"{PUBLIC_BASE}/plots/{spec_id}/{language_of(library)}/{library}/plot-{theme}.png"


def _check_production_pin(item: dict[str, Any], role: str, repo: Path) -> None:
    """Refuse a production render whose implementation changed on main after the pin."""
    spec_id, library, commit = item["spec_id"], item["library"], item[role]["commit"]
    later = git(repo, "log", "--format=%H", f"{commit}..origin/main", "--", impl_path(spec_id, library)).split()
    if later:
        raise HarnessError(
            f"{item['id']} {role}: {len(later)} commit(s) on origin/main touched the implementation after "
            f"{commit[:10]} — the production render no longer matches the pinned source; re-pin the item"
        )


def _snapshot_render(item: dict[str, Any], role: str, theme: str, snapshots_root: Path) -> Path:
    """Path of a snapshot render; refuses a snapshot taken at another commit."""
    library, commit = str(item["library"]), str(item[role]["commit"])
    snapshot = snapshots_root / str(item[role]["render"]["snapshot"])
    snap_manifest = load_yaml(snapshot / "manifest.yaml") or {}
    if str(snap_manifest.get("main_sha")) != commit:
        raise HarnessError(
            f"{item['id']} {role}: snapshot {snapshot} was taken at {snap_manifest.get('main_sha')}, not {commit}"
        )
    return snapshot / "renders" / language_of(library) / library / f"plot-{theme}.png"


def _render_source(
    item: dict[str, Any], role: str, theme: str, snapshots_root: Path, repo: Path, fetch: Callable[[str], bytes | None]
) -> tuple[str, Callable[[], bytes | None]]:
    """(description, loader) for one frozen render; refuses unpinnable sources."""
    if item[role]["render"] == "production":
        _check_production_pin(item, role, repo)
        url = production_url(item["spec_id"], item["library"], theme)
        return url, lambda: fetch(url)
    path = _snapshot_render(item, role, theme, snapshots_root)
    return str(path), lambda: path.read_bytes() if path.is_file() else None


def _refusal(problems: Sequence[str], what: str) -> HarnessError:
    unique = list(dict.fromkeys(problems))  # a pin refusal repeats per theme
    return HarnessError(f"{what} ({len(unique)} problem(s)):\n  " + "\n  ".join(unique))


PNG_HEADER_BYTES = 24  # signature + IHDR length/type + width + height


def check_renders(
    manifest: dict[str, Any], *, repo: Path, snapshots_root: Path, head: Callable[[str], bytes | None] | None = None
) -> dict[str, Any]:
    """Everything freeze would refuse about the sources, without downloading a render.

    Reads only the 24-byte PNG header of every render the set needs (production
    objects over an HTTP Range request, snapshot renders from disk) and checks
    the canvas, plus the production pins and the snapshot commits. A snapshot
    directory that is not present locally is skipped, not refused.
    """

    def default_head(url: str) -> bytes | None:
        return http_get(url, first_bytes=PNG_HEADER_BYTES, timeout=30)

    head = head or default_head
    problems: list[str] = []
    skipped: list[str] = []
    off_canvas: list[str] = []
    checked = 0
    for item in manifest["items"]:
        for role in roles_of(item):
            render = item[role]["render"]
            if render != "production" and not (snapshots_root / str(render["snapshot"])).is_dir():
                skipped.append(f"{item['id']} {role}: snapshot {render['snapshot']} is not present")
                continue
            for theme in THEMES:
                at = f"{item['id']} {role} {theme}"
                try:
                    if render == "production":
                        _check_production_pin(item, role, repo)
                        where = production_url(item["spec_id"], item["library"], theme)
                        data = head(where)
                    else:
                        path = _snapshot_render(item, role, theme, snapshots_root)
                        where = str(path)
                        data = None
                        if path.is_file():
                            with path.open("rb") as f:
                                data = f.read(PNG_HEADER_BYTES)
                    if data is None:
                        problems.append(f"{at}: source {where} not found")
                        continue
                    size = png_size(data)
                except HarnessError as exc:
                    problems.append(str(exc) if str(exc).startswith(item["id"]) else f"{at}: {exc}")
                    continue
                checked += 1
                problem = canvas_problem(item, role, size, where)
                if problem:
                    problems.append(f"{at}: {problem}")
                elif not canonical_canvas(size):
                    off_canvas.append(f"{at}: {size[0]}x{size[1]} (predecessor of a forward-only pair)")
    return {"problems": list(dict.fromkeys(problems)), "checked": checked, "skipped": skipped, "off_canvas": off_canvas}


def freeze(
    manifest: dict[str, Any],
    *,
    repo: Path,
    snapshots_root: Path,
    staging: Path,
    fetch: Callable[[str], bytes | None] = http_get,
    lister: RunLister | None = gh_run_lister,
    stats: Callable[[Path, Path], dict[str, Any]] = pixel_stats,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build the frozen set in ``staging``: every render copied to its object
    path, checked, hashed; pair pixel statistics; the lock; the upload commands.

    Every refusal is collected and raised once at the end, so one dry run
    lists all of them (``validate --check-renders`` finds the source problems
    without downloading anything)."""
    if lister is not None:
        busy = busy_pipeline_runs(lister, now or datetime.now(timezone.utc))
        if busy:
            raise HarnessError("the pipeline is busy; freeze only while it is idle:\n  " + "\n  ".join(busy))
    objects: dict[str, dict[str, Any]] = {}
    sources: dict[str, str] = {}
    pairs: dict[str, dict[str, Any]] = {}
    uploads: list[str] = []
    problems: list[str] = []
    for item in manifest["items"]:
        staged = 0
        for role in roles_of(item):
            for theme in THEMES:
                at = f"{item['id']} {role} {theme}"
                obj = object_path(manifest, item["id"], role, theme)
                try:
                    where, load = _render_source(item, role, theme, snapshots_root, repo, fetch)
                    data = load()
                    if data is None:
                        problems.append(f"{at}: source {where} not found")
                        continue
                    size = png_size(data)
                    problem = canvas_problem(item, role, size, where)
                    if problem:
                        problems.append(f"{at}: {problem}")
                        continue
                    target = staging / obj
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    digest = sha256_bytes(data)
                    objects[obj] = {"sha256": digest, "width": size[0], "height": size[1], "bytes": len(data)}
                    sources[obj] = where
                    staged += 1
                    existing = fetch(f"{PUBLIC_BASE}/{obj}")
                except HarnessError as exc:
                    problems.append(str(exc) if str(exc).startswith(item["id"]) else f"{at}: {exc}")
                    continue
                if existing is None:
                    uploads.append(obj)
                elif sha256_bytes(existing) != digest:
                    problems.append(f"{obj} already exists with different content — a frozen set is never rewritten")
        if item["kind"] == "regen" and staged == len(roles_of(item)) * len(THEMES):
            pairs[item["id"]] = {
                theme: stats(
                    staging / object_path(manifest, item["id"], "new", theme),
                    staging / object_path(manifest, item["id"], "prev", theme),
                )
                for theme in THEMES
            }
            # None (renders of different sizes) differs as well.
            if item.get("class") == "identity" and any(
                p.get("changed_px_pct") != 0 for p in pairs[item["id"]].values()
            ):
                problems.append(f"{item['id']} is labelled identity but its renders differ")
    if problems:
        raise _refusal(problems, "freeze refused")
    lock = {
        "version": 1,
        "set": manifest["set"],
        "frozen_at": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "objects": dict(sorted(objects.items())),
        "sources": dict(sorted(sources.items())),
        "pairs": pairs,
    }
    commands = [upload_command(staging, obj) for obj in uploads]
    return {"lock": lock, "uploads": uploads, "commands": commands}


def upload_command(staging: Path, obj: str) -> list[str]:
    """The one write freeze ever makes: a no-clobber copy of a new object."""
    return ["gcloud", "storage", "cp", "--no-clobber", str(staging / obj), f"{BUCKET}/{obj}"]


def verify_uploaded(lock: dict[str, Any], fetch: Callable[[str], bytes | None] = http_get) -> list[str]:
    """Objects whose public copy is missing or differs from the lock."""
    problems = []
    for obj, meta in lock["objects"].items():
        data = fetch(f"{PUBLIC_BASE}/{obj}")
        if data is None:
            problems.append(f"{obj}: missing")
        elif sha256_bytes(data) != meta["sha256"]:
            problems.append(f"{obj}: sha256 differs")
    return problems


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _manifest_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        default="automation/retest/set-v1.yaml",
        help="the set's manifest (automation/retest/set-v<N>.yaml)",
    )


def _lock_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--lock", default="automation/retest/set-v1.lock.json", help="the set's lock (set-v<N>.lock.json, same set)"
    )


def cmd_validate(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.manifest))
    fresh = sum(1 for i in manifest["items"] if i["kind"] == "fresh")
    print(f"manifest ok: set {manifest['set']}, {fresh} fresh items, {len(manifest['items']) - fresh} regen pairs")
    if Path(args.lock).is_file():
        lock = load_lock(Path(args.lock), manifest)
        wanted = {
            object_path(manifest, i["id"], role, theme)
            for i in manifest["items"]
            for role in roles_of(i)
            for theme in THEMES
        }
        missing = sorted(wanted - set(lock.get("objects") or {}))
        if missing:
            raise HarnessError("lock lacks objects:\n  " + "\n  ".join(missing))
        print(f"lock ok: {len(lock['objects'])} objects")
    else:
        print("lock: not frozen yet")
    if args.check_git:
        missing = check_git(manifest, Path(args.repo))
        if missing:
            raise HarnessError("pinned sources missing:\n  " + "\n  ".join(missing))
        print("git ok: every pinned source exists")
    if args.check_renders:
        repo = Path(args.repo)
        result = check_renders(manifest, repo=repo, snapshots_root=Path(args.snapshots_root or repo))
        for line in result["skipped"]:
            print(f"  skipped {line}")
        if result["problems"]:
            raise _refusal(result["problems"], "freeze would refuse these renders")
        for line in result["off_canvas"]:
            print(f"  off-canvas {line}")
        print(
            f"renders ok: {result['checked']} PNG headers, "
            f"{result['checked'] - len(result['off_canvas'])} on canonical canvases and "
            f"{len(result['off_canvas'])} off-canvas predecessors of forward-only pairs; "
            f"{len(result['skipped'])} skipped"
        )
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.manifest))
    load_lock(Path(args.lock), manifest)
    resume = load_records(Path(args.resume_records)) if args.resume_records else []
    result = plan(
        manifest,
        subset=args.subset,
        models=args.models,
        runs=int(args.runs),
        orders=args.orders,
        rules_sha=args.rules_sha,
        repo=Path(args.repo),
        lister=None if args.skip_idle_check else gh_run_lister,
        resume_records=resume,
        action_sha=args.action_sha,
        spec_source=args.spec_source,
    )
    summary = (
        f"{result['sessions']} sessions ({', '.join(f'{k} {v}' for k, v in result['by_model'].items()) or 'none'}), "
        f"{result['resumed']} resumed, about ${result['estimate_usd']:.0f} API-equivalent"
    )
    print(f"::notice::review retest plan: {summary}")
    resume_lines = resume_log(result["resume_rejected"], result["resume_unused"])
    for line in resume_lines:
        print(f"::warning::{line}")
    write_outputs(
        {
            "matrix": json.dumps(result["cells"], separators=(",", ":")),
            "items": ",".join(result["items"]),
            "sessions": str(result["sessions"]),
            "resumed": ",".join(result["resumed_cells"]),
        }
    )
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write(f"### Review retest plan\n\n{summary}. Items: {', '.join(result['items']) or 'none'}.\n\n")
            if resume_lines:
                f.write("".join(f"- {line}\n" for line in resume_lines) + "\n")
    return 0


def resume_log(rejected: Sequence[dict[str, str]], unused: int) -> list[str]:
    """One line per distinct rejection reason, with its count and first cells."""
    by_reason: dict[str, list[str]] = {}
    for entry in rejected:
        by_reason.setdefault(entry["reason"], []).append(entry["cell"])
    lines = [
        f"resume: {len(cells)} record(s) rejected and run again ({reason}): "
        + ", ".join(cells[:3])
        + (f" and {len(cells) - 3} more" if len(cells) > 3 else "")
        for reason, cells in by_reason.items()
    ]
    if unused:
        lines.append(
            f"resume: {unused} successful record(s) name cells outside this plan (subset, runs, orders) and are not used"
        )
    return lines


def cmd_bundle(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.manifest))
    lock = load_lock(Path(args.lock), manifest)
    by_id = {i["id"]: i for i in manifest["items"]}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for item_id in [s for s in args.items.split(",") if s]:
        if item_id not in by_id:
            raise HarnessError(f"unknown item {item_id}")
        bundle_item(manifest, lock, by_id[item_id], out, Path(args.repo))
        print(f"bundled {item_id}")
    return 0


def cmd_materialize(args: argparse.Namespace) -> int:
    cell = json.loads(args.cell)
    outputs = materialize(
        Path(args.bundles) / cell["item"],
        Path(args.workspace),
        cell,
        Path(args.gate_script),
        spec_source=args.spec_source,
        tmp=TmpPaths(Path(args.tmp_base)),
    )
    outputs["started_at"] = str(int(time.time()))
    write_outputs(outputs)
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    cell = json.loads(args.cell)
    record = collect(
        Path(args.workspace),
        cell,
        Path(args.out),
        execution_file=args.execution_file,
        review_outcome=args.review_outcome,
        materialize_ok=args.materialize_outcome == "success",
        gate_script=Path(args.gate_script),
        prev_stored=args.prev_stored,
        tmp=TmpPaths(Path(args.tmp_base)),
        started_at=float(args.started_at or 0),
        timeout_minutes=float(args.timeout_minutes),
        provenance={
            "criteria_version": args.criteria_version,
            "prompts_tree": args.prompts_tree,
            "harness_sha": args.harness_sha,
            "rules_sha": args.rules_sha,
            "action_sha": args.action_sha,
            "spec_source": args.spec_source,
        },
    )
    print(
        f"::notice::cell {record['cell']}: ok={record['ok']} error={record['error_class'] or '-'} "
        f"model={record['model'] or 'n/a'} alias={record['model_alias'] or 'n/a'} "
        f"score={record['score_typed']} cost={record['cost_usd']}"
    )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.manifest))
    lock_path = Path(args.lock)
    lock_sha = sha256_bytes(lock_path.read_bytes()) if lock_path.is_file() else "unfrozen"
    resumed = load_records(Path(args.resume_records)) if args.resume_records else []
    if resumed:
        # Only the cells plan reused (its compatibility check) are merged: a
        # record plan rejected ran again, and must not survive a failed rerun.
        if args.resumed_cells is None:
            raise HarnessError("--resume-records needs --resumed-cells, the cells plan reused (its resumed output)")
        reused = {c for c in args.resumed_cells.split(",") if c}
        resumed = [r for r in resumed if r.get("ok") and r.get("cell") in reused]
    records = merge_records(resumed, load_cell_records(Path(args.cells)))
    base = load_records(Path(args.compare_records)) if args.compare_records else []
    payload = report(
        records,
        manifest,
        Path(args.out),
        label=args.label,
        subset_label=args.subset,
        rules_sha=args.rules_sha,
        harness_sha=args.harness_sha,
        run_url=args.run_url,
        lock_sha=lock_sha,
        base_records=base,
    )
    cells = payload["metrics"]["cells"]
    print(f"::notice::review retest report: {cells['ok']}/{cells['total']} cells ok")
    return 0


def cmd_gate_report(args: argparse.Namespace) -> int:
    records = gh_gate_records(int(args.limit))
    if args.since:
        cutoff = args.since
        records = [r for r in records if str(r.get("at") or "") >= cutoff]
    result = metrics.gate_monitor(records, comparable_record)
    print(render_gate_report(result))
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


def cmd_first_reviews(args: argparse.Namespace) -> int:
    result = metrics.first_reviews(gh_first_generation_pulls(args.since, int(args.limit)))
    print(render_first_reviews(result, args.since))
    if args.json:
        Path(args.json).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


def cmd_freeze(args: argparse.Namespace) -> int:
    manifest = load_manifest(Path(args.manifest))
    repo = Path(args.repo)
    staging = Path(args.staging)
    result = freeze(
        manifest,
        repo=repo,
        snapshots_root=Path(args.snapshots_root or repo),
        staging=staging,
        lister=None if args.skip_idle_check else gh_run_lister,
    )
    lock_text = json.dumps(result["lock"], indent=2) + "\n"
    (staging / "set.lock.json").write_text(lock_text, encoding="utf-8")
    print(f"staged {len(result['lock']['objects'])} renders in {staging}; {len(result['uploads'])} to upload")
    for obj, pair in result["lock"]["pairs"].items():
        print(
            f"  pair {obj}: "
            + ", ".join(
                f"{t} renders differ in size"
                if p.get("shape_mismatch")
                else f"{t} {p.get('changed_px_pct')}% px, max Δ {p.get('max_channel_delta')}"
                for t, p in pair.items()
            )
        )
    if args.write_lock:
        Path(args.lock).write_text(lock_text, encoding="utf-8")
        print(f"wrote {args.lock}")
    if not args.execute:
        print("\nDry run. The owner-authorized upload is exactly (no clobber, no deletes):\n")
        print("\n".join(shlex.join(c) for c in result["commands"]) or "(nothing to upload)")
        print(f"\nRe-run with --execute{'' if args.write_lock else ' --write-lock'} to upload and write the lock.")
        return 0
    for command in result["commands"]:
        print(f"+ {shlex.join(command)}")
        subprocess.run(command, check=True)
    problems = verify_uploaded(result["lock"])
    if problems:
        raise HarnessError("uploaded set does not match the lock:\n  " + "\n  ".join(problems))
    print(f"verified {len(result['lock']['objects'])} public objects against the lock")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("validate", help="Check the manifest, the lock and (optionally) the pinned sources")
    _manifest_arg(p)
    _lock_arg(p)
    p.add_argument("--check-git", action="store_true")
    p.add_argument(
        "--check-renders",
        action="store_true",
        help="read every render's PNG header (HTTP Range, no download) and check canvases and pins as freeze does",
    )
    p.add_argument("--repo", default=".")
    p.add_argument("--snapshots-root", default="", help="where the manifest's snapshot dirs live (default: --repo)")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("plan", help="Resolve a subset into the matrix of cells")
    _manifest_arg(p)
    _lock_arg(p)
    p.add_argument("--subset", default="core")
    p.add_argument("--models", default="production")
    p.add_argument("--runs", default="3")
    p.add_argument("--orders", default="both")
    p.add_argument("--rules-sha", required=True)
    p.add_argument("--repo", default=".")
    p.add_argument("--resume-records", default="")
    p.add_argument("--action-sha", default="n/a", help="the claude-code-action pin (resumed records must match)")
    p.add_argument("--spec-source", default="pinned", choices=["pinned", "rules_ref"])
    p.add_argument("--skip-idle-check", action="store_true", help="local dry runs only")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("bundle", help="Pinned sources and verified renders per item")
    _manifest_arg(p)
    _lock_arg(p)
    p.add_argument("--items", required=True, help="comma-separated item ids (plan's items output)")
    p.add_argument("--repo", default=".")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_bundle)

    p = sub.add_parser("materialize", help="Lay out one cell in the workspace and /tmp")
    p.add_argument("--workspace", required=True)
    p.add_argument("--bundles", required=True)
    p.add_argument("--cell", required=True, help="the matrix cell as JSON")
    p.add_argument("--gate-script", required=True, help="regen_gate.py of the rules under test")
    p.add_argument("--spec-source", default="pinned", choices=["pinned", "rules_ref"])
    p.add_argument("--tmp-base", default="/tmp")
    p.set_defaults(func=cmd_materialize)

    p = sub.add_parser("collect", help="Gather one cell's outputs into record.json")
    p.add_argument("--workspace", required=True)
    p.add_argument("--cell", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--execution-file", default="")
    p.add_argument("--review-outcome", default="skipped")
    p.add_argument("--materialize-outcome", default="skipped")
    p.add_argument("--gate-script", required=True)
    p.add_argument("--prev-stored", default="n/a")
    p.add_argument("--tmp-base", default="/tmp")
    p.add_argument("--started-at", default="0")
    p.add_argument("--timeout-minutes", default="25")
    p.add_argument("--criteria-version", default="n/a")
    p.add_argument("--prompts-tree", default="n/a")
    p.add_argument("--harness-sha", default="n/a")
    p.add_argument("--rules-sha", default="n/a")
    p.add_argument("--action-sha", default="n/a")
    p.add_argument("--spec-source", default="n/a")
    p.set_defaults(func=cmd_collect)

    p = sub.add_parser("report", help="Aggregate cell records into the report")
    _manifest_arg(p)
    _lock_arg(p)
    p.add_argument("--cells", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--label", default="")
    p.add_argument("--subset", default="")
    p.add_argument("--rules-sha", default="n/a")
    p.add_argument("--harness-sha", default="n/a")
    p.add_argument("--run-url", default="")
    p.add_argument("--compare-records", default="")
    p.add_argument("--resume-records", default="")
    p.add_argument(
        "--resumed-cells",
        default=None,
        help="comma-separated cell ids plan reused (its resumed output); required with --resume-records",
    )
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("gate-report", help="Aggregate production regen-gate records (needs gh)")
    p.add_argument("--limit", default="500")
    p.add_argument("--since", default="", help="ISO date, e.g. 2026-10-01")
    p.add_argument("--json", default="", help="also write the aggregate as JSON here")
    p.set_defaults(func=cmd_gate_report)

    p = sub.add_parser("first-reviews", help="Aggregate the live reviews of first-generation PRs (needs gh)")
    p.add_argument("--since", required=True, help="ISO date the pull requests were created on or after")
    p.add_argument("--limit", default="500", help="how many pull requests to list at most")
    p.add_argument("--json", default="", help="also write the aggregate as JSON here")
    p.set_defaults(func=cmd_first_reviews)

    p = sub.add_parser("freeze", help="Build the frozen set (dry run unless --execute)")
    _manifest_arg(p)
    _lock_arg(p)
    p.add_argument("--repo", default=".")
    p.add_argument("--snapshots-root", default="", help="where the manifest's snapshot dirs live (default: --repo)")
    p.add_argument("--staging", required=True, help="a new local directory for the staged renders")
    p.add_argument("--write-lock", action="store_true", help="write the lock into --lock")
    p.add_argument("--execute", action="store_true", help="upload with --no-clobber and verify (owner-authorized)")
    p.add_argument("--skip-idle-check", action="store_true")
    p.set_defaults(func=cmd_freeze)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except HarnessError as exc:
        print(f"::error::{str(exc).splitlines()[0]}", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
