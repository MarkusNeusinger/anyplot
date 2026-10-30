"""Tests for the JavaScript helpers of agents/anyplot/code/treesitter.py: the grammars, literals and the scopes."""

from collections import Counter

import pytest

from agents.anyplot.code.treesitter import (
    Source,
    js_bindings,
    js_callee,
    js_dotted,
    js_number,
    js_references,
    js_string,
    parse,
    syntax_problems,
    walk,
)

from .conftest import JS_CATALOGUE_FILES, js_library


def grammar(path) -> str:
    return "tsx" if path.suffix == ".tsx" else "javascript"


def first(source: Source, kind: str):
    return next(node for node in walk(source.root) if node.type == kind)


def test_the_catalogue_has_1617_javascript_files() -> None:
    assert len(JS_CATALOGUE_FILES) == 1617
    assert Counter(js_library(path) for path in JS_CATALOGUE_FILES) == {
        "chartjs": 321,
        "d3": 325,
        "echarts": 325,
        "highcharts": 323,
        "muix": 323,
    }


@pytest.mark.parametrize("path", JS_CATALOGUE_FILES, ids=lambda path: f"{path.parts[-4]}-{path.stem}")
def test_every_catalogue_javascript_file_parses_without_error_or_missing_nodes(path) -> None:
    """The `javascript` grammar reads the four classic-script libraries, `tsx` reads MUI X (2026-10-30)."""
    tree = parse(path.read_text(encoding="utf-8"), grammar(path))

    assert syntax_problems(tree) == []
    assert not any(node.is_error or node.is_missing for node in walk(tree.root_node))


@pytest.mark.parametrize(
    ("literal", "value"),
    [
        ('"plain"', "plain"),
        ("'single'", "single"),
        ('"a\\"b"', 'a"b'),
        ('"tab\\tnew\\nline"', "tab\tnew\nline"),
        ('"\\x41\\u0042\\u{43}"', "ABC"),
        ('"\\ud83d\\ude00"', "\U0001f600"),
        ('"#009E73"', "#009E73"),
        ('"line\\\ncontinued"', "linecontinued"),
        ('"\\q"', "q"),
        ("`template`", "template"),
        ("`two\nlines`", "two\nlines"),
        ('"\\0"', "\x00"),
    ],
)
def test_string_values(literal: str, value: str) -> None:
    source = Source(f"x = {literal};\n", "javascript")
    node = next(node for node in walk(source.root) if node.type in ("string", "template_string"))

    assert js_string(source, node) == value


@pytest.mark.parametrize("literal", ["`a ${b} c`", '"\\101"', '"\\8"', '"\\ud83d"', '"\\x4"', '"\\u{110000}"'])
def test_strings_without_a_static_value(literal: str) -> None:
    source = Source(f"x = {literal};\n", "javascript")
    node = next(node for node in walk(source.root) if node.type in ("string", "template_string"))

    assert js_string(source, node) is None


@pytest.mark.parametrize(
    ("literal", "value"),
    [("3", 3.0), ("-4.5", -4.5), ("1e3", 1000.0), ("0x10", 16.0), ("0b11", 3.0), ("0o17", 15.0), ("1_000", 1000.0)]
    + [("10n", 10.0), ("+2", 2.0), ("- -2", 2.0), ("017", 15.0), ("019", 19.0)],
)
def test_numbers(literal: str, value: float) -> None:
    source = Source(f"x = {literal};\n", "javascript")
    assignment = first(source, "assignment_expression")

    assert js_number(source, assignment.child_by_field_name("right")) == value


@pytest.mark.parametrize("literal", ["1" * 400, "9" * 5000 + "n", "1e999", "x", "-x", "!1"])
def test_numbers_never_raise(literal: str) -> None:
    source = Source(f"x = {literal};\n", "javascript")
    assignment = first(source, "assignment_expression")

    assert js_number(source, assignment.child_by_field_name("right")) is None


@pytest.mark.parametrize(
    ("code", "callee"),
    [
        ("f(1);", "f"),
        ("d3.scaleLinear();", "d3.scaleLinear"),
        ("d3.scaleLinear().domain([0, 1]);", None),
        ("Math.random();", "Math.random"),
        ("a?.b?.(1);", "a.b"),
        ("(window.fetch)(1);", "window.fetch"),
        ("x[0](1);", None),
        ("(() => 1)();", None),
        ('import("x");', "import"),
    ],
)
def test_callees(code: str, callee: str | None) -> None:
    source = Source(code + "\n", "javascript")

    assert js_callee(source, first(source, "call_expression")) == callee


def test_dotted_names_stop_at_a_computed_member() -> None:
    source = Source('a.b["c"].d;\n', "javascript")
    member = first(source, "member_expression")

    assert js_dotted(source, member) is None


SCOPES = """
var top1 = 1;
let top2 = 2;
function outer(param, { shorthand, key: renamed }, [first, , ...rest] = []) {
  var inner = param;
  if (inner) {
    const block = 1;
    function nested() {}
  }
  return () => block + nested + shorthand + renamed + first + rest;
}
for (const item of [1]) {}
try {} catch ({ message }) {}
const named = function self() { return self; };
class Klass {}
fetch(top1, top2, inner, item, message, self, Klass, outer, undeclared);
"""


def test_bindings_carry_their_scopes() -> None:
    source = Source(SCOPES, "javascript")
    by_name = {binding.name: binding for binding in js_bindings(source, source.root)}

    assert by_name["top1"].kind == "var" and by_name["top1"].scope.type == "program"
    assert by_name["top2"].kind == "let" and by_name["top2"].scope.type == "program"
    assert {name for name in by_name if by_name[name].kind == "parameter"} == {
        "param",
        "shorthand",
        "renamed",
        "first",
        "rest",
    }
    assert by_name["inner"].scope.type == "function_declaration"
    assert by_name["block"].scope.type == "statement_block"
    assert by_name["nested"].scope.type == "statement_block"
    assert by_name["item"].scope.type == "for_in_statement"
    assert by_name["message"].kind == "catch"
    assert by_name["self"].scope.type == "function_expression"
    assert by_name["Klass"].kind == "class"
    assert "key" not in by_name


def test_references_resolve_to_their_scope_or_are_free() -> None:
    source = Source(SCOPES, "javascript")
    last_call = [node for node in walk(source.root) if node.type == "call_expression"][-1]
    references = [
        reference
        for reference in js_references(source, source.root)
        if last_call.start_byte <= reference.visit.node.start_byte < last_call.end_byte
    ]
    free = {reference.name for reference in references if not reference.bound}

    # inner, block-scoped and function-expression names are not visible at the top level
    assert free == {"fetch", "inner", "item", "message", "self", "undeclared"}


def test_a_shadowing_parameter_resolves_to_the_innermost_binding() -> None:
    source = Source("const t = window.x;\nconst f = (t) => t + 1;\nt.y;\n", "javascript")
    references = {(ref.name, ref.visit.node.start_point[0]): ref for ref in js_references(source, source.root)}

    assert references[("t", 1)].binding.kind == "parameter"  # type: ignore[union-attr]
    assert references[("t", 2)].binding.kind == "const"  # type: ignore[union-attr]


def test_shorthand_properties_are_references_and_jsx_tags_by_case() -> None:
    source = Source("const o = { fetch };\nconst e = <div><Chart /></div>;\n", "tsx")
    names = {reference.name for reference in js_references(source, source.root) if not reference.bound}

    assert names == {"fetch", "Chart"}


def test_type_positions_read_nothing() -> None:
    code = (
        "type P = { a: typeof fetch };\n"
        "interface Q { b: Window }\n"
        "const x: Array<number> = [] as unknown as number[];\n"
        "function f(v: Window): typeof eval { return v!; }\n"
    )
    source = Source(code, "tsx")
    names = {reference.name for reference in js_references(source, source.root) if not reference.bound}

    assert names == set()


def test_imports_bind_their_local_names() -> None:
    source = Source(
        'import React, { useMemo as memo, useState } from "react";\nimport * as M from "@mui/material";\n', "tsx"
    )

    assert sorted(binding.name for binding in js_bindings(source, source.root)) == ["M", "React", "memo", "useState"]
