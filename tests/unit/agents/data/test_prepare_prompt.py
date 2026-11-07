"""The operation reference in root.md names every field and every fixed value of the `prepare_data` models.

The root learns the operations from its prompt, one line per operation under "Step 1: the data", and ToolSafety
validates its calls against the Pydantic models in `data/prepare.py`. The two are written by hand, so this test makes
any drift fail CI: a field or a `Literal` value added to a model and left out of its root.md line, or the reverse
case of a renamed op. A nested model is checked in the line of the first operation that holds it (a condition in
`drop_rows`, whose line the others refer to with "conditions as in drop_rows").
"""

import typing
from pathlib import Path

import pytest
from pydantic import BaseModel

from agents.anyplot.data.prepare import Operation


ROOT = Path(__file__).resolve().parents[4]
PROMPT = (ROOT / "agents" / "anyplot" / "prompts" / "root.md").read_text(encoding="utf-8")
MODELS: list[type[BaseModel]] = list(typing.get_args(typing.get_args(Operation)[0]))


def op_name(model: type[BaseModel]) -> str:
    return str(typing.get_args(model.model_fields["op"].annotation)[0])


def op_line(op: str) -> str:
    """The root.md line that documents `op`: `  - `{"op": "<op>", ...}` (...)`."""
    lines = [line for line in PROMPT.splitlines() if line.startswith(f'  - `{{"op": "{op}"')]
    assert len(lines) == 1, f"root.md has {len(lines)} lines for the operation {op}"
    return lines[0]


def parts(annotation: object) -> tuple[list[object], list[type[BaseModel]]]:
    """The `Literal` values and the nested models inside an annotation (through Optional, list, dict, Annotated)."""
    values: list[object] = []
    models: list[type[BaseModel]] = []
    if typing.get_origin(annotation) is typing.Literal:
        return list(typing.get_args(annotation)), models
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return values, [annotation]
    for argument in typing.get_args(annotation):
        found_values, found_models = parts(argument)
        values += found_values
        models += found_models
    return values, models


def missing_from(line: str, model: type[BaseModel], seen: set[type[BaseModel]]) -> list[str]:
    """What `line` leaves out of `model`: field names as `"field"`, fixed values as `"value"` or `` `value` ``."""
    seen.add(model)
    absent: list[str] = []
    for name, field in model.model_fields.items():
        if name == "op":
            continue
        if f'"{name}"' not in line:
            absent.append(f"field {name}")
        values, nested = parts(field.annotation)
        absent += [f"{name} value {value}" for value in values if f'"{value}"' not in line and f"`{value}`" not in line]
        for inner in nested:
            if inner not in seen:
                absent += missing_from(line, inner, seen)
    return absent


def test_a_line_that_leaves_something_out_is_caught() -> None:
    """The check itself: a `drop_rows` line without the "any of" list and two tests fails."""
    (drop_rows,) = [model for model in MODELS if op_name(model) == "drop_rows"]
    line = '  - `{"op": "drop_rows", "where": [{"column": ..., "test": ..., "value": ...}]}` (`eq`, `ne`, `lt`, `gt`)'

    assert set(missing_from(line, drop_rows, set())) == {"test value contains", "test value is_missing", "field values"}


def test_every_model_has_its_line() -> None:
    ops = [op_name(model) for model in MODELS]
    documented = [line.split('"op": "', 1)[1].split('"', 1)[0] for line in PROMPT.splitlines() if '- `{"op": "' in line]

    assert sorted(documented) == sorted(ops)


@pytest.mark.parametrize("model", MODELS, ids=op_name)
def test_the_line_names_every_field_and_fixed_value(model: type[BaseModel]) -> None:
    # Checked in the union's order, so a nested model is named where it first appears (`drop_rows` before `blank`).
    seen: set[type[BaseModel]] = set()
    for earlier in MODELS[: MODELS.index(model)]:
        for field in earlier.model_fields.values():
            seen.update(parts(field.annotation)[1])

    assert missing_from(op_line(op_name(model)), model, seen) == []
