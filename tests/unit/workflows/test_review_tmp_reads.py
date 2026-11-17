"""The reviewer's reads under /tmp, and the step that names a refused tool call.

A regeneration's review re-scores the predecessor from files impl-review.yml
puts directly under /tmp: its renders, its review without the scores, its
source with the score hidden. The session reads them through one permission
rule. In Claude Code's rule syntax a path with ONE leading slash anchors at
the project (`<project>/tmp/*`), and only TWO name the filesystem root. With
the single-slash form every such read was refused; a review that did not find
another way took the prompt's `PREV_RENDERS = missing` path, wrote no
`review_regen.json`, and the gate kept the live implementation
(`regen_json_missing`).

Three things are pinned here:

- both settings files (production and the retest) carry the absolute form;
- every file the reviewer is pointed at is a direct child of /tmp, which is
  all the rule's `*` covers, and the predecessor's metadata, which holds the
  stored score, is not among the files the rule reaches;
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
RULE = "Read(//tmp/*)"
STEP = "Name the denied tool calls"
SUMMARY = "Claude session summary"
TMP_PATH = re.compile(r"/tmp/[A-Za-z0-9._${}/-]+")


def _rules(path: Path) -> list[str]:
    permissions = json.loads(path.read_text(encoding="utf-8"))["permissions"]
    return [rule for key in ("allow", "ask", "deny") for rule in permissions.get(key, [])]


# --- the rule ---------------------------------------------------------------


@pytest.mark.parametrize("path", SETTINGS, ids=SETTINGS_IDS)
def test_the_read_rule_names_the_filesystems_tmp(path):
    assert RULE in json.loads(path.read_text(encoding="utf-8"))["permissions"]["allow"]


@pytest.mark.parametrize("path", SETTINGS, ids=SETTINGS_IDS)
def test_no_rule_writes_tmp_with_one_leading_slash(path):
    """`Read(/tmp/*)` looks absolute and is `<project>/tmp/*`: it covers nothing the workflow writes."""
    anchored_at_the_project = [rule for rule in _rules(path) if re.match(r"^[A-Za-z]+\(/tmp\b", rule)]
    assert anchored_at_the_project == []


def test_the_workflow_comment_gives_the_rule_as_the_settings_hold_it():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "`Read(//tmp/*)`" in text
    assert "`/tmp/*` only" not in text  # the wording that took the single-slash rule for the absolute one


# --- what the rule reaches ---------------------------------------------------


def _prompted_tmp_paths() -> set[str]:
    """Every /tmp path the reviewer is told about: the review prompt, and the step that hands over the renders."""
    paths = set(TMP_PATH.findall(PROMPT.read_text(encoding="utf-8")))
    renders = str(_step("impl-review.yml", "Download previous production renders (regen)")["run"])
    paths |= {p for p in TMP_PATH.findall(renders) if p.endswith(".png")}
    return {p.rstrip(".") for p in paths}


def test_the_reviewer_is_pointed_at_the_predecessors_files():
    paths = _prompted_tmp_paths()
    for expected in (
        "/tmp/anyplot-prev-plot-light.png",
        "/tmp/anyplot-prev-plot-dark.png",
        "/tmp/anyplot-prev-review.md",
        "/tmp/anyplot-prev-impl${EXT}",
    ):
        assert expected in paths, expected


def test_every_file_the_reviewer_is_pointed_at_is_a_direct_child_of_tmp():
    """The rule's `*` matches one path segment: a file in a folder under /tmp would be refused again."""
    nested = sorted(p for p in _prompted_tmp_paths() if "/" in p.removeprefix("/tmp/"))
    assert nested == []


def test_the_stored_score_stays_out_of_the_reviewers_reach():
    """Main's metadata holds the stored score. The reviewer gets the review without it, never the file."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "/tmp/anyplot-prev-metadata.yaml" not in text
    context = str(_step("impl-review.yml", "Regen context")["run"])
    assert 'PREV_META="$RUNNER_TEMP/anyplot-prev-metadata.yaml"' in context
    assert "--omit-scores" in context
    assert "anyplot-prev-metadata" not in PROMPT.read_text(encoding="utf-8")
    # The predecessor's source with its header (and so its score) goes before the step ends.
    assert context.index("sanitize-source") < context.index("rm -f /tmp/anyplot-prev-impl-raw")


# --- the step ---------------------------------------------------------------


def _result(denials: Any = None, **extra: Any) -> list[dict[str, Any]]:
    result: dict[str, Any] = {"type": "result", "subtype": "success", "is_error": False, **extra}
    if denials is not None:
        result["permission_denials"] = denials
    return [{"type": "system", "subtype": "init", "model": "claude-opus-5-5"}, result]


def _denied(tool: str, **tool_input: Any) -> dict[str, Any]:
    return {"tool_name": tool, "tool_use_id": "toolu_x", "tool_input": tool_input}


READS = [
    _denied("Read", file_path="/tmp/anyplot-prev-plot-light.png"),
    _denied("Read", file_path="/tmp/anyplot-prev-plot-dark.png"),
]


def _run(tmp_path: Path, shell: list[str], execution: Any, *, raw: str | None = None):
    step = _step("impl-review.yml", STEP)
    exec_file = tmp_path / "claude-execution-output.json"
    if raw is not None:
        exec_file.write_text(raw, encoding="utf-8")
    elif execution is not None:
        exec_file.write_text(json.dumps(execution), encoding="utf-8")
    summary = tmp_path / "summary"
    env = {
        **os.environ,
        "EXECUTION_FILE": str(exec_file) if (execution is not None or raw is not None) else "",
        "CLAUDE_STEP": "impl-review",
        "SPEC_ID": "bar-basic",
        "LIBRARY": "d3",
        "PR_NUM": "7",
        "DENIAL_COUNT": step["env"]["DENIAL_COUNT"],
        "DENIAL_LINES": step["env"]["DENIAL_LINES"],
        "GITHUB_STEP_SUMMARY": str(summary),
        "GITHUB_OUTPUT": str(tmp_path / "out"),
    }
    result = subprocess.run([*shell, step["run"]], env=env, capture_output=True, text=True)
    return result, summary.read_text(encoding="utf-8") if summary.exists() else ""


@pytest.mark.parametrize("shell", SHELLS, ids=SHELL_IDS)
class TestNameTheDeniedToolCalls:
    def test_refused_reads_are_counted_and_named(self, tmp_path, shell):
        result, summary = _run(tmp_path, shell, _result(READS))
        assert result.returncode == 0, result.stderr
        lines = result.stdout.splitlines()
        assert lines == [
            "::notice::claude_denials step=impl-review spec=bar-basic lib=d3 pr=7 count=2",
            "::warning::claude_denied step=impl-review spec=bar-basic lib=d3 pr=7"
            " tool=Read path=/tmp/anyplot-prev-plot-light.png",
            "::warning::claude_denied step=impl-review spec=bar-basic lib=d3 pr=7"
            " tool=Read path=/tmp/anyplot-prev-plot-dark.png",
        ]
        assert summary == "- `claude_denials step=impl-review spec=bar-basic lib=d3 pr=7 count=2`\n"

    def test_a_session_without_a_refusal_prints_the_count_alone(self, tmp_path, shell):
        result, summary = _run(tmp_path, shell, _result([]))
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [
            "::notice::claude_denials step=impl-review spec=bar-basic lib=d3 pr=7 count=0"
        ]
        assert "count=0" in summary

    def test_only_a_file_tools_path_is_printed(self, tmp_path, shell):
        """A command, a URL or a prompt can hold anything; the log gets the tool's name and no input."""
        denials = [
            _denied("Bash", command="curl -H 'Authorization: Bearer hunter2' https://example.org"),
            _denied("WebFetch", url="https://example.org/?token=hunter2", prompt="read it"),
            _denied("Grep", pattern="hunter2", path="/home/runner/work/_temp"),
            _denied("NotebookEdit", notebook_path="/tmp/a.ipynb", new_source="hunter2"),
        ]
        result, _ = _run(tmp_path, shell, _result(denials))
        assert result.returncode == 0, result.stderr
        assert "hunter2" not in result.stdout + result.stderr
        assert [line.split(" pr=7 ", 1)[1] for line in result.stdout.splitlines()[1:]] == [
            "tool=Bash path=-",
            "tool=WebFetch path=-",
            "tool=Grep path=/home/runner/work/_temp",
            "tool=NotebookEdit path=/tmp/a.ipynb",
        ]

    def test_a_path_cannot_start_a_workflow_command_or_a_second_line(self, tmp_path, shell):
        hostile = "/tmp/x\n::error::forged\r%0A::add-mask::y `id` $(id) " + "a" * 400
        result, _ = _run(tmp_path, shell, _result([_denied("Re ad\n::notice::t", file_path=hostile)]))
        assert result.returncode == 0, result.stderr
        lines = result.stdout.splitlines()
        assert len(lines) == 2
        call = lines[1].split(" pr=7 ", 1)[1]
        assert re.fullmatch(r"tool=[A-Za-z0-9_.?-]{1,60} path=[A-Za-z0-9_./@+=~?-]{1,200}", call), call
        assert "::" not in call and "%" not in call and "$" not in call and "`" not in call
        assert call.startswith("tool=Re?ad???notice??t path=/tmp/x???error??forged")

    def test_odd_shapes_never_fail_the_step(self, tmp_path, shell):
        denials = [{"tool_name": None, "tool_input": None}, {"tool_input": "a string"}, {}, _denied("Read")]
        result, _ = _run(tmp_path, shell, _result(denials))
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines()[0].endswith("count=4")
        assert [line.split(" pr=7 ", 1)[1] for line in result.stdout.splitlines()[1:]] == ["tool=? path=-"] * 3 + [
            "tool=Read path=-"
        ]

    @pytest.mark.parametrize(
        ("execution", "raw"),
        [
            (None, None),  # the action wrote no execution file
            (None, "not json"),
            (None, ""),
            (_result(None), None),  # a result without the field
            (_result({"count": 2}), None),  # the field in another shape
            ([{"type": "system", "subtype": "init"}], None),  # a session without a result
        ],
        ids=["no-file", "not-json", "empty", "no-field", "not-a-list", "no-result"],
    )
    def test_an_unreadable_session_is_counted_as_unknown(self, tmp_path, shell, execution, raw):
        result, summary = _run(tmp_path, shell, execution, raw=raw)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == [
            "::notice::claude_denials step=impl-review spec=bar-basic lib=d3 pr=7 count=n/a"
        ]
        assert "count=n/a" in summary

    def test_the_last_result_is_the_one_that_counts(self, tmp_path, shell):
        execution = [*_result(READS), {"type": "result", "subtype": "success", "permission_denials": []}]
        result, _ = _run(tmp_path, shell, execution)
        assert result.stdout.splitlines()[0].endswith("count=0")


def test_the_step_records_and_decides_nothing():
    step = _step("impl-review.yml", STEP)
    assert step["continue-on-error"] is True
    assert "id" not in step  # without an id no later step can read it
    script = str(step["run"])
    assert "GITHUB_OUTPUT" not in script and "exit 1" not in script
    assert step["env"]["EXECUTION_FILE"] == "${{ steps.review.outputs.execution_file }}"
    assert step["env"]["CLAUDE_STEP"] == _step("impl-review.yml", SUMMARY)["env"]["CLAUDE_STEP"]


def test_the_step_runs_whenever_the_session_summary_runs():
    assert _step("impl-review.yml", STEP)["if"] == _step("impl-review.yml", SUMMARY)["if"]
    names = [s.get("name") for s in _steps("impl-review.yml")]
    assert names.index(SUMMARY) < names.index(STEP) < names.index("Extract quality score")
