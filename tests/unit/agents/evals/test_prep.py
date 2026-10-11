"""The prep eval (agents/evals/prep.py): the fixtures, the canonical operations, the score, a scripted run."""

import asyncio
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from agents.anyplot.data.parse import parse_dataset
from agents.anyplot.data.prepare import apply_operations
from agents.anyplot.models import FakeJudge, JudgeVerdict
from agents.anyplot.opening import instruction_like
from agents.anyplot.run_queue import RunQueue
from agents.anyplot.services import Services
from agents.evals import prep
from agents.evals.prep import (
    DEFAULT_CASES,
    EXIT_FAILED,
    EXIT_OK,
    EXIT_OUTAGE,
    EXIT_SETUP,
    CaseResult,
    Gates,
    PrepCase,
    SetupError,
    canonical_operations,
    check_cases,
    describe,
    load_cases,
    run_cases,
    verdict_of,
)
from agents.main import Runtime

from ..runtime.fakes import FakeAnthropic


OPERATIONS = ("rename", "drop_columns", "drop_rows", "set_type", "aggregate", "sort", "pivot_longer", "pivot_wider")
HOURS = "Study Hours,Exam Score\n2,55\n5,70\n8,85\n3,60\n"
RENAME = {"op": "rename", "column": "Study Hours", "name": "Hours"}
GHOST = {"op": "rename", "column": "Ghost", "name": "Spirit"}  # no such column: the tool answers unknown_column


def case(case_id: str, message: str, expected: list[dict[str, Any]], locale: str = "en", **extra: Any) -> PrepCase:
    return PrepCase(
        id=case_id, dataset_text=HOURS, message=message, expected_operations=expected, locale=locale, **extra
    )


def runtime() -> Runtime:
    return Runtime(queue=RunQueue(concurrency=1, per_minute=1_000, max_wait_s=600))


class TestFixtures:
    def test_the_set_covers_every_operation_in_both_languages(self) -> None:
        cases = load_cases(DEFAULT_CASES)
        locales = Counter(item.locale for item in cases)
        ops = {operation["op"] for item in cases for operation in item.expected_operations}

        assert len(cases) >= 12
        assert locales["de"] >= 5 and locales["en"] >= 5
        assert ops == set(OPERATIONS)
        assert sum(1 for item in cases if not item.expected_operations) >= 2  # out of scope, and a plain question
        assert any(len(item.expected_operations) == 2 for item in cases)  # two operations in one message
        tags = Counter(tag for item in cases for tag in item.tags)
        for tag in ("percent", "decimal_comma", "date_format", "total_row", "period", "no_tool"):
            assert tags[tag] >= 1, tag

    def test_every_fixture_is_consistent_with_the_operations(self) -> None:
        """The expected operations apply to the fixture's own dataset, and the dataset passes the pre-filter."""
        for item in load_cases(DEFAULT_CASES):
            parsed = parse_dataset(item.dataset_text)
            assert not instruction_like(parsed), item.id
            canonical_operations(item.expected_operations, parsed.profile.decimal)  # raises for a bad fixture
            if item.expected_operations:
                prepared = apply_operations(parsed, _operations(item.expected_operations))
                assert len(prepared.changes) == len(item.expected_operations), item.id
        check_cases(load_cases(DEFAULT_CASES))

    def test_a_bad_directory_or_fixture_is_a_setup_error(self, tmp_path: Path) -> None:
        with pytest.raises(SetupError, match="holds no case"):
            load_cases(tmp_path)
        (tmp_path / "x-001.json").write_text(json.dumps({"dataset_text": "a\n1\n", "message": "hi"}), encoding="utf-8")
        with pytest.raises(SetupError, match="does not load"):
            load_cases(tmp_path)
        bad = case("bad-001", "do it", [{"op": "explode"}])
        with pytest.raises(SetupError, match="do not validate"):
            check_cases([bad])


def _operations(items: list[dict[str, Any]]) -> Any:
    from pydantic import TypeAdapter

    from agents.anyplot.data.prepare import Operation

    return TypeAdapter(list[Operation]).validate_python(items)


class TestCanonical:
    def test_defaults_written_or_left_out_are_the_same(self) -> None:
        bare = [{"op": "sort", "column": "a"}, {"op": "pivot_longer", "columns": ["b", "a"]}]
        written = [
            {"op": "pivot_longer", "columns": ["a", "b"], "names_to": "series", "values_to": "value"},
            {"op": "sort", "column": "a", "descending": False},
        ]

        assert canonical_operations(bare, ".") == canonical_operations(written, ".")

    def test_the_datasets_own_decimal_counts_as_left_out(self) -> None:
        explicit = [{"op": "set_type", "column": "p", "type": "number", "decimal": ","}]
        implicit = [{"op": "set_type", "column": "p", "type": "number"}]

        assert canonical_operations(explicit, ",") == canonical_operations(implicit, ",")
        assert canonical_operations(explicit, ".") != canonical_operations(implicit, ".")

    def test_conditions_and_column_lists_are_sets(self) -> None:
        one = [
            {
                "op": "drop_rows",
                "where": [{"column": "a", "test": "gt", "value": "1"}, {"column": "b", "test": "is_missing"}],
            }
        ]
        other = [
            {
                "op": "drop_rows",
                "where": [{"column": "b", "test": "is_missing"}, {"column": "a", "test": "gt", "value": "1"}],
            }
        ]

        assert canonical_operations(one, ".") == canonical_operations(other, ".")
        assert canonical_operations([{"op": "drop_columns", "columns": ["b", "a"]}], ".") == canonical_operations(
            [{"op": "drop_columns", "columns": ["a", "b"]}], "."
        )
        # The keys of an aggregate keep their order: `by` decides the sort of the result.
        assert canonical_operations([{"op": "aggregate", "by": ["a", "b"], "column": "v", "how": "sum"}], ".") != (
            canonical_operations([{"op": "aggregate", "by": ["b", "a"], "column": "v", "how": "sum"}], ".")
        )

    def test_an_invalid_operation_raises(self) -> None:
        with pytest.raises(ValidationError):
            canonical_operations([{"op": "rename", "column": "a"}], ".")

    def test_describe(self) -> None:
        lines = canonical_operations(
            [
                {"op": "aggregate", "by": ["Datum"], "column": "Betrag", "how": "sum", "period": "month"},
                {"op": "drop_rows", "where": [{"column": "Tier", "test": "eq", "value": "Gesamt"}]},
                {"op": "set_type", "column": "share", "type": "number", "decimal": ","},
                {"op": "pivot_wider", "names_from": "p", "values_from": "v", "index": ["m"]},
            ],
            ".",
        )

        assert sorted(describe(line) for line in lines) == [
            "aggregate Betrag sum by Datum/month",
            "drop_rows Tier eq 'Gesamt'",
            "pivot_wider p with v by m",
            "set_type share number (,)",
        ]


class TestScore:
    CASES = [
        case("a-001", "rename it", [RENAME]),
        case("a-002", "write an email", [], "de", tags=["no_tool"]),
        case("a-003", "sort it", [{"op": "sort", "column": "Exam Score"}]),
    ]

    def test_matches_misses_and_unavailable(self) -> None:
        expected = [canonical_operations(item.expected_operations, ".") for item in self.CASES]
        results = [
            CaseResult("a-001", [RENAME], expected[0], expected[0], True),
            CaseResult("a-002", [], expected[1], [], True, refusal="out_of_scope"),
            CaseResult("a-003", None, expected[2], cause="error: capacity"),
        ]

        scored = prep.score(self.CASES, results)

        assert scored["summary"]["matched"] == 2 and scored["summary"]["exact"] == 1.0
        assert scored["summary"]["unavailable"] == 1 and scored["unavailable_causes"] == {"error: capacity": 1}
        assert scored["per_tag"]["de"]["matched"] == 1 and scored["per_tag"]["no_tool"]["cases"] == 1
        assert verdict_of(scored["summary"], Gates())[0] == EXIT_OUTAGE  # 1 of 3 is over 10 percent
        assert verdict_of(scored["summary"], Gates(max_unavailable=0.5)) == (EXIT_OK, [])

        results[2] = CaseResult("a-003", [RENAME], expected[2], expected[0], False)
        summary = prep.score(self.CASES, results)["summary"]
        assert summary["exact"] == pytest.approx(2 / 3, abs=1e-4)  # rates are rounded to four digits
        code, reasons = verdict_of(summary, Gates())
        assert code == EXIT_FAILED and "below 0.8" in reasons[0]
        assert "miss" in prep.table(self.CASES, results)


def script_for(*answers: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {"root": [item for turn in answers for item in turn], "adapter": [], "reviewer": []}


class TestRun:
    def test_a_scripted_run_reads_the_tool_calls_from_the_session(self, services: Services, swap_models) -> None:
        cases = [
            case("r-001", "rename the hours", [RENAME]),
            case("r-002", "write an email", [], "de", tags=["no_tool"]),
            case("r-003", "sort it", [{"op": "sort", "column": "Exam Score"}]),
            case("r-004", "which column is x?", []),
            case("r-005", "rename the ghost", [GHOST]),
        ]
        root_turns = [
            [{"call": "prepare_data", "args": {"operations": [RENAME]}}, {"text": "Renamed; please confirm."}],
            [],  # refused by the judge before the root
            [
                {
                    "call": "prepare_data",
                    "args": {"operations": [{"op": "sort", "column": "Exam Score", "descending": True}]},
                },
                {"text": "Sorted."},
            ],
            [{"call": "get_dataset_profile", "args": {}}, {"text": "Study Hours is on x."}],
            # The expected list, but the data refuses it (no such column): a miss, not a match.
            [{"call": "prepare_data", "args": {"operations": [GHOST]}}, {"text": "There is no such column."}],
        ]
        fake: FakeAnthropic = swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        in_scope = JudgeVerdict(verdict="in_scope", lang="en", input_tokens=500, output_tokens=20)
        judge.script.extend([in_scope, in_scope, in_scope, JudgeVerdict(verdict="out_of_scope", lang="de"), in_scope])

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, False, True, False]
        assert results[4].found == results[4].expected and results[4].failed_calls == 1
        assert results[0].found == canonical_operations([RENAME], ".") and results[0].llm_calls == 2
        assert results[0].tool_calls == ["prepare_data"] and results[0].cost_usd > 0
        assert results[1].refusal == "out_of_scope" and results[1].tool_calls == [] and results[1].llm_calls == 0
        assert results[2].found == canonical_operations(
            [{"op": "sort", "column": "Exam Score", "descending": True}], "."
        )
        assert results[3].tool_calls == ["get_dataset_profile"] and results[3].found == []
        assert len(fake.calls) == 8
        assert len(services.datasets) == 0  # every session was deleted

    def test_an_error_event_is_an_unavailable_case(self, services: Services, swap_models) -> None:
        swap_models("anthropic-vertex", script_for([]))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        judge.script.extend([JudgeVerdict(verdict="in_scope"), TimeoutError(), TimeoutError()])

        (result,) = asyncio.run(run_cases([case("r-001", "rename it", [RENAME])], runtime=runtime(), services=services))

        assert result.operations is None and result.match is None
        assert result.cause == "error: guard_unavailable"


class TestMain:
    @pytest.fixture(autouse=True)
    def _environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`configure` writes into the process environment; the monkeypatch restores every key it touches."""
        for key, value in (
            ("PYTHON_DOTENV_DISABLED", "1"),
            ("ADK_DISABLE_LOAD_DOTENV", "1"),
            ("AGENT_RENDERER", "fake"),
            ("AGENT_RUNS_PER_MINUTE", "60"),
            ("AGENT_GLOBAL_DAILY_TOKEN_BUDGET", "1000000"),
        ):
            monkeypatch.setenv(key, value)

    def test_a_passing_run_writes_its_report(
        self, tmp_path: Path, services: Services, swap_models, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cases_dir = tmp_path / "cases"
        cases_dir.mkdir()
        for item in (case("m-001", "rename the hours", [RENAME]), case("m-002", "which column?", [])):
            data = item.model_dump(exclude={"id"})
            (cases_dir / f"{item.id}.json").write_text(json.dumps(data), encoding="utf-8")
        swap_models(
            "anthropic-vertex",
            script_for(
                [{"call": "prepare_data", "args": {"operations": [RENAME]}}, {"text": "Done; confirm please."}],
                [{"text": "Study Hours."}],
            ),
        )

        code = prep.main(
            ["--cases", str(cases_dir), "--out", str(tmp_path / "out"), "--calls-per-minute", "0"],
            runtime=runtime(),
            services=services,
        )

        assert code == EXIT_OK
        (path,) = (tmp_path / "out").glob("*-prep-claude-haiku-5-5.json")
        report = json.loads(path.read_text(encoding="utf-8"))
        assert report["passed"] is True and report["summary"]["exact"] == 1.0 and report["stamp"]["cases"] == 2
        assert report["stamp"]["root_prompt_hash"] and len(report["results"]) == 2
        assert "rename the hours" not in path.read_text(encoding="utf-8")  # the messages stay in the fixtures
        out = capsys.readouterr().out
        assert "rename Study Hours to Hours" in out and "PASS" in out
        assert os.environ["AGENT_RENDERER"] == "fake"

    def test_setup_errors(self, tmp_path: Path, services: Services) -> None:
        assert (
            prep.main(["--cases", str(tmp_path / "missing"), "--out", str(tmp_path)], services=services) == EXIT_SETUP
        )
        assert prep.main(["--cases", str(DEFAULT_CASES), "--tags", "nothing"], services=services) == EXIT_SETUP

    def test_the_pacer_spaces_cases_by_the_calls_a_case_makes(self) -> None:
        args = prep.parse_args([])
        assert args.calls_per_minute == 25 and prep.CALLS_PER_CASE == 5
        with pytest.raises(SystemExit):
            prep.parse_args(["--min-exact", "2"])
