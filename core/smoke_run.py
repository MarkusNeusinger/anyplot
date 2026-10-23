"""The perturbation smoke run: does a Python implementation still draw on other tables?

The static checker (`core/adaptability.py`) tests proxies; this module runs the file
(docs/concepts/adaptable-code.md, "Perturbation smoke run" and "The adapt route"). It
composes the pure parts of PR 1: `core.adaptability` finds the `# Data` block and the
column constants, `core.perturbation` builds the perturbed tables and the source to run,
`core.canvas` measures a render and `core.render_identity` compares two. What it adds is
the execution: a sample probe, one process per table and theme, the stale-label hook, the
mapping of an error back to the original source and the JSON record.

Three commands (exit codes are for people; the workflows record the JSON and never gate):

* `run SOURCE`: the smoke run of one implementation. The sample probe runs the head and
  the block once (`ANYPLOT_THEME=light`) and pickles `df` with the column each role's
  constant names. Every perturbed table then replaces the block, the column constants are
  renamed through their role comments, and the whole file runs once per theme in a fresh
  directory, exactly as the generator's Step 3 runs it: `<python> -P {library}.py` with
  `ANYPLOT_THEME`, `MPLBACKEND=Agg`, `PYTHONHASHSEED=0` and `PYTHONDONTWRITEBYTECODE=1`,
  in a process group that a timeout kills whole (bokeh and kaleido start Chrome). An
  execution passes when it exits 0 and writes `plot-{theme}.png` on the canvas; for
  matplotlib and seaborn the `renamed` table must also leave no drawn text that shows a
  retired sample category. The run passes when every binding table passes in every theme;
  an advisory table (`missing_nullable`) is reported, never failed. Exit 0 on pass or
  skipped, 1 on fail, 2 when the run cannot happen (`why: runner_error`).
* `pair --new NEW --prev PREV --out-dir DIR`: both sources rendered unchanged in one
  environment, the new one first (its processes have exited before the predecessor's PNGs
  exist), the raw PNGs copied to `DIR/new/` and `DIR/prev/`, and the render identity of
  each theme. Exit 0 identical, 1 different, 2 error.
* `selfcheck SOURCE`: the generator's Step 3c, the static check and `run` in one command,
  with one line per attempt appended to a JSON-lines log. Exit 0 when the static check
  passes (or the spec is excluded) and the smoke run passes or is skipped for its shape.

The library's setup calls in the head (`core.adaptability.SETUP_CALLS`) run unchanged in
the probe and in every execution; nothing is stripped. Only the 8 Python libraries
(`core.adaptability.LIBRARIES`) run; the others are `skipped` with `why: not_python`.

Mechanics decided here (PR 2 contract, section 10): executions run in parallel threads
(4, or 2 for the Chrome-driven bokeh and plotly), each in its own directory under one
temporary root; stdout and stderr go to files, so a straggler such as a Chrome that holds
the pipes cannot stall the run, and the process group is killed after every execution.
The stale-label hook wraps `matplotlib.text.Text.draw` through a runpy shim, so it sees
the text that was drawn, not every `Text` object a figure holds (an undrawn tick label or
a hidden axis); it skips the mandated title (any text with "anyplot.ai") and retired
values that read as prose, numbers or single characters, as the static checker does.
The executions do not inherit `PYTHONPATH`, so a file runs as Step 3 runs it even when
the runner itself comes from a workflow-ref copy of `core/`.

Usage::

    python -m core.smoke_run run plots/bar-grouped/implementations/python/matplotlib.py --out smoke.json
    python -m core.smoke_run pair --new NEW.py --prev PREV/matplotlib.py --out-dir /tmp/pair --out pair.json
    python -m core.smoke_run selfcheck plots/bar-grouped/implementations/python/matplotlib.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

from core.adaptability import (
    CHECKER_VERSION,
    LIBRARIES,
    MIN_SAMPLE_CHARS,
    PROSE_WORDS,
    RULE_CLASSES,
    Record,
    check_file,
    check_source,
    library_of,
    spec_context,
)
from core.canvas import TOLERANCE, NotAPngError, check_png, png_size
from core.constants import LIBRARY_LANGUAGES
from core.perturbation import Perturbation, perturbations, smoke_source
from core.render_identity import compare


RECORD_VERSION = 1
THEMES = ("light", "dark")
PROBE_THEME = "light"
DEFAULT_TIMEOUT = 120
DEFAULT_WORKERS = 4
LIBRARY_WORKERS = {"bokeh": 2, "plotly": 2}
"""Libraries whose every execution starts a headless Chrome get fewer parallel executions."""
STALE_LABEL_LIBRARIES = frozenset({"matplotlib", "seaborn"})
SKIPPED_SHAPES = ("generated", "network", "excluded")
TITLE_MARK = "anyplot.ai"
DEFAULT_SELFCHECK_LOG = Path("/tmp/anyplot-selfcheck.jsonl")
DEFAULT_SELFCHECK_STATIC = Path("/tmp/anyplot-selfcheck-static.json")
DEFAULT_SELFCHECK_SMOKE = Path("/tmp/anyplot-selfcheck-smoke.json")

SAMPLE_FILE = "sample.pkl"
DATA_FILE = "data.pkl"
TEXTS_FILE = "texts.json"
HOOK_FILE = "_anyplot_text_hook.py"
STDOUT_FILE = "stdout.txt"
STDERR_FILE = "stderr.txt"
_MAX_ERROR_CHARS = 300
_MAX_CODE_CHARS = 120
_TRACEBACK = "Traceback (most recent call last):"
_IGNORED = "Exception ignored"
_FRAME = re.compile(r'^\s*File "(?P<file>.+)", line (?P<line>\d+)')
_NUMBER = re.compile(r"^[-+−]?\d[\d,._]*%?$")

TEXT_HOOK = '''"""Run an implementation and record every matplotlib text it draws (core/smoke_run.py, stale labels)."""

import atexit
import functools
import json
import runpy
import sys


def _main():
    target, out = sys.argv[1], sys.argv[2]
    drawn = []

    def _write():
        with open(out, "w", encoding="utf-8") as handle:
            json.dump(drawn, handle)

    atexit.register(_write)
    try:
        from matplotlib.text import Text
    except ImportError:
        Text = None
    if Text is not None:
        original = Text.draw

        @functools.wraps(original)
        def draw(self, renderer, *args, **kwargs):
            text = self.get_text()
            if self.get_visible() and text:
                drawn.append(str(text))
            return original(self, renderer, *args, **kwargs)

        Text.draw = draw
    sys.argv = [target]
    runpy.run_path(target, run_name="__main__")


_main()
'''


def code_sha256(text: str) -> str:
    """SHA-256 of a source without its leading docstring header (the workflow rewrites `Quality:` and `Updated:`).

    impl-review's record step reimplements this byte for byte; a parity test pins the two.
    """
    body = text.lstrip()
    if body.startswith('"""'):
        end = body.find('"""', 3)
        if end != -1:
            body = body[end + 3 :]
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def language_of(library: str | None) -> str | None:
    """The language of a catalogue library (`core.constants.LIBRARY_LANGUAGES`), None for an unknown one."""
    return LIBRARY_LANGUAGES.get(library) if library else None


def execution_env(theme: str) -> dict[str, str]:
    """The environment of one execution: the runner's, without `PYTHONPATH`, plus the pipeline's theme settings."""
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    env.update(ANYPLOT_THEME=theme, MPLBACKEND="Agg", PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    return env


# --- one execution -----------------------------------------------------------------------------


@dataclass
class Execution:
    """One process: its exit code (None on a timeout), its stderr and its wall time."""

    returncode: int | None
    stderr: str
    seconds: float

    @property
    def timed_out(self) -> bool:
        return self.returncode is None


def _kill_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError, PermissionError:
        pass


def execute(argv: Sequence[str], cwd: Path, env: Mapping[str, str], timeout: float) -> Execution:
    """Run `argv` in `cwd` in a new process group, killed whole on a timeout and after the run.

    stdout and stderr go to files in `cwd`: a pipe would let a straggler that inherited it (a
    Chrome the script did not stop) hold the run until the timeout.
    """
    start = time.monotonic()
    with (cwd / STDOUT_FILE).open("wb") as out, (cwd / STDERR_FILE).open("wb") as err:
        process = subprocess.Popen(
            list(argv), cwd=cwd, env=dict(env), stdin=subprocess.DEVNULL, stdout=out, stderr=err, start_new_session=True
        )
        try:
            returncode: int | None = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            returncode = None
            _kill_group(process.pid)
            process.wait()
        finally:
            _kill_group(process.pid)
    stderr = (cwd / STDERR_FILE).read_text(encoding="utf-8", errors="replace")
    return Execution(returncode, stderr, time.monotonic() - start)


def _same_file(name: str, script: Path) -> bool:
    return os.path.realpath(os.path.join(script.parent, name)) == os.path.realpath(script)


def traceback_error(stderr: str, script: Path) -> tuple[str | None, int | None]:
    """The exception line of the last traceback in `stderr` and the innermost line it names in `script`.

    A syntax error in the script prints its frame without a "Traceback" header, so the search runs
    over the last traceback when there is one and over all of stderr otherwise. A traceback that
    follows "Exception ignored in ..." (a destructor at shutdown, say selenium's) is not the
    error. Without a frame line, the error is stderr's last non-empty line.
    """
    lines = stderr.splitlines()
    starts = [index for index, text in enumerate(lines) if text.startswith(_TRACEBACK)]
    raised = [index for index in starts if index == 0 or not lines[index - 1].startswith(_IGNORED)]
    starts = raised or starts
    block = lines[starts[-1] + 1 :] if starts else lines
    ignored = next((index for index, text in enumerate(block) if text.startswith(_IGNORED)), None)
    if ignored is not None and ignored > 0:
        block = block[:ignored]
    line: int | None = None
    last_frame = -1
    for index, text in enumerate(block):
        match = _FRAME.match(text)
        if match:
            last_frame = index
            if _same_file(match["file"], script):
                line = int(match["line"])
    message = None
    if last_frame >= 0:
        message = next((text.strip() for text in block[last_frame + 1 :] if text and not text[0].isspace()), None)
    if message is None:
        tail = [text.strip() for text in lines if text.strip()]
        message = tail[-1] if tail else None
    if message is not None and len(message) > _MAX_ERROR_CHARS:
        message = message[: _MAX_ERROR_CHARS - 1] + "…"
    return message, line


def line_map(original: str, executed: str) -> dict[int, int]:
    """Each 1-based line of `executed` mapped to a line of `original`.

    The executed source is the original with its block replaced and its column constants
    rewritten (a constant spread over several lines becomes one), so the lines below the
    block shift by the difference in block length. A line that has no counterpart maps to
    the first original line of the region it replaced.
    """
    executed_lines, original_lines = executed.splitlines(), original.splitlines()
    mapping: dict[int, int] = {}
    if not original_lines:
        return mapping
    matcher = SequenceMatcher(None, executed_lines, original_lines, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        for i in range(i1, i2):
            if tag == "equal":
                j = j1 + (i - i1)
            elif j2 > j1:
                j = j1 + min(i - i1, j2 - j1 - 1)
            else:
                j = min(j1, len(original_lines) - 1)
            mapping[i + 1] = j + 1
    return mapping


def source_line(source: str, line: int | None) -> str | None:
    """The stripped text of a 1-based line of `source`, cut to a readable length."""
    if line is None:
        return None
    lines = source.splitlines()
    if not 1 <= line <= len(lines):
        return None
    text = lines[line - 1].strip()
    return text if len(text) <= _MAX_CODE_CHARS else text[: _MAX_CODE_CHARS - 1] + "…"


def _checkable(value: str) -> bool:
    """A retired category a drawn text can be tied to: not prose ("Total"), not a number, not one character."""
    text = value.strip()
    return len(text) >= MIN_SAMPLE_CHARS and text.lower() not in PROSE_WORDS and not _NUMBER.match(text)


def stale_labels(texts: Sequence[str], retired: frozenset[str]) -> list[tuple[str, str]]:
    """`(text, retired category)` for each drawn text that shows a retired category as a whole word."""
    patterns = [
        (value, re.compile(rf"(?<!\w){re.escape(value)}(?!\w)")) for value in sorted(retired) if _checkable(value)
    ]
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for text in texts:
        if text in seen or TITLE_MARK in text:
            continue
        for value, pattern in patterns:
            if pattern.search(text):
                found.append((text, value))
                seen.add(text)
                break
    return found


# --- the smoke run -----------------------------------------------------------------------------


@dataclass
class _Task:
    """One execution of one perturbed table in one theme, and what it found."""

    index: int
    perturbation: Perturbation
    theme: str
    passed: bool = False
    error: str | None = None
    line: int | None = None
    canvas: str | None = None
    stale: list[str] = field(default_factory=list)
    seconds: float = 0.0


@dataclass
class SmokeRun:
    """The inputs of one `run` and the record it builds (`to_dict`)."""

    source_path: Path
    library: str | None
    themes: tuple[str, ...]
    spec_id: str | None = None
    source: str | None = None
    record: Record | None = None
    status: str = "skipped"
    why: str = "runner_error"
    error: str | None = None
    sample: dict[str, object] | None = None
    results: list[dict[str, object]] = field(default_factory=list)
    seconds: float = 0.0

    @property
    def failed(self) -> list[str]:
        return [str(r["name"]) for r in self.results if r["status"] == "fail" and not r["advisory"]]

    @property
    def advisory_failed(self) -> list[str]:
        return [str(r["name"]) for r in self.results if r["status"] == "fail" and r["advisory"]]

    def exit_code(self) -> int:
        if self.why == "runner_error":
            return 2
        return 1 if self.status == "fail" else 0

    def to_dict(self) -> dict[str, object]:
        record = self.record
        return {
            "v": RECORD_VERSION,
            "tool": "core.smoke_run run",
            "checker_version": CHECKER_VERSION,
            "source": str(self.source_path),
            "code_sha256": code_sha256(self.source) if self.source is not None else None,
            "spec": self.spec_id,
            "library": self.library,
            "language": language_of(self.library),
            "shape": record.shape if record else None,
            "color_role": record.color_role if record else None,
            "static_status": record.status if record else None,
            "themes": list(self.themes),
            "status": self.status,
            "why": self.why,
            "error": self.error,
            "sample": self.sample,
            "results": self.results,
            "failed": self.failed,
            "advisory_failed": self.advisory_failed,
            "seconds": round(self.seconds, 1),
        }

    def summary(self) -> list[str]:
        """One summary line and one line per perturbation."""
        head = f"smoke_run {self.spec_id or '?'} {self.library or '?'}: {self.status}"
        if self.why != "-":
            head += f" ({self.why})"
        if self.results:
            head += (
                f": {len(self.results)} perturbations, {len(self.failed)} failed, "
                f"{len(self.advisory_failed)} advisory failed"
            )
        elif self.error:
            head += f": {self.error}"
        elif self.sample and self.sample.get("error"):
            line = self.sample.get("line")
            head += f": sample {'line ' + str(line) + ': ' if line else ''}{self.sample['error']}"
        out = [head]
        for result in self.results:
            if result["status"] == "pass":
                label = "pass"
            else:
                label = "fail (advisory)" if result["advisory"] else "FAIL"
            text = f"  {result['name']!s:<18} {label}"
            if result["status"] != "pass":
                where = f"line {result['line']}: " if result["line"] is not None else ""
                text += f"  {where}{result['error']}"
                if result["code"]:
                    text += f"  |  {result['code']}"
                if result["theme"] and result["theme"] != self.themes[0]:
                    text += f"  [{result['theme']}]"
            out.append(text)
        return out


def run(
    source_path: Path,
    *,
    spec_path: Path | None = None,
    spec_id: str | None = None,
    library: str | None = None,
    themes: Sequence[str] = THEMES,
    timeout: float = DEFAULT_TIMEOUT,
    workers: int | None = None,
    python: str | None = None,
    skip_if_static_fails: bool = False,
    keep: Path | None = None,
) -> SmokeRun:
    """The perturbation smoke run of one source (module docstring); never raises."""
    started = time.monotonic()
    library = (
        library or library_of(source_path) or (source_path.stem if source_path.stem in LIBRARY_LANGUAGES else None)
    )
    smoke = SmokeRun(source_path, library, tuple(themes))
    try:
        _run(smoke, spec_path, spec_id, timeout, workers, python, skip_if_static_fails, keep)
    except Exception as exc:  # the record is written whatever happens; the workflows read why
        smoke.status, smoke.why, smoke.error = "skipped", "runner_error", f"{type(exc).__name__}: {exc}"
    smoke.seconds = time.monotonic() - started
    return smoke


def _run(
    smoke: SmokeRun,
    spec_path: Path | None,
    spec_id: str | None,
    timeout: float,
    workers: int | None,
    python: str | None,
    skip_if_static_fails: bool,
    keep: Path | None,
) -> None:
    library, source_path = smoke.library, smoke.source_path
    try:
        smoke.source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        smoke.error = f"cannot read the source: {exc}"
        if library is not None and library not in LIBRARIES and library in LIBRARY_LANGUAGES:
            smoke.why = "not_python"
        return
    if library is None:
        smoke.error = f"cannot tell the library from {source_path.name}; pass --library"
        return
    if library not in LIBRARIES:
        if library in LIBRARY_LANGUAGES:
            smoke.why = "not_python"
        else:
            smoke.error = f"unknown library {library!r}"
        return
    if spec_path is None:
        if len(source_path.parents) < 3:
            smoke.error = "cannot find the spec next to the source; pass --spec"
            return
        spec_path = source_path.parents[2] / "specification.md"
    try:
        smoke.spec_id, roles, shape = spec_context(spec_path, spec_id)
    except (OSError, UnicodeDecodeError) as exc:
        smoke.error = f"cannot read the spec: {exc}"
        return
    interpreter = python or sys.executable
    if not interpreter or shutil.which(interpreter) is None:
        smoke.error = f"no Python interpreter at {interpreter!r}"
        return
    record = check_source(smoke.source, roles, shape, library=library)
    smoke.record = record
    if skip_if_static_fails and record.status == "fail":
        smoke.why = "static_failed"
        return
    if shape in SKIPPED_SHAPES:
        smoke.why = f"shape:{shape}"
        return
    if record.block is None:
        smoke.why = "no_block"
        return

    root = Path(tempfile.mkdtemp(prefix="anyplot-smoke-")) if keep is None else keep
    root.mkdir(parents=True, exist_ok=True)
    try:
        sample = _probe(smoke.source, record, library, interpreter, root / "00-sample", timeout)
        smoke.sample = sample.as_dict()
        if sample.df is None:
            smoke.status, smoke.why = "fail", "sample_failed"
            return
        items = perturbations(sample.df, sample.columns, roles, shape, record.color_role)
        if not items:
            smoke.why = f"shape:{shape}"
            return
        count = workers or LIBRARY_WORKERS.get(library, DEFAULT_WORKERS)
        tasks = [_Task(index, item, theme) for index, item in enumerate(items, start=1) for theme in smoke.themes]
        with ThreadPoolExecutor(max_workers=max(1, count)) as pool:
            list(
                pool.map(
                    lambda task: _execute_task(task, smoke.source or "", library, interpreter, root, timeout), tasks
                )
            )
        smoke.results = [_result(item, [t for t in tasks if t.perturbation is item], smoke.source) for item in items]
        smoke.status, smoke.why = ("fail", "perturbation_failed") if smoke.failed else ("pass", "-")
    finally:
        if keep is None:
            shutil.rmtree(root, ignore_errors=True)


@dataclass
class _Sample:
    df: pd.DataFrame | None
    columns: dict[str, str | list[str]]
    error: str | None = None
    line: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "pass" if self.df is not None else "fail",
            "rows": len(self.df) if self.df is not None else None,
            "columns": dict(self.columns),
            "error": self.error,
            "line": self.line,
        }


def _probe_epilogue(constants: Mapping[str, str], path: Path) -> str:
    """Pickle `df` and the column each role's constant names; exit with a message when no DataFrame `df` exists."""
    return (
        "\n\n# --- core.smoke_run sample probe ---\n"
        "import pickle as _anyplot_pickle\n"
        "import sys as _anyplot_sys\n\n"
        "import pandas as _anyplot_pd\n\n"
        '_anyplot_df = globals().get("df")\n'
        "if _anyplot_df is None:\n"
        '    _anyplot_sys.exit("smoke_run: the Data block binds no df")\n'
        "if not isinstance(_anyplot_df, _anyplot_pd.DataFrame):\n"
        '    _anyplot_sys.exit(f"smoke_run: df is a {type(_anyplot_df).__name__}, not a pandas DataFrame")\n'
        f"_anyplot_names = {dict(constants)!r}\n"
        "_anyplot_columns = {role: globals().get(name) for role, name in _anyplot_names.items()}\n"
        f"with open({str(path)!r}, 'wb') as _anyplot_file:\n"
        '    _anyplot_pickle.dump({"df": _anyplot_df, "columns": _anyplot_columns}, _anyplot_file)\n'
    )


def _probe(source: str, record: Record, library: str, python: str, directory: Path, timeout: float) -> _Sample:
    """Run the head, the constants and the block (the lines above `# Plot`) and read `df` back."""
    assert record.block is not None
    plot_line = record.block[1]
    directory.mkdir(parents=True, exist_ok=True)
    head = "".join(source.splitlines(keepends=True)[: plot_line - 1])
    script = directory / f"{library}.py"
    script.write_text(head + _probe_epilogue(record.constants, directory / SAMPLE_FILE), encoding="utf-8")
    execution = execute([python, "-P", script.name], directory, execution_env(PROBE_THEME), timeout)
    if execution.timed_out:
        return _Sample(None, {}, f"timed out after {timeout:g} s")
    if execution.returncode != 0 or not (directory / SAMPLE_FILE).is_file():
        error, line = traceback_error(execution.stderr, script)
        return _Sample(
            None, {}, error or f"exit code {execution.returncode}", line if line and line < plot_line else None
        )
    with (directory / SAMPLE_FILE).open("rb") as handle:
        payload = pickle.load(handle)  # written by the probe of the file under test; the runner is no sandbox
    df = payload["df"]
    columns: dict[str, str | list[str]] = {}
    for role, value in payload["columns"].items():
        if isinstance(value, str) and value in df.columns:
            columns[role] = value
        elif (
            isinstance(value, list | tuple)
            and value
            and all(isinstance(item, str) and item in df.columns for item in value)
        ):
            columns[role] = list(value)
    return _Sample(df, columns)


def _execute_task(task: _Task, source: str, library: str, python: str, root: Path, timeout: float) -> None:
    item, theme = task.perturbation, task.theme
    directory = root / f"{task.index:02d}-{item.name}-{theme}"
    directory.mkdir(parents=True, exist_ok=True)
    data = directory / DATA_FILE
    item.df.to_pickle(data)
    code = smoke_source(source, item, str(data))
    script = directory / f"{library}.py"
    script.write_text(code, encoding="utf-8")
    hook = item.name == "renamed" and library in STALE_LABEL_LIBRARIES and bool(item.retired)
    if hook:
        (directory / HOOK_FILE).write_text(TEXT_HOOK, encoding="utf-8")
        argv = [python, "-P", HOOK_FILE, str(script.resolve()), str((directory / TEXTS_FILE).resolve())]
    else:
        argv = [python, "-P", script.name]
    execution = execute(argv, directory, execution_env(theme), timeout)
    task.seconds = execution.seconds
    if execution.timed_out:
        task.error = f"timed out after {timeout:g} s"
        return
    if execution.returncode != 0:
        error, line = traceback_error(execution.stderr, script)
        task.error = error or f"exit code {execution.returncode}"
        task.line = line_map(source, code).get(line) if line is not None else None
        return
    png = directory / f"plot-{theme}.png"
    if not png.is_file():
        task.error = f"no plot-{theme}.png written"
        return
    try:
        verdict = check_png(png, library)
    except (NotAPngError, OSError) as exc:
        task.error = f"plot-{theme}.png is not a readable PNG: {exc}"
        return
    task.canvas = f"{verdict.width}x{verdict.height}"
    if not verdict.ok:
        (tw, th) = verdict.target
        task.error = f"canvas {verdict.width}x{verdict.height}, target {tw}x{th} (+-{TOLERANCE} px)"
        return
    if hook:
        try:
            texts = json.loads((directory / TEXTS_FILE).read_text(encoding="utf-8"))
        except OSError, ValueError:
            texts = []
        stale = stale_labels([str(text) for text in texts], item.retired)
        if stale:
            task.stale = [text for text, _ in stale]
            text, value = stale[0]
            task.error = f"stale label: {text!r} shows the retired category {value!r}"
            return
    task.passed = True


def _result(item: Perturbation, tasks: Sequence[_Task], source: str | None) -> dict[str, object]:
    failing = next((task for task in tasks if not task.passed), None)
    canvas = {task.theme: task.canvas for task in tasks if task.canvas is not None}
    return {
        "name": item.name,
        "description": item.description,
        "advisory": item.advisory,
        "status": "fail" if failing else "pass",
        "rows": len(item.df),
        "theme": failing.theme if failing else None,
        "error": failing.error if failing else None,
        "line": failing.line if failing else None,
        "code": source_line(source or "", failing.line) if failing else None,
        "canvas": canvas or None,
        "stale_labels": failing.stale if failing else [],
        "seconds": round(sum(task.seconds for task in tasks), 1),
    }


# --- pair: two renders in one environment ------------------------------------------------------


@dataclass
class _Side:
    """One source of a pair: its hash, one render per theme and the first error."""

    code_sha256: str | None = None
    renders: dict[str, dict[str, object]] = field(default_factory=dict)
    error: str | None = None
    line: int | None = None

    @property
    def ok(self) -> bool:
        return bool(self.renders) and all(render["status"] == "ok" for render in self.renders.values())

    def as_dict(self) -> dict[str, object]:
        return {"code_sha256": self.code_sha256, "renders": self.renders, "error": self.error, "line": self.line}


def _render_side(
    path: Path, library: str, themes: Sequence[str], python: str, root: Path, out: Path, timeout: float
) -> _Side:
    """Render `path` unchanged once per theme and copy each raw PNG to `out/plot-{theme}.png`."""
    side = _Side()
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        side.error = f"cannot read {path}: {exc}"
        return side
    side.code_sha256 = code_sha256(source)
    out.mkdir(parents=True, exist_ok=True)

    def render(theme: str) -> tuple[str, dict[str, object], str | None, int | None]:
        directory = root / theme
        directory.mkdir(parents=True, exist_ok=True)
        script = directory / f"{library}.py"
        script.write_text(source, encoding="utf-8")
        execution = execute([python, "-P", script.name], directory, execution_env(theme), timeout)
        seconds = round(execution.seconds, 1)
        png = directory / f"plot-{theme}.png"
        error: str | None = None
        line: int | None = None
        size: list[int] | None = None
        if execution.timed_out:
            error = f"timed out after {timeout:g} s"
        elif execution.returncode != 0:
            error, line = traceback_error(execution.stderr, script)
            error = error or f"exit code {execution.returncode}"
        elif not png.is_file():
            error = f"no plot-{theme}.png written"
        else:
            try:
                size = list(png_size(png))
            except (NotAPngError, OSError) as exc:
                error = f"plot-{theme}.png is not a readable PNG: {exc}"
        if error is None:
            shutil.copyfile(png, out / f"plot-{theme}.png")
        status = "ok" if error is None else "fail"
        return theme, {"status": status, "size": size, "seconds": seconds}, error, line

    with ThreadPoolExecutor(max_workers=max(1, len(themes))) as pool:
        rendered = list(pool.map(render, themes))
    for theme, render_record, error, line in rendered:
        side.renders[theme] = render_record
        if error is not None and side.error is None:
            side.error, side.line = f"{theme}: {error}", line
    return side


def pair(
    new_path: Path,
    prev_path: Path,
    out_dir: Path,
    *,
    library: str | None = None,
    themes: Sequence[str] = THEMES,
    timeout: float = DEFAULT_TIMEOUT,
    python: str | None = None,
) -> dict[str, object]:
    """Render the new source, then the predecessor, in one environment and compare the raw renders per theme."""
    library = library or library_of(new_path)
    themes = tuple(themes)
    record: dict[str, object] = {
        "v": RECORD_VERSION,
        "tool": "core.smoke_run pair",
        "library": library,
        "themes": list(themes),
        "new": None,
        "prev": None,
        "identity": None,
        "status": "error",
        "why": "new_render_failed",
    }
    interpreter = python or sys.executable
    if library not in LIBRARIES:
        record["new"] = _Side(error=f"{library!r} is not one of the Python libraries {', '.join(LIBRARIES)}").as_dict()
        return record
    if not interpreter or shutil.which(interpreter) is None:
        record["new"] = _Side(error=f"no Python interpreter at {interpreter!r}").as_dict()
        return record
    for side in ("new", "prev"):
        shutil.rmtree(out_dir / side, ignore_errors=True)
    root = Path(tempfile.mkdtemp(prefix="anyplot-pair-"))
    try:
        new = _render_side(new_path, library, themes, interpreter, root / "new", out_dir / "new", timeout)
        prev = _render_side(prev_path, library, themes, interpreter, root / "prev", out_dir / "prev", timeout)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    record["new"], record["prev"] = new.as_dict(), prev.as_dict()
    if not new.ok:
        return record
    if not prev.ok:
        record["why"] = "prev_render_failed"
        return record
    identity = {
        theme: compare(out_dir / "prev" / f"plot-{theme}.png", out_dir / "new" / f"plot-{theme}.png")
        for theme in themes
    }
    record["identity"] = {theme: result.to_dict() for theme, result in identity.items()}
    failing = [theme for theme, result in identity.items() if not result.passed]
    if any(not result.same_size for result in identity.values()):
        why = "size_changed"
    elif not failing:
        why = "-"
    elif len(failing) == 1:
        why = f"identity_{failing[0]}"
    else:
        why = "identity_both"
    record["status"], record["why"] = ("identical", "-") if why == "-" else ("different", why)
    return record


def pair_exit_code(record: Mapping[str, object]) -> int:
    return {"identical": 0, "different": 1}.get(str(record.get("status")), 2)


def pair_summary(record: Mapping[str, object]) -> str:
    identity = record.get("identity")
    fractions = ""
    if isinstance(identity, dict):
        fractions = " " + " ".join(
            f"{theme}={value['fraction']:.4f}" if value.get("fraction") is not None else f"{theme}=size"
            for theme, value in identity.items()
        )
    head = f"smoke_run pair {record.get('library')}: {record.get('status')} ({record.get('why')}){fractions}"
    errors = [
        f"  {side}: {side_record['error']}"
        for side in ("new", "prev")
        if isinstance(side_record := record.get(side), dict) and side_record.get("error")
    ]
    return "\n".join([head, *errors])


# --- selfcheck: the generator's Step 3c --------------------------------------------------------


def selfcheck(
    source_path: Path,
    *,
    log: Path = DEFAULT_SELFCHECK_LOG,
    static_out: Path = DEFAULT_SELFCHECK_STATIC,
    smoke_out: Path = DEFAULT_SELFCHECK_SMOKE,
    runner: Callable[[Path], SmokeRun] | None = None,
) -> tuple[int, list[str]]:
    """The static check and the smoke run of one catalogue file, logged as one attempt; returns (exit, lines)."""
    if library_of(source_path) is None:
        return 2, [f"::error::selfcheck cannot tell the library from {source_path.name}"]
    try:
        source = source_path.read_text(encoding="utf-8")
        record = check_file(source_path)  # what `python -m core.adaptability check SOURCE` records
    except (OSError, UnicodeDecodeError, IndexError) as exc:
        return 2, [f"::error::selfcheck cannot read its input: {exc}"]
    static_out.parent.mkdir(parents=True, exist_ok=True)
    smoke_out.parent.mkdir(parents=True, exist_ok=True)
    static_out.write_text(json.dumps(record.to_dict(), ensure_ascii=False) + "\n", encoding="utf-8")
    smoke = (runner or run)(source_path)
    smoke_out.write_text(json.dumps(smoke.to_dict(), ensure_ascii=False) + "\n", encoding="utf-8")

    classes = record.classes()
    binding = [cls for cls in classes if not RULE_CLASSES[cls].advisory]
    advisory = [cls for cls in classes if RULE_CLASSES[cls].advisory]
    attempt = _attempts(log) + 1
    entry = {
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "attempt": attempt,
        "code_sha256": code_sha256(source),
        "static": record.status,
        "classes": binding,
        "advisory": advisory,
        "smoke": smoke.status,
        "failed": smoke.failed,
        "advisory_failed": smoke.advisory_failed,
    }
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    static_ok = record.status in ("pass", "excluded")
    smoke_ok = smoke.status == "pass" or (smoke.status == "skipped" and smoke.why.startswith("shape:"))
    if smoke.why == "runner_error":
        code = 2
    else:
        code = 0 if static_ok and smoke_ok else 1
    head = f"static: {record.status}" + (f" ({', '.join(binding)})" if binding else "")
    if advisory:
        head += f"; advisory: {', '.join(advisory)}"
    lines = [head, *record.defect_lines(), *smoke.summary()]
    lines.append(f"selfcheck attempt {attempt}: {'pass' if code == 0 else 'fail'}")
    return code, lines


def _attempts(log: Path) -> int:
    try:
        return sum(1 for line in log.read_text(encoding="utf-8").splitlines() if line.strip())
    except OSError, UnicodeDecodeError:
        return 0


# --- CLI ---------------------------------------------------------------------------------------


def _themes(text: str) -> tuple[str, ...]:
    themes = tuple(dict.fromkeys(part.strip() for part in text.split(",") if part.strip()))
    unknown = [theme for theme in themes if theme not in THEMES]
    if not themes or unknown:
        raise argparse.ArgumentTypeError(f"themes are a comma-separated subset of {','.join(THEMES)}")
    return themes


def _write_json(path: Path | None, payload: Mapping[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m core.smoke_run", description="Run a Python implementation on perturbed tables."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="the perturbation smoke run of one source")
    run_parser.add_argument("source", type=Path)
    run_parser.add_argument("--spec", type=Path, default=None, help="default: SOURCE.parents[2]/specification.md")
    run_parser.add_argument("--spec-id", default=None, help="default: the spec file's directory name")
    run_parser.add_argument("--library", default=None, help="default: SOURCE's stem")
    run_parser.add_argument("--out", type=Path, default=None, help="write the JSON record here")
    run_parser.add_argument("--themes", type=_themes, default=THEMES, help="default: light,dark")
    run_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds per execution")
    run_parser.add_argument(
        "--workers", type=int, default=None, help="parallel executions (default 4; 2 for bokeh/plotly)"
    )
    run_parser.add_argument("--python", default=None, help="interpreter for the executions (default: this one)")
    run_parser.add_argument("--skip-if-static-fails", action="store_true", help="skip when the static check fails")
    run_parser.add_argument("--keep", type=Path, default=None, help="keep each execution's directory here")

    pair_parser = sub.add_parser("pair", help="render two sources in one environment and compare them")
    pair_parser.add_argument("--new", type=Path, required=True, dest="new_source")
    pair_parser.add_argument("--prev", type=Path, required=True, dest="prev_source")
    pair_parser.add_argument("--out-dir", type=Path, required=True)
    pair_parser.add_argument("--library", default=None)
    pair_parser.add_argument("--out", type=Path, default=None)
    pair_parser.add_argument("--themes", type=_themes, default=THEMES)
    pair_parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    pair_parser.add_argument("--python", default=None)

    check_parser = sub.add_parser("selfcheck", help="the generator's Step 3c: static check plus smoke run")
    check_parser.add_argument("source", type=Path)
    check_parser.add_argument("--log", type=Path, default=DEFAULT_SELFCHECK_LOG)
    check_parser.add_argument("--static-out", type=Path, default=DEFAULT_SELFCHECK_STATIC)
    check_parser.add_argument("--smoke-out", type=Path, default=DEFAULT_SELFCHECK_SMOKE)

    args = parser.parse_args(argv)
    if args.command == "run":
        smoke = run(
            args.source,
            spec_path=args.spec,
            spec_id=args.spec_id,
            library=args.library,
            themes=args.themes,
            timeout=args.timeout,
            workers=args.workers,
            python=args.python,
            skip_if_static_fails=args.skip_if_static_fails,
            keep=args.keep,
        )
        _write_json(args.out, smoke.to_dict())
        print("\n".join(smoke.summary()))
        return smoke.exit_code()
    if args.command == "pair":
        try:
            record = pair(
                args.new_source,
                args.prev_source,
                args.out_dir,
                library=args.library,
                themes=args.themes,
                timeout=args.timeout,
                python=args.python,
            )
        except Exception as exc:  # the record is written whatever happens
            record = {"v": RECORD_VERSION, "tool": "core.smoke_run pair", "status": "error", "why": "new_render_failed"}
            record["error"] = f"{type(exc).__name__}: {exc}"
        _write_json(args.out, record)
        print(pair_summary(record))
        return pair_exit_code(record)
    code, lines = selfcheck(args.source, log=args.log, static_out=args.static_out, smoke_out=args.smoke_out)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
