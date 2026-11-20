"""Tests for automation.scripts.pr_guard — which pull requests the pipeline acts on.

Only the pipeline's own: from this repository, on an
`implementation/<spec-id>/<library>` branch with a registered library, with a
full head SHA, and the number that was asked about. Anything else, a missing
or null field included, is refused with a fixed reason code. The CLI runs as
the workflows run it: a separate interpreter on a copy of the file, with the
pull request's JSON on stdin.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from automation.scripts import pr_guard, spec_pr_guard
from core.constants import SUPPORTED_LIBRARIES


REPO = "MarkusNeusinger/anyplot"
LIBS = sorted(SUPPORTED_LIBRARIES)
SHA = "0123456789abcdef0123456789abcdef01234567"


def own(**change: Any) -> dict[str, Any]:
    """A pull request of the pipeline's own, as `gh pr view --json` prints it, with `change` applied."""
    data: dict[str, Any] = {
        "number": 13275,
        "headRefName": "implementation/scatter-matrix/altair",
        "headRefOid": SHA,
        "isCrossRepository": False,
        "headRepository": {"id": "R_x", "name": "anyplot"},
        "headRepositoryOwner": {"id": "U_x", "login": "MarkusNeusinger"},
        "author": {"is_bot": True, "login": "app/github-actions"},
        "baseRefName": "main",
        "body": "**Parent Issue:** #42",
    }
    data.update(change)
    return data


def check(data: Any, **kwargs: Any) -> pr_guard.Verdict:
    return pr_guard.check(data, repo=REPO, libraries=LIBS, **kwargs)


class TestAllowed:
    def test_the_pipelines_own_pull_request_passes_with_its_values(self):
        verdict = check(own(), number=13275)
        assert verdict.allowed and verdict.reason is None
        assert (verdict.number, verdict.spec_id, verdict.library) == (13275, "scatter-matrix", "altair")
        assert verdict.branch == "implementation/scatter-matrix/altair" and verdict.head_sha == SHA

    @pytest.mark.parametrize("library", LIBS)
    def test_every_registered_library_passes(self, library):
        assert check(own(headRefName=f"implementation/a-b-1/{library}")).allowed

    def test_the_repository_compares_without_case(self):
        data = own(headRepository={"name": "AnyPlot"}, headRepositoryOwner={"login": "markusneusinger"})
        assert check(data).allowed

    def test_the_dispatch_inputs_may_be_checked_against_the_branch(self):
        assert check(own(), number=13275, spec_id="scatter-matrix", library="altair").allowed


class TestRefused:
    def test_a_pull_request_from_another_repository(self):
        data = own(isCrossRepository=True, headRepositoryOwner={"login": "someone-else"})
        assert check(data).reason == "cross_repository"

    @pytest.mark.parametrize(
        "change",
        [
            {"isCrossRepository": True},  # the owner and name alone do not decide it
            {"headRepositoryOwner": {"login": "someone-else"}},
            {"headRepository": {"name": "anyplot-fork"}},
        ],
    )
    def test_any_sign_of_another_repository(self, change):
        assert check(own(**change)).reason == "cross_repository"

    @pytest.mark.parametrize(
        "author",
        [
            {"login": "MarkusNeusinger"},
            {"login": "github-actions"},  # GraphQL's spelling is the app/ one
            {"login": "github-actions[bot]"},  # the REST spelling is not what gh prints here
            {"login": "app/claude"},
            {"login": "APP/GITHUB-ACTIONS"},
        ],
    )
    def test_a_pull_request_the_pipeline_did_not_open(self, author):
        assert check(own(author=author)).reason == "author_mismatch"

    @pytest.mark.parametrize("base", ["develop", "Main", "main ", "release/v1"])
    def test_a_pull_request_that_does_not_target_main(self, base):
        assert check(own(baseRefName=base)).reason == "base_mismatch"

    @pytest.mark.parametrize("field", pr_guard.REQUIRED_FIELDS)
    def test_a_missing_field_fails_closed(self, field):
        data = own()
        del data[field]
        assert check(data).reason == "missing_field"

    @pytest.mark.parametrize("field", pr_guard.REQUIRED_FIELDS)
    def test_a_null_field_fails_closed(self, field):
        assert check(own(**{field: None})).reason == "missing_field"

    @pytest.mark.parametrize(
        "change",
        [
            {"isCrossRepository": "false"},  # a string is not the boolean
            {"isCrossRepository": 0},
            {"number": "13275"},
            {"number": True},
            {"number": 0},
            {"headRefName": ["implementation/a/altair"]},
            {"headRefOid": 1},
            {"headRepository": {"name": None}},
            {"headRepository": "anyplot"},
            {"headRepositoryOwner": {}},
            {"author": {"login": None}},
            {"author": "app/github-actions"},
            {"baseRefName": ["main"]},
        ],
    )
    def test_a_field_of_the_wrong_type_fails_closed(self, change):
        assert check(own(**change)).reason == "missing_field"

    @pytest.mark.parametrize("data", [None, [], "implementation/a/altair", 13275])
    def test_data_that_is_not_an_object(self, data):
        assert check(data).reason == "unreadable"

    @pytest.mark.parametrize(
        "branch",
        [
            "implementation/scatter-matrix/altair/extra",  # an extra segment
            "implementation/scatter-matrix",
            "implementation//altair",
            "Implementation/scatter-matrix/altair",
            "implementation/Scatter-Matrix/altair",  # uppercase
            "implementation/scatter-matrix/Altair",
            "implementation/scatter.matrix/altair",  # a dot
            "implementation/scatter_matrix/altair",
            "implementation/-scatter/altair",  # a hyphen at an end, or two in a row
            "implementation/scatter-/altair",
            "implementation/scatter--matrix/altair",
            "implementation/../altair",  # a path segment
            "implementation/scatter-matrix/../altair",
            "implementation/scatter matrix/altair",  # whitespace and shell characters
            "implementation/scatter-matrix/altair\n",
            "implementation/$(x)/altair",
            "implementation/a;b/altair",
            "implementation/a`b`/altair",
            "implementation/scätter/altair",  # not ASCII
            "review-writeback/scatter-matrix/altair/12",  # another pipeline shape, refused here
            "specification/scatter-matrix",
            "main",
            "",
            "implementation/" + "a" * 200 + "/altair",
        ],
    )
    def test_a_branch_outside_the_contract(self, branch):
        assert check(own(headRefName=branch)).reason == "branch_shape"

    @pytest.mark.parametrize("library", ["notalib", "d", "matplotlib2", "plot"])
    def test_an_unknown_library(self, library):
        assert check(own(headRefName=f"implementation/scatter-matrix/{library}")).reason == "unknown_library"

    @pytest.mark.parametrize("sha", ["", "abc", SHA.upper(), SHA + "0", SHA[:-1] + "g", " " + SHA[1:]])
    def test_a_head_that_is_not_a_full_sha(self, sha):
        assert check(own(headRefOid=sha)).reason == "head_sha_shape"

    def test_data_for_another_number(self):
        assert check(own(), number=13276).reason == "number_mismatch"

    @pytest.mark.parametrize(("spec_id", "library"), [("scatter-basic", "altair"), ("scatter-matrix", "bokeh")])
    def test_dispatch_inputs_that_differ_from_the_branch(self, spec_id, library):
        assert check(own(), spec_id=spec_id, library=library).reason == "input_mismatch"

    def test_a_refusal_keeps_only_the_number(self):
        verdict = check(own(isCrossRepository=True))
        assert verdict == pr_guard.Verdict("cross_repository", 13275)
        assert not verdict.allowed and verdict.spec_id == verdict.library == verdict.branch == ""

    def test_the_cross_repository_check_comes_before_the_branch(self):
        """A foreign pull request is named for what it is, whatever its branch looks like."""
        assert check(own(isCrossRepository=True, headRefName="x")).reason == "cross_repository"


class TestOwnPullRequests:
    def test_keeps_the_own_and_names_the_rest(self):
        entries = [own(number=1), own(number=2, isCrossRepository=True), "junk", own(number=3)]
        kept, skipped = pr_guard.own_pull_requests(entries, repo=REPO, libraries=LIBS)
        assert [e["number"] for e in kept] == [1, 3]
        assert [(v.number, v.reason) for v in skipped] == [(2, "cross_repository"), (None, "unreadable")]


class TestCodes:
    def test_every_reason_is_a_fixed_lowercase_word(self):
        for code in pr_guard.REASONS:
            assert code.replace("_", "").isalpha() and code.islower() and len(code) <= 40

    def test_the_spec_id_shape_is_the_spec_guards(self):
        assert pr_guard.SPEC_ID_PATTERN == spec_pr_guard.SPEC_ID_RE.pattern

    def test_every_spec_in_the_catalogue_has_the_shape(self):
        plots = Path(__file__).resolve().parents[4] / "plots"
        specs = [p.name for p in plots.iterdir() if p.is_dir() and not p.name.startswith(".")]
        assert specs
        for spec in specs:
            assert pr_guard.BRANCH_RE.fullmatch(f"implementation/{spec}/altair"), spec


class TestRunnerPython:
    """The jobs stage these two files alone and run them with the runner's own python3 (3.12 on ubuntu-24.04)."""

    STAGED = [pytest.param(pr_guard, id="pr_guard"), pytest.param(sys.modules["core.constants"], id="constants")]

    @pytest.mark.parametrize("module", STAGED)
    def test_parses_as_python_3_12(self, module):
        source = Path(module.__file__).read_text(encoding="utf-8")
        ast.parse(source, feature_version=(3, 12))

    @pytest.mark.parametrize("module", STAGED)
    def test_imports_the_standard_library_only(self, module):
        """Staged alone, a file can import neither a third-party package nor a sibling of its own."""
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        names = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        assert all(n.level == 0 for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)), "relative import"
        assert names <= sys.stdlib_module_names | {"__future__"}, names


# --- the CLI, as the workflows run it -------------------------------------------------------


@pytest.fixture
def staged(tmp_path: Path) -> Path:
    """A copy of the guard alone, the way "Stage the pull request guard" leaves it."""
    target = tmp_path / "pr-guard" / "pr_guard.py"
    target.parent.mkdir()
    shutil.copyfile(pr_guard.__file__, target)
    return target


def run(staged: Path, mode: str, stdin: str, *args: str, libraries: str = " ".join(LIBS)):
    return subprocess.run(
        [sys.executable, "-I", str(staged), mode, "--repo", REPO, "--libraries", libraries, *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=staged.parent.parent,
    )


class TestCheckCli:
    def test_allowed_prints_the_checked_values_and_exits_0(self, staged):
        result = run(staged, "check", json.dumps(own()), "--number", "13275")
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [
            "number=13275",
            "spec_id=scatter-matrix",
            "library=altair",
            "branch=implementation/scatter-matrix/altair",
            f"head_sha={SHA}",
        ]

    def test_refused_prints_one_reason_line_and_exits_1(self, staged):
        result = run(staged, "check", json.dumps(own(isCrossRepository=True)), "--number", "13275")
        assert (result.returncode, result.stdout) == (1, "reason=cross_repository\n")

    def test_nothing_of_a_refused_pull_request_is_printed(self, staged):
        data = own(headRefName="implementation/x/notalib", body="text")
        result = run(staged, "check", json.dumps(data), "--number", "13275")
        assert result.stdout == "reason=unknown_library\n"
        assert "notalib" not in result.stdout + result.stderr

    @pytest.mark.parametrize("stdin", ["", "not json", "{", "[]"])
    def test_unreadable_input(self, staged, stdin):
        result = run(staged, "check", stdin, "--number", "13275")
        assert result.returncode == 1
        assert result.stdout in ("reason=unreadable\n",)

    @pytest.mark.parametrize("number", [None, "", "0", "-1", "13275 ", "#13275", "https://x/pull/1", "1" * 11])
    def test_a_bad_number_is_refused_before_the_data_is_read(self, staged, number):
        args = [] if number is None else ["--number", number]
        result = run(staged, "check", json.dumps(own()), *args)
        assert (result.returncode, result.stdout) == (1, "reason=bad_number\n")

    def test_the_dispatch_inputs_reach_the_check(self, staged):
        args = ["--number", "13275", "--spec-id", "scatter-matrix", "--library", "bokeh"]
        result = run(staged, "check", json.dumps(own()), *args)
        assert (result.returncode, result.stdout) == (1, "reason=input_mismatch\n")

    @pytest.mark.parametrize(("libraries", "repo"), [("", REPO), ("Altair", REPO), ("altair", "anyplot"), ("a", "o/")])
    def test_bad_arguments_exit_2(self, staged, libraries, repo):
        result = subprocess.run(
            [sys.executable, "-I", str(staged), "check", "--repo", repo, "--libraries", libraries, "--number", "1"],
            input=json.dumps(own()),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2 and result.stdout == "reason=guard_failed\n"

    def test_a_too_deeply_nested_document_is_unreadable(self, staged):
        result = run(staged, "check", "[" * 100_000 + "]" * 100_000, "--number", "13275")
        assert (result.returncode, result.stdout) == (1, "reason=unreadable\n")


class TestSpecIdCli:
    """As the workflows call it: the value after `--`, so one that starts with a hyphen is a value too."""

    @staticmethod
    def _run(staged: Path, value: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", str(staged), "spec-id", "--", value], capture_output=True, text=True
        )

    @pytest.mark.parametrize("value", ["scatter-basic", "a", "a1-b2-c3", "x" * 100])
    def test_a_spec_id_in_the_catalogues_shape_is_printed(self, staged, value):
        result = self._run(staged, value)
        assert (result.returncode, result.stdout) == (0, value + "\n")

    @pytest.mark.parametrize(
        "value", ["", "Scatter", "a--b", "-a", "a-", "a b", "a/b", "../a", "a\nb", "$(x)", "a;b", "x" * 101]
    )
    def test_anything_else_prints_nothing(self, staged, value):
        result = self._run(staged, value)
        assert (result.returncode, result.stdout) == (1, "")

    def test_the_workflows_pass_the_value_after_a_double_dash(self):
        workflows = Path(__file__).resolve().parents[4] / ".github" / "workflows"
        calls = [
            line
            for path in workflows.glob("*.yml")
            for line in path.read_text(encoding="utf-8").splitlines()
            if "pr_guard.py" in line and " spec-id " in line or '"$PR_GUARD" spec-id' in line
        ]
        assert calls and all("spec-id -- " in line for line in calls), calls


class TestFilterCli:
    def test_prints_the_own_and_logs_the_rest(self, staged):
        entries = [own(number=1), own(number=2, isCrossRepository=True), own(number=3, headRefName="implementation/x")]
        result = run(staged, "filter", json.dumps(entries))
        assert result.returncode == 0, result.stderr
        assert [e["number"] for e in json.loads(result.stdout)] == [1]
        assert result.stderr.splitlines() == [
            "PR #2: skipped (cross_repository), not one of the pipeline's own pull requests",
            "PR #3: skipped (branch_shape), not one of the pipeline's own pull requests",
        ]

    def test_an_empty_listing_stays_empty(self, staged):
        result = run(staged, "filter", "[]")
        assert (result.returncode, result.stdout, result.stderr) == (0, "[]\n", "")

    @pytest.mark.parametrize("stdin", ["", "{}", "not json"])
    def test_input_that_is_not_a_listing_exits_2(self, staged, stdin):
        result = run(staged, "filter", stdin)
        assert result.returncode == 2 and result.stdout == ""
