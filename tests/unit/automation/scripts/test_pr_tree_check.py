"""pr_tree_check.py: an implementation pull request changes only its pair's two files.

Each test builds a scratch repository whose main holds the catalogue as it is
and whose branch is the pull request head, then runs the check as impl-review
does: against the merge base with origin/main, before the head is checked out.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from automation.scripts import pr_tree_check
from tests.unit.workflows.test_pipeline_retry_gaps import _step


SPEC, LANG, LIB = "heatmap-annotated", "python", "pygal"
IMPL = f"plots/{SPEC}/implementations/{LANG}/{LIB}.py"
META = f"plots/{SPEC}/metadata/{LANG}/{LIB}.yaml"
SCRIPT = Path(pr_tree_check.__file__)


def _git(repo: Path, *args: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t"}
    env["GIT_COMMITTER_EMAIL"] = "t@t"
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env).stdout


def _write(repo: Path, path: str, text: str = "x = 1\n") -> Path:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """main with the pair's two files and another pair's file; the branch `head` starts from it."""
    _git(tmp_path, "init", "-q", "-b", "main")
    _write(tmp_path, IMPL)
    _write(tmp_path, META, "library: pygal\n")
    _write(tmp_path, f"plots/{SPEC}/implementations/{LANG}/matplotlib.py")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "main")
    _git(tmp_path, "checkout", "-q", "-b", "head")
    return tmp_path


def _commit(repo: Path) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "head")
    return _git(repo, "rev-parse", "HEAD").strip()


def _check(repo: Path, head: str, **overrides: str) -> subprocess.CompletedProcess[str]:
    args = {"--base": "main", "--head": head, "--spec-id": SPEC, "--language": LANG, "--library": LIB, "--ext": ".py"}
    args.update({f"--{k.replace('_', '-')}": v for k, v in overrides.items()})
    argv = [sys.executable, "-I", str(SCRIPT), *(item for pair in args.items() for item in pair)]
    return subprocess.run(argv, cwd=repo, capture_output=True, text=True)


def test_the_pairs_implementation_and_metadata_pass(repo):
    _write(repo, IMPL, "x = 2\n")
    _write(repo, META, "library: pygal\nquality_score: 80\n")
    result = _check(repo, _commit(repo))
    assert result.returncode == 0, result.stdout
    assert "::notice::pr_tree_check: 2 file(s), all the pair's own" in result.stdout


def test_a_first_generation_adds_the_two_files_and_passes(repo):
    other = f"plots/{SPEC}/implementations/javascript/muix.tsx"
    _write(repo, other, "export default () => null;\n")
    _write(repo, f"plots/{SPEC}/metadata/javascript/muix.yaml", "library: muix\n")
    result = _check(repo, _commit(repo), language="javascript", library="muix", ext=".tsx")
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("path", [IMPL, META])
def test_one_of_the_two_alone_passes(repo, path):
    """A repair or the review's own metadata commit changes one file."""
    _write(repo, path, "changed = True\n")
    assert _check(repo, _commit(repo)).returncode == 0


@pytest.mark.parametrize("sibling", [".sh", ".pyc", ".R", ".tsx"])
def test_a_sibling_with_another_extension_refuses(repo, sibling):
    """Only the extension impl-review derives from the library is the pair's file."""
    _write(repo, IMPL, "x = 2\n")
    _write(repo, IMPL.removesuffix(".py") + sibling, "echo\n")
    result = _check(repo, _commit(repo))
    assert result.returncode == 1 and f"{LIB}{sibling} (not this pair's implementation or metadata)" in result.stdout


def test_main_moving_on_does_not_count_against_the_head(repo):
    """Three dots: the head is compared with the merge base, so later commits on main are not its changes."""
    _write(repo, IMPL, "x = 2\n")
    head = _commit(repo)
    _git(repo, "checkout", "-q", "main")
    _write(repo, "core/new_module.py")
    _commit(repo)
    assert _check(repo, head).returncode == 0


@pytest.mark.parametrize(
    "path",
    [
        "PIL/__init__.py",  # beside a heredoc python3 in the workspace root
        ".claude/settings.json",
        "prompts/quality-criteria.md",
        f"plots/{SPEC}/implementations/{LANG}/matplotlib.py",  # another library of the same spec
        f"plots/other-spec/implementations/{LANG}/{LIB}.py",
        f"plots/{SPEC}/specification.md",
    ],
)
def test_any_other_path_refuses(repo, path):
    _write(repo, IMPL, "x = 2\n")
    _write(repo, path, "changed = True\n")
    result = _check(repo, _commit(repo))
    assert result.returncode == 1
    assert result.stdout.startswith("::error::the pull request head changes more than its pair's two files: ")
    assert f"{path} (not this pair's implementation or metadata)" in result.stdout


def test_a_symlink_an_executable_and_a_deletion_refuse(repo):
    (repo / IMPL).unlink()
    (repo / IMPL).symlink_to("../../../../etc/passwd")
    result = _check(repo, _commit(repo))
    assert result.returncode == 1 and f"{IMPL} (status T, mode 120000)" in result.stdout

    _git(repo, "checkout", "-q", "main")
    _git(repo, "checkout", "-q", "-b", "exec")
    (repo / IMPL).chmod(0o755)
    result = _check(repo, _commit(repo))
    assert result.returncode == 1 and f"{IMPL} (status M, mode 100755)" in result.stdout

    _git(repo, "checkout", "-q", "main")
    _git(repo, "checkout", "-q", "-b", "gone")
    (repo / META).unlink()
    result = _check(repo, _commit(repo))
    assert result.returncode == 1 and f"{META} (status D, mode 000000)" in result.stdout


def test_a_path_with_a_newline_cannot_hide(repo):
    """-z keeps a name with a newline one path, so it cannot pose as the pair's file."""
    _write(repo, IMPL + "\nPIL/__init__.py")
    result = _check(repo, _commit(repo))
    assert result.returncode == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"spec_id": "Heatmap"},
        {"spec_id": "a/../b"},
        {"language": "py thon"},
        {"library": "pyg.al"},
        {"library": ".*"},
        {"ext": "py"},
        {"ext": ".p*"},
        {"ext": "./x"},
    ],
)
def test_malformed_names_are_a_usage_error(repo, overrides):
    result = _check(repo, _commit(repo), **overrides)
    assert result.returncode == 2 and result.stdout.startswith("::error::pr_tree_check: malformed")


def test_a_head_git_cannot_compare_fails_closed(repo):
    result = _check(repo, "0" * 40)
    assert result.returncode == 2
    assert "git could not compare" in result.stdout


def test_impl_review_runs_it_from_its_own_ref_before_the_checkout():
    step = _step("impl-review.yml", "Checkout PR code")
    script = str(step["run"])
    call = 'python3 -I automation/scripts/pr_tree_check.py --base origin/main --head "$HEAD_SHA"'
    assert script.index("git fetch origin") < script.index(call) < script.index('git checkout "$HEAD_SHA"')
    assert "|| true" not in script[script.index(call) : script.index('git checkout "$HEAD_SHA"')]
    assert "continue-on-error" not in step
    assert step["env"]["SPEC_ID"] == "${{ steps.pr.outputs.specification_id }}"
    assert step["env"]["LIBRARY"] == "${{ steps.pr.outputs.library }}"
    assert step["env"]["LANGUAGE"] == "${{ steps.lang.outputs.language }}"
    assert step["env"]["EXT"] == "${{ steps.lang.outputs.ext }}"
    assert '--library "$LIBRARY" --ext "$EXT"' in script
