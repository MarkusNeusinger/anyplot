"""The error grammar of the R profile: what a failed R render's stderr tells the repair, never its message.

The R counterpart of `render/gates.error_summary`, which reads a Python traceback's
exception class and line. R prints no line numbers for a script run with `--file=`
(owner decision of 2026-10-29: stderr only, no line numbers in PR 3a), so the summary
names where the error happened instead, in a closed shape:

* the function of the first error line: base R's `Error in fn(args) :` and rlang's
  ``Error in `fn()`:`` (ggplot2, dplyr and tidyr since rlang 1.0), as `fn()`;
* rlang's chained cause, ``Caused by error in `fn()`:``, and ggplot2's layer, `Error
  occurred in the 1st layer.`;
* the last three names of base R's `Calls:` line, the call stack at the error;
* fixed texts for the resource errors: out of memory (`cannot allocate vector`, `vector
  memory exhausted`), recursion (`C stack usage`, `evaluation nested too deeply`,
  `infinite recursion`), and a missing package (`there is no package called`, with the
  package's name when it is a valid one).

Names pass only when they are R names (`_NAME`: letters, digits, dots and underscores,
optionally `pkg::`), so neither the message, which can quote a cell of the user's data,
nor anything else of the error text reaches the repair. Without an error line the
summary is a fixed text, as in Python.
"""

import re


NO_ERROR_OUTPUT = "no error output"
NO_ERROR_LINE = "an error that printed no Error line"
OUT_OF_MEMORY = "out of memory"
RECURSION = "recursion too deep"
MISSING_PACKAGE = "a package that is not installed"
MAX_CALLS = 3
MAX_NAME_CHARS = 60

_NAME = re.compile(r"(?:[A-Za-z][A-Za-z0-9.]*::)?(?:[A-Za-z.][A-Za-z0-9._]*|`[^`\n]{1,60}`)")
_ERROR_RLANG = re.compile(r"^Error in `(?P<call>[^`\n]{1,200})`\s*:")
_ERROR_BASE = re.compile(r"^Error in (?P<call>\S[^\n]{0,200})")
_ERROR_BARE = re.compile(r"^Error\s*:")
_CAUSED = re.compile(r"^Caused by error in `(?P<call>[^`\n]{1,200})`\s*:")
_LAYER = re.compile(r"\bin the (?P<ordinal>\d{1,3}(?:st|nd|rd|th)) layer\b")
_CALLS = re.compile(r"^Calls:\s*(?P<calls>.*)$")
_PACKAGE = re.compile(r"there is no package called ['‘`\"]?(?P<package>[A-Za-z][A-Za-z0-9.]{0,40})['’`\"]?")
_PACKAGE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9.]{1,40}")
_MEMORY = re.compile(r"cannot allocate (?:vector|memory)|vector memory (?:exhausted|limit)")
_RECURSION = re.compile(r"C stack usage|evaluation nested too deeply|infinite recursion|stack overflow")


def _function(call: str) -> str | None:
    """`fn()` for a call's text `fn(...)` or `fn()`; None when it is no call of an R name (`df$x`, `x[1]`)."""
    text = call.strip()
    match = _NAME.match(text)
    if match is None or len(match.group(0)) > MAX_NAME_CHARS or not text[match.end() :].startswith("("):
        return None
    return f"{match.group(0).strip('`')}()"


def error_summary(stderr_tail: str) -> str:
    """Where an R render failed: the erroring function, its cause and layer, the last calls; never the message."""
    lines = [line.strip() for line in stderr_tail.splitlines() if line.strip()]
    if not lines:
        return NO_ERROR_OUTPUT
    text = "\n".join(lines)
    if _MEMORY.search(text):
        return OUT_OF_MEMORY
    if _RECURSION.search(text):
        return RECURSION
    package = _PACKAGE.search(text)
    if package is not None:
        name = package.group("package")
        return f"{MISSING_PACKAGE} ({name})" if _PACKAGE_NAME.fullmatch(name) else MISSING_PACKAGE
    where: str | None = None
    found = False
    for line in lines:
        match = _ERROR_RLANG.match(line) or _ERROR_BASE.match(line)
        if match is not None:
            found, where = True, _function(match.group("call"))
            break
        if _ERROR_BARE.match(line):
            found = True
            break
    if not found:
        return NO_ERROR_LINE
    parts = [f"error in {where}" if where is not None else "error"]
    cause = next((match for match in map(_CAUSED.match, lines) if match is not None), None)
    caused = _function(cause.group("call")) if cause is not None else None
    if caused is not None:
        parts.append(f"caused by {caused}")
    layer = _LAYER.search(text)
    if layer is not None:
        parts.append(f"in the {layer.group('ordinal')} layer")
    calls = next((match for match in map(_CALLS.match, lines) if match is not None), None)
    if calls is not None:
        names = [name for name in (part.strip() for part in calls.group("calls").split("->")) if _is_name(name)]
        if names:
            parts.append("calls: " + " -> ".join(names[-MAX_CALLS:]))
    return "; ".join(parts)


def _is_name(text: str) -> bool:
    match = _NAME.fullmatch(text)
    return match is not None and len(text) <= MAX_NAME_CHARS
