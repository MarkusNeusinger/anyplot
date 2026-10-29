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

This module imports only the standard library and tree-sitter (2026-10-29): the R region
and readiness detection built on it is meant to move to `core/` later, so the regen
gate's adapt route can run the same R checks as the agent.

A point's `.row` and `.column` are never read (`first_line`, `last_line` and `column`
index the point instead). Under Python 3.14 the attribute getters of tree-sitter
0.26.0's `Point` hand out an int it does not own: `node.start_point.row` past 256 (the
interpreter's cached small ints) frees the int while it is in use, and the process
segfaults at the next garbage collection (found on 2026-10-29 with the catalogue's
line 271; `point[0]` is safe). A test refuses the attribute form in this package.
"""

import bisect
import functools
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

import tree_sitter_language_pack
from tree_sitter import Language, Node, Parser, Tree


TREE_SITTER_VERSION = "0.26.0"
LANGUAGE_PACK_VERSION = "0.13.0"
"""The pinned versions (`pyproject.toml`, the `agents` extra); a test compares them with the installed ones."""

Grammar = Literal["r"]
GRAMMARS: tuple[Grammar, ...] = ("r",)
"""The grammars this code reads; JavaScript and Julia join with their steps of the plan."""

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
    return [child for child in root.named_children if child.type != "comment"]


def comments(root: Node) -> list[Node]:
    """Every comment node, in source order."""
    return [node for node in walk(root) if node.type == "comment"]


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
