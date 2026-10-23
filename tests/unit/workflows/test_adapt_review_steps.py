"""impl-review's adaptability steps (PR 2 of docs/concepts/adaptable-code.md), run for real where they can be.

- "Adaptability check (record-only)" runs against a throwaway repository whose
  `origin/main` holds the catalogue's bar-grouped matplotlib file (it fails the
  check) and whose detached PR head holds the converted fixture of PR 1 (it
  passes), with the real checker mirror and record builder in `$RUNNER_TEMP/
  regen-tools/`, a fake `gsutil` serving a local "staging" folder, and a stub
  `regen_gate.py` for `adapt-route` (part D of PR 2 implements the real one; one
  test runs it once it is there). The step's fixed `/tmp/anyplot-*` paths are
  moved under the test's own directory.
- The review-free path: which steps it runs, the carried quality label, the
  `regen:adapt` count label, the carried metadata, and what impl-merge reads.

Every path ends with the step's exit code 0 and `review_skipped` as its last
output: anything short of that leaves the review running.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import adapt_record as ar
from tests.unit.workflows.test_pipeline_retry_gaps import _calls, _code_only, _run, _step, _steps


REPO_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "impl-review.yml"
TOOLS = REPO_ROOT / "automation" / "scripts"
FIXTURE = REPO_ROOT / "tests" / "unit" / "core" / "fixtures" / "adaptability" / "bar_grouped_matplotlib.py"
SPEC_ID, LIB = "bar-grouped", "matplotlib"
IMPL = f"plots/{SPEC_ID}/implementations/python/{LIB}.py"
SPEC = f"plots/{SPEC_ID}/specification.md"
ADAPT = "Adaptability check (record-only)"
PY314 = "Set up Python for the adaptability mirror"
CARRIED_LABEL = "Add carried quality score label"
EARLY = "Add preliminary verdict label (early)"
METADATA = "Update metadata and implementation header"
VERDICT = "Add verdict label and take action"
REVIEW_FREE = "steps.adapt.outputs.review_skipped == 'true'"
PINNED_RECORDS = ("/tmp/anyplot-adapt-new.json", "/tmp/anyplot-adapt-prev.json")

FAKE_GSUTIL = """\
printf '%s\\n' "$*" >> "$GSUTIL_LOG"
case "${GSUTIL_MODE:-ok}" in
  nomatch) echo "CommandException: No URLs matched: $4" >&2; exit 1 ;;
  fail) echo "ServiceException: 503 Service Unavailable" >&2; exit 1 ;;
esac
for dest in "$@"; do :; done
cp -r "$GSUTIL_BUCKET"/. "$dest"
"""

# adapt-route as part D specifies it (contract section 5.2): exit 0, adapt_* keys to $GITHUB_OUTPUT.
STUB_GATE = """\
import json, os, sys
with open(os.environ["STUB_LOG"], "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1] != "adapt-route" or os.environ.get("STUB_RC", "0") != "0":
    sys.exit(int(os.environ.get("STUB_RC", "2")))
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    route, why = os.environ.get("STUB_ROUTE", "true"), os.environ.get("STUB_WHY", "route")
    f.write(f"adapt_route={route}\\nadapt_why={why}\\nadapt_prev=fail\\nadapt_new=pass\\n")
print(f"::notice::adapt_route spec=s lib=l route={os.environ.get('STUB_ROUTE', 'true')}")
"""


def _env(tmp_path: Path) -> dict[str, str]:
    empty = tmp_path / "gitconfig"
    empty.touch()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1")
    return env


def _git(tmp_path: Path, repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        capture_output=True,
        text=True,
        env=_env(tmp_path),
        check=True,
    )
    return result.stdout.strip()


def _outputs(path: Path) -> list[tuple[str, str]]:
    """The `key=value` lines of a $GITHUB_OUTPUT file, in order."""
    if not path.exists():
        return []
    pairs = [line.partition("=") for line in path.read_text(encoding="utf-8").splitlines() if "=" in line]
    return [(key, value) for key, _, value in pairs]


class Pair:
    """A PR head (the converted fixture) over origin/main (the catalogue's file), plus staging."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.work = tmp_path / "work"
        self.runner = tmp_path / "runner"
        self.bucket = tmp_path / "bucket"
        self.output = tmp_path / "github_output"
        self.stub_log = tmp_path / "stub_log"
        self.gsutil_log = tmp_path / "gsutil_log"
        self.work.mkdir()
        _git(tmp_path, self.work, "init", "-q", "-b", "main")
        for rel in (IMPL, SPEC):
            path = self.work / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((REPO_ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
        _git(tmp_path, self.work, "add", "-A")
        _git(tmp_path, self.work, "commit", "-q", "-m", "main")
        _git(tmp_path, self.work, "update-ref", "refs/remotes/origin/main", "HEAD")
        _git(tmp_path, self.work, "checkout", "-q", "--detach")
        (self.work / IMPL).write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
        _git(tmp_path, self.work, "commit", "-q", "-am", "converted")
        self.new_text = (self.work / IMPL).read_text(encoding="utf-8")
        self.prev_text = (REPO_ROOT / IMPL).read_text(encoding="utf-8")
        # The workflow-ref copies "Checkout PR code" takes, with the adapt-route stub.
        tools = self.runner / "regen-tools"
        tools.mkdir(parents=True)
        for name in ("adaptability_check.py", "adapt_record.py"):
            shutil.copyfile(TOOLS / name, tools / name)
        (tools / "regen_gate.py").write_text(STUB_GATE, encoding="utf-8")
        # What impl-generate staged for a regeneration.
        (self.bucket / "prev").mkdir(parents=True)
        (self.bucket / "new").mkdir()
        self.stage("new-smoke.json", self.smoke(self.new_text))
        self.stage("prev-smoke.json", self.smoke(self.prev_text, status="skipped", why="static_failed"))
        self.stage("pair.json", {"v": 1, "status": "identical", "why": "-"})
        self.stage("selfcheck.jsonl", '{"static": "fail", "smoke": "pass"}\n{"static": "pass", "smoke": "pass"}\n')
        for side in ("prev", "new"):
            for theme in ("light", "dark"):
                (self.bucket / side / f"plot-{theme}.png").write_bytes(b"\x89PNG")
        # Regen context's sanitized predecessor (adapt-route reads its line count).
        self.tmp_file("anyplot-prev-impl.py").write_text(self.prev_text, encoding="utf-8")

    def tmp_file(self, name: str) -> Path:
        return self.tmp / name

    @staticmethod
    def smoke(text: str, **overrides: Any) -> dict[str, Any]:
        data = {
            "v": 1,
            "code_sha256": ar.code_sha256(text),
            "status": "pass",
            "why": "-",
            "results": [{"name": "renamed", "status": "pass", "advisory": False, "line": None, "error": None}],
            "failed": [],
            "advisory_failed": [],
        }
        data.update(overrides)
        return data

    def stage(self, name: str, data: Any) -> None:
        text = data if isinstance(data, str) else json.dumps(data)
        (self.bucket / name).write_text(text, encoding="utf-8")

    def run(self, **env: str) -> tuple[subprocess.CompletedProcess[str], dict[str, str], list[tuple[str, str]]]:
        script = _step("impl-review.yml", ADAPT)["run"]
        for path in (*PINNED_RECORDS, "/tmp/anyplot-prev-impl.py", "/tmp/anyplot-canvas-gate.txt"):
            assert path in script, path
        script = script.replace("/tmp/anyplot-", f"{self.tmp}/anyplot-")
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir(exist_ok=True)
        (bin_dir / "gsutil").write_text("#!/bin/sh\n" + FAKE_GSUTIL, encoding="utf-8")
        (bin_dir / "gsutil").chmod(0o755)
        defaults = {
            "SPEC_ID": SPEC_ID,
            "LIBRARY": LIB,
            "LANGUAGE": "python",
            "IS_REGEN": "true",
            "GCS_OK": "true",
            "PY314": sys.executable,
            "ADAPT_REVIEW_FREE": "true",
            "CONTEXT_OUTCOME": "success",
            "PREV_STORED": "94",
            "CHANGE_REQUEST_PRESENT": "false",
            "RUNNER_TEMP": str(self.runner),
            "GITHUB_OUTPUT": str(self.output),
            "GSUTIL_BUCKET": str(self.bucket),
            "GSUTIL_LOG": str(self.gsutil_log),
            "STUB_LOG": str(self.stub_log),
        }
        result, _ = _run(script, self.work, self.tmp, **{**defaults, **env})
        outputs = _outputs(self.output)
        return result, dict(outputs), outputs

    def record(self, side: str) -> dict[str, Any] | None:
        path = self.tmp_file(f"anyplot-adapt-{side}.json")
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def route_calls(self) -> list[list[str]]:
        if not self.stub_log.exists():
            return []
        return [json.loads(line) for line in self.stub_log.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def pair(tmp_path: Path) -> Pair:
    return Pair(tmp_path)


def _done(result: subprocess.CompletedProcess[str], ordered: list[tuple[str, str]]) -> None:
    """The step ended cleanly, and review_skipped was its last write."""
    assert result.returncode == 0, result.stdout + result.stderr
    assert ordered[-1][0] == "review_skipped", ordered


class TestAdaptStepRuns:
    def test_a_conversion_inside_the_route_skips_the_review(self, pair):
        result, out, ordered = pair.run()
        _done(result, ordered)
        assert out == {
            "new_status": "pass",
            "prev_status": "fail",
            "route": "true",
            "why": "route",
            "review_skipped": "true",
        }
        # The route's own outputs went to its file, not to this step's.
        assert not any(key.startswith("adapt_") for key, _ in ordered)
        assert (
            "::notice::adapt_review spec=bar-grouped lib=matplotlib switch=on route=true review=skipped why=route"
            in (result.stdout)
        )
        new, prev = pair.record("new"), pair.record("prev")
        assert new is not None and prev is not None
        assert (new["side"], new["status"], new["static"]["status"], new["smoke"]["status"]) == (
            "new",
            "pass",
            "pass",
            "pass",
        )
        assert new["selfcheck"] == {"attempts": 2, "first": "fail"}
        assert new["lines"] == len(pair.new_text.splitlines())
        assert (prev["side"], prev["status"], prev["static"]["status"], prev["smoke"]["status"]) == (
            "prev",
            "fail",
            "fail",
            "skipped",
        )
        assert prev["lines"] == len(pair.prev_text.splitlines())
        assert "selfcheck" not in prev
        assert "side=new status=pass static=pass smoke=pass" in result.stdout
        assert "side=prev status=fail static=fail smoke=skipped rules=layout,columns,interface" in result.stdout

    def test_adapt_route_gets_the_contracts_arguments(self, pair):
        pair.run()
        (call,) = pair.route_calls()
        assert call == [
            "adapt-route",
            "--spec-id",
            SPEC_ID,
            "--library",
            LIB,
            "--adapt-new",
            str(pair.tmp_file("anyplot-adapt-new.json")),
            "--adapt-prev",
            str(pair.tmp_file("anyplot-adapt-prev.json")),
            "--adapt-pair",
            str(pair.runner / "adapt" / "pair.json"),
            "--prev-impl",
            str(pair.tmp_file("anyplot-prev-impl.py")),
            "--new-impl",
            IMPL,
        ]

    def test_the_artifacts_stay_under_runner_temp_and_the_source_copy_goes(self, pair):
        pair.run()
        adapt = pair.runner / "adapt"
        for name in ("new-smoke.json", "prev-smoke.json", "pair.json", "static-new.json", "static-prev.json"):
            assert (adapt / name).is_file(), name
        assert (adapt / "prev" / "plot-light.png").is_file()
        # The predecessor's source carries its stored score in the header.
        assert not (adapt / "prev-src").exists()
        assert sorted(p.name for p in pair.tmp.glob("anyplot-adapt-*")) == [
            "anyplot-adapt-new.json",
            "anyplot-adapt-prev.json",
        ]

    def test_a_first_generation_has_no_predecessor_and_no_route(self, pair):
        pair.tmp_file("anyplot-adapt-prev.json").write_text('{"stale": true}', encoding="utf-8")
        result, out, ordered = pair.run(IS_REGEN="false")
        _done(result, ordered)
        assert out == {
            "new_status": "pass",
            "prev_status": "n/a",
            "route": "n/a",
            "why": "n/a",
            "review_skipped": "false",
        }
        assert pair.record("prev") is None  # a stale record never stands in
        assert pair.route_calls() == []
        assert "route=n/a review=run why=first_generation" in result.stdout

    @pytest.mark.parametrize(
        ("env", "why"),
        [
            ({"ADAPT_REVIEW_FREE": "false"}, "switch_off"),
            ({"ADAPT_REVIEW_FREE": "TRUE"}, "switch_off"),  # only the literal `true`
            ({"ADAPT_REVIEW_FREE": ""}, "switch_off"),
            ({"STUB_ROUTE": "false", "STUB_WHY": "identity_dark"}, "no_route"),
            ({"CONTEXT_OUTCOME": "failure"}, "context_failed"),
            ({"PREV_STORED": "n/a"}, "no_stored_score"),
            ({"PREV_STORED": "0"}, "no_stored_score"),
            ({"PREV_STORED": "101"}, "no_stored_score"),
            ({"PREV_STORED": "9x"}, "no_stored_score"),
            ({"CHANGE_REQUEST_PRESENT": "true"}, "change_request"),
        ],
    )
    def test_anything_short_of_the_full_set_reviews(self, pair, env, why):
        result, out, ordered = pair.run(**env)
        _done(result, ordered)
        assert out["review_skipped"] == "false"
        assert f"review=run why={why}" in result.stdout
        if why == "no_route":
            assert (out["route"], out["why"]) == ("false", "identity_dark")

    def test_a_failed_canvas_gate_reviews_and_reaches_the_route(self, pair):
        pair.tmp_file("anyplot-canvas-gate.txt").write_text("VQ-05 (both): ...", encoding="utf-8")
        result, out, ordered = pair.run()
        _done(result, ordered)
        assert out["review_skipped"] == "false"
        assert "review=run why=canvas_failed" in result.stdout
        assert pair.route_calls()[0][-1] == "--canvas-failed"

    @pytest.mark.parametrize(
        ("env", "why"),
        [
            ({"STUB_RC": "2"}, "route_error"),
            ({"STUB_RC": "1"}, "route_error"),
            ({"STUB_ROUTE": "maybe", "STUB_WHY": "route"}, "route_error"),
            ({"STUB_ROUTE": "", "STUB_WHY": ""}, "route_error"),
            ({"STUB_WHY": "x y"}, "route_error"),
            ({"STUB_WHY": "Route;rm"}, "route_error"),
            ({"STUB_WHY": "prev_passes"}, "prev_passes"),  # `true` must come with why=route
        ],
    )
    def test_an_unclear_route_answer_is_no_route(self, pair, env, why):
        result, out, ordered = pair.run(**env)
        _done(result, ordered)
        assert (out["route"], out["why"], out["review_skipped"]) == ("false", why, "false")

    def test_no_staged_artifacts_read_as_missing(self, pair):
        # The real gate answers new_unknown for a record without a smoke run.
        result, out, ordered = pair.run(GSUTIL_MODE="nomatch", STUB_ROUTE="false", STUB_WHY="new_unknown")
        _done(result, ordered)
        assert len(pair.gsutil_log.read_text(encoding="utf-8").splitlines()) == 1  # a state, not a blip
        assert "no adapt artifacts staged" in result.stdout
        new = pair.record("new")
        assert new is not None and new["smoke"]["status"] == "missing" and new["selfcheck"] is None
        assert (out["new_status"], out["review_skipped"]) == ("unknown", "false")

    def test_a_download_that_keeps_failing_is_retried_and_never_fatal(self, pair):
        result, out, ordered = pair.run(GSUTIL_MODE="fail", STUB_ROUTE="false", STUB_WHY="no_record")
        _done(result, ordered)
        assert len(pair.gsutil_log.read_text(encoding="utf-8").splitlines()) == 3
        assert result.stdout.count("::warning::adapt artifact download failed") == 3
        assert out["new_status"] == "unknown"

    def test_without_gcp_nothing_is_downloaded(self, pair):
        result, out, ordered = pair.run(GCS_OK="false", STUB_ROUTE="false", STUB_WHY="no_record")
        _done(result, ordered)
        assert not pair.gsutil_log.exists()
        assert out["new_status"] == "unknown"

    def test_staged_files_never_stand_in_for_the_mirror(self, pair):
        """Staging is writable from the generation runner; only this step writes static-*.json and prev-src."""
        pair.stage("static-prev.json", {"version": 1, "status": "pass", "findings": []})
        (pair.bucket / "prev-src").mkdir()
        (pair.bucket / "prev-src" / f"{LIB}.py").write_text(pair.new_text, encoding="utf-8")
        result, out, ordered = pair.run()
        _done(result, ordered)
        prev = pair.record("prev")
        assert prev is not None and prev["static"]["status"] == "fail"
        assert prev["lines"] == len(pair.prev_text.splitlines())

    def test_a_smoke_run_of_other_code_is_stale(self, pair):
        pair.stage("new-smoke.json", pair.smoke(pair.new_text + "# edited after the smoke run\n"))
        result, out, ordered = pair.run(STUB_ROUTE="false", STUB_WHY="new_unknown")
        _done(result, ordered)
        new = pair.record("new")
        assert new is not None and (new["status"], new["why"]) == ("unknown", "smoke_stale")

    def test_a_crashing_mirror_is_an_unknown_record(self, pair):
        (pair.runner / "regen-tools" / "adaptability_check.py").write_text("import sys\nsys.exit(1)\n")
        result, out, ordered = pair.run(STUB_ROUTE="false", STUB_WHY="new_unknown")
        _done(result, ordered)
        new = pair.record("new")
        assert new is not None and new["static"] == {"status": "error", "exit": 1}
        assert (out["new_status"], out["prev_status"]) == ("unknown", "unknown")

    def test_a_crashing_record_builder_leaves_no_record_and_reviews(self, pair):
        (pair.runner / "regen-tools" / "adapt_record.py").write_text("raise SystemExit(3)\n")
        result, out, ordered = pair.run(STUB_ROUTE="false", STUB_WHY="no_record")
        _done(result, ordered)
        assert pair.record("new") is None and pair.record("prev") is None
        assert (out["new_status"], out["prev_status"]) == ("n/a", "n/a")
        assert "adapt record (new) not written" in result.stdout

    def test_a_predecessor_missing_on_main_is_unknown(self, pair):
        _git(pair.tmp, pair.work, "update-ref", "-d", "refs/remotes/origin/main")
        result, out, ordered = pair.run(STUB_ROUTE="false", STUB_WHY="prev_unknown")
        _done(result, ordered)
        prev = pair.record("prev")
        assert prev is not None and prev["static"] == {"status": "error", "exit": 2} and prev["lines"] is None
        assert out["prev_status"] == "unknown"

    def test_the_real_gate_routes_this_pair(self, pair):
        """Part D's adapt-route on the same inputs (skipped until part D is merged)."""
        gate = TOOLS / "regen_gate.py"
        if "adapt-route" not in gate.read_text(encoding="utf-8"):
            pytest.skip("regen_gate.py adapt-route arrives with PR 2 part D")
        shutil.copyfile(gate, pair.runner / "regen-tools" / "regen_gate.py")
        identity = {"old_size": [3200, 1800], "new_size": [3200, 1800], "differing": 0, "fraction": 0.0011}
        pair.stage(
            "pair.json",
            {
                "v": 1,
                "tool": "core.smoke_run pair",
                "library": LIB,
                "themes": ["light", "dark"],
                "identity": {
                    "light": {**identity, "bound": 0.005, "passed": True},
                    "dark": {**identity, "bound": 0.005, "passed": True},
                },
                "status": "identical",
                "why": "-",
            },
        )
        result, out, ordered = pair.run()
        _done(result, ordered)
        assert (out["route"], out["why"]) == ("true", "route"), result.stdout


class TestAdaptStepWiring:
    def test_order_canvas_gate_then_mirror_then_the_review(self):
        names = [s.get("name") for s in _steps("impl-review.yml")]
        canvas = names.index("Canvas dimension gate")
        assert names[canvas + 1 : canvas + 4] == [PY314, ADAPT, "React with eyes emoji"]
        assert names.index("Regen context") < names.index(ADAPT)
        assert names.index("Download plot images from staging") < names.index(ADAPT)
        assert names.index(ADAPT) < names.index("Hide the previous review") < names.index("Run AI Quality Review")

    def test_python_only_record_only_and_bounded(self):
        step = _step("impl-review.yml", ADAPT)
        assert step["id"] == "adapt"
        assert step["if"] == "steps.lang.outputs.language == 'python'"
        assert step["continue-on-error"] is True
        assert step["timeout-minutes"] == 5
        assert "exit 1" not in _code_only(step["run"])
        assert step["env"]["ADAPT_REVIEW_FREE"] == "${{ vars.ADAPT_REVIEW_FREE || 'false' }}"
        assert step["env"]["PY314"] == "${{ steps.py314.outputs.python-path }}"
        assert step["env"]["CONTEXT_OUTCOME"] == "${{ steps.regen_ctx.outcome }}"

    def test_the_mirror_runs_on_a_pinned_314_without_touching_path(self):
        step = _step("impl-review.yml", PY314)
        assert step["id"] == "py314"
        assert step["uses"].startswith("actions/setup-python@")
        assert step["with"] == {"python-version": "3.14", "update-environment": False}
        assert step["continue-on-error"] is True
        assert 'PY="${PY314:-python3}"' in _step("impl-review.yml", ADAPT)["run"]

    def test_the_regen_tools_run_from_the_workflow_ref(self):
        script = _step("impl-review.yml", ADAPT)["run"]
        for tool in ("adaptability_check.py", "adapt_record.py", "regen_gate.py"):
            assert f'"$RUNNER_TEMP/regen-tools/{tool}"' in script, tool
        assert "automation/scripts/" not in script

    def test_the_review_never_sees_the_adapt_artifacts(self):
        download = _step("impl-review.yml", "Download plot images from staging")["run"]
        assert 'SRC="gs://anyplot-images/staging/${SPEC_ID}/${LANGUAGE}/${LIBRARY}/plot-*"' in download
        assert "/${LIBRARY}/*" not in download
        adapt = _step("impl-review.yml", ADAPT)["run"]
        assert 'OUT="$RUNNER_TEMP/adapt"' in adapt
        assert 'SRC="gs://anyplot-images/staging/${SPEC_ID}/${LANGUAGE}/${LIBRARY}/adapt/*"' in adapt
        assert 'gsutil -m cp -r "$SRC" "$OUT/"' in adapt
        prompt = _step("impl-review.yml", "Run AI Quality Review")["with"]["prompt"]
        assert "adapt" not in prompt.lower()

    def test_impl_merge_promotes_only_the_renders(self):
        script = _step("impl-merge.yml", "Promote GCS images to production")["run"]
        code = _code_only(script)
        assert 'cp "${STAGING}/plot-*" "${PRODUCTION}/"' in code
        assert '"${STAGING}/*"' not in code
        assert 'gsutil -m rm -r "${STAGING}/"' in code  # the cleanup still removes adapt/


class TestReviewFreeWiring:
    def test_the_review_is_skipped_only_on_the_switch(self):
        assert _step("impl-review.yml", "Run AI Quality Review")["if"] == "steps.adapt.outputs.review_skipped != 'true'"

    @pytest.mark.parametrize(
        "name",
        ["Regen gate", "Stage regen pair", EARLY, "Install Python dependencies for metadata update", METADATA, VERDICT],
    )
    def test_the_review_free_path_runs_these(self, name):
        assert REVIEW_FREE in _step("impl-review.yml", name)["if"], name

    @pytest.mark.parametrize(
        "name",
        [
            "Resolve review model",
            "Extract quality score",
            "Validate review output",
            "Add quality score label",
            "Check review feedback format (never gating)",
            "Write back the re-score (regen keep)",
            "Re-dispatch review after a post-score failure",
        ],
    )
    def test_and_never_these(self, name):
        assert "review_skipped" not in _step("impl-review.yml", name).get("if", ""), name

    def test_the_gate_and_the_metadata_need_a_regeneration_and_a_merge(self):
        assert _step("impl-review.yml", "Regen gate")["if"].startswith("steps.regen.outputs.is_regen == 'true' && (")
        cond = _step("impl-review.yml", METADATA)["if"]
        assert f"({REVIEW_FREE} && steps.gate.outputs.verdict == 'merge')" in cond

    def test_the_gate_gets_the_adapt_inputs(self):
        step = _step("impl-review.yml", "Regen gate")
        script = step["run"]
        assert step["env"]["REVIEW_SKIPPED"] == "${{ steps.adapt.outputs.review_skipped }}"
        for line in (
            "[ -s /tmp/anyplot-adapt-new.json ] && ADAPT+=(--adapt-new /tmp/anyplot-adapt-new.json)",
            "[ -s /tmp/anyplot-adapt-prev.json ] && ADAPT+=(--adapt-prev /tmp/anyplot-adapt-prev.json)",
            '[ -s "$RUNNER_TEMP/adapt/pair.json" ] && ADAPT+=(--adapt-pair "$RUNNER_TEMP/adapt/pair.json")',
            '[ "$REVIEW_SKIPPED" = "true" ] && ADAPT+=(--review-skipped)',
            '"${FLAGS[@]}" "${ADAPT[@]}"; then',
        ):
            assert line in script, line

    def test_the_pair_artifact_carries_the_adapt_folder(self):
        script = _step("impl-review.yml", "Stage regen pair")["run"]
        assert 'cp -r "$RUNNER_TEMP/adapt/." "$DIR/adapt/"' in script
        assert 'rm -rf "$DIR/adapt/prev-src"' in script
        assert 'cp /tmp/anyplot-adapt-new.json /tmp/anyplot-adapt-prev.json "$DIR/adapt/"' in script

    def test_the_carried_label_comes_after_the_gate_and_before_any_verdict(self):
        names = [s.get("name") for s in _steps("impl-review.yml")]
        assert names.index("Regen gate") < names.index("Upload regen pair") < names.index(CARRIED_LABEL)
        assert names.index(CARRIED_LABEL) + 1 == names.index(EARLY)
        step = _step("impl-review.yml", CARRIED_LABEL)
        assert step["if"] == f"{REVIEW_FREE} && steps.gate.outputs.verdict == 'merge'"
        assert step["env"]["SCORE"] == "${{ steps.regen_ctx.outputs.prev_stored }}"
        assert "continue-on-error" not in step

    def test_the_metadata_step_carries_on_the_review_free_path(self):
        env = _step("impl-review.yml", METADATA)["env"]
        assert env["REVIEW_CARRIED"] == f"${{{{ {REVIEW_FREE} }}}}"
        assert env["CARRY_FROM"] == "/tmp/anyplot-prev-metadata.yaml"
        assert (
            env["SCORE"]
            == f"${{{{ {REVIEW_FREE} && steps.regen_ctx.outputs.prev_stored || steps.score.outputs.score }}}}"
        )
        assert (
            'git show "origin/main:${META_FILE}" > /tmp/anyplot-prev-metadata.yaml'
            in _step("impl-review.yml", "Regen context")["run"]
        )


class TestCarriedQualityLabel:
    ENV = {"PR_NUM": "7", "SCORE": "94"}

    def _label(self, tmp_path: Path, **env: str):
        return _run(_step("impl-review.yml", CARRIED_LABEL)["run"], tmp_path, tmp_path, **{**self.ENV, **env})

    def test_the_stored_score_labels_the_pr(self, tmp_path):
        result, calls = self._label(tmp_path)
        assert result.returncode == 0, result.stdout + result.stderr
        create = [
            "label",
            "create",
            "quality:94",
            "--force",
            "--color",
            "0e8a16",
            "--description",
            "Quality score 94/100",
        ]
        assert create in calls
        assert _calls(calls, "pr", "edit") == [["pr", "edit", "7", "--add-label", "quality:94"]]

    def test_an_older_quality_label_goes_first(self, tmp_path):
        # The fake gh prints $GH_LABELS for the `--jq` read, which selects the other quality:* labels.
        result, calls = self._label(tmp_path, GH_LABELS="quality:88")
        assert result.returncode == 0, result.stdout + result.stderr
        assert _calls(calls, "pr", "edit") == [
            ["pr", "edit", "7", "--remove-label", "quality:88"],
            ["pr", "edit", "7", "--add-label", "quality:94"],
        ]

    @pytest.mark.parametrize("score", ["", "n/a", "0", "101"])
    def test_no_score_stops_before_any_verdict(self, tmp_path, score):
        result, calls = self._label(tmp_path, SCORE=score)
        assert result.returncode == 1
        assert not calls

    def test_a_lost_label_fails_the_step(self, tmp_path):
        result, calls = self._label(tmp_path, GH_FAIL_ADD_LABEL="quality:94")
        assert result.returncode == 1
        assert calls.count(["pr", "edit", "7", "--add-label", "quality:94"]) == 4


class TestAdaptCountLabel:
    """regen:adapt between regen:improved and ai-approved, best effort."""

    ENV = {"PR_NUM": "7", "SCORE": "", "ATTEMPT_COUNT": "0", "IS_REGEN": "true", "GATE_VERDICT": "merge"}

    def _early(self, tmp_path: Path, **env: str):
        defaults = {"GITHUB_OUTPUT": str(tmp_path / "github_output"), "RUNNER_TEMP": str(tmp_path / "runner")}
        return _run(_step("impl-review.yml", EARLY)["run"], tmp_path, tmp_path, **{**self.ENV, **defaults, **env})

    def test_a_counted_merge_is_labelled_in_order(self, tmp_path):
        result, calls = self._early(tmp_path, ADAPT_COUNTED="true")
        assert result.returncode == 0, result.stdout + result.stderr
        assert [c[-1] for c in _calls(calls, "pr", "edit")] == ["regen:improved", "regen:adapt", "ai-approved"]
        assert any(c[:4] == ["label", "create", "regen:adapt", "--force"] for c in calls)

    @pytest.mark.parametrize("counted", ["false", ""])
    def test_an_uncounted_merge_is_not(self, tmp_path, counted):
        _, calls = self._early(tmp_path, ADAPT_COUNTED=counted)
        assert [c[-1] for c in _calls(calls, "pr", "edit")] == ["regen:improved", "ai-approved"]

    def test_a_lost_count_label_never_holds_up_the_merge(self, tmp_path):
        result, calls = self._early(tmp_path, ADAPT_COUNTED="true", GH_FAIL_ADD_LABEL="regen:adapt")
        assert result.returncode == 0, result.stdout + result.stderr
        assert calls.count(["pr", "edit", "7", "--add-label", "regen:adapt"]) == 3
        assert ["pr", "edit", "7", "--add-label", "ai-approved"] in calls
        assert "::error::" not in result.stdout

    def test_a_kept_regeneration_gets_no_count(self, tmp_path):
        _, calls = self._early(tmp_path, ADAPT_COUNTED="true", GATE_VERDICT="keep")
        assert [c[-1] for c in _calls(calls, "pr", "edit")] == ["regen:kept"]

    def test_the_label_comes_from_the_gate(self):
        assert _step("impl-review.yml", EARLY)["env"]["ADAPT_COUNTED"] == "${{ steps.gate.outputs.adapt_counted }}"
        assert _step("impl-review.yml", VERDICT)["env"]["ADAPT_COUNTED"] == "${{ steps.gate.outputs.adapt_counted }}"


def _writer() -> str:
    run = _step("impl-review.yml", METADATA)["run"]
    return run.split("cat > /tmp/update_metadata.py << 'EOF'\n", 1)[1].split("\nEOF\n", 1)[0]


PREV_REVIEW = {
    "strengths": ["clean"],
    "weaknesses": ["Suggestion: larger legend"],
    "image_description": "Light render: ...\n\nDark render: ...",
    "criteria_checklist": {"visual_quality": {"score": 30, "max": 30, "items": []}},
    "verdict": "APPROVED",
    "model": "claude-opus-5-5",
    "criteria_version": "qc-e1373b1495.aqr-15492a059e.sg-7006008fc6.lib-e97ebfa5c3",
    "rendered_at": "2026-10-01T01:58:44Z",
}
PREV_META = {
    "library": LIB,
    "created": "2026-05-28T00:00:00Z",
    "updated": "2026-10-01T02:00:00Z",
    "library_version": "3.10.9",
    "language_version": "3.13.14",
    "generated_by": "claude-sonnet",
    "workflow_run": 100,
    "quality_score": 94,
    "review": PREV_REVIEW,
    "impl_tags": {"techniques": ["annotations"], "dependencies": []},
}
# What impl-generate wrote on the PR branch: measured versions, no score, an empty review.
BRANCH_META = {
    "library": LIB,
    "language": "python",
    "specification_id": SPEC_ID,
    "created": "2026-05-28T00:00:00Z",
    "updated": "2026-10-24T09:00:00Z",
    "generated_by": "claude-sonnet",
    "workflow_run": 200,
    "issue": 42,
    "language_version": "3.14.9",
    "library_version": "3.11.1",
    "preview_url_light": "https://storage.googleapis.com/anyplot-images/plots/bar-grouped/python/matplotlib/plot-light.png",
    "preview_url_dark": "https://storage.googleapis.com/anyplot-images/plots/bar-grouped/python/matplotlib/plot-dark.png",
    "preview_html_light": None,
    "preview_html_dark": None,
    "quality_score": None,
    "review": {"strengths": [], "weaknesses": []},
}


class TestCarriedMetadata:
    """Contract section 7: what the merged metadata holds after a review-free merge."""

    def _write(self, tmp_path: Path, score: str, env: dict[str, str], prev: dict[str, Any] = PREV_META):
        (tmp_path / "update_metadata.py").write_text(_writer(), encoding="utf-8")
        meta = tmp_path / "meta.yaml"
        meta.write_text(yaml.safe_dump(BRANCH_META, sort_keys=False), encoding="utf-8")
        carry = tmp_path / "prev-metadata.yaml"
        carry.write_text(yaml.safe_dump(prev, sort_keys=False), encoding="utf-8")
        # A stray review file never reaches a carried review.
        (tmp_path / "review_strengths.json").write_text('["planted"]', encoding="utf-8")
        base = {
            k: v
            for k, v in os.environ.items()
            if k not in {"REVIEW_MODEL", "CRITERIA_VERSION", "RENDERED_AT", "REVIEW_APPROVED", "REVIEW_CARRIED"}
        }
        result = subprocess.run(
            [sys.executable, "update_metadata.py", str(meta), score, "2026-10-24T09:30:11Z"],
            cwd=tmp_path,
            env={**base, "CARRY_FROM": str(carry), **env},
            capture_output=True,
            text=True,
        )
        data = yaml.safe_load(meta.read_text(encoding="utf-8"))
        return result, data, meta.read_text(encoding="utf-8")

    def test_the_stored_review_carries_over_unchanged(self, tmp_path):
        env = {
            "REVIEW_CARRIED": "true",
            # This run's values never overwrite or pop the carried provenance.
            "REVIEW_APPROVED": "true",
            "REVIEW_MODEL": "",
            "CRITERIA_VERSION": "",
            "RENDERED_AT": "2026-10-24T09:01:00Z",
        }
        result, data, _ = self._write(tmp_path, "94", env)
        assert result.returncode == 0, result.stderr
        assert data["quality_score"] == 94
        assert data["review"] == {**PREV_REVIEW, "carried": True}
        assert data["impl_tags"] == PREV_META["impl_tags"]
        assert data["updated"] == "2026-10-24T09:30:11Z"
        for key in (
            "library_version",
            "language_version",
            "generated_by",
            "workflow_run",
            "created",
            "preview_url_light",
            "preview_url_dark",
            "preview_html_light",
            "preview_html_dark",
            "issue",
        ):
            assert data[key] == BRANCH_META[key], key

    def test_the_merged_file_reads_like_any_stored_review(self, tmp_path):
        """impl-merge merges the file as it is; sync_to_postgres and the next regen read it."""
        _, data, text = self._write(tmp_path, "94", {"REVIEW_CARRIED": "true"})
        assert "rendered_at: '2026-10-01T01:58:44Z'" in text
        assert isinstance(data["quality_score"], int) and data["quality_score"] > 0
        assert data["review"]["criteria_checklist"] and data["review"]["weaknesses"]

    @pytest.mark.parametrize(("score", "prev_score"), [("93", 94), ("94", None), ("94", "94"), ("0", 0), ("94", True)])
    def test_a_score_that_is_not_the_stored_one_fails(self, tmp_path, score, prev_score):
        result, data, _ = self._write(
            tmp_path, score, {"REVIEW_CARRIED": "true"}, prev={**PREV_META, "quality_score": prev_score}
        )
        assert result.returncode != 0
        assert "carried review:" in result.stderr
        assert data == BRANCH_META  # nothing written

    def test_a_predecessor_without_tags_or_review(self, tmp_path):
        prev = {k: v for k, v in PREV_META.items() if k not in ("impl_tags", "review")}
        result, data, _ = self._write(tmp_path, "94", {"REVIEW_CARRIED": "true"}, prev=prev)
        assert result.returncode == 0, result.stderr
        assert data["review"] == {"carried": True}
        assert "impl_tags" not in data

    @pytest.mark.parametrize("carried", ["false", "", "1"])
    def test_a_review_that_ran_is_never_carried(self, tmp_path, carried):
        (tmp_path / "update_metadata.py").write_text(_writer(), encoding="utf-8")
        meta = tmp_path / "meta.yaml"
        meta.write_text(yaml.safe_dump({**BRANCH_META, "review": {**PREV_REVIEW, "carried": True}}), encoding="utf-8")
        (tmp_path / "review_strengths.json").write_text('["new"]', encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "update_metadata.py", str(meta), "91", "2026-10-24T09:30:11Z"],
            cwd=tmp_path,
            env={**os.environ, "REVIEW_CARRIED": carried, "REVIEW_MODEL": "claude-opus-5-5"},
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        data = yaml.safe_load(meta.read_text(encoding="utf-8"))
        assert data["quality_score"] == 91
        assert data["review"]["strengths"] == ["new"]
        assert "carried" not in data["review"]

    def test_the_header_and_commit_follow_the_mode(self):
        script = _step("impl-review.yml", METADATA)["run"]
        # The header code writes "Quality: ${SCORE}/100" from the measured versions, as on every path.
        assert (
            "export IMPL_FILE LANGUAGE SPEC_ID TITLE LIBRARY LIBRARY_VERSION LANGUAGE_VERSION SCORE DATE_INFO" in script
        )
        assert 'git commit -m "chore(${LIBRARY}): carry the stored review over for ${SPEC_ID}"' in script


class TestVerdictStepReviewFree:
    ENV = {
        "PR_NUM": "7",
        "SPEC_ID": "spec-a",
        "LIBRARY": "plotly",
        "LANGUAGE": "python",
        "EXT": ".py",
        "SCORE": "",
        "ATTEMPT": "1",
        "ATTEMPT_COUNT": "0",
        "ISSUE_NUMBER": "",
        "REPOSITORY": "owner/repo",
        "RUN_ID": "1",
        "MODEL": "sonnet",
        "IS_REGEN": "true",
        "GATE_REASON": "adapt route",
        "PREV_STORED": "94",
        "MODEL_ID": "n/a",
        "REVIEW_SKIPPED": "true",
    }

    def _verdict(self, tmp_path: Path, **env: str):
        runner = tmp_path / "runner" / "regen-tools"
        runner.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TOOLS / "regen_gate.py", runner / "regen_gate.py")
        # The step's fixed /tmp/anyplot-* files, moved under this test's directory (parallel runs).
        script = _step("impl-review.yml", VERDICT)["run"].replace("/tmp/anyplot-", f"{tmp_path}/anyplot-")
        return _run(script, tmp_path, tmp_path, **{**self.ENV, "RUNNER_TEMP": str(tmp_path / "runner"), **env})

    def _comment(self, calls: list[list[str]]) -> str:
        (comment,) = _calls(calls, "pr", "comment")
        return Path(comment[comment.index("--body-file") + 1]).read_text(encoding="utf-8")

    def test_a_review_free_merge_says_no_review_ran(self, tmp_path):
        result, calls = self._verdict(tmp_path, GATE_VERDICT="merge", GATE_CODE="adapt_identity")
        assert result.returncode == 0, result.stdout + result.stderr
        body = self._comment(calls)
        assert "No review ran: the adapt route held." in body
        assert "The stored score (94) and its review carry over unchanged" in body
        assert "(score )" not in body
        assert ["workflow", "run", "impl-merge.yml", "-f", "pr_number=7"] in calls

    def test_a_reviewed_counted_merge_names_the_count(self, tmp_path):
        result, calls = self._verdict(
            tmp_path, GATE_VERDICT="merge", REVIEW_SKIPPED="", SCORE="92", ADAPT_COUNTED="true"
        )
        assert result.returncode == 0, result.stdout + result.stderr
        body = self._comment(calls)
        assert "compared this render (score 92)" in body
        assert "The adapt route held as well, so this PR is labelled `regen:adapt`" in body

    def test_a_review_free_keep_has_no_rescore(self, tmp_path):
        result, calls = self._verdict(tmp_path, GATE_VERDICT="keep", GATE_CODE="no_score", WB_STATUS="")
        assert result.returncode == 0, result.stdout + result.stderr
        body = self._comment(calls)
        assert "compared this render (no review: the adapt route skipped it)" in body
        assert "**Stored review:** unchanged (the gate has no re-score of the live implementation: no_score)." in body
        assert ["pr", "close", "7", "--delete-branch"] in calls


def test_every_regen_tool_the_workflow_runs_is_copied():
    """A tool missing from "Checkout PR code"'s copy only fails on a runner."""
    text = WORKFLOW.read_text(encoding="utf-8")
    copy = _step("impl-review.yml", "Checkout PR code")["run"]
    copied = set(re.findall(r"automation/scripts/(\w+\.py)", copy[: copy.index("git fetch origin")]))
    used = set(re.findall(r"\$\{?RUNNER_TEMP\}?/regen-tools/(\w+\.py)", text))
    for alias in re.findall(r'(\w+)="\$\{?RUNNER_TEMP\}?/regen-tools/?"', text):
        used |= set(re.findall(rf"\$\{{?{alias}\}}?/(\w+\.py)", text))
    assert {"adaptability_check.py", "adapt_record.py", "regen_gate.py", "regen_writeback.py"} <= used
    assert used <= copied, f"used but not copied: {sorted(used - copied)}"
