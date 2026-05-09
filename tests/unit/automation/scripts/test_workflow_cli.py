"""Tests for automation.scripts.workflow_cli module."""

import argparse
import json
import sys
from io import StringIO
from unittest.mock import patch

import pytest

from automation.scripts.workflow_cli import (
    cmd_extract_branch,
    cmd_extract_parent_issue,
    cmd_extract_sub_issue,
    cmd_get_attempt_count,
    cmd_quality_label,
    cmd_status_transition,
    main,
)


def run_cmd(func, **kwargs) -> tuple[int, str]:
    """Run a CLI command function and capture its output."""
    args = argparse.Namespace(**kwargs)
    captured = StringIO()
    with patch("sys.stdout", captured):
        code = func(args)
    return code, captured.getvalue().strip()


class TestExtractBranch:
    """Tests for extract-branch command."""

    def test_valid_auto_branch(self):
        code, output = run_cmd(cmd_extract_branch, branch="auto/scatter-basic/matplotlib")
        assert code == 0
        data = json.loads(output)
        assert data["spec_id"] == "scatter-basic"
        assert data["library"] == "matplotlib"
        assert data["is_auto_branch"] is True

    def test_valid_auto_branch_different_spec(self):
        code, output = run_cmd(cmd_extract_branch, branch="auto/heatmap-basic/seaborn")
        assert code == 0
        data = json.loads(output)
        assert data["spec_id"] == "heatmap-basic"
        assert data["library"] == "seaborn"
        assert data["is_auto_branch"] is True

    def test_invalid_branch(self):
        code, output = run_cmd(cmd_extract_branch, branch="feature/something")
        assert code == 1
        assert output == "null"

    def test_main_branch(self):
        code, output = run_cmd(cmd_extract_branch, branch="main")
        assert code == 1
        assert output == "null"


class TestExtractSubIssue:
    """Tests for extract-sub-issue command."""

    def test_with_sub_issue(self):
        code, output = run_cmd(cmd_extract_sub_issue, pr_body="Sub-Issue: #42")
        assert code == 0
        assert output == "42"

    def test_with_sub_issue_different_format(self):
        code, output = run_cmd(cmd_extract_sub_issue, pr_body="Sub-Issue: #123\nMore text")
        assert code == 0
        assert output == "123"

    def test_without_sub_issue(self):
        code, output = run_cmd(cmd_extract_sub_issue, pr_body="No sub-issue here")
        assert code == 1
        assert output == ""

    def test_empty_body(self):
        code, output = run_cmd(cmd_extract_sub_issue, pr_body="")
        assert code == 1
        assert output == ""


class TestExtractParentIssue:
    """Tests for extract-parent-issue command."""

    def test_from_pr_body(self):
        code, output = run_cmd(cmd_extract_parent_issue, pr_body="Parent Issue: #99\nSome text", issue_body=None)
        assert code == 0
        assert output == "99"

    def test_from_issue_body_fallback(self):
        code, output = run_cmd(cmd_extract_parent_issue, pr_body="No parent here", issue_body="Parent Issue: #77")
        assert code == 0
        assert output == "77"

    def test_not_found(self):
        code, output = run_cmd(cmd_extract_parent_issue, pr_body="Nothing", issue_body="Also nothing")
        assert code == 1
        assert output == ""

    def test_both_none(self):
        code, output = run_cmd(cmd_extract_parent_issue, pr_body="", issue_body=None)
        assert code == 1
        assert output == ""


class TestGetAttemptCount:
    """Tests for get-attempt-count command."""

    def test_with_attempt_labels(self):
        code, output = run_cmd(cmd_get_attempt_count, labels="ai-attempt-2,library:matplotlib")
        assert code == 0
        assert output == "2"

    def test_with_attempt_1(self):
        code, output = run_cmd(cmd_get_attempt_count, labels="ai-attempt-1")
        assert code == 0
        assert output == "1"

    def test_with_attempt_3(self):
        code, output = run_cmd(cmd_get_attempt_count, labels="testing,ai-attempt-3,done")
        assert code == 0
        assert output == "3"

    def test_without_attempt_labels(self):
        code, output = run_cmd(cmd_get_attempt_count, labels="library:matplotlib,testing")
        assert code == 0
        assert output == "0"

    def test_empty_labels(self):
        code, output = run_cmd(cmd_get_attempt_count, labels="")
        assert code == 0
        assert output == "0"


class TestStatusTransition:
    """Tests for status-transition command."""

    def test_simple_transition(self):
        code, output = run_cmd(
            cmd_status_transition, current_labels="generating,library:matplotlib", to_status="testing"
        )
        assert code == 0
        assert '--remove-label "generating"' in output
        assert '--add-label "testing"' in output

    def test_no_change_needed(self):
        code, output = run_cmd(cmd_status_transition, current_labels="testing", to_status="testing")
        assert code == 0
        assert output == ""

    def test_empty_current_labels(self):
        code, output = run_cmd(cmd_status_transition, current_labels="", to_status="reviewing")
        assert code == 0
        assert '--add-label "reviewing"' in output

    def test_multiple_status_labels(self):
        code, output = run_cmd(cmd_status_transition, current_labels="generating,testing", to_status="done")
        assert code == 0
        assert "done" in output


class TestQualityLabel:
    """Tests for quality-label command."""

    def test_excellent(self):
        code, output = run_cmd(cmd_quality_label, score=95)
        assert code == 0
        assert output == "quality:excellent"

    def test_good(self):
        code, output = run_cmd(cmd_quality_label, score=87)
        assert code == 0
        assert output == "quality:good"

    def test_needs_work(self):
        code, output = run_cmd(cmd_quality_label, score=78)
        assert code == 0
        assert output == "quality:needs-work"

    def test_poor(self):
        code, output = run_cmd(cmd_quality_label, score=50)
        assert code == 0
        assert output == "quality:poor"

    def test_boundary_excellent(self):
        code, output = run_cmd(cmd_quality_label, score=90)
        assert code == 0
        assert output == "quality:excellent"

    def test_boundary_good(self):
        code, output = run_cmd(cmd_quality_label, score=85)
        assert code == 0
        assert output == "quality:good"

    def test_boundary_needs_work(self):
        code, output = run_cmd(cmd_quality_label, score=75)
        assert code == 0
        assert output == "quality:needs-work"


class TestMain:
    """Tests for main() CLI entry point."""

    def test_extract_branch_via_main(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["workflow_cli", "extract-branch", "auto/test-spec/plotly"])
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert data["spec_id"] == "test-spec"
        assert data["library"] == "plotly"

    def test_extract_sub_issue_via_main(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["workflow_cli", "extract-sub-issue", "Sub-Issue: #55"])
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "55"

    def test_extract_parent_issue_via_main(self, monkeypatch, capsys):
        monkeypatch.setattr(
            sys, "argv", ["workflow_cli", "extract-parent-issue", "Parent Issue: #88", "--issue-body", ""]
        )
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "88"

    def test_get_attempt_count_via_main(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["workflow_cli", "get-attempt-count", "ai-attempt-3,done"])
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "3"

    def test_status_transition_via_main(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["workflow_cli", "status-transition", "generating", "done"])
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert "done" in captured.out

    def test_quality_label_via_main(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["workflow_cli", "quality-label", "92"])
        code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == "quality:excellent"

    def test_missing_command(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["workflow_cli"])
        with pytest.raises(SystemExit):
            main()

    def test_unknown_command(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["workflow_cli", "unknown-command"])
        with pytest.raises(SystemExit):
            main()
