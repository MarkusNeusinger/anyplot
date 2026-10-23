"""automation/scripts/adapt_record.py: impl-review's adapt records, one per side of a Python pair.

The record format is the interface to the regen gate (`regen_gate.py adapt-route` and
`decide --adapt-new/--adapt-prev`), so the tests pin the derived status table, the
fields the gate reads, the notice line, and the two copies the module shares with
other code: `code_sha256` with `core.smoke_run` and `RULE_ORDER` with `core.adaptability`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from automation.scripts import adapt_record as ar
from automation.scripts import regen_gate
from core import adaptability, smoke_run


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
SCRIPT = REPO_ROOT / "automation" / "scripts" / "adapt_record.py"
MIRROR = REPO_ROOT / "automation" / "scripts" / "adaptability_check.py"
FIXTURE = REPO_ROOT / "tests" / "unit" / "core" / "fixtures" / "adaptability" / "bar_grouped_matplotlib.py"
CATALOGUE = REPO_ROOT / "plots" / "bar-grouped" / "implementations" / "python" / "matplotlib.py"
SPEC = REPO_ROOT / "plots" / "bar-grouped" / "specification.md"
SOURCE = '"""anyplot.ai\nbar-grouped: Grouped Bar Chart\nQuality: pending | Created: 2026-10-23\n"""\n\nimport os\n'
STATIC_PASS = {
    "version": 1,
    "status": "pass",
    "shape": "table",
    "color_role": "group",
    "block": {"start": 31, "end": 40},
    "constants": {"category": "QUARTER", "group": "PRODUCT_LINE", "value": "SALES"},
    "findings": [{"rule": 4, "class": "data-coordinate", "line": 77, "observed": "o", "cause": "c", "advisory": True}],
    "lines": ["CQ-01 (code): (advisory) line 77 ..."],
}


def _reference_sha(text: str) -> str:
    """Contract section 1.1, verbatim: the rule core.smoke_run implements."""
    body = text.lstrip()
    if body.startswith('"""'):
        end = body.find('"""', 3)
        if end != -1:
            body = body[end + 3 :]
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


RESULT_PASS = {
    "name": "renamed",
    "description": "d",
    "advisory": False,
    "status": "pass",
    "rows": 12,
    "theme": None,
    "error": None,
    "line": None,
    "code": None,
    "canvas": {},
    "stale_labels": [],
    "seconds": 4.2,
}
RESULT_ADVISORY_FAIL = {
    **RESULT_PASS,
    "name": "missing_nullable",
    "advisory": True,
    "status": "fail",
    "theme": "light",
    "error": "TypeError: boolean value of NA is ambiguous",
    "line": 58,
    "code": "if gaps[tie] <= NEAR_TIE * top:",
    "canvas": None,
    "seconds": 1.9,
}


def _smoke(source_text: str, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "v": 1,
        "tool": "core.smoke_run run",
        "code_sha256": ar.code_sha256(source_text),
        "spec": "bar-grouped",
        "library": "matplotlib",
        "status": "pass",
        "why": "-",
        "results": [RESULT_PASS, RESULT_ADVISORY_FAIL],
        "failed": [],
        "advisory_failed": ["missing_nullable"],
    }
    data.update(overrides)
    return data


def _write(path: Path, data: Any) -> Path:
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def _record(
    tmp_path: Path,
    *,
    side: str = "new",
    static: Any = STATIC_PASS,
    exit_code: int = 0,
    smoke: Any = None,
    selfcheck: str | None = None,
    source: str | None = SOURCE,
) -> dict[str, Any]:
    src = tmp_path / "matplotlib.py"
    if source is not None:
        src.write_text(source, encoding="utf-8")
    return ar.build_record(
        side=side,
        spec="bar-grouped",
        lib="matplotlib",
        language="python",
        source=src,
        static=_write(tmp_path / "static.json", static) if static is not None else tmp_path / "absent.json",
        static_exit=exit_code,
        smoke=_write(tmp_path / "smoke.json", smoke) if smoke is not None else tmp_path / "absent-smoke.json",
        selfcheck=_write(tmp_path / "selfcheck.jsonl", selfcheck) if selfcheck is not None else None,
    )


class TestSharedCopies:
    @pytest.mark.parametrize(
        "text",
        [
            SOURCE,
            '\n\n  """anyplot.ai\nQuality: 91/100 | Updated: 2026-10-24\n"""\nx = 1\n',
            "x = 1\n",
            '"""unterminated header\nx = 1\n',
            "",
            '"""a"""',
        ],
    )
    def test_code_sha256_is_the_contracts_rule(self, text):
        assert ar.code_sha256(text) == _reference_sha(text)

    def test_the_header_does_not_count(self):
        reviewed = SOURCE.replace("Quality: pending | Created: 2026-10-23", "Quality: 94/100 | Updated: 2026-10-24")
        assert ar.code_sha256(reviewed) == ar.code_sha256(SOURCE)
        assert ar.code_sha256(SOURCE + "x = 1\n") != ar.code_sha256(SOURCE)

    def test_code_sha256_matches_core_smoke_run(self):
        """The staged smoke runs carry core.smoke_run's hash; a drift would make every one stale."""
        smoke_run = pytest.importorskip("core.smoke_run", reason="core.smoke_run arrives with PR 2 part B")
        for text in (SOURCE, CATALOGUE.read_text(encoding="utf-8"), "x = 1\n", ""):
            assert ar.code_sha256(text) == smoke_run.code_sha256(text)

    def test_rule_order_is_the_checkers(self):
        assert ar.RULE_ORDER == adaptability.RULE_ORDER

    def test_selfcheck_skip_prefixes_are_core_smoke_runs(self):
        """The first-attempt pass rate agrees with selfcheck's exit code."""
        assert ar.SELFCHECK_SKIP_PREFIXES == smoke_run.SELFCHECK_SKIP_PREFIXES

    def test_the_gates_derivation_is_derive_status(self):
        """The gate rejects a record whose status does not follow from its blocks, by this very table."""
        assert ar.SMOKE_NOT_APPLICABLE == regen_gate.ADAPT_SMOKE_NOT_APPLICABLE
        statics = (*ar.STATIC_STATUSES, "error", "weird")
        smokes = (*ar.STAGED_SMOKE_STATUSES, "missing", "stale", "weird")
        whys = ("-", "shape:generated", "shape:network", "shape:excluded", "no_perturbations:table", "runner_error")
        for static in statics:
            for smoke in smokes:
                for why in whys:
                    expected = ar.derive_status(static, smoke, why)[0]
                    assert regen_gate.derived_adapt_status(static, smoke, why) == expected, (static, smoke, why)


class TestDerivedStatus:
    @pytest.mark.parametrize(
        ("static", "smoke", "why", "expected"),
        [
            ("error", "pass", "-", ("unknown", "static_error")),
            ("excluded", "missing", "-", ("excluded", "excluded")),
            ("fail", "pass", "-", ("fail", "static_fail")),
            ("fail", "missing", "-", ("fail", "static_fail")),
            ("pass", "missing", "-", ("unknown", "smoke_missing")),
            ("pass", "stale", "-", ("unknown", "smoke_stale")),
            ("pass", "fail", "perturbation_failed", ("fail", "smoke_fail")),
            ("pass", "skipped", "shape:generated", ("pass", "smoke_na")),
            ("pass", "skipped", "shape:network", ("pass", "smoke_na")),
            ("pass", "skipped", "shape:excluded", ("unknown", "smoke_skipped")),
            ("pass", "skipped", "runner_error", ("unknown", "smoke_skipped")),
            ("pass", "skipped", "no_block", ("unknown", "smoke_skipped")),
            # The sample gave nothing to perturb: the smoke run checked nothing.
            ("pass", "skipped", "no_perturbations:table", ("unknown", "smoke_skipped")),
            ("pass", "pass", "-", ("pass", "-")),
        ],
    )
    def test_first_matching_rule_wins(self, static, smoke, why, expected):
        assert ar.derive_status(static, smoke, why) == expected


class TestStatic:
    def test_the_mirrors_record_verbatim_plus_exit(self, tmp_path):
        record = _record(tmp_path, smoke=_smoke(SOURCE))
        assert record["static"] == {**STATIC_PASS, "exit": 0}
        assert record["checker_version"] == 1

    @pytest.mark.parametrize(
        ("static", "exit_code"),
        [
            (None, 2),  # unreadable input: the mirror writes nothing
            (None, 1),  # a crash before --out
            (None, 0),
            ("{not json", 0),
            ({"status": "maybe"}, 0),
            (["pass"], 0),
            (STATIC_PASS, 2),  # a file the mirror did not write this time
        ],
    )
    def test_anything_else_is_an_error(self, tmp_path, static, exit_code):
        record = _record(tmp_path, static=static, exit_code=exit_code, smoke=_smoke(SOURCE))
        assert record["static"] == {"status": "error", "exit": exit_code}
        assert (record["status"], record["why"]) == ("unknown", "static_error")
        assert record["checker_version"] is None


class TestSmoke:
    def test_a_fresh_run_is_trimmed(self, tmp_path):
        smoke = _record(tmp_path, smoke=_smoke(SOURCE))["smoke"]
        assert smoke == {
            "status": "pass",
            "why": "-",
            "fresh": True,
            "failed": [],
            "advisory_failed": ["missing_nullable"],
            "results": [
                {"name": "renamed", "status": "pass", "advisory": False, "line": None, "error": None},
                {
                    "name": "missing_nullable",
                    "status": "fail",
                    "advisory": True,
                    "line": 58,
                    "error": "TypeError: boolean value of NA is ambiguous",
                },
            ],
        }

    @pytest.mark.parametrize("smoke", [None, "{not json", ["pass"], {"status": "error"}, {"code_sha256": "x"}])
    def test_no_usable_file_is_missing(self, tmp_path, smoke):
        record = _record(tmp_path, smoke=smoke)
        assert record["smoke"]["status"] == "missing"
        assert record["smoke"]["fresh"] is None
        assert (record["status"], record["why"]) == ("unknown", "smoke_missing")

    @pytest.mark.parametrize("sha", ["0" * 64, None, 7])
    def test_a_run_on_other_code_is_stale(self, tmp_path, sha):
        record = _record(tmp_path, smoke=_smoke(SOURCE, code_sha256=sha, status="fail", failed=["renamed"]))
        assert record["smoke"] == {
            "status": "stale",
            "why": "-",
            "fresh": False,
            "failed": [],
            "advisory_failed": [],
            "results": [],
        }
        assert (record["status"], record["why"]) == ("unknown", "smoke_stale")

    def test_an_unreadable_source_makes_any_run_stale(self, tmp_path):
        record = _record(tmp_path, smoke=_smoke(SOURCE), source=None)
        assert record["smoke"]["status"] == "stale"
        assert record["lines"] is None and record["code_sha256"] is None

    def test_the_header_rewrite_after_the_smoke_run_is_not_stale(self, tmp_path):
        reviewed = SOURCE.replace("Quality: pending", "Quality: 91/100")
        record = _record(tmp_path, smoke=_smoke(SOURCE), source=reviewed)
        assert record["smoke"]["fresh"] is True

    def test_untrusted_values_are_reduced_to_tokens(self, tmp_path):
        """The generation runner had a model shell: nothing from the file reaches a notice unfiltered."""
        evil = "x\n::error::forged"
        smoke = _smoke(
            SOURCE,
            status="fail",
            why=evil,
            failed=["renamed", evil, 3, "more_categories"],
            advisory_failed=evil,
            results=[{"name": evil, "status": "fail", "advisory": "yes", "line": True, "error": "a\n" * 400}, "junk"],
        )
        record = _record(tmp_path, smoke=smoke)
        assert record["smoke"]["why"] == "-"
        assert record["smoke"]["failed"] == ["renamed", "more_categories"]
        assert record["smoke"]["advisory_failed"] == []
        (result,) = record["smoke"]["results"]
        assert result["name"] == "-" and result["advisory"] is False and result["line"] is None
        assert "\n" not in result["error"] and len(result["error"]) == ar.MAX_ERROR_CHARS
        notice = ar.notice_line(record)
        assert "\n" not in notice and "forged" not in notice


class TestSelfcheck:
    def test_attempts_and_the_first_outcome(self, tmp_path):
        log = "\n".join(
            json.dumps(line)
            for line in (
                {"attempt": 1, "static": "fail", "classes": ["palette"], "smoke": "pass"},
                {"attempt": 2, "static": "pass", "classes": [], "smoke": "pass"},
            )
        )
        assert _record(tmp_path, smoke=_smoke(SOURCE), selfcheck=log + "\n")["selfcheck"] == {
            "attempts": 2,
            "first": "fail",
        }

    @pytest.mark.parametrize(
        ("static", "smoke", "first"),
        [("pass", "pass", "pass"), ("excluded", "skipped", "pass"), ("pass", "fail", "fail"), ("fail", "pass", "fail")],
    )
    def test_a_first_attempt_passes_like_selfchecks_exit_0(self, tmp_path, static, smoke, first):
        log = json.dumps({"attempt": 1, "static": static, "smoke": smoke})
        assert _record(tmp_path, selfcheck=log)["selfcheck"] == {"attempts": 1, "first": first}

    @pytest.mark.parametrize(
        ("smoke", "smoke_why", "first"),
        [
            ("skipped", "shape:generated", "pass"),
            ("skipped", "no_perturbations:table", "pass"),  # selfcheck exits 0 on it too
            ("skipped", "runner_error", "fail"),
            ("skipped", "no_block", "fail"),
            ("pass", "-", "pass"),
        ],
    )
    def test_a_skip_passes_only_for_the_shape(self, tmp_path, smoke, smoke_why, first):
        log = json.dumps({"attempt": 1, "static": "pass", "smoke": smoke, "smoke_why": smoke_why})
        assert _record(tmp_path, selfcheck=log)["selfcheck"] == {"attempts": 1, "first": first}

    @pytest.mark.parametrize("log", [None, "", "garbage\n[1]\n"])
    def test_no_log_is_null(self, tmp_path, log):
        assert _record(tmp_path, selfcheck=log)["selfcheck"] is None

    def test_garbage_lines_are_not_attempts(self, tmp_path):
        log = 'oops\n{"static": "pass", "smoke": "pass"}\n\n'
        assert _record(tmp_path, selfcheck=log)["selfcheck"] == {"attempts": 1, "first": "pass"}

    def test_the_prev_side_has_no_selfcheck(self, tmp_path):
        record = _record(tmp_path, side="prev", selfcheck='{"static": "pass", "smoke": "pass"}')
        assert "selfcheck" not in record


class TestRecord:
    def test_the_fields_the_gate_reads(self, tmp_path):
        record = _record(tmp_path, smoke=_smoke(SOURCE))
        assert record["v"] == 1
        assert (record["side"], record["spec"], record["lib"], record["language"]) == (
            "new",
            "bar-grouped",
            "matplotlib",
            "python",
        )
        assert record["checker_version"] == 1
        assert record["status"] in ar.STATUSES
        assert record["static"]["status"] == "pass"
        assert record["smoke"]["status"] == "pass"
        assert record["lines"] == len(SOURCE.splitlines())
        assert record["code_sha256"] == ar.code_sha256(SOURCE)
        assert list(record) == [
            "v",
            "side",
            "spec",
            "lib",
            "language",
            "checker_version",
            "status",
            "why",
            "lines",
            "code_sha256",
            "static",
            "smoke",
            "selfcheck",
        ]
        json.dumps(record)  # serializable as it stands

    def test_the_contract_example(self, tmp_path):
        record = _record(
            tmp_path,
            smoke=_smoke(SOURCE),
            selfcheck='{"static": "fail", "smoke": "pass"}\n{"static": "pass", "smoke": "pass"}\n',
        )
        assert (record["status"], record["why"]) == ("pass", "-")
        assert ar.notice_line(record) == (
            "::notice::adapt_check spec=bar-grouped lib=matplotlib side=new status=pass static=pass smoke=pass "
            "rules=- advisory=data-coordinate perturbations=- advisory_perturbations=missing_nullable version=1 "
            f"lines={len(SOURCE.splitlines())} selfcheck_attempts=2 selfcheck_first=fail why=-"
        )

    def test_a_failing_predecessor(self, tmp_path):
        static = {
            **STATIC_PASS,
            "status": "fail",
            "findings": [
                {"rule": 5, "class": "palette", "line": 9, "observed": "o", "cause": "c", "advisory": False},
                {"rule": 1, "class": "layout", "line": 40, "observed": "o", "cause": "c", "advisory": False},
                {"rule": 3, "class": "interface", "line": 47, "observed": "o", "cause": "c", "advisory": False},
                {"rule": 3, "class": "interface", "line": 52, "observed": "o", "cause": "c", "advisory": False},
                {"rule": 2, "class": "columns", "line": 25, "observed": "o", "cause": "c", "advisory": False},
                {"rule": 9, "class": "unknown", "line": 1, "observed": "o", "cause": "c", "advisory": False},
            ],
        }
        smoke = _smoke(SOURCE, status="skipped", why="static_failed", results=[], advisory_failed=[])
        record = _record(tmp_path, side="prev", static=static, exit_code=1, smoke=smoke)
        assert (record["status"], record["why"]) == ("fail", "static_fail")
        assert ar.notice_line(record) == (
            "::notice::adapt_check spec=bar-grouped lib=matplotlib side=prev status=fail static=fail smoke=skipped "
            "rules=layout,columns,interface,palette advisory=- perturbations=- advisory_perturbations=- version=1 "
            f"lines={len(SOURCE.splitlines())} why=static_fail"
        )

    @pytest.mark.parametrize("prev_smoke", [None, "stale"])
    def test_a_static_only_regression_reaches_the_gate(self, tmp_path, prev_smoke):
        """A predecessor without a fresh smoke run that passes the static check, a new file that fails it.

        The predecessor's record is `unknown` and keeps `static.status: pass`; the gate reads that as a
        certain regression without any smoke run.
        """
        (tmp_path / "prev").mkdir()
        (tmp_path / "new").mkdir()
        smoke = _smoke("other code") if prev_smoke == "stale" else None
        prev = _record(tmp_path / "prev", side="prev", smoke=smoke)
        why = f"smoke_{prev_smoke or 'missing'}"
        assert (prev["status"], prev["why"], prev["static"]["status"]) == ("unknown", why, "pass")
        static_fail = {**STATIC_PASS, "status": "fail"}
        new = _record(tmp_path / "new", static=static_fail, exit_code=1, smoke=_smoke(SOURCE))
        assert (new["status"], new["static"]["status"]) == ("fail", "fail")
        inp = regen_gate.GateInput(
            spec_id="bar-grouped",
            score=None,
            regen=None,
            adapt=regen_gate.AdaptInput(
                library="matplotlib", language="python", new=new, prev=prev, new_error=None, prev_error=None
            ),
        )
        assessed = regen_gate.adapt_assess(inp, None)
        assert (assessed.regression, assessed.static_regression) == (True, True)

    def test_a_record_without_any_input(self, tmp_path):
        record = _record(tmp_path, static=None, exit_code=2, source=None)
        assert (record["status"], record["why"]) == ("unknown", "static_error")
        assert ar.notice_line(record).endswith(
            "static=error smoke=missing rules=- advisory=- perturbations=- advisory_perturbations=- version=n/a "
            "lines=n/a selfcheck_attempts=n/a selfcheck_first=n/a why=static_error"
        )


class TestCli:
    def _args(self, tmp_path: Path, out: Path, *extra: str) -> list[str]:
        src = tmp_path / "matplotlib.py"
        src.write_text(SOURCE, encoding="utf-8")
        _write(tmp_path / "static.json", STATIC_PASS)
        _write(tmp_path / "smoke.json", _smoke(SOURCE))
        return [
            "record",
            "--side",
            "new",
            "--spec",
            "bar-grouped",
            "--lib",
            "matplotlib",
            "--language",
            "python",
            "--source",
            str(src),
            "--static",
            str(tmp_path / "static.json"),
            "--static-exit",
            "0",
            "--smoke",
            str(tmp_path / "smoke.json"),
            "--out",
            str(out),
            *extra,
        ]

    def test_writes_the_record_and_prints_the_notice(self, tmp_path, capsys):
        out = tmp_path / "anyplot-adapt-new.json"
        assert ar.main(self._args(tmp_path, out)) == 0
        record = json.loads(out.read_text(encoding="utf-8"))
        assert record["status"] == "pass" and record["selfcheck"] is None
        assert capsys.readouterr().out.strip() == ar.notice_line(record)

    def test_an_unwritable_record_exits_1(self, tmp_path, capsys):
        assert ar.main(self._args(tmp_path, tmp_path / "no" / "such" / "dir.json")) == 1
        assert "::warning::adapt record (new) not written" in capsys.readouterr().out

    def test_a_usage_error_exits_2(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            ar.main(self._args(tmp_path, tmp_path / "r.json", "--side", "both"))
        assert exc.value.code == 2

    def test_runs_as_a_script_without_the_package(self, tmp_path):
        """The workflow runs its regen-tools copy, where `automation` is not importable."""
        tools = tmp_path / "regen-tools"
        tools.mkdir()
        (tools / "adapt_record.py").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
        out = tmp_path / "r.json"
        result = subprocess.run(
            [sys.executable, "-I", str(tools / "adapt_record.py"), *self._args(tmp_path, out)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.startswith("::notice::adapt_check spec=bar-grouped lib=matplotlib side=new status=pass ")

    def test_imports_only_the_standard_library(self):
        import ast

        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        modules = {
            alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
        } | {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        assert modules <= set(sys.stdlib_module_names) | {"__future__"}


class TestWithTheMirror:
    """The mirror's real --out file is what the record builder reads."""

    @pytest.mark.parametrize(
        ("source", "exit_code", "status", "why"), [(FIXTURE, 0, "pass", "-"), (CATALOGUE, 1, "fail", "static_fail")]
    )
    def test_a_converted_and_an_unconverted_file(self, tmp_path, source, exit_code, status, why):
        src = tmp_path / "matplotlib.py"  # the checker infers the library from the stem
        src.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        static = tmp_path / "static.json"
        command = [sys.executable, "-I", str(MIRROR), "check", str(src)]
        command += ["--spec", str(SPEC), "--spec-id", "bar-grouped", "--out", str(static)]
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode == exit_code, result.stdout + result.stderr
        record = ar.build_record(
            side="new",
            spec="bar-grouped",
            lib="matplotlib",
            language="python",
            source=src,
            static=static,
            static_exit=result.returncode,
            smoke=_write(tmp_path / "smoke.json", _smoke(src.read_text(encoding="utf-8"), advisory_failed=[])),
        )
        assert (record["status"], record["why"]) == (status, why)
        assert record["static"]["status"] == ("pass" if exit_code == 0 else "fail")
        if status == "fail":
            assert "rules=layout,columns,interface" in ar.notice_line(record)
