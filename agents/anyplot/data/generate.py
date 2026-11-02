"""The `generate_data` source: a table the server computes from formulas the model chose.

Owner decision of 2026-10-11: a function such as "sin x von -pi bis pi" is a
deterministic data source in step 1, not a path around the data layer. The design is
docs/concepts/agent-network.md, "Two steps: data first, then the plot". The model never
writes rows: it chooses a `Generate` spec (one or two variables, each a range of evenly
spaced points, and one to ten series, each an expression over the variables), and
`generate` computes the table with NumPy. The result is canonical CSV text that
`parse_dataset` reads back as number columns, plus a change line, so the caller stores it
as an ordinary dataset version (preview, profile, bindings, confirmation, undo), and the
plot and its export (`plot.py` with `data.csv`) work unchanged. No ADK import.

The expressions are a whitelist over Python's `ast`, evaluated by walking the checked
tree; no text ever reaches `eval`, `exec` or `compile`:

* numbers (int or float literals), the spec's variables, the constants `pi`, `e`, `tau`;
* unary `+` and `-`; binary `+ - * / ** % //`; parentheses;
* calls of `FUNCTIONS` with positional arguments: one for `sin` to `sign`, two for
  `atan2`, `min` and `max` (elementwise).

Anything else (attributes, indexing, strings, comparisons, `and` and `or`, conditionals,
lambdas, comprehensions, keyword or starred arguments, `:=`, the bitwise operators,
`^` among them, a number glued to a name such as `2x`, a `#` comment) is
`invalid_expression` with a message that names the construct, and so is an expression
of more than `MAX_EXPRESSION_NODES` nodes. The typographic operators `−`, `×`, `·` and
`⋅` read as `-` and `*`. A range's `start` and `stop` are expressions over the
constants only. Every value is a float64 array evaluated under `np.errstate(all="ignore")`,
never a Python int or float, so an overflow (`10**400`), a division by zero or a function
outside its domain (`log(-1)`) gives inf or NaN, which become missing cells, never an
exception.

The table: the variable columns first (two variables make a grid, the cartesian
product with the first variable slowest), then the series columns; every value
rounded to `SIGNIFICANT_DIGITS` significant digits and written as the parser writes a
number (`repr` of the float, so every column re-parses as `number`), a missing cell
empty. The variables are rounded before the series are computed, so every row holds
`y = f(x)` for the `x` it shows. Errors raise `GenerateError(code, message)`:
`invalid_expression`, `invalid_range` (an endpoint that is not finite, equal endpoints,
a range wider than a float holds, points that round to the same value),
`too_many_points` (a grid over `MAX_GRID_ROWS`), `undefined` (a series without one
defined value) and `too_large` (a CSV over the computed-data cap `MAX_COMPUTED_BYTES`; the message names
about how many rows fit). A message names the variable or series and at most quotes
the expression's own text, and the change line quotes only the checked expression.

`looks_like_formula` is the dataset route's guard: text pasted into the data field that
asks for a formula is refused (`422 formula`) instead of reaching the transcriber, which
would let a model write the rows. Text that holds its own values is data, never a
formula, so the guard never keeps a table in words from the transcriber.
"""

import ast
import csv
import io
import keyword
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Literal, Self

import numpy as np
import numpy.typing as npt
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from ..schemas import MAX_NOTE_CHARS
from .parse import MAX_COMPUTED_BYTES, SNIFF_LINES, sniff_delimiter
from .prepare import NewName
from .transcribe import MAX_TRANSCRIBE_CHARS


MAX_EXPRESSION_CHARS = 200
MAX_EXPRESSION_NODES = 100
"""Expression nodes (names, numbers, operations, calls) of one expression."""
MAX_POINTS = 5_000
"""Points of one variable."""
MAX_GRID_ROWS = 10_000
"""Rows of a two-variable grid, the product of both variables' points."""
MAX_SERIES = 10
MAX_VARIABLES = 2
DEFAULT_POINTS = 200
SIGNIFICANT_DIGITS = 8
CHANGE_DIGITS = 5
"""Significant digits of a range's endpoints in the change line."""
MAX_FORMULA_CHARS = 300
"""The longest line or sentence the guard reads for a formula; a longer one is prose or a table row."""
MIN_DATA_VALUES = 3
"""Numbers besides a formula's own (its ranges, its expressions, a point count) that make pasted text data."""

GenerateErrorCode = Literal["invalid_expression", "invalid_range", "too_many_points", "undefined", "too_large"]
Array = npt.NDArray[np.float64]

CONSTANTS: dict[str, float] = {"pi": math.pi, "e": math.e, "tau": math.tau}
UNARY_FUNCTIONS: dict[str, np.ufunc] = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "asin": np.arcsin,
    "acos": np.arccos,
    "atan": np.arctan,
    "sinh": np.sinh,
    "cosh": np.cosh,
    "tanh": np.tanh,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
    "log2": np.log2,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "floor": np.floor,
    "ceil": np.ceil,
    "round": np.rint,  # half to even, as Python's round
    "sign": np.sign,
}
BINARY_FUNCTIONS: dict[str, np.ufunc] = {"atan2": np.arctan2, "min": np.minimum, "max": np.maximum}
FUNCTIONS: frozenset[str] = frozenset(UNARY_FUNCTIONS) | frozenset(BINARY_FUNCTIONS)
_FUNCTION_LIST = ", ".join([*UNARY_FUNCTIONS, *BINARY_FUNCTIONS])
ONLY = f"names, numbers, + - * / ** % //, parentheses and the functions {_FUNCTION_LIST} only"
_OPERATORS: dict[type[ast.operator], np.ufunc] = {
    ast.Add: np.add,
    ast.Sub: np.subtract,
    ast.Mult: np.multiply,
    ast.Div: np.divide,
    ast.Pow: np.power,
    ast.Mod: np.mod,
    ast.FloorDiv: np.floor_divide,
}
_SYMBOLS: dict[type[ast.operator], str] = {
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.LShift: "<<",
    ast.RShift: ">>",
    ast.MatMult: "@",
}
_FORBIDDEN: tuple[tuple[type[ast.AST] | tuple[type[ast.AST], ...], str], ...] = (
    (ast.Attribute, "attributes such as x.real are not allowed"),
    (ast.Subscript, "indexing such as x[0] is not allowed"),
    (ast.Compare, "comparisons such as x > 0 are not allowed"),
    (ast.BoolOp, "'and' and 'or' are not allowed"),
    (ast.IfExp, "conditional expressions (a if b else c) are not allowed"),
    (ast.Lambda, "lambda is not allowed"),
    ((ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp), "comprehensions are not allowed"),
    (ast.NamedExpr, "':=' is not allowed"),
    (ast.Starred, "starred arguments are not allowed"),
    ((ast.List, ast.Tuple, ast.Set, ast.Dict), "lists, tuples, sets and dicts are not allowed; write one value"),
    ((ast.JoinedStr, ast.FormattedValue), "strings are not allowed"),
)
_GLUED = re.compile(r"(?<![\w.])(?P<number>[0-9]+(?:\.[0-9]*)?)(?![eE][+-]?[0-9])(?P<name>[A-Za-z_]\w*)")
_WHITESPACE = re.compile(r"\s+")
_TYPOGRAPHIC = str.maketrans({"−": "-", "×": "*", "·": "*", "⋅": "*"})
"""Operators a model or a user types as typography; each reads as its ASCII form."""
_IDENTIFIER = r"^[A-Za-z_][A-Za-z0-9_]{0,63}$"


class GenerateError(Exception):
    """A spec that cannot be computed; `code` is fixed, `message` names variables and series at most."""

    def __init__(self, code: GenerateErrorCode, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code: GenerateErrorCode = code
        self.message = message


@dataclass(frozen=True)
class Generated:
    """The result of `generate`: canonical CSV text, the change line, and one warning per series with gaps."""

    csv: str
    changes: list[str]
    warnings: list[str]


# --- Spec models ------------------------------------------------------------------------------


def _variable_name(name: str) -> str:
    """A variable is referenced by its name in the expressions, so it is no function, constant or keyword."""
    if name in FUNCTIONS or name in CONSTANTS or keyword.iskeyword(name):
        raise ValueError("a variable is named like a function, a constant or a keyword; choose another name")
    return name


Expr = Annotated[str, Field(min_length=1, max_length=MAX_EXPRESSION_CHARS)]
VariableName = Annotated[str, Field(min_length=1, max_length=64, pattern=_IDENTIFIER), AfterValidator(_variable_name)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Range(_Strict):
    """One variable: `points` evenly spaced values from `start` to `stop`, both included.

    `start` and `stop` are expressions over numbers and the constants (`-pi`, `2*pi`);
    a JSON number is read as its text, so `"start": -3` needs no quoting.
    """

    model_config = ConfigDict(extra="forbid", coerce_numbers_to_str=True)

    name: VariableName = "x"
    start: Expr
    stop: Expr
    points: int = Field(default=DEFAULT_POINTS, ge=2, le=MAX_POINTS)


class Series(_Strict):
    """One computed column: `expression` over the variables, named `name`."""

    name: NewName
    expression: Expr


class Generate(_Strict):
    """The arguments of `generate_data`: one or two variables and one to ten series, all names distinct."""

    variables: list[Range] = Field(min_length=1, max_length=MAX_VARIABLES)
    series: list[Series] = Field(min_length=1, max_length=MAX_SERIES)

    @model_validator(mode="after")
    def _distinct_names(self) -> Self:
        names = [item.name for item in self.variables] + [item.name for item in self.series]
        if len(set(names)) != len(names):
            raise ValueError("variable and series names must be distinct")
        return self


# --- Generating -------------------------------------------------------------------------------


def generate(spec: Generate) -> Generated:
    """Compute the table of `spec`; raises `GenerateError`."""
    names = [variable.name for variable in spec.variables]
    allowed = frozenset(names)
    ranges = [_range(variable) for variable in spec.variables]
    rows = math.prod(variable.points for variable in spec.variables)
    if rows > MAX_GRID_ROWS:
        sizes = " x ".join(str(variable.points) for variable in spec.variables)
        raise GenerateError(
            "too_many_points",
            f"a grid of {sizes} points has {rows:,} rows; at most {MAX_GRID_ROWS:,} fit, use fewer points",
        )
    # Every expression is checked before any is computed, so one bad series fails the call as a whole.
    trees = [(series, parse_expression(series.expression, allowed, series.name)) for series in spec.series]

    axes = [_axis(variable, start, stop) for variable, (start, stop) in zip(spec.variables, ranges, strict=True)]
    if len(axes) == 2:
        values = {names[0]: np.repeat(axes[0], axes[1].size), names[1]: np.tile(axes[1], axes[0].size)}
    else:
        values = {names[0]: axes[0]}

    columns = [_texts(values[name]) for name in names]
    warnings: list[str] = []
    for series, tree in trees:
        with np.errstate(all="ignore"):
            result = np.broadcast_to(_evaluate(tree, values), (rows,))
        defined = np.isfinite(result)
        undefined = rows - int(defined.sum())
        if undefined == rows:
            raise GenerateError(
                "undefined",
                f"{series.name}: no value is defined over the range (a value beyond the number range, or log or sqrt "
                "of negative numbers, for example)",
            )
        if undefined:
            verb = "is" if undefined == 1 else "are"
            warnings.append(f"{series.name}: {undefined} of {rows} values {verb} undefined and left empty")
        columns.append(_texts(result))

    csv_text = _write([*names, *(series.name for series in spec.series)], columns)
    size = len(csv_text.encode("utf-8"))
    if size > MAX_COMPUTED_BYTES:
        # The row count that fits at this table's width, so the model's one retry aims at a size that fits.
        fit = rows * MAX_COMPUTED_BYTES // size
        hint = f"about {fit:,} rows of {len(columns)} columns fit"
        if len(spec.variables) > 1:
            side = math.isqrt(fit)
            hint += f", such as {side} x {side} points"
        raise GenerateError(
            "too_large",
            f"the table would be larger than {MAX_COMPUTED_BYTES // 1024:,} KB; {hint}; use fewer points or fewer series",
        )
    return Generated(csv=csv_text, changes=[_change(spec, ranges, rows)], warnings=warnings)


def _range(variable: Range) -> tuple[float, float]:
    """The endpoints of one variable as floats; raises for one that is not finite, equal ones or a too-wide range."""
    start = _endpoint(variable.start, f"{variable.name}.start")
    stop = _endpoint(variable.stop, f"{variable.name}.stop")
    if start == stop:
        raise GenerateError("invalid_range", f"{variable.name}: start and stop are the same value")
    if not math.isfinite(stop - start):
        raise GenerateError("invalid_range", f"{variable.name}: the range is wider than a number can hold")
    return start, stop


def _endpoint(text: str, where: str) -> float:
    tree = parse_expression(text, frozenset(), where, endpoint=True)
    with np.errstate(all="ignore"):
        value = float(_evaluate(tree, {}))
    if not math.isfinite(value):
        raise GenerateError("invalid_range", f"{where}: the value is not a finite number")
    return value


def _axis(variable: Range, start: float, stop: float) -> Array:
    """The variable's points at `SIGNIFICANT_DIGITS` significant digits: the values the table shows and the series use.

    Rounding before the series are computed keeps every row true to what it shows
    (`y = f(x)` for the written `x`). A range so narrow for its points that two
    neighbours round to the same value is refused: the column would repeat an `x`
    with different `y` values.
    """
    points = np.array([_round(value) for value in np.linspace(start, stop, variable.points).tolist()], dtype=np.float64)
    if np.any(np.diff(points) == 0):
        raise GenerateError(
            "invalid_range",
            f"{variable.name}: {variable.points} points from {_number_text(start)} to {_number_text(stop)} do not "
            f"stay distinct at {SIGNIFICANT_DIGITS} significant digits; use fewer points or a wider range",
        )
    return points


def _round(value: float) -> float:
    """`value` at `SIGNIFICANT_DIGITS` significant digits, `0.0` for a negative zero."""
    rounded = float(f"{value:.{SIGNIFICANT_DIGITS}g}")
    return rounded if rounded else 0.0


def _texts(values: Array) -> list[str]:
    """Every value at `SIGNIFICANT_DIGITS` significant digits, written as the parser writes a number; NaN and inf empty."""
    return [repr(_round(value)) if math.isfinite(value) else "" for value in values.tolist()]


def _write(names: list[str], columns: list[list[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(names)
    writer.writerows(zip(*columns, strict=True))
    return buffer.getvalue()


def _change(spec: Generate, ranges: list[tuple[float, float]], rows: int) -> str:
    """`generated 200 rows: x from -3.1416 to 3.1416, y = sin(x)`; a grid names each variable's points."""
    grid = len(spec.variables) > 1
    spans = []
    for variable, (start, stop) in zip(spec.variables, ranges, strict=True):
        span = f"{variable.name} from {_number_text(start)} to {_number_text(stop)}"
        spans.append(f"{span} ({variable.points} points)" if grid else span)
    # The source parse_expression read: whitespace collapsed, typographic operators in ASCII, no comment.
    formulas = ", ".join(f"{series.name} = {_source(series.expression)}" for series in spec.series)
    line = f"generated {rows} {'row' if rows == 1 else 'rows'}: {' and '.join(spans)}, {formulas}"
    return line if len(line) <= MAX_NOTE_CHARS else line[: MAX_NOTE_CHARS - 1] + "…"


def _number_text(value: float) -> str:
    """An endpoint for the change line: a whole number in full, else `CHANGE_DIGITS` significant digits.

    Ordinary magnitudes are written without an exponent (`123456`, `-3.1416`, `0.00012346`);
    only a very large or very small value keeps one (`1.2346e+20`).
    """
    if value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    if 1e-4 <= abs(value) < 1e15:
        return np.format_float_positional(value, precision=CHANGE_DIGITS, unique=False, fractional=False, trim="-")
    return f"{value:.{CHANGE_DIGITS}g}"


def _one_line(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def _source(text: str) -> str:
    """The text `parse_expression` reads: one line, the typographic operators in ASCII."""
    return _one_line(text).translate(_TYPOGRAPHIC)


# --- Expressions ------------------------------------------------------------------------------


def parse_expression(text: str, variables: frozenset[str] | None, where: str, *, endpoint: bool = False) -> ast.expr:
    """The checked tree of one expression; raises `GenerateError("invalid_expression", ...)`.

    `variables` are the names an expression may use besides the constants; None accepts
    any name that is no function (`looks_like_formula` reads a pasted formula whose
    variables it cannot know). `where` names the series or endpoint in the message.
    """
    source = _source(text)
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise GenerateError("invalid_expression", f"{where}: {_syntax_hint(source, exc)}") from None
    except ValueError, RecursionError, MemoryError:
        raise GenerateError("invalid_expression", f"{where}: the expression cannot be read") from None
    _check(tree.body, variables, where, endpoint)
    if "#" in source:
        # No string passed the check, so a '#' starts a comment: free text the change line would quote.
        raise GenerateError("invalid_expression", f"{where}: comments (#) are not allowed; write the expression only")
    nodes = sum(1 for node in ast.walk(tree.body) if isinstance(node, ast.expr))
    if nodes > MAX_EXPRESSION_NODES:
        raise GenerateError(
            "invalid_expression", f"{where}: the expression has more than {MAX_EXPRESSION_NODES} parts; simplify it"
        )
    return tree.body


def _syntax_hint(source: str, exc: SyntaxError) -> str:
    glued = _GLUED.search(source)
    if glued:
        number, name = glued.group("number"), glued.group("name")
        return f"'{number}{name}' needs an operator: write {number}*{name}"
    if "²" in source or "³" in source:
        return "'²' and '³' are not operators; write x**2 or x**3"
    if "√" in source:
        return "'√' is not an operator; write sqrt(x)"
    return f"the expression cannot be read ({exc.msg}); use {ONLY}"


def _check(node: ast.expr, variables: frozenset[str] | None, where: str, endpoint: bool) -> None:
    """Raise for every node outside the whitelist, naming the construct; returns for an expression that may be evaluated."""

    def fail(message: str) -> GenerateError:
        return GenerateError("invalid_expression", f"{where}: {message}")

    match node:
        case ast.Constant(value=value):
            if isinstance(value, bool) or value is None or value is Ellipsis:
                raise fail("True, False, None and ... are not allowed; " + ONLY)
            if isinstance(value, str | bytes):
                raise fail("strings are not allowed; " + ONLY)
            if not isinstance(value, int | float):
                raise fail("complex numbers are not allowed")
        case ast.Name(id=name):
            if name in CONSTANTS:
                return
            if name in FUNCTIONS:
                raise fail(f"'{name}' is a function; write {name}(x)")
            if name == "π":
                raise fail("write pi for π")
            if endpoint:
                raise fail("start and stop take numbers and the constants pi, e, tau only, no variable")
            if variables is not None and name not in variables:
                known = ", ".join(sorted(variables))
                raise fail(f"unknown name '{_clip(name)}'; use the variables {known} and the constants pi, e, tau")
        case ast.UnaryOp(op=op, operand=operand):
            if isinstance(op, ast.Not):
                raise fail("'not' is not allowed; " + ONLY)
            if isinstance(op, ast.Invert):
                raise fail("'~' is not allowed; " + ONLY)
            _check(operand, variables, where, endpoint)
        case ast.BinOp(left=left, op=op, right=right):
            if isinstance(op, ast.BitXor):
                raise fail("'^' is not a power; write x**2")
            if type(op) not in _OPERATORS:
                symbol = _SYMBOLS.get(type(op), type(op).__name__)
                raise fail(f"'{symbol}' is not allowed; " + ONLY)
            _check(left, variables, where, endpoint)
            _check(right, variables, where, endpoint)
        case ast.Call(func=func, args=args, keywords=keywords):
            if keywords:
                raise fail("keyword arguments such as f(x=1) are not allowed; pass the arguments in order")
            if isinstance(func, ast.Constant) and isinstance(func.value, int | float):
                raise fail("a number before '(' needs an operator: write 2*(x + 1)")
            if not isinstance(func, ast.Name):
                _check(func, variables, where, endpoint)
                raise fail("only a function name can be called, as in sin(x); write a*(b) for a product")
            name = func.id
            if name not in FUNCTIONS:
                if name in CONSTANTS or variables is None or name in variables:
                    raise fail(f"'{_clip(name)}(' needs an operator: write {_clip(name)}*(...)")
                raise fail(f"unknown function '{_clip(name)}'; the functions are {_FUNCTION_LIST}")
            arity = 1 if name in UNARY_FUNCTIONS else 2
            if any(isinstance(arg, ast.Starred) for arg in args):
                raise fail("starred arguments are not allowed")
            if len(args) != arity:
                raise fail(f"{name} takes {arity} {'argument' if arity == 1 else 'arguments'}")
            for arg in args:
                _check(arg, variables, where, endpoint)
        case _:
            for kind, message in _FORBIDDEN:
                if isinstance(node, kind):
                    raise fail(message)
            raise fail(ONLY)


def _evaluate(node: ast.expr, values: Mapping[str, Array]) -> Array:
    """The value of a checked tree as a float64 array (0-d for a constant part), never a Python number.

    Python floats raise on an overflow (`10.0**400`) and on a division by zero; NumPy's
    float64 under the caller's `np.errstate(all="ignore")` gives inf or NaN instead.
    """
    match node:
        case ast.Constant(value=int() | float() as value):
            try:
                number = float(value)
            except OverflowError:  # an integer literal beyond the float range
                number = math.inf
            return np.asarray(number, dtype=np.float64)
        case ast.Name(id=name):
            return values[name] if name in values else np.asarray(CONSTANTS[name], dtype=np.float64)
        case ast.UnaryOp(op=op, operand=operand):
            inner = _evaluate(operand, values)
            return np.asarray(np.negative(inner), dtype=np.float64) if isinstance(op, ast.USub) else inner
        case ast.BinOp(left=left, op=op, right=right):
            result = _OPERATORS[type(op)](_evaluate(left, values), _evaluate(right, values))
            return np.asarray(result, dtype=np.float64)
        case ast.Call(func=ast.Name(id=name), args=args):
            arguments = [_evaluate(arg, values) for arg in args]
            function = UNARY_FUNCTIONS.get(name) or BINARY_FUNCTIONS[name]
            return np.asarray(function(*arguments), dtype=np.float64)
    raise GenerateError("invalid_expression", ONLY)  # unreachable for a checked tree


def _clip(text: str, limit: int = 40) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


# --- The dataset route's guard ------------------------------------------------------------------

_SEGMENT = re.compile(r"\n|(?<=[.!?;])\s+")
"""Where pasted text splits into the lines and sentences the guard reads one by one."""
_CALL = re.compile(r"(?i)(?<![\w.])(?P<name>" + "|".join(sorted(FUNCTIONS, key=len, reverse=True)) + r")\s*\(")
_BARE_FUNCTIONS = "asin|acos|atan|sinh|cosh|tanh|sin|cos|tan|exp|log10|log2|log|ln|sqrt"
_BARE_CALL = re.compile(rf"(?i)(?<![\w.])(?P<name>{_BARE_FUNCTIONS})\s+(?P<arg>[A-Za-z])(?![\w(])")
"""A call written without parentheses, of one one-letter variable: `sin x`, `log x`, `ln t`."""
_ROOT_SIGN = re.compile(r"√\s*(?:(?P<paren>\()|(?P<arg>[A-Za-z_]\w*|[0-9]+(?:\.[0-9]+)?))")
_LN = re.compile(r"(?i)(?<![\w.])ln\s*\(")
_IMPLICIT_PRODUCT = re.compile(
    # The boundary before the number is consumed (and written back), not a lookbehind, so the digit
    # loop can start only after it: linear on any input, which a lookbehind does not make evident.
    r"(?P<before>^|[^\w.])(?P<number>[0-9]+(?:\.[0-9]+)?)(?![eE][+-]?[0-9])(?=[A-Za-z_(])"
)
_ASSIGNMENT = re.compile(
    # A lookahead, so that assignments in a row ("a = 2, y = x**2") are each found.
    r"(?<![\w.=<>!])(?=(?P<lhs>[^\W\d]\w{0,30}(?:\s*\(\s*[^\W\d]\w{0,10}(?:\s*,\s*[^\W\d]\w{0,10})?\s*\))?)"
    r"\s*=(?!=)\s*(?P<rhs>[^\n=;]{1,200}))"
)
_MATH_NAME = re.compile(r"[^\W\d]\w?|[^\W\d]\w{0,10}\s*\(.*\)")
"""The left side of a formula: a name of one or two characters (`y`, `y1`) or a function's head (`f(x)`)."""
_PARAMETER = re.compile(r"[^\W\d_]")
"""The left side of a parameter (`a = 2`) or of a variable's values (`x = 1, 2, 3`): one letter."""
_RHS_STOP = re.compile(
    r"(?i)\s(?:from|von|for|für|fuer|with|mit|between|zwischen|in|over|über|ueber|on|auf|where|wobei|bis|to|and|und)\b"
)
_ENDPOINT = r"[-+−]?\s?(?:[0-9]+(?:[.,][0-9]+)?\s?\*?\s?(?:pi|π|tau|e)?|pi|π|tau|e)(?:\s?/\s?[0-9]+)?"
_RANGE = re.compile(
    rf"(?i)\b(?:from|von|between|zwischen)\s+(?P<start>{_ENDPOINT})\s+(?:to|bis|and|und)\s+(?P<stop>{_ENDPOINT})(?!\w)"
)
_CONSTANT_ENDPOINT = re.compile(r"(?i)pi|π|tau|^[-+−]?\s?e$")
_SUBJECT = re.compile(
    r"(?<![\w'’.,-])(?<!\bin )(?<!\bpro )(?<!\bper )(?<!\bje )(?<![0-9] )"
    r"[b-df-zθφ](?:\s*(?:,|\band\b|\bund\b)\s*[b-df-zθφ])?\s+$"
)
"""A one-letter variable right before a range phrase (`x von`, `für n von`, `x and y from`): never `a` or `e`,
and never a unit (`CO2 in t von`, `12 t von`)."""
_POWER = re.compile(
    r"\*\*|(?<=[\w)])\s?\^\s?(?=[\w(+-])|(?:(?<!\w)[a-ln-zA-LN-Z]|\))\s?[²³]|(?i:\bhoch\s+(?:[0-9]+|[a-z])\b)"
)
"""A power: `**`, `^` between operands, `²` or `³` after a one-letter variable or a parenthesis (`x²`, never
a unit such as `m²` or `km²`), `hoch n`."""
_SHAPES = re.compile(
    r"(?i)\b(?:sine|sinus\w*|cosine|[ck]osinus\w*|tangens\w*|parab\w*|hyperb\w*|squared|cubed|quadratic"
    r"|quadratisch\w*|cubic|kubisch\w*|polynom\w*|logarithm\w*|exponential(?:funktion|kurve)\w*"
    r"|exponential\s+(?:function|curve)|wurzelfunktion\w*|square\s+root|quadratwurzel\w*"
    r"|gau(?:ss|ß)(?:\s*(?:-\s*)?kurve\w*|sche\w*|ian\w*|verteilung\w*)|gaussian|normalverteilung\w*"
    r"|normal\s+(?:distribution|curve)|bell\s+curve|glockenkurve\w*|spiralen?|spirals?)\b"
)
"""The names of a curve. Words that data has as well (`curve`, `Kurve`, `function`, `exp`, `exponential growth`,
`Quadratmeter`) are none: a formula request needs more than they say."""
_COUNT = re.compile(
    r"(?i)(?:^|[^\w.])[0-9]+\s*(?:points?|punkte?n?|werte?n?|values?|samples?|stützstellen|steps?|schritte?n?)\b"
    r"|\b(?:in\s+steps\s+of|step(?:\s+size)?|schrittweite|(?:in\s+)?schritten\s+von|abstand)\s*(?:[:=]\s*)?"
    r"[-+−]?[0-9]+(?:[.,][0-9]+)?"
)
"""A point count or a step (`30 points`, `mit 50 Punkten`, `in Schritten von 0.5`): part of a formula request."""
_VALUE = re.compile(r"(?<![\w.])[-+−]?[0-9]+(?:[.,][0-9]+)?(?P<unit>[^\W\d_]*)")
_OPERATOR_BEFORE = frozenset("+-−*/^×·")
_OPERATOR_AFTER = frozenset("*/^×·²³")
_DIGIT = re.compile(r"[0-9]")
MAX_SHAPE_WORDS = 6
"""The longest request that names a curve and nothing else (`zeichne eine Gaußkurve`), in words."""


def looks_like_formula(text: str) -> bool:
    """Whether pasted text asks for a formula to compute rather than holding a table.

    The dataset route asks this only where the parser found no table (`no_table`, a
    broken `unparseable`, or the one-column reading the transcriber would get), so the
    text reaches neither the transcriber nor the store. It reads what the transcriber
    would read (at most `MAX_TRANSCRIBE_CHARS` characters); text of several lines whose
    sniffed delimiter splits two of its first lines is a table, perhaps a broken one.
    The rest is read line by line and sentence by sentence, each of at most
    `MAX_FORMULA_CHARS` characters, and is a formula when one of them holds one of these:

    * a call of a function of the expression language whose argument uses a variable
      (`sin(x)`, `exp(-t)`, `Sin(x)`; never `Max(3)`, a name with a count, see
      `_formula_call`), or a call without parentheses (`sin x`, `√x`);
    * an assignment of an expression with a variable (`y = x**2`, `f(x) = 2x + 1`,
      `y = x`; never `Tier = Hund` or `Äpfel = 3x`, see `_assignment`);
    * a range phrase `from <a> to <b>` or `von <a> bis <b>` whose ends are numbers, `pi`
      or `e`, with a constant at an end, a one-letter variable right before it
      (`für n von 0 bis 10`; never a unit, as in `CO2 in t von 2020 bis 2023`), a power
      (`x**2`, `x^2`, `x²`, `hoch n`; never `m²`) or a curve's name in the text
      (`Parabel`, `Sinuskurve`, `normal distribution`; never a word that data has as
      well, such as `curve`, `Funktion`, `exp` or `Quadratmeter`);
    * a curve's name and nothing else, in at most `MAX_SHAPE_WORDS` words without a
      number (`Gaußkurve`).

    Text that holds its own values is data, whatever else it says: `MIN_DATA_VALUES`
    numbers or more outside a formula's parts (its ranges, its expressions, parameters
    such as `a = 2` or `x = 1, 2, 3`, a point count or a step) make it a table in words
    for the transcriber ("Umsatz von 2020 bis 2024: 10 12 15", "exponential growth from
    2019 to 2023: 1 2 4 8 16", a space-separated table under the header `x sin(x)`). A
    number glued to a word (`CO2`) or that is the operand of an operator (`x^2`,
    `2x + 1`) is no value. A formula on a line or sentence longer than
    `MAX_FORMULA_CHARS` characters is not found; the transcriber's own rule
    (`prompts/transcriber.md`: compute nothing, write only the values the text holds)
    covers it.
    """
    stripped = text.strip()
    if not stripped or len(stripped) > MAX_TRANSCRIBE_CHARS:
        return False
    lines = [line for line in stripped.splitlines() if line.strip()]
    if _delimited(stripped, lines):
        return False
    segments = [segment.strip() for segment in _SEGMENT.split(stripped) if segment.strip()]
    readable = "\n".join(segment for segment in segments if len(segment) <= MAX_FORMULA_CHARS)
    signs = bool(_POWER.search(readable) or _SHAPES.search(readable))
    formula = False
    values = 0
    for segment in segments:
        if len(segment) <= MAX_FORMULA_CHARS:
            parts, found = _formula_parts(segment, signs)
            formula = formula or found
            segment = _blank(segment, parts)
        values += _data_values(segment)
    if values >= MIN_DATA_VALUES:
        return False
    return formula or _shape_only(stripped)


def _delimited(text: str, lines: list[str]) -> bool:
    """Whether text of several lines is a table: its sniffed delimiter is in at least two of its first lines."""
    if len(lines) < 2:
        return False
    delimiter = sniff_delimiter(text)[0]
    return delimiter is not None and sum(delimiter in line for line in lines[:SNIFF_LINES]) >= 2


def _formula_parts(segment: str, signs: bool) -> tuple[list[tuple[int, int]], bool]:
    """The spans of one line or sentence that belong to a formula request, and whether it asks for a formula.

    `signs` says whether the text has a power or a curve's name, which makes a range
    phrase with plain numbers a formula's range. Parameters (`a = 2`, `x = 1, 2, 3`),
    point counts and every range phrase are parts without being a formula by themselves.
    """
    parts: list[tuple[int, int]] = []
    found = False
    for match in _CALL.finditer(segment):
        end = _closing(segment, match.end() - 1)
        if end is not None and _formula_call(match.group("name"), segment[match.start() : end]):
            parts.append((match.start(), end))
            found = True
    for pattern in (_BARE_CALL, _ROOT_SIGN):
        for match in pattern.finditer(segment):
            parts.append(match.span())
            found = True
    for match in _ASSIGNMENT.finditer(segment):
        part, formula = _assignment(match)
        if part is not None:
            parts.append(part)
            found = found or formula
    for match in _RANGE.finditer(segment):
        parts.append(match.span())
        ends = (match.group("start"), match.group("stop"))
        if (
            signs
            or any(_CONSTANT_ENDPOINT.search(end.strip()) for end in ends)
            or _SUBJECT.search(segment[: match.start()])
        ):
            found = True
    parts.extend(match.span() for match in _COUNT.finditer(segment))
    return parts, found


def _formula_call(name: str, text: str) -> bool:
    """Whether a call found in pasted text (`text` from the name to its `)`) is a formula's.

    Its argument must parse under the whitelist and use a variable, so `Max(3)` or
    `Abs(12)` (a name with a count) is none. A function name written with a capital
    letter, as a name or a word is (`Max(Anna, Tom)`, `Abs(atz)`), counts only with a
    one-letter variable or an operator inside (`Sin(x)`, `Exp(-t)`).
    """
    tree = _parse_formula(name.lower() + text[len(name) :], implicit_product=True)
    if tree is None:
        return False
    variables = _variables(tree)
    if not variables:
        return False
    operator = any(isinstance(node, ast.BinOp | ast.UnaryOp) for node in ast.walk(tree))
    return name.islower() or operator or all(len(variable) == 1 for variable in variables)


def _assignment(match: re.Match[str]) -> tuple[tuple[int, int] | None, bool]:
    """The span of an assignment's right side that is part of a formula request, and whether it is a formula.

    The right side, cut before a word such as `from`, `for` or `von`, or its part before
    the first comma, is a formula when it parses under the whitelist and uses a
    variable: with an operator or a call (`y = x**2`), or as a bare name of one or two
    letters (`y = x`), so `Tier = Hund` stays data. A number glued to a name (`2x`) is a
    product only after a formula's left side (`y`, `f(x)`), so `Äpfel = 3x` stays a
    count. One letter set to numbers (`a = 2`, `x = 1, 2, 3`) is a parameter: part of
    the request, but no formula by itself.
    """
    lhs, rhs, start = match.group("lhs"), match.group("rhs"), match.start("rhs")
    candidate = _RHS_STOP.split(rhs, maxsplit=1)[0].rstrip()
    math_name = _MATH_NAME.fullmatch(lhs) is not None
    for piece in dict.fromkeys((candidate, candidate.split(",", 1)[0].rstrip())):
        tree = _parse_formula(piece, implicit_product=math_name)
        if tree is None or not _variables(tree):
            continue
        if isinstance(tree, ast.Name) and len(tree.id) > 2:
            continue
        return (start, start + len(piece)), True
    if _PARAMETER.fullmatch(lhs) and _constants(candidate):
        return (start, start + len(candidate)), False
    return None, False


def _constants(text: str) -> bool:
    """Whether `text` is one or more numbers or constant expressions, separated by commas or semicolons."""
    for item in re.split(r"[,;]", text):
        tree = _parse_formula(item, implicit_product=True)
        if tree is None or _variables(tree):
            return False
    return True


def _parse_formula(text: str, *, implicit_product: bool) -> ast.expr | None:
    """The checked tree of a formula as people type it (`x^2`, `x²`, `√x`, `sin x`, `ln(x)`, `2x`), or None."""
    normalised = text.strip().replace("^", "**").replace("²", "**2").replace("³", "**3").replace("π", "pi")
    normalised = _LN.sub("log(", normalised)
    normalised = _ROOT_SIGN.sub(lambda m: "sqrt(" if m.group("paren") else f"sqrt({m.group('arg')})", normalised)
    normalised = _BARE_CALL.sub(lambda m: f"{_bare_name(m.group('name'))}({m.group('arg')})", normalised)
    if implicit_product:
        normalised = _IMPLICIT_PRODUCT.sub(r"\g<before>\g<number>*", normalised)
    if not normalised:
        return None
    try:
        return parse_expression(normalised, None, "text")
    except GenerateError:
        return None


def _bare_name(name: str) -> str:
    lower = name.lower()
    return "log" if lower == "ln" else lower


def _variables(tree: ast.expr) -> list[str]:
    """The names of a checked tree that are neither a function nor a constant."""
    return [
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id not in FUNCTIONS and node.id not in CONSTANTS
    ]


def _closing(text: str, index: int) -> int | None:
    """One past the `)` that closes the parenthesis at `index`, within `MAX_EXPRESSION_CHARS`; None without one."""
    depth = 0
    for position in range(index, min(len(text), index + MAX_EXPRESSION_CHARS)):
        if text[position] == "(":
            depth += 1
        elif text[position] == ")":
            depth -= 1
            if depth == 0:
                return position + 1
    return None


def _blank(text: str, parts: list[tuple[int, int]]) -> str:
    """`text` with every span of `parts` replaced by spaces, so its numbers count as no value."""
    chars = list(text)
    for start, end in parts:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _data_values(text: str) -> int:
    """How many numbers of `text` stand as values: not glued to a word, and no operand of an operator.

    `CO2` holds none, `x^2` and `2x + 1` none (the `2` follows `^`, `2x` comes before
    `+`), while `3x,` (a count), `m² 5 7 9`, `-5 -3 0` and `4,5 5,1` hold values.
    """
    count = 0
    for match in _VALUE.finditer(text):
        before = text[: match.start()].rstrip()[-1:]
        after = text[match.end() :].lstrip()[:1]
        if before in _OPERATOR_BEFORE or after in _OPERATOR_AFTER:
            continue
        if len(match.group("unit")) == 1 and after and after in "+-−":
            continue
        count += 1
    return count


def _shape_only(text: str) -> bool:
    """A short request that names a curve and holds no number (`Gaußkurve`, `eine Parabel`)."""
    return len(text.split()) <= MAX_SHAPE_WORDS and not _DIGIT.search(text) and _SHAPES.search(text) is not None


def stated_values(text: str) -> int:
    """How many numbers of `text` stand as values, outside its range phrases (`between 10 and 100`, `von 1 bis 5`).

    The data-request guard (`classify.looks_like_data_request`) counts them as the formula
    guard counts its values: a request that names its sizes ("3 Kategorien und 20 Zeilen")
    holds fewer than `MIN_DATA_VALUES`, a sentence with its own data ("Hund 7, Katze 3 und
    Vogel 4") holds that many.
    """
    return _data_values(_blank(text, [match.span() for match in _RANGE.finditer(text)]))
