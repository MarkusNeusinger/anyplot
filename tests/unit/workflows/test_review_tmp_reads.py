"""The reviewer's reads under /tmp, and the step that names a refused tool call.

A regeneration's review re-scores the predecessor from files impl-review.yml
puts directly under /tmp: its renders, its review without the scores, its
source with the score hidden. The session reads them through one permission
rule. In Claude Code's rule syntax a path with ONE leading slash anchors where
its settings file is (the project, or the directory of a file passed with
`--settings`), and only TWO name the filesystem root. With the single-slash
form the read was refused; a review that treated the files as missing wrote no
`review_regen.json`, and the gate kept the live implementation
(`regen_json_missing`).

Three things are pinned here:

- both settings files (production and the retest) carry the absolute form,
  narrowed to the pipeline's own file names (`anyplot-*`);
- every file a prompt points a session at is one the rule covers, a direct
  child of /tmp with such a name, or is on a short list of files that are
  reached another way; and every /tmp file a step leaves there before
  the review is on an exact list, which has no file that carries the stored
  score as a field (the PR's JSON, main's metadata, the unsanitized source);
- "Name the denied tool calls" prints the count and one line per refused
  call, under `bash -e` and `bash -eo pipefail`, and never fails the job.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.unit.workflows.test_pipeline_retry_gaps import _step, _steps
from tests.unit.workflows.test_render_hash_steps import SHELL_IDS, SHELLS


ROOT = Path(__file__).resolve().parents[3]
SETTINGS = [ROOT / ".claude" / "settings.json", ROOT / "automation" / "retest" / "claude-settings.json"]
SETTINGS_IDS = ["production", "retest"]
WORKFLOW = ROOT / ".github" / "workflows" / "impl-review.yml"
PROMPT = ROOT / "prompts" / "workflow-prompts" / "ai-quality-review.md"
RULE = "Read(//tmp/anyplot-*)"
PROMPTS = ROOT / "prompts" / "workflow-prompts"
REVIEW = "Run AI Quality Review"
STEP = "Name the denied tool calls"
SUMMARY = "Claude session summary"
TMP_PATH = re.compile(r"/tmp/[A-Za-z0-9._${}/-]+")

# Every file a step puts directly under /tmp before the review session starts, and why the session may read it.
# None carries the stored score as a field. (The previous review's own wording can still quote a score, for
# example "minor at 95/100": --omit-scores drops the numbers, not the prose.) A new name here is a decision,
# not a formality: a file here whose name starts with `anyplot-` is one the reviewer's Read tool opens.
BEFORE_THE_REVIEW = {
    "/tmp/anyplot-prev-plot-light.png": "the predecessor's render, which the review re-scores",
    "/tmp/anyplot-prev-plot-dark.png": "the predecessor's render, which the review re-scores",
    "/tmp/anyplot-prev-review.md": "the previous review, written with --omit-scores",
    "/tmp/anyplot-prev-weaknesses.json": "its weakness ids, from the same call",
    "/tmp/anyplot-prev-impl${EXT}": "the predecessor's source after sanitize-source",
    "/tmp/anyplot-prev-impl.py": "the same file, as the adaptability check names it",
    "/tmp/anyplot-change-request.txt": "the change request from the PR body",
    "/tmp/anyplot-canvas-gate.txt": "the canvas gate's message",
    "/tmp/anyplot-adapt-new.json": "the adaptability record of the new file: statuses, no score",
    "/tmp/anyplot-adapt-prev.json": "the adaptability record of the predecessor: statuses, no score",
    "/tmp/anyplot-regen-gate.py": "the gate script the prompt's self-check calls",
    "/tmp/clear-label.err": "stderr of a label call",
    "/tmp/regen-labels.err": "stderr of a label read",
    "/tmp/gsutil.err": "stderr of the render download",
    "/tmp/gsutil-prev.err": "stderr of the predecessor's render download",
}


def _rules(path: Path) -> list[str]:
    permissions = json.loads(path.read_text(encoding="utf-8"))["permissions"]
    return [rule for key in ("allow", "ask", "deny") for rule in permissions.get(key, [])]


# --- the rule ---------------------------------------------------------------


@pytest.mark.parametrize("path", SETTINGS, ids=SETTINGS_IDS)
def test_the_read_rule_names_the_filesystems_tmp(path):
    assert RULE in json.loads(path.read_text(encoding="utf-8"))["permissions"]["allow"]


@pytest.mark.parametrize("path", SETTINGS, ids=SETTINGS_IDS)
def test_no_rule_writes_tmp_with_one_leading_slash(path):
    """`Read(/tmp/*)` looks absolute and is anchored at its settings file: it covers nothing the workflow writes."""
    not_absolute = [rule for rule in _rules(path) if re.match(r"^[A-Za-z]+\(/tmp\b", rule)]
    assert not_absolute == []


def test_the_workflow_comment_gives_the_rule_as_the_settings_hold_it():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert f"`{RULE}`" in text
    assert "`/tmp/*` only" not in text  # the wording that took the single-slash rule for the absolute one


# --- what the rule reaches ---------------------------------------------------


def _prompted_tmp_paths() -> set[str]:
    """Every /tmp path the reviewer is told about: the review prompt, and the step that hands over the renders."""
    paths = set(TMP_PATH.findall(PROMPT.read_text(encoding="utf-8")))
    renders = str(_step("impl-review.yml", "Download previous production renders (regen)")["run"])
    paths |= {p for p in TMP_PATH.findall(renders) if p.endswith(".png")}
    return {p.rstrip(".") for p in paths}


def _tmp_paths_before_the_review() -> set[str]:
    """Every /tmp path in the script or the environment of a step that runs before the review session."""
    steps = _steps("impl-review.yml")
    before = steps[: [s.get("name") for s in steps].index(REVIEW)]
    found: set[str] = set()
    for step in before:
        text = "\n".join([str(step.get("run", "")), *(str(value) for value in (step.get("env") or {}).values())])
        code = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))  # not the comments
        found |= {p.rstrip(".") for p in TMP_PATH.findall(code)}
    return found


def test_the_reviewer_is_pointed_at_the_predecessors_files():
    paths = _prompted_tmp_paths()
    for expected in (
        "/tmp/anyplot-prev-plot-light.png",
        "/tmp/anyplot-prev-plot-dark.png",
        "/tmp/anyplot-prev-review.md",
        "/tmp/anyplot-prev-impl${EXT}",
    ):
        assert expected in paths, expected


def _covered(path: str) -> bool:
    """What `Read(//tmp/anyplot-*)` allows: a direct child of /tmp whose name starts with `anyplot-`."""
    name = path.removeprefix("/tmp/")
    return path.startswith("/tmp/") and "/" not in name and name.startswith("anyplot-")


# The /tmp paths a workflow prompt names that the rule does not cover, and what they are. The Read tool is
# refused them, as it was before the rule had its absolute form.
OUTSIDE_THE_RULE = {
    "/tmp/ai_feedback.md": "the review a repair works from",
    "/tmp/change-requests.json": "the similarity audit's own output, which it writes",
    "/tmp/anyplot-prev-src/{LIBRARY}.py": "the predecessor's source for the generator's smoke run, read by a script",
    "/tmp/anyplot-readiness/automation/scripts/readiness_scan.py": (
        "the agent chat's validator copy that the generator and the repair run for their readiness check, never read"
    ),
}


def test_every_file_the_reviewer_is_pointed_at_is_one_the_rule_covers():
    """The rule's `*` matches one path segment and the name is fixed: any other file would be refused again."""
    assert len(_prompted_tmp_paths()) >= 6  # the search finds them at all
    assert sorted(p for p in _prompted_tmp_paths() if not _covered(p)) == []


def test_a_prompt_names_no_tmp_path_outside_the_rule_unnoticed():
    """A new hand-over file with another name would be refused in silence; the list makes it a decision."""
    named = {p.rstrip(".") for prompt in PROMPTS.glob("*.md") for p in TMP_PATH.findall(prompt.read_text("utf-8"))}
    assert any(_covered(p) for p in named)
    assert {p for p in named if not _covered(p)} == set(OUTSIDE_THE_RULE)


@pytest.mark.parametrize(
    ("path", "covered"),
    [
        ("/tmp/anyplot-prev-plot-light.png", True),
        ("/tmp/anyplot-prev-impl${EXT}", True),
        ("/tmp/anyplot-prev-src/matplotlib.py", False),
        ("/tmp/pr.json", False),
        ("/tmp/gsutil.err", False),
        ("/home/runner/work/_temp/anyplot-prev-metadata.yaml", False),
    ],
)
def test_the_reach_of_the_rule_as_these_tests_read_it(path, covered):
    assert _covered(path) is covered


def test_every_tmp_file_before_the_review_is_one_the_reviewer_may_open():
    """What a step leaves under /tmp, the Read rule reaches. The list is exact, so a new file is a decision."""
    assert _tmp_paths_before_the_review() == set(BEFORE_THE_REVIEW)
    # Whatever the prompt points at is on the list too: nothing is handed over that this test does not see.
    assert {p for p in _prompted_tmp_paths() if "anyplot-prev-" in p} <= set(BEFORE_THE_REVIEW)


def test_no_step_before_the_review_builds_a_tmp_path_the_list_cannot_see():
    """The exact list reads literal `/tmp/<name>` paths. A path made another way would pass it unseen."""
    steps = _steps("impl-review.yml")
    before = steps[: [s.get("name") for s in steps].index(REVIEW)]
    hidden = re.compile(r"mktemp|TMPDIR|tempfile|/tmp(?![/A-Za-z0-9._-])|/tmp/[\"']|/tmp/\$")
    for step in before:
        values = [str(step.get("run", "")), *map(str, (step.get("env") or {}).values())]
        values += [str(value) for value in (step.get("with") or {}).values()]
        code = [line for value in values for line in value.splitlines() if not line.lstrip().startswith("#")]
        found = [line.strip() for line in code if hidden.search(line)]
        assert found == [], step.get("name")


def test_the_files_that_carry_the_stored_score_stay_out_of_tmp():
    """Three carry it as such: main's metadata, the predecessor's raw source, and the PR's JSON with its body."""
    text = WORKFLOW.read_text(encoding="utf-8")
    for name in ("anyplot-prev-metadata.yaml", "anyplot-prev-impl-raw", "pr.json", "pr.err"):
        assert f"/tmp/{name}" not in text, name
    context = str(_step("impl-review.yml", "Regen context")["run"])
    assert 'PREV_META="$RUNNER_TEMP/anyplot-prev-metadata.yaml"' in context
    assert 'echo "{}" > "$PREV_META"' in context and '--metadata "$PREV_META"' in context
    assert 'RAW="$RUNNER_TEMP/anyplot-prev-impl-raw"' in context
    assert 'git show "origin/main:${IMPL_FILE}" > "$RAW"' in context
    assert '--source "$RAW" --out "/tmp/anyplot-prev-impl${EXT}"' in context
    assert "--omit-scores" in context
    info = str(_step("impl-review.yml", "Extract PR info")["run"])
    assert '> "$RUNNER_TEMP/pr.json" 2> "$RUNNER_TEMP/pr.err"' in info
    assert 'PR_DATA=$(cat "$RUNNER_TEMP/pr.json")' in info
    assert "anyplot-prev-metadata" not in PROMPT.read_text(encoding="utf-8")


# --- the step ---------------------------------------------------------------


def _result(denials: Any = None, **extra: Any) -> list[dict[str, Any]]:
    result: dict[str, Any] = {"type": "result", "subtype": "success", "is_error": False, **extra}
    if denials is not None:
        result["permission_denials"] = denials
    return [{"type": "system", "subtype": "init", "model": "claude-opus-5-5"}, result]


def _denied(tool: Any, **tool_input: Any) -> dict[str, Any]:
    return {"tool_name": tool, "tool_use_id": "toolu_x", "tool_input": tool_input}


READS = [
    _denied("Read", file_path="/tmp/anyplot-prev-plot-light.png"),
    _denied("Read", file_path="/tmp/anyplot-prev-plot-dark.png"),
]
WHERE = "step=impl-review spec=bar-basic lib=d3 pr=7"


def _run(tmp_path: Path, shell: list[str], execution: Any, *, raw: str | bytes | None = None, **env: str):
    step = _step("impl-review.yml", STEP)
    exec_file = tmp_path / "claude-execution-output.json"
    if isinstance(raw, bytes):
        exec_file.write_bytes(raw)
    elif raw is not None:
        exec_file.write_text(raw, encoding="utf-8")
    elif execution is not None:
        exec_file.write_text(json.dumps(execution), encoding="utf-8")
    summary = tmp_path / "summary"
    full_env = {
        **os.environ,
        "EXECUTION_FILE": str(exec_file) if exec_file.exists() else "",
        "CLAUDE_STEP": "impl-review",
        "SPEC_ID": "bar-basic",
        "LIBRARY": "d3",
        "PR_NUM": "7",
        "GITHUB_STEP_SUMMARY": str(summary),
        "GITHUB_OUTPUT": str(tmp_path / "out"),
        **env,
    }
    result = subprocess.run([*shell, step["run"]], env=full_env, capture_output=True, text=True, timeout=60)
    return result, summary.read_text(encoding="utf-8") if summary.exists() else ""


def _calls(result: subprocess.CompletedProcess) -> list[str]:
    """The part of each warning after the run's labels."""
    lines = result.stdout.splitlines()[1:]
    assert all(line.startswith(f"::warning::claude_denied {WHERE} ") for line in lines), lines
    return [line.removeprefix(f"::warning::claude_denied {WHERE} ") for line in lines]


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestNameTheDeniedToolCalls:
    def test_refused_reads_are_counted_and_named(self, tmp_path, shell):
        result, summary = _run(tmp_path, shell, _result(READS))
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [
            f"::notice::claude_denials {WHERE} count=2",
            f"::warning::claude_denied {WHERE} tool=Read path=/tmp/anyplot-prev-plot-light.png",
            f"::warning::claude_denied {WHERE} tool=Read path=/tmp/anyplot-prev-plot-dark.png",
        ]
        assert summary == f"- `claude_denials {WHERE} count=2`\n"
        assert result.stderr == ""

    def test_a_session_without_a_refusal_prints_the_count_alone(self, tmp_path, shell):
        result, summary = _run(tmp_path, shell, _result([]))
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [f"::notice::claude_denials {WHERE} count=0"]
        assert summary == f"- `claude_denials {WHERE} count=0`\n"

    def test_only_a_file_tools_path_is_printed(self, tmp_path, shell):
        """A command, a URL, a prompt or the argument of a tool outside the list can hold anything."""
        denials = [
            _denied("Bash", command="curl -H 'Authorization: Bearer hunter2' https://example.org"),
            _denied("WebFetch", url="https://example.org/?token=hunter2", prompt="read it", path="hunter2"),
            _denied("mcp__files__open", path="/x?token=hunter2", file_path="https://h/q?key=hunter2"),
            _denied("read", file_path="/tmp/hunter2"),  # not the tool's name
            _denied("Grep", pattern="hunter2", path="/home/runner/work/_temp"),
            _denied("Glob", pattern="/tmp/hunter2*", path="/tmp"),
            _denied("NotebookEdit", notebook_path="/tmp/a.ipynb", new_source="hunter2"),
            _denied("Edit", file_path="/tmp/b.py", old_string="hunter2", new_string="hunter2"),
        ]
        result, _ = _run(tmp_path, shell, _result(denials))
        assert result.returncode == 0, result.stderr
        assert "hunter2" not in result.stdout + result.stderr
        assert _calls(result) == [
            "tool=Bash path=-",
            "tool=WebFetch path=-",
            "tool=mcp__files__open path=-",
            "tool=read path=-",
            "tool=Grep path=/home/runner/work/_temp",
            "tool=Glob path=/tmp",
            "tool=NotebookEdit path=/tmp/a.ipynb",
            "tool=Edit path=/tmp/b.py",
        ]

    def test_a_path_cannot_start_a_workflow_command_or_a_second_line(self, tmp_path, shell):
        hostile = "/tmp/x\n::error::forged\r%0A::add-mask::y `id` $(id)  \x00" + "a" * 400
        result, _ = _run(tmp_path, shell, _result([_denied("Read", file_path=hostile)]))
        assert result.returncode == 0, result.stderr
        (call,) = _calls(result)
        assert re.fullmatch(r"tool=Read path=[A-Za-z0-9_./@+=~?-]{200}", call), call
        assert call.startswith("tool=Read path=/tmp/x???error??forged??0A??add-mask??y??id?")

    def test_a_tool_name_cannot_either(self, tmp_path, shell):
        result, _ = _run(tmp_path, shell, _result([_denied("Re ad\n::notice::t%0A" + "b" * 400, file_path="/tmp/x")]))
        assert result.returncode == 0, result.stderr
        (call,) = _calls(result)
        assert re.fullmatch(r"tool=[A-Za-z0-9_.?-]{60} path=-", call), call
        assert call.startswith("tool=Re?ad???notice??t?0A")

    def test_the_runs_labels_are_cut_the_same_way(self, tmp_path, shell):
        result, summary = _run(tmp_path, shell, _result([]), SPEC_ID="a\n::error::b", LIBRARY="d3`id`", PR_NUM="7 8")
        assert result.returncode == 0, result.stderr
        expected = "claude_denials step=impl-review spec=a???error??b lib=d3?id? pr=7?8 count=0"
        assert result.stdout.splitlines() == [f"::notice::{expected}"]
        assert summary == f"- `{expected}`\n"

    def test_a_huge_value_costs_nothing_and_is_cut(self, tmp_path, shell):
        denials = [_denied("Read", file_path="$" * 2_000_000), _denied("x" * 2_000_000, file_path="/tmp/y")]
        result, _ = _run(tmp_path, shell, _result(denials))  # _run gives the step 60 s; it needs well under one
        assert result.returncode == 0, result.stderr
        assert _calls(result) == ["tool=Read path=" + "?" * 200, "tool=" + "x" * 60 + " path=-"]

    def test_every_counted_call_gets_its_line_whatever_its_shape(self, tmp_path, shell):
        denials = [
            {"tool_name": None, "tool_input": None},
            {"tool_input": "a string"},
            {},
            "a string",
            7,
            None,
            ["a", "list"],
            _denied("Read"),
            _denied("Read", file_path=""),
            _denied("Read", file_path=None, path=False, notebook_path="/tmp/n.ipynb"),
            # Only a string is a path or a name: nothing else is turned into text.
            _denied("Read", file_path=0),
            _denied("Read", file_path={"a": "hunter2"}),
            _denied("Read", file_path=["/tmp/hunter2"]),
            _denied(False, file_path="/tmp/z"),
            _denied(404, file_path="/tmp/z"),
            _denied("", file_path="/tmp/z"),
        ]
        result, _ = _run(tmp_path, shell, _result(denials))
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines()[0] == f"::notice::claude_denials {WHERE} count={len(denials)}"
        assert "hunter2" not in result.stdout
        assert _calls(result) == [
            *["tool=? path=-"] * 7,
            "tool=Read path=-",
            "tool=Read path=-",
            "tool=Read path=/tmp/n.ipynb",
            *["tool=Read path=-"] * 3,
            *["tool=? path=-"] * 3,
        ]

    def test_a_value_nested_past_any_depth_never_ends_the_step(self, tmp_path, shell):
        """Whether the parser takes the file or not depends on the Python: either way every line is printed."""
        deep = "[" * 60_000 + "]" * 60_000
        raw = json.dumps(_result([_denied("Read", file_path="MARK"), READS[0]])).replace('"MARK"', deep)
        result, _ = _run(tmp_path, shell, None, raw=raw)
        assert result.returncode == 0, result.stderr
        assert result.stderr == ""
        lines = result.stdout.splitlines()
        if lines[0].endswith("count=n/a"):
            assert len(lines) == 1
        else:
            assert lines[0] == f"::notice::claude_denials {WHERE} count=2"
            assert _calls(result) == ["tool=Read path=-", "tool=Read path=/tmp/anyplot-prev-plot-light.png"]

    @pytest.mark.parametrize("summary", ["a-directory", "missing/folder/summary", ""])
    def test_a_summary_that_cannot_be_written_drops_no_line(self, tmp_path, shell, summary):
        (tmp_path / "a-directory").mkdir()
        target = str(tmp_path / summary) if summary else ""
        result, _ = _run(tmp_path, shell, _result(READS), GITHUB_STEP_SUMMARY=target)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines()[0] == f"::notice::claude_denials {WHERE} count=2"
        assert len(_calls(result)) == 2

    def test_an_unpaired_surrogate_elsewhere_in_the_file_hides_nothing(self, tmp_path, shell):
        """`JSON.stringify` writes one as an escape, which jq refuses for the whole file."""
        raw = json.dumps(_result(READS[:1])).replace(
            '"type": "system"', '"note": "cut \\ud83d here", "type": "system"', 1
        )
        assert "\\ud83d" in raw
        result, _ = _run(tmp_path, shell, None, raw=raw)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [
            f"::notice::claude_denials {WHERE} count=1",
            f"::warning::claude_denied {WHERE} tool=Read path=/tmp/anyplot-prev-plot-light.png",
        ]

    def test_a_surrogate_inside_a_path_is_cut_like_any_other_character(self, tmp_path, shell):
        raw = json.dumps(_result([_denied("Read", file_path="/tmp/MARK/x")])).replace("MARK", "\\ud83d")
        result, _ = _run(tmp_path, shell, None, raw=raw)
        assert result.returncode == 0, result.stderr
        assert _calls(result) == ["tool=Read path=/tmp/?/x"]

    @pytest.mark.parametrize(
        ("execution", "raw"),
        [
            (None, None),  # the action wrote no execution file
            (None, "not json"),
            (None, ""),
            (None, b"\xff\xfe\x00["),  # not UTF-8
            (None, "[" * 100_000),  # deeper than the parser goes
            (_result(None), None),  # a result without the field
            (_result({"count": 2}), None),  # the field in another shape
            (_result("two"), None),
            ([{"type": "system", "subtype": "init"}], None),  # a session without a result
            ({"type": "result", "permission_denials": READS}, None),  # not a list of messages
            (["result", 7, None], None),
        ],
        ids=[
            "no-file",
            "not-json",
            "empty",
            "not-utf8",
            "too-deep",
            "no-field",
            "field-an-object",
            "field-a-string",
            "no-result",
            "top-level-object",
            "no-objects",
        ],
    )
    def test_a_session_that_leaves_no_list_is_counted_as_unknown(self, tmp_path, shell, execution, raw):
        result, summary = _run(tmp_path, shell, execution, raw=raw)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [f"::notice::claude_denials {WHERE} count=n/a"]
        assert summary == f"- `claude_denials {WHERE} count=n/a`\n"

    def test_the_last_result_is_the_one_that_counts(self, tmp_path, shell):
        later = {"type": "result", "subtype": "success", "permission_denials": [_denied("Read", file_path="/tmp/l")]}
        result, _ = _run(tmp_path, shell, [*_result(READS), later])
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [
            f"::notice::claude_denials {WHERE} count=1",
            f"::warning::claude_denied {WHERE} tool=Read path=/tmp/l",
        ]


def test_the_step_records_and_decides_nothing():
    step = _step("impl-review.yml", STEP)
    assert step["continue-on-error"] is True
    assert step["timeout-minutes"] == 2
    assert "id" not in step  # without an id no later step can read it
    script = str(step["run"])
    assert "GITHUB_OUTPUT" not in script and "exit 1" not in script and "sys.exit" not in script
    assert step["env"]["EXECUTION_FILE"] == "${{ steps.review.outputs.execution_file }}"
    assert step["env"]["CLAUDE_STEP"] == _step("impl-review.yml", SUMMARY)["env"]["CLAUDE_STEP"]


def test_the_step_runs_whenever_the_session_summary_runs():
    assert _step("impl-review.yml", STEP)["if"] == _step("impl-review.yml", SUMMARY)["if"]
    names = [s.get("name") for s in _steps("impl-review.yml")]
    assert names.index(SUMMARY) < names.index(STEP) < names.index("Extract quality score")
