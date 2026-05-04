"""Tests for `agentic.workflows.modules.regen.pr_create`.

Real subprocess calls (git fetch, git push, gh pr create) are too
side-effecting to run in unit tests, so we patch `subprocess.run` /
`subprocess.check_output` and verify the orchestration sequence.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from agentic.workflows.modules.regen import QualityEval
from agentic.workflows.modules.regen.pr_create import _build_pr_body, _read_spec_issue, create_regen_pr


def _quality(score: int = 87) -> QualityEval:
    return QualityEval(
        score=score,
        vq=30,
        de=13,
        sc=15,
        dq=14,
        cq=10,
        lm=5,
        image_description="...",
        strengths=["clean"],
        weaknesses=["minor"],
        criteria_checklist={},
        verdict="APPROVED",
    )


def test_read_spec_issue_returns_int(tmp_path):
    spec_yaml = tmp_path / "scatter-basic" / "specification.yaml"
    spec_yaml.parent.mkdir(parents=True)
    spec_yaml.write_text(yaml.safe_dump({"spec_id": "scatter-basic", "issue": 42}), encoding="utf-8")
    assert _read_spec_issue("scatter-basic", plots_root=tmp_path) == 42


def test_read_spec_issue_missing_yaml_returns_none(tmp_path):
    assert _read_spec_issue("nonexistent", plots_root=tmp_path) is None


def test_build_pr_body_includes_parent_issue_marker():
    body = _build_pr_body("scatter-basic", "altair", _quality(87), parent_issue=42)
    assert "**Parent Issue:** #42" in body
    assert "Quality: 87/100" in body
    assert "VQ: 30/30" in body  # category breakdown


def test_build_pr_body_omits_parent_when_no_issue():
    body = _build_pr_body("scatter-basic", "altair", _quality(87), parent_issue=None)
    assert "**Parent Issue:**" not in body
    assert "Quality: 87/100" in body


def _setup_repo(tmp_path: Path, with_issue: int | None = 42) -> None:
    plots = tmp_path / "plots" / "scatter-basic"
    (plots / "implementations" / "python").mkdir(parents=True)
    (plots / "metadata" / "python").mkdir(parents=True)
    (plots / "implementations" / "python" / "altair.py").write_text("# stub", encoding="utf-8")
    (plots / "metadata" / "python" / "altair.yaml").write_text("library: altair", encoding="utf-8")
    spec_data: dict = {"spec_id": "scatter-basic"}
    if with_issue is not None:
        spec_data["issue"] = with_issue
    (plots / "specification.yaml").write_text(yaml.safe_dump(spec_data), encoding="utf-8")


def test_create_regen_pr_orchestration(tmp_path, monkeypatch):
    """Verify the sequence of subprocess calls: fetch → branch -D → worktree
    add → git add/commit/push → gh pr create → label → cleanup."""
    monkeypatch.chdir(tmp_path)
    _setup_repo(tmp_path)
    # The function calls .exists() on the worktree dir; create it after
    # `git worktree add` is mocked. We simulate by making the worktree dir
    # appear after the mocked 'add' call. Easiest: pre-create it so the
    # cleanup branch in finally also fires.
    worktree = tmp_path / ".worktrees" / "scatter-basic-altair"
    worktree.mkdir(parents=True)
    (worktree / "plots" / "scatter-basic" / "implementations" / "python").mkdir(parents=True)
    (worktree / "plots" / "scatter-basic" / "metadata" / "python").mkdir(parents=True)

    pr_url = "https://github.com/owner/repo/pull/123"

    with (
        patch("agentic.workflows.modules.regen.pr_create.subprocess") as sp,
        patch("agentic.workflows.modules.regen.pr_create.time.sleep"),
    ):
        sp.run.return_value = None
        sp.check_output.side_effect = [
            # 1) `gh pr create ...` → PR URL on the last line
            f"Creating PR...\n{pr_url}\n",
            # 2) `gh repo view --json owner,name` (called by _add_labels)
            '{"owner":{"login":"owner"},"name":"repo"}',
        ]
        result = create_regen_pr(
            "scatter-basic",
            "altair",
            _quality(87),
            plots_root=tmp_path / "plots",
            worktrees_root=tmp_path / ".worktrees",
        )

    assert result.pr_url == pr_url
    assert result.pr_number == 123
    assert result.branch == "implementation/scatter-basic/altair"

    # Verify key calls in order
    cmds = [c.args[0] for c in sp.run.call_args_list]
    assert cmds[0] == ["git", "fetch", "origin", "main"]
    # branch -D before worktree add (idempotent retry support)
    assert any(cmd[:3] == ["git", "branch", "-D"] for cmd in cmds[:5])
    assert any(cmd[:3] == ["git", "worktree", "add"] for cmd in cmds)
    # commit + push (`git -C <worktree> ...`)
    assert any("commit" in cmd and cmd[0] == "git" for cmd in cmds)
    assert any("push" in cmd and cmd[0] == "git" for cmd in cmds)
    # cleanup: branch -D MUST appear after the work is done
    assert ["git", "worktree", "prune"] in cmds
    assert ["git", "branch", "-D", "implementation/scatter-basic/altair"] in cmds


def test_create_regen_pr_cleans_up_branch_even_on_failure(tmp_path, monkeypatch):
    """Even if `gh pr create` blows up, the local branch must be deleted so
    the next attempt isn't blocked by 'branch already exists'."""
    monkeypatch.chdir(tmp_path)
    _setup_repo(tmp_path)
    worktree = tmp_path / ".worktrees" / "scatter-basic-altair"
    worktree.mkdir(parents=True)
    (worktree / "plots" / "scatter-basic" / "implementations" / "python").mkdir(parents=True)
    (worktree / "plots" / "scatter-basic" / "metadata" / "python").mkdir(parents=True)

    import subprocess as real_sp

    with patch("agentic.workflows.modules.regen.pr_create.subprocess") as sp:
        sp.run.return_value = None
        sp.CalledProcessError = real_sp.CalledProcessError
        sp.check_output.side_effect = real_sp.CalledProcessError(1, ["gh", "pr", "create"])
        with pytest.raises(real_sp.CalledProcessError):
            create_regen_pr(
                "scatter-basic",
                "altair",
                _quality(87),
                plots_root=tmp_path / "plots",
                worktrees_root=tmp_path / ".worktrees",
            )
        cmds = [c.args[0] for c in sp.run.call_args_list]
        # branch -D MUST appear in cleanup (after the exception)
        assert ["git", "branch", "-D", "implementation/scatter-basic/altair"] in cmds


def test_add_labels_uses_rest_api(tmp_path, monkeypatch):
    """`_add_labels` must use the REST API (gh api …/labels) rather than
    `gh pr edit --add-label`, which is unreliable on this repo. Each label
    is posted in its own call so webhook events don't pile up in the
    `impl-merge.yml` concurrency group — the last label (`ai-approved`)
    must be the one that triggers the actual merge run."""
    from agentic.workflows.modules.regen.pr_create import _add_labels

    with (
        patch("agentic.workflows.modules.regen.pr_create.subprocess") as sp,
        patch("agentic.workflows.modules.regen.pr_create.time.sleep") as sleep,
    ):
        sp.check_output.return_value = '{"owner":{"login":"o"},"name":"r"}'
        sp.run.return_value = None
        _add_labels(123, ["quality:87", "ai-approved"])

        # One POST per label, in the order given
        cmds = [c.args[0] for c in sp.run.call_args_list]
        assert len(cmds) == 2
        for cmd in cmds:
            assert cmd[:4] == ["gh", "api", "-X", "POST"]
            assert cmd[4] == "repos/o/r/issues/123/labels"
        assert "labels[]=quality:87" in cmds[0]
        assert "labels[]=ai-approved" in cmds[1]
        # Sleep between posts so the first webhook's run finishes
        # (early-skip ~4-5s) before the second webhook fires.
        assert sleep.call_count == 1
        assert sleep.call_args.args[0] >= 5
