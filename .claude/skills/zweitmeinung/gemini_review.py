"""Ask Gemini for a second opinion through Vertex AI, with read-only tools.

This replaces headless `agy -p`: Google's Antigravity FAQ and a staff reply of
2026-10-16 forbid running agy from third-party coding agents under a consumer
login. Vertex AI is plain Google Cloud usage, billed to the project's billing
account (the Google AI Ultra Cloud credit applies).

Gemini gets the briefing, the inlined diff and attachments, and five read-only
tools: list_files, read_file, read_files and search over the files git tracks
in --root (plus everything in --data), and http_get on the public API
(https://api.anyplot.ai, no /debug or /mcp). It has no shell, no write access
and never sees a credential: the script holds the Google login (ADC) and only
text crosses to Gemini.

Run from the repository root with:
    uv run --no-project --with google-genai==2.29.0 python -I .claude/skills/zweitmeinung/gemini_review.py ...
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import posixpath
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import NoReturn


PROJECT = "anyplot"
LOCATION = "global"  # second opinions: cheapest; the site's agents stay on eu
DEFAULT_MODEL = "gemini-4-argon"
LABELS = {"purpose": "second-opinion"}

MAX_FILE_BYTES = 300_000
MAX_TOOL_CHARS = 60_000
MAX_LIST_ENTRIES = 500
MAX_SEARCH_HITS = 200
MAX_SEARCH_LINE = 4_000  # longer lines (minified bundles, base64) are skipped
MAX_READ_FILES = 10
DEFAULT_MAX_TURNS = 8
DEFAULT_MAX_INPUT_TOKENS = 600_000  # summed over all turns, cached tokens included
MAX_NUDGES = 2  # extra turns granted after the budget to a model that keeps calling tools
MAX_OUTPUT_TOKENS = 32_768
HTTP_HOST = "api.anyplot.ai"

BUDGET_USED = "Not run: the tool budget is used up. Do not call tools again; write the review now."
LAST_TOOL_TURN = "This was the last tool turn. Do not call tools again; write the review now."

# --diff-base inlines the diff and the changed files into the first prompt, so
# Gemini does not spend tool turns on them (every turn re-sends the whole history).
MAX_INLINE_FILE_BYTES = 60_000
MAX_INLINE_TOTAL_BYTES = 240_000  # about 60k tokens
NO_INLINE = {"uv.lock", "yarn.lock", "package-lock.json", "pnpm-lock.yaml", "CHANGELOG.md"}

# USD per 1M tokens on Vertex AI global: (input, output incl. thinking, cached input).
# From the billing pricing export, 2026-10-21. Regional (eu) is 10 % more.
PRICES = {
    ("gemini-4-argon", "online"): (4.00, 20.00, 0.20),
    ("gemini-3.8-flash", "online"): (1.50, 7.50, 0.15),
    ("gemini-3.8-flash", "flex"): (0.75, 3.75, 0.075),
}
# Flex PayGo: half price for latency-tolerant requests, global endpoint only, and
# only for some models (3.8 Flash yes, 4 Argon no; Vertex docs, 2026-10-21).
FLEX_MODELS = {"gemini-3.8-flash"}
FLEX_HEADERS = {"X-Vertex-AI-LLM-Shared-Request-Type": "flex", "X-Vertex-AI-LLM-Request-Type": "shared"}
FLEX_WAIT_MS = 300_000  # a Flex request still queued after this goes online

SECRET_NAME_PATTERNS = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    "*credentials*",
    "*secret*",
    "*oauth*",
    "api-key",
]
SECRET_DIRS = {".ssh", ".gnupg", ".config", ".gemini", ".aws", ".kube", ".docker", ".git"}

INSTRUCTIONS = """\
You are reviewing a plan or code change as an independent second opinion.
You have read-only tools: list_files, read_file, read_files (several files in
one call) and search over the repository the briefing is about, and http_get on
the public API https://api.anyplot.ai.
Use them to verify claims before you make them, and cite path:line for every
claim about the code. Mark claims you could not verify. You cannot run code,
change files, or reach anything else; do not ask for that.

The diff under review and the full text of the changed files may already be
included after the briefing; do not read those again. Every tool turn re-sends
the whole conversation, so plan your reads: request all the files and searches
you need in one turn, as several calls in parallel, and aim for two or three
tool turns at most. When you have what you need, stop calling tools and write
the review the briefing asks for.
"""


def fail(message: str, code: int = 2) -> NoReturn:
    print(f"gemini_review: {message}", file=sys.stderr)
    sys.exit(code)


def looks_secret(rel: Path) -> bool:
    if any(part in SECRET_DIRS for part in rel.parts):
        return True
    return any(fnmatch.fnmatch(rel.name.lower(), pattern) for pattern in SECRET_NAME_PATTERNS)


class Workspace:
    """Read-only view of the files Gemini may see."""

    def __init__(self, root: Path, data: Path | None) -> None:
        self.root = root
        self.data = data
        listing = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
        if listing.returncode != 0:
            fail(f"--root must be a git working tree: {root}")
        allowed = [root.resolve()] + ([data.resolve()] if data else [])
        candidates = {rel: root / rel for rel in listing.stdout.decode("utf-8", "replace").split("\0") if rel}
        if data:
            candidates.update(
                {
                    f"data/{p.relative_to(data)}": p
                    for p in data.rglob("*")
                    if p.is_file() and not looks_secret(p.relative_to(data))
                }
            )
        # Built once: every entry, symlinks included, must resolve to a regular file
        # inside --root or --data, so list_files, read_file and search see the same
        # set. Tracked files of a public repository are public already and are not
        # name-filtered; untracked files (.env, local settings) never appear.
        self._visible: dict[str, Path] = {}
        for rel, path in candidates.items():
            real = path.resolve()
            if real.is_file() and any(real.is_relative_to(a) for a in allowed):
                self._visible[rel] = real

    def visible(self) -> dict[str, Path]:
        return self._visible

    def normalise(self, path: str) -> str:
        rel = path.strip()
        if rel.startswith(str(self.root) + "/"):
            rel = rel[len(str(self.root)) + 1 :]
        while rel.startswith("./"):
            rel = rel[2:]
        return rel.lstrip("/")

    def resolve(self, path: str) -> Path | None:
        return self._visible.get(self.normalise(path))

    def list_files(self, path: str = "", pattern: str = "") -> str:
        prefix = self.normalise(path).rstrip("/")
        prefix = "" if prefix in ("", ".") else prefix + "/"
        names = sorted(n for n in self.visible() if n.startswith(prefix))
        if pattern:
            names = [n for n in names if fnmatch.fnmatch(n, pattern) or fnmatch.fnmatch(Path(n).name, pattern)]
        more = len(names) - MAX_LIST_ENTRIES
        lines = names[:MAX_LIST_ENTRIES]
        if more > 0:
            lines.append(f"... {more} more; narrow the path or pattern")
        return "\n".join(lines) or "(no files)"

    def read_file(self, path: str, start_line: int = 1, end_line: int = 0) -> str:
        target = self.resolve(path)
        if target is None:
            return f"not found or not readable: {path} (use list_files; only tracked repository files and data/ are visible)"
        if target.stat().st_size > 5_000_000:
            return "file too large"
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(1, int(start_line or 1))
        end = min(len(lines), int(end_line) if end_line else len(lines))
        out, size = [], 0
        for number in range(start, end + 1):
            row = f"{number}: {lines[number - 1]}"
            size += len(row) + 1
            if size > MAX_TOOL_CHARS:
                out.append(f"... truncated at line {number - 1} of {len(lines)}; read on with start_line={number}")
                break
            out.append(row)
        return "\n".join(out) or "(empty range)"

    def read_files(self, paths: list[str]) -> str:
        out, size = [], 0
        for path in paths[:MAX_READ_FILES]:
            text = self.read_file(path)
            if out and size + len(text) > 2 * MAX_TOOL_CHARS:
                out.append(
                    f"... stopped before {path}: the combined output limit is reached; read the rest in another call"
                )
                break
            size += len(text)
            out.append(f"=== {path} ===\n{text}")
        if len(paths) > MAX_READ_FILES:
            out.append(f"... only the first {MAX_READ_FILES} paths were read")
        return "\n\n".join(out) or "(no paths)"

    def search(self, pattern: str, path: str = "", glob: str = "") -> str:
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return f"invalid regex: {exc}"
        prefix = self.normalise(path).rstrip("/")
        prefix = "" if prefix in ("", ".") else prefix + "/"
        hits: list[str] = []
        for rel, file in sorted(self.visible().items()):
            if not rel.startswith(prefix) or (
                glob and not fnmatch.fnmatch(Path(rel).name, glob) and not fnmatch.fnmatch(rel, glob)
            ):
                continue
            try:
                if file.stat().st_size > 2_000_000:
                    continue
                text = file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if len(line) <= MAX_SEARCH_LINE and regex.search(line):
                    hits.append(f"{rel}:{number}: {line.strip()[:240]}")
                    if len(hits) >= MAX_SEARCH_HITS:
                        return "\n".join(hits + ["... more hits; narrow the pattern, path or glob"])
        return "\n".join(hits) or "(no matches)"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None  # a redirect surfaces as an HTTPError instead of being followed


def http_get(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != HTTP_HOST or parsed.port not in (None, 443):
        return f"refused: only https://{HTTP_HOST}/ is allowed"
    path = urllib.parse.unquote(parsed.path)
    if "//" in path or "\\" in path or ".." in path.split("/"):
        return "refused: path must be normalised (no //, \\ or ..)"
    if posixpath.normpath(path or "/").lower().startswith(("/debug", "/mcp")):
        return "refused: /debug and /mcp are not available"
    request = urllib.request.Request(url, headers={"User-Agent": "anyplot-second-opinion/1"}, method="GET")
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=20) as response:
            body = response.read(MAX_TOOL_CHARS + 1).decode("utf-8", "replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location") if exc.headers else None
        return f"HTTP {exc.code}" + (f" (redirect to {location}, not followed)" if location else "")
    except (urllib.error.URLError, TimeoutError) as exc:
        return f"request failed: {exc}"
    if len(body) > MAX_TOOL_CHARS:
        body = body[:MAX_TOOL_CHARS] + "\n... truncated"
    return f"HTTP {status}\n{body}"


def tool_declarations():
    from google.genai import types

    def decl(name: str, description: str, properties: dict, required: list[str]) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=name,
            description=description,
            parameters_json_schema={"type": "object", "properties": properties, "required": required},
        )

    return types.Tool(
        function_declarations=[
            decl(
                "list_files",
                "List repository files (tracked by git) and data/ files under a directory.",
                {
                    "path": {
                        "type": "string",
                        "description": "Directory relative to the repository root; empty for all.",
                    },
                    "pattern": {"type": "string", "description": "Optional glob such as '*.py'."},
                },
                [],
            ),
            decl(
                "read_file",
                "Read a file with line numbers. Long files are cut; continue with start_line.",
                {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer", "description": "0 or omitted reads to the end."},
                },
                ["path"],
            ),
            decl(
                "read_files",
                f"Read up to {MAX_READ_FILES} whole files in one call, with line numbers. "
                "Prefer this over several read_file calls: every extra turn re-sends the conversation.",
                {"paths": {"type": "array", "items": {"type": "string"}}},
                ["paths"],
            ),
            decl(
                "search",
                "Search file contents with a Python regular expression; returns path:line: text.",
                {
                    "pattern": {"type": "string"},
                    "path": {"type": "string", "description": "Directory to limit the search to."},
                    "glob": {"type": "string", "description": "File name glob such as '*.ts'."},
                },
                ["pattern"],
            ),
            decl(
                "http_get",
                f"GET a URL on the public anyplot API (https://{HTTP_HOST}/...), for live data.",
                {"url": {"type": "string"}},
                ["url"],
            ),
        ]
    )


def run_tool(workspace: Workspace, name: str, args: dict) -> str:
    try:
        if name == "list_files":
            return workspace.list_files(str(args.get("path", "")), str(args.get("pattern", "")))
        if name == "read_file":
            return workspace.read_file(
                str(args["path"]), int(args.get("start_line", 1) or 1), int(args.get("end_line", 0) or 0)
            )
        if name == "read_files":
            paths = args["paths"]
            return workspace.read_files([paths] if isinstance(paths, str) else [str(p) for p in paths])
        if name == "search":
            return workspace.search(str(args["pattern"]), str(args.get("path", "")), str(args.get("glob", "")))
        if name == "http_get":
            return http_get(str(args["url"]))
    except (KeyError, ValueError, TypeError) as exc:
        return f"bad arguments: {exc}"
    return f"unknown tool: {name}"


def check_attachment(path: Path, root: Path, data: Path | None) -> str:
    resolved = path.resolve()
    if not resolved.is_file():
        fail(f"attachment is not a file: {path}")
    if resolved.is_relative_to(root):
        rel = resolved.relative_to(root)
        shown = str(rel)
    elif data and resolved.is_relative_to(data):
        rel = resolved.relative_to(data)
        shown = f"data/{rel}"
    else:
        fail(f"attachment lies outside --root and --data: {path}")
    if looks_secret(rel):
        fail(f"attachment looks like a secret or credentials file, refusing: {rel}")
    if resolved.stat().st_size > MAX_FILE_BYTES:
        fail(f"attachment is larger than {MAX_FILE_BYTES} bytes, attach an excerpt: {rel}")
    return shown


def git_text(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode != 0:
        fail(f"git {' '.join(args)} failed: {result.stderr.decode('utf-8', 'replace').strip()[:300]}")
    return result.stdout.decode("utf-8", "replace")


def inline_changes(workspace: Workspace, base: str) -> list[str]:
    """The diff against base plus the changed files' full text, within the size caps."""
    root = workspace.root
    parts = [f'<diff base="{base}">\n{git_text(root, "diff", f"{base}...HEAD")}\n</diff>']
    names = git_text(root, "diff", "--name-only", "--diff-filter=AMR", f"{base}...HEAD").splitlines()
    budget = MAX_INLINE_TOTAL_BYTES
    skipped = []
    for rel in names:
        path = workspace.visible().get(rel)
        if path is None or Path(rel).name in NO_INLINE:
            skipped.append(rel)
            continue
        raw = path.read_bytes()
        if b"\0" in raw or len(raw) > MAX_INLINE_FILE_BYTES or len(raw) > budget:
            skipped.append(rel)
            continue
        budget -= len(raw)
        parts.append(f'<file path="{rel}">\n{raw.decode("utf-8", "replace")}\n</file>')
    if skipped:
        parts.append("Changed but not included (read them with the tools if you need them): " + ", ".join(skipped))
    return parts


def build_prompt(briefing: Path, attachments: list[Path], workspace: Workspace, diff_base: str | None) -> str:
    if not briefing.is_file():
        fail(f"briefing not found: {briefing}")
    parts = [briefing.read_text(encoding="utf-8").strip()]
    if diff_base:
        parts += inline_changes(workspace, diff_base)
    for path in attachments:
        shown = check_attachment(path, workspace.root, workspace.data)
        text = path.resolve().read_text(encoding="utf-8", errors="replace")
        parts.append(f'<file path="{shown}">\n{text}\n</file>')
    return "\n\n".join(parts)


def make_client(flex: bool = False):
    from google import genai
    from google.genai import types

    # A Flex request is tried once: the SDK retries timeouts as well, and five
    # 15-minute attempts per turn kept one review waiting for over an hour
    # (2026-10-22). cmd_review sends the turn online instead.
    return genai.Client(
        vertexai=True,
        project=PROJECT,
        location=LOCATION,
        http_options=types.HttpOptions(
            timeout=FLEX_WAIT_MS if flex else 900_000,
            headers=FLEX_HEADERS if flex else None,
            retry_options=types.HttpRetryOptions(
                attempts=1 if flex else 3, initial_delay=2.0, http_status_codes=[429, 500, 503]
            ),
        ),
    )


def flex_unavailable(exc: Exception) -> bool:
    """Flex had no capacity: the request timed out in the queue or was refused."""
    import httpx
    from google.genai import errors

    return isinstance(exc, httpx.TimeoutException) or (isinstance(exc, errors.APIError) and exc.code in (429, 500, 503))


def cmd_check(args: argparse.Namespace) -> None:
    client = make_client()
    try:
        client.models.get(model=args.model)
    except Exception as exc:  # report the API's reason, nothing else
        fail(
            f"model {args.model} not reachable on Vertex ({PROJECT}/{LOCATION}): {type(exc).__name__}: {str(exc)[:300]}"
        )
    print(json.dumps({"ok": True, "model": args.model, "project": PROJECT, "location": LOCATION}))


def cmd_review(args: argparse.Namespace) -> None:
    from google.genai import types

    root = Path(args.root).resolve()
    data = Path(args.data).resolve() if args.data else None
    if data and not data.is_dir():
        fail(f"--data is not a directory: {data}")
    workspace = Workspace(root, data)
    prompt = build_prompt(Path(args.briefing), [Path(p) for p in args.attach], workspace, args.diff_base)
    flex = args.model in FLEX_MODELS if args.flex is None else args.flex
    if flex and args.model not in FLEX_MODELS:
        fail(f"Flex PayGo is not available for {args.model}; known: {', '.join(sorted(FLEX_MODELS))}")
    flex_requested = flex
    online = make_client()

    counted = online.models.count_tokens(model=args.model, contents=prompt).total_tokens or 0
    if counted > args.max_input_tokens // 4:
        fail(f"the briefing and attachments have {counted} tokens; trim them (cap {args.max_input_tokens // 4})")

    # One config for every turn: the tools are part of the cached prefix, and a last
    # turn without them lost the implicit cache (2026-10-21) while Flash kept calling
    # tools anyway. The budget is enforced through the tool responses instead.
    config = types.GenerateContentConfig(
        system_instruction=INSTRUCTIONS,
        thinking_config=types.ThinkingConfig(thinking_level=args.thinking.upper()),
        max_output_tokens=MAX_OUTPUT_TOKENS,
        labels=LABELS,
        tools=[tool_declarations()],
    )

    client = make_client(True) if flex else online
    contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    totals = {"prompt": 0, "cached": 0, "output": 0, "thoughts": 0}
    per_turn: list[list[int]] = []  # [prompt, cached] per call, to see the cache hit rate
    traffic: set[str] = set()
    tool_calls: dict[str, int] = {}
    response = None
    stopped_by = None
    tool_turns = 0
    nudges = 0
    while True:
        try:
            response = client.models.generate_content(model=args.model, contents=contents, config=config)
        except Exception as exc:
            if not flex or not flex_unavailable(exc):
                raise
            # No Flex capacity now: this turn and the rest of the run go online.
            flex, client = False, online
            continue
        usage = response.usage_metadata
        if usage:
            totals["prompt"] += usage.prompt_token_count or 0
            totals["cached"] += usage.cached_content_token_count or 0
            totals["output"] += usage.candidates_token_count or 0
            totals["thoughts"] += usage.thoughts_token_count or 0
            per_turn.append([usage.prompt_token_count or 0, usage.cached_content_token_count or 0])
            if usage.traffic_type:
                traffic.add(getattr(usage.traffic_type, "name", str(usage.traffic_type)))
        if not response.candidates or not response.candidates[0].content:
            break
        contents.append(response.candidates[0].content)
        calls = response.function_calls or []
        if not calls:
            break
        if stopped_by is None and totals["prompt"] >= args.max_input_tokens:
            stopped_by = "max_input_tokens"
        if stopped_by is not None:
            nudges += 1
            if nudges > MAX_NUDGES:
                break  # still calling tools after the budget: no review, exit 3
        tool_turns += 1
        last = stopped_by is None and tool_turns >= args.max_turns
        # Every call gets a response, so the history stays valid. The turn holds
        # function responses only: a text part beside them makes Vertex answer 400
        # ("Requests ending with a model turn are not supported").
        replies = []
        for call in calls:
            tool_calls[call.name] = tool_calls.get(call.name, 0) + 1
            if stopped_by is not None:
                reply = {"result": BUDGET_USED}
            else:
                reply = {"result": run_tool(workspace, call.name, dict(call.args or {}))}
                if last:
                    reply["note"] = LAST_TOOL_TURN
            replies.append(types.Part.from_function_response(name=call.name, response=reply))
        if last:
            stopped_by = "max_turns"
        contents.append(types.Content(role="user", parts=replies))

    # Priced as flex only when Vertex confirms it; a flex request may run as online.
    rates = PRICES.get((args.model, "flex" if traffic == {"ON_DEMAND_FLEX"} else "online"))
    cost = None
    if rates:
        uncached = totals["prompt"] - totals["cached"]
        cost = round(
            (uncached * rates[0] + (totals["output"] + totals["thoughts"]) * rates[1] + totals["cached"] * rates[2])
            / 1e6,
            4,
        )

    candidate = response.candidates[0] if response and response.candidates else None
    finish = candidate.finish_reason.name if candidate and candidate.finish_reason else None
    block = response.prompt_feedback.block_reason if response and response.prompt_feedback else None
    parts = (candidate.content.parts or []) if candidate and candidate.content else []
    text = "".join(p.text for p in parts if p.text and not p.thought)

    Path(args.out).write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "model": args.model,
                "model_version": response.model_version if response else None,
                "location": LOCATION,
                "flex_requested": flex_requested,
                "flex_fallback": flex_requested and not flex,
                "traffic_type": sorted(traffic),
                "turns": len([c for c in contents if c.role == "model"]),
                "tool_calls": tool_calls,
                "stopped_by": stopped_by,
                "prompt_tokens": totals["prompt"],
                "cached_tokens": totals["cached"],
                "per_turn_prompt_cached": per_turn,
                "output_tokens": totals["output"],
                "thought_tokens": totals["thoughts"],
                "est_cost_usd": cost,
                "finish_reason": finish,
                "block_reason": str(block) if block else None,
                "out": args.out,
            }
        )
    )
    if block:
        sys.exit(3)
    if finish and finish != "STOP":
        sys.exit(4)
    if not text.strip():
        sys.exit(3)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="verify that the model is reachable on Vertex (no generation)")

    review = sub.add_parser("review", help="send a briefing and write Gemini's answer to a file")
    review.add_argument("--briefing", required=True, help="the briefing (Markdown)")
    review.add_argument("--attach", nargs="*", default=[], help="files appended verbatim, inside --root or --data")
    review.add_argument("--diff-base", help="inline the diff against this ref and the changed files' text")
    review.add_argument(
        "--flex",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Flex PayGo, half price and slower (default: on where the model supports it)",
    )
    review.add_argument("--root", default=".", help="repository Gemini may read (tracked files only); default cwd")
    review.add_argument("--data", help="directory of prefetched files Gemini may read as data/...")
    review.add_argument("--out", required=True, help="file for Gemini's answer")
    review.add_argument("--thinking", default="high", choices=["low", "medium", "high"])
    review.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    review.add_argument("--max-input-tokens", type=int, default=DEFAULT_MAX_INPUT_TOKENS)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    {"check": cmd_check, "review": cmd_review}[args.command](args)


if __name__ == "__main__":
    main()
