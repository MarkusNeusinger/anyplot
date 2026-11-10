"""The render hash and the repair and generate gates (P2a) in impl-generate, impl-repair and impl-review.

The catalogue audit of 2026-11-08 traced 50 findings to renders that do not
come from the merged code: repairs that pushed renders without a code change,
a missing-PNG branch that exited 0, and a generation that checked out
origin/main under cached renders when the branch was never pushed. Now
impl-repair fails unless it pushed a change to the implementation and the
workspace holds that file, and fails without both renders; impl-generate fails
unless the pushed branch carries the file in the workspace. Both stage
`render.sha256`, and impl-review compares it with the file at the PR head,
warn-only. Both also record, warn-only, whether a render is older than the
implementation file.

The step scripts run here under `bash -e` (the Actions default) and
`bash -eo pipefail`, against a scratch origin whose workflow-ref commit carries
the real render_hash.py and regen_gate.py, with a stub `gsutil` over a
directory that stands in for the bucket and the stub `gh` of
test_pipeline_retry_gaps.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from automation.scripts.render_hash import read_hash, render_hash
from tests.unit.workflows.test_pipeline_retry_gaps import _calls, _run, _step, _steps


TOOLS = Path(__file__).resolve().parents[3] / "automation" / "scripts"
SPEC, LANG, LIB, EXT = "scatter-basic", "python", "matplotlib", ".py"
BRANCH = f"implementation/{SPEC}/{LIB}"
IMPL = f"plots/{SPEC}/implementations/{LANG}/{LIB}{EXT}"
STAGING = f"anyplot-images/staging/{SPEC}/{LANG}/{LIB}"
SHELLS = [["bash", "-e", "-c"], ["bash", "-eo", "pipefail", "-c"]]
SHELL_IDS = ["bash-e", "pipefail"]
CODE = '""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nQuality: {score} | Created: 2026-11-09\n"""\n\nx = {x}\n'

# A bucket in $FAKE_GCS. `cp gs://… LOCAL` fails like gsutil on a missing
# object, or with a 503 when GSUTIL_FAIL=1; `cp LOCAL gs://…/render.sha256`
# stores the file; every other `cp` (the renders) is accepted and dropped;
# `rm` deletes. Every call goes to $GSUTIL_LOG, one line each.
FAKE_GSUTIL = r"""#!/bin/bash
printf '%s\n' "$*" >> "$GSUTIL_LOG"
while [ $# -gt 0 ]; do
  case "$1" in -m) shift ;; -h) shift 2 ;; *) break ;; esac
done
cmd="$1"; shift
case "$cmd" in
  cp)
    dst="${@: -1}"
    if [[ "$1" == gs://* ]]; then
      [ "${GSUTIL_FAIL:-0}" = "1" ] && { echo "ServiceException: 503 Backend Error" >&2; exit 1; }
      [ -f "$FAKE_GCS/${1#gs://}" ] || { echo "CommandException: No URLs matched: $1" >&2; exit 1; }
      cp "$FAKE_GCS/${1#gs://}" "$dst"
    elif [[ "$dst" == gs://*render.sha256 ]]; then
      mkdir -p "$(dirname "$FAKE_GCS/${dst#gs://}")"
      cp "$1" "$FAKE_GCS/${dst#gs://}"
    fi ;;
  rm) rm -f "$FAKE_GCS/${1#gs://}" ;;
esac
exit 0
"""

# Logs every call like test_pipeline_retry_gaps' stub. `api` prints the file
# $GH_HEADS (the PR comments' first lines; fails with GH_FAIL_API=1), and
# `pr comment` exits $GH_COMMENT_RC.
FAKE_GH = r"""#!/bin/sh
for arg in "$@"; do printf '%s\n' "$arg"; done >> "$GH_LOG"
echo "--END--" >> "$GH_LOG"
case "$1 $2" in
  "api "*) [ "${GH_FAIL_API:-0}" = "1" ] && { echo "HTTP 502" >&2; exit 1; }
           [ -n "${GH_HEADS:-}" ] && cat "$GH_HEADS"
           exit 0 ;;
  "pr comment") exit "${GH_COMMENT_RC:-0}" ;;
esac
exit 0
"""


def _git_env(tmp: Path) -> dict[str, str]:
    """No user or system git config and no inherited GIT_* or GH_* state."""
    empty = tmp / "gitconfig"
    empty.touch()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_"))}
    env.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1")
    return env


class Repo:
    """A bare origin whose main is the workflow ref (with the real tools) and a workspace on the PR branch.

    The branch head (`start_sha`) holds the implementation with the header
    impl-review commits (`Quality: 72/100`); main holds it as generated.
    """

    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.origin, self.ws = tmp / "origin.git", tmp / "ws"
        self.gcs, self.runner, self.bin = tmp / "gcs", tmp / "runner", tmp / "bin"
        for path in (self.ws, self.gcs, self.runner, self.bin):
            path.mkdir()
        for name, body in (("gsutil", FAKE_GSUTIL), ("gh", FAKE_GH), ("sleep", "#!/bin/sh\n")):
            (self.bin / name).write_text(body, encoding="utf-8")
            (self.bin / name).chmod(0o755)
        self.git("init", "-q", "-b", "main")
        (self.ws / "automation" / "scripts").mkdir(parents=True)
        for name in ("render_hash.py", "regen_gate.py"):
            shutil.copy(TOOLS / name, self.ws / "automation" / "scripts" / name)
        self.commit({IMPL: CODE.format(score="pending", x=1)}, "workflow ref")
        self.workflow_sha = self.git("rev-parse", "HEAD")
        subprocess.run(["git", "clone", "-q", "--bare", str(self.ws), str(self.origin)], check=True, env=_git_env(tmp))
        self.git("remote", "add", "origin", str(self.origin))
        self.git("checkout", "-q", "-b", BRANCH)
        self.commit({IMPL: CODE.format(score="72/100", x=1)}, "chore: store the review")
        self.push()
        self.start_sha = self.git("rev-parse", "HEAD")

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.ws), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            capture_output=True,
            text=True,
            env=_git_env(self.tmp),
            check=True,
        )
        return result.stdout.strip()

    def commit(self, files: dict[str, str], message: str) -> None:
        for path, text in files.items():
            (self.ws / path).parent.mkdir(parents=True, exist_ok=True)
            (self.ws / path).write_text(text, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def push(self) -> None:
        self.git("push", "-q", "origin", f"HEAD:refs/heads/{BRANCH}")

    def run(self, script: str, shell: list[str], **env: str) -> subprocess.CompletedProcess[str]:
        assert "${{" not in script
        return subprocess.run(
            [*shell, script],
            cwd=self.ws,
            env={
                **_git_env(self.tmp),
                "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
                "FAKE_GCS": str(self.gcs),
                "GSUTIL_LOG": str(self.tmp / "gsutil.log"),
                "GH_LOG": str(self.tmp / "gh.log"),
                "GITHUB_OUTPUT": str(self.tmp / "output"),
                "GITHUB_STEP_SUMMARY": str(self.tmp / "summary"),
                "RUNNER_TEMP": str(self.runner),
                "GITHUB_SHA": self.workflow_sha,
                "SPEC_ID": SPEC,
                "LIBRARY": LIB,
                "LANGUAGE": LANG,
                "EXT": EXT,
                "BRANCH": BRANCH,
                "REPOSITORY": "o/r",
                **env,
            },
            capture_output=True,
            text=True,
        )

    def read(self, name: str) -> str:
        path = self.tmp / name
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def gh_calls(self) -> list[list[str]]:
        return [c.splitlines() for c in self.read("gh.log").split("--END--\n") if c]

    def staged_hash(self) -> str | None:
        path = self.gcs / STAGING / "render.sha256"
        return read_hash(path) if path.exists() else None


def _names(workflow: str) -> list[str]:
    return [str(s.get("name")) for s in _steps(workflow)]


# --- impl-repair: the push gate, the renders, the crash comment ---------------------------------


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestRepairPushGate:
    SCRIPT = str(_step("impl-repair.yml", "Check the repair's push")["run"])

    def _gate(self, repo: Repo, shell: list[str], **env: str) -> subprocess.CompletedProcess[str]:
        return repo.run(self.SCRIPT, shell, **{"START_SHA": repo.start_sha, **env})

    def test_a_pushed_change_in_a_clean_workspace_passes(self, tmp_path, shell):
        repo = Repo(tmp_path)
        repo.commit({IMPL: CODE.format(score="72/100", x=2)}, "fix: repair")
        repo.push()
        result = self._gate(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::notice::The repair pushed" in result.stdout and repo.read("output") == ""

    @pytest.mark.parametrize("other_commit", [False, True], ids=["nothing-pushed", "other-file-pushed"])
    def test_no_change_to_the_implementation_fails(self, tmp_path, shell, other_commit):
        repo = Repo(tmp_path)
        if other_commit:
            repo.commit({"notes.txt": "x\n"}, "chore: other file")
            repo.push()
        result = self._gate(repo, shell)
        assert result.returncode == 1
        assert repo.read("output") == (
            f"gate=the repair pushed no change to {IMPL} since {repo.start_sha[:7]}"
            " (a retry after a run whose push landed has to change the file again)\n"
        )

    def test_a_change_committed_but_not_pushed_fails(self, tmp_path, shell):
        repo = Repo(tmp_path)
        repo.commit({IMPL: CODE.format(score="72/100", x=2)}, "fix: repair")
        result = self._gate(repo, shell)
        assert result.returncode == 1 and "pushed no change" in repo.read("output")

    def test_a_workspace_that_differs_from_the_push_fails(self, tmp_path, shell):
        repo = Repo(tmp_path)
        repo.commit({IMPL: CODE.format(score="72/100", x=2)}, "fix: repair")
        repo.push()
        (repo.ws / IMPL).write_text(CODE.format(score="72/100", x=3), encoding="utf-8")
        result = self._gate(repo, shell)
        assert result.returncode == 1
        assert repo.read("output").startswith(f"gate={IMPL} in the workspace is not the pushed file")

    def test_an_unknown_start_fails_closed(self, tmp_path, shell):
        repo = Repo(tmp_path)
        repo.commit({IMPL: CODE.format(score="72/100", x=2)}, "fix: repair")
        repo.push()
        result = self._gate(repo, shell, START_SHA="")
        assert result.returncode == 1 and repo.read("output").startswith("gate=could not compare")


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
def test_repair_fails_without_both_renders(tmp_path, shell):
    repo = Repo(tmp_path)
    (repo.ws / IMPL).parent.joinpath("plot-light.png").write_bytes(b"png")
    result = repo.run(str(_step("impl-repair.yml", "Process repaired image")["run"]), shell)
    assert result.returncode == 1
    assert "::error::Missing plot-{light,dark}.png after repair" in result.stdout
    assert repo.read("output") == "gate=the repair left no plot-light.png and plot-dark.png\n"


def _age_renders(repo: Repo, light: int, dark: int) -> None:
    """Write each render that many seconds after the implementation file was last written (negative: before it)."""
    impl = repo.ws / IMPL
    written = impl.stat().st_mtime
    for theme, seconds in (("light", light), ("dark", dark)):
        png = impl.parent / f"plot-{theme}.png"
        png.write_bytes(b"png")
        os.utime(png, (written + seconds, written + seconds))


# The renders' age against the file (light, dark), and what the job summary says.
FRESHNESS = [
    ((60, 60), "fresh"),
    ((-60, -60), f"stale (plot-light.png, plot-dark.png older than {LIB}{EXT})"),
    ((-60, 60), f"stale (plot-light.png older than {LIB}{EXT})"),
    ((60, -60), f"stale (plot-dark.png older than {LIB}{EXT})"),
]
FRESHNESS_IDS = ["rendered-last", "written-after-both", "light-stale", "dark-stale"]


def _assert_freshness(result: subprocess.CompletedProcess[str], repo: Repo, expected: str) -> None:
    """The summary line, the warning only when stale, and never a failure."""
    assert result.returncode == 0, result.stdout + result.stderr
    assert repo.read("summary") == f"**Render freshness:** {expected}\n"
    if expected == "fresh":
        assert "render_freshness" not in result.stdout
    else:
        assert f"::warning::render_freshness status=stale: {expected[len('stale (') : -1]}" in result.stdout


# `python -m core.images …` rewrites the PNGs in place, as the real module does.
FAKE_PYTHON = '#!/bin/sh\nfor arg in "$@"; do [ -f "$arg" ] && touch "$arg"; done\nexit 0\n'


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
@pytest.mark.parametrize(("ages", "expected"), FRESHNESS, ids=FRESHNESS_IDS)
def test_repair_records_render_freshness_without_failing(tmp_path, shell, ages, expected):
    """The whole step runs: freshness is read before the processing rewrites the PNGs, and gates nothing."""
    repo = Repo(tmp_path)
    _age_renders(repo, *ages)
    (repo.ws / ".venv" / "bin").mkdir(parents=True)
    (repo.ws / ".venv" / "bin" / "activate").touch()
    (repo.bin / "python").write_text(FAKE_PYTHON, encoding="utf-8")
    (repo.bin / "python").chmod(0o755)
    step = _step("impl-repair.yml", "Process repaired image")
    assert step["env"]["EXT"] == "${{ steps.lang.outputs.ext }}"  # without it every repair reads fresh
    result = repo.run(str(step["run"]), shell)
    _assert_freshness(result, repo, expected)
    assert repo.read("output") == ""  # never a gate
    assert "::notice::Processed both themes after repair" in result.stdout
    # The stub rewrote both PNGs, so a block placed after the processing would read `fresh`.
    assert all(
        (repo.ws / IMPL).parent.joinpath(f"plot-{t}.png").stat().st_mtime > (repo.ws / IMPL).stat().st_mtime
        for t in ("light", "dark")
    )


@pytest.mark.parametrize(
    ("markers", "expected"),
    [
        ("0", "The repair failed a gate: G1. Automatically"),
        ("1", "After its one auto-retry, the repair failed a gate: G1."),
    ],
    ids=["auto-retry", "exhausted"],
)
def test_a_failed_gate_is_named_in_the_crash_comment(tmp_path, markers, expected):
    env = {"PR_NUM": "7", "SPEC_ID": "spec-a", "LIBRARY": "plotly", "ATTEMPT": "2", "MODEL": "sonnet"}
    script = str(_step("impl-repair.yml", "Handle repair failure")["run"])
    result, calls = _run(script, tmp_path, tmp_path, REPOSITORY="o/r", RUN_ID="1", GH_MARKERS=markers, GATE="G1", **env)
    assert result.returncode == 0, result.stdout + result.stderr
    (comment,) = _calls(calls, "pr", "comment")
    assert expected in "\n".join(comment)
    assert "Claude Code Action" not in "\n".join(comment)


# --- impl-generate: the branch gate and the render source ---------------------------------------

GENERATE = str(_step("impl-generate.yml", "Create library metadata file")["run"])
CACHE = GENERATE[GENERATE.index("# The file those renders came from") : GENERATE.index("# Configure git auth")]
BRANCH_GATE = GENERATE[
    GENERATE.index("# The generator (or the adopt step) pushes the branch.") : GENERATE.index(
        "# An implementation PR never changes dependency files"
    )
]


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestGenerateBranchGate:
    def _metadata(self, repo: Repo, shell: list[str]) -> subprocess.CompletedProcess[str]:
        """The step from the render cache to the checkout, without the token line and the bare fetch between."""
        script = 'IMPL_DIR="plots/${SPEC_ID}/implementations/${LANGUAGE}"\n' + CACHE
        return repo.run(script + BRANCH_GATE, shell)

    def test_an_unreachable_origin_fails_with_its_own_message(self, tmp_path, shell):
        repo = Repo(tmp_path)
        repo.git("remote", "set-url", "origin", str(tmp_path / "gone.git"))
        result = self._metadata(repo, shell)
        assert result.returncode == 1
        assert f"::error::Could not look up {BRANCH} on origin (git ls-remote exit 128)" in result.stdout
        assert repo.git("rev-parse", "HEAD") == repo.start_sha

    def test_a_branch_that_was_never_pushed_fails_instead_of_taking_main(self, tmp_path, shell):
        repo = Repo(tmp_path)
        repo.git("push", "-q", "origin", "--delete", BRANCH)
        result = self._metadata(repo, shell)
        assert result.returncode == 1
        assert f"::error::Remote branch {BRANCH} not found" in result.stdout
        assert repo.git("rev-parse", "HEAD") == repo.start_sha  # nothing was checked out
        assert 'git checkout -B "$BRANCH" origin/main' not in GENERATE

    def test_the_pushed_file_passes_and_is_the_render_source(self, tmp_path, shell):
        repo = Repo(tmp_path)
        rendered = CODE.format(score="87/100", x=9)
        repo.commit({IMPL: rendered}, "feat: implement")
        repo.push()
        # The gate fetches the branch itself: no tracking ref is left from the push.
        repo.git("update-ref", "-d", f"refs/remotes/origin/{BRANCH}")
        # Another tracked file changed in the workspace: only the implementation is compared.
        other = repo.ws / "automation" / "scripts" / "render_hash.py"
        other.write_text(other.read_text(encoding="utf-8") + "# a local edit\n", encoding="utf-8")
        result = self._metadata(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (repo.runner / "render-source").read_text(encoding="utf-8") == rendered
        assert (repo.ws / IMPL).read_text(encoding="utf-8") == rendered
        assert repo.git("rev-parse", f"origin/{BRANCH}") == repo.git("rev-parse", "HEAD")
        assert repo.read("summary") == ""  # no renders here, so no freshness line

    @pytest.mark.parametrize("case", ["unpushed-commit", "uncommitted-edit", "stale-branch"])
    def test_a_branch_that_does_not_carry_the_rendered_file_fails(self, tmp_path, shell, case):
        """The ref exists, but it holds other code than the renders came from.

        `stale-branch` is a ref an earlier run left behind: this run cut its
        branch from main again, and its own push never landed.
        """
        repo = Repo(tmp_path)
        rendered = CODE.format(score="87/100", x=9)
        if case == "stale-branch":
            repo.git("checkout", "-q", "-B", BRANCH, "main")
        if case == "uncommitted-edit":
            (repo.ws / IMPL).write_text(rendered, encoding="utf-8")
        else:
            repo.commit({IMPL: rendered}, "feat: implement (the push never landed)")
        head = repo.git("rev-parse", "HEAD")
        result = self._metadata(repo, shell)
        assert result.returncode == 1
        assert f"::error::{IMPL} in the workspace is not the file on origin/{BRANCH} (git diff exit 1)" in result.stdout
        assert (repo.runner / "render-source").read_text(encoding="utf-8") == rendered
        # Nothing was checked out: the workspace still holds this run's file.
        assert repo.git("rev-parse", "HEAD") == head
        assert (repo.ws / IMPL).read_text(encoding="utf-8") == rendered

    def test_a_pushed_branch_without_the_implementation_fails(self, tmp_path, shell):
        repo = Repo(tmp_path)
        rendered = (repo.ws / IMPL).read_text(encoding="utf-8")
        repo.git("rm", "-q", "--cached", IMPL)
        repo.git("commit", "-q", "-m", "chore: the branch loses the file")
        repo.push()
        result = self._metadata(repo, shell)
        assert result.returncode == 1
        assert f"::error::{IMPL} is not on origin/{BRANCH}" in result.stdout
        assert (repo.ws / IMPL).read_text(encoding="utf-8") == rendered

    @pytest.mark.parametrize(("ages", "expected"), FRESHNESS, ids=FRESHNESS_IDS)
    def test_render_freshness_is_recorded_without_failing(self, tmp_path, shell, ages, expected):
        repo = Repo(tmp_path)
        _age_renders(repo, *ages)
        _assert_freshness(self._metadata(repo, shell), repo, expected)

    def test_one_render_alone_is_still_compared(self, tmp_path, shell):
        repo = Repo(tmp_path)
        _age_renders(repo, -60, 60)
        (repo.ws / IMPL).parent.joinpath("plot-dark.png").unlink()
        _assert_freshness(self._metadata(repo, shell), repo, f"stale (plot-light.png older than {LIB}{EXT})")


# --- the upload steps stage render.sha256 ---------------------------------------------------------

UPLOADS = [
    ("impl-generate.yml", "Upload to GCS Staging", "render-source"),
    ("impl-repair.yml", "Upload repaired plot to GCS staging", IMPL),
]


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
@pytest.mark.parametrize(("workflow", "step", "source"), UPLOADS, ids=["generate", "repair"])
class TestUploadStagesTheHash:
    def _upload(self, repo: Repo, workflow: str, step: str, source: str, shell, **env: str):
        for theme in ("light", "dark"):
            (repo.ws / IMPL).parent.joinpath(f"plot-{theme}.png").write_bytes(b"png")
        path = repo.runner / source if source == "render-source" else repo.ws / source
        path.write_text(CODE.format(score="87/100", x=5), encoding="utf-8")
        return repo.run(str(_step(workflow, step)["run"]), shell, **env)

    def test_the_hash_of_the_rendered_file_is_staged_without_an_acl_call(self, tmp_path, shell, workflow, step, source):
        repo = Repo(tmp_path)
        result = self._upload(repo, workflow, step, source, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert repo.staged_hash() == render_hash(CODE.format(score="pending", x=5).encode())
        calls = repo.read("gsutil.log").splitlines()
        (upload,) = [c for c in calls if c.endswith(f"gs://{STAGING}/render.sha256")]
        assert upload.startswith("-h Cache-Control:no-store cp ")
        assert not [c for c in calls if "acl" in c and "render.sha256" in c]

    def test_without_the_tools_a_stale_hash_goes(self, tmp_path, shell, workflow, step, source):
        repo = Repo(tmp_path)
        (repo.gcs / STAGING).mkdir(parents=True)
        (repo.gcs / STAGING / "render.sha256").write_text("f" * 64 + "\n", encoding="utf-8")
        result = self._upload(repo, workflow, step, source, shell, GITHUB_SHA="0" * 40)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::render.sha256 not staged" in result.stdout
        assert repo.staged_hash() is None


# --- impl-review: the warn-only check ------------------------------------------------------------

REVIEW_STEP = "Check the render hash (warn-only)"


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestReviewCheck:
    def _review(self, tmp_path: Path, shell, staged: str | None, **env: str):
        repo = Repo(tmp_path)
        tools = repo.runner / "regen-tools"
        tools.mkdir()
        for name in ("render_hash.py", "regen_gate.py"):
            shutil.copy(TOOLS / name, tools / name)
        if staged is not None:
            (repo.gcs / STAGING).mkdir(parents=True)
            (repo.gcs / STAGING / "render.sha256").write_text(f"{staged}  x\n", encoding="utf-8")
        # "Hide the previous review" rewrites the workspace copy; the check reads the head.
        (repo.ws / IMPL).write_text("rewritten\n", encoding="utf-8")
        script = str(_step("impl-review.yml", REVIEW_STEP)["run"])
        result = repo.run(script, shell, PR_NUM="7", HEAD_SHA=repo.start_sha, RUN_URL="https://run/1", **env)
        return result, repo

    def test_renders_of_the_head_post_nothing(self, tmp_path, shell):
        # Generated with `Quality: pending`, reviewed at the head that stores 72/100.
        result, repo = self._review(tmp_path, shell, render_hash(CODE.format(score="pending", x=1).encode()))
        assert result.returncode == 0, result.stdout + result.stderr
        assert not _calls(repo.gh_calls(), "pr", "comment")
        assert repo.read("output") == "status=match\n"
        assert "**Render hash:** match" in repo.read("summary")

    @pytest.mark.parametrize(
        ("staged", "env", "status"),
        [("f" * 64, {}, "mismatch"), (None, {}, "missing"), ("f" * 64, {"GSUTIL_FAIL": "1"}, "unreadable")],
    )
    def test_anything_else_comments_once_and_never_fails(self, tmp_path, shell, staged, env, status):
        result, repo = self._review(tmp_path, shell, staged, **env)
        assert result.returncode == 0, result.stdout + result.stderr
        (comment,) = _calls(repo.gh_calls(), "pr", "comment")
        assert comment[:4] == ["pr", "comment", "7", "--body-file"]
        assert f"<!-- render-hash:v1 status={status} head={repo.start_sha} -->" in Path(comment[4]).read_text()
        assert repo.read("output") == f"status={status}\n"
        assert f"::warning::render_hash status={status}" in result.stdout

    def test_a_lost_comment_only_warns(self, tmp_path, shell):
        result, _ = self._review(tmp_path, shell, None, GH_COMMENT_RC="1")
        assert result.returncode == 0
        assert "::warning::render-hash comment not posted on PR #7" in result.stdout

    @pytest.mark.parametrize(
        ("heads", "env", "posted"),
        [
            ("same", {}, False),  # a re-review or a resumed review of the same head
            ("other-head", {}, True),
            ("other-status", {}, True),
            ("same", {"GH_FAIL_API": "1"}, True),  # an unreadable list posts it
        ],
    )
    def test_one_comment_per_status_and_head(self, tmp_path, shell, heads, env, posted):
        """A resumed review of the same head adds no comment, so the pause stays the PR's last bot comment.

        The review's pause dedupe compares that last comment's first line with
        its marker; a hash comment posted on every run would sit in between.
        """
        listing = tmp_path / "heads"
        result, repo = self._review(tmp_path, shell, None, GH_HEADS=str(listing), **env)
        assert result.returncode == 0  # first run: posts
        marker = {
            "same": f"<!-- render-hash:v1 status=missing head={repo.start_sha} -->",
            "other-head": f"<!-- render-hash:v1 status=missing head={'e' * 40} -->",
            "other-status": f"<!-- render-hash:v1 status=mismatch head={repo.start_sha} -->",
        }[heads]
        listing.write_text(f"## :robot: AI Review\n{marker}\n", encoding="utf-8")
        (tmp_path / "gh.log").unlink()
        script = str(_step("impl-review.yml", REVIEW_STEP)["run"])
        again = repo.run(script, shell, PR_NUM="7", HEAD_SHA=repo.start_sha, GH_HEADS=str(listing), **env)
        assert again.returncode == 0, again.stdout + again.stderr
        assert bool(_calls(repo.gh_calls(), "pr", "comment")) == posted
        assert ("already carries this render-hash comment" in again.stdout) == (not posted)


# --- wiring ----------------------------------------------------------------------------------------


def test_the_review_checks_after_the_download_and_before_the_review():
    names = _names("impl-review.yml")
    step = _step("impl-review.yml", REVIEW_STEP)
    assert names.index("Download plot images from staging") + 1 == names.index(REVIEW_STEP)
    assert names.index(REVIEW_STEP) < names.index("Hide the previous review") < names.index("Run AI Quality Review")
    assert step["continue-on-error"] is True and step["if"] == "steps.gcs.outcome == 'success'"
    assert "id" not in step  # no later step can key a decision on it


def test_the_repair_gate_sits_between_claude_and_the_renders():
    names = _names("impl-repair.yml")
    gate = names.index("Check the repair's push")
    assert names[gate - 1] == "Stop when Claude stopped the session"
    assert names[gate + 1] == "Process repaired image"
    checkout = str(_step("impl-repair.yml", "Checkout PR branch")["run"])
    assert checkout.index('git checkout "$BRANCH"') < checkout.index('echo "start_sha=$(git rev-parse HEAD)"')


def test_the_hash_never_reaches_production():
    """Review and merge copy `plot-*` objects only, and render.sha256 is not one."""
    promote = str(_step("impl-merge.yml", "Promote GCS images to production")["run"])
    assert 'cp "${STAGING}/plot-*" "${PRODUCTION}/"' in promote
    download = str(_step("impl-review.yml", "Download plot images from staging")["run"])
    assert "/${LIBRARY}/plot-*" in download and "render.sha256" not in download
