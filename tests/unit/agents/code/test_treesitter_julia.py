"""Tests for the Julia helpers of agents/anyplot/code/treesitter.py: the catalogue parse, strings, names, calls,
assignments and bindings."""

import pytest
from tree_sitter import Node

from agents.anyplot.code.treesitter import (
    Source,
    jl_argument,
    jl_arguments,
    jl_assignment,
    jl_bindings,
    jl_callee,
    jl_dotted,
    jl_macro_name,
    jl_macro_string,
    jl_number,
    jl_string,
    parse,
    statements,
    syntax_problems,
    walk,
)

from .conftest import JULIA_CATALOGUE_FILES


def first(source: Source, kind: str) -> Node:
    return next(node for node in walk(source.root) if node.type == kind)


def test_the_catalogue_has_325_makie_files() -> None:
    assert len(JULIA_CATALOGUE_FILES) == 325


@pytest.mark.parametrize("path", JULIA_CATALOGUE_FILES, ids=lambda path: path.parts[-4])
def test_every_catalogue_makie_file_parses_without_error_or_missing_nodes(path) -> None:
    """The gate of the plan's step 5: tree-sitter-julia of the pinned pack reads all 325 Makie files."""
    tree = parse(path.read_text(encoding="utf-8"), "julia")

    assert syntax_problems(tree) == []
    assert not any(node.is_error or node.is_missing for node in walk(tree.root_node))


def test_comments_are_no_statements() -> None:
    source = Source("# a line comment\n#= a block\ncomment =#\nx = 1\n", "julia")

    assert [source.text(node) for node in statements(source.root)] == ["x = 1"]


@pytest.mark.parametrize(
    ("literal", "value"),
    [
        ('"plain"', "plain"),
        ('"a\\$b"', "a$b"),
        ('"q\\"uote \\\\ back"', 'q"uote \\ back'),
        ('"tab\\tnew\\nline"', "tab\tnew\nline"),
        ('"\\u00e9\\x41\\101"', "éAA"),
        ('"Zürich · 3 °C"', "Zürich · 3 °C"),
        ('"one \\\n    two"', "one two"),
        ('""', ""),
    ],
)
def test_julia_strings_decode_to_their_value(literal: str, value: str) -> None:
    source = Source(f"x = {literal}\n", "julia")

    assert jl_string(source, first(source, "string_literal")) == value


@pytest.mark.parametrize(
    "literal", ['"a $b"', '"a $(f(x))"', '"""triple"""', '"\\xff"', '"\\q"', '"\\777"', '"\\ud800"']
)
def test_strings_without_a_static_value_decode_to_none(literal: str) -> None:
    """An interpolation exists only at run time, a triple-quoted string is dedented, a raw byte is no character."""
    source = Source(f"x = {literal}\n", "julia")

    assert jl_string(source, first(source, "string_literal")) is None


def test_string_macros_give_their_prefix_and_text() -> None:
    source = Source('a = colorant"#009E73"\nb = L"%$(x)"\nc = r"ab+"i\n', "julia")
    macros = [node for node in walk(source.root) if node.type == "prefixed_string_literal"]

    assert [jl_macro_string(source, node) for node in macros] == [("colorant", "#009E73"), ("L", "%$(x)"), ("r", "ab+")]


def test_dotted_names_callees_and_macros() -> None:
    source = Source(
        'Random.seed!(42)\nBase.Filesystem.rm(p)\n-(x)\nf(x)(y)\nBase.:+(1, 2)\n@printf("%d", 1)\n', "julia"
    )
    calls = list(source.root.named_children)

    assert [jl_callee(source, node) for node in calls[:5]] == [
        "Random.seed!",
        "Base.Filesystem.rm",
        "-",
        None,
        "Base.+",
    ]
    assert jl_macro_name(source, calls[5]) == "@printf"
    assert jl_dotted(source, first(source, "identifier")) == "Random"
    module_macro = Source("Base.@kwdef struct K\n    a::Int = 1\nend\n", "julia")
    assert jl_macro_name(module_macro, first(module_macro, "macrocall_expression")) == "Base.@kwdef"


def test_arguments_split_positional_and_keyword() -> None:
    source = Source("f(a, b...; k = 1, kw)\ng(x, y = 2)\n", "julia")
    f, g = source.root.named_children
    arguments = jl_arguments(source, f)

    assert [(argument.position, argument.name, argument.splat) for argument in arguments] == [
        (0, None, False),
        (1, None, True),
        (None, "k", False),
        (None, "kw", False),
    ]
    assert source.text(arguments[2].value) == "1"
    assert jl_argument(jl_arguments(source, g), "y") is not None
    assert jl_argument(jl_arguments(source, g), "missing", 0) is not None


@pytest.mark.parametrize(
    ("code", "names", "mutation", "function"),
    [
        ("x = 1", ("x",), False, False),
        ("a, b = 1, 2", ("a", "b"), False, False),
        ("x::Float64 = 1.0", ("x",), False, False),
        ("x[1] = 2", ("x",), True, False),
        ("x.a.b = 2", ("x",), True, False),
        ("x .= 3", ("x",), True, False),
        ("x += 1", ("x",), False, False),
        ("f(x) = x + 1", ("f",), False, True),
        ("f(x::T) where {T} = x", ("f",), False, True),
        ("Base.show(io, x) = nothing", ("Base.show",), False, True),
    ],
)
def test_assignments_name_what_they_bind(code: str, names: tuple[str, ...], mutation: bool, function: bool) -> None:
    source = Source(code + "\n", "julia")
    assignment = jl_assignment(source, source.root.named_children[0])

    assert assignment is not None
    assert (assignment.names, assignment.mutation, assignment.function) == (names, mutation, function)


def test_bindings_cover_every_binding_site() -> None:
    code = (
        "const A = 1\n"
        "function f(p, q = 2; k = 3, rest...)\n    local l = 1\nend\n"
        "g(x) = x\n"
        "h = (u, v) -> u\n"
        "map(xs) do item\n    item\nend\n"
        "for (i, j) in pairs, n in 1:2\nend\n"
        "[c for c in 1:3]\n"
        "let w = 1\nend\n"
        "try\n    f()\ncatch err\nend\n"
        "struct S{T} <: Number\nend\n"
        "using Dates: Date\n"
        "f(k = 9)\n"
        "t = (named = 1,)\n"
    )
    source = Source(code, "julia")
    names = [name for name, _ in jl_bindings(source, source.root)]

    for name in ("A", "f", "p", "q", "k", "rest", "l", "g", "x", "h", "u", "v", "item", "i", "j", "n", "c", "w"):
        assert name in names, name
    for name in ("err", "S", "Date", "t"):
        assert name in names, name
    assert "named" not in names  # a named tuple's field binds nothing
    assert names.count("k") == 1  # the keyword argument of the call `f(k = 9)` binds nothing


@pytest.mark.parametrize(
    ("literal", "value"),
    [
        ("3", 3.0),
        ("-4.5", -4.5),
        ("1e3", 1000.0),
        ("1.5f0", 1.5),
        ("0x10", 16.0),
        ("1_000", 1000.0),
        (".5", 0.5),
        ("+(2)", None),
        ("x", None),
    ],
)
def test_numbers(literal: str, value: float | None) -> None:
    source = Source(f"y = {literal}\n", "julia")
    assignment = jl_assignment(source, source.root.named_children[0])

    assert assignment is not None
    assert jl_number(source, assignment.value) == value
