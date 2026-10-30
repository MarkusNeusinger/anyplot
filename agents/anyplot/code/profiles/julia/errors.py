"""The error grammar of the Julia profile: what a failed Julia render's stderr tells the repair, never its message.

The Julia counterpart of `render/gates.error_summary` (Python: the exception class and
the line) and `profiles/r/errors.py`. Julia ends an uncaught error in a script with

    ERROR: LoadError: BoundsError: attempt to access 2-element Vector{Int64} at index [5]
    Stacktrace:
     [1] throw_boundserror(A::Vector{Int64}, I::Tuple{Int64})
       @ Base ./essentials.jl:14
     ...
     [3] getindex
       @ ./essentials.jl:974 [inlined]
     [4] g(v::Vector{Int64})
       @ Main /work/plot.jl:2
     [5] top-level scope
       @ /work/plot.jl:5
     ...
    in expression starting at /work/plot.jl:5

(measured in the J1 image on 2026-10-29), so the summary reads three places in a closed
shape:

* the exception type of the first `ERROR:` line when it is one of `EXCEPTION_TYPES`
  (`BoundsError`), with the variable an `UndefVarError` names and the function a
  `MethodError` finds no method of, both only when they are Julia names; any other first
  line (`error("...")` prints its message alone, Makie's compute pipeline prints "Failed
  to resolve ...") is "an error", and a tail without the line is "an error (the tail cut
  off its first line)";
* the innermost frame in the plot (`@ Main /work/plot.jl:2` inside a function, `@
  /work/plot.jl:5` at the top level): its line, and the function the plot called there,
  the frame just inside it (`getindex`, Makie's `text!`), when that is a Julia name;
* the last `in expression starting at /work/plot.jl:N` line: the top-level statement
  that failed, named when it differs from the frame's line.

Fixed texts stand for the failures whose cause is not the plot's code alone: a process
start (`failed process: ... ProcessSignaled(31)`, the exec filter's kill), a precompiled
package image that does not match the run's flags (`--compiled-modules=strict`'s
"not available with flags", a toolchain fault), out of memory, recursion
(`StackOverflowError`) and a package that is not installed (with its name when it is a
Julia name).

Makie's stacks are long: a deep failure printed 7,674 characters, so the last 2,000
(`render/contract.MAX_STDERR_CHARS`) lose the `ERROR:` line and keep the plot's frame and
the expression line (measured; the corpus test reads both the whole stderr and its tail).
Since J2b the Julia row keeps that line in front of the tail (`RuntimeCommand.stderr_head`,
`agents/renderer/executor.stderr_tail`), so "the tail cut off its first line" is left for a
stderr past the renderer's 64 KiB read.

The lines count the run form, where the loader replaced the working form's one
placeholder line with 15 or more (`loader.loader_span`). Given the loader's span
(`loader`), the summary names the working form's lines, which the adapter edits, and a
line inside the loader as the placeholder's, "the data loader".

Names pass only when they are Julia names
(`_NAME`), so neither the message, which can quote a cell or a column of the user's
data, nor anything else of the error text reaches the repair.
"""

import re


CODE_FILE = "plot.jl"
NO_ERROR_OUTPUT = "no error output"
NO_ERROR_LINE = "an error that printed no ERROR line and no frame in the plot"
CUT_OFF = "an error (the tail cut off its first line)"
UNNAMED = "an error"
OUT_OF_MEMORY = "out of memory"
RECURSION = "recursion too deep"
MISSING_PACKAGE = "a package that is not installed"
PROCESS_STARTED = "a process start, which the sandbox refuses"
CACHE_MISS = "a precompiled package image that does not match the run's flags (a toolchain fault, not the code)"
LOADER = "the data loader"
"""What a line in the loader is called: the server's read of `data.csv`, which stands for the placeholder line."""
MAX_NAME_CHARS = 60

EXCEPTION_TYPES = frozenset(
    {
        "ArgumentError",
        "AssertionError",
        "BoundsError",
        "CanonicalIndexError",
        "CompositeException",
        "DimensionMismatch",
        "DivideError",
        "DomainError",
        "EOFError",
        "ErrorException",
        "FieldError",
        "InexactError",
        "InitError",
        "InvalidStateException",
        "KeyError",
        "MethodError",
        "MissingException",
        "OverflowError",
        "ParseError",
        "ProcessFailedException",
        "ReadOnlyMemoryError",
        "StringIndexError",
        "SystemError",
        "TaskFailedException",
        "TypeError",
        "UndefKeywordError",
        "UndefRefError",
        "UndefVarError",
    }
)
"""The exception types a summary may name: Base's, which print as `Type: message` or `Type(...)`."""

_NAME = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_]*\.)*[A-Za-z_][A-Za-z0-9_]*!?")
_ERROR = re.compile(r"^ERROR:\s*(?:LoadError:\s*)?(?P<rest>.*)$")
_TYPE = re.compile(r"(?P<type>[A-Z][A-Za-z0-9_]*)(?:\{[^}\n]*\})?(?::|\(|$)")
_UNDEFINED = re.compile(r"^UndefVarError: `(?P<name>[^`\n]{1,80})`")
_NO_METHOD = re.compile(r"^MethodError: no method matching (?P<name>[^\s(]{1,80})\(")
_FRAME = re.compile(r"^\[(?P<index>\d{1,4})\]\s+(?P<frame>.*)$")
_AT = re.compile(r"^@\s+(?:(?P<module>[A-Za-z_][\w.]*)\s+)?(?P<file>\S+?):(?P<line>\d{1,7})(?:\s|$)")
_EXPRESSION = re.compile(r"^in expression starting at (?P<file>\S+?):(?P<line>\d{1,7})$")
_PACKAGE = re.compile(r"Package (?P<package>[A-Za-z][A-Za-z0-9_]{0,40}) not found in current path")
_PROCESS = re.compile(r"failed process: |ProcessSignaled\(|ProcessExited\(")
_CACHE_MISS = re.compile(r"Precompiled image .{0,200} not available with flags")
_MEMORY = re.compile(r"\bOutOfMemoryError\b")
_RECURSION = re.compile(r"\bStackOverflowError\b")


def _is_name(text: str) -> bool:
    return len(text) <= MAX_NAME_CHARS and _NAME.fullmatch(text) is not None


def _in_code(path: str, code_file: str) -> bool:
    """Whether a frame's file is the plot: `plot.jl`, `/work/plot.jl` or any path ending in it."""
    return path == code_file or path.endswith(f"/{code_file}")


def _exception(lines: list[str]) -> str | None:
    """The first `ERROR:` line in a closed shape, or None when there is none."""
    for line in lines:
        match = _ERROR.match(line)
        if match is None:
            continue
        rest = match.group("rest")
        kind = _TYPE.match(rest)
        name = kind.group("type") if kind is not None else None
        if name not in EXCEPTION_TYPES:
            return UNNAMED
        undefined = _UNDEFINED.match(rest)
        if undefined is not None and _is_name(undefined.group("name")):
            return f"{name} for {undefined.group('name')}"
        method = _NO_METHOD.match(rest)
        if method is not None and _is_name(method.group("name")):
            return f"{name} for {method.group('name')}()"
        return name
    return None


def _plot_frame(lines: list[str], code_file: str) -> tuple[int, str | None] | None:
    """The innermost frame in the plot: its line, and the function the plot called there when it is a name."""
    previous: str | None = None
    current: str | None = None
    for line in lines:
        frame = _FRAME.match(line)
        if frame is not None:
            previous, current = current, frame.group("frame")
            continue
        at = _AT.match(line)
        if at is None or current is None or not _in_code(at.group("file"), code_file):
            continue
        called = None
        if previous is not None:
            head = re.match(r"[^\s(]+", previous)
            if head is not None and _is_name(head.group(0)):
                called = head.group(0)
        return int(at.group("line")), called
    return None


def working_line(line: int, loader: tuple[int, int] | None) -> tuple[int, bool]:
    """The working form's line for a run-form `line`, and whether it falls in the loader.

    `loader` is the loader's first line and line count in the run form (`loader.loader_span`), which replaced the
    working form's one placeholder line: a line before it stays, a line in it is the placeholder's, a line after it
    moves up by the count minus one. Without `loader` the line stays as it is.
    """
    if loader is None:
        return line, False
    first, count = loader
    if line < first:
        return line, False
    if line < first + count:
        return first, True
    return line - count + 1, False


def _at(line: int, loader: tuple[int, int] | None) -> str:
    shown, inside = working_line(line, loader)
    return f"{shown} ({LOADER})" if inside else str(shown)


def error_summary(stderr_tail: str, *, code_file: str = CODE_FILE, loader: tuple[int, int] | None = None) -> str:
    """Where a Julia render failed: the exception type, the plot's line and the function it called; never the
    message. With `loader` (`loader.loader_span` of the run form) the lines are the working form's, which the
    adapter edits, and a line in the loader is the placeholder's, named as the data loader."""
    lines = [line.strip() for line in stderr_tail.splitlines() if line.strip()]
    if not lines:
        return NO_ERROR_OUTPUT
    text = "\n".join(lines)
    if _CACHE_MISS.search(text):
        return CACHE_MISS
    if _MEMORY.search(text):
        return OUT_OF_MEMORY
    if _RECURSION.search(text):
        return RECURSION
    package = _PACKAGE.search(text)
    if package is not None:
        return f"{MISSING_PACKAGE} ({package.group('package')})"
    kind = PROCESS_STARTED if _PROCESS.search(text) else _exception(lines)
    frame = _plot_frame(lines, code_file)
    expressions = [match for match in map(_EXPRESSION.match, lines) if match is not None]
    expression = next(
        (int(match.group("line")) for match in reversed(expressions) if _in_code(match.group("file"), code_file)), None
    )
    if kind is None and frame is None and expression is None:
        return NO_ERROR_LINE
    parts = [kind or CUT_OFF]
    line = frame[0] if frame is not None else expression
    if line is not None:
        parts[0] += f" at line {_at(line, loader)}"
    if frame is not None and frame[1] is not None:
        parts.append(f"in {frame[1]}()")
    if expression is not None and line is not None and _at(expression, loader) != _at(line, loader):
        parts.append(f"the statement starts at line {_at(expression, loader)}")
    return "; ".join(parts)
