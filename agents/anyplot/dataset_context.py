"""What the adapter and the reviewer learn about where the user's data comes from.

The live test of 2026-10-14 drew the Lorenz attractor from a `run_data_code` table and
titled it "Trajektorie im Raum": the adapter saw the columns `t, x, y, z` and nothing
else. The dataset context block gives it what the session knows about the data, all of
it screened or written by the server:

* the notes the user pasted with the table (`StoredDataset.context_lines`), which the
  dataset route kept only after the pre-filter and the scope judge passed them; a
  JSON-stat title, source and one-category dimensions are among them (`data/parse.py`);
* the source of a computed table (`StoredDataset.source`): for `generate_data` the
  ranges and expressions the server validated (`generated_source`), for `run_data_code`
  the names the validated snippet defines and calls (`code_source`), never its comments
  or string literals.

`dataset_context` joins them within `MAX_CONTEXT_CHARS`; the pipeline fences the result as
`<user_notes>` under a fixed heading, so it reaches both models as data.
"""

import ast
from collections.abc import Sequence

from .data.generate import Generate


MAX_CONTEXT_CHARS = 1_500
"""The dataset context block at most: the pasted notes take up to 2,000 characters, and a title needs few of them."""
MAX_SOURCE_CHARS = 400
"""A computed table's source line: the names of a snippet, or the expressions of up to ten series."""
MAX_SOURCE_NAMES = 12
"""Names a snippet's source line lists per kind (defined functions, calls, assigned names)."""
NOTES_HEADING = "Notes the user pasted with the data:"
SOURCE_HEADING = "Where the data comes from:"


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def generated_source(spec: Generate) -> str:
    """The source line of a `generate_data` table: its ranges and expressions, as the server validated them."""
    ranges = "; ".join(
        f"{item.name} from {item.start} to {item.stop} ({item.points} points)" for item in spec.variables
    )
    series = "; ".join(f"{item.name} = {item.expression}" for item in spec.series)
    return _clip(f"computed by the server from formulas: {ranges}; {series}", MAX_SOURCE_CHARS)


def code_source(code: str, language: str) -> str:
    """The source line of a `run_data_code` table: the names its validated snippet defines, calls and assigns.

    Only identifiers, never comments or string literals. The identifiers are not screened
    (the root wrote the code, possibly from the user's snippet, and the validator checks
    what it does, not its names), so they reach the adapter and the reviewer only fenced as
    `<user_notes>` data, at most `MAX_SOURCE_NAMES` per kind and `MAX_SOURCE_CHARS` in all.
    A function the root named after the system (`def lorenz(...)`) carries the subject
    into the title.
    """
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return f"computed by Python code (translated from {language})"
    defined: list[str] = []
    calls: list[str] = []
    assigned: list[str] = []
    for item in ast.walk(tree):
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
            defined.append(item.name)
        elif isinstance(item, ast.Call):
            name = _dotted(item.func)
            if name:
                calls.append(name)
        elif isinstance(item, ast.Assign):
            assigned += [target.id for target in item.targets if isinstance(target, ast.Name)]
    parts = [f"computed by Python code (translated from {language})"]
    for label, names in (("functions defined", defined), ("calls", calls), ("names", assigned)):
        unique = list(dict.fromkeys(names))[:MAX_SOURCE_NAMES]
        if unique:
            parts.append(f"{label}: {', '.join(unique)}")
    return _clip("; ".join(parts), MAX_SOURCE_CHARS)


def _dotted(node: ast.expr) -> str | None:
    """`np.linspace` for a call of an attribute chain on a name; None for anything else."""
    names: list[str] = []
    while isinstance(node, ast.Attribute):
        names.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return ".".join([node.id, *reversed(names)])


def dataset_context(context_lines: Sequence[str], source: str | None) -> str:
    """The dataset context block's text (empty when there is none): the source line first, then the notes."""
    parts: list[str] = []
    if source:
        parts.append(f"{SOURCE_HEADING} {source}")
    notes = [" ".join(line.split()) for line in context_lines if line.strip()]
    if notes:
        parts.append(NOTES_HEADING + "\n" + "\n".join(notes))
    return _clip("\n".join(parts), MAX_CONTEXT_CHARS)
