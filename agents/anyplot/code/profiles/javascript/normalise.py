"""The JavaScript normaliser: catalogue code of Chart.js, D3, ECharts, Highcharts and MUI X in, code with one canvas.

The JavaScript counterpart of `profiles/julia/normalise.py`. The harness draws the page at a
fixed size and screenshots it (`automation/js-render/render.mjs`), so the canvas follows
from the orientation directive alone, and the normaliser has less to rewrite than for the
languages that save their own figure. `normalise(code, library=...)` makes these rewrites,
in the order `_STEPS` runs them, each only when it applies:

1. **Catalogue header.** The four comment lines that open every catalogue file
   (`// anyplot.ai`, `// <spec-id>: <title>`, `// Library: ...`, `// Quality: ...`, all
   1,617 files on 2026-10-30) go with the blank lines after them. Only lines of that shape
   go, so a comment below the header, the directive among them, stays.
2. **Orientation directive.** The file gets exactly one directive, in the form
   `//# anyplot-orientation: square` (or `landscape`), on its first line: the
   orientation the harness picks now (the first line that matches its pattern, else
   landscape; `regions.find_directives`), so the render does not change. Every other
   directive line that is a comment of its own goes. 724 catalogue files carry one, 723 of
   them right after the header and one at line 14 (violin-split, Highcharts); the 893
   without one get `landscape` written out, the harness's default. The directive is then
   a protected region the adapter cannot drop or contradict, as the protected save is in
   the other languages. A directive's text that stands in a string, a template or a block
   comment, where the harness reads it all the same, is left alone with a note, which the
   readiness scan reports as `savefig-target`.
3. **Catalogue title.** Every string or template literal in the catalogue title form
   (`normalise.is_catalogue_title`, the Python profile's rule, shared for parity:
   `[<descriptive> · ]<spec-id> · javascript · <library> · anyplot.ai`) becomes `""`, and
   JSX text in that form (MUI X's `<Typography>bar-basic · javascript · muix ·
   anyplot.ai</Typography>`) becomes `{""}`, its spacing kept; the call or element that
   shows it stays. A template with a substitution is computed and stays.

The MUI X files written for MUI X 7.29 stay as they are: their imports that MUI X 9 does not
export are a readiness hint (`coupling.py`, `deprecated-api`), not a rewrite (owner decision
of 2026-10-30, question 13). The canvas needs no step of its own: the directive fixes it,
and `measure_canvas` reports 3200x1800 or 2400x2400.

Each step is checked with tree-sitter and dropped with a note when its result has a
syntax problem the input did not have; code with syntax problems is returned unchanged.
The steps read no number, so no literal can overflow them, and they never raise. The
result is idempotent: `normalise(normalise(x)) == normalise(x)` (a corpus test).
"""

import re
from collections.abc import Callable

from ...normalise import TARGETS, Canvas, Normalised, is_catalogue_title
from ...treesitter import Source, js_string, syntax_problems, walk
from .regions import DIRECTIVE, Orientation, find_directives, grammar_for


HEADER_FIRST_LINE = "// anyplot.ai"
HEADER_LINE = re.compile(r"// (?:anyplot\.ai\s*$|[a-z0-9]+(?:-[a-z0-9]+)*: |Library: |Quality: )")
CANVASES: dict[Orientation, tuple[int, int]] = {"landscape": TARGETS[0], "square": TARGETS[1]}
"""The harness's canvas per orientation (`render.mjs`, `ORIENTATIONS` at `deviceScaleFactor` 2)."""

TextEdit = tuple[int, int, str]  # replace code[start:end] with the text
StepResult = tuple[str, list[str], list[str]]  # the code, the changes made, the notes on what was left alone


def normalise(code: str, *, library: str = "chartjs") -> str:
    """The normalised code; see the module docstring."""
    return normalise_report(code, library=library).code


def normalise_report(code: str, *, library: str = "chartjs") -> Normalised:
    """`normalise` with the list of changes made and the notes on what was left alone."""
    grammar = grammar_for(library)
    problems = syntax_problems(Source(code, grammar).tree)
    if problems:
        return Normalised(code, (), (f"syntax: {problems[0].message()}; nothing was normalised",))
    changes: list[str] = []
    notes: list[str] = []
    for name, step in _STEPS:
        new_code, step_changes, step_notes = step(Source(code, grammar))
        if new_code != code and syntax_problems(Source(new_code, grammar).tree):
            notes.append(f"{name}: the rewrite would not parse; left unchanged")
            continue
        code = new_code
        changes.extend(step_changes)
        notes.extend(step_notes)
    return Normalised(code, tuple(changes), tuple(notes))


def measure_canvas(code: str, *, library: str = "chartjs") -> Canvas:
    """The canvas the harness renders: 3200x1800, or 2400x2400 for a square directive (the first one it reads)."""
    directives = find_directives(Source(code, grammar_for(library)))
    orientation: Orientation = directives[0].orientation if directives else "landscape"
    canvas = CANVASES[orientation]
    return Canvas(None, None, canvas, canvas, None)


# --- header ------------------------------------------------------------------------------


def _strip_header(source: Source) -> StepResult:
    code = source.code
    lines = code.splitlines(keepends=True)
    if not lines or lines[0].rstrip() != HEADER_FIRST_LINE:
        return code, [], []
    end = 0
    while end < len(lines) and HEADER_LINE.match(lines[end]):
        end += 1
    header_end = end
    while end < len(lines) and not lines[end].strip():
        end += 1
    span = "line 1" if header_end == 1 else f"lines 1-{header_end}"
    return "".join(lines[end:]), [f"removed the catalogue header at {span}"], []


# --- orientation -------------------------------------------------------------------------


def _one_directive(source: Source) -> StepResult:
    """One directive, in the canonical form, on the first line (module docstring, step 2)."""
    code = source.code
    directives = find_directives(source)
    if directives and not directives[0].comment:
        note = (
            f"orientation: the directive the harness reads stands at line {directives[0].line} outside a comment of "
            "its own; left alone"
        )
        return code, [], [note]
    orientation: Orientation = directives[0].orientation if directives else "landscape"
    canonical = DIRECTIVE.format(orientation=orientation)
    own = [directive for directive in directives if directive.comment]
    if len(own) == 1 and own[0].span.start == 0 and own[0].text == canonical and len(directives) == 1:
        return code, [], []
    edits: list[TextEdit] = [(directive.span.start, directive.span.end, "") for directive in own]
    body = _apply(code, edits)
    if own:
        lines = ", ".join(str(directive.line) for directive in own)
        change = f"moved the orientation directive ({orientation}) from line {lines} to line 1 as {canonical}"
    else:
        change = f"wrote the harness's default orientation out as {canonical} on line 1"
    newline = "\r\n" if "\r\n" in code[:200] else "\n"
    return canonical + newline + body, [change], []


# --- title -------------------------------------------------------------------------------


def _strip_title(source: Source) -> StepResult:
    edits: list[TextEdit] = []
    changes: list[str] = []
    for node in walk(source.root):
        if node.type in ("string", "template_string"):
            value = js_string(source, node)
            if value is None or not is_catalogue_title(value):
                continue
            span = source.node_span(node)
            edits.append((span.start, span.end, '""'))
            changes.append(f"emptied the catalogue title at {span.lines()}")
        elif node.type == "jsx_text":
            text = source.text(node)
            if not text.strip() or not is_catalogue_title(text):
                continue
            span = source.node_span(node)
            lead = len(text) - len(text.lstrip())
            trail = len(text.rstrip())
            edits.append((span.start + lead, span.start + trail, '{""}'))
            changes.append(f"emptied the catalogue title at {span.lines()}")
    return _apply(source.code, edits), changes, []


# --- helpers -----------------------------------------------------------------------------


def _apply(code: str, edits: list[TextEdit]) -> str:
    """`code` with each `(start, end, text)` applied; the edits do not overlap."""
    out: list[str] = []
    cursor = 0
    for start, end, text in sorted(edits):
        out += [code[cursor:start], text]
        cursor = end
    out.append(code[cursor:])
    return "".join(out)


_STEPS: tuple[tuple[str, Callable[[Source], StepResult]], ...] = (
    ("header", _strip_header),
    ("orientation", _one_directive),
    ("title", _strip_title),
)
