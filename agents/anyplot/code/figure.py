"""The figure save of plotly and bokeh: the one statement that writes the figure as JSON, and the export's normal save.

plotly and bokeh draw in a browser, which plot code in the sandbox must not start, so their run
form ends on a statement that writes the figure as JSON to `plot-<theme>.json`, which the
renderer's figure mode draws with the package's own JavaScript (`harness.py --figure`, PB-1 of
step 4 in agentic/specs/261024-agent-all-libraries.md). The statement is pinned: the normaliser
writes it, the regions protect it as the final save, the SECURITY validator admits it in exactly
this shape and nowhere else, and nothing in it but the plot's name is free:

    fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")    # plotly
    fig.write_json(f"plot-{THEME}.json")                                         # plotly without a size

    with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:       # bokeh
        json.dump(json_item(p), figure_file)

plotly's size is the catalogue's `write_image(width=, height=)`, moved into the figure, so the
figure mode's device scale draws the catalogue's layout on the canvas (800 x 450 at scale 4,
1600 x 900 at 2, 600 x 600 at 4: `device_scale`); bokeh's is the figure's own
(`figure(width=4800, height=2700)` draws at 2/3). bokeh's statement needs the `json` module and
`open`, which no profile admits anywhere else: the validator lifts `import json` and the
statement out of the scan only when they are exactly this shape (`code/validate.py`).

The export is the one place where the downloaded `plot.py` is not the run form (owner decision of
2026-10-31, the plan's question 10): `export_form` swaps the statement back for the library's
normal save, as the catalogue writes it, which runs unchanged on the user's machine with
`data.csv`:

    fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
    fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

    export_png(p, filename=f"plot-{THEME}.png")
    output_file(f"plot-{THEME}.html")
    save(p)

and bokeh's imports with it (`import json` and `from bokeh.embed import json_item` out, `from
bokeh.io import export_png, output_file, save` in). plotly's scale is the figure mode's, so the
exported PNG has the pixels of the chat's render; a catalogue file that wrote 1600 x 900 at
scale 3 (4800 x 2700) exports at scale 2.
"""

import ast
import math
from dataclasses import dataclass
from typing import Literal


FigureKind = Literal["plotly", "bokeh"]
FIGURE_KINDS: tuple[FigureKind, ...] = ("plotly", "bokeh")
JSON_SUFFIX = ".json"
FIGURE_TARGET = 'f"plot-{THEME}.json"'
"""The figure's file in the run form; the plot step may write nothing else (`harness.FIGURE_FILE`)."""
THEME_NAME = "THEME"
FIGURE_HANDLE = "figure_file"
"""The name bokeh's statement binds the open file to."""
JSON_MODULE = "json"
JSON_ITEM = "json_item"
JSON_ITEM_MODULE = "bokeh.embed"
BOKEH_EXPORT_IMPORT = "from bokeh.io import export_png, output_file, save"
LANDSCAPE = (3200, 1800)
SQUARE = (2400, 2400)
LANDSCAPE_CSS = (1600, 900)
"""The figure mode's size for a plotly figure without one (`render.mjs`, `figureSize`)."""
MIN_SIDE = 320
MAX_SIDE = 6400
"""The sides a figure may name in CSS pixels (`render.mjs` `FIGURE_MIN_SIDE` and `FIGURE_MAX_SIDE`, pinned by a test);
the validator admits a pinned size only inside them."""


@dataclass(frozen=True, slots=True)
class FigureSave:
    """A pinned figure save: the library, the plot's name, plotly's size (None without one) and bokeh's file name."""

    kind: FigureKind
    name: str
    size: tuple[int, int] | None = None
    handle: str | None = None


def is_figure_target(node: ast.AST) -> bool:
    """Exactly `f"plot-{THEME}.json"`: no conversion, no format spec."""
    if not isinstance(node, ast.JoinedStr) or len(node.values) != 3:
        return False
    head, middle, tail = node.values
    return (
        isinstance(head, ast.Constant)
        and head.value == "plot-"
        and isinstance(middle, ast.FormattedValue)
        and isinstance(middle.value, ast.Name)
        and middle.value.id == THEME_NAME
        and middle.conversion == -1
        and middle.format_spec is None
        and isinstance(tail, ast.Constant)
        and tail.value == JSON_SUFFIX
    )


def _side(node: ast.expr) -> int | None:
    """A plain int literal inside the figure mode's range, else None (a bool, a float, a name, a sign)."""
    if isinstance(node, ast.Constant) and type(node.value) is int and MIN_SIDE <= node.value <= MAX_SIDE:
        return node.value
    return None


def _plain(node: ast.AST) -> str | None:
    """The identifier of a plain name read, else None."""
    return node.id if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) else None


def match_figure_save(stmt: ast.stmt, kind: FigureKind) -> FigureSave | None:
    """The pinned figure save of `kind` in `stmt` (module docstring), or None for any other statement."""
    if kind == "plotly":
        return _match_plotly(stmt)
    return _match_bokeh(stmt)


def _match_plotly(stmt: ast.stmt) -> FigureSave | None:
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return None
    call = stmt.value
    func = call.func
    if not (isinstance(func, ast.Attribute) and func.attr == "write_json"):
        return None
    if len(call.args) != 1 or call.keywords or not is_figure_target(call.args[0]):
        return None
    receiver = func.value
    name = _plain(receiver)
    if name is not None:
        return FigureSave("plotly", name)
    if not (isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Attribute)):
        return None
    if receiver.func.attr != "update_layout" or receiver.args or len(receiver.keywords) != 2:
        return None
    sides = {keyword.arg: _side(keyword.value) for keyword in receiver.keywords}
    name = _plain(receiver.func.value)
    width, height = sides.get("width"), sides.get("height")
    if name is None or width is None or height is None:
        return None
    return FigureSave("plotly", name, (width, height))


def _match_bokeh(stmt: ast.stmt) -> FigureSave | None:
    if not isinstance(stmt, ast.With) or len(stmt.items) != 1 or len(stmt.body) != 1:
        return None
    item = stmt.items[0]
    opened, handle_node = item.context_expr, item.optional_vars
    if not (isinstance(handle_node, ast.Name) and isinstance(opened, ast.Call) and _plain(opened.func) == "open"):
        return None
    if len(opened.args) != 2:
        return None
    mode = opened.args[1]
    encoding = opened.keywords[0] if len(opened.keywords) == 1 else None
    if not (
        is_figure_target(opened.args[0])
        and isinstance(mode, ast.Constant)
        and mode.value == "w"
        and encoding is not None
        and encoding.arg == "encoding"
        and isinstance(encoding.value, ast.Constant)
        and encoding.value.value == "utf-8"
    ):
        return None
    inner = stmt.body[0]
    if not (isinstance(inner, ast.Expr) and isinstance(inner.value, ast.Call)):
        return None
    dump = inner.value
    if not (
        isinstance(dump.func, ast.Attribute)
        and dump.func.attr == "dump"
        and _plain(dump.func.value) == JSON_MODULE
        and len(dump.args) == 2
        and not dump.keywords
    ):
        return None
    item_call, target = dump.args
    if not (
        isinstance(item_call, ast.Call)
        and _plain(item_call.func) == JSON_ITEM
        and len(item_call.args) == 1
        and not item_call.keywords
    ):
        return None
    name, handle = _plain(item_call.args[0]), handle_node.id
    reserved = {THEME_NAME, JSON_MODULE, JSON_ITEM, "open"}
    if name is None or _plain(target) != handle or handle == name or {name, handle} & reserved:
        return None
    return FigureSave("bokeh", name, handle=handle)


def figure_saves(tree: ast.Module, kind: FigureKind) -> list[tuple[ast.stmt, FigureSave]]:
    """Every module-level pinned figure save of `kind`, in order."""
    return [(stmt, found) for stmt in tree.body if (found := match_figure_save(stmt, kind)) is not None]


def json_save(kind: FigureKind, name: str, size: tuple[int, int] | None = None) -> str:
    """The pinned statement's text (module docstring), without a trailing newline."""
    if kind == "plotly":
        if size is None:
            return f"{name}.write_json({FIGURE_TARGET})"
        return f"{name}.update_layout(width={size[0]}, height={size[1]}).write_json({FIGURE_TARGET})"
    return (
        f'with open({FIGURE_TARGET}, "w", encoding="utf-8") as {FIGURE_HANDLE}:\n'
        f"    {JSON_MODULE}.dump({JSON_ITEM}({name}), {FIGURE_HANDLE})"
    )


def device_scale(width: float, height: float) -> float:
    """The figure mode's device scale for a figure of `width` x `height` CSS pixels (`render.mjs`, `figureCanvas`):
    a figure at 4:3 or wider goes into the landscape canvas, whose CSS width is the figure's, at least 16:9 of its
    height, rounded up to a multiple of 16; a narrower one into the square canvas of its larger side."""
    if 3 * width < 4 * height:
        return SQUARE[0] / math.ceil(max(width, height))
    css_width = 16 * math.ceil(max(width, height * 16 / 9) / 16)
    return LANDSCAPE[0] / css_width


def _scale_text(scale: float) -> str:
    """A scale as the shortest literal that writes it to four decimals: `4`, `2`, `1.5`, `0.6667`."""
    rounded = round(scale, 4)
    return str(int(rounded)) if rounded == int(rounded) else repr(rounded)


def normal_save(found: FigureSave) -> str:
    """The library's normal save the export carries in place of the pinned statement (module docstring), without a
    trailing newline."""
    png, html = 'f"plot-{THEME}.png"', 'f"plot-{THEME}.html"'
    if found.kind == "plotly":
        width, height = found.size or LANDSCAPE_CSS
        scale = _scale_text(device_scale(width, height))
        size = f", width={width}, height={height}" if found.size is not None else ""
        return (
            f"{found.name}.write_image({png}{size}, scale={scale})\n"
            f'{found.name}.write_html({html}, include_plotlyjs="cdn")'
        )
    return f"export_png({found.name}, filename={png})\noutput_file({html})\nsave({found.name})"


def _loads(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def _ending(line: str) -> str:
    """The line break `line` ends with (`\\n` when it has none, the file's last line)."""
    return line[len(line.rstrip("\r\n")) :] or "\n"


def export_form(run_form: str, kind: FigureKind) -> str:
    """`run_form` with its last pinned figure save swapped for the library's normal save, bokeh's imports with it
    (module docstring); unchanged when it holds no pinned save or does not parse, so an export of an export is the
    export. bokeh's `import json` and `json_item` import go only when nothing else reads the name; the `bokeh.io`
    import takes the `json_item` import's line, or follows the last module-level import without one."""
    try:
        tree = ast.parse(run_form)
    except SyntaxError:
        return run_form
    saves = figure_saves(tree, kind)
    if not saves:
        return run_form
    stmt, found = saves[-1]
    lines = run_form.splitlines(keepends=True)
    first, last = stmt.lineno, stmt.end_lineno or stmt.lineno
    indent, ending = lines[first - 1][: stmt.col_offset], _ending(lines[last - 1])
    edits = {first: (last, "".join(f"{indent}{line}{ending}" for line in normal_save(found).split("\n")))}
    if kind == "bokeh":
        used = set().union(*(_loads(node) for node in tree.body if node is not stmt))
        imports = [node for node in tree.body if isinstance(node, ast.Import | ast.ImportFrom)]
        placed = False
        for node in imports:
            end = node.end_lineno or node.lineno
            if is_json_import(node) and JSON_MODULE not in used:
                edits[node.lineno] = (end, "")
            elif is_json_item_import(node) and JSON_ITEM not in used:
                edits[node.lineno] = (end, BOKEH_EXPORT_IMPORT + _ending(lines[end - 1]))
                placed = True
        if not placed:
            after = (imports[-1].end_lineno or imports[-1].lineno) if imports else 0
            if after:
                end, text = edits.get(after, (after, lines[after - 1]))
                edits[after] = (end, text + BOKEH_EXPORT_IMPORT + "\n")
            else:
                edits[1] = (1, BOKEH_EXPORT_IMPORT + "\n" + edits.get(1, (1, lines[0]))[1])
    out: list[str] = []
    line = 1
    while line <= len(lines):
        if line in edits:
            end, text = edits[line]
            out.append(text)
            line = end + 1
            continue
        out.append(lines[line - 1])
        line += 1
    return "".join(out)


def _is_import(node: ast.stmt, module: str) -> bool:
    """`import <module>` alone, without an alias."""
    return (
        isinstance(node, ast.Import)
        and len(node.names) == 1
        and node.names[0].name == module
        and node.names[0].asname is None
    )


def _is_from_import(node: ast.stmt, module: str, name: str) -> bool:
    """`from <module> import <name>` alone, without an alias."""
    return (
        isinstance(node, ast.ImportFrom)
        and node.level == 0
        and node.module == module
        and len(node.names) == 1
        and node.names[0].name == name
        and node.names[0].asname is None
    )


def is_json_import(node: ast.stmt) -> bool:
    """`import json` alone (bokeh's figure save reads the module)."""
    return _is_import(node, JSON_MODULE)


def is_json_item_import(node: ast.stmt) -> bool:
    """`from bokeh.embed import json_item` alone."""
    return _is_from_import(node, JSON_ITEM_MODULE, JSON_ITEM)
