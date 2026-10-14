"""The prep eval (agents/evals/prep.py): the fixtures, the canonical operations, the score, a scripted run."""

import asyncio
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from agents.anyplot.data.generate import Generate, generate
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
    canonical_code,
    canonical_operations,
    check_cases,
    describe,
    load_cases,
    run_cases,
    verdict_of,
)
from agents.main import Runtime

from ..runtime.fakes import FakeAnthropic


OPERATIONS = (
    "rename",
    "drop_columns",
    "drop_rows",
    "set_type",
    "aggregate",
    "sort",
    "pivot_longer",
    "pivot_wider",
    "classify",
)
HOURS = "Study Hours,Exam Score\n2,55\n5,70\n8,85\n3,60\n"
RENAME = {"op": "rename", "column": "Study Hours", "name": "Hours"}
GHOST = {"op": "rename", "column": "Ghost", "name": "Spirit"}  # no such column: the tool answers unknown_column
SINE = {"name": "y", "expression": "sin(x)"}
SINE_CALL = {"variables": [{"start": "-pi", "stop": "pi"}], "series": [SINE]}
CODE_CALL = {"op": "run_data_code", "rows": 4, "columns": 2}


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

        # 23 single-step cases, 10 `hard` ones (chains, ambiguity, unsupported asks) and 11 data-code cases.
        assert len(cases) == 44
        assert sum(1 for item in cases if "hard" in item.tags) == 10
        assert locales["de"] >= 5 and locales["en"] >= 5
        assert ops == {*OPERATIONS, "generate_data", "run_data_code"}
        assert sum(1 for item in cases if not item.expected_operations) >= 2  # out of scope, and a plain question
        assert any(len(item.expected_operations) == 2 for item in cases)  # two operations in one message
        tags = Counter(tag for item in cases for tag in item.tags)
        for tag in ("percent", "decimal_comma", "date_format", "total_row", "period", "no_tool"):
            assert tags[tag] >= 1, tag
        # The formulas: a sine, a parabola with its points, a parametric circle and a grid, with and without data.
        formulas = [item for item in cases if "formula" in item.tags]
        assert len(formulas) == 4 and {item.locale for item in formulas} == {"de", "en"}
        assert tags["grid"] == 1 and tags["parametric"] == 1
        assert any(item.dataset_text is None for item in formulas) and any(item.dataset_text for item in formulas)

    def test_the_data_code_cases(self) -> None:
        """Python, NumPy, JavaScript, R and a textbook formula run; a plot call is stripped; a file read and a
        general-purpose script are refused (owner decision of 2026-10-14)."""
        cases = [item for item in load_cases(DEFAULT_CASES) if "data_code" in item.tags]
        tags = Counter(tag for item in cases for tag in item.tags)

        assert len(cases) == 11 and {item.locale for item in cases} == {"de", "en"}
        assert tags["python"] >= 3 and tags["javascript"] == tags["r"] == tags["math"] == 1
        assert tags["strip_plot"] == 1 and tags["file_access"] == 1 and tags["general_runner"] == 1
        # Described in words only, the computation decides the tool: an ODE, an iteration, random numbers.
        assert tags["words"] == 3 and tags["ode"] == tags["iteration"] == tags["random"] == 1
        refused = [item for item in cases if item.refuse]
        assert {item.id for item in refused} == {"en-code-reads-a-file", "en-code-general-script"}
        assert all(not item.expected_operations for item in refused)

    def test_every_fixture_is_consistent_with_the_operations(self) -> None:
        """The expected operations apply to the fixture's own dataset, and the dataset passes the pre-filter.

        A formula's expected call computes, and its table parses as number columns.
        """
        for item in load_cases(DEFAULT_CASES):
            parsed = parse_dataset(item.dataset_text) if item.dataset_text else None
            assert parsed is None or not instruction_like(parsed), item.id
            decimal = parsed.profile.decimal if parsed else "."
            canonical_operations(item.expected_operations, decimal)  # raises for a bad fixture
            formulas = [operation for operation in item.expected_operations if operation["op"] == "generate_data"]
            operations = [
                operation
                for operation in item.expected_operations
                if operation["op"] not in ("generate_data", "run_data_code")
            ]
            for formula in formulas:
                spec = Generate.model_validate({key: value for key, value in formula.items() if key != "op"})
                table = parse_dataset(generate(spec).csv)
                assert set(table.column_dtypes.values()) == {"number"}, item.id
            if operations:
                assert parsed is not None, item.id
                prepared = apply_operations(parsed, _operations(operations))
                assert len(prepared.changes) == len(operations), item.id
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
                {
                    "op": "classify",
                    "name": "Klasse",
                    "rules": [{"where": [{"column": "y", "test": "gt", "value": 0}], "label": "Klasse 1"}],
                    "otherwise": "Klasse 2",
                },
            ],
            ".",
        )

        assert sorted(describe(line) for line in lines) == [
            "aggregate Betrag sum by Datum/month",
            "classify Klasse: 'Klasse 1' if y gt '0'; else 'Klasse 2'",
            "drop_rows Tier eq 'Gesamt'",
            "pivot_wider p with v by m",
            "set_type share number (,)",
        ]

    def test_classify_keeps_its_rule_order_and_ignores_the_order_of_a_rules_conditions(self) -> None:
        high = {"column": "y", "test": "gt", "value": "0.5"}
        named = {"column": "x", "test": "ne", "value": "a"}

        def call(first: list[dict[str, Any]], labels: tuple[str, str]) -> list[str]:
            rules = [{"where": first, "label": labels[0]}, {"where": [high], "label": labels[1]}]
            return canonical_operations([{"op": "classify", "name": "k", "rules": rules}], ".")

        assert call([high, named], ("a", "b")) == call([named, high], ("a", "b"))
        assert call([high, named], ("a", "b")) != call([high, named], ("b", "a"))

    def test_a_generate_data_call_is_one_item_with_defaults_and_whitespace_left_out(self) -> None:
        bare = [{"op": "generate_data", "variables": [{"start": "-pi", "stop": "pi"}], "series": [SINE]}]
        written = [
            {
                "op": "generate_data",
                "variables": [{"name": "x", "start": " - pi", "stop": "pi ", "points": 200}],
                "series": [{"name": "y", "expression": "sin( x )"}],
            }
        ]

        assert canonical_operations(bare, ".") == canonical_operations(written, ".")
        (line,) = canonical_operations(bare, ".")
        assert json.loads(line) == {
            "op": "generate_data",
            "variables": [{"start": "-pi", "stop": "pi"}],
            "series": [{"name": "y", "expression": "sin(x)"}],
        }
        assert describe(line) == "generate_data x -pi..pi (200): y = sin(x)"
        # The series are a set, the variables keep their order (the first is the grid's slowest), and a JSON number
        # as an endpoint is its text.
        circle = [{"name": "x", "expression": "cos(t)"}, {"name": "y", "expression": "sin(t)"}]
        one = {"op": "generate_data", "variables": [{"name": "t", "start": 0, "stop": "2*pi"}], "series": circle}
        other = {**one, "variables": [{"name": "t", "start": "0", "stop": "2 * pi"}], "series": circle[::-1]}
        assert canonical_operations([one], ".") == canonical_operations([other], ".")
        x, y = {"name": "x", "start": "0", "stop": "1"}, {"name": "y", "start": "0", "stop": "1"}
        grid = {"op": "generate_data", "variables": [x, y], "series": [{"name": "z", "expression": "x*y"}]}
        swapped = {**grid, "variables": [y, x]}
        assert canonical_operations([grid], ".") != canonical_operations([swapped], ".")
        # A formula and an operation in one turn are two items.
        assert len(canonical_operations([*bare, RENAME], ".")) == 2
        with pytest.raises(ValidationError):
            canonical_operations([{"op": "generate_data", "variables": [], "series": [SINE]}], ".")

    def test_describe_a_code_table_without_its_size(self) -> None:
        """The fake renderer stores a fixture table, so a code call is compared without rows and columns."""
        line = canonical_code({"op": "run_data_code", "rows": 5, "columns": 2}, size=False)

        assert describe(line) == "run_data_code: a table"

    def test_a_generate_data_call_matches_by_the_table_it_computes(self) -> None:
        """Endpoints compare by value and expressions by what they compute, so an equivalent call is no miss."""

        def lines(start: Any, stop: Any, expression: str, points: int = 50, name: str = "y") -> list[str]:
            variables = [{"start": start, "stop": stop, "points": points}]
            call = {"op": "generate_data", "variables": variables, "series": [{"name": name, "expression": expression}]}
            return canonical_operations([call, RENAME], ".")

        parabola = lines("-3", "3", "x**2")
        for start, stop, expression in ((-3.0, 3.0, "x**2"), ("-3.0", "3", "x*x"), ("-3", "3", "(x)**2")):
            found = lines(start, stop, expression)
            assert found != parabola and prep.same_operations(found, parabola), (start, stop, expression)
        assert prep.same_operations(lines("0", "tau", "sin(x)"), lines("0", "pi*2", "sin(x)"))
        # Other points, another name or another formula are a miss; so is a call the server cannot compute.
        assert not prep.same_operations(lines("-3", "3", "x**2", points=51), parabola)
        assert not prep.same_operations(lines("-3", "3", "x**2", name="f"), parabola)
        assert not prep.same_operations(lines("-3", "3", "x**3"), parabola)
        undefined = lines("-3", "3", "log(-1 - x**2)")
        (formula,) = [line for line in undefined if "generate_data" in line]
        assert prep.comparison_key(formula) == formula and not prep.same_operations(undefined, parabola)
        assert prep.same_operations(undefined, undefined)


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

    def test_generate_data_calls_are_read_and_scored_like_operations(self, services: Services, swap_models) -> None:
        """A formula case may come without a dataset; a formula the server cannot compute is a miss (`failed_calls`)."""
        expected = [{"op": "generate_data", **SINE_CALL}]
        cases = [
            PrepCase(id="g-001", message="zeichne sin(x) von -pi bis pi", expected_operations=expected, locale="de"),
            case("g-002", "plot sin(x) as a new version", expected),
            PrepCase(id="g-003", message="plot log of minus one", expected_operations=expected, locale="en"),
        ]
        undefined = {"variables": SINE_CALL["variables"], "series": [{"name": "y", "expression": "log(-1 - x**2)"}]}
        root_turns = [
            [{"call": "generate_data", "args": SINE_CALL}, {"text": "Generated 200 rows; please confirm."}],
            [{"call": "generate_data", "args": SINE_CALL}, {"text": "Generated a new version."}],
            [{"call": "generate_data", "args": undefined}, {"text": "That formula has no value there."}],
        ]
        swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        in_scope = JudgeVerdict(verdict="in_scope", lang="en", input_tokens=500, output_tokens=20)
        judge.script.extend([in_scope] * 4)  # the scope judge three times, the dataset judge once (g-002)

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, True, False]
        assert results[0].found == canonical_operations(expected, ".") and results[0].tool_calls == ["generate_data"]
        assert results[2].failed_calls == 1 and results[2].found != results[2].expected
        assert "generate_data x -pi..pi (200): y = sin(x)" in prep.table(cases, results)
        assert len(judge.calls) == 4 and len(services.datasets) == 0  # every session was deleted

    def test_run_data_code_calls_are_scored_by_the_table_they_stored(self, services: Services, swap_models) -> None:
        """The code varies from run to run: a call counts as the rows and columns it stored, and a `refuse` case
        passes when nothing was stored (the fake backend's fixture table has 4 rows and 2 columns)."""
        snippet = "import numpy as np\nimport pandas as pd\nx = np.arange(4)\ndf = pd.DataFrame({'x': x, 'y': x**2})\n"
        call = {"call": "run_data_code", "args": {"code": snippet, "source_language": "python"}}
        reader = {
            "call": "run_data_code",
            "args": {"code": "import pandas as pd\ndf = pd.read_csv('f.csv')\n", "source_language": "python"},
        }
        cases = [
            PrepCase(id="c-001", message="plot my code", expected_operations=[CODE_CALL], locale="en"),
            PrepCase(id="c-002", message="plot my code", expected_operations=[{**CODE_CALL, "rows": 5}], locale="en"),
            PrepCase(id="c-003", message="read my file", expected_operations=[], locale="en", refuse=True),
            PrepCase(id="c-004", message="read my file", expected_operations=[], locale="en", refuse=True),
        ]
        root_turns = [
            [call, {"text": "Computed 4 rows; please confirm."}],
            [call, {"text": "Computed 4 rows; please confirm."}],
            [reader, {"text": "I cannot read files; paste the contents in the data panel."}],
            [call, {"text": "Computed 4 rows."}],
        ]
        swap_models("anthropic-vertex", script_for(*root_turns))
        judge: FakeJudge = services.judge  # type: ignore[assignment]
        judge.script.extend([JudgeVerdict(verdict="in_scope", lang="en")] * 8)

        results = asyncio.run(run_cases(cases, runtime=runtime(), services=services))

        assert [result.match for result in results] == [True, False, True, False]
        assert results[0].found == canonical_operations([CODE_CALL], ".") and results[0].stored_calls == 1
        assert results[2].failed_calls == 1 and results[2].stored_calls == 0
        assert "run_data_code: 4 rows x 2 columns" in prep.table(cases, results)

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
