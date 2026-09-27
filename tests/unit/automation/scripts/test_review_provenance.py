"""Tests for automation.scripts.review_provenance — rules version and resolved model."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from automation.scripts.review_provenance import (
    criteria_version,
    execution_summary,
    git_blob_id,
    main,
    parse_criteria_version,
    resolved_model,
    same_rules,
    tree_id,
)


def _rules_tree(root: Path, library: str | None = "matplotlib") -> None:
    (root / "prompts" / "workflow-prompts").mkdir(parents=True)
    (root / "prompts" / "library").mkdir(parents=True)
    (root / "prompts" / "quality-criteria.md").write_text("# criteria\n", encoding="utf-8")
    (root / "prompts" / "workflow-prompts" / "ai-quality-review.md").write_text("# review\n", encoding="utf-8")
    (root / "prompts" / "default-style-guide.md").write_text("# style\n", encoding="utf-8")
    if library:
        (root / "prompts" / "library" / f"{library}.md").write_text(f"# {library}\n", encoding="utf-8")


class TestBlobId:
    def test_empty_blob_matches_git(self):
        assert git_blob_id(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"

    def test_content_blob_matches_git(self):
        # `printf 'hello\n' | git hash-object --stdin`
        assert git_blob_id(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


class TestCriteriaVersion:
    def test_format_with_library(self, tmp_path):
        _rules_tree(tmp_path)
        version = criteria_version(tmp_path, "matplotlib")
        qc = git_blob_id(b"# criteria\n")[:10]
        lib = git_blob_id(b"# matplotlib\n")[:10]
        assert version.startswith(f"qc-{qc}.aqr-")
        assert version.endswith(f".lib-{lib}")
        assert len(version.split(".")) == 4

    def test_format_without_library(self, tmp_path):
        _rules_tree(tmp_path)
        assert len(criteria_version(tmp_path).split(".")) == 3

    def test_missing_files_are_named(self, tmp_path):
        _rules_tree(tmp_path, library=None)
        (tmp_path / "prompts" / "default-style-guide.md").unlink()
        version = criteria_version(tmp_path, "nosuchlib")
        assert ".sg-missing." in version
        assert version.endswith(".lib-missing")

    def test_parse_and_compare(self, tmp_path):
        _rules_tree(tmp_path)
        version = criteria_version(tmp_path, "matplotlib")
        parts = parse_criteria_version(version)
        assert set(parts) == {"qc", "aqr", "sg", "lib"}
        assert same_rules(version, version)
        other = version.replace(f"qc-{parts['qc']}", "qc-0000000000")
        assert not same_rules(version, other)
        assert same_rules(version, other, components=("aqr",))
        assert not same_rules(version, "n/a")
        assert not same_rules("qc-missing.aqr-missing", "qc-missing.aqr-missing")


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
class TestTreeId:
    def test_matches_git_rev_parse(self, tmp_path):
        repo = tmp_path / "repo"
        _rules_tree(repo)
        (repo / "prompts" / "library" / "zz-extra.md").write_text("x" * 50, encoding="utf-8")
        (repo / "prompts" / "empty-dir").mkdir()  # git ignores empty directories
        script = repo / "prompts" / "tool.sh"
        script.write_text("#!/bin/sh\n", encoding="utf-8")
        script.chmod(0o755)
        git = [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "commit.gpgsign=false",
        ]
        subprocess.run([*git, "init", "-q"], check=True)
        subprocess.run([*git, "add", "prompts"], check=True)
        subprocess.run([*git, "commit", "-q", "-m", "x"], check=True)
        expected = subprocess.run(
            [*git, "rev-parse", "HEAD:prompts"], check=True, capture_output=True, text=True
        ).stdout.strip()
        assert tree_id(repo / "prompts") == expected

    def test_missing_or_empty_directory(self, tmp_path):
        assert tree_id(tmp_path / "absent") is None
        (tmp_path / "empty").mkdir()
        assert tree_id(tmp_path / "empty") is None


def _execution_file(tmp_path: Path, messages: list[dict], jsonl: bool = False) -> Path:
    path = tmp_path / "claude-execution-output.json"
    if jsonl:
        path.write_text("\n".join(json.dumps(m) for m in messages) + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(messages), encoding="utf-8")
    return path


INIT = {"type": "system", "subtype": "init", "model": "claude-sonnet-5", "session_id": "s"}
HELPER = {"type": "system", "subtype": "init", "model": "claude-haiku-4-5-20251001"}
RESULT = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "duration_ms": 198000,
    "num_turns": 21,
    "total_cost_usd": 0.578123,
    "result": "Review written.",
}


class TestResolvedModel:
    """An unresolved model is ``None`` — never the alias passed for an id."""

    def test_reads_the_first_init_message(self, tmp_path):
        assistant = {"type": "assistant", "message": {"model": "claude-haiku-4-5-20251001"}}
        path = _execution_file(tmp_path, [INIT, assistant, HELPER, RESULT])
        assert resolved_model(path) == "claude-sonnet-5"

    def test_never_takes_a_helper_model(self, tmp_path):
        path = _execution_file(tmp_path, [{"type": "assistant", "model": "claude-haiku-4-5"}, RESULT])
        assert resolved_model(path) is None

    def test_jsonl(self, tmp_path):
        path = _execution_file(tmp_path, [INIT, RESULT], jsonl=True)
        assert resolved_model(path) == "claude-sonnet-5"

    def test_messages_wrapper(self, tmp_path):
        path = tmp_path / "out.json"
        path.write_text(json.dumps({"messages": [INIT]}), encoding="utf-8")
        assert resolved_model(path) == "claude-sonnet-5"

    @pytest.mark.parametrize("content", ["", "{not json", "[1, 2]", '"text"'])
    def test_malformed_file_is_unresolved(self, tmp_path, content):
        path = tmp_path / "out.json"
        path.write_text(content, encoding="utf-8")
        assert resolved_model(path) is None

    def test_missing_file_is_unresolved(self, tmp_path):
        assert resolved_model(tmp_path / "absent.json") is None
        assert resolved_model("") is None
        assert resolved_model(None) is None

    def test_implausible_model_is_unresolved(self, tmp_path):
        path = _execution_file(tmp_path, [{**INIT, "model": "claude sonnet\nevil=1"}])
        assert resolved_model(path) is None


class TestExecutionSummary:
    def test_success(self, tmp_path):
        summary = execution_summary(_execution_file(tmp_path, [INIT, RESULT]), "claude-sonnet")
        assert summary == {
            "model": "claude-sonnet-5",
            "cost_usd": 0.5781,
            "turns": 21,
            "duration_ms": 198000,
            "is_error": False,
            "result_subtype": "success",
            "error_class": "",
        }

    def test_quota_error(self, tmp_path):
        result = {**RESULT, "is_error": True, "result": "Claude AI usage limit reached|1759000000"}
        assert execution_summary(_execution_file(tmp_path, [INIT, result]), "x")["error_class"] == "quota"

    def test_other_error(self, tmp_path):
        result = {**RESULT, "subtype": "error_max_turns", "is_error": False, "result": ""}
        summary = execution_summary(_execution_file(tmp_path, [INIT, result]), "x")
        assert summary["error_class"] == "other"
        assert summary["is_error"] is True

    def test_no_result(self, tmp_path):
        summary = execution_summary(_execution_file(tmp_path, [INIT]), "x")
        assert summary["error_class"] == "no_result"
        assert summary["model"] == "claude-sonnet-5"
        assert execution_summary(None, "claude-opus")["model"] == "claude-opus"
        assert execution_summary(None)["model"] is None

    def test_summary_carries_no_transcript(self, tmp_path):
        result = {**RESULT, "result": "SECRET TRANSCRIPT TEXT"}
        summary = execution_summary(_execution_file(tmp_path, [INIT, result]), "x")
        assert "SECRET" not in json.dumps(summary)


class TestCli:
    def test_criteria_version_writes_outputs(self, tmp_path, monkeypatch, capsys):
        _rules_tree(tmp_path)
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        assert main(["criteria-version", "--root", str(tmp_path), "--library", "matplotlib"]) == 0
        text = out.read_text(encoding="utf-8")
        assert f"criteria_version={criteria_version(tmp_path, 'matplotlib')}\n" in text
        assert f"prompts_tree={tree_id(tmp_path / 'prompts')}\n" in text

    def test_model_writes_output(self, tmp_path, monkeypatch):
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        path = _execution_file(tmp_path, [INIT, RESULT])
        assert main(["model", "--execution-file", str(path)]) == 0
        assert out.read_text(encoding="utf-8") == "model_id=claude-sonnet-5\n"

    def test_model_with_empty_execution_file_argument_is_empty(self, tmp_path, monkeypatch):
        # impl-review reads an empty model_id as unresolved: review.model is
        # left out of the metadata and the gate record says n/a.
        out = tmp_path / "gh_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out))
        assert main(["model", "--execution-file", ""]) == 0
        assert out.read_text(encoding="utf-8") == "model_id=\n"

    def test_model_has_no_alias_fallback(self):
        with pytest.raises(SystemExit):
            main(["model", "--execution-file", "", "--fallback", "claude-opus"])
