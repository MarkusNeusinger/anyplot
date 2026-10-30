"""tree-sitter for the catalogue code that is not Python: parsing, syntax findings and the node helpers the profiles share.

The Python profile reads code with `ast`; every other language of the catalogue (R first,
then JavaScript and Julia, `agentic/specs/261024-agent-all-libraries.md`) is read with
tree-sitter, through this module. Two packages are pinned exactly in the `agents` extra
(owner decision of 2026-10-29): `tree-sitter` 0.26.0 and `tree-sitter-language-pack`
0.13.0, which bundles every grammar as a compiled extension in its wheel (the R grammar
is r-lib's tree-sitter-r, MIT). The pack's 1.x line downloads grammars at run time, which
the service must never do, so `GRAMMARS` names the grammars this code reads and a test
pins both versions.

The module has three layers, and only the last one knows a grammar's node names:

* **Parsing.** `Source` parses a string once and maps tree-sitter's positions (0-based
  rows, UTF-8 byte columns) to the 1-based lines and character offsets the edit applier
  and the messages use, the same convention as `regions.SourceIndex` for Python: lines
  are 1-based and inclusive, offsets 0-based with an exclusive end, so
  `code[span.start:span.end]` is the region. Non-ASCII text (the catalogue's `·`, `—`
  and `°`) never shifts a span.
* **Syntax and walking.** `syntax_problems` lists the ERROR and MISSING nodes, which is
  how tree-sitter reports code it could not read; it never raises, so a profile turns
  them into a `syntax` finding. `walk` is an iterative pre-order walk (no recursion, so a
  deeply nested adversarial file cannot exhaust the stack), and `statements` and
  `comments` split a program's top level.
* **R.** R's string literals decoded to their value (escapes and raw strings
  `r"(...)"`), backtick names, callee names (`fn`, `pkg::fn`, `pkg:::fn`), the arguments
  of a call or subset with their names and positions, and assignments (`<-`, `=`, `->`,
  `<<-`, `->>`) with the name they bind.
* **Julia** (J2a of step 5, 2026-10-29; tree-sitter-julia from the same pack, which reads
  all 325 catalogue Makie files without an ERROR or MISSING node). Julia's string literals
  decoded to their value (escapes, line continuations; `None` for a string with an
  interpolation or a triple-quoted one), the prefix and text of a string macro
  (`colorant"#009E73"`), dotted names (`Random.seed!`, `Base.Filesystem.rm`), the
  positional and keyword arguments of a call, assignments with the names they bind, and
  every binding site (assignments, parameters, loop and `let` variables, functions,
  types). The grammar names few fields, so the helpers read children by position.
* **JavaScript** (JS-3 of step 3, 2026-10-30; the pack's `javascript` grammar for the
  Chart.js, D3, ECharts and Highcharts files and its `tsx` grammar, TypeScript with JSX,
  for MUI X's, which read all 1,617 catalogue files without an ERROR or MISSING node).
  String and template literals decoded to their value (`None` for a template with a
  substitution), numbers, dotted callees (`d3.scaleLinear`, `Math.random`), and the
  scopes: every binding with the node whose range it is visible in (`var` its function,
  `let`, `const`, classes and function declarations their block, parameters their
  function), so `js_references` can tell a free name, which the page's global object
  resolves, from one the file binds around it. Type positions of TSX (annotations,
  aliases, interfaces) run nothing and are skipped. The grammar names its fields, so the
  helpers read them by name.

This module imports only the standard library and tree-sitter (2026-10-29): the R,
Julia and JavaScript region and readiness detection built on it is meant to move to
`core/` later, so the regen gate's adapt route can run the same checks as the agent.

A point's `.row` and `.column` are never read (`first_line`, `last_line` and `column`
index the point instead). Under Python 3.14 the attribute getters of tree-sitter
0.26.0's `Point` hand out an int it does not own: `node.start_point.row` past 256 (the
interpreter's cached small ints) frees the int while it is in use, and the process
segfaults at the next garbage collection (found on 2026-10-29 with the catalogue's
line 271; `point[0]` is safe). A test refuses the attribute form in this package.
"""

import bisect
import functools
import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

import tree_sitter_language_pack
from tree_sitter import Language, Node, Parser, Tree


TREE_SITTER_VERSION = "0.26.0"
LANGUAGE_PACK_VERSION = "0.13.0"
"""The pinned versions (`pyproject.toml`, the `agents` extra); a test compares them with the installed ones."""

Grammar = Literal["r", "julia", "javascript", "tsx"]
GRAMMARS: tuple[Grammar, ...] = ("r", "julia", "javascript", "tsx")
"""The grammars this code reads. The pack's `typescript` grammar (TypeScript without JSX) is not among them: MUI X's
files are `.tsx`, which the `tsx` grammar reads, and no catalogue file is `.ts`."""
COMMENTS = frozenset({"comment", "line_comment", "block_comment", "html_comment"})
"""The comment node types: R's and JavaScript's `comment` (`//` and `/* */` in JavaScript), Julia's `line_comment`
(`# ...`) and `block_comment` (`#= ... =#`), and JavaScript's `html_comment` (`<!--`, which a classic script reads as a
line comment)."""

MAX_SYNTAX_PROBLEMS = 20
"""`syntax_problems` stops after this many: the first one is what a repair needs."""


@functools.cache
def language(grammar: Grammar) -> Language:
    """The compiled grammar from the language pack; never downloaded (0.13.0 bundles it)."""
    if grammar not in GRAMMARS:
        raise ValueError(f"no tree-sitter grammar {grammar!r}; served: {', '.join(GRAMMARS)}")
    return tree_sitter_language_pack.get_language(grammar)


def parse(code: str, grammar: Grammar) -> Tree:
    """`code` parsed as `grammar`. tree-sitter never fails: unreadable code shows as ERROR and MISSING nodes."""
    return Parser(language(grammar)).parse(code.encode("utf-8"))


def first_line(node: Node) -> int:
    """The 1-based line `node` starts on (the module docstring says why the point is indexed)."""
    return node.start_point[0] + 1


def last_line(node: Node) -> int:
    """The 1-based line `node` ends on."""
    return node.end_point[0] + 1


def column(node: Node) -> int:
    """The UTF-8 byte column `node` starts at; 0 for a node at the start of its line."""
    return node.start_point[1]


@dataclass(frozen=True, slots=True)
class Span:
    """A region of a source string: lines `first_line..last_line` and characters `[start, end)`.

    The twin of `regions.Span` for the tree-sitter languages (this module imports nothing
    from the Python profile); both have the same fields and methods, so the edit applier
    takes either.
    """

    first_line: int
    last_line: int
    start: int
    end: int

    def overlaps(self, start: int, end: int) -> bool:
        """Whether the half-open character range `[start, end)` shares a character with this span."""
        return start < self.end and self.start < end

    def lines(self) -> str:
        """`line 12` or `lines 12-14`, for messages."""
        if self.first_line == self.last_line:
            return f"line {self.first_line}"
        return f"lines {self.first_line}-{self.last_line}"


class Source:
    """One parsed source string and the maps between tree-sitter's positions and the text's.

    tree-sitter counts rows by `\\n` and columns in UTF-8 bytes; `Source` answers in
    1-based lines and character offsets. A line ends after its `\\n` (a `\\r` before it
    stays part of the line, as tree-sitter keeps it).
    """

    def __init__(self, code: str, grammar: Grammar) -> None:
        self.code = code
        self.grammar = grammar
        self.data = code.encode("utf-8")
        self.tree = parse(code, grammar)
        self.root = self.tree.root_node
        # The character offset of every byte offset that starts a character, for the non-ASCII case only.
        self._char_bytes: list[int] | None = None
        if len(self.data) != len(code):
            offsets, position = [], 0
            for char in code:
                offsets.append(position)
                position += len(char.encode("utf-8"))
            offsets.append(position)
            self._char_bytes = offsets
        self._line_starts = [0]
        position = code.find("\n")
        while position != -1:
            self._line_starts.append(position + 1)
            position = code.find("\n", position + 1)

    @property
    def line_count(self) -> int:
        """Number of lines; a trailing newline opens an empty last line."""
        return len(self._line_starts)

    def char(self, byte_offset: int) -> int:
        """The character offset of a byte offset (one that starts a character, as every node boundary does)."""
        if self._char_bytes is None:
            return byte_offset
        return bisect.bisect_left(self._char_bytes, byte_offset)

    def line_start(self, line: int) -> int:
        """Offset of the first character of `line`."""
        return self._line_starts[line - 1]

    def line_end(self, line: int) -> int:
        """Offset just past the newline that ends `line` (the end of the source on the last line)."""
        return self._line_starts[line] if line < len(self._line_starts) else len(self.code)

    def line_text(self, line: int) -> str:
        """The text of `line` including its newline."""
        return self.code[self.line_start(line) : self.line_end(line)]

    def line_of(self, offset: int) -> int:
        """The 1-based line that holds the character at `offset`."""
        return bisect.bisect_right(self._line_starts, offset)

    def text(self, node: Node) -> str:
        """The exact source text of `node`."""
        return self.data[node.start_byte : node.end_byte].decode("utf-8")

    def node_span(self, node: Node) -> Span:
        """The exact characters of `node`."""
        return Span(first_line(node), last_line(node), self.char(node.start_byte), self.char(node.end_byte))

    def lines_span(self, node: Node) -> Span:
        """The whole lines of `node`, newline of its last line included."""
        first, last = first_line(node), last_line(node)
        return Span(first, last, self.line_start(first), self.line_end(last))


@dataclass(frozen=True, slots=True)
class SyntaxProblem:
    """Code tree-sitter could not read: an ERROR node, or a MISSING token it inserted to recover (`missing`)."""

    line: int
    missing: str | None = None

    def message(self) -> str:
        """`unexpected code at line 12` or `missing ")" at line 12`, for findings and readiness reasons."""
        if self.missing is not None:
            return f'missing "{self.missing}" at line {self.line}'
        return f"unexpected code at line {self.line}"


def syntax_problems(tree: Tree, limit: int = MAX_SYNTAX_PROBLEMS) -> list[SyntaxProblem]:
    """The ERROR and MISSING nodes of `tree` in source order, at most `limit`; empty for code that reads cleanly.

    Only subtrees that report an error are entered, so clean code costs one check.
    """
    problems: list[SyntaxProblem] = []
    stack = [tree.root_node] if tree.root_node.has_error else []
    while stack and len(problems) < limit:
        node = stack.pop()
        if node.is_missing:
            problems.append(SyntaxProblem(first_line(node), node.type))
        elif node.is_error:
            problems.append(SyntaxProblem(first_line(node)))
        else:
            stack.extend(reversed([child for child in node.children if child.has_error or child.is_missing]))
    return problems


def walk(node: Node) -> Iterator[Node]:
    """`node` and every node below it, in source order (pre-order), without recursion."""
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


@dataclass(frozen=True, slots=True)
class Visit:
    """A node met by `visits`, with its parent and its field name in that parent (None for none)."""

    node: Node
    parent: Node | None
    field: str | None


def visits(root: Node) -> Iterator[Visit]:
    """Every node below and including `root` in source order, with its parent and field, without recursion.

    The rules of a profile ask where a node stands (an argument's name or its value, the
    callee of a call, the right side of `$`), and `Node.parent` walks down from the root
    on every call, so one pass hands the context along instead.
    """
    stack: list[Visit] = [Visit(root, None, None)]
    while stack:
        visit = stack.pop()
        yield visit
        node = visit.node
        children = node.children
        stack.extend(
            Visit(children[index], node, node.field_name_for_child(index)) for index in reversed(range(len(children)))
        )


def statements(root: Node) -> list[Node]:
    """The top-level statements of a program: its named children that are not comments."""
    return [child for child in root.named_children if child.type not in COMMENTS]


def comments(root: Node) -> list[Node]:
    """Every comment node, in source order."""
    return [node for node in walk(root) if node.type in COMMENTS]


# --- R ---------------------------------------------------------------------------------------

R_ASSIGNMENTS = frozenset({"<-", "=", "<<-", "->", "->>"})
R_LEFT_ASSIGNMENTS = frozenset({"<-", "=", "<<-"})
R_SUPER_ASSIGNMENTS = frozenset({"<<-", "->>"})
R_LITERALS = frozenset({"float", "integer", "complex", "true", "false", "null", "na", "inf", "nan"})
"""The R grammar's literal node types besides `string`."""

_R_SIMPLE_ESCAPES = {
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "b": "\b",
    "a": "\a",
    "f": "\f",
    "v": "\v",
    "\\": "\\",
    "'": "'",
    '"': '"',
    "`": "`",
    " ": " ",
    "\n": "\n",
}
_HEX = frozenset("0123456789abcdefABCDEF")
_OCTAL = frozenset("01234567")
_RAW_OPENERS = {"(": ")", "[": "]", "{": "}"}


def r_string(text: str) -> str | None:
    """The value of an R string literal's source text, or None when R would not read it.

    Quoted strings (`"..."`, `'...'`) take R's escapes: the single letters, octal
    `\\ooo`, `\\xhh`, `\\uhhhh`, `\\u{hhhh}`, `\\Uhhhhhhhh` and `\\U{...}`. R refuses an
    unknown escape and a nul character, so those give None, and so does a code point
    that is no character. Raw strings (`r"(...)"`, `R'[...]'`, `r"--{...}--"`, R 4.0)
    are their content, verbatim.
    """
    if len(text) >= 2 and text[0] in "rR" and text[1] in "\"'":
        return _r_raw_string(text)
    if len(text) < 2 or text[0] not in "\"'`" or text[-1] != text[0]:
        return None
    return _r_unescape(text[1:-1])


def _r_raw_string(text: str) -> str | None:
    quote = text[1]
    dashes = len(text) - len(text[2:].lstrip("-")) - 2
    opener_at = 2 + dashes
    if opener_at >= len(text) or text[opener_at] not in _RAW_OPENERS:
        return None
    closing = _RAW_OPENERS[text[opener_at]] + "-" * dashes + quote
    if not text.endswith(closing) or len(text) < opener_at + 1 + len(closing):
        return None
    return text[opener_at + 1 : len(text) - len(closing)]


def _r_unescape(body: str) -> str | None:
    out: list[str] = []
    position = 0
    while position < len(body):
        char = body[position]
        if char != "\\":
            out.append(char)
            position += 1
            continue
        if position + 1 >= len(body):
            return None
        code = body[position + 1]
        if code in _R_SIMPLE_ESCAPES:
            out.append(_R_SIMPLE_ESCAPES[code])
            position += 2
            continue
        value: int | None
        if code in _OCTAL:
            end = position + 1
            while end < len(body) and end < position + 4 and body[end] in _OCTAL:
                end += 1
            value = int(body[position + 1 : end], 8)
            position = end
        elif code in "xuU":
            value, position = _r_hex_escape(body, position + 2, {"x": 2, "u": 4, "U": 8}[code], code != "x")
        else:
            return None  # R: "'\q' is an unrecognized escape"
        if value is None:
            return None
        if value == 0 or value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
            return None
        out.append(chr(value))
    return "".join(out)


def _r_hex_escape(body: str, start: int, width: int, braces: bool) -> tuple[int | None, int]:
    """The code point of a `\\x`, `\\u` or `\\U` escape whose digits start at `start`, and the offset after it."""
    if braces and start < len(body) and body[start] == "{":
        end = body.find("}", start)
        digits = body[start + 1 : end] if end != -1 else ""
        if not digits or len(digits) > width or any(char not in _HEX for char in digits):
            return None, start
        return int(digits, 16), end + 1
    end = start
    while end < len(body) and end < start + width and body[end] in _HEX:
        end += 1
    if end == start:
        return None, start
    return int(body[start:end], 16), end


def r_name(text: str) -> str | None:
    """An R identifier's name: the text itself, or a backtick name's content (`` `my var` `` is `my var`)."""
    if text.startswith("`"):
        return r_string(text)
    return text


def r_identifier(source: Source, node: Node) -> str | None:
    """The name of an `identifier` node, backticks removed; None for any other node."""
    if node.type != "identifier":
        return None
    return r_name(source.text(node))


def r_string_value(source: Source, node: Node) -> str | None:
    """The value of a `string` node; None for any other node or one R would not read."""
    if node.type != "string":
        return None
    return r_string(source.text(node))


def r_unwrap(node: Node) -> Node:
    """`node` without enclosing parentheses: `((x))` is `x`."""
    while node.type == "parenthesized_expression":
        inner = [child for child in node.named_children if child.type != "comment"]
        if len(inner) != 1:
            return node
        node = inner[0]
    return node


def r_callee(source: Source, call: Node) -> str | None:
    """The function a `call` names: `fn`, `pkg::fn` or `pkg:::fn`; None for any other callee (a call, a string)."""
    function = call.child_by_field_name("function")
    if function is None:
        return None
    if function.type == "identifier":
        return r_identifier(source, function)
    if function.type == "namespace_operator":
        return r_namespace(source, function)
    return None


def r_namespace(source: Source, node: Node) -> str | None:
    """`pkg::fn` or `pkg:::fn` for a `namespace_operator` node whose two sides are names, else None."""
    lhs, operator, rhs = (
        node.child_by_field_name("lhs"),
        node.child_by_field_name("operator"),
        node.child_by_field_name("rhs"),
    )
    if lhs is None or operator is None or rhs is None:
        return None
    package = r_identifier(source, lhs) if lhs.type == "identifier" else r_string_value(source, lhs)
    name = r_identifier(source, rhs) if rhs.type == "identifier" else r_string_value(source, rhs)
    if package is None or name is None:
        return None
    return f"{package}{source.text(operator)}{name}"


@dataclass(frozen=True, slots=True)
class Argument:
    """One argument of an R call or subset, in source order.

    `name` is the decoded argument name (`f(x = 1)`, ``f(`x` = 1)``, `f("x" = 1)`) or None
    for a positional one; `value` is None for an empty slot (`f(a, , b)`) or a name with
    no value (`f(x = )`). `position` counts every slot, empty ones included.
    """

    position: int
    name: str | None
    name_node: Node | None
    value: Node | None
    node: Node | None


def r_arguments(source: Source, node: Node) -> list[Argument]:
    """The arguments of a `call`, `subset` or `subset2` node, empty slots included; [] for any other node."""
    arguments = node.child_by_field_name("arguments")
    if arguments is None:
        return []
    found: list[Argument] = []
    pending: Node | None = None
    position = 0
    seen_any = False
    for child in arguments.children:
        if child.type == "argument":
            pending = child
            seen_any = True
        elif child.type == "comma":
            found.append(_argument(source, position, pending))
            position += 1
            pending = None
            seen_any = True
    if pending is not None or (seen_any and found):
        found.append(_argument(source, position, pending))
    return found


def _argument(source: Source, position: int, node: Node | None) -> Argument:
    if node is None:
        return Argument(position, None, None, None, None)
    name_node = node.child_by_field_name("name")
    name: str | None = None
    if name_node is not None:
        name = r_identifier(source, name_node) if name_node.type == "identifier" else r_string_value(source, name_node)
        if name is None:
            name = source.text(name_node)
    return Argument(position, name, name_node, node.child_by_field_name("value"), node)


def r_argument(arguments: list[Argument], name: str, position: int | None = None) -> Argument | None:
    """The argument called `name`, else the positional one at `position` (counting positional slots only)."""
    named = next((argument for argument in arguments if argument.name == name), None)
    if named is not None or position is None:
        return named
    positional = [argument for argument in arguments if argument.name is None]
    return positional[position] if position < len(positional) else None


@dataclass(frozen=True, slots=True)
class Assignment:
    """An R assignment: `target <- value` (also `=`, `<<-`, and `value -> target`, `->>`).

    `name` is the variable the assignment binds: the target's own name, or for a
    replacement form (`names(x) <- v`, `x$a[1] <- v`) the name at its root, which R
    rebinds too; None when the target binds no name R can see statically.
    """

    node: Node
    operator: str
    target: Node
    value: Node
    name: str | None

    @property
    def is_super(self) -> bool:
        """`<<-` or `->>`, which assigns in an enclosing environment."""
        return self.operator in R_SUPER_ASSIGNMENTS


def r_assignment(source: Source, node: Node) -> Assignment | None:
    """The assignment `node` is, or None for any other node."""
    if node.type != "binary_operator":
        return None
    operator = node.child_by_field_name("operator")
    lhs, rhs = node.child_by_field_name("lhs"), node.child_by_field_name("rhs")
    if operator is None or lhs is None or rhs is None:
        return None
    text = source.text(operator)
    if text not in R_ASSIGNMENTS:
        return None
    target, value = (lhs, rhs) if text in R_LEFT_ASSIGNMENTS else (rhs, lhs)
    return Assignment(node, text, target, value, r_bound_name(source, target))


def r_bound_name(source: Source, target: Node) -> str | None:
    """The variable an assignment target rebinds: `x`, `"x"`, and the root of `f(x, ...)`, `x[i]`, `x$a`, `x@a`."""
    node = r_unwrap(target)
    for _ in range(1000):  # a chain of replacement forms; the bound only guards a pathological file
        if node.type == "identifier":
            return r_identifier(source, node)
        if node.type == "string":
            return r_string_value(source, node)
        if node.type in ("subset", "subset2"):
            inner = node.child_by_field_name("function")
        elif node.type == "extract_operator":
            inner = node.child_by_field_name("lhs")
        elif node.type == "call":
            first = next((argument for argument in r_arguments(source, node) if argument.value is not None), None)
            inner = first.value if first is not None else None
        else:
            return None
        if inner is None:
            return None
        node = r_unwrap(inner)
    return None


def r_operator(source: Source, node: Node) -> str | None:
    """The operator text of a `binary_operator` or `unary_operator` node, else None."""
    if node.type not in ("binary_operator", "unary_operator"):
        return None
    operator = node.child_by_field_name("operator")
    return source.text(operator) if operator is not None else None


def r_number(source: Source, node: Node) -> float | None:
    """The value of a numeric literal (`3`, `4.5`, `1e3`, `0x10`, `2L`), a signed one, or None."""
    sign = 1.0
    node = r_unwrap(node)
    while node.type == "unary_operator":
        operator = r_operator(source, node)
        operand = node.child_by_field_name("rhs")
        if operator not in ("-", "+") or operand is None:
            return None
        sign = -sign if operator == "-" else sign
        node = r_unwrap(operand)
    if node.type not in ("float", "integer"):
        return None
    text = source.text(node).rstrip("L")
    try:
        value = float(int(text, 16)) if text.lower().startswith("0x") else float(text)
    except ValueError:
        return None
    return sign * value


def r_is_lookup(visit: Visit) -> bool:
    """Whether an `identifier` reads a variable or function: not an argument's or a parameter's name, not the
    field after `$` or `@`, not a side of `pkg::name`, and not the plain target of an assignment or a `for`."""
    parent, field = visit.parent, visit.field
    if visit.node.type != "identifier" or parent is None:
        return False
    if parent.type in ("argument", "parameter") and field == "name":
        return False
    if parent.type == "extract_operator" and field == "rhs":
        return False
    if parent.type == "namespace_operator":
        return False
    if parent.type == "for_statement" and field == "variable":
        return False
    if parent.type == "binary_operator":
        operator = parent.child_by_field_name("operator")
        text = operator.type if operator is not None else ""
        if text in R_LEFT_ASSIGNMENTS and field == "lhs":
            return False
        if text in R_ASSIGNMENTS - R_LEFT_ASSIGNMENTS and field == "rhs":
            return False
    return True


def r_bindings(source: Source, root: Node) -> list[tuple[str, Node]]:
    """Every place below `root` that binds a name: an assignment (any of the five operators, replacement forms by
    their root name), a function parameter and a `for` variable; `(name, node)` in source order."""
    found: list[tuple[str, Node]] = []
    for visit in visits(root):
        node = visit.node
        if node.type == "binary_operator":
            assignment = r_assignment(source, node)
            if assignment is not None and assignment.name is not None:
                found.append((assignment.name, node))
        elif node.type == "parameter":
            name = node.child_by_field_name("name")
            text = r_identifier(source, name) if name is not None else None
            if text is not None:
                found.append((text, node))
        elif node.type == "for_statement":
            variable = node.child_by_field_name("variable")
            text = r_identifier(source, variable) if variable is not None else None
            if text is not None:
                found.append((text, node))
    return found


# --- Julia -----------------------------------------------------------------------------------

JL_LITERALS = frozenset({"integer_literal", "float_literal", "boolean_literal", "character_literal"})
"""The Julia grammar's literal node types besides strings."""
JL_STRINGS = frozenset({"string_literal", "prefixed_string_literal", "command_literal", "prefixed_command_literal"})
JL_ASSIGNMENTS = frozenset({"assignment", "compound_assignment_expression"})
_JL_SIMPLE_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "v": "\v",
    "e": "\x1b",
    "\\": "\\",
    '"': '"',
    "'": "'",
    "$": "$",
}
_JL_LINE_BLANKS = " \t"


def jl_string(source: Source, node: Node) -> str | None:
    """The value of a plain `"..."` string literal, or None.

    None for any other node, for a triple-quoted string (Julia dedents it), for a string
    with an interpolation (`"$x"`, whose value exists only at run time) and for one Julia
    would refuse or that holds a raw byte (`\\xff`). Escapes: the single letters,
    `\\$`, octal `\\ooo`, `\\xhh`, `\\uhhhh` and `\\Uhhhhhhhh`, and a backslash before a
    line break, which drops the break and the next line's leading blanks.
    """
    if node.type != "string_literal" or any(child.type == "string_interpolation" for child in node.children):
        return None
    text = source.text(node)
    if text.startswith('"""') or len(text) < 2 or not text.endswith('"'):
        return None
    return _jl_unescape(text[1:-1])


def _jl_unescape(body: str) -> str | None:
    out: list[str] = []
    position = 0
    while position < len(body):
        char = body[position]
        if char != "\\":
            out.append(char)
            position += 1
            continue
        if position + 1 >= len(body):
            return None
        code = body[position + 1]
        if code in _JL_SIMPLE_ESCAPES:
            out.append(_JL_SIMPLE_ESCAPES[code])
            position += 2
            continue
        if code in "\r\n":  # a line continuation: the break and the next line's leading blanks go
            position += 3 if body.startswith("\r\n", position + 1) else 2
            while position < len(body) and body[position] in _JL_LINE_BLANKS:
                position += 1
            continue
        value: int | None
        if code in _OCTAL:
            end = position + 1
            while end < len(body) and end < position + 4 and body[end] in _OCTAL:
                end += 1
            value = int(body[position + 1 : end], 8)
            position = end
            if value > 0x7F:
                return None  # a raw byte, no character
        elif code in "xuU":
            value, position = _r_hex_escape(body, position + 2, {"x": 2, "u": 4, "U": 8}[code], False)
            if value is not None and code == "x" and value > 0x7F:
                return None
        else:
            return None  # Julia: "invalid escape sequence"
        if value is None or value > 0x10FFFF or 0xD800 <= value <= 0xDFFF:
            return None
        out.append(chr(value))
    return "".join(out)


def jl_macro_string(source: Source, node: Node) -> tuple[str, str] | None:
    """`(prefix, text)` of a string macro such as `colorant"#009E73"` (the text between the quotes, unescaped as the
    macro receives it, so `\\"` stays two characters); None for any other node or a computed prefix."""
    if node.type not in ("prefixed_string_literal", "prefixed_command_literal"):
        return None
    prefix = node.child_by_field_name("prefix")
    if prefix is None or prefix.type != "identifier":
        return None
    name = source.text(prefix)
    rest = source.data[prefix.end_byte : node.end_byte].decode("utf-8")
    suffix = node.child_by_field_name("suffix")
    if suffix is not None:
        rest = rest[: len(rest) - len(source.text(suffix))]
    for quote in ('"""', '"', "```", "`"):
        if rest.startswith(quote) and rest.endswith(quote) and len(rest) >= 2 * len(quote):
            return name, rest[len(quote) : len(rest) - len(quote)]
    return None


def jl_unwrap(node: Node) -> Node:
    """`node` without enclosing parentheses: `((x))` is `x`."""
    while node.type == "parenthesized_expression":
        inner = [child for child in node.named_children if child.type not in COMMENTS]
        if len(inner) != 1:
            return node
        node = inner[0]
    return node


def jl_named(node: Node) -> list[Node]:
    """The named children of `node` without comments."""
    return [child for child in node.named_children if child.type not in COMMENTS]


def _jl_member(source: Source, node: Node) -> str | None:
    """The member name after a `.`: `name`, or an operator quoted as `:+` (`Base.:+`)."""
    if node.type == "identifier":
        return source.text(node)
    if node.type == "quote_expression":
        inner = jl_named(node)
        if len(inner) == 1 and inner[0].type in ("identifier", "operator"):
            return source.text(inner[0])
    return None


def jl_dotted(source: Source, node: Node) -> str | None:
    """`name` or `Module.Sub.name` for an identifier or a chain of fields over names; None for anything else."""
    parts: list[str] = []
    for _ in range(1000):  # a chain of fields; the bound only guards a pathological file
        if node.type != "field_expression":
            break
        named = jl_named(node)
        if len(named) != 2:
            return None
        member = _jl_member(source, named[1])
        if member is None:
            return None
        parts.append(member)
        node = named[0]
    if node.type != "identifier":
        return None
    parts.append(source.text(node))
    return ".".join(reversed(parts))


def jl_root(node: Node) -> Node:
    """The value a chain of fields, indexes and calls starts from: `x` in `x.a[1].b`."""
    for _ in range(1000):
        if node.type in ("field_expression", "index_expression", "call_expression", "broadcast_call_expression"):
            named = jl_named(node)
            if not named:
                return node
            node = named[0]
        elif node.type in ("parenthesized_expression", "typed_expression"):
            named = jl_named(node)
            if not named:
                return node
            node = named[0]
        else:
            return node
    return node


def jl_callee(source: Source, call: Node) -> str | None:
    """The function a `call_expression` or `broadcast_call_expression` names: `f`, `Module.f` or an operator (`-`);
    None for any other callee (a call, an index, a parenthesised value)."""
    if call.type not in ("call_expression", "broadcast_call_expression") or not call.children:
        return None
    function = call.children[0]
    if function.type == "operator":
        return source.text(function)
    return jl_dotted(source, function)


def jl_macro_name(source: Source, node: Node) -> str | None:
    """`@name` or `Module.@name` of a `macrocall_expression`; None for any other node."""
    if node.type != "macrocall_expression" or not node.children:
        return None
    head = node.children[0]
    if head.type == "macro_identifier":
        return source.text(head)
    if head.type == "field_expression":
        named = jl_named(head)
        if len(named) == 2 and named[1].type == "macro_identifier":
            module = jl_dotted(source, named[0])
            return f"{module}.{source.text(named[1])}" if module is not None else None
    return None


@dataclass(frozen=True, slots=True)
class JlArgument:
    """One argument of a Julia call, in source order.

    `position` counts the positional arguments only (None for a keyword); `name` is a
    keyword's name (`f(x; k = 1)`, `f(x, k = 1)`, and `f(; k)`, which passes the variable
    `k` as `k = k`); `splat` marks `xs...`.
    """

    position: int | None
    name: str | None
    value: Node
    node: Node
    splat: bool


def jl_argument_list(call: Node) -> Node | None:
    """The `argument_list` of a call, broadcast call or macro call, else None."""
    return next((child for child in call.children if child.type in ("argument_list", "macro_argument_list")), None)


def jl_arguments(source: Source, call: Node) -> list[JlArgument]:
    """The arguments of a call's parentheses (a `do` block is not among them); [] for any other node."""
    arguments = jl_argument_list(call)
    if arguments is None:
        return []
    found: list[JlArgument] = []
    keywords = False
    position = 0
    for child in arguments.children:
        if child.type == ";":
            keywords = True
            continue
        if not child.is_named or child.type in COMMENTS:
            continue
        splat = child.type == "splat_expression"
        if child.type == "assignment" and arguments.type == "argument_list":
            named = jl_named(child)
            if len(named) >= 2 and named[0].type == "identifier":
                found.append(JlArgument(None, source.text(named[0]), named[-1], child, False))
                continue
        if keywords and child.type == "identifier":
            found.append(JlArgument(None, source.text(child), child, child, False))
            continue
        if keywords:
            found.append(JlArgument(None, None, child, child, splat))
            continue
        found.append(JlArgument(position, None, child, child, splat))
        position += 1
    return found


def jl_argument(arguments: list[JlArgument], name: str, position: int | None = None) -> JlArgument | None:
    """The keyword argument `name`, else the positional one at `position`."""
    named = next((argument for argument in arguments if argument.name == name), None)
    if named is not None or position is None:
        return named
    return next((argument for argument in arguments if argument.position == position), None)


@dataclass(frozen=True, slots=True)
class JlAssignment:
    """A Julia assignment (`x = v`, `x += v`, `x .= v`, `const x = v`, `f(x) = body`).

    `names` are the variables it binds: the target's names (`a, b = ...` binds both, `x::T
    = v` binds `x`); for a store into a value (`x[1] = v`, `x.a = v`, `x .= v`) the name at
    its root, which the store changes (`mutation`); for a short function definition
    (`f(x) = ...`) the function's name (`function`).
    """

    node: Node
    operator: str
    target: Node
    value: Node
    names: tuple[str, ...]
    mutation: bool
    function: bool


def jl_assignment(source: Source, node: Node) -> JlAssignment | None:
    """The assignment `node` is, or None for any other node."""
    if node.type not in JL_ASSIGNMENTS:
        return None
    named = jl_named(node)
    operator = next((child for child in named if child.type == "operator"), None)
    if len(named) < 3 or operator is None:
        return None
    target, value = named[0], named[-1]
    text = source.text(operator)
    names, kind = _jl_target(source, target)
    mutation = kind == "mutation" or (node.type == "compound_assignment_expression" and text.startswith("."))
    return JlAssignment(node, text, target, value, tuple(names), mutation, kind == "function")


def _jl_target(source: Source, target: Node) -> tuple[list[str], str]:
    """The names an assignment target binds and how: `bind`, `mutation` (a store into a value) or `function`."""
    node = jl_unwrap(target)
    kind = node.type
    if kind == "identifier":
        return [source.text(node)], "bind"
    if kind == "typed_expression":
        named = jl_named(node)
        return _jl_target(source, named[0]) if named else ([], "bind")
    if kind in ("open_tuple", "tuple_expression"):
        names: list[str] = []
        for item in jl_named(node):
            if item.type == "assignment":  # `(; a = b) = ...` is not valid; a named tuple element binds nothing
                continue
            names += _jl_target(source, item)[0]
        return names, "bind"
    if kind == "splat_expression":
        named = jl_named(node)
        return _jl_target(source, named[0]) if named else ([], "bind")
    if kind in ("index_expression", "field_expression"):
        root = jl_root(node)
        return ([source.text(root)] if root.type == "identifier" else []), "mutation"
    if kind == "where_expression":
        named = jl_named(node)
        return _jl_target(source, named[0]) if named else ([], "function")
    if kind == "call_expression":
        name = jl_callee(source, node)
        return ([name] if name is not None else []), "function"
    return [], "bind"


def jl_parameters(source: Source, node: Node) -> list[tuple[str, Node]]:
    """The parameters a function form binds: a `function` definition, a short definition (`f(x) = ...`), an arrow
    function (`x -> ...`, `(a, b) -> ...`) or a `do` block (`do a, b`); [] for any other node."""
    if node.type == "function_definition":
        signature = next((child for child in node.named_children if child.type == "signature"), None)
        head = jl_named(signature)[0] if signature is not None and jl_named(signature) else None
        while head is not None and head.type in ("where_expression", "typed_expression"):
            inner = jl_named(head)
            head = inner[0] if inner else None
        if head is None:
            return []
        if head.type == "call_expression":
            head = jl_argument_list(head)
        return _jl_parameter_names(source, head) if head is not None else []
    if node.type in JL_ASSIGNMENTS:
        assignment = jl_assignment(source, node)
        if assignment is None or not assignment.function:
            return []
        head = jl_unwrap(assignment.target)
        while head.type in ("where_expression", "typed_expression"):
            inner = jl_named(head)
            if not inner:
                return []
            head = inner[0]
        arguments = jl_argument_list(head) if head.type == "call_expression" else None
        return _jl_parameter_names(source, arguments) if arguments is not None else []
    if node.type == "arrow_function_expression":
        named = jl_named(node)
        return _jl_parameter_names(source, named[0]) if named else []
    if node.type == "do_clause":
        found: list[tuple[str, Node]] = []
        for child in jl_named(node):
            if child.type == "block":
                break
            found += _jl_parameter_names(source, child)
        return found
    return []


def _jl_parameter_names(source: Source, node: Node) -> list[tuple[str, Node]]:
    """The names a parameter or a list of them binds: `x`, `x::T`, `x = 1`, `xs...`, `(a, b)` and `; k = 1`."""
    found: list[tuple[str, Node]] = []
    stack = [node]
    while stack:
        current = jl_unwrap(stack.pop())
        kind = current.type
        if kind == "identifier":
            found.append((source.text(current), current))
        elif kind in ("argument_list", "tuple_expression", "open_tuple"):
            stack.extend(reversed(jl_named(current)))
        elif kind in ("typed_expression", "splat_expression", "assignment"):
            named = jl_named(current)
            if named and not (kind == "typed_expression" and source.text(current).startswith("::")):
                stack.append(named[0])
    return found


def jl_bindings(source: Source, root: Node) -> list[tuple[str, Node]]:
    """Every place below `root` that binds a name, `(name, node)` in source order: an assignment (stores into a
    value by their root name, short function definitions by the function's name), a compound assignment, a function,
    macro, type or module definition, a parameter, a loop, comprehension, `let` or `catch` variable, `global x` and
    `local x`, and a name `using X: y` or `import` brings in.

    A keyword argument (`f(k = 1)`) and a named tuple's field (`(a = 1,)`) bind nothing.
    """
    found: list[tuple[str, Node]] = []
    for visit in visits(root):
        node, parent = visit.node, visit.parent
        kind = node.type
        if kind in JL_ASSIGNMENTS:
            if parent is not None and parent.type in ("argument_list", "tuple_expression", "macro_argument_list"):
                continue  # a keyword argument, a named tuple's field, a parameter's default (below)
            assignment = jl_assignment(source, node)
            if assignment is not None:
                found += [(name, node) for name in assignment.names]
                found += jl_parameters(source, node)
        elif kind == "function_definition":
            signature = next((child for child in node.named_children if child.type == "signature"), None)
            head = jl_named(signature)[0] if signature is not None and jl_named(signature) else None
            while head is not None and head.type in ("where_expression", "typed_expression"):
                inner = jl_named(head)
                head = inner[0] if inner else None
            name = jl_callee(source, head) if head is not None and head.type == "call_expression" else None
            if name is not None:
                found.append((name, node))
            found += jl_parameters(source, node)
        elif kind in ("arrow_function_expression", "do_clause"):
            found += jl_parameters(source, node)
        elif kind == "for_binding":
            named = jl_named(node)
            if named:
                found += [(name, node) for name in _jl_target(source, named[0])[0]]
        elif kind == "catch_clause":
            named = jl_named(node)
            if named and named[0].type == "identifier":
                found.append((source.text(named[0]), node))
        elif kind in ("global_statement", "local_statement"):
            found += [(source.text(child), node) for child in jl_named(node) if child.type == "identifier"]
        elif kind in ("struct_definition", "abstract_definition", "primitive_definition"):
            head = next((child for child in node.named_children if child.type == "type_head"), None)
            first = jl_root(jl_named(head)[0]) if head is not None and jl_named(head) else None
            while first is not None and first.type in ("binary_expression", "parametrized_type_expression"):
                first = jl_named(first)[0] if jl_named(first) else None
            if first is not None and first.type == "identifier":
                found.append((source.text(first), node))
        elif kind in ("macro_definition", "module_definition"):
            for child in jl_named(node):
                target = child
                if target.type == "signature":
                    inner = jl_named(target)
                    target = inner[0] if inner else target
                if target.type == "call_expression":
                    callee = jl_callee(source, target)
                    if callee is not None:
                        found.append((callee, node))
                    break
                if target.type == "identifier":
                    found.append((source.text(target), node))
                    break
        elif kind == "selected_import":
            found += [(source.text(child), node) for child in jl_named(node)[1:] if child.type == "identifier"]
        elif kind == "import_alias":
            named = jl_named(node)
            if named and named[-1].type == "identifier":
                found.append((source.text(named[-1]), node))
        elif kind in ("using_statement", "import_statement"):
            for child in jl_named(node):
                if child.type == "identifier":
                    found.append((source.text(child), node))
                elif child.type == "import_path":
                    parts = [part for part in jl_named(child) if part.type == "identifier"]
                    if parts:
                        found.append((source.text(parts[-1]), node))
    return found


def jl_number(source: Source, node: Node) -> float | None:
    """The value of a numeric literal (`3`, `4.5`, `1e3`, `1.5f0`, `0x10`, `1_000`), a signed one, or None."""
    sign = 1.0
    node = jl_unwrap(node)
    while node.type == "unary_expression":
        named = jl_named(node)
        operator = next((child for child in node.children if child.type == "operator"), None)
        text = source.text(operator) if operator is not None else ""
        if text not in ("-", "+") or len(named) != 2:
            return None
        sign = -sign if text == "-" else sign
        node = jl_unwrap(named[-1])
    text = source.text(node).replace("_", "")
    try:
        if node.type == "integer_literal":
            return sign * float(int(text, 0))
        if node.type == "float_literal":
            if text.lower().startswith("0x"):
                return sign * float.fromhex(text)
            return sign * float(text.replace("f", "e"))
    except ValueError, OverflowError:  # past Python's 4,300 digits, or an integer or hex float past a double
        return None
    return None


# --- JavaScript ------------------------------------------------------------------------------

JS_LITERALS = frozenset({"number", "true", "false", "null", "undefined"})
"""The JavaScript grammar's literal node types besides strings, templates and regular expressions."""
JS_STRINGS = frozenset({"string", "template_string"})
JS_FUNCTIONS = frozenset(
    {
        "function_declaration",
        "function_expression",
        "generator_function_declaration",
        "generator_function",
        "arrow_function",
        "method_definition",
    }
)
"""The nodes that open a function scope: their parameters, and every `var` inside them, are theirs."""
JS_BLOCKS = frozenset({"program", "statement_block", "switch_body", "class_static_block"})
"""The nodes that open a block scope for `let`, `const`, classes and function declarations."""
JS_TYPE_NODES = frozenset(
    {
        "type_annotation",
        "type_arguments",
        "type_parameters",
        "type_alias_declaration",
        "interface_declaration",
        "implements_clause",
        "type_query",
        "type_predicate_annotation",
        "asserts_annotation",
        "opting_type_annotation",
        "omitting_type_annotation",
        "adding_type_annotation",
        "abstract_method_signature",
        "function_signature",
        "index_signature",
    }
)
"""TSX nodes that hold types only: TypeScript erases them, so nothing in them runs or reads a value."""
JS_TYPE_WRAPPERS = frozenset(
    {"as_expression", "satisfies_expression", "non_null_expression", "instantiation_expression"}
)
"""TSX expressions whose value is their first child's: `x as T`, `x satisfies T`, `x!`, `f<T>`."""
_JS_SIMPLE_ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v"}
JS_LINE_SEPARATORS = (chr(0x2028), chr(0x2029))
"""U+2028 and U+2029, which end a line in JavaScript as `\\n` and `\\r` do (written by number: they are invisible)."""
_JS_LINE_BREAKS = ("\r\n", "\n", "\r", *JS_LINE_SEPARATORS)


def js_string(source: Source, node: Node) -> str | None:
    """The value of a `string` node or of a `template_string` without a substitution, else None.

    Escapes: the single letters, `\\0`, `\\xhh`, `\\uhhhh`, `\\u{h...}` (a surrogate pair
    joins into one character), a backslash before a line break (which drops both), and any
    other character escaping itself. A legacy octal escape (`\\101`, a syntax error in a
    module and in a template), `\\8`, `\\9` and a lone surrogate give None. A template's
    line breaks read as `\\n`, as JavaScript cooks them.
    """
    if node.type == "template_string":
        if any(child.type == "template_substitution" for child in node.children):
            return None
        text = source.text(node)
        if len(text) < 2 or not text.startswith("`") or not text.endswith("`"):
            return None
        return _js_unescape(text[1:-1].replace("\r\n", "\n").replace("\r", "\n"))
    if node.type != "string":
        return None
    text = source.text(node)
    if len(text) < 2 or text[0] not in "\"'" or text[-1] != text[0]:
        return None
    return _js_unescape(text[1:-1])


def _js_unescape(body: str) -> str | None:
    out: list[str] = []
    position = 0
    while position < len(body):
        char = body[position]
        if char != "\\":
            out.append(char)
            position += 1
            continue
        if position + 1 >= len(body):
            return None
        code = body[position + 1]
        if code in _JS_SIMPLE_ESCAPES:
            out.append(_JS_SIMPLE_ESCAPES[code])
            position += 2
            continue
        breaks = next((mark for mark in _JS_LINE_BREAKS if body.startswith(mark, position + 1)), None)
        if breaks is not None:  # a line continuation: the backslash and the break go
            position += 1 + len(breaks)
            continue
        if code == "0" and not (position + 2 < len(body) and body[position + 2].isdigit()):
            out.append("\x00")
            position += 2
            continue
        if code.isdigit():
            return None  # a legacy octal escape, `\8` or `\9`
        if code == "x":
            digits = body[position + 2 : position + 4]
            if len(digits) != 2 or any(digit not in _HEX for digit in digits):
                return None
            out.append(chr(int(digits, 16)))
            position += 4
            continue
        if code == "u":
            value, position = _js_unicode_escape(body, position + 2)
            if value is None:
                return None
            out.append(chr(value))
            continue
        out.append(code)  # an identity escape: `\"`, `\'`, `\\`, `` \` ``, `\$`, `\q`
        position += 2
    text = "".join(out)
    try:  # join surrogate pairs (two escapes for one emoji); a lone surrogate is no text
        return text.encode("utf-16-le", "surrogatepass").decode("utf-16-le")
    except UnicodeDecodeError:
        return None


def _js_unicode_escape(body: str, start: int) -> tuple[int | None, int]:
    """The code unit or code point of a `\\uhhhh` or `\\u{h...}` escape whose digits start at `start`, and the offset
    after it."""
    if start < len(body) and body[start] == "{":
        end = body.find("}", start)
        digits = body[start + 1 : end] if end != -1 else ""
        if not digits or len(digits) > 8 or any(char not in _HEX for char in digits):
            return None, start
        value = int(digits, 16)
        return (value if value <= 0x10FFFF else None), end + 1
    digits = body[start : start + 4]
    if len(digits) != 4 or any(char not in _HEX for char in digits):
        return None, start
    return int(digits, 16), start + 4


def js_unwrap(node: Node) -> Node:
    """`node` without enclosing parentheses and TSX's type wrappers: `((x as T)!)` is `x`."""
    for _ in range(1000):  # nested wrappers; the bound only guards a pathological file
        if node.type == "parenthesized_expression" or node.type in JS_TYPE_WRAPPERS:
            inner = [child for child in node.named_children if child.type not in COMMENTS]
            if not inner or (node.type == "parenthesized_expression" and len(inner) != 1):
                return node
            node = inner[0]
        else:
            return node
    return node


def js_named(node: Node) -> list[Node]:
    """The named children of `node` without comments."""
    return [child for child in node.named_children if child.type not in COMMENTS]


def js_property(source: Source, node: Node) -> str | None:
    """The property a `member_expression` reads (`a.b` and `a?.b`: `b`), or a `subscript_expression` whose index is a
    string or a template without a substitution (`a["b"]`, `` a[`b`] ``); None for any other node or index."""
    if node.type == "member_expression":
        prop = node.child_by_field_name("property")
        return source.text(prop) if prop is not None and prop.type == "property_identifier" else None
    if node.type == "subscript_expression":
        index = node.child_by_field_name("index")
        return js_string(source, js_unwrap(index)) if index is not None else None
    return None


def js_object(node: Node) -> Node | None:
    """The object a `member_expression` or `subscript_expression` reads from, else None."""
    if node.type not in ("member_expression", "subscript_expression"):
        return None
    return node.child_by_field_name("object")


def js_dotted(source: Source, node: Node) -> str | None:
    """`name` or `a.b.c` for an identifier or a chain of plain member accesses over one (`?.` reads as `.`); None for
    anything else (a call, a computed index, `this`)."""
    parts: list[str] = []
    node = js_unwrap(node)
    for _ in range(1000):  # a chain of members; the bound only guards a pathological file
        if node.type != "member_expression":
            break
        prop = node.child_by_field_name("property")
        inner = node.child_by_field_name("object")
        if prop is None or prop.type != "property_identifier" or inner is None:
            return None
        parts.append(source.text(prop))
        node = js_unwrap(inner)
    if node.type != "identifier":
        return None
    parts.append(source.text(node))
    return ".".join(reversed(parts))


def js_root(node: Node) -> Node:
    """The value a chain of members, indexes and calls starts from: `x` in `x.a[1].b()`."""
    for _ in range(1000):
        node = js_unwrap(node)
        if node.type in ("member_expression", "subscript_expression"):
            inner = node.child_by_field_name("object")
        elif node.type == "call_expression":
            inner = node.child_by_field_name("function")
        else:
            return node
        if inner is None:
            return node
        node = inner
    return node


def js_callee(source: Source, call: Node) -> str | None:
    """The function a `call_expression` or `new_expression` names: `f`, `d3.scaleLinear` or `import`; None for any
    other callee (a call's result, a computed member, a function literal)."""
    if call.type == "call_expression":
        function = call.child_by_field_name("function")
    elif call.type == "new_expression":
        function = call.child_by_field_name("constructor")
    else:
        return None
    if function is None:
        return None
    if function.type == "import":
        return "import"
    return js_dotted(source, function)


def js_arguments(call: Node) -> list[Node]:
    """The argument expressions of a call or `new` in source order (a spread as its `spread_element`); [] without an
    argument list (`new Foo`, a tagged template)."""
    arguments = call.child_by_field_name("arguments")
    if arguments is None or arguments.type != "arguments":
        return []
    return js_named(arguments)


def js_number(source: Source, node: Node) -> float | None:
    """The value of a numeric literal (`3`, `4.5`, `1e3`, `0x10`, `0b1`, `0o7`, `1_000`, `10n`), a signed one, or
    None; never raises (a literal past a double is None)."""
    sign = 1.0
    node = js_unwrap(node)
    for _ in range(1000):  # a chain of signs; the bound only guards a pathological file
        if node.type != "unary_expression":
            break
        operator = node.child_by_field_name("operator")
        argument = node.child_by_field_name("argument")
        text = source.text(operator) if operator is not None else ""
        if text not in ("-", "+") or argument is None:
            return None
        sign = -sign if text == "-" else sign
        node = js_unwrap(argument)
    if node.type != "number":
        return None
    text = source.text(node).replace("_", "").lower()
    try:
        if text.endswith("n"):
            return sign * float(int(text[:-1], 0))
        if text.startswith(("0x", "0b", "0o")):
            return sign * float(int(text, 0))
        if len(text) > 1 and text[0] == "0" and text.isdigit():
            return sign * float(int(text, 8 if set(text) <= set("01234567") else 10))  # legacy octal `017`
        value = float(text)
    except ValueError, OverflowError:  # past Python's 4,300 digits, or an integer past a double
        return None
    return sign * value if math.isfinite(value) else None


@dataclass(frozen=True, slots=True)
class JsBinding:
    """One name a JavaScript file binds: the node that names it, the node whose range it is visible in, and how.

    `kind` is `var`, `let`, `const`, `using`, `function`, `class`, `parameter`, `catch`,
    `import`, `enum` or `namespace`; `declaration` is the statement or declarator it comes
    from (a `variable_declarator`, a function, an `import_statement`, ...).
    """

    name: str
    node: Node
    scope: Node
    kind: str
    declaration: Node

    def visible_at(self, node: Node) -> bool:
        """Whether `node` lies in this binding's scope."""
        return self.scope.start_byte <= node.start_byte < self.scope.end_byte


def js_scope(node: Node, kinds: frozenset[str]) -> Node:
    """The nearest ancestor of `node` among `kinds`, or the root."""
    current = node.parent
    while current is not None:
        if current.type in kinds:
            return current
        if current.parent is None:
            return current
        current = current.parent
    return node


def js_pattern_names(source: Source, pattern: Node) -> list[Node]:
    """The nodes that name the variables a binding pattern binds: `x`, `{ a, b: c, d = 1, ...e }`, `[f, , g = 2,
    ...h]` and TSX's typed parameters; a default value binds nothing."""
    found: list[Node] = []
    stack = [pattern]
    while stack:
        node = stack.pop()
        kind = node.type
        if kind in ("identifier", "shorthand_property_identifier_pattern"):
            found.append(node)
        elif kind in ("object_pattern", "array_pattern"):
            stack.extend(reversed(js_named(node)))
        elif kind == "pair_pattern":
            value = node.child_by_field_name("value")
            if value is not None:
                stack.append(value)
        elif kind in ("assignment_pattern", "object_assignment_pattern"):
            left = node.child_by_field_name("left")
            if left is not None:
                stack.append(left)
        elif kind == "rest_pattern":
            stack.extend(child for child in js_named(node) if child.type not in JS_TYPE_NODES)
        elif kind in ("required_parameter", "optional_parameter"):
            inner = node.child_by_field_name("pattern")
            if inner is not None:
                stack.append(inner)
    return found


def js_bindings(source: Source, root: Node) -> list[JsBinding]:
    """Every name bound below `root`, in source order (module docstring, "JavaScript").

    `var` is visible in its function (or the program), `let`, `const`, `using`, a class and a
    function declaration in their block (a function declaration in a block as in strict
    code, the smaller of the two scopes a script may give it), a parameter in its function,
    a `catch` parameter in its clause, a `for` head's `let` or `const` in its loop, an
    import in the program, and the name of a function or class expression inside itself.
    """
    found: list[JsBinding] = []

    def add(names: list[Node], scope: Node, kind: str, declaration: Node) -> None:
        found.extend(JsBinding(source.text(name), name, scope, kind, declaration) for name in names)

    for node in walk(root):
        kind = node.type
        if kind == "variable_declarator":
            name = node.child_by_field_name("name")
            declaration = node.parent
            if name is None or declaration is None:
                continue
            if declaration.type == "variable_declaration":
                add(js_pattern_names(source, name), js_scope(node, JS_FUNCTIONS | {"program"}), "var", node)
            else:
                word = _js_declaration_kind(source, declaration)
                holder = declaration.parent
                scope = holder if holder is not None and holder.type == "for_statement" else js_scope(node, JS_BLOCKS)
                add(js_pattern_names(source, name), scope, word, node)
        elif kind == "for_in_statement":
            left = node.child_by_field_name("left")
            head = node.child_by_field_name("kind")
            if left is None or head is None:
                continue  # `for (x of xs)` assigns a name bound elsewhere
            head_kind = source.text(head)
            scope = js_scope(node, JS_FUNCTIONS | {"program"}) if head_kind == "var" else node
            add(js_pattern_names(source, left), scope, head_kind, node)
        elif kind in ("function_declaration", "generator_function_declaration"):
            name = node.child_by_field_name("name")
            if name is not None:
                add([name], js_scope(node, JS_BLOCKS), "function", node)
            add(_js_parameters(source, node), node, "parameter", node)
        elif kind in ("function_expression", "generator_function"):
            name = node.child_by_field_name("name")
            if name is not None:
                add([name], node, "function", node)
            add(_js_parameters(source, node), node, "parameter", node)
        elif kind in ("arrow_function", "method_definition"):
            add(_js_parameters(source, node), node, "parameter", node)
        elif kind in ("class_declaration", "abstract_class_declaration"):
            name = node.child_by_field_name("name")
            if name is not None:
                add([name], js_scope(node, JS_BLOCKS), "class", node)
        elif kind == "class":
            name = node.child_by_field_name("name")
            if name is not None:
                add([name], node, "class", node)
        elif kind == "catch_clause":
            parameter = node.child_by_field_name("parameter")
            if parameter is not None:
                add(js_pattern_names(source, parameter), node, "catch", node)
        elif kind == "import_statement":
            add(_js_import_names(node), js_scope(node, frozenset({"program"})), "import", node)
        elif kind in ("enum_declaration", "internal_module", "module"):
            name = node.child_by_field_name("name")
            if name is not None and name.type == "identifier":
                add([name], js_scope(node, JS_BLOCKS), "enum" if kind == "enum_declaration" else "namespace", node)
    return found


def _js_declaration_kind(source: Source, declaration: Node) -> str:
    """`let`, `const` or `using` of a `lexical_declaration` or `using_declaration`."""
    word = declaration.child_by_field_name("kind")
    if word is not None:
        return source.text(word)
    first = declaration.children[0] if declaration.children else None
    return source.text(first) if first is not None and not first.is_named else "let"


def _js_parameters(source: Source, function: Node) -> list[Node]:
    """The names a function's parameters bind: `formal_parameters`, or an arrow function's single `parameter`."""
    parameters = function.child_by_field_name("parameters")
    if parameters is not None:
        return [name for child in js_named(parameters) for name in js_pattern_names(source, child)]
    single = function.child_by_field_name("parameter")
    return js_pattern_names(source, single) if single is not None else []


def _js_import_names(statement: Node) -> list[Node]:
    """The local names an `import` binds: the default name, `* as name`, and each `{ a }` or `{ a as b }`."""
    found: list[Node] = []
    for clause in js_named(statement):
        if clause.type == "import_require_clause":  # TSX's `import x = require("y")`
            found += [child for child in js_named(clause)[:1] if child.type == "identifier"]
            continue
        if clause.type != "import_clause":
            continue
        for part in js_named(clause):
            if part.type == "identifier":
                found.append(part)
            elif part.type == "namespace_import":
                found += [child for child in js_named(part) if child.type == "identifier"]
            elif part.type == "named_imports":
                for specifier in js_named(part):
                    if specifier.type != "import_specifier":
                        continue
                    alias = specifier.child_by_field_name("alias")
                    name = alias if alias is not None else specifier.child_by_field_name("name")
                    if name is not None and name.type == "identifier":
                        found.append(name)
    return found


def js_is_reference(visit: Visit) -> bool:
    """Whether an `identifier` or `shorthand_property_identifier` reads (or assigns) a variable: not a name a
    declaration, parameter or import binds (`js_bindings`), not an imported or exported name under an alias, and not a
    lowercase JSX tag, which names an HTML or SVG element.

    The caller skips type positions (`JS_TYPE_NODES`) and the bindings themselves.
    """
    node, parent, field = visit.node, visit.parent, visit.field
    if node.type == "shorthand_property_identifier":
        return True  # `{ a }` reads `a`
    if node.type != "identifier" or parent is None:
        return False
    ptype = parent.type
    if ptype == "import_specifier":
        return False  # bound (`alias`, or the name without one) or the module's export name
    if ptype == "export_specifier":
        return field == "name"  # `export { a as b }` reads `a`
    if ptype in ("jsx_opening_element", "jsx_closing_element", "jsx_self_closing_element") and field == "name":
        text = node.text.decode("utf-8") if node.text is not None else ""
        return text[:1].isupper() or text[:1] in ("_", "$")
    if ptype in ("jsx_namespace_name", "namespace_export", "nested_identifier"):
        return False
    return ptype != "meta_property"


@dataclass(frozen=True, slots=True)
class JsReference:
    """An identifier that reads or assigns a variable: its name, the visit that met it, and the binding it resolves to,
    the one with the innermost scope around it; None for a free name, which the page's global object resolves."""

    name: str
    visit: Visit
    binding: JsBinding | None

    @property
    def bound(self) -> bool:
        return self.binding is not None


def js_resolve(bindings: list[JsBinding], node: Node) -> JsBinding | None:
    """The binding among `bindings` (of one name) that `node` reads: the innermost scope around it, else None."""
    visible = [binding for binding in bindings if binding.visible_at(node)]
    if not visible:
        return None
    return max(visible, key=lambda binding: (binding.scope.start_byte, -binding.scope.end_byte))


def js_references(source: Source, root: Node, bindings: list[JsBinding] | None = None) -> list[JsReference]:
    """Every reference below `root` in source order, type positions skipped (`js_is_reference`)."""
    bindings = js_bindings(source, root) if bindings is None else bindings
    binding_ids = {binding.node.id for binding in bindings}
    by_name: dict[str, list[JsBinding]] = {}
    for binding in bindings:
        by_name.setdefault(binding.name, []).append(binding)
    found: list[JsReference] = []
    stack: list[Visit] = [Visit(root, None, None)]
    while stack:
        visit = stack.pop()
        node = visit.node
        if node.type in JS_TYPE_NODES:
            continue
        if node.id not in binding_ids and node.type in ("identifier", "shorthand_property_identifier"):
            if js_is_reference(visit):
                name = source.text(node)
                found.append(JsReference(name, visit, js_resolve(by_name.get(name, []), node)))
        children = node.children
        named_seen = 0
        pushed: list[Visit] = []
        for index, child in enumerate(children):
            if node.type in JS_TYPE_WRAPPERS and child.is_named and child.type not in COMMENTS:
                named_seen += 1
                if named_seen > 1:
                    continue  # the type after `as`, `satisfies` or the arguments of `f<T>`
            pushed.append(Visit(child, node, node.field_name_for_child(index)))
        stack.extend(reversed(pushed))
    return found
