"""impl-merge's promotion fails loudly instead of passing a stale pair.

PR #12800 (waterfall-basic/muix) merged while "Promote GCS images to
production" passed: the copy from staging failed with its stderr thrown away,
the step printed "No staging files to promote", deleted staging anyway and
announced "Promoted images to production". Production kept the previous
renders under the new code and review.

The step now lists staging first. Missing theme renders fail the step when
the PR changed its implementation, a failed listing or copy fails it with
staging kept, and the notice names the number of files copied. "Report a
failed promotion" then comments the command that fixes the pair. Both scripts
run here under `bash -eo pipefail` against a directory that stands in for the
bucket, with a fake `gsutil`, a fake `gh` and a no-op `sleep` on PATH.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml


WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "impl-merge.yml"
PROMOTE = "Promote GCS images to production"
REPORT = "Report a failed promotion"
SPEC, LANG, LIB = "waterfall-basic", "javascript", "muix"
STAGING = f"anyplot-images/staging/{SPEC}/{LANG}/{LIB}"
PRODUCTION = f"anyplot-images/plots/{SPEC}/{LANG}/{LIB}"
IMPL = f"plots/{SPEC}/implementations/{LANG}/{LIB}.tsx"
META = f"plots/{SPEC}/metadata/{LANG}/{LIB}.yaml"
RENDERS = ["plot-light.png", "plot-dark.png", "plot-light_400.webp", "plot-dark.html"]

# A bucket in $FAKE_GCS: `ls` and `cp` expand the glob like gsutil (one `*`
# stays inside one level), `rm -r` removes a prefix. GSUTIL_FAIL_<CMD>=N fails
# the first N calls of that command with a 503 on stderr. Every call is
# recorded, NUL-separated, as one file in $CALLS.
FAKE_GSUTIL = r"""#!/bin/bash
n=$(ls "$CALLS" | wc -l)
printf '%s\0' gsutil "$@" > "$CALLS/$n"
while [ $# -gt 0 ]; do
  case "$1" in
    -m) shift ;;
    -h) shift 2 ;;
    *) break ;;
  esac
done
cmd="$1"; shift
upper=$(echo "$cmd" | tr a-z A-Z)
limit_var="GSUTIL_FAIL_${upper}"
limit="${!limit_var:-0}"
counter="$CALLS/../fail-$cmd"
done_count=$(cat "$counter" 2>/dev/null || echo 0)
if [ "$done_count" -lt "$limit" ]; then
  echo $((done_count + 1)) > "$counter"
  echo "ServiceException: 503 Backend Error" >&2
  exit 1
fi
local_path() { echo "$FAKE_GCS/${1#gs://}"; }
shopt -s nullglob
case "$cmd" in
  ls)
    # shellcheck disable=SC2206
    matches=( $(local_path "$1") )
    files=()
    for m in "${matches[@]}"; do [ -f "$m" ] && files+=("$m"); done
    if [ ${#files[@]} -eq 0 ]; then
      echo "CommandException: One or more URLs matched no objects." >&2
      exit 1
    fi
    for m in "${files[@]}"; do echo "gs://${m#"$FAKE_GCS"/}"; done ;;
  cp)
    # shellcheck disable=SC2206
    matches=( $(local_path "$1") )
    dst=$(local_path "$2")
    if [ ${#matches[@]} -eq 0 ]; then
      echo "CommandException: No URLs matched: $1" >&2
      exit 1
    fi
    mkdir -p "$dst"
    for m in "${matches[@]}"; do [ -f "$m" ] && cp "$m" "$dst/"; done
    echo "Operation completed over ${#matches[@]} objects." >&2 ;;
  rm)
    [ "$1" = "-r" ] && shift
    target=$(local_path "$1")
    if [ ! -e "$target" ]; then
      echo "CommandException: 1 files/objects could not be removed." >&2
      exit 1
    fi
    rm -rf "$target" ;;
  *)
    echo "fake gsutil: unexpected command $cmd" >&2
    exit 2 ;;
esac
"""

# `pr view --json files` prints $GH_FILES (fails with GH_FAIL_FILES=1),
# `pr comment` exits $GH_COMMENT_RC. Every call is recorded like gsutil's.
FAKE_GH = r"""#!/bin/bash
n=$(ls "$CALLS" | wc -l)
printf '%s\0' gh "$@" > "$CALLS/$n"
case "$1 $2" in
  "pr view")
    [ "${GH_FAIL_FILES:-0}" = "1" ] && { echo "HTTP 502" >&2; exit 1; }
    printf '%s\n' $GH_FILES ;;
  "pr comment") exit "${GH_COMMENT_RC:-0}" ;;
esac
exit 0
"""


def _steps() -> list[dict[str, Any]]:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return list(workflow["jobs"]["merge"]["steps"])


def _step(name: str) -> dict[str, Any]:
    (step,) = [s for s in _steps() if s.get("name") == name]
    return step


def _code(script: str) -> str:
    return "\n".join(line for line in script.splitlines() if not line.lstrip().startswith("#"))


def _git_env(tmp: Path) -> dict[str, str]:
    """No user or system git config (signing, hooks) and no inherited GIT_* state."""
    empty = tmp / "gitconfig"
    empty.touch()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "GH_"))}
    # The ceiling keeps git from finding a repository above the test's own.
    env.update(GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1", GIT_CEILING_DIRECTORIES=str(tmp))
    return env


class Runner:
    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.gcs = tmp / "gcs"
        self.calls_dir = tmp / "calls"
        self.calls_dir.mkdir()
        self.bin = tmp / "bin"
        self.bin.mkdir()
        for name, body in (("gsutil", FAKE_GSUTIL), ("gh", FAKE_GH), ("sleep", "#!/bin/sh\nexit 0\n")):
            (self.bin / name).write_text(body, encoding="utf-8")
            (self.bin / name).chmod(0o755)
        self.runner_temp = tmp / "runner-temp"
        self.runner_temp.mkdir()
        self.output = tmp / "github-output"
        self.summary = tmp / "step-summary"
        self.ws = tmp / "workspace"
        self.ws.mkdir()
        self.put(PRODUCTION, {"plot-light.png": "old", "plot-dark.png": "old"})

    def put(self, prefix: str, files: dict[str, str]) -> None:
        for name, text in files.items():
            path = self.gcs / prefix / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def stage(self, names: list[str]) -> None:
        self.put(STAGING, dict.fromkeys(names, "new"))
        self.put(f"{STAGING}/adapt", {"new-smoke.json": "{}"})

    def read(self, prefix: str, name: str) -> str:
        return (self.gcs / prefix / name).read_text(encoding="utf-8")

    def origin_main(self, metadata: str) -> None:
        """A bare origin whose main holds the merged metadata, cloned into the workspace."""
        seed = self.tmp / "seed"
        seed.mkdir()
        env = _git_env(self.tmp)
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run([*git, "-C", str(seed), "init", "-q", "-b", "main"], check=True, env=env)
        (seed / META).parent.mkdir(parents=True)
        (seed / META).write_text(metadata, encoding="utf-8")
        subprocess.run([*git, "-C", str(seed), "add", "-A"], check=True, env=env)
        subprocess.run([*git, "-C", str(seed), "commit", "-q", "-m", "merged"], check=True, env=env)
        origin = self.tmp / "origin.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(seed), str(origin)], check=True, env=env)
        self.ws.rmdir()
        subprocess.run(["git", "clone", "-q", str(origin), str(self.ws)], check=True, env=env)

    def run(self, name: str, **env: str) -> subprocess.CompletedProcess[str]:
        script = _step(name)["run"]
        assert "${{" not in script
        values = {
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            "CALLS": str(self.calls_dir),
            "FAKE_GCS": str(self.gcs),
            "RUNNER_TEMP": str(self.runner_temp),
            "GITHUB_OUTPUT": str(self.output),
            "GITHUB_STEP_SUMMARY": str(self.summary),
            "GH_TOKEN": "unused",
            "GH_REPO": "o/r",
            "PR_NUM": "12800",
            "SPEC_ID": SPEC,
            "LANGUAGE": LANG,
            "LIBRARY": LIB,
            "RUN_URL": "https://github.com/o/r/actions/runs/1",
            "GH_FILES": f"{IMPL} {META}",
            **env,
        }
        # As Actions runs a `run:` step (it adds no pipefail; this is stricter).
        return subprocess.run(
            ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
            cwd=self.ws,
            env={**_git_env(self.tmp), **values},
            capture_output=True,
            text=True,
        )

    def calls(self, tool: str, *prefix: str) -> list[list[str]]:
        files = sorted(self.calls_dir.iterdir(), key=lambda p: int(p.name))
        calls = [p.read_bytes().decode().split("\0")[:-1] for p in files]
        wanted = [tool, *prefix]
        return [c[1:] for c in calls if c[: len(wanted)] == wanted]

    def outputs(self) -> dict[str, str]:
        if not self.output.exists():
            return {}
        return dict(line.split("=", 1) for line in self.output.read_text(encoding="utf-8").splitlines())


@pytest.fixture
def runner(tmp_path: Path) -> Runner:
    return Runner(tmp_path)


# --- Promote GCS images to production ---------------------------------------


def test_promotes_the_renders_with_their_count_and_cleans_staging(runner: Runner) -> None:
    runner.stage(RENDERS)
    result = runner.run(PROMOTE)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"::notice::Promoted images to production: 4 file(s) of {SPEC}/{LANG}/{LIB}" in result.stdout
    for name in RENDERS:
        assert runner.read(PRODUCTION, name) == "new"
    assert not (runner.gcs / PRODUCTION / "adapt").exists()  # the records stay out
    assert not (runner.gcs / STAGING).exists()
    assert runner.outputs() == {}
    assert runner.calls("gh") == []  # complete staging needs no file list


def test_empty_staging_fails_when_the_pr_changed_its_implementation(runner: Runner) -> None:
    result = runner.run(PROMOTE)
    assert result.returncode == 1
    assert "::error::Staging lacks plot-light.png plot-dark.png" in result.stdout
    assert "merged PR #12800 changed its implementation" in result.stdout
    assert "Promoted images to production" not in result.stdout
    assert runner.outputs() == {"failure": "missing"}
    assert runner.read(PRODUCTION, "plot-light.png") == "old"
    assert runner.calls("gsutil", "-m") == []  # neither a copy nor a cleanup ran


def test_empty_staging_passes_a_pr_that_changed_no_implementation(runner: Runner) -> None:
    result = runner.run(PROMOTE, GH_FILES=META)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "::notice::Nothing promoted: staging lacks plot-light.png plot-dark.png" in result.stdout
    assert "Promoted images to production" not in result.stdout
    assert runner.outputs() == {}
    (view,) = runner.calls("gh", "pr", "view")
    assert view == ["pr", "view", "12800", "--repo", "o/r", "--json", "files", "-q", ".files[].path"]


def test_an_unreadable_file_list_counts_as_a_changed_implementation(runner: Runner) -> None:
    result = runner.run(PROMOTE, GH_FAIL_FILES="1")
    assert result.returncode == 1
    assert result.stdout.count("::warning::gh pr view (files) failed") == 3
    assert runner.outputs() == {"failure": "missing"}


def test_half_a_pair_is_not_promoted(runner: Runner) -> None:
    runner.stage(["plot-light.png", "plot-light_400.webp"])
    result = runner.run(PROMOTE)
    assert result.returncode == 1
    assert "::error::Staging lacks plot-dark.png" in result.stdout
    assert "(2 plot-* object(s) staged)" in result.stdout
    assert runner.read(PRODUCTION, "plot-light.png") == "old"
    assert (runner.gcs / STAGING / "plot-light.png").exists()
    assert runner.outputs() == {"failure": "missing"}


def test_a_failed_copy_keeps_staging_for_a_re_dispatch(runner: Runner) -> None:
    runner.stage(RENDERS)
    result = runner.run(PROMOTE, GSUTIL_FAIL_CP="3")
    assert result.returncode == 1
    assert result.stdout.count("::warning::Copying") == 3
    assert "503 Backend Error" in result.stdout  # gsutil's own words reach the log
    assert "Staging is kept: re-dispatch impl-merge.yml -f pr_number=12800" in result.stdout
    assert "Promoted images to production" not in result.stdout
    assert runner.outputs() == {"failure": "transfer"}
    assert (runner.gcs / STAGING / "plot-light.png").exists()
    assert runner.calls("gsutil", "-m", "rm") == []


def test_a_transient_copy_failure_is_retried(runner: Runner) -> None:
    runner.stage(RENDERS)
    result = runner.run(PROMOTE, GSUTIL_FAIL_CP="1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "::notice::Promoted images to production: 4 file(s)" in result.stdout
    assert len(runner.calls("gsutil", "-m", "-h")) == 2


def test_a_listing_error_is_retried_and_then_reported_as_a_transfer_failure(runner: Runner) -> None:
    runner.stage(RENDERS)
    result = runner.run(PROMOTE, GSUTIL_FAIL_LS="3")
    assert result.returncode == 1
    assert result.stdout.count("::warning::Listing") == 3
    assert runner.outputs() == {"failure": "transfer"}
    assert (runner.gcs / STAGING / "plot-light.png").exists()


def test_a_listing_error_that_clears_promotes_as_usual(runner: Runner) -> None:
    runner.stage(RENDERS)
    result = runner.run(PROMOTE, GSUTIL_FAIL_LS="1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "::notice::Promoted images to production: 4 file(s)" in result.stdout


def test_a_failed_cleanup_only_warns(runner: Runner) -> None:
    runner.stage(RENDERS)
    result = runner.run(PROMOTE, GSUTIL_FAIL_RM="1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "::warning::Could not remove" in result.stdout
    assert "::notice::Promoted images to production: 4 file(s)" in result.stdout


def test_the_step_swallows_no_gsutil_error() -> None:
    code = _code(_step(PROMOTE)["run"])
    assert "/dev/null" not in code
    assert "|| true" not in code
    assert "|| echo" not in code
    assert "acl ch" not in code  # uniform bucket-level access: IAM makes the objects public


# --- Report a failed promotion -----------------------------------------------


def test_missing_renders_get_an_adopt_from_main_command_with_the_author(runner: Runner) -> None:
    runner.origin_main("library: muix\ngenerated_by: claude-opus-5-5\nquality_score: 87\n")
    result = runner.run(REPORT, FAILURE="missing")
    assert result.returncode == 0, result.stdout + result.stderr
    command = (
        f"gh workflow run impl-generate.yml -f specification_id={SPEC} -f library={LIB}"
        " -f source_ref=main -f source_model=claude-opus-5-5"
    )
    (comment,) = runner.calls("gh", "pr", "comment")
    assert comment[:5] == ["pr", "comment", "12800", "--repo", "o/r"]
    body = comment[6]
    opening = f"**Promotion failed:** staging lacked this PR's renders of `{SPEC}/{LANG}/{LIB}`"
    assert body.startswith(opening)
    assert "(both theme PNGs are needed)" in body
    assert f"```bash\n{command}\n```" in body
    assert "(https://github.com/o/r/actions/runs/1)" in body
    assert command in runner.summary.read_text(encoding="utf-8")
    assert f"::error::Promotion of {SPEC}/{LANG}/{LIB} failed (missing); to fix it: {command}" in result.stdout


@pytest.mark.parametrize("author", ["'adopted:gemini/muix-9'", ".hidden-model", "a" * 41])
def test_an_author_impl_generate_would_refuse_is_left_out(runner: Runner, author: str) -> None:
    runner.origin_main(f"library: muix\ngenerated_by: {author}\n")
    result = runner.run(REPORT, FAILURE="missing")
    assert result.returncode == 0, result.stdout + result.stderr
    body = runner.calls("gh", "pr", "comment")[0][6]
    assert f"-f library={LIB} -f source_ref=main\n" in body
    assert "source_model" not in body


def test_without_the_merged_metadata_the_command_has_no_author(runner: Runner) -> None:
    result = runner.run(REPORT, FAILURE="missing")  # no git checkout at all
    assert result.returncode == 0, result.stdout + result.stderr
    body = runner.calls("gh", "pr", "comment")[0][6]
    assert "-f source_ref=main\n" in body


@pytest.mark.parametrize(("language", "library"), [("r", "ggplot2"), ("julia", "makie")])
def test_r_and_julia_get_a_forced_regeneration(runner: Runner, language: str, library: str) -> None:
    result = runner.run(REPORT, FAILURE="missing", LANGUAGE=language, LIBRARY=library)
    assert result.returncode == 0, result.stdout + result.stderr
    body = runner.calls("gh", "pr", "comment")[0][6]
    command = f"gh workflow run impl-generate.yml -f specification_id={SPEC} -f library={library} -f regen_gate=false"
    assert command in body
    assert "source_ref" not in body
    assert "Adopt mode renders Python and JavaScript only, so this is a forced regeneration" in body


def test_a_failed_transfer_gets_a_merge_re_dispatch(runner: Runner) -> None:
    result = runner.run(REPORT, FAILURE="transfer")
    assert result.returncode == 0, result.stdout + result.stderr
    body = runner.calls("gh", "pr", "comment")[0][6]
    assert "Staging is kept, and a re-dispatch promotes it:" in body
    assert "```bash\ngh workflow run impl-merge.yml -f pr_number=12800\n```" in body
    assert "impl-generate" not in body


def test_a_lost_comment_leaves_the_command_in_the_summary(runner: Runner) -> None:
    result = runner.run(REPORT, FAILURE="transfer", GH_COMMENT_RC="1")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "::warning::Could not comment on PR #12800" in result.stdout
    assert "gh workflow run impl-merge.yml -f pr_number=12800" in runner.summary.read_text(encoding="utf-8")


# --- Wiring --------------------------------------------------------------------


def test_the_report_follows_the_promotion_and_the_bookkeeping_waits_for_success() -> None:
    names = [s.get("name") for s in _steps()]
    promote = names.index(PROMOTE)
    assert names[promote + 1] == REPORT
    assert _step(PROMOTE)["id"] == "promote"
    assert _step(REPORT)["if"] == "failure() && steps.promote.outputs.failure != ''"
    # A failed promotion skips the "done" label, the "Complete" comment with its
    # preview links, the issue close and the sync dispatch.
    for step in _steps()[promote + 2 :]:
        condition = step.get("if", "")
        assert "always()" not in condition, step["name"]
        assert "failure()" not in condition, step["name"]
