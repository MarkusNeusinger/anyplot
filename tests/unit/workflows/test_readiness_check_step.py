"""The readiness check in impl-review.yml and its way into the regen gate (P2b).

"Readiness check" reads the staged `adapt/readiness.json` against the
implementation at the PR head and the one on origin/main
(automation/scripts/readiness_record.py, the workflow-ref copy) and leaves its
verdict in `$RUNNER_TEMP/readiness-verdict.json`. "Regen gate" hands that file
to `regen_gate.py decide --readiness`, where a regression keeps the live
implementation. The step never fails the job and leaves no copy of either
source behind (the predecessor's header holds the stored score).

The step script runs here under `bash -e` and `bash -eo pipefail` against the
scratch origin of test_render_hash_steps, whose main holds the file as
generated and whose PR head holds it with the review's header.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

import pytest

from automation.scripts import readiness_scan, regen_gate
from automation.scripts.readiness_record import code_sha256
from tests.unit.automation.scripts.test_regen_gate import NEW_CHECKLIST, _checklist_json, _regen
from tests.unit.workflows.test_pipeline_retry_gaps import _step, _steps
from tests.unit.workflows.test_render_hash_steps import CODE, IMPL, LIB, SHELL_IDS, SHELLS, SPEC, TOOLS, Repo


STEP = "Readiness check"
ADAPT = "Adaptability check (record-only)"
KEY = "security:banned-attribute"
MAIN = CODE.format(score="pending", x=1)
HEAD = CODE.format(score="72/100", x=1)  # the same code under the review's header: one hash


def _repo(tmp_path) -> Repo:
    repo = Repo(tmp_path)
    tools = repo.runner / "regen-tools"
    tools.mkdir()
    shutil.copy(TOOLS / "readiness_record.py", tools / "readiness_record.py")  # a single file: it imports no sibling
    repo.git("fetch", "-q", "origin")  # impl-review's checkout has origin/main
    return repo


def _side(status: str, refusals: list[str] | None = None) -> dict:
    return {"status": status, "refusals": refusals or [], "spec_refused": False, "coupled": [], "findings": {}}


def _stage(repo: Repo, *, new: str = HEAD, prev: str | None = MAIN, **overrides: Any) -> None:
    """What the adaptability step downloaded from staging: the scanner's record of `new` against `prev`."""
    record = {
        "version": 2,
        "spec_id": SPEC,
        "library": LIB,
        "language": "python",
        "new_sha256": code_sha256(new),
        "prev_sha256": None if prev is None else code_sha256(prev),
        "verdict": "regression",
        "new": _side("blocked", [KEY]),
        "prev": None if prev is None else _side("coupled"),
        "added": [KEY],
        "removed": [],
        **overrides,
    }
    (repo.runner / "adapt").mkdir(exist_ok=True)
    (repo.runner / "adapt" / "readiness.json").write_text(json.dumps(record), encoding="utf-8")


def _run(repo: Repo, shell: list[str], **env: str) -> subprocess.CompletedProcess[str]:
    script = str(_step("impl-review.yml", STEP)["run"])
    return repo.run(script, shell, **{"HEAD_SHA": repo.git("rev-parse", "HEAD"), **env})


def _verdict(repo: Repo) -> dict | None:
    path = repo.runner / "readiness-verdict.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestReadinessCheckStep:
    def test_a_regression_is_read_against_the_head_and_main(self, tmp_path, shell):
        repo = _repo(tmp_path)
        _stage(repo)
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (
            f"::warning::readiness_check spec={SPEC} lib={LIB} status=regression new=blocked prev=coupled "
            f"added={KEY} removed=none"
        ) in result.stdout
        assert repo.read("summary") == f"**Readiness check:** regression: {KEY} (new blocked, predecessor coupled)\n"
        assert _verdict(repo) == {
            "version": 1,
            "status": "regression",
            "new": "blocked",
            "prev": "coupled",
            "added": [KEY],
            "removed": [],
        }

    def test_the_head_is_read_not_the_workspace(self, tmp_path, shell):
        """`Hide the previous review` rewrites the workspace copy later; an edit there never makes a record stale."""
        repo = _repo(tmp_path)
        _stage(repo)
        (repo.ws / IMPL).write_text(CODE.format(score="pending", x=99), encoding="utf-8")
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _verdict(repo)["status"] == "regression"

    def test_the_reviews_header_commit_keeps_the_record(self, tmp_path, shell):
        """A re-review reads the head after impl-review stored its review in the header: same code, same record."""
        repo = _repo(tmp_path)
        _stage(repo)
        header = '""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nLibrary: matplotlib 3.12.1 | Python 3.14.9\n'
        repo.commit({IMPL: header + 'Quality: 91/100 | Updated: 2026-11-15\n"""\n\nx = 1\n'}, "chore: store the review")
        repo.push()
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert _verdict(repo)["status"] == "regression"

    def test_a_push_after_the_scan_makes_the_record_stale(self, tmp_path, shell):
        repo = _repo(tmp_path)
        _stage(repo)
        repo.commit({IMPL: CODE.format(score="72/100", x=2)}, "fix: repair")
        repo.push()
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "status=stale new=blocked prev=coupled added=none removed=none why=head" in result.stdout
        assert _verdict(repo)["status"] == "stale" and _verdict(repo)["added"] == []

    def test_no_staged_record_is_missing(self, tmp_path, shell):
        repo = _repo(tmp_path)
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::notice::readiness_check" in result.stdout and "status=missing" in result.stdout
        assert _verdict(repo)["status"] == "missing"

    def test_a_first_generation_has_no_predecessor(self, tmp_path, shell):
        repo = _repo(tmp_path)
        other = "plots/line-basic/implementations/python/matplotlib.py"
        source = CODE.format(score="pending", x=3)
        repo.commit({other: source}, "feat: implement line-basic")
        repo.push()
        _stage(repo, new=source, prev=None, spec_id="line-basic")
        result = _run(repo, shell, SPEC_ID="line-basic")
        assert result.returncode == 0, result.stdout + result.stderr
        assert repo.read("summary") == "**Readiness check:** first generation (new blocked)\n"
        assert _verdict(repo)["status"] == "first_generation"

    def test_a_verdict_of_an_earlier_run_never_stands_in(self, tmp_path, shell):
        """The reader is gone (a failed copy): the old verdict goes, and the gate then decides without one."""
        repo = _repo(tmp_path)
        _stage(repo)
        (repo.runner / "readiness-verdict.json").write_text('{"status": "none"}', encoding="utf-8")
        (repo.runner / "regen-tools" / "readiness_record.py").unlink()
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::readiness check did not run; the regen gate decides without it" in result.stdout
        assert _verdict(repo) is None

    def test_no_copy_of_either_source_is_left_behind(self, tmp_path, shell):
        repo = _repo(tmp_path)
        _stage(repo)
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert sorted(p.name for p in repo.runner.iterdir()) == ["adapt", "readiness-verdict.json", "regen-tools"]


# --- wiring ------------------------------------------------------------------------------------


def test_the_step_never_gates_by_itself_and_follows_the_download_of_the_adapt_folder():
    names = [s.get("name") for s in _steps("impl-review.yml")]
    step = _step("impl-review.yml", STEP)
    # The adaptability step clears $RUNNER_TEMP/adapt and downloads staging's adapt/ folder into it.
    assert names[names.index(ADAPT) + 1] == STEP
    assert 'SRC="gs://anyplot-images/staging/${SPEC_ID}/${LANGUAGE}/${LIBRARY}/adapt/*"' in str(
        _step("impl-review.yml", ADAPT)["run"]
    )
    assert names.index(STEP) < names.index("Hide the previous review") < names.index("Run AI Quality Review")
    assert step["if"] == "steps.lang.outputs.language == 'python'"  # like the scan
    assert step["continue-on-error"] is True and step["timeout-minutes"] == 2
    assert "id" not in step  # its only way into a decision is the verdict file the gate reads
    assert "exit 1" not in str(step["run"])
    assert step["env"]["HEAD_SHA"] == "${{ steps.pr.outputs.head_sha }}"


def test_the_reviewer_cannot_read_the_verdict_or_the_sources():
    """`.claude/settings.json` allows the reviewer's Read tool on /tmp/* only."""
    script = str(_step("impl-review.yml", STEP)["run"])
    assert "/tmp/" not in script
    for name in ("readiness-head-source", "readiness-main-source", "readiness-verdict.json"):
        assert f'"$RUNNER_TEMP/{name}"' in script
    assert script.rstrip().endswith('rm -f "$NEW" "$PREV"')


def test_the_reader_is_the_workflow_refs_copy():
    """Copied before the checkout of the PR head, so the head cannot choose how its record is read."""
    checkout = str(_step("impl-review.yml", "Checkout PR code")["run"])
    assert checkout.index("automation/scripts/readiness_record.py") < checkout.index("git checkout")


def test_the_gate_gets_the_verdict_only_when_there_is_one():
    gate = str(_step("impl-review.yml", "Regen gate")["run"])
    flag = '[ -s "$RUNNER_TEMP/readiness-verdict.json" ] && ADAPT+=(--readiness "$RUNNER_TEMP/readiness-verdict.json")'
    assert flag in gate
    assert gate.index(flag) < gate.index('python3 "$RUNNER_TEMP/regen-tools/regen_gate.py" decide')
    names = [s.get("name") for s in _steps("impl-review.yml")]
    assert names.index(STEP) < names.index("Regen gate")


def test_the_pair_artifact_keeps_the_verdict():
    script = str(_step("impl-review.yml", "Stage regen pair")["run"])
    assert 'cp "$RUNNER_TEMP/readiness-verdict.json" "$DIR/adapt/" 2>/dev/null || true' in script


# --- scan, check and gate together ---------------------------------------------------------------


@pytest.mark.parametrize("shell", SHELLS[:1], ids=SHELL_IDS[:1])
def test_a_scanned_regression_reaches_the_gate_as_a_keep(tmp_path, shell, monkeypatch, capsys):
    """The real scanner's record of a regeneration, read by the step, turns the gate's merge into keep."""
    repo = _repo(tmp_path)
    regenerated = MAIN + "import socket\n"
    repo.commit({IMPL: regenerated}, "feat: regenerate")
    repo.push()
    (tmp_path / "new.py").write_text(regenerated, encoding="utf-8")
    (tmp_path / "prev.py").write_text(MAIN, encoding="utf-8")
    (repo.runner / "adapt").mkdir()
    arguments = ["scan", "--new", str(tmp_path / "new.py"), "--prev", str(tmp_path / "prev.py")]
    arguments += ["--spec-id", SPEC, "--library", LIB, "--out", str(repo.runner / "adapt" / "readiness.json")]
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert readiness_scan.main(arguments) == 0

    result = _run(repo, shell)
    assert result.returncode == 0, result.stdout + result.stderr
    verdict = _verdict(repo)
    assert verdict["status"] == "regression" and verdict["added"] == ["security:banned-import"]

    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "gate_output"))
    (tmp_path / "review_regen.json").write_text(json.dumps(_regen()), encoding="utf-8")
    (tmp_path / "review_checklist.json").write_text(json.dumps(_checklist_json(NEW_CHECKLIST)), encoding="utf-8")
    (tmp_path / "weaknesses.json").write_text(json.dumps([{"id": "W2", "text": "legend", "class": "defect"}]))
    decide = ["decide", "--spec-id", SPEC, "--library", LIB, "--score", "85", "--prev-stored", "80"]
    decide += ["--regen-json", str(tmp_path / "review_regen.json"), "--prev-renders", "available"]
    decide += ["--weaknesses-json", str(tmp_path / "weaknesses.json")]
    capsys.readouterr()
    assert regen_gate.main([*decide, "--readiness", str(repo.runner / "readiness-verdict.json")]) == 0
    assert " verdict=keep code=readiness_regression readiness=regression " in capsys.readouterr().out
    assert regen_gate.main(decide) == 0  # the same review without the check
    assert " verdict=merge code=merge " in capsys.readouterr().out
