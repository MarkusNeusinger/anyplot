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
"code"}``), ``regen`` (the parsed ``review_regen.json``) and ``regen_counts``
(``{"total", "visible", "permission"}``, the gate record's improvement
counts).

Labels (from the set manifest, applied at report time so a corrected label
re-scores old records): ``defects`` and ``permitted`` per item
(``[{"id", "criteria", "match"}]``), ``expected`` gate verdicts per order and
the pair ``class`` (``identity``, ``near-identical`` or ``different``).
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
ADD_RE = re.compile(r"^\s*(?:\W*\b(?:VQ|DE|SC|DQ|CQ|LM)-\d{2}\W*)?(?:add|consider adding|include|introduce)\b", re.I)
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
    for runs in units.values():
        per_run_topics = []
        per_run_ids = []
        for record in runs:
            weaknesses = [str(w) for w in record.get("weaknesses") or []]
            counts.append(float(len(weaknesses)))
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


def defect_metrics(units: dict[str, list[dict[str, Any]]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_defect: dict[str, dict[str, Any]] = {}
    alarms: dict[str, dict[str, Any]] = {}
    for key, runs in units.items():
        item_labels = labels.get(str(runs[0]["item"])) or {}
        for label in item_labels.get("defects") or []:
            hits = [defect_hit(label, r) for r in runs]
            per_defect[f"{runs[0]['item']}/{label['id']}@{key}"] = {
                "runs": len(hits),
                "misses": hits.count(False),
                "always": all(hits) and bool(hits),
                "never": not any(hits),
            }
        for label in item_labels.get("permitted") or []:
            flags = [probe_false_alarm(label, r) for r in runs]
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
    counts = record.get("regen_counts")
    if isinstance(counts, dict) and isinstance(counts.get("permission"), int):
        return int(counts["permission"])
    return None


def gate_metrics(units: dict[str, list[dict[str, Any]]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Regen units: verdict stability and accuracy, score spread, tolerance
    calibration on identity and near-identical pairs, and order bias."""
    verdict_groups: list[list[str]] = []
    correct: list[bool] = []
    rescored: list[list[float]] = []
    new: list[list[float]] = []
    delta: list[list[float]] = []
    calibration: dict[str, dict[str, list[bool]]] = {
        "identity": {"below_tolerance": [], "visible_claims": []},
        "near-identical": {"below_tolerance": [], "visible_claims": []},
    }
    permission_cited: list[bool] = []
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
            if pair_class in calibration:
                calibration[pair_class]["visible_claims"].append(_visible_improvements(record) > 0)
            cited = _permission_citations(record)
            if cited is not None:
                permission_cited.append(cited > 0)
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
    ``harness_changed`` when the harness version or action SHA differ.
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
    return out


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
    }

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
    if improvements["permission_n"] >= 10 and (improvements["permission_cited_share"] or 0) > 0.10:
        alarms.append(
            f"reviews cite an 'Expected, not a defect' bullet as an improvement in "
            f"{improvements['permission_cited']}/{improvements['permission_n']} decisions — the 8b prompt or "
            "the specs' characteristic kinds need a look"
        )
    return report
