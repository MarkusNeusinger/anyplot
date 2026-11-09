"""Tests for agents/anyplot/code/treesitter.py: the pinned grammar, syntax problems, positions and R helpers."""

import ast
import os
import re
import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path
from typing import cast

import pytest

from agents.anyplot.code import treesitter
from agents.anyplot.code.treesitter import (
    Source,
    parse,
    r_argument,
    r_arguments,
    r_assignment,
    r_callee,
    r_number,
    r_string,
    statements,
    syntax_problems,
    walk,
)

from .conftest import R_CATALOGUE_FILES, REPO_ROOT, merged_specs


def test_versions_are_pinned_exactly_in_the_agents_extra_and_installed() -> None:
    """A pack release changes the grammars the validators read, so both packages move only with the lock."""
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    agents = project["project"]["optional-dependencies"]["agents"]
    assert f"tree-sitter=={treesitter.TREE_SITTER_VERSION}" in agents
    assert version("tree-sitter") == treesitter.TREE_SITTER_VERSION
    assert f"tree-sitter-language-pack=={version('tree-sitter-language-pack')}" in agents


def test_the_service_reads_grammars_only_through_the_registry_that_never_downloads() -> None:
    """The pack's `get_language`, `get_parser`, `download`, `init` and `prefetch` fetch a missing grammar; its
    `LanguageRegistry` loads from the grammar directory alone, so no module under agents/ uses anything else."""
    allowed = {"LanguageRegistry", "LanguageNotFoundError"}
    used: dict[str, set[str]] = {}
    for path in (REPO_ROOT / "agents").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = used.setdefault(str(path.relative_to(REPO_ROOT)), set())
        aliases = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
            if alias.name == "tree_sitter_language_pack"
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("tree_sitter_language_pack"):
                names |= {alias.name for alias in node.names}
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
                names.add(node.attr)

    assert used["agents/anyplot/code/treesitter.py"] == allowed
    assert {path: sorted(names - allowed) for path, names in used.items() if names - allowed} == {}


def test_a_missing_grammar_stops_the_start_without_a_download(tmp_path: Path) -> None:
    """An empty grammar directory fails `check_grammars` on its first grammar, offline: nothing reaches a cache."""
    cache = tmp_path / "cache"
    environment = {
        **os.environ,
        treesitter.GRAMMARS_DIR_ENV: str(tmp_path / "grammars"),
        "TREE_SITTER_LANGUAGE_PACK_CACHE_DIR": str(cache),
        "TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL": f"file://{tmp_path}/no-manifest.json",
        "XDG_CACHE_HOME": str(cache),
    }
    (tmp_path / "grammars").mkdir()
    started = subprocess.run(
        [sys.executable, "-c", "from agents.anyplot.code import treesitter; treesitter.check_grammars()"],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert started.returncode != 0
    assert "RuntimeError: tree-sitter grammar 'r' is not in" in started.stderr
    assert not cache.exists()


def test_the_service_start_checks_every_grammar(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    from agents import main

    def missing() -> None:
        raise RuntimeError("tree-sitter grammar 'r' is not in /nowhere")

    monkeypatch.setattr(treesitter, "check_grammars", missing)
    with pytest.raises(RuntimeError, match="grammar 'r'"), TestClient(main.app):
        pass


def test_every_image_with_the_agents_extra_bakes_exactly_the_profiles_grammars_read_only() -> None:
    """An image that installs the `agents` extra fetches the grammars the code profiles load (`GRAMMARS`) at build
    time, out of the 23 MB bundle, and serves them from a root-owned directory, with the pack's manifest URL on a
    file that does not exist. A new profile adds its grammar to `GRAMMARS` and to `TREE_SITTER_GRAMMARS` together,
    or this fails."""
    patterns = ("Dockerfile", "*/Dockerfile", "*/*/Dockerfile", "*/*.Dockerfile", "*/*/*.Dockerfile")
    dockerfiles = sorted(
        {
            path
            for pattern in patterns
            for path in REPO_ROOT.glob(pattern)
            if not any(part.startswith(".") for part in path.relative_to(REPO_ROOT).parts)
        }
    )
    with_agents = [path for path in dockerfiles if "--extra agents" in path.read_text(encoding="utf-8")]

    assert REPO_ROOT / "agents" / "Dockerfile" in with_agents
    for path in with_agents:
        text = path.read_text(encoding="utf-8")
        match = re.search(r'^ARG TREE_SITTER_GRAMMARS="([^"]*)"$', text, re.MULTILINE)
        assert match is not None, f"{path} installs the agents extra without fetching the grammars"
        assert sorted(match.group(1).split()) == sorted(treesitter.GRAMMARS), path
        assert 'pack.download(sys.argv[1:])" $TREE_SITTER_GRAMMARS' in text, path
        copy = re.search(r"^COPY --from=builder /app/tree-sitter-grammars (\S+)$", text, re.MULTILINE)
        assert copy is not None, f"{path} must copy the grammars without --chown, so they stay root's"
        assert f"ENV {treesitter.GRAMMARS_DIR_ENV}=/app/{copy.group(1).removeprefix('./')}\n" in text, path
        assert re.search(r"^ENV TREE_SITTER_LANGUAGE_PACK_MANIFEST_URL=file:///nonexistent/", text, re.MULTILINE)


def test_only_the_served_grammars_load() -> None:
    assert treesitter.GRAMMARS == ("r", "julia", "javascript", "tsx")
    assert treesitter.language("r") is treesitter.language("r")
    assert treesitter.language("julia") is not treesitter.language("r")
    assert treesitter.language("tsx") is not treesitter.language("javascript")
    for grammar in ("python", "typescript"):
        with pytest.raises(ValueError, match="no tree-sitter grammar"):
            treesitter.language(cast(treesitter.Grammar, grammar))


def test_the_parse_gate_reads_every_merged_r_file() -> None:
    """The parse gate below runs over every merged ggplot2 implementation, not a count of a day (325 on
    2026-10-29): the glob finds exactly the specs whose metadata names one."""
    assert R_CATALOGUE_FILES
    assert {path.parts[-4] for path in R_CATALOGUE_FILES} == merged_specs("r", "ggplot2")


@pytest.mark.parametrize("path", R_CATALOGUE_FILES, ids=lambda path: path.parts[-4])
def test_every_catalogue_r_file_parses_without_error_or_missing_nodes(path) -> None:
    """The gate of the owner decision of 2026-10-29: the grammar reads all 325 ggplot2 files."""
    tree = parse(path.read_text(encoding="utf-8"), "r")

    assert syntax_problems(tree) == []
    assert not any(node.is_error or node.is_missing for node in walk(tree.root_node))


@pytest.mark.parametrize(
    ("code", "message"), [("f(a, (b\n", "line 1"), ("x <- )\n", "line 1"), ("x <- 1\ny <- function(a {\n", "line 2")]
)
def test_syntax_problems_name_the_line(code: str, message: str) -> None:
    problems = syntax_problems(parse(code, "r"))

    assert problems
    assert message in problems[0].message()


def test_syntax_problems_are_capped_and_clean_code_has_none() -> None:
    assert syntax_problems(parse("x <- 1\n", "r")) == []
    assert len(syntax_problems(parse(")\n" * 50, "r"), limit=3)) <= 3


def test_walk_is_iterative_on_deeply_nested_code() -> None:
    code = "x <- " + "(" * 1000 + "1" + ")" * 1000 + "\n"
    source = Source(code, "r")

    assert sum(1 for node in walk(source.root) if node.type == "parenthesized_expression") == 1000
    assert syntax_problems(source.tree) == []


def test_nesting_past_the_parsers_depth_is_a_syntax_problem() -> None:
    """tree-sitter stops nesting at about 1,024 levels and reports the rest as errors: deeper code fails closed."""
    code = "x <- " + "(" * 5000 + "1" + ")" * 5000 + "\n"

    assert syntax_problems(parse(code, "r"))


def test_positions_are_characters_and_lines_with_non_ascii_text() -> None:
    code = 'x <- "anyplot · ggplot2 — 3 °C"\ny <- f(a = 1)\n'
    source = Source(code, "r")
    first, second = statements(source.root)

    assert source.node_span(first).end == code.index("\n")
    span = source.node_span(second)
    assert code[span.start : span.end] == "y <- f(a = 1)"
    assert (span.first_line, span.last_line) == (2, 2)
    whole = source.lines_span(second)
    assert code[whole.start : whole.end] == "y <- f(a = 1)\n"
    assert source.line_of(span.start) == 2
    assert source.line_count == 3


def test_statements_skip_comments() -> None:
    source = Source("# Data\nx <- 1\n# Plot\nplot(x)\n", "r")

    assert [node.type for node in statements(source.root)] == ["binary_operator", "call"]
    assert [source.text(node) for node in treesitter.comments(source.root)] == ["# Data", "# Plot"]


@pytest.mark.parametrize(
    ("literal", "value"),
    [
        ('"plain"', "plain"),
        ("'single'", "single"),
        (r'"tab\there"', "tab\there"),
        (r'"quote \" inside"', 'quote " inside'),
        (r'"é\u{e9}\x41\101\U0001F600"', "ééAA\U0001f600"),
        ('r"(raw "text")"', 'raw "text"'),
        ("R'[raw]'", "raw"),
        ('r"--{a}-}--"', "a}-"),
        ('"multi\nline"', "multi\nline"),
    ],
)
def test_r_strings_decode_to_their_value(literal: str, value: str) -> None:
    assert r_string(literal) == value


@pytest.mark.parametrize("literal", [r'"\q"', r'"\0"', r'"\x"', r'"\u{}"', 'r"(open"', "plain"])
def test_r_strings_r_would_refuse_decode_to_none(literal: str) -> None:
    assert r_string(literal) is None


def test_backtick_names_and_namespaced_callees() -> None:
    source = Source('`my var` <- 1\nbase::system("id")\ngrDevices:::png("x")\n`system`("id")\n"system"("id")\n', "r")
    assignment, base_call, triple, backtick, string = statements(source.root)

    found = r_assignment(source, assignment)
    assert found is not None and found.name == "my var"
    assert r_callee(source, base_call) == "base::system"
    assert r_callee(source, triple) == "grDevices:::png"
    assert r_callee(source, backtick) == "system"
    assert r_callee(source, string) is None


def test_arguments_keep_names_positions_and_empty_slots() -> None:
    source = Source('f(a = 1, , "b" = 2, `c d` = 3, x)\ng()\n', "r")
    call, empty = statements(source.root)
    arguments = r_arguments(source, call)

    assert [(argument.position, argument.name) for argument in arguments] == [
        (0, "a"),
        (1, None),
        (2, "b"),
        (3, "c d"),
        (4, None),
    ]
    assert arguments[1].value is None
    assert r_arguments(source, empty) == []
    second = r_argument(arguments, "missing", 1)
    assert second is not None and second.position == 4


@pytest.mark.parametrize(
    ("code", "operator", "name", "is_super"),
    [
        ("x <- 1", "<-", "x", False),
        ("x = 1", "=", "x", False),
        ("1 -> x", "->", "x", False),
        ("x <<- 1", "<<-", "x", True),
        ("1 ->> x", "->>", "x", True),
        ('"x" <- 1', "<-", "x", False),
        ("names(x)[2] <- 'b'", "<-", "x", False),
        ("x$a@b[[1]] <- 2", "<-", "x", False),
    ],
)
def test_assignments_name_the_variable_they_bind(code: str, operator: str, name: str, is_super: bool) -> None:
    source = Source(code + "\n", "r")
    found = r_assignment(source, statements(source.root)[0])

    assert found is not None
    assert (found.operator, found.name, found.is_super) == (operator, name, is_super)


def test_a_call_argument_is_no_assignment() -> None:
    source = Source("f(x = 1)\n", "r")

    assert all(r_assignment(source, node) is None for node in walk(source.root))


@pytest.mark.parametrize(
    ("code", "value"),
    [("3", 3.0), ("-4.5", -4.5), ("1e3", 1000.0), ("0x10", 16.0), ("2L", 2.0), ("(7)", 7.0), ("x", None)],
)
def test_numbers(code: str, value: float | None) -> None:
    source = Source(code + "\n", "r")

    assert r_number(source, statements(source.root)[0]) == value


def test_module_imports_only_the_standard_library_and_tree_sitter() -> None:
    """The R detection is meant to move to core/ (2026-10-29): this module may not import from agents.*."""
    tree = ast.parse((REPO_ROOT / "agents/anyplot/code/treesitter.py").read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
    } | {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}

    assert not any(isinstance(node, ast.ImportFrom) and node.level for node in ast.walk(tree))
    assert imported <= {
        "bisect",
        "functools",
        "math",
        "collections",
        "dataclasses",
        "importlib",
        "os",
        "pathlib",
        "typing",
        "tree_sitter",
        "tree_sitter_language_pack",
    }


def test_no_module_reads_a_points_row_or_column_attribute() -> None:
    """tree-sitter 0.26.0's `Point.row` and `.column` free an int past 256 under Python 3.14 (segfault at the next
    collection, 2026-10-29); the modules index the point (`first_line`, `last_line`, `column`)."""
    paths = [
        REPO_ROOT / "agents/anyplot/code/treesitter.py",
        *(REPO_ROOT / "agents/anyplot/code/profiles").rglob("*.py"),
    ]
    found = [
        f"{path.name}:{node.lineno}"
        for path in paths
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.Attribute) and node.attr in ("row", "column")
    ]

    assert found == []
