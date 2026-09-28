"""Tests for automation.scripts.review_retest — the review retest harness CLI."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import review_retest as rt


REPO_ROOT = Path(__file__).resolve().parents[4]
GATE_SCRIPT = REPO_ROOT / "automation" / "scripts" / "regen_gate.py"
MANIFEST = REPO_ROOT / "automation" / "retest" / "set-v1.yaml"
NOW = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
A = "a" * 40
B = "b" * 40
ACTION = "c" * 40

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


def fake_png(width: int = 3200, height: int = 1800, salt: bytes = b"") -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    chunk = struct.pack(">I", 13) + b"IHDR" + ihdr + struct.pack(">I", zlib.crc32(b"IHDR" + ihdr))
    return b"\x89PNG\r\n\x1a\n" + chunk + salt


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest(**overrides: Any) -> dict[str, Any]:
    manifest = {
        "version": 1,
        "set": "v1",
        "gcs_prefix": "retest/sets/v1",
        "baseline_rules_sha": A,
        "spec_commit": A,
        "labels": "draft",
        "items": [
            {
                "id": "f-bubble-basic-matplotlib",
                "kind": "fresh",
                "tier": "core",
                "spec_id": "bubble-basic",
                "library": "matplotlib",
                "new": {"commit": A, "render": "production"},
                "defects": [{"id": "D1", "criteria": ["VQ-03"], "match": "legend"}],
                "permitted": [],
            },
            {
                "id": "r-bubble-basic-matplotlib-b-a",
                "kind": "regen",
                "tier": "core",
                "spec_id": "bubble-basic",
                "library": "matplotlib",
                "class": "different",
                "new": {"commit": B, "render": "production"},
                "prev": {"commit": A, "render": "production"},
                "expected": None,
            },
            {
                "id": "f-scatter-basic-ggplot2",
                "kind": "fresh",
                "tier": "full",
                "spec_id": "scatter-basic",
                "library": "ggplot2",
                "new": {"commit": A, "render": "production"},
            },
        ],
    }
    manifest.update(overrides)
    return manifest


def _confirmed_manifest() -> dict[str, Any]:
    manifest = _manifest(labels="confirmed")
    manifest["items"][1]["expected"] = {"forward": "merge", "reversed": "keep"}
    return manifest


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestManifest:
    def test_shipped_manifest_is_valid(self):
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        assert rt.validate_manifest(manifest) == []
        assert manifest["baseline_rules_sha"].startswith("0674ab6b5")
        core = [i for i in manifest["items"] if i["tier"] == "core"]
        assert sum(1 for i in core if i["kind"] == "fresh") == 15
        assert {i["library"] for i in core if i["kind"] == "fresh"} == set(rt.LIBRARY_LANGUAGE)
        identity = {i["id"] for i in core if i.get("class") == "identity"}
        assert {"r-bubble-basic-chartjs-v5-v5", "r-bubble-basic-letsplot-v3-v3"} <= identity  # decision D14

    def test_shipped_labels_are_complete(self):
        """The owner's confirmation (decision D4) is the one-line switch to `labels: confirmed`."""
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        assert rt.validate_manifest({**manifest, "labels": "confirmed"}) == []
        core_fresh = [i for i in manifest["items"] if i["tier"] == "core" and i["kind"] == "fresh"]
        assert all(i["defects"] for i in core_fresh), "every core fresh item carries its named defect"
        for item in manifest["items"]:
            if item["kind"] == "regen" and item["class"] == "identity":
                assert item["expected"] == {"forward": "keep", "reversed": "keep"}, item["id"]

    def test_valid_example(self):
        assert rt.validate_manifest(_manifest()) == []

    @pytest.mark.parametrize(
        ("mutate", "message"),
        [
            (lambda m: m["items"].append(copy.deepcopy(m["items"][0])), "duplicate id"),
            (lambda m: m["items"][0].update(kind="other"), "kind must be"),
            (lambda m: m["items"][0]["new"].update(commit="abc123"), "full 40-hex"),
            (lambda m: m["items"][0].update(library="excel"), "unknown library"),
            (lambda m: m["items"][0]["defects"][0].update(criteria=["XX-01"]), "known criterion ids"),
            (lambda m: m["items"][0]["defects"][0].update(match="(unclosed"), "does not compile"),
            (lambda m: m["items"][1].update({"class": "identity"}), "identity pair needs"),
            (lambda m: m["items"][1].update(expected={"forward": "keep"}), "expected must give"),
            (lambda m: m.update(labels="confirmed"), "confirmed labels need expected"),
            (lambda m: m["items"][0].update(prev={"commit": A, "render": "production"}), "fresh item has no prev"),
            (lambda m: m["items"][0]["new"].update(render="somewhere"), "render must be"),
            (lambda m: m.update(gcs_prefix="elsewhere"), "gcs_prefix"),
            (lambda m: m["items"][0].update(id="Bad_ID"), "id must match"),
        ],
    )
    def test_invalid(self, mutate, message):
        manifest = _manifest()
        mutate(manifest)
        assert any(message in e for e in rt.validate_manifest(manifest)), rt.validate_manifest(manifest)

    def test_library_map_matches_core_constants(self):
        from core.constants import LIBRARY_LANGUAGES, library_file_extension

        assert rt.LIBRARY_LANGUAGE == LIBRARY_LANGUAGES
        assert {lib: rt.ext_of(lib) for lib in rt.LIBRARY_LANGUAGE} == {
            lib: library_file_extension(lib) for lib in LIBRARY_LANGUAGES
        }

    def test_metadata_reset_keys_match_impl_generate(self):
        workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/impl-generate.yml").read_text(encoding="utf-8"))
        step = next(
            s
            for job in workflow["jobs"].values()
            for s in job["steps"]
            if s.get("name") == "Create library metadata file"
        )
        block = step["run"].split("data = {", 1)[1].split("\n}", 1)[0]
        keys = tuple(re.findall(r"^\s*'([a-z_]+)':", block, re.MULTILINE))
        assert keys == rt.IMPL_GENERATE_METADATA_KEYS


class TestLabelGate:
    """Draft labels are validated but never reach a report (decision D4)."""

    def test_draft_labels_are_ignored(self):
        labels = rt.item_labels(_manifest())
        assert labels["f-bubble-basic-matplotlib"]["defects"] == []
        assert labels["f-bubble-basic-matplotlib"]["permitted"] == []
        # The pair class is measured, not a label: it always applies.
        assert labels["r-bubble-basic-matplotlib-b-a"]["class"] == "different"

    def test_confirmed_labels_apply(self):
        labels = rt.item_labels(_confirmed_manifest())
        assert [d["id"] for d in labels["f-bubble-basic-matplotlib"]["defects"]] == ["D1"]
        assert labels["r-bubble-basic-matplotlib-b-a"]["expected"] == {"forward": "merge", "reversed": "keep"}


# Scoped defect patterns of set v1 (PR #11964 review): each matches a phrasing
# of its own defect and not a weakness about something else, so an unrelated
# weakness is never credited as the named defect.
SCOPED_LABELS: dict[tuple[str, str], tuple[list[str], list[str]]] = {
    ("f-area-elevation-profile-seaborn", "D1"): (
        [
            "Y-axis label 'Elevation (m)' is partially cut off at the left edge",
            "The y-axis title touches the left canvas edge",
        ],
        ["the legend is clipped at the right edge", "The title is cut off at the top"],
    ),
    ("f-bar-horizontal-makie", "D2"): (
        [
            "Title hierarchy is inverted: the subtitle appears above the title",
            "Title and subtitle are in the wrong order",
        ],
        ["Visual hierarchy between the bars is weak", "The legend is placed above the title"],
    ),
    ("f-bode-basic-altair", "D1"): (
        [
            "In the dark render, axis titles and tick labels are dark on dark and nearly illegible",
            "Dark render: labels and titles are dark gray on near-black and nearly unreadable",
            "Axis labels use dark gray text on the dark background",
        ],
        [
            "Tick labels are small and hard to read at this size",
            "Low contrast between the magnitude and phase curves",
            "In the dark render the legend text is illegible",
            "The chart title has low contrast in the dark render",
            "Data labels are hard to read in dark mode",
        ],
    ),
    ("f-waterfall-basic-muix", "D2"): (
        [
            "Value labels show the running total instead of each step's change",
            "Value labels are cumulative rather than incremental",
            "The data labels read as cumulative totals",
        ],
        [
            "The final cumulative total bar has no label",
            "Colors do not change between positive and negative steps",
            "Value labels on the cumulative total bar are missing",
            "Labels are cut off on the cumulative bar",
        ],
    ),
    ("f-bubble-basic-d3", "D1"): (
        [
            "d3.forceCollide moves the bubbles off their data values",
            "The circles are nudged away from their values to avoid overlap",
        ],
        [
            "Two labels collide near the top-right bubble",
            "The legend is forced into the top-left corner",
            "Bubble labels are shifted away from their bubbles",
        ],
    ),
    ("f-scatter-hr-diagram-letsplot", "D2"): (
        ["The yellow 'Sun' label has low contrast on the light background"],
        ["Low-contrast gridlines in the light render", "The yellow G-type stars blend into the light background"],
    ),
}


def _shipped_defect(item_id: str, defect_id: str) -> dict[str, Any]:
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    item = next(i for i in manifest["items"] if i["id"] == item_id)
    return next(d for d in item["defects"] if d["id"] == defect_id)


def _caught(label: dict[str, Any], weakness: str) -> bool:
    """Every listed criterion below max, so only the pattern decides."""
    checklist = {cid: {"score": 1, "max": 2, "comment": ""} for cid in label["criteria"]}
    return rt.metrics.defect_hit(label, {"checklist": checklist, "weaknesses": [weakness]})


class TestScopedLabelPatterns:
    @pytest.mark.parametrize(
        ("key", "phrasing"),
        [(key, p) for key, (hits, _) in SCOPED_LABELS.items() for p in hits],
        ids=lambda v: v[0] if isinstance(v, tuple) else None,
    )
    def test_matches_its_own_defect(self, key, phrasing):
        assert _caught(_shipped_defect(*key), phrasing)

    @pytest.mark.parametrize(
        ("key", "phrasing"),
        [(key, p) for key, (_, misses) in SCOPED_LABELS.items() for p in misses],
        ids=lambda v: v[0] if isinstance(v, tuple) else None,
    )
    def test_ignores_an_unrelated_weakness(self, key, phrasing):
        assert not _caught(_shipped_defect(*key), phrasing)


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------


def _plan(manifest=None, **kwargs):
    params = {
        "subset": "core",
        "models": "production",
        "runs": 3,
        "orders": "both",
        "rules_sha": B,
        "action_sha": ACTION,
        "repo": REPO_ROOT,
        "lister": lambda wf, status: [],
        "now": NOW,
        "ancestor": lambda repo, a, b: True,
    }
    params.update(kwargs)
    return rt.plan(manifest or _manifest(), **params)


def _resumed(cell: str, model_alias: str = "opus", **overrides: Any) -> dict[str, Any]:
    """A successful record of an earlier run of the arm ``_plan`` plans."""
    record = {
        "cell": cell,
        "ok": True,
        "set": "v1",
        "harness_version": rt.HARNESS_VERSION,
        "action_sha": ACTION,
        "rules_sha": B,
        "spec_source": "pinned",
        "model_alias": model_alias,
        "harness_sha": A,  # the dispatch commit: never compared
    }
    record.update(overrides)
    return record


class TestPlan:
    def test_core_production_counts_and_models(self):
        result = _plan()
        assert result["sessions"] == 3 * (1 + 2)
        assert result["by_model"] == {"fresh/opus": 3, "regen/opus": 6}
        assert result["items"] == ["f-bubble-basic-matplotlib", "r-bubble-basic-matplotlib-b-a"]
        assert result["estimate_usd"] == pytest.approx(
            3 * rt.COST_ESTIMATE[("fresh", "opus")] + 6 * rt.COST_ESTIMATE[("regen", "opus")]
        )

    def test_run_major_order(self):
        cells = _plan()["cells"]
        assert [c["run"] for c in cells] == [1, 1, 1, 2, 2, 2, 3, 3, 3]
        assert [c["id"] for c in cells[:3]] == [
            "f-bubble-basic-matplotlib__r1",
            "r-bubble-basic-matplotlib-b-a__fwd__r1",
            "r-bubble-basic-matplotlib-b-a__rev__r1",
        ]
        assert cells[0]["order"] == "" and cells[1]["order"] == "forward"

    def test_models_orders_subset(self):
        result = _plan(models="sonnet", orders="forward", runs=2, subset="full")
        assert result["sessions"] == 2 * 3
        assert {c["model"] for c in result["cells"]} == {"sonnet"}
        only = _plan(subset="f-scatter-basic-ggplot2", runs=1)
        assert [c["item"] for c in only["cells"]] == ["f-scatter-basic-ggplot2"]

    def test_unknown_subset_refused(self):
        with pytest.raises(rt.HarnessError, match="unknown item id"):
            _plan(subset="f-nope")

    def test_session_cap(self):
        manifest = _manifest()
        base = manifest["items"][0]
        manifest["items"] = [{**copy.deepcopy(base), "id": f"f-item-{i}"} for i in range(81)]
        assert _plan(manifest, runs=2)["sessions"] == 162
        with pytest.raises(rt.HarnessError, match="exceed the cap of 240"):
            _plan(manifest, runs=3)

    def test_busy_pipeline_refused(self):
        def lister(workflow, status):
            if workflow == "impl-review.yml" and status == "in_progress":
                return [{"databaseId": 1, "createdAt": (NOW - timedelta(minutes=5)).isoformat()}]
            return []

        with pytest.raises(rt.HarnessError, match="impl-review.yml run 1"):
            _plan(lister=lister)

    def test_stale_in_progress_run_is_ignored(self):
        def lister(workflow, status):
            if status == "in_progress":
                return [{"databaseId": 9, "createdAt": "2026-05-27T00:00:00Z"}]
            return []

        assert _plan(lister=lister)["sessions"] == 9

    def test_queued_run_counts_regardless_of_age(self):
        def lister(workflow, status):
            return [{"databaseId": 2, "createdAt": "2026-05-27T00:00:00Z"}] if status == "queued" else []

        with pytest.raises(rt.HarnessError, match="queued"):
            _plan(lister=lister)

    def test_regen_refused_before_the_gate_commit(self):
        with pytest.raises(rt.HarnessError, match="predates 02e1a7974"):
            _plan(ancestor=lambda repo, a, b: False)
        fresh_only = _plan(subset="f-bubble-basic-matplotlib", ancestor=lambda repo, a, b: False)
        assert fresh_only["sessions"] == 3

    def test_resume_skips_successful_cells(self):
        done = [
            _resumed("f-bubble-basic-matplotlib__r1"),
            _resumed("f-bubble-basic-matplotlib__r2", ok=False),
            _resumed("r-bubble-basic-matplotlib-b-a__rev__r1", harness_sha=B),
        ]
        result = _plan(resume_records=done)
        assert result["resumed"] == 2
        assert result["resumed_cells"] == ["f-bubble-basic-matplotlib__r1", "r-bubble-basic-matplotlib-b-a__rev__r1"]
        assert result["resume_rejected"] == [] and result["resume_unused"] == 0
        assert result["sessions"] == 7
        assert "f-bubble-basic-matplotlib__r1" not in {c["id"] for c in result["cells"]}

    def test_resume_rejects_a_record_from_other_rules(self):
        done = [_resumed("f-bubble-basic-matplotlib__r1", rules_sha=A), _resumed("f-bubble-basic-matplotlib__r2")]
        result = _plan(resume_records=done)
        assert result["resumed_cells"] == ["f-bubble-basic-matplotlib__r2"]
        assert "f-bubble-basic-matplotlib__r1" in {c["id"] for c in result["cells"]}
        assert result["resume_rejected"] == [
            {"cell": "f-bubble-basic-matplotlib__r1", "reason": f"rules_sha {A[:10]} != {B[:10]}"}
        ]

    def test_resume_rejects_a_record_from_another_model(self):
        # models=sonnet runs every cell on Sonnet: only the Sonnet regen record
        # measures the same; the Opus fresh record is run again.
        done = [
            _resumed("f-bubble-basic-matplotlib__r1", model_alias="opus"),
            _resumed("r-bubble-basic-matplotlib-b-a__fwd__r1", model_alias="sonnet"),
        ]
        result = _plan(models="sonnet", resume_records=done)
        assert result["resumed_cells"] == ["r-bubble-basic-matplotlib-b-a__fwd__r1"]
        assert result["resume_rejected"] == [
            {"cell": "f-bubble-basic-matplotlib__r1", "reason": "model_alias opus != sonnet"}
        ]

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("set", "v0"),
            ("harness_version", "0"),
            ("action_sha", A),
            ("spec_source", "rules_ref"),
            ("rules_sha", None),  # no provenance can't be shown to match
            ("action_sha", "n/a"),
        ],
    )
    def test_resume_rejects_any_other_measurement(self, field, value):
        cell = "f-bubble-basic-matplotlib__r1"
        record = _resumed(cell, **{field: value})
        if value is None:
            del record[field]
        result = _plan(resume_records=[record])
        assert result["resumed"] == 0 and result["sessions"] == 9
        assert result["resume_rejected"][0]["reason"].startswith(f"{field} ")

    def test_resume_without_a_known_action_pin_reuses_nothing(self):
        result = _plan(action_sha="n/a", resume_records=[_resumed("f-bubble-basic-matplotlib__r1", action_sha="n/a")])
        assert result["resumed"] == 0
        assert result["resume_rejected"][0]["reason"] == "action_sha n/a != n/a"

    def test_resume_records_outside_the_plan_are_unused(self):
        done = [_resumed("f-scatter-basic-ggplot2__r1"), _resumed("f-bubble-basic-matplotlib__r4")]
        result = _plan(resume_records=done)
        assert result["resumed"] == 0 and result["resume_rejected"] == []
        assert result["resume_unused"] == 2

    def test_resume_log_groups_reasons(self):
        rejected = [{"cell": f"c{i}", "reason": "rules_sha aaaaaaaaaa != bbbbbbbbbb"} for i in range(5)]
        rejected.append({"cell": "d1", "reason": "model_alias opus != sonnet"})
        lines = rt.resume_log(rejected, unused=2)
        assert lines == [
            "resume: 5 record(s) rejected and run again (rules_sha aaaaaaaaaa != bbbbbbbbbb): c0, c1, c2 and 2 more",
            "resume: 1 record(s) rejected and run again (model_alias opus != sonnet): d1",
            "resume: 2 successful record(s) name cells outside this plan (subset, runs, orders) and are not used",
        ]

    def test_idle_check_that_cannot_list_runs_refuses(self, monkeypatch):
        def failing_run(args, **kwargs):
            return subprocess.CompletedProcess(args, 1, stdout="", stderr="HTTP 401: Bad credentials")

        monkeypatch.setattr(rt.subprocess, "run", failing_run)
        with pytest.raises(rt.HarnessError, match="cannot list impl-generate.yml runs"):
            _plan(lister=rt.gh_run_lister)


# ---------------------------------------------------------------------------
# A throwaway repository with two versions of one implementation
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _stored_metadata(score: int, weaknesses: list[str]) -> str:
    return yaml.safe_dump(
        {
            "library": "matplotlib",
            "language": "python",
            "specification_id": "bubble-basic",
            "created": "2026-05-28T00:00:00Z",
            "updated": "2026-09-27T00:00:00Z",
            "generated_by": "claude-sonnet",
            "workflow_run": 1,
            "issue": 7,
            "language_version": "3.13.4",
            "library_version": "3.10.0",
            "preview_url_light": "https://example.invalid/l.png",
            "preview_url_dark": "https://example.invalid/d.png",
            "preview_html_light": None,
            "preview_html_dark": None,
            "quality_score": score,
            "impl_tags": {"techniques": ["alpha-blending"]},
            "review": {
                "strengths": ["clean"],
                "weaknesses": weaknesses,
                "model": "claude-sonnet-5",
                "criteria_version": "qc-a.aqr-b.sg-c.lib-d",
            },
        }
    )


@pytest.fixture
def repo(tmp_path) -> dict[str, Any]:
    root = tmp_path / "repo"
    spec = root / "plots" / "bubble-basic"
    (spec / "implementations" / "python").mkdir(parents=True)
    (spec / "metadata" / "python").mkdir(parents=True)
    (spec / "specification.md").write_text(
        "# bubble-basic\n\n## What a good version looks like\n- Overlap is expected\n", encoding="utf-8"
    )
    (spec / "specification.yaml").write_text("title: Basic Bubble\n", encoding="utf-8")
    impl = spec / "implementations" / "python" / "matplotlib.py"
    meta = spec / "metadata" / "python" / "matplotlib.yaml"
    impl.write_text(
        '""" anyplot.ai\nbubble-basic: Basic Bubble\nLibrary: matplotlib 3.10 | Python 3.13\nQuality: 88/100 | Created: 2026-05-28\n"""\nold = 1\n',
        encoding="utf-8",
    )
    meta.write_text(_stored_metadata(88, ["legend small", "labels overlap"]), encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "v0")
    v0 = _git(root, "rev-parse", "HEAD")
    impl.write_text(
        '""" anyplot.ai\nbubble-basic: Basic Bubble\nLibrary: matplotlib 3.10 | Python 3.13\nQuality: 92/100 | Updated: 2026-09-27\n"""\nnew = 2\nmore = 3\n',
        encoding="utf-8",
    )
    meta.write_text(_stored_metadata(92, ["title long"]), encoding="utf-8")
    _git(root, "commit", "-q", "-am", "v1")
    v1 = _git(root, "rev-parse", "HEAD")
    return {"root": root, "v0": v0, "v1": v1}


def _repo_manifest(repo: dict[str, Any]) -> dict[str, Any]:
    return _manifest(
        baseline_rules_sha=repo["v1"],
        spec_commit=repo["v1"],
        items=[
            {
                "id": "f-bubble-basic-matplotlib",
                "kind": "fresh",
                "tier": "core",
                "spec_id": "bubble-basic",
                "library": "matplotlib",
                "new": {"commit": repo["v1"], "render": "production"},
            },
            {
                "id": "r-bubble-basic-matplotlib-v1-v0",
                "kind": "regen",
                "tier": "core",
                "spec_id": "bubble-basic",
                "library": "matplotlib",
                "class": "different",
                "new": {"commit": repo["v1"], "render": "production"},
                "prev": {"commit": repo["v0"], "render": "production"},
                "expected": None,
            },
        ],
    )


def _renders(manifest: dict[str, Any]) -> dict[str, bytes]:
    renders = {}
    for item in manifest["items"]:
        for role in rt.roles_of(item):
            for theme in rt.THEMES:
                obj = rt.object_path(manifest, item["id"], role, theme)
                renders[obj] = fake_png(salt=obj.encode())
    return renders


def _lock(manifest: dict[str, Any], renders: dict[str, bytes]) -> dict[str, Any]:
    return {
        "version": 1,
        "set": manifest["set"],
        "objects": {obj: {"sha256": sha(data), "width": 3200, "height": 1800} for obj, data in renders.items()},
    }


def _fetcher(renders: dict[str, bytes]):
    def fetch(url: str) -> bytes | None:
        return renders.get(url.removeprefix(rt.PUBLIC_BASE + "/"))

    return fetch


@pytest.fixture
def bundles(repo, tmp_path) -> dict[str, Any]:
    manifest = _repo_manifest(repo)
    renders = _renders(manifest)
    lock = _lock(manifest, renders)
    out = tmp_path / "bundles"
    for item in manifest["items"]:
        rt.bundle_item(manifest, lock, item, out, repo["root"], fetch=_fetcher(renders))
    return {"manifest": manifest, "renders": renders, "lock": lock, "out": out, **repo}


class TestBundle:
    def test_layout(self, bundles):
        regen = bundles["out"] / "r-bubble-basic-matplotlib-v1-v0"
        info = json.loads((regen / "item.json").read_text(encoding="utf-8"))
        assert info["seeded"] is True
        assert info["commits"] == {"new": bundles["v1"], "prev": bundles["v0"]}
        assert info["canvas"]["prev-dark"] == [3200, 1800]
        assert "new = 2" in (regen / "new" / "matplotlib.py").read_text(encoding="utf-8")
        assert "old = 1" in (regen / "prev" / "matplotlib.py").read_text(encoding="utf-8")
        assert (regen / "prev" / "plot-light.png").read_bytes() == bundles["renders"][
            "retest/sets/v1/r-bubble-basic-matplotlib-v1-v0/prev-light.png"
        ]
        assert (regen / "spec" / "specification.yaml").is_file()

    def test_sha_mismatch_is_refused(self, repo, tmp_path):
        manifest = _repo_manifest(repo)
        renders = _renders(manifest)
        lock = _lock(manifest, renders)
        tampered = dict(renders)
        obj = "retest/sets/v1/f-bubble-basic-matplotlib/new-dark.png"
        tampered[obj] = fake_png(salt=b"other")
        with pytest.raises(rt.HarnessError, match="sha256 mismatch"):
            rt.bundle_item(manifest, lock, manifest["items"][0], tmp_path / "b", repo["root"], fetch=_fetcher(tampered))

    def test_off_canvas_render_is_refused(self, repo, tmp_path):
        manifest = _repo_manifest(repo)
        renders = {obj: fake_png(3000, 1800, salt=obj.encode()) for obj in _renders(manifest)}
        lock = _lock(manifest, renders)
        with pytest.raises(rt.HarnessError, match="not a canonical canvas"):
            rt.bundle_item(manifest, lock, manifest["items"][0], tmp_path / "b", repo["root"], fetch=_fetcher(renders))

    def test_missing_object_is_refused(self, repo, tmp_path):
        manifest = _repo_manifest(repo)
        renders = _renders(manifest)
        with pytest.raises(rt.HarnessError, match="missing from the bucket"):
            rt.bundle_item(
                manifest,
                _lock(manifest, renders),
                manifest["items"][0],
                tmp_path / "b",
                repo["root"],
                fetch=lambda u: None,
            )

    def test_png_size(self):
        assert rt.png_size(fake_png(2400, 2400)) == (2400, 2400)
        with pytest.raises(rt.HarnessError):
            rt.png_size(b"GIF89a")
        assert rt.canonical_canvas((3216, 1784))
        assert not rt.canonical_canvas((3217, 1800))


# ---------------------------------------------------------------------------
# materialize
# ---------------------------------------------------------------------------


def _cell(item: str, kind: str, order: str = "", run: int = 1, model: str = "sonnet") -> dict[str, Any]:
    return {
        "id": rt.cell_id(item, order or None, run),
        "set": "v1",
        "item": item,
        "kind": kind,
        "tier": "core",
        "spec_id": "bubble-basic",
        "library": "matplotlib",
        "order": order,
        "run": run,
        "model": model,
    }


@pytest.fixture
def workspace(tmp_path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "review_regen.json").write_text("stale", encoding="utf-8")
    return ws


class TestMaterialize:
    def test_fresh_cell(self, bundles, workspace, tmp_path):
        tmp = rt.TmpPaths(tmp_path / "tmp")
        out = rt.materialize(
            bundles["out"] / "f-bubble-basic-matplotlib",
            workspace,
            _cell("f-bubble-basic-matplotlib", "fresh"),
            GATE_SCRIPT,
            tmp=tmp,
        )
        assert out["is_regen"] == "false"
        assert out["prev_renders"] == "missing"
        impl = (workspace / "plots/bubble-basic/implementations/python/matplotlib.py").read_text(encoding="utf-8")
        assert "Quality: pending | Updated: 2026-09-27" in impl
        assert "92/100" not in impl
        meta = yaml.safe_load(
            (workspace / "plots/bubble-basic/metadata/python/matplotlib.yaml").read_text(encoding="utf-8")
        )
        assert tuple(meta) == rt.IMPL_GENERATE_METADATA_KEYS
        assert meta["quality_score"] is None
        assert meta["review"] == {"strengths": [], "weaknesses": []}
        assert "impl_tags" not in meta
        assert (workspace / "plot_images/plot-light.png").is_file()
        assert not (workspace / "review_regen.json").exists()  # stale output removed
        assert "## What a good version looks like" in (workspace / "plots/bubble-basic/specification.md").read_text()

    @pytest.mark.parametrize(
        ("order", "subject_marker", "prev_marker"),
        [("forward", "new = 2", "old = 1"), ("reversed", "old = 1", "new = 2")],
    )
    def test_regen_cell_both_orders(self, bundles, workspace, tmp_path, order, subject_marker, prev_marker):
        tmp = rt.TmpPaths(tmp_path / "tmp")
        out = rt.materialize(
            bundles["out"] / "r-bubble-basic-matplotlib-v1-v0",
            workspace,
            _cell("r-bubble-basic-matplotlib-v1-v0", "regen", order),
            GATE_SCRIPT,
            tmp=tmp,
        )
        impl = (workspace / "plots/bubble-basic/implementations/python/matplotlib.py").read_text(encoding="utf-8")
        assert subject_marker in impl
        assert "Quality: pending" in impl
        prev_impl = tmp.prev_impl(".py").read_text(encoding="utf-8")
        assert prev_marker in prev_impl
        assert "Quality: hidden/100" in prev_impl  # sanitized by the rules-under-test gate script
        assert out["prev_renders"] == "available"
        assert out["prev_light"] == str(tmp.base / "anyplot-prev-plot-light.png")
        assert out["prev_stored"] == ("88" if order == "forward" else "92")
        review = tmp.prev_review.read_text(encoding="utf-8")
        assert "**W1:**" in review and "Previous quality score" not in review  # --omit-scores
        assert "**C1:** Overlap is expected" in review
        assert out["prev_lines"] == str(prev_impl.count("\n"))
        assert out["new_lines"] == str(impl.count("\n"))
        subject = "new" if order == "forward" else "prev"
        other = "prev" if order == "forward" else "new"
        bundle = bundles["out"] / "r-bubble-basic-matplotlib-v1-v0"
        assert (workspace / "plot_images/plot-dark.png").read_bytes() == (
            bundle / subject / "plot-dark.png"
        ).read_bytes()
        assert tmp.prev_dark.read_bytes() == (bundle / other / "plot-dark.png").read_bytes()

    def test_regen_cell_without_order_is_refused(self, bundles, workspace, tmp_path):
        with pytest.raises(rt.HarnessError, match="has no order"):
            rt.materialize(
                bundles["out"] / "r-bubble-basic-matplotlib-v1-v0",
                workspace,
                _cell("r-bubble-basic-matplotlib-v1-v0", "regen"),
                GATE_SCRIPT,
                tmp=rt.TmpPaths(tmp_path / "tmp"),
            )

    @pytest.mark.parametrize(
        "header",
        [
            '""" anyplot.ai\nx: y\nLibrary: a 1 | Python 3.13\nQuality: 91/100 | Created: 2026-05-28\n"""\n',
            "#' anyplot.ai\n#' x: y\n#' Library: ggplot2 3.5 | R 4.4\n#' Quality: 91/100 | Created: 2026-05-28\n",
            "# anyplot.ai\n# x: y\n# Library: makie 0.21 | Julia 1.11\n# Quality: 91/100 | Created: 2026-05-28\n",
            "// anyplot.ai\n// x: y\n// Library: d3 7 | JavaScript 22\n// Quality: 91/100 | Created: 2026-05-28\n",
        ],
    )
    def test_pending_header_for_every_language(self, header):
        assert "Quality: pending | Created: 2026-05-28" in rt.reset_header_score(header + "body\n")


# ---------------------------------------------------------------------------
# collect
# ---------------------------------------------------------------------------


def _write_review(ws: Path, score: int = 88, regen: dict | None = None) -> None:
    (ws / "review_regen.json").unlink(missing_ok=True)  # the fixture's stale file; materialize would drop it
    (ws / "quality_score.txt").write_text(f"{score}\n", encoding="utf-8")
    (ws / "review_weaknesses.json").write_text('["Legend circles invisible", "Add a subtitle"]', encoding="utf-8")
    (ws / "review_strengths.json").write_text('["clean"]', encoding="utf-8")
    (ws / "review_checklist.json").write_text(
        json.dumps(
            {
                "visual_quality": {
                    "score": 11,
                    "max": 14,
                    "items": [
                        {"id": "VQ-01", "name": "Text", "score": 7, "max": 8, "comment": "small ticks"},
                        {"id": "VQ-03", "name": "Vis", "score": 4, "max": 6, "comment": "legend invisible"},
                        {"id": "VQ-03", "name": "dupe", "score": 0, "max": 6, "comment": "ignored"},
                        {"id": "XX-99", "name": "unknown", "score": 5, "max": 5},
                        {"id": "VQ-04", "name": "bad", "score": True, "max": 4},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    (ws / "review_comment.md").write_text("## AI Review\n", encoding="utf-8")
    if regen is not None:
        (ws / "review_regen.json").write_text(json.dumps(regen), encoding="utf-8")


def _execution(tmp_path: Path, result: dict | None) -> Path:
    messages: list[dict] = [{"type": "system", "subtype": "init", "model": "claude-sonnet-5"}]
    messages.append({"type": "assistant", "message": {"content": "TRANSCRIPT SECRET"}})
    if result is not None:
        messages.append({"type": "result", **result})
    path = tmp_path / "claude-execution-output.json"
    path.write_text(json.dumps(messages), encoding="utf-8")
    return path


OK_RESULT = {"subtype": "success", "is_error": False, "num_turns": 20, "duration_ms": 190000, "total_cost_usd": 0.61}


class TestCollect:
    def test_fresh_record(self, workspace, tmp_path):
        _write_review(workspace)
        out = tmp_path / "cell"
        record = rt.collect(
            workspace,
            _cell("f-bubble-basic-matplotlib", "fresh"),
            out,
            execution_file=str(_execution(tmp_path, OK_RESULT)),
            review_outcome="success",
            materialize_ok=True,
            gate_script=GATE_SCRIPT,
            prev_stored="n/a",
            provenance={
                "criteria_version": "qc-a",
                "rules_sha": B,
                "harness_sha": A,
                "action_sha": "x",
                "prompts_tree": "t",
                "spec_source": "pinned",
            },
        )
        assert record["ok"] is True and record["error_class"] == ""
        assert record["spec_source"] == "pinned"  # plan's resume check compares it
        assert record["model"] == "claude-sonnet-5"
        assert record["model_alias"] == "sonnet"
        assert record["cost_usd"] == 0.61 and record["turns"] == 20
        assert record["score_typed"] == 88
        assert set(record["checklist"]) == {"VQ-01", "VQ-03", "XX-99"}
        assert record["checklist"]["VQ-03"]["comment"] == "legend invisible"
        assert record["checklist_sum"] == 11  # canonical items only
        assert record["weaknesses"] == ["Legend circles invisible", "Add a subtitle"]
        assert record["gate"] is None and record["order"] is None
        assert record["comment_written"] is True
        assert record["rules_sha"] == B and record["criteria_version"] == "qc-a"
        saved = json.loads((out / "record.json").read_text(encoding="utf-8"))
        assert saved["cell"] == "f-bubble-basic-matplotlib__r1"
        assert sorted(p.name for p in (out / "files").iterdir()) == [
            "quality_score.txt",
            "review_checklist.json",
            "review_comment.md",
            "review_strengths.json",
            "review_weaknesses.json",
        ]

    @pytest.mark.parametrize("init", [None, {"type": "system", "subtype": "init", "model": "not a model id!"}])
    def test_unresolved_model_is_none_never_the_alias(self, workspace, tmp_path, capsys, init):
        """#11950: an alias must never pass for a resolved model id."""
        _write_review(workspace)
        execution = ""
        if init is not None:
            path = tmp_path / "exec.json"
            path.write_text(json.dumps([init, {"type": "result", **OK_RESULT}]), encoding="utf-8")
            execution = str(path)
        cell = _cell("f-bubble-basic-matplotlib", "fresh", model="opus")
        out = tmp_path / "cell"
        code = rt.main(
            [
                "collect",
                "--workspace",
                str(workspace),
                "--cell",
                json.dumps(cell),
                "--out",
                str(out),
                "--execution-file",
                execution,
                "--review-outcome",
                "success",
                "--materialize-outcome",
                "success",
                "--gate-script",
                str(GATE_SCRIPT),
            ]
        )
        assert code == 0
        record = json.loads((out / "record.json").read_text(encoding="utf-8"))
        assert record["model"] is None
        assert record["model_alias"] == "opus"
        assert "claude-opus" not in json.dumps(record)
        assert "model=n/a alias=opus" in capsys.readouterr().out

    def test_transcript_is_never_copied(self, workspace, tmp_path):
        _write_review(workspace)
        out = tmp_path / "cell"
        rt.collect(
            workspace,
            _cell("f-bubble-basic-matplotlib", "fresh"),
            out,
            execution_file=str(_execution(tmp_path, OK_RESULT)),
            review_outcome="success",
            materialize_ok=True,
            gate_script=GATE_SCRIPT,
            prev_stored="n/a",
        )
        for path in out.rglob("*"):
            if path.is_file():
                assert "TRANSCRIPT SECRET" not in path.read_text(encoding="utf-8")

    def test_regen_record_runs_the_gate(self, bundles, workspace, tmp_path):
        tmp = rt.TmpPaths(tmp_path / "tmp")
        cell = _cell("r-bubble-basic-matplotlib-v1-v0", "regen", "forward")
        out = rt.materialize(bundles["out"] / cell["item"], workspace, cell, GATE_SCRIPT, tmp=tmp)
        regen = {
            "prev_rescored": 87,
            "improvements": [{"ref": "W1", "what": "legend larger", "where_visible": "legend"}],
            "regressions": [],
            "scenario_changed": False,
            "encodings_added": [],
            "change_request_applied": None,
        }
        _write_review(workspace, score=88, regen=regen)
        record = rt.collect(
            workspace,
            cell,
            tmp_path / "cell",
            execution_file=str(_execution(tmp_path, OK_RESULT)),
            review_outcome="success",
            materialize_ok=True,
            gate_script=GATE_SCRIPT,
            prev_stored=out["prev_stored"],
            tmp=tmp,
        )
        assert record["gate"]["verdict"] == "merge"
        assert record["gate"]["prev_rescored"] == 87
        assert record["gate"]["code"] == "merge"
        assert record["prev_stored"] == 88
        assert record["regen"]["prev_rescored"] == 87
        assert record["regen_counts"] == {"total": 1, "visible": 1, "permission": 0}
        assert record["order"] == "forward"

    @pytest.mark.parametrize("ref", ["C2", "c2"])  # c2: the gate coerces the ref before judging
    def test_permission_citation_is_counted_apart(self, bundles, workspace, tmp_path, ref):
        """regen_counts follows the gate record: a cited permission is never a visible improvement."""
        tmp = rt.TmpPaths(tmp_path / "tmp")
        cell = _cell("r-bubble-basic-matplotlib-v1-v0", "regen", "forward")
        out = rt.materialize(bundles["out"] / cell["item"], workspace, cell, GATE_SCRIPT, tmp=tmp)
        (workspace / "plots/bubble-basic/specification.md").write_text(
            "# bubble-basic\n\n## What a good version looks like\n\n"
            "- A good version shows: a size legend drawn like the marks.\n"
            "- Expected, not a defect: overlapping bubbles in dense regions.\n",
            encoding="utf-8",
        )
        regen = {
            "prev_rescored": 87,
            "improvements": [
                {"ref": ref, "what": "overlap", "where_visible": "centre cluster"},
                {"ref": "W1", "what": "legend larger", "where_visible": ""},
            ],
            "regressions": [],
            "scenario_changed": False,
            "encodings_added": [],
            "change_request_applied": None,
        }
        _write_review(workspace, score=88, regen=regen)
        record = rt.collect(
            workspace,
            cell,
            tmp_path / "cell",
            execution_file=str(_execution(tmp_path, OK_RESULT)),
            review_outcome="success",
            materialize_ok=True,
            gate_script=GATE_SCRIPT,
            prev_stored=out["prev_stored"],
            tmp=tmp,
        )
        assert record["regen_counts"] == {"total": 2, "visible": 0, "permission": 1}
        assert record["gate"]["verdict"] == "keep"
        assert record["gate"]["code"] == "no_visible_improvement"

    def test_improvement_counts(self):
        labelled = "## What a good version looks like\n- A good version shows: x\n- Expected, not a defect: y\n"
        regen = {
            "improvements": [
                {"ref": "C2", "where_visible": "a"},
                {"ref": "C1", "where_visible": "b"},
                {"ref": "new", "where_visible": " "},
                {"ref": "c2", "where_visible": "a"},  # the gate coerces c2 -> C2: a permission, never visible
                "not an item",
            ]
        }
        assert rt.improvement_counts(regen, labelled) == {"total": 4, "visible": 1, "permission": 2}
        assert regen["improvements"][3]["ref"] == "c2"  # the record's raw regen stays untouched
        # A section without kind prefixes (the pinned v1 specs) has no permissions.
        assert rt.improvement_counts(regen, "## What a good version looks like\n- x\n- y\n") == {
            "total": 4,
            "visible": 3,
            "permission": 0,
        }
        assert rt.improvement_counts(None, labelled) is None
        assert rt.improvement_counts({"improvements": "none"}, labelled) is None

    @pytest.mark.parametrize(
        ("result", "outcome", "materialize_ok", "started_ago", "expected"),
        [
            ({**OK_RESULT, "is_error": True, "result": "Claude AI usage limit reached"}, "failure", True, 60, "quota"),
            (None, "failure", True, 25 * 60, "timeout"),
            (None, "cancelled", True, 60, "timeout"),
            (None, "failure", True, 60, "no_result"),
            ({**OK_RESULT, "subtype": "error_max_turns"}, "success", True, 60, "other"),
            (OK_RESULT, "success", True, 60, "no_output"),
            (OK_RESULT, "skipped", False, 0, "harness"),
        ],
    )
    def test_error_classes(self, workspace, tmp_path, result, outcome, materialize_ok, started_ago, expected):
        record = rt.collect(
            workspace,
            _cell("f-bubble-basic-matplotlib", "fresh"),
            tmp_path / "cell",
            execution_file=str(_execution(tmp_path, result)),
            review_outcome=outcome,
            materialize_ok=materialize_ok,
            gate_script=GATE_SCRIPT,
            prev_stored="n/a",
            started_at=1000.0 if started_ago else 0.0,
            now=1000.0 + started_ago,
        )
        assert record["ok"] is False
        assert record["error_class"] == expected

    def test_quota_error_with_a_score_is_still_quota(self, workspace, tmp_path):
        _write_review(workspace)
        result = {**OK_RESULT, "is_error": True, "result": "rate limit exceeded"}
        record = rt.collect(
            workspace,
            _cell("f-bubble-basic-matplotlib", "fresh"),
            tmp_path / "cell",
            execution_file=str(_execution(tmp_path, result)),
            review_outcome="failure",
            materialize_ok=True,
            gate_script=GATE_SCRIPT,
            prev_stored="n/a",
        )
        assert record["error_class"] == "quota" and record["ok"] is False


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------


def _record(cell: str, item: str, run: int, score: int, **extra) -> dict[str, Any]:
    record = {
        "v": 1,
        "harness_version": "1",
        "set": "v1",
        "cell": cell,
        "item": item,
        "kind": "fresh",
        "order": None,
        "run": run,
        "model": "claude-opus-5-5",
        "ok": True,
        "error_class": "",
        "score_typed": score,
        "checklist_sum": score,
        "checklist": {
            "VQ-03": {"score": 4 if score < 90 else 6, "max": 6, "comment": "legend faint" if score < 90 else "ok"}
        },
        "weaknesses": ["legend faint"] if score < 90 else [],
        "cost_usd": 1.2,
        "rules_sha": B,
        "action_sha": "x",
    }
    record.update(extra)
    return record


class TestReport:
    def test_report_files_and_snippet(self, tmp_path):
        records = [
            _record("f-bubble-basic-matplotlib__r1", "f-bubble-basic-matplotlib", 1, 89),
            _record("f-bubble-basic-matplotlib__r2", "f-bubble-basic-matplotlib", 2, 91),
            _record("f-scatter-basic-ggplot2__r1", "f-scatter-basic-ggplot2", 1, 88),
            {
                **_record("f-scatter-basic-ggplot2__r2", "f-scatter-basic-ggplot2", 2, 0),
                "ok": False,
                "error_class": "quota",
                "score_typed": None,
            },
        ]
        payload = rt.report(
            records,
            _confirmed_manifest(),
            tmp_path / "report",
            label="baseline",
            subset_label="core",
            rules_sha=B,
            harness_sha=A,
            run_url="https://github.com/o/r/actions/runs/1",
            lock_sha="c" * 64,
        )
        snippet = (tmp_path / "report" / "snippet.md").read_text(encoding="utf-8")
        assert snippet.splitlines()[0] == "### Review retest — set v1 core (2 fresh × 2)"
        assert "Fresh: claude-opus-5-5 · rules bbbbbbb · harness v1" in snippet
        assert "| Items with split verdict at 90 | 1/1 |" in snippet
        assert "| Named-defect miss rate | 1/2 |" in snippet  # D1 on f-bubble-basic-matplotlib, missed in run 2
        assert "| Sessions / API-equivalent cost | 3/4 / $5 |" in snippet
        assert "lock sha256 cccccccccccc" in snippet
        text = (tmp_path / "report" / "retest-report.md").read_text(encoding="utf-8")
        assert 'errors: {"quota": 1}' in text
        assert "## Snippet for the PR body" in text
        lines = (tmp_path / "report" / "records.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 4
        assert payload["metrics"]["cells"]["ok"] == 3

    def test_draft_labels_leave_the_label_metrics_empty(self, tmp_path):
        records = [
            _record("f-bubble-basic-matplotlib__r1", "f-bubble-basic-matplotlib", 1, 89),
            _record("f-bubble-basic-matplotlib__r2", "f-bubble-basic-matplotlib", 2, 91),
        ]
        rt.report(
            records,
            _manifest(),
            tmp_path / "report",
            label="baseline",
            subset_label="core",
            rules_sha=B,
            harness_sha=A,
            run_url="u",
            lock_sha="c" * 64,
        )
        snippet = (tmp_path / "report" / "snippet.md").read_text(encoding="utf-8")
        assert "| Named-defect miss rate | – (no labels) |" in snippet
        assert "(labels: draft)" in (tmp_path / "report" / "retest-report.md").read_text(encoding="utf-8")

    def test_unresolved_model_is_its_own_group(self, tmp_path):
        records = [
            _record("f-bubble-basic-matplotlib__r1", "f-bubble-basic-matplotlib", 1, 89),
            _record(
                "f-bubble-basic-matplotlib__r2", "f-bubble-basic-matplotlib", 2, 91, model=None, model_alias="opus"
            ),
        ]
        payload = rt.report(
            records,
            _manifest(),
            tmp_path / "report",
            label="x",
            subset_label="core",
            rules_sha=B,
            harness_sha=A,
            run_url="u",
            lock_sha="c" * 64,
        )
        assert set(payload["metrics"]["groups"]) == {"fresh|claude-opus-5-5", "fresh|unresolved (opus)"}
        assert "claude-opus ·" not in (tmp_path / "report" / "snippet.md").read_text(encoding="utf-8")

    def test_comparison_columns(self, tmp_path):
        base = [
            _record(f"f-bubble-basic-matplotlib__r{r}", "f-bubble-basic-matplotlib", r, s, rules_sha=A)
            for r, s in ((1, 86), (2, 92))
        ] + [
            _record(f"f-scatter-basic-ggplot2__r{r}", "f-scatter-basic-ggplot2", r, s, rules_sha=A)
            for r, s in ((1, 80), (2, 84))
        ]
        cand = [
            _record(f"f-bubble-basic-matplotlib__r{r}", "f-bubble-basic-matplotlib", r, s)
            for r, s in ((1, 90), (2, 90))
        ] + [_record(f"f-scatter-basic-ggplot2__r{r}", "f-scatter-basic-ggplot2", r, s) for r, s in ((1, 82), (2, 82))]
        rt.report(
            cand,
            _manifest(),
            tmp_path / "report",
            label="candidate",
            subset_label="core",
            rules_sha=B,
            harness_sha=A,
            run_url="u",
            lock_sha="c" * 64,
            base_records=base,
        )
        snippet = (tmp_path / "report" / "snippet.md").read_text(encoding="utf-8")
        assert "| Metric | Baseline | Candidate | Δ (95% CI) |" in snippet
        assert f"rules {A[:7]} → {B[:7]}" in snippet
        row = next(line for line in snippet.splitlines() if line.startswith("| Total mean"))
        # Baseline pooled SD, one degree of freedom per unit:
        # sqrt((1 * var[86, 92] + 1 * var[80, 84]) / (1 + 1)) = sqrt((18 + 8) / 2) = 3.6.
        assert row.startswith("| Total mean / pooled within-item SD (typed) | 85.5 / 3.6 | 86.0 / 0.0 | 0.5 (")
        assert " / -3.6 (" in row

    def test_merge_records_prefers_success(self):
        resumed = [{"cell": "a", "ok": True, "run": 1, "v": "resumed"}, {"cell": "b", "ok": False, "run": 1}]
        fresh = [{"cell": "a", "ok": False, "run": 1}, {"cell": "b", "ok": True, "run": 1, "v": "fresh"}]
        merged = {r["cell"]: r for r in rt.merge_records(resumed, fresh)}
        assert merged["a"]["v"] == "resumed"
        assert merged["b"]["v"] == "fresh"

    def test_load_cell_records(self, tmp_path):
        for name in ("cell-a", "cell-b"):
            (tmp_path / name).mkdir()
            (tmp_path / name / "record.json").write_text(json.dumps({"cell": name}), encoding="utf-8")
        (tmp_path / "cell-c").mkdir()  # an upload with no record
        assert [r["cell"] for r in rt.load_cell_records(tmp_path)] == ["cell-a", "cell-b"]


# ---------------------------------------------------------------------------
# gate-report
# ---------------------------------------------------------------------------


class TestGateReport:
    def test_comparable_record(self):
        record = {
            "model": "claude-sonnet-5",
            "prev_model": "claude-sonnet-5",
            "criteria_version": "qc-a.aqr-b.sg-c.lib-d",
            "prev_criteria_version": "qc-a.aqr-b.sg-x.lib-y",
        }
        assert rt.comparable_record(record)  # sg and lib may differ; qc and aqr decide
        assert not rt.comparable_record({**record, "prev_model": "n/a"})
        assert not rt.comparable_record({**record, "prev_criteria_version": "qc-z.aqr-b"})
        assert not rt.comparable_record({**record, "model": "n/a", "prev_model": "n/a"})

    def test_markers_from_comments(self, monkeypatch):
        from automation.scripts.regen_gate import render_record_marker

        marker = render_record_marker({"v": 1, "spec": "s", "lib": "altair", "verdict": "keep", "code": "regression"})
        calls: list[list[str]] = []

        def fake_run(args, **kwargs):
            calls.append(args)
            if args[:3] == ["gh", "pr", "list"]:
                stdout = json.dumps([{"number": 5}] if "regen:kept" in args else [{"number": 6}])
            else:
                bodies = [f"## Kept\n{marker}", None] if args[3].endswith("/5/comments") else ["no marker"]
                stdout = "\n".join(json.dumps(b) for b in bodies) + "\n"
            return subprocess.CompletedProcess(args, 0, stdout=stdout, stderr="")

        monkeypatch.setattr(rt.subprocess, "run", fake_run)
        records = rt.gh_gate_records(100)
        assert records == [{"v": 1, "spec": "s", "lib": "altair", "verdict": "keep", "code": "regression"}]
        text = rt.render_gate_report(rt.metrics.gate_monitor(records, rt.comparable_record))
        assert "Decisions: 1; merge rate 0%" in text
        assert "regression 1" in text

    def test_reads_permission_and_counted_visible_from_real_records(self):
        """Records as regen_gate.py writes them since #11948: `visible` counts only
        what the gate counted, `permission` the cited "Expected, not a defect" bullets."""
        from automation.scripts.regen_gate import (
            GateInput,
            build_record,
            decide,
            parse_record_markers,
            render_record_marker,
        )

        def record(improvements: list[dict[str, str]], permissions: frozenset[str]) -> dict[str, Any]:
            regen = {
                "prev_rescored": 90,
                "improvements": improvements,
                "regressions": [],
                "scenario_changed": False,
                "encodings_added": [],
                "change_request_applied": None,
            }
            result = decide(
                GateInput(
                    spec_id="bubble-basic",
                    score=91,
                    regen=regen,
                    known_weakness_ids=frozenset({"W1"}),
                    characteristic_count=3,
                    permission_refs=permissions,
                )
            )
            built = build_record(result, spec_id="bubble-basic", library="altair", score=91, prev_stored=92)
            return parse_record_markers(render_record_marker(built))[0]

        permission_only = record([{"ref": "C2", "what": "overlap", "where_visible": "centre"}], frozenset({"C2"}))
        assert permission_only["code"] == "no_visible_improvement"
        assert permission_only["improvements"]["visible"] == 0
        assert permission_only["improvements"]["permission"] == 1
        merged = record(
            [
                {"ref": "W1", "what": "legend", "where_visible": "legend"},
                {"ref": "C2", "what": "overlap", "where_visible": "centre"},
            ],
            frozenset({"C2"}),
        )
        assert merged["verdict"] == "merge" and merged["improvements"]["visible"] == 1

        result = rt.metrics.gate_monitor([permission_only, merged], rt.comparable_record)
        assert result["improvements"]["visible_mean"] == pytest.approx(0.5)
        assert result["improvements"]["permission_cited"] == 2
        assert result["improvements"]["permission_only_keeps"] == 1
        text = rt.render_gate_report(result)
        assert "Counted visible improvements (never a permission): mean 0.5 per decision, at least one in 50%" in text
        assert "Permission cited as an improvement: 2/2 decisions (100%); kept with nothing else counted: 1" in text


# Every flag the harness may pass to a rules-under-test gate: exactly what
# regen_gate.py had at GATE_MIN_COMMIT (02e1a7974), so any rules_ref the plan
# accepts can run. TestBaselineOverlay checks this set against that commit.
BASE_GATE_FLAGS = {
    "context": {
        "--metadata",
        "--spec-id",
        "--language",
        "--library",
        "--spec-file",
        "--omit-scores",
        "--out-md",
        "--out-weaknesses",
    },
    "sanitize-source": {"--source", "--out"},
    "decide": {
        "--spec-id",
        "--library",
        "--score",
        "--prev-stored",
        "--regen-json",
        "--weaknesses-json",
        "--spec-file",
        "--prev-renders",
    },
}


def _gate_at(commit: str, target: Path) -> Path:
    """regen_gate.py as it was at ``commit``; skips when this clone lacks the commit."""
    shown = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:automation/scripts/regen_gate.py"], capture_output=True
    )
    if shown.returncode != 0:
        pytest.skip(f"{commit[:10]} is not in this clone (shallow checkout)")
    target.mkdir(parents=True, exist_ok=True)
    path = target / "regen_gate.py"
    path.write_bytes(shown.stdout)
    return path


def _merge_regen() -> dict[str, Any]:
    return {
        "prev_rescored": 87,
        "improvements": [{"ref": "W1", "what": "legend larger", "where_visible": "legend"}],
        "regressions": [],
        "scenario_changed": False,
        "encodings_added": [],
        "change_request_applied": None,
    }


class TestBaselineOverlay:
    """The documented baseline arm (rules_ref = baseline_rules_sha, 0674ab6b5) runs
    on today's harness: materialize and collect hand an overlay gate only the flags
    it already had, and take everything newer from the harness's own copy."""

    def test_only_base_flags_reach_the_overlay(self, bundles, workspace, tmp_path, monkeypatch):
        calls: list[list[str]] = []
        real = rt._run_gate

        def spy(gate_script: Path, args: list[str], python: str = sys.executable) -> dict[str, str]:
            calls.append(list(args))
            return real(gate_script, args, python)

        monkeypatch.setattr(rt, "_run_gate", spy)
        tmp = rt.TmpPaths(tmp_path / "tmp")
        cell = _cell("r-bubble-basic-matplotlib-v1-v0", "regen", "forward")
        out = rt.materialize(bundles["out"] / cell["item"], workspace, cell, GATE_SCRIPT, tmp=tmp)
        _write_review(workspace, score=88, regen=_merge_regen())
        rt.collect(
            workspace,
            cell,
            tmp_path / "cell",
            execution_file="",
            review_outcome="success",
            materialize_ok=True,
            gate_script=GATE_SCRIPT,
            prev_stored=out["prev_stored"],
            tmp=tmp,
        )
        assert [c[0] for c in calls] == ["context", "sanitize-source", "decide"]
        for call in calls:
            flags = {arg for arg in call[1:] if arg.startswith("--")}
            assert flags <= BASE_GATE_FLAGS[call[0]], call

    def test_base_flags_exist_at_the_oldest_accepted_rules(self, tmp_path):
        gate = _gate_at(rt.GATE_MIN_COMMIT, tmp_path / "min")
        for sub, flags in BASE_GATE_FLAGS.items():
            usage = subprocess.run(
                [sys.executable, str(gate), sub, "--help"], capture_output=True, text=True, check=True
            ).stdout
            assert flags <= set(re.findall(r"--[a-z-]+", usage)), sub

    def test_regen_cell_on_the_baseline_rules(self, bundles, workspace, tmp_path):
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        gate = _gate_at(manifest["baseline_rules_sha"], tmp_path / "baseline")
        tmp = rt.TmpPaths(tmp_path / "tmp")
        cell = _cell("r-bubble-basic-matplotlib-v1-v0", "regen", "forward")
        out = rt.materialize(bundles["out"] / cell["item"], workspace, cell, gate, tmp=tmp)
        assert out["prev_stored"] == "88"
        assert "Quality: hidden/100" in tmp.prev_impl(".py").read_text(encoding="utf-8")
        assert "Previous quality score" not in tmp.prev_review.read_text(encoding="utf-8")
        impl = (workspace / "plots/bubble-basic/implementations/python/matplotlib.py").read_text(encoding="utf-8")
        assert "Quality: pending" in impl  # the harness's own header reset, not the overlay's
        _write_review(workspace, score=88, regen=_merge_regen())
        record = rt.collect(
            workspace,
            cell,
            tmp_path / "cell",
            execution_file="",
            review_outcome="success",
            materialize_ok=True,
            gate_script=gate,
            prev_stored=out["prev_stored"],
            tmp=tmp,
        )
        assert record["gate"]["verdict"] == "merge" and record["gate"]["prev_rescored"] == 87
        assert record["gate"]["code"] is None  # reason codes arrived with #11950
        assert record["regen_counts"] == {"total": 1, "visible": 1, "permission": 0}
        assert record["model"] is None and record["model_alias"] == "sonnet"


# ---------------------------------------------------------------------------
# freeze
# ---------------------------------------------------------------------------


def _snapshot(root: Path, name: str, commit: str, renders: dict[tuple[str, str], bytes]) -> str:
    snap = root / name
    (snap).mkdir(parents=True)
    (snap / "manifest.yaml").write_text(f"version: {name}\nmain_sha: {commit}\n", encoding="utf-8")
    for (lib, theme), data in renders.items():
        target = snap / "renders" / rt.language_of(lib) / lib / f"plot-{theme}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return name


def _no_stats(a: Path, b: Path) -> dict[str, Any]:
    return {"changed_px_pct": 0.0 if a.read_bytes() == b.read_bytes() else 5.0, "max_channel_delta": 1}


class TestFreeze:
    def _setup(self, repo: dict[str, Any], tmp_path: Path, identity: bool = False) -> dict[str, Any]:
        snaps = tmp_path / "snaps"
        v0 = _snapshot(
            snaps, "v0", repo["v0"], {("matplotlib", t): fake_png(salt=b"v0" + t.encode()) for t in rt.THEMES}
        )
        v1 = _snapshot(
            snaps, "v1", repo["v1"], {("matplotlib", t): fake_png(salt=b"v1" + t.encode()) for t in rt.THEMES}
        )
        _git(repo["root"], "update-ref", "refs/remotes/origin/main", repo["v1"])
        prev = (
            {"commit": repo["v1"], "render": {"snapshot": v1}}
            if identity
            else {"commit": repo["v0"], "render": {"snapshot": v0}}
        )
        manifest = _manifest(
            baseline_rules_sha=repo["v1"],
            spec_commit=repo["v1"],
            items=[
                {
                    "id": "f-bubble-basic-matplotlib",
                    "kind": "fresh",
                    "tier": "core",
                    "spec_id": "bubble-basic",
                    "library": "matplotlib",
                    "new": {"commit": repo["v1"], "render": "production"},
                },
                {
                    "id": "r-pair",
                    "kind": "regen",
                    "tier": "core",
                    "spec_id": "bubble-basic",
                    "library": "matplotlib",
                    "class": "identity",
                    "new": {"commit": repo["v1"], "render": {"snapshot": v1}},
                    "prev": prev,
                    "expected": None,
                },
            ],
        )
        production = {
            f"{rt.PUBLIC_BASE}/plots/bubble-basic/python/matplotlib/plot-{t}.png": fake_png(salt=b"prod" + t.encode())
            for t in rt.THEMES
        }
        return {"manifest": manifest, "snaps": snaps, "production": production}

    def _freeze(self, setup, repo, tmp_path, bucket: dict[str, bytes] | None = None):
        bucket = bucket or {}

        def fetch(url: str) -> bytes | None:
            return setup["production"].get(url) or bucket.get(url)

        return rt.freeze(
            setup["manifest"],
            repo=repo["root"],
            snapshots_root=setup["snaps"],
            staging=tmp_path / "staging",
            fetch=fetch,
            lister=lambda wf, st: [],
            stats=_no_stats,
            now=NOW,
        )

    def test_dry_run_builds_the_lock_and_no_clobber_commands(self, repo, tmp_path):
        setup = self._setup(repo, tmp_path, identity=True)
        result = self._freeze(setup, repo, tmp_path)
        lock = result["lock"]
        assert len(lock["objects"]) == 6
        obj = "retest/sets/v1/f-bubble-basic-matplotlib/new-light.png"
        assert lock["objects"][obj]["sha256"] == sha(fake_png(salt=b"prodlight"))
        assert lock["sources"][obj].endswith("/plots/bubble-basic/python/matplotlib/plot-light.png")
        assert lock["pairs"]["r-pair"]["light"]["changed_px_pct"] == 0.0
        assert (tmp_path / "staging" / obj).read_bytes() == fake_png(salt=b"prodlight")
        assert len(result["commands"]) == 6
        for command in result["commands"]:
            assert command[:5] == [
                "gcloud",
                "storage",
                "cp",
                "--no-clobber",
                str(tmp_path / "staging" / command[5].split("anyplot-images/", 1)[1]),
            ]
            assert command[5].startswith("gs://anyplot-images/retest/sets/v1/")
        # The lock satisfies the harness's own loader.
        lock_file = tmp_path / "lock.json"
        lock_file.write_text(json.dumps(lock), encoding="utf-8")
        assert rt.load_lock(lock_file, setup["manifest"])["set"] == "v1"

    def test_identity_pair_with_different_renders_is_refused(self, repo, tmp_path):
        setup = self._setup(repo, tmp_path, identity=False)
        with pytest.raises(rt.HarnessError, match="labelled identity but its renders differ"):
            self._freeze(setup, repo, tmp_path)

    def test_existing_object_is_skipped_or_refused(self, repo, tmp_path):
        setup = self._setup(repo, tmp_path, identity=True)
        obj = "retest/sets/v1/f-bubble-basic-matplotlib/new-light.png"
        same = {f"{rt.PUBLIC_BASE}/{obj}": fake_png(salt=b"prodlight")}
        assert len(self._freeze(setup, repo, tmp_path, bucket=same)["commands"]) == 5
        different = {f"{rt.PUBLIC_BASE}/{obj}": fake_png(salt=b"other")}
        with pytest.raises(rt.HarnessError, match="never rewritten"):
            self._freeze(setup, repo, tmp_path / "again", bucket=different)

    def test_production_render_newer_than_the_pin_is_refused(self, repo, tmp_path):
        setup = self._setup(repo, tmp_path, identity=True)
        setup["manifest"]["items"][0]["new"]["commit"] = repo["v0"]
        with pytest.raises(rt.HarnessError, match="touched the implementation after"):
            self._freeze(setup, repo, tmp_path)

    def test_snapshot_taken_at_another_commit_is_refused(self, repo, tmp_path):
        setup = self._setup(repo, tmp_path, identity=True)
        setup["manifest"]["items"][1]["new"]["commit"] = repo["v0"]
        setup["manifest"]["items"][1]["prev"]["commit"] = repo["v0"]
        with pytest.raises(rt.HarnessError, match="was taken at"):
            self._freeze(setup, repo, tmp_path)

    def test_busy_pipeline_is_refused(self, repo, tmp_path):
        setup = self._setup(repo, tmp_path, identity=True)

        def lister(wf, st):
            return [{"databaseId": 3, "createdAt": NOW.isoformat()}] if st == "queued" else []

        with pytest.raises(rt.HarnessError, match="busy"):
            rt.freeze(
                setup["manifest"],
                repo=repo["root"],
                snapshots_root=setup["snaps"],
                staging=tmp_path / "s",
                fetch=lambda u: None,
                lister=lister,
                stats=_no_stats,
                now=NOW,
            )

    def test_every_refusal_is_listed_at_once(self, repo, tmp_path):
        setup = self._setup(repo, tmp_path, identity=True)
        setup["production"] = {url: fake_png(4800, 2700, salt=url.encode()) for url in setup["production"]}
        setup["manifest"]["items"][1]["new"]["commit"] = repo["v0"]
        setup["manifest"]["items"][1]["prev"]["commit"] = repo["v0"]
        with pytest.raises(rt.HarnessError) as refused:
            self._freeze(setup, repo, tmp_path)
        text = str(refused.value)
        assert text.startswith("freeze refused (4 problem(s)):")
        assert "f-bubble-basic-matplotlib new light: 4800x2700 is not a canonical canvas" in text
        assert "f-bubble-basic-matplotlib new dark: 4800x2700 is not a canonical canvas" in text
        # A pin refusal is reported once per role, not once per theme.
        assert text.count("was taken at") == 2

    def test_verify_uploaded(self):
        lock = {"objects": {"a.png": {"sha256": sha(b"x")}, "b.png": {"sha256": sha(b"y")}}}
        bucket = {f"{rt.PUBLIC_BASE}/a.png": b"x", f"{rt.PUBLIC_BASE}/b.png": b"z"}
        assert rt.verify_uploaded(lock, fetch=bucket.get) == ["b.png: sha256 differs"]

    def test_pixel_stats(self, tmp_path):
        from PIL import Image

        a, b = tmp_path / "a.png", tmp_path / "b.png"
        Image.new("RGBA", (4, 4), (10, 10, 10, 255)).save(a)
        img = Image.new("RGBA", (4, 4), (10, 10, 10, 255))
        img.putpixel((0, 0), (47, 10, 10, 255))
        img.save(b)
        assert rt.pixel_stats(a, b) == {"changed_px_pct": 6.25, "max_channel_delta": 37}
        assert rt.pixel_stats(a, a) == {"changed_px_pct": 0.0, "max_channel_delta": 0}


class TestCheckRenders:
    """validate --check-renders: freeze's source refusals from PNG headers alone."""

    def _manifest(self, repo: dict[str, Any], snaps: Path) -> dict[str, Any]:
        _snapshot(snaps, "v1", repo["v1"], {("matplotlib", t): fake_png(2400, 2400) for t in rt.THEMES})
        # Named v0 but taken at v1: freeze would refuse it.
        _snapshot(snaps, "v0", repo["v1"], {("matplotlib", t): fake_png() for t in rt.THEMES})
        _git(repo["root"], "update-ref", "refs/remotes/origin/main", repo["v1"])
        base = {"tier": "core", "spec_id": "bubble-basic", "library": "matplotlib"}
        return _manifest(
            baseline_rules_sha=repo["v1"],
            spec_commit=repo["v1"],
            items=[
                {**base, "id": "f-a", "kind": "fresh", "new": {"commit": repo["v1"], "render": "production"}},
                {**base, "id": "f-b", "kind": "fresh", "new": {"commit": repo["v0"], "render": "production"}},
                {
                    **base,
                    "id": "r-c",
                    "kind": "regen",
                    "class": "different",
                    "new": {"commit": repo["v1"], "render": {"snapshot": "v1"}},
                    "prev": {"commit": repo["v0"], "render": {"snapshot": "v0"}},
                },
                {
                    **base,
                    "id": "r-d",
                    "kind": "regen",
                    "class": "identity",
                    "new": {"commit": repo["v1"], "render": {"snapshot": "absent"}},
                    "prev": {"commit": repo["v1"], "render": {"snapshot": "absent"}},
                },
            ],
        )

    def test_lists_every_problem_from_headers(self, repo, tmp_path):
        snaps = tmp_path / "snaps"
        manifest = self._manifest(repo, snaps)
        heads: list[str] = []

        def head(url: str) -> bytes:
            heads.append(url)
            return (fake_png(4800, 2700) if url.endswith("plot-dark.png") else fake_png())[: rt.PNG_HEADER_BYTES]

        result = rt.check_renders(manifest, repo=repo["root"], snapshots_root=snaps, head=head)
        assert result["problems"] == [
            f"f-a new dark: 4800x2700 is not a canonical canvas ({rt.PUBLIC_BASE}/plots/bubble-basic/python/matplotlib/plot-dark.png)",
            f"f-b new: 1 commit(s) on origin/main touched the implementation after {repo['v0'][:10]} — the production "
            "render no longer matches the pinned source; re-pin the item",
            f"r-c prev: snapshot {snaps / 'v0'} was taken at {repo['v1']}, not {repo['v0']}",
        ]
        assert result["checked"] == 4  # f-a light and dark, r-c new light and dark
        assert result["skipped"] == [
            "r-d new: snapshot absent is not present",
            "r-d prev: snapshot absent is not present",
        ]
        assert len(heads) == 2  # only f-a: a failed pin is never fetched

    def test_missing_production_object(self, repo, tmp_path):
        snaps = tmp_path / "snaps"
        manifest = self._manifest(repo, snaps)
        manifest["items"] = manifest["items"][:1]
        result = rt.check_renders(manifest, repo=repo["root"], snapshots_root=snaps, head=lambda url: None)
        assert [p.split(":")[0] for p in result["problems"]] == ["f-a new light", "f-a new dark"]
        assert all("not found" in p for p in result["problems"])

    def test_cli(self, monkeypatch, capsys, tmp_path):
        calls: list[Path] = []

        def fake(manifest, *, repo, snapshots_root, head=None):
            calls.append(snapshots_root)
            return {"problems": [], "checked": 94, "skipped": []}

        monkeypatch.setattr(rt, "check_renders", fake)
        lock = str(tmp_path / "absent.json")
        assert rt.main(["validate", "--manifest", str(MANIFEST), "--lock", lock, "--check-renders"]) == 0
        assert "renders ok: 94 PNG headers on canonical canvases, 0 skipped" in capsys.readouterr().out
        assert calls == [Path(".")]

        def failing(manifest, *, repo, snapshots_root, head=None):
            return {"problems": ["x new light: 4800x2700 is not a canonical canvas"], "checked": 1, "skipped": []}

        monkeypatch.setattr(rt, "check_renders", failing)
        assert rt.main(["validate", "--manifest", str(MANIFEST), "--lock", lock, "--check-renders"]) == 1
        assert "freeze would refuse these renders (1 problem(s))" in capsys.readouterr().err

    def test_http_get_range_reads_only_the_header(self, monkeypatch):
        seen: dict[str, Any] = {}

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self, n: int = -1) -> bytes:
                seen["read"] = n
                return b"x" * (n if n > 0 else 100)

        def urlopen(request, timeout):
            seen["range"] = request.get_header("Range")
            return Response()

        monkeypatch.setattr(rt.urllib.request, "urlopen", urlopen)
        assert rt.http_get("https://example.invalid/a.png", first_bytes=24) == b"x" * 24
        assert seen == {"range": "bytes=0-23", "read": 24}
        seen.clear()
        assert rt.http_get("https://example.invalid/a.png") == b"x" * 100
        assert seen == {"range": None, "read": -1}


class TestCli:
    def test_validate_shipped_manifest(self, capsys):
        assert (
            rt.main(["validate", "--manifest", str(MANIFEST), "--lock", str(MANIFEST.with_suffix(".lock.json"))]) == 0
        )
        assert "manifest ok: set v1" in capsys.readouterr().out

    def test_plan_refuses_an_unfrozen_set(self, tmp_path, capsys):
        code = rt.main(
            [
                "plan",
                "--manifest",
                str(MANIFEST),
                "--lock",
                str(tmp_path / "absent.json"),
                "--rules-sha",
                A,
                "--skip-idle-check",
            ]
        )
        assert code == 1
        assert "not frozen yet" in capsys.readouterr().err

    def test_plan_writes_matrix_outputs(self, tmp_path, monkeypatch):
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        lock = {"version": 1, "set": "v1", "objects": {}}
        lock_file = tmp_path / "lock.json"
        lock_file.write_text(json.dumps(lock), encoding="utf-8")
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        monkeypatch.setattr(rt, "is_ancestor", lambda repo, a, b: True)  # independent of clone depth
        code = rt.main(
            [
                "plan",
                "--manifest",
                str(MANIFEST),
                "--lock",
                str(lock_file),
                "--rules-sha",
                manifest["baseline_rules_sha"],
                "--repo",
                str(REPO_ROOT),
                "--skip-idle-check",
            ]
        )
        assert code == 0
        values = dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines())
        cells = json.loads(values["matrix"])
        assert values["sessions"] == str(len(cells)) == str(3 * (15 + 7 * 2))
        assert all(set(c) >= {"id", "item", "kind", "spec_id", "library", "order", "run", "model"} for c in cells)
        assert len({c["id"] for c in cells}) == len(cells)
        assert all(re.fullmatch(r"[a-z0-9_-]+", c["id"]) for c in cells)  # safe artifact names

    def test_plan_reports_reused_and_rejected_resume_records(self, tmp_path, monkeypatch, capsys):
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        rules = manifest["baseline_rules_sha"]
        lock_file = tmp_path / "lock.json"
        lock_file.write_text(json.dumps({"version": 1, "set": "v1", "objects": {}}), encoding="utf-8")
        resume = tmp_path / "records.jsonl"
        kept = _resumed("f-bubble-basic-ggplot2__r1", rules_sha=rules)
        other_rules = _resumed("f-bubble-basic-ggplot2__r2", rules_sha=B)
        resume.write_text("".join(json.dumps(r) + "\n" for r in (kept, other_rules)), encoding="utf-8")
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        monkeypatch.setattr(rt, "is_ancestor", lambda repo, a, b: True)
        args = ["plan", "--manifest", str(MANIFEST), "--lock", str(lock_file), "--rules-sha", rules]
        args += ["--action-sha", ACTION, "--resume-records", str(resume), "--repo", str(REPO_ROOT)]
        assert rt.main([*args, "--subset", "f-bubble-basic-ggplot2", "--skip-idle-check"]) == 0
        values = dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines())
        assert values["resumed"] == "f-bubble-basic-ggplot2__r1"
        assert [c["id"] for c in json.loads(values["matrix"])] == [
            "f-bubble-basic-ggplot2__r2",
            "f-bubble-basic-ggplot2__r3",
        ]
        stdout = capsys.readouterr().out
        assert (
            f"::warning::resume: 1 record(s) rejected and run again (rules_sha {B[:10]} != {rules[:10]}): "
            "f-bubble-basic-ggplot2__r2"
        ) in stdout

    def test_report_merges_only_the_cells_plan_reused(self, tmp_path):
        manifest_file = tmp_path / "manifest.yaml"
        manifest_file.write_text(yaml.safe_dump(_manifest()), encoding="utf-8")
        item = "f-bubble-basic-matplotlib"
        resume = tmp_path / "records.jsonl"
        resumed = [_record(f"{item}__r1", item, 1, 90), _record(f"{item}__r2", item, 2, 70, rules_sha=A)]
        resume.write_text("".join(json.dumps(r) + "\n" for r in resumed), encoding="utf-8")
        cells = tmp_path / "cells"
        (cells / f"cell-{item}__r2").mkdir(parents=True)
        rerun = {**_record(f"{item}__r2", item, 2, 0), "ok": False, "error_class": "quota", "score_typed": None}
        (cells / f"cell-{item}__r2" / "record.json").write_text(json.dumps(rerun), encoding="utf-8")
        base = ["report", "--manifest", str(manifest_file), "--lock", str(tmp_path / "absent.json")]
        base += ["--cells", str(cells), "--resume-records", str(resume)]

        # Without plan's list the report refuses rather than guess.
        assert rt.main([*base, "--out", str(tmp_path / "refused")]) == 1

        assert rt.main([*base, "--out", str(tmp_path / "report"), "--resumed-cells", f"{item}__r1"]) == 0
        merged = rt.load_records(tmp_path / "report" / "records.jsonl")
        # r2's old record (other rules) was rejected by plan; its failed rerun stands.
        assert [(r["cell"], r["ok"]) for r in merged] == [(f"{item}__r1", True), (f"{item}__r2", False)]

    def test_cell_lifecycle_through_the_cli(self, bundles, workspace, tmp_path, monkeypatch):
        """materialize → (a review) → collect → report, called the way the workflow calls them."""
        monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        cell = _cell("r-bubble-basic-matplotlib-v1-v0", "regen", "reversed")
        tmp_base = tmp_path / "tmp"
        assert (
            rt.main(
                [
                    "materialize",
                    "--workspace",
                    str(workspace),
                    "--bundles",
                    str(bundles["out"]),
                    "--cell",
                    json.dumps(cell, indent=2),
                    "--gate-script",
                    str(GATE_SCRIPT),
                    "--tmp-base",
                    str(tmp_base),
                ]
            )
            == 0
        )
        outputs = dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines())
        assert outputs["is_regen"] == "true" and outputs["prev_stored"] == "92"
        assert outputs["started_at"].isdigit()

        regen = {
            "prev_rescored": 92,
            "improvements": [],
            "regressions": [],
            "scenario_changed": False,
            "encodings_added": [],
            "change_request_applied": None,
        }
        _write_review(workspace, score=86, regen=regen)
        cell_dir = tmp_path / "cells" / f"cell-{cell['id']}"
        assert (
            rt.main(
                [
                    "collect",
                    "--workspace",
                    str(workspace),
                    "--cell",
                    json.dumps(cell),
                    "--out",
                    str(cell_dir),
                    "--execution-file",
                    str(_execution(tmp_path, OK_RESULT)),
                    "--review-outcome",
                    "success",
                    "--materialize-outcome",
                    "success",
                    "--gate-script",
                    str(GATE_SCRIPT),
                    "--prev-stored",
                    outputs["prev_stored"],
                    "--tmp-base",
                    str(tmp_base),
                    "--started-at",
                    outputs["started_at"],
                    "--rules-sha",
                    B,
                ]
            )
            == 0
        )
        record = json.loads((cell_dir / "record.json").read_text(encoding="utf-8"))
        assert record["gate"]["verdict"] == "keep" and record["gate"]["code"] == "no_visible_improvement"
        assert record["order"] == "reversed"

        manifest_file = tmp_path / "manifest.yaml"
        manifest_file.write_text(yaml.safe_dump(bundles["manifest"]), encoding="utf-8")
        report_dir = tmp_path / "report"
        assert (
            rt.main(
                [
                    "report",
                    "--manifest",
                    str(manifest_file),
                    "--lock",
                    str(tmp_path / "absent.lock.json"),
                    "--cells",
                    str(tmp_path / "cells"),
                    "--out",
                    str(report_dir),
                    "--label",
                    "smoke",
                    "--rules-sha",
                    B,
                    "--harness-sha",
                    A,
                    "--run-url",
                    "u",
                ]
            )
            == 0
        )
        snippet = (report_dir / "snippet.md").read_text(encoding="utf-8")
        assert "(1 pair × 1 order × 1)" in snippet
        assert "Regen: claude-sonnet-5" in snippet
        assert "lock sha256 unfrozen" in snippet
