"""impl-review's "Write back the re-score (regen keep)" step, run for real.

The step script runs against a throwaway bare `origin` (its `main` holds the
pair's metadata and implementation) and a workspace clone detached at a PR
head, with a fake `gh` that records its calls and a no-op `sleep`. Every path
ends with exactly one `status` in the output file, and the workspace's branch
and HEAD are where they were: the verdict step imports core.constants from it.
The step's own `GIT_CONFIG_*` env applies, so no hook in the workspace runs.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from automation.scripts import regen_writeback as wb
from automation.scripts.regen_gate import CRITERIA


REPO_ROOT = Path(__file__).parent.parent.parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "impl-review.yml"
STEP = "Write back the re-score (regen keep)"
SPEC, LIB, KEPT = "count-basic", "ggplot2", "11955"
META, IMPL = "plots/count-basic/metadata/r/ggplot2.yaml", "plots/count-basic/implementations/r/ggplot2.R"
BRANCH = f"review-writeback/{SPEC}/{LIB}/{KEPT}"
PREV_CHECKLIST = {**CRITERIA, "VQ-02": 4, "DE-01": 5, "LM-02": 3}
CATEGORY_KEYS = {
    "VQ": "visual_quality",
    "DE": "design_excellence",
    "SC": "spec_compliance",
    "DQ": "data_quality",
    "CQ": "code_quality",
    "LM": "library_mastery",
}
METADATA = {
    "library": LIB,
    "specification_id": SPEC,
    "created": "2026-08-11T06:48:31Z",
    "updated": "2026-09-28T11:00:18Z",
    "quality_score": 87,
    "review": {
        "strengths": ["old"],
        "weaknesses": ["old"],
        "verdict": "APPROVED",
        "model": "claude-sonnet-5",
        "rendered_at": "2026-09-28T10:58:01Z",
    },
    "impl_tags": {"techniques": ["annotations"]},
}
HEADER = "#' anyplot.ai\n#' count-basic: Basic Count Plot\n#' Library: ggplot2 3.5.1 | R 4.4.1\n#' Quality: 87/100 | Updated: 2026-09-28\n\nlibrary(ggplot2)\n"


def _checklist_json(scores: dict[str, int]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for cid, score in scores.items():
        cat = out.setdefault(CATEGORY_KEYS[cid[:2]], {"score": 0, "max": 0, "items": []})
        cat["items"].append(
            {"id": cid, "name": cid, "score": score, "max": CRITERIA[cid], "passed": True, "comment": ""}
        )
        cat["score"] += score
        cat["max"] += CRITERIA[cid]
    return out


PREV_REVIEW = {
    "image_description": "Light render (plot-light.png): …\n\nDark render (plot-dark.png): …",
    "criteria_checklist": _checklist_json(PREV_CHECKLIST),
    "strengths": ["Counts from the stat engine"],
    "weaknesses": ["VQ-02 (light): a label overlaps a bar → clear it. Likely cause: vjust.", "Suggestion: a"],
    "verdict": "REJECTED",
}
REGEN = {"prev_rescored": 80, "prev_checklist": PREV_CHECKLIST}

FAKE_GH = """#!/bin/sh
printf '%s\\n' "$*" >> "$FAKE_GH_LOG"
case "$1 $2" in
  "pr list")
    case "$*" in
      *--head*) printf '%s' "${FAKE_GH_EXISTING:-}" ;;
      *) printf '%s' "${FAKE_GH_OPEN:-}" ;;
    esac
    exit "${FAKE_GH_LIST_RC:-0}" ;;
  "pr create")
    [ "${FAKE_GH_CREATE_RC:-0}" = 0 ] || exit "$FAKE_GH_CREATE_RC"
    echo "https://github.com/o/r/pull/12001" ;;
  "workflow run") exit "${FAKE_GH_DISPATCH_RC:-0}" ;;
  *) exit 0 ;;
esac
"""


def _env(tmp_path: Path, **extra: str) -> dict[str, str]:
    """No user or system git config (signing, hooks) and no inherited GIT_* state."""
    empty = tmp_path / "gitconfig"
    empty.touch()
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1", **extra)
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


class Setup:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.origin = tmp_path / "origin.git"
        self.ws = tmp_path / "workspace"
        seed = tmp_path / "seed"
        seed.mkdir()
        _git(tmp_path, seed, "init", "-q", "-b", "main")
        self.write(seed, META, yaml.safe_dump(METADATA, sort_keys=False))
        self.write(seed, IMPL, HEADER)
        self.write(seed, "core/constants.py", "SUPPORTED_LIBRARIES = []\n")
        _git(tmp_path, seed, "add", "-A")
        _git(tmp_path, seed, "commit", "-q", "-m", "main")
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(self.origin)], check=True, env=_env(tmp_path))
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.ws)], check=True, env=_env(tmp_path))
        # The PR head the review ran on: detached, with a regenerated file.
        _git(tmp_path, self.ws, "checkout", "-q", "--detach")
        self.write(self.ws, IMPL, HEADER.replace("87/100", "pending") + "# regenerated\n")
        _git(tmp_path, self.ws, "commit", "-q", "-am", "regenerated")
        self.head = _git(tmp_path, self.ws, "rev-parse", "HEAD")
        (self.ws / "review_prev.json").write_text(json.dumps(PREV_REVIEW), encoding="utf-8")
        (self.ws / "review_regen.json").write_text(json.dumps(REGEN), encoding="utf-8")
        # The workflow-ref copy of the helpers.
        self.runner_temp = tmp_path / "runner"
        tools = self.runner_temp / "regen-tools"
        tools.mkdir(parents=True)
        for name in ("regen_writeback.py", "regen_gate.py"):
            shutil.copy(REPO_ROOT / "automation" / "scripts" / name, tools / name)
        self.bin = tmp_path / "bin"
        self.bin.mkdir()
        (self.bin / "gh").write_text(FAKE_GH, encoding="utf-8")
        (self.bin / "sleep").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        for name in ("gh", "sleep"):
            (self.bin / name).chmod(0o755)
        self.log = tmp_path / "gh.log"
        self.output = tmp_path / "github_output"

    @staticmethod
    def write(repo: Path, path: str, text: str) -> None:
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text, encoding="utf-8")

    def blob(self, path: str) -> str:
        return _git(self.tmp, self.origin, "rev-parse", f"main:{path}")

    def commit_on_main(self, path: str, text: str, ref: str = "main") -> None:
        other = self.tmp / f"other-{len(list(self.tmp.glob('other-*')))}"
        subprocess.run(["git", "clone", "-q", str(self.origin), str(other)], check=True, env=_env(self.tmp))
        self.write(other, path, text)
        _git(self.tmp, other, "add", "-A")
        _git(self.tmp, other, "commit", "-q", "-m", f"{ref} moves")
        _git(self.tmp, other, "push", "-q", "origin", f"HEAD:refs/heads/{ref}")

    def run(self, **env: str) -> subprocess.CompletedProcess[str]:
        run = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        step = next(s for job in run["jobs"].values() for s in job["steps"] if s.get("name") == STEP)
        script = step["run"].replace("/tmp/", f"{self.tmp}/")
        (self.tmp / "step.sh").write_text(script, encoding="utf-8")
        self.output.unlink(missing_ok=True)
        values = {
            # The step's own git settings (hooks off), as Actions sets them.
            **{k: str(v) for k, v in step["env"].items() if k.startswith("GIT_CONFIG_")},
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "GITHUB_OUTPUT": str(self.output),
            "RUNNER_TEMP": str(self.runner_temp),
            "FAKE_GH_LOG": str(self.log),
            "GH_TOKEN": "unused",
            "PR_NUM": KEPT,
            "SPEC_ID": SPEC,
            "LIBRARY": LIB,
            "LANGUAGE": "r",
            "EXT": ".R",
            "GATE_CODE": "regression",
            "PREV_RESCORED": "80",
            "PREV_STORED": "87",
            "PREV_META_BLOB": self.blob(META),
            "PREV_IMPL_BLOB": self.blob(IMPL),
            "REVIEW_MODEL": "claude-opus-5",
            "CRITERIA_VERSION": "qc-a.aqr-b.sg-c.lib-d",
            "REPOSITORY": "o/r",
            "RUN_ID": "1",
            "WORKFLOW_REF": "main",
            **env,
        }
        # As Actions runs a `run:` step.
        return subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", str(self.tmp / "step.sh")],
            cwd=self.ws,
            env=_env(self.tmp, **values),
            capture_output=True,
            text=True,
        )

    def outputs(self) -> list[tuple[str, str]]:
        text = self.output.read_text(encoding="utf-8") if self.output.exists() else ""
        pairs: list[tuple[str, str]] = []
        for line in text.splitlines():
            key, sep, value = line.partition("=")
            if sep:
                pairs.append((key, value))
        return pairs

    def status(self) -> str:
        statuses = [v for k, v in self.outputs() if k == "status"]
        assert len(statuses) == 1, statuses
        return statuses[0]

    def gh_calls(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def remote_branch(self) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.origin), "rev-parse", "-q", "--verify", f"refs/heads/{BRANCH}"],
            capture_output=True,
            text=True,
            env=_env(self.tmp),
        )
        return result.stdout.strip()

    def assert_workspace_untouched(self) -> None:
        assert _git(self.tmp, self.ws, "rev-parse", "HEAD") == self.head
        assert _git(self.tmp, self.ws, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"  # still detached
        assert _git(self.tmp, self.ws, "status", "--porcelain", "--untracked-files=no") == ""
        assert len(_git(self.tmp, self.ws, "worktree", "list").splitlines()) == 1


@pytest.fixture
def setup(tmp_path: Path) -> Setup:
    return Setup(tmp_path)


class TestWritebackStep:
    def test_opened(self, setup):
        result = setup.run()
        assert result.returncode == 0, result.stdout + result.stderr
        assert setup.status() == "opened"
        assert dict(setup.outputs())["pr"] == "12001"
        assert dict(setup.outputs())["score"] == "80"
        # One commit on top of main with exactly the two files.
        head = setup.remote_branch()
        assert head
        assert _git(setup.tmp, setup.origin, "rev-parse", f"{head}^") == _git(
            setup.tmp, setup.origin, "rev-parse", "main"
        )
        assert _git(setup.tmp, setup.origin, "diff", "--name-only", "main", head).splitlines() == [IMPL, META]
        assert _git(setup.tmp, setup.origin, "log", "-1", "--format=%s%n%an", head).splitlines() == [
            f"chore({LIB}): store re-score 80 for {SPEC} (kept regen #{KEPT})",
            "github-actions[bot]",
        ]
        assert wb.verify_diff(setup.origin, "main", head, SPEC, LIB) == []
        stored = yaml.safe_load(_git(setup.tmp, setup.origin, "show", f"{head}:{META}"))
        assert stored["quality_score"] == 80
        assert stored["review"]["model"] == "claude-opus-5"
        assert stored["review"]["weaknesses"] == PREV_REVIEW["weaknesses"]
        assert stored["updated"] == METADATA["updated"]
        assert stored["review"]["rendered_at"] == "2026-09-28T10:58:01Z"
        assert "#' Quality: 80/100 | Updated: 2026-09-28" in _git(setup.tmp, setup.origin, "show", f"{head}:{IMPL}")
        calls = setup.gh_calls()
        create = next(c for c in calls if c.startswith("pr create"))
        assert f"--base main --head {BRANCH} --label review-writeback" in create
        assert "workflow run impl-merge.yml --ref main -f pr_number=12001" in calls
        assert not any(c.startswith("pr close") for c in calls)
        setup.assert_workspace_untouched()

    @pytest.mark.parametrize("hooks_off", [True, False])
    def test_no_workspace_hook_runs(self, setup, hooks_off):
        """Hooks the session could plant in the workspace's .git never run; the
        control run without the step's GIT_CONFIG_* shows they would."""
        hooks = setup.ws / ".git" / "hooks"
        names = ("post-checkout", "pre-commit", "commit-msg", "post-commit", "pre-push", "reference-transaction")
        for name in names:
            (hooks / name).write_text(f'#!/bin/sh\necho {name} >> "{setup.tmp}/hooks-ran"\nexit 0\n', encoding="utf-8")
            (hooks / name).chmod(0o755)
        result = setup.run() if hooks_off else setup.run(GIT_CONFIG_COUNT="0")
        assert result.returncode == 0, result.stdout + result.stderr
        assert setup.status() == "opened"
        ran = setup.tmp / "hooks-ran"
        if hooks_off:
            assert not ran.exists(), ran.read_text(encoding="utf-8")
        else:
            assert {"post-checkout", "pre-commit", "pre-push"} <= set(ran.read_text(encoding="utf-8").split())

    def test_a_branch_smoke_dispatches_on_its_own_ref(self, setup):
        assert setup.run(WORKFLOW_REF="feat/review-writeback").returncode == 0
        assert "workflow run impl-merge.yml --ref feat/review-writeback -f pr_number=12001" in setup.gh_calls()

    @pytest.mark.parametrize("value", ["n/a", "", "8O"])
    def test_no_rescore(self, setup, value):
        result = setup.run(PREV_RESCORED=value, GATE_CODE="canvas_failed")
        assert result.returncode == 0, result.stderr
        assert setup.status() == "no_rescore"
        assert "reason=gate code canvas_failed" in result.stdout
        assert setup.gh_calls() == []
        assert setup.remote_branch() == ""
        setup.assert_workspace_untouched()

    def test_invalid(self, setup):
        bad = {**PREV_REVIEW, "criteria_checklist": _checklist_json({**PREV_CHECKLIST, "VQ-02": 5})}
        (setup.ws / "review_prev.json").write_text(json.dumps(bad), encoding="utf-8")
        result = setup.run()
        assert result.returncode == 0, result.stderr
        assert setup.status() == "invalid"
        assert (
            "::warning::review_prev.json: criteria_checklist differs from prev_checklist at VQ-02 5 vs 4"
            in result.stdout
        )
        assert setup.gh_calls() == []
        setup.assert_workspace_untouched()

    def test_missing_review_prev_is_invalid(self, setup):
        (setup.ws / "review_prev.json").unlink()
        assert setup.run().returncode == 0
        assert setup.status() == "invalid"

    @pytest.mark.parametrize("path", [META, IMPL])
    def test_stale_when_main_changed_a_pair_file(self, setup, path):
        before = {"PREV_META_BLOB": setup.blob(META), "PREV_IMPL_BLOB": setup.blob(IMPL)}
        setup.commit_on_main(path, (HEADER if path == IMPL else yaml.safe_dump(METADATA)) + "# moved\n")
        result = setup.run(**before)
        assert result.returncode == 0, result.stderr
        assert setup.status() == "stale"
        assert not any(c.startswith("pr create") for c in setup.gh_calls())
        assert setup.remote_branch() == ""
        setup.assert_workspace_untouched()

    def test_stale_without_a_recorded_blob(self, setup):
        assert setup.run(PREV_META_BLOB="").returncode == 0
        assert setup.status() == "stale"

    def test_unchanged(self, setup):
        # main already stores exactly this re-score.
        meta = setup.ws / "applied.yaml"
        meta.write_text(yaml.safe_dump(METADATA, sort_keys=False), encoding="utf-8")
        impl = setup.ws / "applied.R"
        impl.write_text(HEADER, encoding="utf-8")
        args = ["apply", "--metadata", str(meta), "--prev-review", str(setup.ws / "review_prev.json"), "--score", "80"]
        assert (
            wb.main(
                [*args, "--model", "claude-opus-5", "--criteria-version", "qc-a.aqr-b.sg-c.lib-d", "--impl", str(impl)]
            )
            == 0
        )
        setup.commit_on_main(META, meta.read_text(encoding="utf-8"))
        setup.commit_on_main(IMPL, impl.read_text(encoding="utf-8"))
        meta.unlink()
        impl.unlink()
        result = setup.run()
        assert result.returncode == 0, result.stderr
        assert setup.status() == "unchanged"
        assert not any(c.startswith("pr create") for c in setup.gh_calls())
        assert setup.remote_branch() == ""
        setup.assert_workspace_untouched()

    def test_a_failed_dispatch_closes_the_pr(self, setup):
        result = setup.run(FAKE_GH_DISPATCH_RC="1")
        assert result.returncode == 0, result.stderr
        assert setup.status() == "failed"
        assert "pr" not in dict(setup.outputs())
        close = [c for c in setup.gh_calls() if c.startswith("pr close 12001")]
        assert len(close) == 1 and "--delete-branch" in close[0]
        setup.assert_workspace_untouched()

    def test_a_failed_create_deletes_the_pushed_branch(self, setup):
        result = setup.run(FAKE_GH_CREATE_RC="1")
        assert result.returncode == 0, result.stderr
        assert setup.status() == "failed"
        assert setup.remote_branch() == ""
        assert not any(c.startswith("workflow run") for c in setup.gh_calls())

    def test_a_create_that_lost_its_response_is_found(self, setup):
        assert setup.run(FAKE_GH_CREATE_RC="1", FAKE_GH_EXISTING="12002").returncode == 0
        assert setup.status() == "opened"
        assert "workflow run impl-merge.yml --ref main -f pr_number=12002" in setup.gh_calls()

    def test_a_leftover_branch_is_deleted_before_the_push(self, setup):
        """A rescue re-run of the same kept PR reuses the branch name; a push onto it would be refused."""
        setup.commit_on_main(META, yaml.safe_dump({**METADATA, "quality_score": 70}), ref=BRANCH)
        leftover = setup.remote_branch()
        assert leftover
        result = setup.run()
        assert result.returncode == 0, result.stdout + result.stderr
        assert setup.status() == "opened"
        head = setup.remote_branch()
        assert head != leftover
        assert _git(setup.tmp, setup.origin, "rev-parse", f"{head}^") == _git(
            setup.tmp, setup.origin, "rev-parse", "main"
        )

    def test_an_open_write_back_of_the_pair_is_superseded(self, setup):
        result = setup.run(FAKE_GH_OPEN="11990\n")
        assert result.returncode == 0, result.stderr
        assert setup.status() == "opened"
        close = [c for c in setup.gh_calls() if c.startswith("pr close 11990")]
        assert len(close) == 1 and "--delete-branch" in close[0]
        listing = next(c for c in setup.gh_calls() if c.startswith("pr list --state open --label review-writeback"))
        assert f'startswith("review-writeback/{SPEC}/{LIB}/")' in listing

    def test_a_failed_listing_is_failed(self, setup):
        assert setup.run(FAKE_GH_LIST_RC="1").returncode == 0
        assert setup.status() == "failed"
        assert setup.remote_branch() == ""

    def test_an_unexpected_error_still_writes_failed(self, setup):
        """apply cannot parse main's metadata: the step fails, and its status says so."""
        setup.commit_on_main(META, "library: [unclosed\n")
        result = setup.run(PREV_META_BLOB=setup.blob(META), PREV_IMPL_BLOB=setup.blob(IMPL))
        assert result.returncode != 0
        assert setup.status() == "failed"
        assert setup.remote_branch() == ""
        setup.assert_workspace_untouched()
