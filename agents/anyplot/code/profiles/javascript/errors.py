"""The error grammar of the JavaScript profile: what a failed render's stderr tells the repair, never its message.

The JavaScript counterpart of `profiles/julia/errors.py`. In sandbox mode the harness
(`automation/js-render/render.mjs`, JS-2) ends every failed render with one line, the last
on stderr, after its bounded summary of console errors:

    render: error: <kind> <Class> <file>:<line>: <message>

or `-` in place of `<file>:<line>` when the error has no line in the snippet. `<kind>` is
`page` (an uncaught error in the page), `import` (`ImportRefused`, `ImportNotFound`),
`build` (`SyntaxError` in the snippet, `BuildError` elsewhere), `draw` (`NoOutput`),
`crash` (`PageCrashed`), `data` (`DataError`), `timeout` (`TimeoutError`) or `harness`
(anything else); `<file>` is the code file (`plot.js`, `plot.tsx`) and `<line>` its line
in the snippet: the harness takes the page's offset off a classic script's frames, maps a
MUI X bundle's frame back through its source map, and esbuild names `plot.tsx:<line>`
itself. The summary reads the kind, the class and the line, in a closed shape:

* `page` with a class of `PAGE_CLASSES` (JavaScript's own errors and the DOM's): the class
  and the line (`TypeError at line 12`); any other class, which the snippet can name
  itself, is "an error";
* every other kind is a fixed text (`KIND_TEXTS`) with the line when it has one: an import
  the image refuses or its MUI X does not export, a syntax error, nothing drawn, a crash,
  a timeout, and the faults that are not the code's (the data file, the build outside the
  snippet, the harness);
* a stderr without the final line (the renderer killed the run, or the harness died
  before it could print it) is "an error that printed no final error line".

The message (`<message>`, up to 200 characters) can quote a cell or a column of the
user's data, and the console summary above the line can quote anything the snippet
printed, so neither reaches the repair.

The lines count the run form, whose one loader line replaced the working form's one
placeholder line (`loader.loader_span`), so a line maps to itself, and a line on the loader
is named "the data loader".
"""

import re


CODE_FILES = ("plot.js", "plot.tsx")
NO_ERROR_OUTPUT = "no error output"
NO_FINAL_LINE = "an error that printed no final error line"
UNNAMED = "an error"
LOADER = "the data loader"
"""What a line in the loader is called: the read of the harness's table, which stands for the placeholder line."""
PAGE_CLASSES = frozenset(
    {
        "Error",
        "TypeError",
        "RangeError",
        "ReferenceError",
        "SyntaxError",
        "EvalError",
        "URIError",
        "AggregateError",
        "InternalError",
        "DOMException",
        "IndexSizeError",
        "HierarchyRequestError",
        "InvalidCharacterError",
        "InvalidStateError",
        "NotFoundError",
        "NotSupportedError",
        "SecurityError",
        "NetworkError",
        "QuotaExceededError",
        "DataCloneError",
        "EncodingError",
    }
)
"""The classes a page error may be named by: ECMAScript's and the DOM's (`DOMException` names); a class of the
snippet's own, which could carry anything, is "an error"."""
KIND_TEXTS: dict[tuple[str, str | None], str] = {
    ("import", "ImportRefused"): "an import the image refuses (only the allowlisted React and MUI modules)",
    ("import", "ImportNotFound"): "an import the image's MUI X does not export",
    ("import", None): "an import the image cannot bundle",
    ("build", "SyntaxError"): "a syntax error",
    ("build", None): "a build error outside the plot's code (a toolchain fault, not the code)",
    ("draw", None): "nothing drawn: the page has no canvas, svg or img in #container",
    ("crash", None): "the page crashed (out of memory, most likely)",
    ("data", None): "the data file could not be read (a pipeline fault, not the code)",
    ("timeout", None): "the page did not settle within 15 s (a loop that does not end, or a ready signal never set)",
    ("harness", None): "a harness error (a toolchain fault, not the code)",
}
"""The fixed text of each kind, with a class where the kind has several (`None` for the rest of that kind)."""

_FINAL = re.compile(
    r"^render: error: (?P<kind>[a-z]{1,16}) (?P<cls>[A-Za-z_$][\w$]{0,63}) "
    r"(?:-|(?P<file>[^\s:]{1,64}):(?P<line>\d{1,7})): "
)


def working_line(line: int, loader: tuple[int, int] | None) -> tuple[int, bool]:
    """The working form's line for a run-form `line`, and whether it falls in the loader (`profiles/julia/errors`'s
    rule: the loader replaced the one placeholder line; JavaScript's is one line too, so only the flag can change)."""
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


def error_summary(stderr_tail: str, *, loader: tuple[int, int] | None = None, line_count: int | None = None) -> str:
    """Where a JavaScript render failed: the kind, the class and the snippet's line of the harness's final error line;
    never the message. With `loader` (`loader.loader_span` of the run form) a line on the loader is named as the data
    loader; with `line_count` (the run form's lines) a line past the code's end is left out.

    Only the last line counts: the harness prints its own there, and the console summary above it holds what the
    snippet printed, which can look like a final line (`console.error("render: error: ...")`). A thrown value that is
    no `Error` has no frame, and the harness then names a line of its own wrapper after the snippet (measured with
    `throw "text"` in a three-line snippet: `plot.js:7`), which `line_count` drops.
    """
    lines = [line.rstrip() for line in stderr_tail.splitlines() if line.strip()]
    if not lines:
        return NO_ERROR_OUTPUT
    match = _FINAL.match(lines[-1])
    if match is None:
        return NO_FINAL_LINE
    kind, cls = match.group("kind"), match.group("cls")
    if kind == "page":
        text = cls if cls in PAGE_CLASSES else UNNAMED
    else:
        text = KIND_TEXTS.get((kind, cls)) or KIND_TEXTS.get((kind, None)) or UNNAMED
    file, line = match.group("file"), match.group("line")
    if line is not None and file in CODE_FILES and (line_count is None or int(line) <= line_count):
        text += f" at line {_at(int(line), loader)}"
    return text
