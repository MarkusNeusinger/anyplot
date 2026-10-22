"""The second-opinion script keeps Gemini read-only and its tool loop valid.

`.claude/skills/zweitmeinung/gemini_review.py` hands Gemini read-only tools over
a repository. These tests pin the confinement (only tracked files and --data,
no symlink escapes, no secret-looking data files, only the public API without
/debug and /mcp) and the tool loop against a fake Vertex client: the last tool
turn carries function responses only, because a text part beside them made
Vertex answer 400 on 2026-10-21, and a model that keeps calling tools after the
budget is cut off instead of looping.
"""

import importlib.util
import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "zweitmeinung" / "gemini_review.py"


@pytest.fixture(scope="module")
def gr():
    spec = importlib.util.spec_from_file_location("gemini_review", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("OUTSIDE-TOKEN\n")
    root = tmp_path / "repo"
    (root / "docs").mkdir(parents=True)
    (root / "a.py").write_text("print(1)\n")
    (root / "docs" / "b.md").write_text("# B\n")
    os.symlink("../outside/secret.txt", root / "link.txt")
    git(root, "init", "-q", "-b", "main")
    git(root, "add", "a.py", "docs/b.md", "link.txt")
    git(root, "commit", "-q", "-m", "base")
    (root / ".env").write_text("DATABASE_URL=UNTRACKED-TOKEN\n")
    return root


@pytest.fixture
def data(tmp_path: Path) -> Path:
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "review.txt").write_text("prefetched\n")
    (folder / "server.pem").write_text("PEM-TOKEN\n")
    return folder


def test_workspace_shows_tracked_files_and_data_only(gr, repo, data):
    visible = set(gr.Workspace(repo, data).visible())

    assert visible == {"a.py", "docs/b.md", "data/review.txt"}


def test_read_file_cannot_leave_the_workspace(gr, repo, data):
    ws = gr.Workspace(repo, data)

    assert ws.read_file(str(repo / "a.py")) == "1: print(1)"
    for path in ("../outside/secret.txt", "link.txt", ".env", "/etc/passwd", "data/server.pem"):
        assert ws.read_file(path).startswith("not found or not readable"), path


def test_search_sees_no_hidden_content(gr, repo, data):
    ws = gr.Workspace(repo, data)

    assert ws.search("TOKEN") == "(no matches)"
    assert ws.search("print") == "a.py:1: print(1)"


def test_read_files_reads_several_files_and_caps_the_count(gr, repo, data):
    ws = gr.Workspace(repo, data)

    both = ws.read_files(["a.py", "docs/b.md"])
    assert "=== a.py ===\n1: print(1)" in both
    assert "=== docs/b.md ===\n1: # B" in both
    assert f"only the first {gr.MAX_READ_FILES} paths" in ws.read_files(["a.py"] * (gr.MAX_READ_FILES + 1))


@pytest.mark.parametrize(
    "url",
    [
        "http://api.anyplot.ai/specs",
        "https://example.com/specs",
        "https://api.anyplot.ai:8443/specs",
        "https://api.anyplot.ai//debug",
        "https://api.anyplot.ai/%64ebug/status",
        "https://api.anyplot.ai/v1/../debug",
        "https://api.anyplot.ai/DEBUG",
        "https://api.anyplot.ai/mcp/",
    ],
)
def test_http_get_refuses_before_any_request(gr, url):
    assert gr.http_get(url).startswith("refused")


def test_attachments_stay_inside_root_or_data(gr, repo, data, tmp_path):
    assert gr.check_attachment(data / "review.txt", repo, data) == "data/review.txt"
    for path in (tmp_path / "outside" / "secret.txt", data / "server.pem"):
        with pytest.raises(SystemExit) as exc:
            gr.check_attachment(path, repo, data)
        assert exc.value.code == 2


def test_inline_changes_skips_lock_files_large_and_binary_files(gr, repo):
    git(repo, "switch", "-q", "-c", "work")
    (repo / "a.py").write_text("print(2)\n")
    (repo / "uv.lock").write_text("lock\n")
    (repo / "big.txt").write_text("x" * (gr.MAX_INLINE_FILE_BYTES + 1))
    (repo / "blob.dat").write_bytes(b"\0\1\2")
    git(repo, "add", "a.py", "uv.lock", "big.txt", "blob.dat")
    git(repo, "commit", "-q", "-m", "work")

    parts = gr.inline_changes(gr.Workspace(repo, None), "main")

    assert parts[0].startswith('<diff base="main">')
    assert '<file path="a.py">\nprint(2)\n\n</file>' in parts
    assert not any(part.startswith('<file path="uv.lock">') for part in parts)
    assert parts[-1].startswith("Changed but not included")
    for name in ("big.txt", "blob.dat", "uv.lock"):
        assert name in parts[-1]


# --- the tool loop, against a fake Vertex client ---------------------------------


@pytest.fixture
def types():
    return pytest.importorskip("google.genai.types")


def calls(types, *names: str, prompt: int = 100):
    parts = [types.Part(function_call=types.FunctionCall(name="read_file", args={"path": n})) for n in names]
    return response(types, parts, prompt)


def answer(types, text: str, prompt: int = 100):
    return response(types, [types.Part(text=text)], prompt)


def response(types, parts, prompt: int):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=parts), finish_reason="STOP")],
        usage_metadata=types.GenerateContentResponseUsageMetadata(
            prompt_token_count=prompt, cached_content_token_count=0, candidates_token_count=5, thoughts_token_count=0
        ),
    )


class FakeModels:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def count_tokens(self, model, contents):
        return SimpleNamespace(total_tokens=10)

    def generate_content(self, model, contents, config):
        self.requests.append((list(contents), config))
        return self.responses.pop(0)


def review(gr, monkeypatch, tmp_path, repo, responses, *extra):
    models = FakeModels(responses)
    monkeypatch.setattr(gr, "make_client", lambda flex=False: SimpleNamespace(models=models))
    briefing = tmp_path / "briefing.md"
    briefing.write_text("Review the change.")
    out = tmp_path / "out.md"
    args = gr.build_parser().parse_args(
        [
            "--model",
            "gemini-3.8-flash",
            "review",
            "--briefing",
            str(briefing),
            "--root",
            str(repo),
            "--out",
            str(out),
            *extra,
        ]
    )
    code = 0
    try:
        gr.cmd_review(args)
    except SystemExit as exc:
        code = exc.code
    return code, out.read_text(), models


def tool_replies(request) -> list:
    contents, _ = request
    return contents[-1].parts


def test_last_tool_turn_carries_function_responses_only(gr, types, monkeypatch, tmp_path, repo, capsys):
    code, text, models = review(
        gr,
        monkeypatch,
        tmp_path,
        repo,
        [calls(types, "a.py", "docs/b.md"), answer(types, "Looks fine.")],
        "--max-turns",
        "1",
    )

    assert (code, text) == (0, "Looks fine.")
    replies = tool_replies(models.requests[1])
    assert all(part.function_response and not part.text for part in replies)
    assert [part.function_response.response["result"] for part in replies] == ["1: print(1)", "1: # B"]
    assert all(part.function_response.response["note"] == gr.LAST_TOOL_TURN for part in replies)
    # One config for every turn keeps the tools in the cached prefix.
    assert models.requests[0][1] is models.requests[1][1]
    assert json.loads(capsys.readouterr().out)["stopped_by"] == "max_turns"


def test_model_that_keeps_calling_tools_is_cut_off(gr, types, monkeypatch, tmp_path, repo):
    responses = [calls(types, "a.py") for _ in range(2 + gr.MAX_NUDGES)]

    code, text, models = review(gr, monkeypatch, tmp_path, repo, responses, "--max-turns", "1")

    assert (code, text) == (3, "")
    assert len(models.requests) == 2 + gr.MAX_NUDGES
    for request in models.requests[2:]:
        assert [part.function_response.response for part in tool_replies(request)] == [{"result": gr.BUDGET_USED}]


def test_token_budget_stops_tool_use(gr, types, monkeypatch, tmp_path, repo, capsys):
    responses = [calls(types, "a.py"), calls(types, "docs/b.md"), answer(types, "Done.")]

    code, text, models = review(gr, monkeypatch, tmp_path, repo, responses, "--max-input-tokens", "150")

    assert (code, text) == (0, "Done.")
    assert tool_replies(models.requests[2])[0].function_response.response == {"result": gr.BUDGET_USED}
    assert json.loads(capsys.readouterr().out)["stopped_by"] == "max_input_tokens"
