"""The record-only contract check in impl-review.yml (P2b).

"Contract check (record-only)" runs automation/scripts/contract_check.py, the
workflow-ref copy, on the implementation at the PR head and, when main holds
the file, on its predecessor. It writes a job-summary line and a notice, never
fails the job, and leaves no copy of the predecessor behind (its header holds
the stored score, which the review must not see).

The step script runs here under `bash -e` and `bash -eo pipefail` against the
scratch origin of test_render_hash_steps.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from tests.unit.workflows.test_pipeline_retry_gaps import _step, _steps
from tests.unit.workflows.test_render_hash_steps import (
    BRANCH,
    CODE,
    EXT,
    IMPL,
    LANG,
    LIB,
    SHELL_IDS,
    SHELLS,
    SPEC,
    TOOLS,
    Repo,
)


STEP = "Contract check (record-only)"
COMPLIANT = (
    '""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nQuality: pending | Created: 2026-11-10\n"""\n\n'
    "import os\n\n"
    'THEME = os.getenv("ANYPLOT_THEME", "light")\n'
    f'TITLE = "{SPEC} · {LANG} · {LIB} · anyplot.ai"\n'
    'OUT = f"plot-{THEME}.png"\n'
)


def _repo(tmp_path) -> Repo:
    repo = Repo(tmp_path)
    tools = repo.runner / "regen-tools"
    tools.mkdir()
    shutil.copy(TOOLS / "contract_check.py", tools / "contract_check.py")
    repo.git("fetch", "-q", "origin")  # impl-review's checkout has origin/main
    return repo


def _run(repo: Repo, shell: list[str], **env: str) -> subprocess.CompletedProcess[str]:
    script = str(_step("impl-review.yml", STEP)["run"])
    return repo.run(script, shell, **{"HEAD_SHA": repo.git("rev-parse", "HEAD"), **env})


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestContractCheckStep:
    def test_a_regeneration_is_checked_against_its_predecessor(self, tmp_path, shell):
        """Main holds a file without the contract; the PR head fixes all of it."""
        repo = _repo(tmp_path)
        assert "anyplot.ai" in CODE and "ANYPLOT_THEME" not in CODE  # the fixture file breaks title, theme, save
        repo.commit({IMPL: COMPLIANT}, "feat: regenerate")
        repo.push()
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert repo.read("summary") == "**Contract check (record-only):** clean\n"
        assert (
            f"::notice::contract_check library={LIB} status=clean violations=none prev=title,theme,save new_only=none"
            in result.stdout
        )

    def test_inherited_violations_are_not_new(self, tmp_path, shell):
        repo = _repo(tmp_path)
        result = _run(repo, shell)  # the head still holds the fixture file, like main
        assert result.returncode == 0, result.stdout + result.stderr
        assert repo.read("summary") == (
            "**Contract check (record-only):** title, theme, save (new in this version: none)\n"
        )

    def test_the_head_is_read_not_the_workspace(self, tmp_path, shell):
        """`Hide the previous review` rewrites the workspace copy later; an edit there never counts."""
        repo = _repo(tmp_path)
        (repo.ws / IMPL).write_text(COMPLIANT, encoding="utf-8")
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "status=violations violations=title,theme,save" in result.stdout

    def test_a_first_generation_has_no_predecessor(self, tmp_path, shell):
        repo = _repo(tmp_path)
        other = "plots/line-basic/implementations/python/matplotlib.py"
        repo.commit({other: COMPLIANT.replace(SPEC, "line-basic")}, "feat: implement line-basic")
        repo.push()
        result = _run(repo, shell, SPEC_ID="line-basic")
        assert result.returncode == 0, result.stdout + result.stderr
        assert repo.read("summary") == "**Contract check (record-only):** clean\n"
        assert "prev=n/a" in result.stdout

    def test_another_language_is_read_under_its_own_path(self, tmp_path, shell):
        """The path comes from LANGUAGE and EXT: a JavaScript file is found, and the save rule does not apply."""
        repo = _repo(tmp_path)
        source = (
            "// anyplot.ai\n// scatter-basic: Basic Scatter Plot\n"
            "const t = window.ANYPLOT_TOKENS;\n"
            f'const TITLE = "{SPEC} · javascript · d3 · anyplot.ai";\n'
        )
        repo.commit({f"plots/{SPEC}/implementations/javascript/d3.js": source}, "feat: implement d3")
        repo.push()
        result = _run(repo, shell, LANGUAGE="javascript", LIBRARY="d3", EXT=".js")
        assert result.returncode == 0, result.stdout + result.stderr
        assert repo.read("summary") == "**Contract check (record-only):** clean\n"
        assert "::notice::contract_check library=d3 status=clean violations=none prev=n/a" in result.stdout

    def test_a_missing_file_or_tool_never_fails_the_job(self, tmp_path, shell):
        repo = _repo(tmp_path)
        result = _run(repo, shell, SPEC_ID="no-such-spec")
        assert result.returncode == 0, result.stdout + result.stderr
        assert "status=unreadable" in result.stdout
        (repo.runner / "regen-tools" / "contract_check.py").unlink()
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "::warning::contract check did not run" in result.stdout

    def test_no_copy_of_either_source_is_left_behind(self, tmp_path, shell):
        repo = _repo(tmp_path)
        result = _run(repo, shell)
        assert result.returncode == 0, result.stdout + result.stderr
        assert sorted(p.name for p in repo.runner.iterdir()) == ["regen-tools"]


def test_the_step_is_record_only_and_sits_after_the_canvas_gate():
    names = [s.get("name") for s in _steps("impl-review.yml")]
    step = _step("impl-review.yml", STEP)
    assert names[names.index("Canvas dimension gate") + 1] == STEP
    assert names.index(STEP) < names.index("Hide the previous review") < names.index("Run AI Quality Review")
    assert step["continue-on-error"] is True
    assert "id" not in step and "if" not in step  # every language, and no later step can key a decision on it
    assert "exit 1" not in str(step["run"])
    assert step["env"]["EXT"] == "${{ steps.lang.outputs.ext }}"
    assert step["env"]["HEAD_SHA"] == "${{ steps.pr.outputs.head_sha }}"


def test_the_checker_is_the_workflow_refs_copy():
    """Copied before the checkout of the PR head, so the head cannot choose its own rules."""
    checkout = str(_step("impl-review.yml", "Checkout PR code")["run"])
    assert checkout.index("automation/scripts/contract_check.py") < checkout.index("git checkout")
    assert f"origin/{BRANCH}" not in str(_step("impl-review.yml", STEP)["run"])
    assert EXT == ".py"
