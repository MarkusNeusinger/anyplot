"""Tests for automation.scripts.render_hash, the staged renders' tie to their code (P2a, warn-only).

The hash ignores only the header score: the generator's own `Quality: N/100`,
impl-generate's reset to `pending` and the review's blind copy hash alike,
while any other byte of the file changes it. `check` reports match, mismatch,
missing or unreadable, never fails, and writes a PR comment for everything but
a match. The script also runs as the workflow-ref copy, next to its own
regen_gate.py.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from automation.scripts import regen_gate
from automation.scripts.render_hash import MARKER, compare, main, read_hash, render_hash


TOOLS = Path(__file__).resolve().parents[4] / "automation" / "scripts"
HEAD = "0123456789abcdef0123456789abcdef01234567"
BODY = "import os\n\nTHEME = os.getenv('ANYPLOT_THEME', 'light')\n"


def _python(score: str, tail: str = " | Created: 2026-11-09", body: str = BODY) -> bytes:
    return f'""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nLibrary: matplotlib | Python 3.14\nQuality: {score}{tail}\n"""\n\n{body}'.encode()


class TestRenderHash:
    def test_the_header_score_never_changes_the_hash(self):
        pending = render_hash(_python("pending"))
        assert render_hash(_python("87/100")) == pending
        assert render_hash(_python("0/100")) == pending
        assert render_hash(_python("92/100", tail=" | Created: 2026-11-09")) == pending

    def test_the_hash_is_the_sha256_of_the_pending_form(self):
        text = _python("87/100").decode()
        expected = hashlib.sha256(regen_gate.reset_header_score(text).encode()).hexdigest()
        assert render_hash(_python("87/100")) == expected

    @pytest.mark.parametrize(
        "other",
        [
            _python("pending", body=BODY.replace("light", "dark")),  # code
            _python("pending", body=BODY + "\n"),  # one byte
            _python("pending", tail=" | Updated: 2026-11-09"),  # the header's date
            _python("pending").replace(b"Library: matplotlib |", b"Library: matplotlib 3.10.3 |"),
        ],
        ids=["code", "trailing-newline", "date", "library-line"],
    )
    def test_every_other_byte_counts(self, other):
        # The review's header writer rewrites the Library and date lines too, so a
        # re-review of the same staging after that commit reads as a mismatch.
        assert render_hash(other) != render_hash(_python("pending"))

    def test_a_score_outside_the_header_still_counts(self):
        body = BODY + "\n" * 20 + "# Quality: 50/100\n"
        assert render_hash(_python("pending", body=body)) != render_hash(
            _python("pending", body=body.replace("50/100", "51/100"))
        )

    def test_line_endings_and_non_utf8_bytes_hash_as_they_are(self):
        crlf = _python("87/100").replace(b"\n", b"\r\n")
        assert render_hash(crlf) == render_hash(_python("pending").replace(b"\n", b"\r\n"))
        assert render_hash(crlf) != render_hash(_python("pending"))
        assert render_hash(b"x = '\xff'\n") != render_hash(b"x = '\xfe'\n")


class TestCompare:
    def _files(self, tmp_path: Path, staged: bytes, head: bytes | None) -> tuple[Path, Path]:
        hash_file, source = tmp_path / "render.sha256", tmp_path / "head.py"
        (tmp_path / "rendered.py").write_bytes(staged)
        main(["write", "--source", str(tmp_path / "rendered.py"), "--out", str(hash_file)])
        if head is not None:
            source.write_bytes(head)
        return hash_file, source

    def test_the_renders_of_the_committed_code_match(self, tmp_path):
        hash_file, source = self._files(tmp_path, _python("87/100"), _python("pending"))
        status, staged, head, reason = compare(hash_file, source)
        assert (status, reason) == ("match", "")
        assert staged == head == render_hash(_python("pending"))

    def test_renders_of_other_code_mismatch(self, tmp_path):
        hash_file, source = self._files(tmp_path, _python("pending"), _python("pending", body="x = 1\n"))
        assert compare(hash_file, source)[0] == "mismatch"

    def test_a_missing_hash_file(self, tmp_path):
        source = tmp_path / "head.py"
        source.write_bytes(_python("pending"))
        status, staged, head, reason = compare(tmp_path / "absent", source)
        assert (status, staged, reason) == ("missing", "", "no render.sha256 in staging")
        assert head == render_hash(_python("pending"))

    @pytest.mark.parametrize("content", ["", "not-a-hash  plots/x.py\n", "ABC" * 30])
    def test_a_file_without_a_hash_is_unreadable(self, tmp_path, content):
        (tmp_path / "render.sha256").write_text(content, encoding="utf-8")
        (tmp_path / "head.py").write_bytes(_python("pending"))
        assert compare(tmp_path / "render.sha256", tmp_path / "head.py")[0] == "unreadable"
        assert read_hash(tmp_path / "render.sha256") is None

    def test_an_unreadable_head_or_staging(self, tmp_path):
        hash_file, _ = self._files(tmp_path, _python("pending"), None)
        assert compare(hash_file, tmp_path / "absent")[0] == "unreadable"
        status, _, _, reason = compare(hash_file, tmp_path / "rendered.py", fetch_error="HTTP 503\nretry")
        assert status == "unreadable" and reason == "staging could not be read (HTTP 503 retry)"


class TestCli:
    def _check(self, tmp_path: Path, monkeypatch, staged: bytes | None, head: bytes) -> tuple[str, str, Path]:
        output, summary = tmp_path / "output", tmp_path / "summary"
        monkeypatch.setenv("GITHUB_OUTPUT", str(output))
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
        (tmp_path / "head.py").write_bytes(head)
        if staged is not None:
            (tmp_path / "rendered.py").write_bytes(staged)
            main(["write", "--source", str(tmp_path / "rendered.py"), "--out", str(tmp_path / "render.sha256")])
        body = tmp_path / "comment.md"
        args = ["check", "--hash", str(tmp_path / "render.sha256"), "--source", str(tmp_path / "head.py")]
        assert main([*args, "--head", HEAD, "--run-url", "https://run/1", "--comment-out", str(body)]) == 0
        return output.read_text(encoding="utf-8"), summary.read_text(encoding="utf-8"), body

    def test_write_uses_the_sha256sum_format(self, tmp_path, capsys):
        (tmp_path / "x.py").write_bytes(_python("pending"))
        main(["write", "--source", str(tmp_path / "x.py"), "--out", str(tmp_path / "render.sha256")])
        digest = render_hash(_python("pending"))
        assert (tmp_path / "render.sha256").read_text(encoding="utf-8") == f"{digest}  {tmp_path / 'x.py'}\n"
        assert f"::notice::render_hash sha256={digest[:12]}" in capsys.readouterr().out

    def test_a_match_writes_no_comment(self, tmp_path, monkeypatch, capsys):
        output, summary, body = self._check(tmp_path, monkeypatch, _python("87/100"), _python("pending"))
        assert output == "status=match\n"
        assert "**Render hash:** match: the staged renders come from the implementation at `0123456`." in summary
        assert not body.exists()
        assert "::notice::render_hash status=match" in capsys.readouterr().out

    def test_a_mismatch_warns_and_writes_the_comment(self, tmp_path, monkeypatch, capsys):
        output, summary, body = self._check(tmp_path, monkeypatch, _python("pending"), _python("pending", body="x\n"))
        assert output == "status=mismatch\n"
        assert "**Render hash:** mismatch at `0123456`" in summary and "warn-only, the score is unchanged" in summary
        assert "::warning::render_hash status=mismatch head=0123456" in capsys.readouterr().out
        text = body.read_text(encoding="utf-8")
        assert text.splitlines()[0] == MARKER.format(status="mismatch", head=HEAD)
        assert "## :warning: Staged renders do not match this code" in text
        assert render_hash(_python("pending"))[:12] in text and "the review and its score go ahead unchanged" in text
        assert text.endswith(":robot: *[impl-review](https://run/1)*\n")
        # Repair reads the last comment that contains "AI Review" as its feedback.
        assert "AI Review" not in text

    def test_a_missing_hash_writes_the_comment(self, tmp_path, monkeypatch):
        output, _, body = self._check(tmp_path, monkeypatch, None, _python("pending"))
        assert output == "status=missing\n"
        assert "Renders staged before the hash existed have none." in body.read_text(encoding="utf-8")

    def test_a_usage_error_exits_2(self):
        with pytest.raises(SystemExit) as exc:
            main(["check", "--hash", "x"])
        assert exc.value.code == 2


def test_runs_as_the_workflow_ref_copy_next_to_its_own_regen_gate(tmp_path):
    """The workflows run a copy beside a copy of regen_gate.py, never the checkout's package."""
    for name in ("render_hash.py", "regen_gate.py"):
        shutil.copy(TOOLS / name, tmp_path / name)
    (tmp_path / "x.py").write_bytes(_python("87/100"))
    result = subprocess.run(
        [sys.executable, "-I", str(tmp_path / "render_hash.py"), "write", "--source", "x.py", "--out", "render.sha256"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert read_hash(tmp_path / "render.sha256") == render_hash(_python("pending"))
