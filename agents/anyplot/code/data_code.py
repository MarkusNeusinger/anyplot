"""The data snippet before it runs: the `__main__` guard stripped, then the DATA profile of the validator.

`run_data_code` (`tools/session.py`) runs a snippet the root translated to Python from
what the user pasted or typed. Scripts often end in `if __name__ == "__main__":`,
which the dunder rule refuses; the guard is boilerplate, not intent, so
`strip_main_guard` replaces every top-level guard without an `else` by its dedented
body before validation, deterministically, instead of asking the root to remember it.
A guard with an `else`, or one that is not top-level, stays and fails the dunder rule.
No ADK import.
"""

import ast
import textwrap

from .validate import Finding, validate_data_code


def _is_main_test(test: ast.expr) -> bool:
    """`__name__ == "__main__"`, either way round."""
    if not (isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq)):
        return False
    sides = [test.left, test.comparators[0]]
    names = [side for side in sides if isinstance(side, ast.Name) and side.id == "__name__"]
    texts = [side for side in sides if isinstance(side, ast.Constant) and side.value == "__main__"]
    return len(names) == 1 and len(texts) == 1


def _first_line(statement: ast.stmt) -> int:
    """The first line of a statement, its decorators included."""
    decorators: list[ast.expr] = getattr(statement, "decorator_list", [])
    return min([statement.lineno, *(decorator.lineno for decorator in decorators)])


def strip_main_guard(code: str) -> str:
    """`code` with every top-level `if __name__ == "__main__":` (no `else`) replaced by its dedented body.

    Code that does not parse is returned unchanged: the validator reports its syntax error.
    """
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError):
        return code
    guards = [node for node in tree.body if isinstance(node, ast.If) and not node.orelse and _is_main_test(node.test)]
    if not guards:
        return code
    lines = code.splitlines(keepends=True)
    for guard in reversed(guards):  # from the bottom, so the line numbers above stay valid
        end = guard.end_lineno or guard.lineno
        first = _first_line(guard.body[0])
        if first == guard.lineno:  # `if __name__ == "__main__": main()` on one line
            segments = [ast.get_source_segment(code, statement) or "" for statement in guard.body]
            body = "".join(segment + "\n" for segment in segments)
        else:
            body = textwrap.dedent("".join(lines[first - 1 : end]))
            if not body.endswith("\n"):
                body += "\n"
        lines[guard.lineno - 1 : end] = [body]
    return "".join(lines)


def check_data_code(code: str) -> tuple[str, list[Finding]]:
    """The snippet as it will run (the guard stripped) and its DATA-profile findings; empty findings mean it may run."""
    prepared = strip_main_guard(code)
    return prepared, validate_data_code(prepared)
