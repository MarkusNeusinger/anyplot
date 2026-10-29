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

This module imports only the standard library and tree-sitter (2026-10-29): the R and
Julia region and readiness detection built on it is meant to move to `core/` later, so
the regen gate's adapt route can run the same checks as the agent.

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

Grammar = Literal["r", "julia"]
GRAMMARS: tuple[Grammar, ...] = ("r", "julia")
"""The grammars this code reads; JavaScript joins with its step of the plan."""
COMMENTS = frozenset({"comment", "line_comment", "block_comment"})
"""The comment node types: R's `comment`, Julia's `line_comment` (`# ...`) and `block_comment` (`#= ... =#`)."""

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
