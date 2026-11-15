"""Tests for automation.scripts.render_hash, the staged renders' tie to their code (P2a, P2b).

The render hash ignores only the header score: the generator's own
`Quality: N/100`, impl-generate's reset to `pending` and the review's blind
copy hash alike, while any other byte of the file changes it. The code hash
ignores the whole header, the block impl-review's writer replaces, and nothing
else: a JavaScript directive and every line of code count. `check` reports
match, mismatch, missing or unreadable, never fails, and writes a PR comment
for everything but a match. Only a mismatch against a file with a code hash
stops the review. The script also runs as the workflow-ref copy, next to its
own regen_gate.py and impl_header.py.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from automation.scripts import regen_gate
from automation.scripts.impl_header import replace_js_header
from automation.scripts.render_hash import (
    CODE_NAME,
    FORM_CODE,
    FORM_LEGACY,
    KEEP_CODE,
    LANGUAGES,
    MARKER,
    STOP_LABEL,
    code_hash,
    compare,
    main,
    read_hash,
    read_hashes,
    render_hash,
    strip_header,
)


TOOLS = Path(__file__).resolve().parents[4] / "automation" / "scripts"
HEAD = "0123456789abcdef0123456789abcdef01234567"
BODY = "import os\n\nTHEME = os.getenv('ANYPLOT_THEME', 'light')\n"


def _python(score: str, tail: str = " | Created: 2026-11-09", body: str = BODY) -> bytes:
    return f'""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nLibrary: matplotlib | Python 3.14\nQuality: {score}{tail}\n"""\n\n{body}'.encode()


# What impl-review's header commit turns `_python("pending")` into: another
# first line, the full versions, the score.
REVIEWED = (
    '""" anyplot.ai\nscatter-basic: Basic Scatter Plot\nLibrary: matplotlib 3.10.3 | Python 3.14.10\n'
    f'Quality: 87/100 | Updated: 2026-11-15\n"""\n\n{BODY}'
).encode()

# One file per language as the generator commits it, and as it stands after
# impl-review's header commit.
R_CODE = "library(ggplot2)\n\n# The data\nx <- 1\n"
JULIA_CODE = "using CairoMakie\n\n# The data\nx = 1\n"
JS_CODE = "const t = window.ANYPLOT_TOKENS;\n// The data\nconst value = 68;\n"
SQUARE = "//# anyplot-orientation: square\n"
JS_NEW_HEADER = (
    "// anyplot.ai\n// gauge-basic: Basic Gauge Chart\n// Library: d3 7.9.0 | JavaScript 22.23.3\n"
    "// Quality: 93/100 | Updated: 2026-11-15"
)
JS_OLD_HEADER = (
    "// anyplot.ai\n// gauge-basic: Basic Gauge Chart\n// Library: d3 | JavaScript 22\n"
    "// Quality: pending | Created: 2026-11-15\n"
)
PAIRS = {
    "python": (_python("pending").decode(), REVIEWED.decode()),
    "r": (
        "#' anyplot.ai\n#' gauge-basic: Basic Gauge Chart\n#' Library: ggplot2 | R 4.5\n#' Quality: pending | Created: 2026-11-15\n\n"
        + R_CODE,
        "#' anyplot.ai\n#' gauge-basic: Basic Gauge Chart\n#' Library: ggplot2 4.0.1 | R 4.5.2\n#' Quality: 93/100 | Updated: 2026-11-15\n\n"
        + R_CODE,
    ),
    "julia": (
        "# anyplot.ai\n# gauge-basic: Basic Gauge Chart\n# Library: makie | Julia 1.12\n# Quality: pending | Created: 2026-11-15\n\n"
        + JULIA_CODE,
        "# anyplot.ai\n# gauge-basic: Basic Gauge Chart\n# Library: makie 0.24.6 | Julia 1.12.1\n# Quality: 93/100 | Updated: 2026-11-15\n\n"
        + JULIA_CODE,
    ),
    "javascript": (JS_OLD_HEADER + SQUARE + "\n" + JS_CODE, JS_NEW_HEADER + "\n" + SQUARE + "\n" + JS_CODE),
}


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
        # The review's header writer rewrites the Library and date lines too, so
        # after that commit the head has another render hash. The code hash is
        # what still ties it to its renders (TestCodeHash).
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


class TestCodeHash:
    """The code hash: blind to the header impl-review rewrites, and to nothing else."""

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_the_header_commit_never_changes_it(self, language):
        generated, reviewed = PAIRS[language]
        assert render_hash(generated.encode()) != render_hash(reviewed.encode())
        assert code_hash(generated.encode(), language) == code_hash(reviewed.encode(), language)

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_a_changed_line_of_code_changes_it(self, language):
        generated, reviewed = PAIRS[language]
        edited = reviewed.replace("x <- 1", "x <- 2").replace("x = 1", "x = 2")
        edited = edited.replace("'light'", "'dark'").replace("value = 68", "value = 69")
        assert edited != reviewed
        assert code_hash(edited.encode(), language) != code_hash(generated.encode(), language)

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_a_file_without_a_header_hashes_like_the_file_with_one_prepended(self, language):
        # The writer prepends its header and one line break when a file has none.
        _, reviewed = PAIRS[language]
        bare = strip_header(reviewed, language).lstrip("\n")
        assert bare != reviewed and code_hash(bare.encode(), language) == code_hash(reviewed.encode(), language)

    def test_python_reads_the_docstring_the_writer_replaces(self):
        text = _python("pending").decode()
        assert strip_header(text, "python") == "\n\n" + BODY
        # Not at the very start: the writer prepends a header and leaves this
        # docstring where it is, so it is code to the hash as well.
        late = "\n" + text
        assert strip_header(late, "python") == late
        # A second docstring belongs to the code.
        two = text.replace(BODY, '"""Notes."""\n' + BODY)
        assert code_hash(two.encode(), "python") != code_hash(text.encode(), "python")

    def test_a_comment_below_the_header_block_is_code(self):
        r_generated, _ = PAIRS["r"]
        assert code_hash(r_generated.replace("# The data", "# Other").encode(), "r") != code_hash(
            r_generated.encode(), "r"
        )

    def test_a_javascript_directive_counts(self):
        _, reviewed = PAIRS["javascript"]
        without = reviewed.replace(SQUARE, "")
        other = reviewed.replace("square", "landscape")
        hashes = {code_hash(text.encode(), "javascript") for text in (reviewed, without, other)}
        assert len(hashes) == 3

    @pytest.mark.parametrize(
        "before",
        [
            SQUARE + JS_OLD_HEADER + "\n" + JS_CODE,  # the directive above the header: the writer moves it
            JS_OLD_HEADER + SQUARE + "\n" + JS_CODE,
            JS_OLD_HEADER + SQUARE + JS_OLD_HEADER + "\n" + JS_CODE,  # a stale second block: the writer drops it
            SQUARE + "\n" + JS_CODE,  # no header at all
            JS_OLD_HEADER + "\n" + JS_CODE,  # no directive
        ],
        ids=["directive-first", "header-first", "stale-second-block", "no-header", "no-directive"],
    )
    def test_javascript_is_what_the_writer_leaves_below_its_header(self, before):
        after = replace_js_header(before, JS_NEW_HEADER)
        assert after != before
        assert code_hash(after.encode(), "javascript") == code_hash(before.encode(), "javascript")
        # Writing the header again changes nothing either.
        again = replace_js_header(after, JS_NEW_HEADER.replace("93", "95"))
        assert code_hash(again.encode(), "javascript") == code_hash(before.encode(), "javascript")

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_line_endings_do_not_count(self, language):
        # The writer reads in text mode and writes "\n".
        generated, reviewed = PAIRS[language]
        crlf = generated.replace("\n", "\r\n").encode()
        assert code_hash(crlf, language) == code_hash(reviewed.encode(), language)

    def test_non_utf8_bytes_hash_as_they_are(self):
        assert code_hash(b"x = '\xff'\n", "python") != code_hash(b"x = '\xfe'\n", "python")


class TestCompare:
    def _files(self, tmp_path: Path, staged: bytes, head: bytes | None) -> tuple[Path, Path]:
        hash_file, source = tmp_path / "render.sha256", tmp_path / "head.py"
        (tmp_path / "rendered.py").write_bytes(staged)
        main(["write", "--source", str(tmp_path / "rendered.py"), "--language", "python", "--out", str(hash_file)])
        if head is not None:
            source.write_bytes(head)
        return hash_file, source

    def test_the_renders_of_the_committed_code_match(self, tmp_path):
        hash_file, source = self._files(tmp_path, _python("87/100"), _python("pending"))
        result = compare(hash_file, source, language="python")
        assert (result.status, result.reason, result.via, result.form) == ("match", "", "file", FORM_CODE)
        assert result.staged == result.head == render_hash(_python("pending"))
        assert not result.stop

    def test_the_head_after_the_header_commit_matches_by_its_code(self, tmp_path):
        hash_file, source = self._files(tmp_path, _python("pending"), REVIEWED)
        result = compare(hash_file, source, language="python")
        assert (result.status, result.via, result.stop) == ("match", CODE_NAME, False)
        assert result.staged != result.head

    def test_renders_of_other_code_mismatch_and_stop(self, tmp_path):
        hash_file, source = self._files(tmp_path, _python("pending"), _python("pending", body="x = 1\n"))
        result = compare(hash_file, source, language="python")
        assert (result.status, result.form, result.stop) == ("mismatch", FORM_CODE, True)

    def test_a_file_without_the_code_hash_never_stops(self, tmp_path):
        hash_file, source = self._files(tmp_path, _python("pending"), _python("pending", body="x = 1\n"))
        hash_file.write_text(hash_file.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
        result = compare(hash_file, source, language="python")
        assert (result.status, result.form, result.stop) == ("mismatch", FORM_LEGACY, False)
        # The header commit cannot be told from other code either.
        source.write_bytes(REVIEWED)
        (tmp_path / "rendered.py").write_bytes(_python("pending"))
        hash_file.write_text(f"{render_hash(_python('pending'))}  x.py\n", encoding="utf-8")
        assert compare(hash_file, source, language="python").status == "mismatch"

    @pytest.mark.parametrize("language", ["", "cobol"])
    def test_without_a_known_language_the_code_hash_is_not_read(self, tmp_path, language):
        hash_file, source = self._files(tmp_path, _python("pending"), REVIEWED)
        result = compare(hash_file, source, language=language)
        assert (result.status, result.form, result.stop) == ("mismatch", FORM_LEGACY, False)

    @pytest.mark.parametrize(
        "second",
        ["", "not-a-hash  code\n", "{code}  other\n", "{code}\n", "{code}  code  extra\n"],
        ids=["absent", "no-hash", "other-name", "no-name", "three-fields"],
    )
    def test_only_a_code_line_of_this_writer_counts(self, tmp_path, second):
        hash_file, _ = self._files(tmp_path, _python("pending"), None)
        staged, code = read_hashes(hash_file)
        assert staged == render_hash(_python("pending")) and code == code_hash(_python("pending"), "python")
        hash_file.write_text(f"{staged}  x.py\n" + second.format(code=code), encoding="utf-8")
        assert read_hashes(hash_file) == (staged, None)

    def test_a_missing_hash_file(self, tmp_path):
        source = tmp_path / "head.py"
        source.write_bytes(_python("pending"))
        result = compare(tmp_path / "absent", source, language="python")
        assert (result.status, result.staged, result.reason) == ("missing", "", "no render.sha256 in staging")
        assert result.head == render_hash(_python("pending"))
        assert not result.stop

    @pytest.mark.parametrize("content", ["", "not-a-hash  plots/x.py\n", "ABC" * 30])
    def test_a_file_without_a_hash_is_unreadable(self, tmp_path, content):
        (tmp_path / "render.sha256").write_text(content, encoding="utf-8")
        (tmp_path / "head.py").write_bytes(_python("pending"))
        result = compare(tmp_path / "render.sha256", tmp_path / "head.py", language="python")
        assert (result.status, result.stop) == ("unreadable", False)
        assert read_hash(tmp_path / "render.sha256") is None

    def test_an_unreadable_head_or_staging(self, tmp_path):
        hash_file, _ = self._files(tmp_path, _python("pending"), None)
        absent = compare(hash_file, tmp_path / "absent", language="python")
        assert (absent.status, absent.stop) == ("unreadable", False)
        failed = compare(hash_file, tmp_path / "rendered.py", fetch_error="HTTP 503\nretry", language="python")
        assert failed.status == "unreadable" and failed.reason == "staging could not be read (HTTP 503 retry)"
        assert not failed.stop


class TestCli:
    def _check(
        self, tmp_path: Path, monkeypatch, staged: bytes | None, head: bytes, *extra: str, legacy: bool = False
    ) -> tuple[str, str, Path]:
        output, summary = tmp_path / "output", tmp_path / "summary"
        monkeypatch.setenv("GITHUB_OUTPUT", str(output))
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
        (tmp_path / "head.py").write_bytes(head)
        hash_file = tmp_path / "render.sha256"
        if staged is not None:
            (tmp_path / "rendered.py").write_bytes(staged)
            main(["write", "--source", str(tmp_path / "rendered.py"), "--language", "python", "--out", str(hash_file)])
            if legacy:
                hash_file.write_text(hash_file.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
        body = tmp_path / "comment.md"
        args = ["check", "--hash", str(hash_file), "--source", str(tmp_path / "head.py"), "--language", "python"]
        assert main([*args, "--head", HEAD, "--run-url", "https://run/1", "--comment-out", str(body), *extra]) == 0
        return output.read_text(encoding="utf-8"), summary.read_text(encoding="utf-8"), body

    def test_write_uses_the_sha256sum_format(self, tmp_path, capsys):
        (tmp_path / "x.py").write_bytes(_python("pending"))
        main(["write", "--source", str(tmp_path / "x.py"), "--language", "python", "--out", str(tmp_path / "h")])
        digest, code = render_hash(_python("pending")), code_hash(_python("pending"), "python")
        assert (tmp_path / "h").read_text(encoding="utf-8") == f"{digest}  {tmp_path / 'x.py'}\n{code}  code\n"
        out = capsys.readouterr().out
        assert f"::notice::render_hash sha256={digest[:12]} code={code[:12]} language=python" in out

    @pytest.mark.parametrize("language", [[], ["--language", "cobol"]], ids=["absent", "unknown"])
    def test_write_fails_without_a_known_language(self, tmp_path, language):
        # A file without the code hash is never enforced, so half a file must not be written.
        (tmp_path / "x.py").write_bytes(_python("pending"))
        with pytest.raises(SystemExit) as exc:
            main(["write", "--source", str(tmp_path / "x.py"), "--out", str(tmp_path / "h"), *language])
        assert exc.value.code == 2 and not (tmp_path / "h").exists()

    def test_a_match_writes_no_comment(self, tmp_path, monkeypatch, capsys):
        output, summary, body = self._check(tmp_path, monkeypatch, _python("87/100"), _python("pending"))
        assert output == "status=match\nstop=false\n"
        assert "**Render hash:** match: the staged renders come from the implementation at `0123456`." in summary
        assert not body.exists()
        assert "::notice::render_hash status=match" in capsys.readouterr().out

    def test_a_match_by_the_code_says_so(self, tmp_path, monkeypatch, capsys):
        output, summary, body = self._check(tmp_path, monkeypatch, _python("pending"), REVIEWED)
        assert output == "status=match\nstop=false\n"
        assert "only the file header differs" in summary
        assert not body.exists()
        assert "head=0123456 via=code form=two-line" in capsys.readouterr().out

    def test_a_mismatch_stops_a_first_generation(self, tmp_path, monkeypatch, capsys):
        output, summary, body = self._check(
            tmp_path,
            monkeypatch,
            _python("pending"),
            _python("pending", body="x\n"),
            "--spec-id",
            "scatter-basic",
            "--library",
            "matplotlib",
        )
        assert output == "status=mismatch\nstop=true\n"
        assert "**Render hash:** mismatch at `0123456`" in summary and "the review does not run" in summary
        assert "::warning::render_hash status=mismatch head=0123456 form=two-line stop=true" in capsys.readouterr().out
        text = body.read_text(encoding="utf-8")
        assert text.splitlines()[0] == MARKER.format(status="mismatch", head=HEAD)
        assert "## :warning: Staged renders do not match this code" in text
        assert render_hash(_python("pending"))[:12] in text
        assert "The review did not run" in text and f"labelled `{STOP_LABEL}`" in text
        assert "gh workflow run bulk-generate.yml -f specification_id=scatter-basic -f library=matplotlib" in text
        assert "go ahead unchanged" not in text and KEEP_CODE not in text
        assert text.endswith(":robot: *[impl-review](https://run/1)*\n")
        # Repair reads the last comment that contains "AI Review" as its feedback.
        assert "AI Review" not in text

    def test_a_mismatch_on_a_regeneration_names_the_keep(self, tmp_path, monkeypatch):
        output, _, body = self._check(
            tmp_path, monkeypatch, _python("pending"), _python("pending", body="x\n"), "--regeneration"
        )
        assert output == "status=mismatch\nstop=true\n"
        text = body.read_text(encoding="utf-8")
        assert "The review did not run" in text and f"(`{KEEP_CODE}`)" in text
        assert STOP_LABEL not in text and "bulk-generate" not in text

    def test_a_mismatch_against_a_legacy_file_only_warns(self, tmp_path, monkeypatch, capsys):
        output, summary, body = self._check(
            tmp_path, monkeypatch, _python("pending"), _python("pending", body="x\n"), legacy=True
        )
        assert output == "status=mismatch\nstop=false\n"
        assert "warn-only, the score is unchanged" in summary
        assert "form=legacy stop=false" in capsys.readouterr().out
        text = body.read_text(encoding="utf-8")
        assert "the review and its score go ahead unchanged" in text and "holds no code hash" in text
        assert "The review did not run" not in text

    def test_a_missing_hash_writes_the_comment(self, tmp_path, monkeypatch):
        output, summary, body = self._check(tmp_path, monkeypatch, None, _python("pending"))
        assert output == "status=missing\nstop=false\n"
        assert "warn-only, the score is unchanged" in summary
        text = body.read_text(encoding="utf-8")
        assert "Renders staged before the hash existed have none." in text
        assert "the review and its score go ahead unchanged" in text

    def test_a_usage_error_exits_2(self):
        with pytest.raises(SystemExit) as exc:
            main(["check", "--hash", "x"])
        assert exc.value.code == 2


@pytest.mark.parametrize(
    ("language", "name", "content", "copies"),
    [
        ("python", "x.py", _python("87/100").decode(), ("render_hash.py", "regen_gate.py")),
        ("javascript", "x.js", PAIRS["javascript"][0], ("render_hash.py", "regen_gate.py", "impl_header.py")),
    ],
    ids=["python", "javascript"],
)
def test_runs_as_the_workflow_ref_copy_next_to_its_own_modules(tmp_path, language, name, content, copies):
    """The workflows run a copy beside copies of its modules, never the checkout's package.

    Python, R and Julia need regen_gate.py alone; JavaScript also impl_header.py.
    """
    for module in copies:
        shutil.copy(TOOLS / module, tmp_path / module)
    (tmp_path / name).write_text(content, encoding="utf-8")
    command = [sys.executable, "-I", str(tmp_path / "render_hash.py"), "write", "--source", name]
    result = subprocess.run(
        [*command, "--language", language, "--out", "render.sha256"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    staged, code = read_hashes(tmp_path / "render.sha256")
    assert staged == render_hash(regen_gate.reset_header_score(content).encode())
    assert code == code_hash(content.encode(), language)


def test_javascript_without_impl_header_fails_and_writes_nothing(tmp_path):
    """A copy that lacks impl_header.py must not write a file without the code hash."""
    for module in ("render_hash.py", "regen_gate.py"):
        shutil.copy(TOOLS / module, tmp_path / module)
    (tmp_path / "x.js").write_text(PAIRS["javascript"][0], encoding="utf-8")
    command = [sys.executable, "-I", str(tmp_path / "render_hash.py"), "write", "--source", "x.js"]
    result = subprocess.run(
        [*command, "--language", "javascript", "--out", "render.sha256"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode != 0
    assert not (tmp_path / "render.sha256").exists()
