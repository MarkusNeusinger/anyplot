"""Metrics for the review retest harness and the regen gate monitor.

Pure functions, no IO: ``review_retest.py`` loads the cell records and the
manifest's labels and passes plain dicts in. Every metric is computed per arm
and grouped by ``(kind, resolved model)``. A *unit* is an item for fresh cells
and an item-order (``forward`` / ``reversed``) for regen cells; runs of the
same unit are the repeated sessions whose disagreement the harness measures.

Record fields read here (written by ``review_retest.py collect``): ``cell``,
``item``, ``kind``, ``order``, ``run``, ``model`` (the resolved id, or None
when the session named none), ``model_alias``, ``ok``, ``error_class``,
``score_typed``, ``checklist`` (``{id: {"score", "max", "comment"}}``),
``checklist_sum``, ``weaknesses``, ``gate`` (``{"verdict", "prev_rescored",
"code"}``), ``regen`` (the parsed ``review_regen.json``, whose
``prev_weaknesses`` feeds ``class_flip``), ``regen_counts`` (``{"total",
"visible", "permission"}`` plus, from P3 on, ``"obsolete"``, ``"carriers"``,
``"suggestion"``, ``"unverified"`` and ``"de_lm"``, and from P3.1 on,
``"addition"``, ``"polish"``, ``"no_kind"``, ``"carriers_pn"`` and
``"by_kind"``: the gate record's improvement counts) and
``spec_characteristics`` (``{"count",
"permission"}``: how many characteristic bullets the spec the reviewer saw
has, and which of them are "Expected, not a defect" bullets).

Labels (from the set manifest, applied at report time so a corrected label
re-scores old records): ``defects`` and ``permitted`` per item
(``[{"id", "criteria", "match"}]``, optionally with a ``spec_source`` that
limits the label to runs whose reviewer saw that spec text), ``fixes`` per regen item (the same shape:
predecessor defects the forward new version fixes; ``None`` when the item is
not labeled for carriers), ``expected`` gate verdicts per order and the pair
``class`` (``identity``, ``near-identical`` or ``different``).
"""

from __future__ import annotations

import math
import random
import re
import statistics
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from itertools import combinations
from typing import Any


CRITERIA_IDS: tuple[str, ...] = (
    *(f"VQ-0{i}" for i in range(1, 8)),
    *(f"DE-0{i}" for i in range(1, 4)),
    *(f"SC-0{i}" for i in range(1, 5)),
    *(f"DQ-0{i}" for i in range(1, 4)),
    *(f"CQ-0{i}" for i in range(1, 6)),
    *(f"LM-0{i}" for i in range(1, 3)),
)
# The criteria a fixed defect can carry a regen merge on: DE and LM levels
# never do, because stored reviews deduct them almost always (plan P3, D11),
# and neither does DQ-01 feature coverage, for the same reason (P3.1).
CARRIER_CRITERIA: tuple[str, ...] = tuple(c for c in CRITERIA_IDS if c[:2] in ("VQ", "SC", "DQ", "CQ") and c != "DQ-01")
APPROVAL_LINE = 90

# Weakness topics, taxonomy v1. A weakness belongs to every topic it matches.
TAXONOMY_VERSION = "topics-v1"
TOPICS: dict[str, re.Pattern[str]] = {
    name: re.compile(pattern, re.IGNORECASE)
    for name, pattern in {
        "legend": r"\blegend|colou?r ?bar|\bkey\b",
        "title": r"\btitle|subtitle|heading",
        "text_size": r"font|text size|too small|tiny|legib|readab",
        "overlap": r"overlap|collid|collision|crowd|clutter|occlu|obscur",
        "clipping": r"clip|cut off|cut-off|truncat|chopped|off[- ]canvas",
        "layout": r"layout|white ?space|margin|padding|spacing|aspect|empty space|balance",
        "grid_spines": r"\bgrid|spine|axis line",
        "palette_theme": r"palette|imprint|colou?r scheme|\btheme",
        "dark_contrast": r"dark[- ](render|theme|mode|background)|contrast|dark-on-dark|light-on-light",
        "alpha": r"\balpha|opacity|transparen|translucen",
        "marker_visibility": r"marker|glyph|bubble size|dot size|invisible|barely visible",
        "axis_range": r"axis range|\brange\b|\blimits?\b|ylim|xlim|log scale|\bdomain\b",
        "ticks": r"\btick",
        "annotation": r"annotat|highlight|callout",
        "reference_line": r"trend ?line|regression line|reference line|mean line|fit line|loess",
        "extra_encoding": r"encoding|encodes",
        "data_scenario": r"scenario|realis|plausib|invented|fabricat|real[- ]world|synthetic",
        "density": r"density|too (many|few)|number of (points|bubbles|categories|bars)|sparse",
        "code_structure": r"refactor|code (structure|length|size)|lines of code|\bkiss\b|verbose|complex",
        "idiom": r"idiom|library feature|native|deprecated",
        "interactivity": r"interactiv|hover|tooltip|zoom",
        "displacement": r"jitter|displac|nudg|force[- ]?(layout|simulation|collide)|dodge|off (their|its) (true )?(value|position)",
    }.items()
}
CRITERION_PREFIX_RE = re.compile(r"^\s*\W*((?:VQ|DE|SC|DQ|CQ|LM)-\d{2})\b")
# An order to add something, behind an optional criterion prefix: the legacy
# "VQ-03: add …" and, from P3 on, the defect line's "VQ-03, SC-04 (both): add …".
# A "Suggestion: …" line is no order and never counts.
_ID = r"(?:VQ|DE|SC|DQ|CQ|LM|AR)-\d{2}"
ADD_RE = re.compile(
    rf"^\s*(?:\W*\b{_ID}(?:,\s*{_ID})*\W*(?:\((?:light|dark|both|code)\)\W*)?)?"
    r"(?:add|consider adding|include|introduce)\b",
    re.I,
)
# A defect line's prefix, ``<ID>[, <ID>] (<light|dark|both|code>): <text>``:
# the format of regen_gate.DEFECT_RE (a unit test keeps the two patterns equal).
DEFECT_LINE_RE = re.compile(rf"^(?P<ids>{_ID}(?:, {_ID})*) \((?P<render>light|dark|both|code)\): \S")
# The 19 criteria a defect line carries a deduction on (70 points), and the
# five whose level is a judgment (30 points).
TECHNICAL_IDS: tuple[str, ...] = tuple(c for c in CRITERIA_IDS if c[:2] in ("VQ", "SC", "DQ", "CQ"))
JUDGMENT_IDS: tuple[str, ...] = tuple(c for c in CRITERIA_IDS if c[:2] in ("DE", "LM"))
LIMITING_VERSION = "limiting-v1"
LIMITING_RE = re.compile(
    r"\b(but|however|although|though|slight(ly)?|minor|could|should|lacks?|lacking|missing|too|not|no|only|"
    r"except|while|small|overlaps?|clip\w*|crowd\w*|faint|weak|cramped|inconsistent|unclear|hard)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Small statistics
# ---------------------------------------------------------------------------


def mean(values: Iterable[float]) -> float | None:
    data = list(values)
    return sum(data) / len(data) if data else None


def pooled_sd(groups: Iterable[Sequence[float]]) -> float | None:
    """``sqrt(sum_g (n_g - 1) var_g / sum_g (n_g - 1))`` over the groups of two or more values.

    Pooled by degrees of freedom: a unit with five runs weighs twice as much
    as one with three, so a unit that lost runs to a usage limit doesn't
    count as much as a complete one. With equal run counts this is the mean
    of the variances.
    """
    eligible = [g for g in groups if len(g) >= 2]
    dof = sum(len(g) - 1 for g in eligible)
    if not dof:
        return None
    return math.sqrt(sum((len(g) - 1) * statistics.variance(g) for g in eligible) / dof)


def flip_rate(groups: Iterable[Sequence[float]], threshold: float = 1) -> float | None:
    """Share of groups (at least two values) whose values differ by ``threshold`` or more."""
    eligible = [g for g in groups if len(g) >= 2]
    if not eligible:
        return None
    return sum(1 for g in eligible if max(g) - min(g) >= threshold) / len(eligible)


def share(flags: Iterable[bool]) -> float | None:
    data = list(flags)
    return sum(1 for f in data if f) / len(data) if data else None


def bootstrap_ci(
    units: Sequence[Any],
    statistic: Callable[[Sequence[Any]], float | None],
    *,
    seed: int = 20260927,
    resamples: int = 2000,
    alpha: float = 0.05,
) -> tuple[float, float] | None:
    """Percentile bootstrap CI of ``statistic`` over units resampled with replacement.

    Deterministic for a fixed seed. ``None`` when there are fewer than two
    units or the statistic is undefined on every resample.
    """
    if len(units) < 2:
        return None
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(resamples):
        sample = [units[rng.randrange(len(units))] for _ in units]
        value = statistic(sample)
        if value is not None:
            values.append(value)
    if not values:
        return None
    values.sort()
    lo = values[int(math.floor(alpha / 2 * (len(values) - 1)))]
    hi = values[int(math.ceil((1 - alpha / 2) * (len(values) - 1)))]
    return (lo, hi)


# ---------------------------------------------------------------------------
# Text heuristics
# ---------------------------------------------------------------------------


def topics(text: str) -> set[str]:
    return {name for name, pattern in TOPICS.items() if pattern.search(text or "")}


def review_topics(weaknesses: Iterable[str]) -> set[str]:
    found: set[str] = set()
    for weakness in weaknesses:
        found |= topics(weakness)
    return found


def review_criterion_ids(weaknesses: Iterable[str]) -> set[str]:
    ids = set()
    for weakness in weaknesses:
        match = CRITERION_PREFIX_RE.match(weakness or "")
        if match:
            ids.add(match.group(1))
    return ids


def jaccard(a: set[str], b: set[str]) -> float | None:
    union = a | b
    return len(a & b) / len(union) if union else None


def mean_pairwise_jaccard(sets: Sequence[set[str]]) -> float | None:
    values = [j for a, b in combinations(sets, 2) if (j := jaccard(a, b)) is not None]
    return mean(values)


def is_add_weakness(text: str) -> bool:
    return bool(ADD_RE.match(text or ""))


def has_limiting_word(text: str) -> bool:
    return bool(LIMITING_RE.search(text or ""))


def defect_line_ids(weaknesses: Iterable[Any]) -> set[str]:
    """Every ID the defect lines of a weakness list name; a ``Suggestion:`` line names none."""
    ids: set[str] = set()
    for weakness in weaknesses:
        match = DEFECT_LINE_RE.match(str(weakness or "").strip())
        if match:
            ids.update(match.group("ids").split(", "))
    return ids


def silent_deductions(checklist: Any, weaknesses: Iterable[Any]) -> tuple[list[str], int]:
    """Technical items below their maximum that no defect line names, and how
    many technical items are below their maximum at all.

    A deduction without a defect line leaves a repair nothing to act on. DE
    and LM items are judgments, never counted here, and a ``Suggestion:`` line
    carries no deduction. A review in the format before defect lines names
    nothing, so every deduction of such an arm reads as silent.
    """
    named = defect_line_ids(weaknesses)
    below = []
    for cid in TECHNICAL_IDS:
        item = checklist.get(cid) if isinstance(checklist, dict) else None
        if (
            isinstance(item, dict)
            and isinstance(item.get("score"), int | float)
            and isinstance(item.get("max"), int | float)
            and item["score"] < item["max"]
        ):
            below.append(cid)
    return [cid for cid in below if cid not in named], len(below)


# ---------------------------------------------------------------------------
# Records → units
# ---------------------------------------------------------------------------


def unit_key(record: dict[str, Any]) -> str:
    order = record.get("order")
    return f"{record['item']}__{order}" if order else str(record["item"])


def model_label(record: dict[str, Any]) -> str:
    """The resolved model id a record is grouped under.

    A session whose execution file named no model is ``unresolved (<alias>)``:
    kept apart from the resolved groups and never shown under its alias as if
    that were an id.
    """
    model = record.get("model")
    if isinstance(model, str) and model.strip() and model != "n/a":
        return model
    alias = record.get("model_alias")
    return f"unresolved ({alias})" if alias else "unresolved"


def group_key(record: dict[str, Any]) -> tuple[str, str]:
    return (str(record.get("kind") or "?"), model_label(record))


def ok_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in records if r.get("ok") and isinstance(r.get("score_typed"), int)]


def by_unit(records: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    units: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        units[unit_key(record)].append(record)
    for runs in units.values():
        runs.sort(key=lambda r: r.get("run") or 0)
    return dict(units)


def _criterion(record: dict[str, Any], cid: str) -> dict[str, Any] | None:
    item = (record.get("checklist") or {}).get(cid)
    if (
        isinstance(item, dict)
        and isinstance(item.get("score"), int | float)
        and isinstance(item.get("max"), int | float)
    ):
        return item
    return None


def is_auto_reject(record: dict[str, Any]) -> bool:
    return record.get("score_typed") == 0


# ---------------------------------------------------------------------------
# Per-group metrics
# ---------------------------------------------------------------------------


def criterion_metrics(units: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, float | None]]:
    out: dict[str, dict[str, float | None]] = {}
    for cid in CRITERIA_IDS:
        groups: list[list[float]] = []
        at_max: list[bool] = []
        for runs in units.values():
            values = []
            for record in runs:
                item = _criterion(record, cid)
                if item is None:
                    continue
                values.append(float(item["score"]))
                at_max.append(item["score"] >= item["max"])
            if values:
                groups.append(values)
        flat = [v for g in groups for v in g]
        out[cid] = {"mean": mean(flat), "at_max": share(at_max), "sd": pooled_sd(groups), "flip": flip_rate(groups)}
    return out


def total_metrics(units: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Typed and summed totals; units with an auto-reject run are reported apart."""
    clean = {k: runs for k, runs in units.items() if not any(is_auto_reject(r) for r in runs)}
    rejected = sorted(k for k in units if k not in clean)

    def stats(field: str) -> dict[str, float | None]:
        groups = [[float(r[field]) for r in runs if isinstance(r.get(field), int | float)] for runs in clean.values()]
        groups = [g for g in groups if g]
        return {"mean": mean(v for g in groups for v in g), "sd": pooled_sd(groups), "n_units": float(len(groups))}

    both = [
        r
        for runs in units.values()
        for r in runs
        if isinstance(r.get("score_typed"), int) and isinstance(r.get("checklist_sum"), int | float)
    ]
    return {
        "typed": stats("score_typed"),
        "sum": stats("checklist_sum"),
        "typed_ne_sum": share(r["score_typed"] != r["checklist_sum"] for r in both),
        "auto_reject_units": rejected,
    }


def verdict_metrics(units: dict[str, list[dict[str, Any]]], line: int = APPROVAL_LINE) -> dict[str, Any]:
    """Fresh items: straddle share and pairwise disagreement at the approval line."""
    out: dict[str, Any] = {}
    for field in ("score_typed", "checklist_sum"):
        straddle: list[bool] = []
        disagree: list[bool] = []
        for runs in units.values():
            passes = [r[field] >= line for r in runs if isinstance(r.get(field), int | float)]
            if len(passes) < 2:
                continue
            straddle.append(len(set(passes)) > 1)
            disagree.extend(a != b for a, b in combinations(passes, 2))
        key = "typed" if field == "score_typed" else "sum"
        out[key] = {"straddle": share(straddle), "straddle_units": len(straddle), "disagreement": share(disagree)}
    return out


def weakness_metrics(units: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    counts: list[float] = []
    topic_j: list[float] = []
    id_j: list[float] = []
    adds: list[bool] = []
    unlimited: list[bool] = []
    silent = below = 0
    silent_runs: list[bool] = []
    for runs in units.values():
        per_run_topics = []
        per_run_ids = []
        for record in runs:
            weaknesses = [str(w) for w in record.get("weaknesses") or []]
            counts.append(float(len(weaknesses)))
            if not is_auto_reject(record):  # an auto-reject scores 0 whatever the items say
                unnamed, deducted = silent_deductions(record.get("checklist"), weaknesses)
                silent += len(unnamed)
                below += deducted
                silent_runs.append(bool(unnamed))
            adds.extend(is_add_weakness(w) for w in weaknesses)
            per_run_topics.append(review_topics(weaknesses))
            per_run_ids.append(review_criterion_ids(weaknesses))
            for cid in CRITERIA_IDS:
                item = _criterion(record, cid)
                if item is not None and item["score"] < item["max"]:
                    unlimited.append(not has_limiting_word(str(item.get("comment") or "")))
        if len(runs) >= 2:
            value = mean_pairwise_jaccard(per_run_topics)
            if value is not None:
                topic_j.append(value)
            if all(per_run_ids):
                value = mean_pairwise_jaccard(per_run_ids)
                if value is not None:
                    id_j.append(value)
    return {
        "count_mean": mean(counts),
        "topic_jaccard": mean(topic_j),
        "id_jaccard": mean(id_j),
        "add_share": share(adds),
        "below_max_without_limiting_word": share(unlimited),
        # Technical items below their maximum that no defect line names, over
        # all such items, and the share of runs with at least one.
        "silent_deductions": silent / below if below else None,
        "silent_deductions_count": silent,
        "silent_deductions_n": below,
        "silent_deduction_runs": share(silent_runs),
        "taxonomy": TAXONOMY_VERSION,
        "limiting": LIMITING_VERSION,
    }


def _label_hit(label: dict[str, Any], record: dict[str, Any]) -> tuple[bool, bool]:
    """(regex matched a weakness, a listed criterion is below max with a matching comment)."""
    pattern = re.compile(label.get("match") or r"(?!)", re.IGNORECASE)
    in_weakness = any(pattern.search(str(w)) for w in record.get("weaknesses") or [])
    deducted = False
    for cid in label.get("criteria") or []:
        item = _criterion(record, cid)
        if item is not None and item["score"] < item["max"] and pattern.search(str(item.get("comment") or "")):
            deducted = True
    return in_weakness, deducted


def defect_hit(label: dict[str, Any], record: dict[str, Any]) -> bool:
    """A named defect is caught when a listed criterion is below max and the regex
    matches a weakness or that criterion's comment."""
    below = any(
        (item := _criterion(record, cid)) is not None and item["score"] < item["max"]
        for cid in label.get("criteria") or []
    )
    if not below:
        return False
    in_weakness, deducted = _label_hit(label, record)
    return in_weakness or deducted


def probe_false_alarm(label: dict[str, Any], record: dict[str, Any]) -> bool:
    """A permitted feature is flagged when a weakness names it or a listed criterion
    is deducted with a comment that names it."""
    in_weakness, deducted = _label_hit(label, record)
    return in_weakness or deducted


def _label_runs(label: dict[str, Any], runs: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """The runs a label applies to: all of them, or, for a label with a
    ``spec_source``, those whose reviewer saw the spec text from that source
    (a defect that only a later spec clause makes one)."""
    wanted = label.get("spec_source")
    return [r for r in runs if not wanted or r.get("spec_source") == wanted]


def defect_metrics(units: dict[str, list[dict[str, Any]]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_defect: dict[str, dict[str, Any]] = {}
    alarms: dict[str, dict[str, Any]] = {}
    for key, runs in units.items():
        item_labels = labels.get(str(runs[0]["item"])) or {}
        for label in item_labels.get("defects") or []:
            hits = [defect_hit(label, r) for r in _label_runs(label, runs)]
            if not hits:
                continue
            per_defect[f"{runs[0]['item']}/{label['id']}@{key}"] = {
                "runs": len(hits),
                "misses": hits.count(False),
                "always": all(hits) and bool(hits),
                "never": not any(hits),
            }
        for label in item_labels.get("permitted") or []:
            flags = [probe_false_alarm(label, r) for r in _label_runs(label, runs)]
            if not flags:
                continue
            alarms[f"{runs[0]['item']}/{label['id']}@{key}"] = {"runs": len(flags), "alarms": sum(flags)}
    runs_total = sum(d["runs"] for d in per_defect.values())
    probe_runs = sum(a["runs"] for a in alarms.values())
    return {
        "defect_runs": runs_total,
        "defect_misses": sum(d["misses"] for d in per_defect.values()),
        "miss_rate": (sum(d["misses"] for d in per_defect.values()) / runs_total) if runs_total else None,
        "detected_every_run": share(d["always"] for d in per_defect.values()),
        "never_detected": sorted(k for k, d in per_defect.items() if d["never"]),
        "per_defect": per_defect,
        "probe_runs": probe_runs,
        "false_alarms": sum(a["alarms"] for a in alarms.values()),
        "false_alarm_rate": (sum(a["alarms"] for a in alarms.values()) / probe_runs) if probe_runs else None,
        "per_probe": alarms,
    }


def _visible_improvements(record: dict[str, Any]) -> int:
    """Visible improvements the gate counts: never one that cites a permission.

    Reads ``regen_counts["visible"]`` (the gate record's semantics); a record
    without it counts every improvement with a ``where_visible``.
    """
    counts = record.get("regen_counts")
    if isinstance(counts, dict) and isinstance(counts.get("visible"), int):
        return int(counts["visible"])
    regen = record.get("regen")
    if not isinstance(regen, dict) or not isinstance(regen.get("improvements"), list):
        return 0
    return sum(1 for i in regen["improvements"] if isinstance(i, dict) and str(i.get("where_visible") or "").strip())


def _permission_citations(record: dict[str, Any]) -> int | None:
    """Improvements citing an "Expected, not a defect" bullet; None when unknown."""
    return _regen_count(record, "permission")


def _regen_count(record: dict[str, Any], key: str) -> int | None:
    """One of the record's ``regen_counts``; None when the record predates the key."""
    counts = record.get("regen_counts")
    value = counts.get(key) if isinstance(counts, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else None


RESCORE_CLASSES = ("defect", "suggestion", "obsolete")


def weakness_classes(record: dict[str, Any]) -> dict[str, str]:
    """``{W id: class}`` the review's ``prev_weaknesses`` gave, read as the gate reads it.

    The first entry per ``W`` wins; an unknown class reads as ``suggestion``.
    Empty for a review under older rules, which wrote no classification.
    """
    regen = record.get("regen")
    entries = regen.get("prev_weaknesses") if isinstance(regen, dict) else None
    out: dict[str, str] = {}
    for entry in entries if isinstance(entries, list) else []:
        ref = entry.get("ref") if isinstance(entry, dict) else None
        if not isinstance(ref, str) or not re.fullmatch(r"W[1-9]\d*", ref.strip().upper()):
            continue
        cls = str(entry.get("class") or "").strip().lower()
        out.setdefault(ref.strip().upper(), cls if cls in RESCORE_CLASSES else "suggestion")
    return out


def class_flips(units: dict[str, list[dict[str, Any]]]) -> list[bool]:
    """One flag per (unit, W id) seen in at least two classified runs: the class differs.

    A run that classified other W's but not this one reads it as the gate
    does, as a suggestion.
    """
    flips: list[bool] = []
    for runs in units.values():
        classified = [c for r in runs if (c := weakness_classes(r))]
        if len(classified) < 2:
            continue
        for ref in sorted({ref for c in classified for ref in c}):
            flips.append(len({c.get(ref, "suggestion") for c in classified}) > 1)
    return flips


def _canonical_ref(ref: Any) -> str:
    """``c2`` -> ``C2``, ``New`` -> ``new``: the gate's own coercion of a ref."""
    text = str(ref or "").strip()
    return "new" if text.lower() == "new" else text.upper()


def carrier_claimed(record: dict[str, Any], fixes: Sequence[dict[str, Any]]) -> bool | None:
    """Whether a regen review cites an improvement that can carry a merge.

    A carrier is a visible improvement the gate counts (not a permission, a
    non-empty ``where_visible``) that either cites an affirmative
    characteristic (a C id of the spec the reviewer saw that is not an
    "Expected, not a defect" bullet; an unlabeled bullet counts as affirmative,
    as the gate reads it) or whose ``what`` matches one of the pair's ``fixes``
    labels. It needs no field of a newer review prompt, so it reads the same
    under every rules version. ``None`` when the record does not say which
    characteristics the spec had.
    """
    spec = record.get("spec_characteristics")
    regen = record.get("regen")
    if not isinstance(spec, dict) or not isinstance(spec.get("count"), int) or not isinstance(regen, dict):
        return None
    permission = {_canonical_ref(ref) for ref in spec.get("permission") or []}
    affirmative = {f"C{i}" for i in range(1, spec["count"] + 1)} - permission
    patterns = [re.compile(str(label.get("match") or r"(?!)"), re.IGNORECASE) for label in fixes]
    for item in regen.get("improvements") or []:
        if not isinstance(item, dict):
            continue
        ref = _canonical_ref(item.get("ref"))
        if ref in permission or not str(item.get("where_visible") or "").strip():
            continue
        if ref in affirmative or any(p.search(str(item.get("what") or "")) for p in patterns):
            return True
    return False


def gate_metrics(units: dict[str, list[dict[str, Any]]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Regen units: verdict stability and accuracy, score spread, tolerance
    calibration on identity and near-identical pairs, order bias, and forward
    merges without a labeled carrier."""
    verdict_groups: list[list[str]] = []
    correct: list[bool] = []
    rescored: list[list[float]] = []
    new: list[list[float]] = []
    delta: list[list[float]] = []
    calibration: dict[str, dict[str, list[bool]]] = {
        "identity": {"below_tolerance": [], "visible_claims": [], "carrier_claims": []},
        "near-identical": {"below_tolerance": [], "visible_claims": [], "carrier_claims": []},
    }
    permission_cited: list[bool] = []
    obsolete_cited: list[bool] = []
    # Forward merges on items labeled for carriers: True when no carrier was cited.
    uncarried: list[bool] = []
    carrier_units = 0
    per_item: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for runs in units.values():
        item = str(runs[0]["item"])
        order = str(runs[0].get("order") or "forward")
        per_item[item][order] = runs
        item_labels = labels.get(item) or {}
        expected = (item_labels.get("expected") or {}).get(order)
        pair_class = item_labels.get("class")
        verdicts = [str((r.get("gate") or {}).get("verdict")) for r in runs if (r.get("gate") or {}).get("verdict")]
        if verdicts:
            verdict_groups.append(verdicts)
        if expected:
            correct.extend(v == expected for v in verdicts)
        fixes = item_labels.get("fixes")
        if order == "forward" and isinstance(fixes, list):
            carrier_units += 1
            for record in runs:
                if (record.get("gate") or {}).get("verdict") != "merge":
                    continue
                claimed = carrier_claimed(record, fixes)
                if claimed is not None:
                    uncarried.append(not claimed)
        rs, ns, ds = [], [], []
        for record in runs:
            prev = (record.get("gate") or {}).get("prev_rescored")
            score = record.get("score_typed")
            if isinstance(score, int):
                ns.append(float(score))
            if isinstance(prev, int) and isinstance(score, int):
                rs.append(float(prev))
                ds.append(float(score - prev))
                if pair_class in calibration:
                    calibration[pair_class]["below_tolerance"].append(score - prev < -1)
            carriers = _regen_count(record, "carriers")
            if pair_class in calibration:
                calibration[pair_class]["visible_claims"].append(_visible_improvements(record) > 0)
                if carriers is not None:
                    calibration[pair_class]["carrier_claims"].append(carriers > 0)
            cited = _permission_citations(record)
            if cited is not None:
                permission_cited.append(cited > 0)
            obsolete = _regen_count(record, "obsolete")
            if obsolete is not None:
                obsolete_cited.append(obsolete > 0)
        rescored.append(rs)
        new.append(ns)
        delta.append(ds)

    biases = []
    for orders in per_item.values():
        forward, reversed_ = orders.get("forward"), orders.get("reversed")
        if not forward or not reversed_:
            continue
        # X = the forward run's new version (A) and its predecessor (B).
        blind_a = mean(float(r["score_typed"]) for r in forward if isinstance(r.get("score_typed"), int))
        blind_b = mean(float(r["score_typed"]) for r in reversed_ if isinstance(r.get("score_typed"), int))
        rescore_a = mean(
            float(r["gate"]["prev_rescored"])
            for r in reversed_
            if isinstance((r.get("gate") or {}).get("prev_rescored"), int)
        )
        rescore_b = mean(
            float(r["gate"]["prev_rescored"])
            for r in forward
            if isinstance((r.get("gate") or {}).get("prev_rescored"), int)
        )
        if blind_a is None or blind_b is None or rescore_a is None or rescore_b is None:
            continue
        # Negative: a version scores lower as the predecessor than blind as
        # the new one — second-scored versions are marked down, which biases
        # the gate toward merge.
        biases.append(((rescore_a - blind_a) + (rescore_b - blind_b)) / 2)

    flips = class_flips(units)
    return {
        "verdict_flip": share(len(set(v)) > 1 for v in verdict_groups if len(v) >= 2),
        "accuracy": share(correct),
        "accuracy_n": len(correct),
        "sd_prev_rescored": pooled_sd(rescored),
        "sd_new": pooled_sd(new),
        "sd_delta": pooled_sd(delta),
        "calibration": {
            cls: {name: share(values) for name, values in parts.items()} | {"n": len(parts["visible_claims"])}
            for cls, parts in calibration.items()
        },
        "order_bias": mean(biases),
        "order_bias_items": len(biases),
        # Runs whose review cited a permission as an improvement (not counted
        # by the gate; a sign the reviewer misreads the characteristic kinds).
        "permission_cited": share(permission_cited),
        "permission_cited_n": len(permission_cited),
        # Runs citing a previous weakness the review itself classed obsolete.
        "obsolete_cited": share(obsolete_cited),
        "obsolete_cited_n": len(obsolete_cited),
        # (unit, W id) pairs whose class differs across runs: how stable the
        # re-score's defect / suggestion / obsolete reading is.
        "class_flip": share(flips),
        "class_flip_n": len(flips),
        # Forward merges whose review cited no carrier (no visible improvement
        # matching a `fixes` label or citing an affirmative C id), on the
        # forward units of items labeled for carriers (`carrier_units`).
        "merges_without_carrier": share(uncarried),
        "merges_without_carrier_count": sum(uncarried),
        "merges_without_carrier_n": len(uncarried),
        "carrier_units": carrier_units,
    }


def group_metrics(records: Sequence[dict[str, Any]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    units = by_unit(records)
    kind = str(records[0].get("kind")) if records else "?"
    out: dict[str, Any] = {
        "kind": kind,
        "model": model_label(records[0]) if records else "?",
        "runs": len(records),
        "units": len(units),
        "criteria": criterion_metrics(units),
        "total": total_metrics(units),
        "weaknesses": weakness_metrics(units),
        "defects": defect_metrics(units, labels),
    }
    if kind == "fresh":
        out["verdicts"] = verdict_metrics(units)
    if kind == "regen":
        out["gate"] = gate_metrics(units, labels)
    sds = [(cid, v["sd"]) for cid, v in out["criteria"].items() if v["sd"] is not None]
    out["noisiest_criteria"] = [
        {"id": cid, "sd": sd} for cid, sd in sorted(sds, key=lambda x: (-x[1], x[0]))[:3] if sd > 0
    ]
    return out


def arm_metrics(records: Sequence[dict[str, Any]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Everything for one arm: cell accounting plus metrics per (kind, model)."""
    errors = Counter(str(r.get("error_class") or "unknown") for r in records if not r.get("ok"))
    good = ok_records(records)
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in good:
        groups[group_key(record)].append(record)
    return {
        "cells": {"total": len(records), "ok": len(good), "errors": dict(sorted(errors.items()))},
        "cost_usd": sum(float(r["cost_usd"]) for r in records if isinstance(r.get("cost_usd"), int | float)),
        "models": sorted({model_label(r) for r in good}),
        "groups": {f"{kind}|{model}": group_metrics(rs, labels) for (kind, model), rs in sorted(groups.items())},
    }


# ---------------------------------------------------------------------------
# Arm comparison
# ---------------------------------------------------------------------------


def _unit_totals(records: Sequence[dict[str, Any]]) -> dict[str, list[float]]:
    return {
        key: [float(r["score_typed"]) for r in runs]
        for key, runs in by_unit(ok_records(records)).items()
        if not any(is_auto_reject(r) for r in runs)
    }


def compare_arms(
    base: Sequence[dict[str, Any]],
    cand: Sequence[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    *,
    seed: int = 20260927,
) -> dict[str, Any]:
    """Candidate minus baseline, paired by unit, per kind.

    Soft flags only (never blocking): ``noise_up`` when the CI of Δ pooled SD
    lies above 0; ``model_changed`` when the resolved models differ;
    ``harness_changed`` when the harness version or action SHA differ;
    ``label set differs`` when the arms counted different defects or probes.
    """
    out: dict[str, Any] = {"kinds": {}, "flags": []}
    for kind in ("fresh", "regen"):
        b = _unit_totals([r for r in base if r.get("kind") == kind])
        c = _unit_totals([r for r in cand if r.get("kind") == kind])
        paired = sorted(set(b) & set(c))
        if not paired:
            continue

        def d_mean(units: Sequence[str], b: dict[str, list[float]] = b, c: dict[str, list[float]] = c) -> float | None:
            diffs = [statistics.fmean(c[u]) - statistics.fmean(b[u]) for u in units]
            return mean(diffs)

        def d_sd(units: Sequence[str], b: dict[str, list[float]] = b, c: dict[str, list[float]] = c) -> float | None:
            sb, sc = pooled_sd([b[u] for u in units]), pooled_sd([c[u] for u in units])
            return None if sb is None or sc is None else sc - sb

        base_arm = arm_metrics([r for r in base if r.get("kind") == kind], labels)
        cand_arm = arm_metrics([r for r in cand if r.get("kind") == kind], labels)
        entry: dict[str, Any] = {
            "paired_units": len(paired),
            "delta_mean": d_mean(paired),
            "delta_mean_ci": bootstrap_ci(paired, d_mean, seed=seed),
            "delta_sd": d_sd(paired),
            "delta_sd_ci": bootstrap_ci(paired, d_sd, seed=seed),
            "base": _headline(base_arm),
            "cand": _headline(cand_arm),
        }
        ci = entry["delta_sd_ci"]
        if ci is not None and ci[0] > 0:
            out["flags"].append(f"noise up ({kind})")
        out["kinds"][kind] = entry

    def facet(records: Sequence[dict[str, Any]], field: str) -> set[str]:
        return {str(r.get(field)) for r in ok_records(records)}

    # An unresolved model can never be shown to match another arm's, so any
    # unresolved group flags as well.
    base_models = {model_label(r) for r in ok_records(base)}
    cand_models = {model_label(r) for r in ok_records(cand)}
    if base_models != cand_models or any(label.startswith("unresolved") for label in base_models | cand_models):
        out["flags"].append("model changed")
    if facet(base, "harness_version") != facet(cand, "harness_version") or facet(base, "action_sha") != facet(
        cand, "action_sha"
    ):
        out["flags"].append("harness changed")
    if facet(base, "set") != facet(cand, "set"):
        out["flags"].append("set changed")
    # A label with a ``spec_source`` counts in one arm only, and an arm that
    # lost a unit lacks its labels: the miss and false-alarm rates of the two
    # arms then pool different labels.
    if _label_keys(arm_metrics(base, labels)) != _label_keys(arm_metrics(cand, labels)):
        out["flags"].append("label set differs")
    return out


def _label_keys(arm: dict[str, Any]) -> set[str]:
    """Every defect and probe an arm's groups counted."""
    return {
        key
        for group in arm["groups"].values()
        for part in ("per_defect", "per_probe")
        for key in group["defects"][part]
    }


def _headline(arm: dict[str, Any]) -> dict[str, Any]:
    """Flip, miss and false-alarm rates pooled across an arm's groups."""
    flips, misses, runs, alarms, probes = [], 0, 0, 0, 0
    for group in arm["groups"].values():
        for crit in group["criteria"].values():
            if crit["flip"] is not None:
                flips.append(crit["flip"])
        misses += group["defects"]["defect_misses"]
        runs += group["defects"]["defect_runs"]
        alarms += group["defects"]["false_alarms"]
        probes += group["defects"]["probe_runs"]
    return {
        "criterion_flip_mean": mean(flips),
        "miss_rate": misses / runs if runs else None,
        "false_alarm_rate": alarms / probes if probes else None,
    }


# ---------------------------------------------------------------------------
# Regen gate monitoring (production records from PR-comment markers)
# ---------------------------------------------------------------------------


def _summary(values: Sequence[float], seed: int) -> dict[str, Any]:
    return {
        "n": len(values),
        "mean": mean(values),
        "median": statistics.median(values) if values else None,
        "sd": statistics.stdev(values) if len(values) >= 2 else None,
        "ci": bootstrap_ci(list(values), lambda s: mean(s), seed=seed),
    }


def _week(at: Any) -> str:
    try:
        stamp = datetime.fromisoformat(str(at).replace("Z", "+00:00"))
    except ValueError:
        return "unknown"
    year, week, _ = stamp.isocalendar()
    return f"{year}-W{week:02d}"


def gate_monitor(
    records: Sequence[dict[str, Any]], comparable: Callable[[dict[str, Any]], bool], *, seed: int = 20260927
) -> dict[str, Any]:
    """Aggregate production gate records.

    ``drift`` is ``prev_rescored - prev_stored`` (how the same predecessor
    scores today versus its stored review); ``margin`` is ``new -
    prev_rescored``. ``comparable`` says whether a record's stored review ran
    under the same model and rules as today's review — only then does drift
    isolate contrast bias from rules, model and render age.

    ``improvements`` reads the record's counts as the gate wrote them:
    ``visible`` holds only the improvements the gate counted (never one that
    cites an "Expected, not a defect" bullet), ``permission`` the cited
    permissions. A record without ``permission`` (none is expected: the key
    shipped with the first record) is left out of the permission shares.

    From P3 on, a record also carries ``obsolete``, ``carriers``,
    ``suggestion``, ``unverified`` and ``de_lm``, and its ``visible`` excludes
    obsolete citations as well; an older record's ``visible`` still counts
    them. Records without the P3 keys are left out of the carrier, obsolete,
    unverified and design-or-library shares (``carrier_n`` is their count).

    From P3.1 on, a record also carries ``addition``, ``polish``, ``no_kind``,
    ``carriers_pn`` and the ``by_kind`` histogram. Only those records
    (``kind_n``) enter the addition and polish shares (decisions listing at
    least one item of that kind, from ``by_kind``), the no-kind share
    (decisions with a would-be carrier without a kind, from ``no_kind``),
    ``kind_valid_share`` (listed improvements that name a
    kind) and ``pn_only_merge_share`` (merges whose every carrier is a ``P``
    or ``new`` item, over ``pn_merge_n`` merges).

    From P9b on, a keep record carries ``writeback``: what happened to the
    session's re-score of the live implementation (``opened``,
    ``unchanged``, ``no_rescore``, ``invalid``, ``stale`` or ``failed``).
    ``writeback`` counts those values over the keeps that carry the key.

    From P8 on, a record also carries ``code`` (the code improvements that
    held). ``code_path_merges`` counts the merges with ``carriers == 0`` and
    ``code >= 1`` — the code path — over the ``code_path_n`` records with both
    keys; suggestions may ride along, so ``visible`` is not tested.
    """
    n = len(records)
    merges = sum(1 for r in records if r.get("verdict") == "merge")
    codes = Counter(str(r.get("code") or "unknown") for r in records)

    def drift_of(rs: Iterable[dict[str, Any]]) -> list[float]:
        return [
            float(r["prev_rescored"] - r["prev_stored"])
            for r in rs
            if isinstance(r.get("prev_rescored"), int) and isinstance(r.get("prev_stored"), int)
        ]

    comparable_records = [r for r in records if comparable(r)]
    margins = [
        float(r["new"] - r["prev_rescored"])
        for r in records
        if isinstance(r.get("new"), int) and isinstance(r.get("prev_rescored"), int)
    ]
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_lib: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_week: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_model[str(record.get("model") or "n/a")].append(record)
        by_lib[str(record.get("lib") or "n/a")].append(record)
        by_week[_week(record.get("at"))].append(record)

    def counts(record: dict[str, Any]) -> dict[str, Any] | None:
        value = record.get("improvements")
        return value if isinstance(value, dict) else None

    def count(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    counted = [(r, c) for r in records if (c := counts(r)) is not None]
    with_permission = [(r, c) for r, c in counted if count(c.get("permission")) is not None]
    visible = [float(v) for _, c in counted if (v := count(c.get("visible"))) is not None]
    cited = [(r, c) for r, c in with_permission if c["permission"] > 0]
    # P3 records (the classification counts); older ones are left out.
    classified = [c for _, c in counted if count(c.get("carriers")) is not None]
    carriers = [float(c["carriers"]) for c in classified]

    def with_any(key: str) -> int:
        return sum(1 for c in classified if (count(c.get(key)) or 0) > 0)

    def over_classified(n: int) -> float | None:
        return n / len(classified) if classified else None

    permission_or_obsolete = sum(
        1 for _, c in with_permission if c["permission"] > 0 or (count(c.get("obsolete")) or 0) > 0
    )
    # P3.1 records (the kind counts); older ones are left out.
    kinded = [(r, c) for r, c in counted if count(c.get("no_kind")) is not None]

    def by_kind(c: dict[str, Any]) -> dict[str, Any]:
        value = c.get("by_kind")
        return value if isinstance(value, dict) else {}

    def kinded_share(present: Callable[[dict[str, Any]], bool]) -> float | None:
        return sum(1 for _, c in kinded if present(c)) / len(kinded) if kinded else None

    histograms = [by_kind(c) for _, c in kinded]
    listed = sum(count(v) or 0 for h in histograms for v in h.values())
    unnamed = sum(count(h.get("none")) or 0 for h in histograms)
    carried_merges = [c for r, c in kinded if r.get("verdict") == "merge" and (count(c.get("carriers")) or 0) > 0]
    pn_only = sum(1 for c in carried_merges if count(c.get("carriers_pn")) == count(c.get("carriers")))
    # P8 records; older ones lack ``code`` and are left out.
    coded = [(r, c) for r, c in counted if count(c.get("code")) is not None and count(c.get("carriers")) is not None]
    improvements: dict[str, Any] = {
        "n": len(counted),
        "visible_mean": mean(visible),
        "with_visible": share(v > 0 for v in visible),
        "permission_n": len(with_permission),
        "permission_cited": len(cited),
        "permission_cited_share": len(cited) / len(with_permission) if with_permission else None,
        # Kept with a cited permission and nothing else visible that counts.
        "permission_only_keeps": sum(
            1 for r, c in cited if r.get("code") == "no_visible_improvement" and count(c.get("visible")) == 0
        ),
        "permission_or_obsolete_cited": permission_or_obsolete,
        "permission_or_obsolete_share": permission_or_obsolete / len(with_permission) if with_permission else None,
        "carrier_n": len(classified),
        "carriers_mean": mean(carriers),
        "with_carrier": share(v > 0 for v in carriers),
        "no_defect_improvement": codes.get("no_defect_improvement", 0),
        "obsolete_cited": with_any("obsolete"),
        "obsolete_cited_share": over_classified(with_any("obsolete")),
        "unverified_share": over_classified(with_any("unverified")),
        "de_lm_share": over_classified(with_any("de_lm")),
        "kind_n": len(kinded),
        # Any listed item of that kind (by_kind), whatever its class.
        "addition_share": kinded_share(lambda c: (count(by_kind(c).get("addition")) or 0) > 0),
        "polish_share": kinded_share(lambda c: (count(by_kind(c).get("polish")) or 0) > 0),
        # A would-be carrier without a kind: the top-level count, which the alarm reads.
        "no_kind_share": kinded_share(lambda c: (count(c.get("no_kind")) or 0) > 0),
        # Improvements, not decisions: the share of listed items that name a kind.
        "kind_valid_share": (listed - unnamed) / listed if listed else None,
        "pn_merge_n": len(carried_merges),
        "pn_only_merge_share": pn_only / len(carried_merges) if carried_merges else None,
        # P8 records (the code count): merges no carrier carried, only a code improvement.
        "code_path_n": len(coded),
        "code_path_merges": sum(
            1
            for r, c in coded
            if r.get("verdict") == "merge" and count(c.get("carriers")) == 0 and (count(c.get("code")) or 0) >= 1
        ),
    }

    # P9b keeps; older records and merges carry no `writeback`.
    writeback = Counter(
        str(r["writeback"]) for r in records if r.get("verdict") == "keep" and isinstance(r.get("writeback"), str)
    )
    writeback_n = sum(writeback.values())

    drift_comparable = _summary(drift_of(comparable_records), seed)
    report: dict[str, Any] = {
        "n": n,
        "merge_rate": merges / n if n else None,
        "codes": dict(codes.most_common()),
        "drift_all": _summary(drift_of(records), seed),
        "drift_comparable": drift_comparable,
        "drift_by_model": {k: _summary(drift_of(v), seed) for k, v in sorted(by_model.items())},
        "drift_by_library": {k: _summary(drift_of(v), seed) for k, v in sorted(by_lib.items())},
        "margin": _summary(margins, seed),
        "margin_within_tolerance": share(-1 <= m <= 0 for m in margins),
        "improvements": improvements,
        "writeback": {"n": writeback_n, "counts": dict(writeback.most_common())},
        "weekly": {
            week: {
                "n": len(rs),
                "merge_rate": sum(1 for r in rs if r.get("verdict") == "merge") / len(rs),
                "drift_mean": mean(drift_of(rs)),
            }
            for week, rs in sorted(by_week.items())
        },
        "alarms": [],
    }
    alarms: list[str] = report["alarms"]
    if drift_comparable["n"] >= 20 and (drift_comparable["mean"] or 0) <= -1.5:
        alarms.append(
            f"possible contrast bias: comparable re-scores average {drift_comparable['mean']:+.1f} "
            f"below their stored score (n={drift_comparable['n']}) — check the harness's order bias on the current rules"
        )
    invalid = codes.get("regen_json_invalid", 0)
    if n >= 10 and invalid / n > 0.10:
        alarms.append(f"regen_json_invalid in {invalid}/{n} decisions — a contract or prompt problem")
    if n >= 30 and report["merge_rate"] is not None and not 0.05 <= report["merge_rate"] <= 0.50:
        alarms.append(f"merge rate {report['merge_rate']:.0%} over {n} decisions — look at the reason codes")
    if improvements["permission_n"] >= 10 and (improvements["permission_or_obsolete_share"] or 0) > 0.10:
        alarms.append(
            f"reviews cite an 'Expected, not a defect' bullet or an obsolete weakness as an improvement in "
            f"{improvements['permission_or_obsolete_cited']}/{improvements['permission_n']} decisions — the 8b "
            "prompt or the specs' characteristic kinds need a look"
        )
    invalid_writeback = writeback.get("invalid", 0)
    if writeback_n >= 10 and invalid_writeback / writeback_n > 0.10:
        alarms.append(
            f"review_prev.json invalid in {invalid_writeback}/{writeback_n} keeps, so their re-scores were not "
            "stored — the 8b step 5 prompt needs work"
        )
    # No alarm for de_lm: DE deductions are normal on specs that are not -basic.
    if improvements["carrier_n"] >= 10 and (improvements["unverified_share"] or 0) > 0.20:
        alarms.append(
            f"an unverified claim (a rule the scores do not confirm, or none) in "
            f"{improvements['unverified_share']:.0%} of {improvements['carrier_n']} decisions — the review's "
            "self-check or the defect definitions need work"
        )
    if improvements["kind_n"] >= 10 and (improvements["no_kind_share"] or 0) > 0.05:
        alarms.append(
            f"a would-be carrier without a kind in {improvements['no_kind_share']:.0%} of "
            f"{improvements['kind_n']} decisions — the 8b kind sentence or the self-check needs a look"
        )
    return report


# ---------------------------------------------------------------------------
# Live first reviews (production review comments of first-generation PRs)
# ---------------------------------------------------------------------------


REVIEW_HEADING_RE = re.compile(r"^## AI Review - Attempt (\d+)/\d+", re.MULTILINE)
REVIEW_SCORE_RE = re.compile(r"^### Score: (\d{1,3})/100", re.MULTILINE)
REVIEW_ITEM_RE = re.compile(r"^- \[[ xX]\] ((?:VQ|DE|SC|DQ|CQ|LM)-\d{2}):[^\n]*?\((\d+)/(\d+)\)", re.MULTILINE)
REVIEW_WEAKNESSES_RE = re.compile(r"^### Weaknesses[ \t]*\n(.*?)(?=^#{2,3} |\Z)", re.MULTILINE | re.DOTALL)
# impl-review's own commit on the PR branch, and the merge of main before the merge.
BOOKKEEPING_COMMIT_RE = re.compile(r"^(chore\(|Merge )")
NEAR_LINE = (APPROVAL_LINE, APPROVAL_LINE + 1)


def parse_review_comment(body: str) -> dict[str, Any] | None:
    """One ``## AI Review - Attempt N/3`` comment as impl-review posts it.

    Returns the attempt, the typed score, the 24 item scores in the record's
    ``checklist`` shape and the weakness lines; ``None`` for any other comment
    or a review without a score line.
    """
    heading = REVIEW_HEADING_RE.search(body or "")
    score = REVIEW_SCORE_RE.search(body or "")
    if not heading or not score or int(score.group(1)) > 100:
        return None
    checklist: dict[str, dict[str, int]] = {}
    for cid, value, top in REVIEW_ITEM_RE.findall(body):
        checklist.setdefault(cid, {"score": int(value), "max": int(top)})
    section = REVIEW_WEAKNESSES_RE.search(body)
    weaknesses = [
        line[2:].strip() for line in (section.group(1) if section else "").splitlines() if line.startswith("- ")
    ]
    return {
        "attempt": int(heading.group(1)),
        "score": int(score.group(1)),
        "checklist": checklist,
        "weaknesses": weaknesses,
    }


def _points(review: dict[str, Any], ids: Iterable[str]) -> int | None:
    """Sum of the listed items; ``None`` when the review lacks one of them."""
    total = 0
    for cid in ids:
        item = review["checklist"].get(cid)
        if item is None:
            return None
        total += int(item["score"])
    return total


def _gain(before: dict[str, Any], after: dict[str, Any], ids: Iterable[str]) -> int | None:
    ids = tuple(ids)
    a, b = _points(before, ids), _points(after, ids)
    return None if a is None or b is None else b - a


def repair_committed(commits: Sequence[dict[str, Any]], review_at: str, next_review_at: str) -> bool:
    """Whether a commit other than bookkeeping landed between two reviews.

    ``commits`` hold ``at`` (an ISO timestamp, compared as text) and
    ``headline``. impl-review's score commit and a merge of ``main`` are
    bookkeeping; anything else in the window is the repair's change.
    """
    return any(
        review_at < str(c.get("at") or "") < next_review_at
        and not BOOKKEEPING_COMMIT_RE.match(str(c.get("headline") or ""))
        for c in commits
    )


def first_reviews(pulls: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate the live reviews of first-generation pull requests.

    Each pull holds ``number``, ``spec_id``, ``library``, ``reviews`` (parsed
    comments with their ``at`` timestamp, in posting order) and ``commits``.
    A pull's first review is its attempt-1 review (a pull whose first comment
    is a later attempt has none); every later one follows a repair. Reports the first-review histogram and the share at the approval
    line or one above it, per spec the between-library SD and the items no
    library differs on, silent deductions, and per repair the gain on the
    technical against the judgment items and whether the repair committed.
    """
    firsts = [(p, p["reviews"][0]) for p in pulls if p.get("reviews") and p["reviews"][0]["attempt"] == 1]
    scores = [r["score"] for _, r in firsts]
    by_spec: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pull, review in firsts:
        by_spec[str(pull["spec_id"])].append(review)
    specs = {}
    for spec_id, reviews in sorted(by_spec.items()):
        totals = [float(r["score"]) for r in reviews]
        constant = []
        for cid in CRITERIA_IDS:
            values = {r["checklist"][cid]["score"] for r in reviews if cid in r["checklist"]}
            if len(reviews) >= 2 and len(values) == 1:
                constant.append(cid)
        specs[spec_id] = {
            "n": len(reviews),
            "mean": mean(totals),
            "sd": statistics.stdev(totals) if len(totals) >= 2 else None,
            "zero_variance": constant,
        }
    silent = below = 0
    silent_pulls = []
    for pull, review in firsts:
        unnamed, deducted = silent_deductions(review["checklist"], review["weaknesses"])
        silent += len(unnamed)
        below += deducted
        if unnamed:
            silent_pulls.append({"number": pull["number"], "items": unnamed})
    repairs = []
    for pull in pulls:
        reviews = pull.get("reviews") or []
        for before, after in zip(reviews, reviews[1:], strict=False):
            repairs.append(
                {
                    "number": pull["number"],
                    "library": pull["library"],
                    "from": before["score"],
                    "to": after["score"],
                    "technical": _gain(before, after, TECHNICAL_IDS),
                    "judgment": _gain(before, after, JUDGMENT_IDS),
                    "committed": repair_committed(pull.get("commits") or [], str(before["at"]), str(after["at"])),
                }
            )
    return {
        "pulls": len(pulls),
        "first_reviews": len(firsts),
        "histogram": dict(sorted(Counter(scores).items())),
        "mean": mean(float(s) for s in scores),
        "sd": statistics.stdev(scores) if len(scores) >= 2 else None,
        "approved_first": sum(1 for s in scores if s >= APPROVAL_LINE),
        "near_line": share(s in NEAR_LINE for s in scores),
        "specs": specs,
        "silent_deductions": silent / below if below else None,
        "silent_deductions_count": silent,
        "silent_deductions_n": below,
        "silent_pulls": silent_pulls,
        "repairs": repairs,
        "repair_gain_technical": sum(r["technical"] or 0 for r in repairs),
        "repair_gain_judgment": sum(r["judgment"] or 0 for r in repairs),
        "repairs_without_commit": [r["number"] for r in repairs if not r["committed"]],
    }
