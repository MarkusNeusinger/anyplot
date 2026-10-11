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
`^` among them, a number glued to a name such as `2x`) is `invalid_expression` with a
message that names the construct, and so is an expression of more than
`MAX_EXPRESSION_NODES` nodes. A range's `start` and `stop` are expressions over the
constants only. Every value is a float64 array evaluated under `np.errstate(all="ignore")`,
never a Python int or float, so an overflow (`10**400`), a division by zero or a function
outside its domain (`log(-1)`) gives inf or NaN, which become missing cells, never an
exception.

The table: the variable columns first (two variables make a grid, the cartesian
product with the first variable slowest), then the series columns; every value
rounded to `SIGNIFICANT_DIGITS` significant digits and written as the parser writes a
number (`repr` of the float, so every column re-parses as `number`), a missing cell
empty. Errors raise `GenerateError(code, message)`: `invalid_expression`,
`invalid_range` (an endpoint that is not finite, equal endpoints, a range wider than a
float holds), `too_many_points` (a grid over `MAX_GRID_ROWS`), `undefined` (a series
without one defined value) and `too_large` (a CSV over the parser's input cap). A
message names the variable or series and at most quotes the expression's own text.

`looks_like_formula` is the dataset route's guard: text pasted into the data field that
asks for a formula is refused (`422 formula`) instead of reaching the transcriber, which
would let a model write the rows.
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
from .parse import MAX_INPUT_BYTES, sniff_delimiter
from .prepare import NewName


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
MAX_FORMULA_LINES = 3

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

    axes = [
        np.linspace(start, stop, variable.points, dtype=np.float64)
        for variable, (start, stop) in zip(spec.variables, ranges, strict=True)
    ]
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
                f"{series.name}: no value is defined over the range (for example log or sqrt of negative numbers)",
            )
        if undefined:
            verb = "is" if undefined == 1 else "are"
            warnings.append(f"{series.name}: {undefined} of {rows} values {verb} undefined and left empty")
        columns.append(_texts(result))

    csv_text = _write([*names, *(series.name for series in spec.series)], columns)
    if len(csv_text.encode("utf-8")) > MAX_INPUT_BYTES:
        raise GenerateError(
            "too_large",
            f"the table would be larger than {MAX_INPUT_BYTES // 1024} KB; use fewer points or fewer series",
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


def _texts(values: Array) -> list[str]:
    """Every value at `SIGNIFICANT_DIGITS` significant digits, written as the parser writes a number; NaN and inf empty."""
    texts = []
    for value in values.tolist():
        if not math.isfinite(value):
            texts.append("")
            continue
        rounded = float(f"{value:.{SIGNIFICANT_DIGITS}g}")
        texts.append(repr(rounded if rounded else 0.0))  # no `-0.0`
    return texts


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
        span = f"{variable.name} from {start:.{CHANGE_DIGITS}g} to {stop:.{CHANGE_DIGITS}g}"
        spans.append(f"{span} ({variable.points} points)" if grid else span)
    formulas = ", ".join(f"{series.name} = {_one_line(series.expression)}" for series in spec.series)
    line = f"generated {rows} {'row' if rows == 1 else 'rows'}: {' and '.join(spans)}, {formulas}"
    return line if len(line) <= MAX_NOTE_CHARS else line[: MAX_NOTE_CHARS - 1] + "…"


def _one_line(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


# --- Expressions ------------------------------------------------------------------------------


def parse_expression(text: str, variables: frozenset[str] | None, where: str, *, endpoint: bool = False) -> ast.expr:
    """The checked tree of one expression; raises `GenerateError("invalid_expression", ...)`.

    `variables` are the names an expression may use besides the constants; None accepts
    any name that is no function (`looks_like_formula` reads a pasted formula whose
    variables it cannot know). `where` names the series or endpoint in the message.
    """
    source = _one_line(text)
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:
        raise GenerateError("invalid_expression", f"{where}: {_syntax_hint(source, exc)}") from None
    except (ValueError, RecursionError, MemoryError):
        raise GenerateError("invalid_expression", f"{where}: the expression cannot be read") from None
    _check(tree.body, variables, where, endpoint)
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
            if endpoint:
                raise fail("start and stop take numbers and the constants pi, e, tau only, no variable")
            if variables is not None and name not in variables:
                if name == "π":
                    raise fail("write pi for π")
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

_CALL = re.compile(r"(?i)(?<![\w.])(?:" + "|".join(sorted(FUNCTIONS, key=len, reverse=True)) + r")\(")
_ASSIGNMENT = re.compile(
    r"(?<![\w.=<>!])[A-Za-z_]\w{0,30}(?:\s*\(\s*[A-Za-z_]\w{0,10}(?:\s*,\s*[A-Za-z_]\w{0,10})?\s*\))?"
    r"\s*=(?!=)\s*(?P<rhs>[^\n=;]{1,200})"
)
_RHS_STOP = re.compile(
    r"(?i)\s(?:from|von|for|für|fuer|with|mit|between|zwischen|in|over|über|ueber|on|auf|where|wobei|bis|to|and|und)\b"
)
_ENDPOINT = r"[-+−]?\s?(?:[0-9]+(?:[.,][0-9]+)?\s?\*?\s?(?:pi|π|tau|e)?|pi|π|tau|e)(?:\s?/\s?[0-9]+)?"
_RANGE = re.compile(
    rf"(?i)\b(?:from|von|between|zwischen)\s+(?P<start>{_ENDPOINT})\s+(?:to|bis|and|und)\s+(?P<stop>{_ENDPOINT})(?!\w)"
)
_CONSTANT_ENDPOINT = re.compile(r"(?i)pi|π|tau|^[-+−]?\s?e$")
_VARIABLE = re.compile(r"(?i)(?<![\w'’.-])[xtyz](?![\w'’.-])")
_MATH_WORDS = re.compile(
    r"(?i)\b(?:a?sinh?|a?cosh?|a?tanh?|atan2|exp|log(?:10|2)?|ln|sqrt|sine|sinus|cosine|[ck]osinus|tangent|tangens"
    r"|parabola|parabel|squared|quadrat\w*|cubed|functions?|funktion\w*|curve|kurve|exponential\w*|logarithm\w*"
    r"|wurzel|polynom\w*|gau(?:ss|ß)\w*|normalverteilung|normal\s+distribution|bell\s+curve|glockenkurve|spirale?)\b"
)
_POWER = re.compile(r"\*\*|\^|[²³]")
_IMPLICIT_PRODUCT = re.compile(r"(?<![\w.])([0-9]+(?:\.[0-9]+)?)(?![eE][+-]?[0-9])(?=[A-Za-z_(])")


def looks_like_formula(text: str) -> bool:
    """Whether pasted text asks for a formula to compute rather than holding a table.

    The dataset route asks this only where the parser found no table (`no_table`, a
    broken `unparseable`, or the one-column reading the transcriber would get), so the
    text reaches neither the transcriber nor the store. A formula is short: at most
    `MAX_FORMULA_CHARS` characters on at most `MAX_FORMULA_LINES` lines, and text of
    several lines with a delimiter in its first one is a table, perhaps a broken one. It
    then needs one of these:

    * a call of a function of the expression language, as in `sin(x)` or `exp(-t)`;
    * an assignment `<name> = <expression>` whose expression (cut before a word such as
      `from`, `for` or `von`) parses under the whitelist and uses a variable: with an
      operator or a call (`y = x**2`, `f(x) = 2x + 1`), or a bare name of one or two
      letters (`y = x`), so `Tier = Hund` or `Anzahl = 7` stays data;
    * a range phrase `from <a> to <b>` or `von <a> bis <b>` whose ends are numbers, `pi`
      or `e` (`-pi`, `2 pi`, `-3.5`), together with a sign of mathematics: a constant at
      an end, a variable `x`, `t`, `y` or `z` as a word, a power (`**`, `^`, `²`), or a
      word such as `sin`, `parabola` or `Kurve`. So "Umsatz von 2020 bis 2024: 10 12 15"
      stays data, and "from Monday to Friday" has no numbers at all.
    """
    stripped = text.strip()
    if not stripped or len(stripped) > MAX_FORMULA_CHARS:
        return False
    lines = [line for line in stripped.splitlines() if line.strip()]
    if len(lines) > MAX_FORMULA_LINES:
        return False
    if len(lines) > 1 and sniff_delimiter(stripped)[0] is not None:
        return False
    if _CALL.search(stripped):
        return True
    if any(_formula_expression(match.group("rhs")) for match in _ASSIGNMENT.finditer(stripped)):
        return True
    for match in _RANGE.finditer(stripped):
        ends = (match.group("start"), match.group("stop"))
        if (
            any(_CONSTANT_ENDPOINT.search(end.strip()) for end in ends)
            or _VARIABLE.search(stripped)
            or _POWER.search(stripped)
            or _MATH_WORDS.search(stripped)
        ):
            return True
    return False


def _formula_expression(rhs: str) -> bool:
    """Whether the right side of an assignment, up to a word such as `from`, is an expression with a variable."""
    candidate = _RHS_STOP.split(rhs, maxsplit=1)[0]
    for text in (candidate, candidate.split(",", 1)[0]):
        normalised = text.strip().replace("^", "**").replace("²", "**2").replace("³", "**3")
        normalised = normalised.replace("π", "pi").replace("·", "*").replace("×", "*").replace("−", "-")
        normalised = _IMPLICIT_PRODUCT.sub(r"\1*", normalised)
        if not normalised:
            continue
        try:
            tree = parse_expression(normalised, None, "rhs")
        except GenerateError:
            continue
        names = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
        variables = [name for name in names if name not in FUNCTIONS and name not in CONSTANTS]
        if not variables:
            continue
        if isinstance(tree, ast.Name):
            if len(tree.id) <= 2:
                return True
            continue
        return True
    return False
