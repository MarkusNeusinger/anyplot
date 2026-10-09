"""Two-profile AST validator of the plot pipeline (docs/concepts/agent-network.md, "Adapt and validate").

The SECURITY profile runs on the normalised catalogue original (eligibility) and on every
adapted working form; the ADAPTATION profile runs on adapted code only. Both functions
return an empty list for valid code and never raise on invalid code: a syntax error, an
oversize file or a string that is not UTF-8 text is itself a `Finding`. Only an unknown
`library` raises, because that is a caller bug, not a property of the code.

The validator is one guardrail layer, not the boundary: the sandbox (no egress, read-only
root, no environment) and the loader substitution are the others. Its job is to make the
adapter's output boring: a fixed import surface, no reflection, no I/O, one data source.

Decisions this module takes where the design leaves room:

* **Import surface.** COMMON plus the science stack (`scipy.{stats, interpolate, signal,
  cluster.hierarchy, spatial, optimize, special, integrate, ndimage}`, `sklearn` without
  `datasets`, `statsmodels.{api, nonparametric, tsa, graphics}`) plus, for matplotlib
  and seaborn, `matplotlib`, `seaborn` and the bundled `mpl_toolkits.{mplot3d,
  axes_grid1, axisartist}`. The four extra scipy modules, `statsmodels.graphics` and
  the toolkits were admitted after the readiness sweep showed them behind most of the
  catalogue's benign import blocks; each was walked for file or network helpers and
  has none. Third-party plotting helpers (cartopy, qrcode, wordcloud, matplotlib_venn,
  squarify, adjustText) stay banned: they are not in the agents image, and admitting
  one is an owner decision, not a validator default.
* **Attribute names are banned outright, on any object.** `.format`, `.eval`, `.query`,
  `.show`, `.use`, `.load`, `.read_*`, `.to_csv` and the rest are findings wherever they
  appear, called or not, because the receiver's type is not knowable without executing
  (`f = pd.read_csv; f(path)` and `x = df; x.eval(...)` have to fail too). The price is
  a false positive on a column accessed as an attribute (`df.load`, `df.read_count`):
  the message says to subscript instead, and the single repair does. `.use` is wider
  than the design's `matplotlib.use` because `matplotlib.style.use` accepts paths and
  URLs; `.io` and `ExcelWriter` are added for `pandas.io.common.get_handle` and the
  Excel writer, which the design's list does not name.
* **Module paths are resolved through import aliases** (`import numpy as np`,
  `import matplotlib.pyplot as plt`, `from numpy import random`, plus one level of
  `name = <module chain>` assignment). The resolver drives the RNG rule and the
  messages; the security bans do not depend on it.
* **`os` is allowed only as the THEME block uses it.** Every occurrence of a name bound
  by `import os [as X]` must be the receiver of `X.getenv("ANYPLOT_THEME", ...)` or
  `X.environ.get("ANYPLOT_THEME", ...)` with the literal first argument, at most two
  positional arguments and no keyword other than `default`. `from os import ...` is a
  banned import. Note `__file__` is a dunder, so the catalogue's `sys.path` guard fails
  twice (`sys` and `__file__`); the normaliser strips that guard before eligibility.
* **Dunders and strings.** Every identifier matching `^__\\w+__$` (names, attributes,
  keywords, parameters, function names) and every string or bytes literal containing a
  dunder identifier is a finding; `__name__ == "__main__"` guards therefore fail, which
  is intended (no catalogue file uses one). Strings built at runtime (`"__cla" + "ss__"`)
  pass this check but have no consumer: `getattr`, `eval`, `exec`, `vars`, `__import__`
  and `.format` are all banned.
* **URL literals** match `http://`, `https://`, `ftp://`, and `file:`/`data:` followed
  by a non-space character, case-insensitively and at a word boundary, so a subtitle
  "Source data: 2024 survey" or the word "profile:" passes while `data:image/png;...`
  and `file:///etc/passwd` do not.
* **savefig.** Every `savefig` call (not only the last) must target exactly the f-string
  `f"plot-{THEME}.png"`, as the first positional argument or `fname=`; a file without a
  savefig call is a finding too. A second savefig writing elsewhere is never wanted.
* **`type()`** is allowed with exactly one plain positional argument; anything else
  (three arguments, starred arguments, keywords) is the class-creating form.
* **String method names.** pandas resolves `df.agg("to_csv")`, `df.apply("eval")` and
  `df.transform(...)` by `getattr` on the frame (falling back to numpy), so a string
  argument of `agg`, `aggregate`, `apply`, `transform` or `applymap` that names a banned
  attribute or function is a finding.
* **RNG allowance (ADAPTATION).** Exactly `np.random.default_rng(<int literal>)` (positional
  or `seed=`), either bound once by a plain `name = ...` assignment whose every use is a
  `name.choice(...)`, `name.permutation(...)` or `name.uniform(...)` call, or used inline
  as `np.random.default_rng(7).uniform(...)`. Everything else under `numpy.random.*`,
  the stdlib `random` module and scipy's `.rvs` samplers are findings.
* **Literal data (ADAPTATION).** A list, tuple or set literal is flattened through nested
  containers and its numeric leaves counted (`int`, `float`, `complex` and their signed
  forms; not `bool`); more than 20 at the outermost container is a finding.
* **Palette (ADAPTATION).** `IMPRINT` and `IMPRINT_PALETTE` (the two names the catalogue
  uses) must be lists or tuples of string literals that keep `original_palette` as their
  prefix in order (hex compared case-insensitively); the entries after the prefix must be
  the canonical `core.palette.IMPRINT` positions not already in the original, in
  canonical order, which for a canonical original is exactly "the next positions".
* **Placeholder (ADAPTATION).** Exactly one `df = load_user_data()` statement, anywhere;
  any other use of the name `load_user_data` is a separate finding.

Rule ids: `size`, `encoding`, `syntax`, `banned-import`, `star-import`,
`relative-import`, `os-use`, `banned-name`, `banned-call`, `banned-attribute`, `dunder`,
`banned-statement`, `url-literal`, `string-length`, `savefig-target` (SECURITY);
`placeholder-count`, `placeholder-use`, `rng`, `literal-data`, `palette-prefix`
(ADAPTATION). Findings are sorted by line; messages never echo more than about 60
characters of code and never echo string literal contents.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal, TypeVar

from core.constants import SUPPORTED_LIBRARIES
from core.palette import IMPRINT

from ..schemas import MAX_CODE_CHARS


Profile = Literal["security", "adaptation"]

MAX_STRING_CHARS = 200
MAX_LITERAL_NUMBERS = 20
MAX_MESSAGE_CHARS = 300
MAX_SNIPPET_CHARS = 60
PLACEHOLDER = "df = load_user_data()"
THEME_VARIABLE = "ANYPLOT_THEME"

COMMON_IMPORTS: frozenset[str] = frozenset(
    {
        "numpy",
        "pandas",
        "math",
        "statistics",
        "datetime",
        "collections",
        "itertools",
        "functools",
        "textwrap",
        "colorsys",
        "re",
    }
)
# Shared by every Python plotting library: the science stack minus its data loaders.
# Every package here was walked for public names that read, load, save, open or fetch
# (2026-10-09, scipy 1.18, statsmodels 0.14): none exist; `scipy.ndimage.imread` is
# long gone. `scipy.io` and `scipy.datasets` stay out.
SHARED_SCIENCE_IMPORTS: frozenset[str] = frozenset(
    {
        "scipy.stats",
        "scipy.interpolate",
        "scipy.signal",
        "scipy.cluster.hierarchy",
        "scipy.spatial",
        "scipy.optimize",
        "scipy.special",
        "scipy.integrate",
        "scipy.ndimage",
        "sklearn",
        "statsmodels.api",
        "statsmodels.nonparametric",
        "statsmodels.tsa",
        "statsmodels.graphics",
    }
)
DENIED_IMPORTS: frozenset[str] = frozenset({"sklearn.datasets", "statsmodels.formula", "scipy.io", "scipy.datasets"})
# The three toolkits ship with matplotlib and do no I/O. Third-party plotting helpers
# (cartopy, qrcode, wordcloud, matplotlib_venn, squarify, adjustText) stay banned: they
# are not installed in the agents image, and admitting one is an owner decision.
_MATPLOTLIB_STACK: frozenset[str] = frozenset(
    {"matplotlib", "mpl_toolkits.mplot3d", "mpl_toolkits.axes_grid1", "mpl_toolkits.axisartist"}
)
# Phase 1 enables matplotlib and seaborn. The other Python libraries save through
# different calls (`write_image`, `ggsave`, `render_to_png`), so their profile needs
# more than an import allowlist; until then they raise `ValueError`.
LIBRARY_IMPORTS: dict[str, frozenset[str]] = {
    "matplotlib": _MATPLOTLIB_STACK,
    "seaborn": _MATPLOTLIB_STACK | {"seaborn"},
}

BANNED_NAMES: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "input",
        "breakpoint",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "memoryview",
        "exit",
        "quit",
    }
)
BANNED_ATTRIBUTES: frozenset[str] = frozenset(
    {"format", "format_map", "eval", "query", "memmap", "ctypeslib", "f2py", "use", "show", "io"}
)
BANNED_IO: frozenset[str] = frozenset(
    {
        "ExcelFile",
        "ExcelWriter",
        "HDFStore",
        "to_csv",
        "to_pickle",
        "to_parquet",
        "to_excel",
        "to_sql",
        "to_hdf",
        "to_feather",
        "to_json",
        "to_html",
        "to_clipboard",
        "save",
        "savez",
        "savez_compressed",
        "savetxt",
        "genfromtxt",
        "fromfile",
        "fromregex",
        "DataSource",
        "tofile",
        "imread",
        "get_sample_data",
        "rc_file",
        "urlopen",
    }
)
# `read_*` (pandas readers), `fetch_*` (sklearn downloaders), `load*` (`np.load`,
# `np.loadtxt`, `sns.load_dataset`, sklearn's `load_*`).
_BANNED_IO_PATTERN = re.compile(r"^(?:read_\w+|fetch_\w+|load\w*)$")
_STRING_DISPATCH_METHODS = frozenset({"agg", "aggregate", "apply", "transform", "applymap"})

_DUNDER_NAME = re.compile(r"^__\w+__$")
_DUNDER_IN_TEXT = re.compile(r"__\w+__")
_URL_IN_TEXT = re.compile(r"(?i)(?:https?|ftp)://|\b(?:file|data):\S")

_BANNED_STATEMENTS: dict[type[ast.AST], str] = {
    ast.ClassDef: "class definition",
    ast.AsyncFunctionDef: "async def",
    ast.AsyncFor: "async for",
    ast.AsyncWith: "async with",
    ast.Await: "await",
    ast.Yield: "yield",
    ast.YieldFrom: "yield from",
    ast.Global: "global",
    ast.Nonlocal: "nonlocal",
}

_RNG_FACTORY = "numpy.random.default_rng"
_RNG_ALLOWED_METHODS = frozenset({"choice", "permutation", "uniform"})
_RNG_ALLOWED_TEXT = "/".join(f".{method}" for method in sorted(_RNG_ALLOWED_METHODS))
_PALETTE_NAMES = frozenset({"IMPRINT", "IMPRINT_PALETTE"})

_Node = TypeVar("_Node", bound=ast.AST)


@dataclass(frozen=True, slots=True)
class Finding:
    """One validator result: a short kebab-case rule id, one message line, a 1-based line."""

    rule: str
    message: str
    line: int | None


def validate_security(code: str, *, library: str) -> list[Finding]:
    """The SECURITY profile: import surface, reflection, I/O, statements, literals, savefig.

    Raises `ValueError` for a library id that is not in the catalogue or has no profile
    yet; never raises for the code itself.
    """
    if library not in SUPPORTED_LIBRARIES:
        raise ValueError(f"unknown library {library!r}")
    library_imports = LIBRARY_IMPORTS.get(library)
    if library_imports is None:
        raise ValueError(f"no validator profile for {library!r} yet; enabled: {', '.join(sorted(LIBRARY_IMPORTS))}")
    tree, findings = _parse(code)
    if tree is None:
        return findings
    scan = _Scan(tree)
    scan.security(library, COMMON_IMPORTS | SHARED_SCIENCE_IMPORTS | library_imports)
    return scan.result()


def validate_adaptation(code: str, *, original_palette: list[str]) -> list[Finding]:
    """The ADAPTATION profile: one placeholder, no fabricated data, the palette prefix kept."""
    tree, findings = _parse(code)
    if tree is None:
        return findings
    scan = _Scan(tree)
    scan.adaptation(original_palette)
    return scan.result()


def _parse(code: str) -> tuple[ast.Module | None, list[Finding]]:
    """Size, encoding and syntax: the checks that run before any rule can."""
    if len(code) > MAX_CODE_CHARS:
        return None, [Finding("size", f"code is {len(code):,} characters; the limit is {MAX_CODE_CHARS:,}", None)]
    try:
        code.encode("utf-8")
    except UnicodeEncodeError:
        return None, [Finding("encoding", "code is not valid UTF-8 text", None)]
    try:
        tree = ast.parse(code, feature_version=(3, 13))
    except SyntaxError as exc:
        return None, [Finding("syntax", f"syntax error: {exc.msg}", exc.lineno)]
    except (ValueError, RecursionError) as exc:  # null bytes, expression nesting
        return None, [Finding("syntax", f"cannot parse: {exc}", None)]
    return tree, []


def _is_numeric(node: ast.AST) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        node = node.operand
    return isinstance(node, ast.Constant) and type(node.value) in (int, float, complex)


def _numeric_leaves(node: ast.AST) -> int:
    """Numeric literal leaves of a (nested) list, tuple or set literal."""
    if not isinstance(node, ast.List | ast.Tuple | ast.Set):
        return 0
    return sum(1 if _is_numeric(elt) else _numeric_leaves(elt) for elt in node.elts)


def _hex(value: str) -> str:
    return value.strip().upper()


def _text(node: ast.Constant) -> str | None:
    """The textual content of a string or bytes literal, or None for other constants."""
    if isinstance(node.value, str):
        return node.value
    if isinstance(node.value, bytes):
        return node.value.decode("latin-1")
    return None


def _snippet(node: ast.AST) -> str:
    text = ast.unparse(node)
    if len(text) > MAX_SNIPPET_CHARS:
        text = text[: MAX_SNIPPET_CHARS - 3] + "..."
    return text


def _module_allowed(path: str, allowed: Iterable[str]) -> bool:
    return any(path == prefix or path.startswith(prefix + ".") for prefix in allowed)


def _is_placeholder(node: ast.AST | None) -> bool:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "df"
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "load_user_data"
        and not node.value.args
        and not node.value.keywords
    )


def _is_theme_target(node: ast.AST) -> bool:
    """Exactly `f"plot-{THEME}.png"`: three parts, the middle a bare `THEME` with no spec."""
    if not isinstance(node, ast.JoinedStr) or len(node.values) != 3:
        return False
    head, middle, tail = node.values
    return (
        isinstance(head, ast.Constant)
        and head.value == "plot-"
        and isinstance(middle, ast.FormattedValue)
        and isinstance(middle.value, ast.Name)
        and middle.value.id == "THEME"
        and middle.conversion == -1
        and middle.format_spec is None
        and isinstance(tail, ast.Constant)
        and tail.value == ".png"
    )


def _single_name_target(node: ast.AST) -> ast.Name | None:
    """The `name` of a plain `name = ...` or `name: T = ...` statement, else None."""
    if isinstance(node, ast.Assign):
        targets: list[ast.expr] = node.targets
    elif isinstance(node, ast.AnnAssign):
        targets = [node.target]
    else:
        return None
    if len(targets) == 1 and isinstance(targets[0], ast.Name):
        return targets[0]
    return None


class _Scan:
    """One parsed module, indexed by node type, with parent links and import aliases."""

    def __init__(self, tree: ast.Module) -> None:
        self.by_type: defaultdict[type[ast.AST], list[ast.AST]] = defaultdict(list)
        self.parents: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            self.by_type[type(node)].append(node)
            for child in ast.iter_child_nodes(node):
                self.parents[child] = node
        self.findings: list[Finding] = []
        self.os_names: set[str] = set()
        self.aliases: dict[str, str] = {}
        self._collect_aliases()

    # -- shared --------------------------------------------------------------------------

    def add(self, rule: str, message: str, node: ast.AST | None) -> None:
        self.findings.append(Finding(rule, message[:MAX_MESSAGE_CHARS], self._line(node)))

    def result(self) -> list[Finding]:
        unique = dict.fromkeys(self.findings)
        return sorted(unique, key=lambda f: (f.line is None, f.line or 0, f.rule, f.message))

    def of(self, node_type: type[_Node]) -> list[_Node]:
        return [node for node in self.by_type[node_type] if isinstance(node, node_type)]

    def _line(self, node: ast.AST | None) -> int | None:
        while node is not None:
            line = getattr(node, "lineno", None)
            if isinstance(line, int):
                return line
            node = self.parents.get(node)
        return None

    def _collect_aliases(self) -> None:
        """Name bound by an import (or a one-level module assignment) → dotted module path."""
        for import_node in self.of(ast.Import):
            for alias in import_node.names:
                if alias.asname:
                    self.aliases[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    self.aliases[root] = root
        for from_node in self.of(ast.ImportFrom):
            if from_node.level or not from_node.module:
                continue
            for alias in from_node.names:
                if alias.name != "*":
                    self.aliases[alias.asname or alias.name] = f"{from_node.module}.{alias.name}"
        for assign in sorted(self.of(ast.Assign), key=lambda n: n.lineno):
            target = _single_name_target(assign)
            path = self.resolve(assign.value) if target is not None else None
            if target is not None and path is not None:
                self.aliases[target.id] = path

    def resolve(self, node: ast.AST) -> str | None:
        """`np.random.normal` → `numpy.random.normal`; None when the root is not a module."""
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        root = self.aliases.get(node.id)
        if root is None:
            return None
        return ".".join([root, *reversed(parts)])

    def _is_call_receiver(self, node: ast.AST, methods: frozenset[str]) -> bool:
        """`node` is the value of an attribute in `methods` that is itself called."""
        attribute = self.parents.get(node)
        if not isinstance(attribute, ast.Attribute) or attribute.value is not node or attribute.attr not in methods:
            return False
        call = self.parents.get(attribute)
        return isinstance(call, ast.Call) and call.func is attribute

    # -- SECURITY ------------------------------------------------------------------------

    def security(self, library: str, allowed_imports: frozenset[str]) -> None:
        self._check_imports(library, allowed_imports)
        self._check_os_use()
        self._check_names()
        self._check_attributes()
        self._check_calls()
        self._check_statements()
        self._check_strings()
        self._check_savefig()

    def _check_imports(self, library: str, allowed: frozenset[str]) -> None:
        def denied(path: str) -> bool:
            return _module_allowed(path, DENIED_IMPORTS)

        def permitted(path: str) -> bool:
            return _module_allowed(path, allowed) and not denied(path)

        for import_node in self.of(ast.Import):
            for alias in import_node.names:
                if alias.name == "os":
                    self.os_names.add(alias.asname or "os")
                elif not permitted(alias.name):
                    self.add("banned-import", f"import of '{alias.name}' is not allowed with {library}", alias)
        for from_node in self.of(ast.ImportFrom):
            if from_node.level or not from_node.module:
                self.add("relative-import", "relative imports are not allowed", from_node)
                continue
            for alias in from_node.names:
                if alias.name == "*":
                    self.add("star-import", f"star import from '{from_node.module}' is not allowed", alias)
                    continue
                path = f"{from_node.module}.{alias.name}"
                if denied(path) or not (permitted(from_node.module) or permitted(path)):
                    self.add("banned-import", f"import of '{path}' is not allowed with {library}", alias)
                self._check_function_name(alias.name, alias)

    def _check_function_name(self, name: str, node: ast.AST) -> None:
        """A function reached by a `from` import: the attribute set and the I/O set apply."""
        if name in BANNED_ATTRIBUTES:
            self.add("banned-attribute", f"'{name}' is not allowed", node)
        elif name in BANNED_IO or _BANNED_IO_PATTERN.match(name):
            self.add("banned-call", f"'{name}' is not allowed", node)

    def _check_os_use(self) -> None:
        for name in self.of(ast.Name):
            if name.id in self.os_names and not self._is_theme_lookup(name):
                self.add("os-use", f"'{name.id}' may only be used as {name.id}.getenv('{THEME_VARIABLE}', ...)", name)

    def _is_theme_lookup(self, name: ast.Name) -> bool:
        """`os.getenv("ANYPLOT_THEME", ...)` or `os.environ.get("ANYPLOT_THEME", ...)` around `name`."""
        node: ast.AST = name
        attribute = self.parents.get(node)
        expected = "getenv"
        if isinstance(attribute, ast.Attribute) and attribute.value is node and attribute.attr == "environ":
            node = attribute
            attribute = self.parents.get(node)
            expected = "get"
        if not isinstance(attribute, ast.Attribute) or attribute.value is not node or attribute.attr != expected:
            return False
        call = self.parents.get(attribute)
        if not isinstance(call, ast.Call) or call.func is not attribute:
            return False
        if not 1 <= len(call.args) <= 2 or any(keyword.arg != "default" for keyword in call.keywords):
            return False
        key = call.args[0]
        return isinstance(key, ast.Constant) and key.value == THEME_VARIABLE

    def _check_names(self) -> None:
        for name in self.of(ast.Name):
            if name.id in BANNED_NAMES:
                self.add("banned-name", f"'{name.id}' is not allowed", name)
            if _DUNDER_NAME.match(name.id):
                self.add("dunder", f"dunder name '{name.id}' is not allowed", name)
        for parameter in self.of(ast.arg):
            if parameter.arg in BANNED_NAMES:
                self.add("banned-name", f"parameter '{parameter.arg}' is not allowed", parameter)
            if _DUNDER_NAME.match(parameter.arg):
                self.add("dunder", f"dunder parameter '{parameter.arg}' is not allowed", parameter)
        for function in self.of(ast.FunctionDef):
            if _DUNDER_NAME.match(function.name):
                self.add("dunder", f"dunder function name '{function.name}' is not allowed", function)
        for keyword in self.of(ast.keyword):
            if keyword.arg is not None and _DUNDER_NAME.match(keyword.arg):
                self.add("dunder", f"dunder keyword '{keyword.arg}' is not allowed", keyword)

    def _check_attributes(self) -> None:
        for attribute in self.of(ast.Attribute):
            if _DUNDER_NAME.match(attribute.attr):
                self.add("dunder", f"dunder attribute '.{attribute.attr}' is not allowed", attribute)
            elif attribute.attr in BANNED_ATTRIBUTES:
                self.add("banned-attribute", f"attribute '.{attribute.attr}' is not allowed", attribute)
            elif attribute.attr in BANNED_IO or _BANNED_IO_PATTERN.match(attribute.attr):
                # `df.load` / `df.read_count`: a column reached as an attribute, not a module function.
                column_like = self.resolve(attribute.value) is None and attribute.attr.startswith(("read_", "load"))
                hint = "; a column of that name must be subscripted" if column_like else ""
                self.add("banned-call", f"'{_snippet(attribute)}' is not allowed{hint}", attribute)

    def _check_calls(self) -> None:
        for call in self.of(ast.Call):
            func = call.func
            if isinstance(func, ast.Name) and func.id == "type":
                plain = len(call.args) == 1 and not call.keywords and not isinstance(call.args[0], ast.Starred)
                if not plain:
                    self.add("banned-call", "type() is only allowed with one argument", call)
            if isinstance(func, ast.Attribute) and func.attr in _STRING_DISPATCH_METHODS:
                for argument in [*call.args, *[keyword.value for keyword in call.keywords]]:
                    for constant in ast.walk(argument):
                        if isinstance(constant, ast.Constant) and isinstance(constant.value, str):
                            self._check_dispatch_name(constant.value, func.attr, constant)

    def _check_dispatch_name(self, name: str, method: str, node: ast.AST) -> None:
        """`df.agg("to_csv")` reaches the method by `getattr`: the name is checked as if written."""
        if name in BANNED_NAMES or name in BANNED_ATTRIBUTES or name in BANNED_IO or _BANNED_IO_PATTERN.match(name):
            self.add("banned-call", f"'{name}' is not allowed as a method name in .{method}()", node)

    def _check_statements(self) -> None:
        for node_type, label in _BANNED_STATEMENTS.items():
            for node in self.by_type[node_type]:
                self.add("banned-statement", f"{label} is not allowed", node)
        for comprehension in self.of(ast.comprehension):
            if comprehension.is_async:
                self.add("banned-statement", "async comprehension is not allowed", comprehension)

    def _check_strings(self) -> None:
        for constant in self.of(ast.Constant):
            text = _text(constant)
            if text is None:
                continue
            if len(text) > MAX_STRING_CHARS:
                message = f"string literal is {len(text):,} characters; the limit is {MAX_STRING_CHARS}"
                self.add("string-length", message, constant)
            if _DUNDER_IN_TEXT.search(text):
                self.add("dunder", "string literal contains a dunder identifier", constant)
            if _URL_IN_TEXT.search(text):
                self.add("url-literal", "string literal contains a URL or a file:/data: scheme", constant)

    def _check_savefig(self) -> None:
        found = False
        for call in self.of(ast.Call):
            func = call.func
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            else:
                continue
            if name != "savefig":
                continue
            found = True
            target = call.args[0] if call.args else next((k.value for k in call.keywords if k.arg == "fname"), None)
            if target is None or not _is_theme_target(target):
                self.add("savefig-target", 'savefig target must be exactly f"plot-{THEME}.png"', call)
        if not found:
            self.add("savefig-target", "no savefig call found", None)

    # -- ADAPTATION ----------------------------------------------------------------------

    def adaptation(self, original_palette: list[str]) -> None:
        self._check_placeholder()
        self._check_rng()
        self._check_literal_data()
        self._check_palette(original_palette)

    def _check_placeholder(self) -> None:
        count = sum(1 for assign in self.of(ast.Assign) if _is_placeholder(assign))
        if count != 1:
            self.add("placeholder-count", f"expected exactly one '{PLACEHOLDER}' statement, found {count}", None)
        for name in self.of(ast.Name):
            if name.id != "load_user_data":
                continue
            call = self.parents.get(name)
            if not (isinstance(call, ast.Call) and call.func is name and _is_placeholder(self.parents.get(call))):
                self.add("placeholder-use", f"'load_user_data' is only allowed in the statement '{PLACEHOLDER}'", name)

    def _check_rng(self) -> None:
        for call in self.of(ast.Call):
            path = self.resolve(call.func)
            if path == _RNG_FACTORY:
                self._check_default_rng(call)
            elif path is not None and (
                path.startswith("numpy.random.") or path == "random" or path.startswith("random.")
            ):
                self.add("rng", f"random data generation '{_snippet(call.func)}' is not allowed", call)
        for attribute in self.of(ast.Attribute):
            if attribute.attr == "rvs":
                self.add("rng", f"random sampling '{_snippet(attribute)}' is not allowed", attribute)

    def _check_default_rng(self, call: ast.Call) -> None:
        """The one allowance: a seeded generator used for jitter and subsampling only."""
        seed = call.args[0] if len(call.args) == 1 and not call.keywords else None
        if not call.args and len(call.keywords) == 1 and call.keywords[0].arg == "seed":
            seed = call.keywords[0].value
        if not (isinstance(seed, ast.Constant) and type(seed.value) is int):
            self.add("rng", "np.random.default_rng must be seeded with an int literal", call)
            return
        if self._is_call_receiver(call, _RNG_ALLOWED_METHODS):
            return
        parent = self.parents.get(call)
        target = _single_name_target(parent) if parent is not None else None
        if target is None:
            message = f"the seeded generator may only be bound to a name or used inline for {_RNG_ALLOWED_TEXT}(...)"
            self.add("rng", message, call)
            return
        name = target.id
        uses = [node for node in self.of(ast.Name) if node.id == name]
        stores = sum(1 for node in uses if not isinstance(node.ctx, ast.Load))
        stores += sum(1 for parameter in self.of(ast.arg) if parameter.arg == name)
        if stores != 1:
            self.add("rng", f"'{name}' must be bound exactly once, to the seeded generator", call)
        for use in uses:
            if isinstance(use.ctx, ast.Load) and not self._is_call_receiver(use, _RNG_ALLOWED_METHODS):
                self.add("rng", f"'{name}' may only be used as {name}{_RNG_ALLOWED_TEXT}(...)", use)

    def _check_literal_data(self) -> None:
        for node_type in (ast.List, ast.Tuple, ast.Set):
            for literal in self.by_type[node_type]:
                if isinstance(self.parents.get(literal), ast.List | ast.Tuple | ast.Set):
                    continue  # counted at the outermost container
                count = _numeric_leaves(literal)
                if count > MAX_LITERAL_NUMBERS:
                    message = (
                        f"literal with {count} numeric values; the limit is {MAX_LITERAL_NUMBERS}, data comes from df"
                    )
                    self.add("literal-data", message, literal)

    def _check_palette(self, original_palette: list[str]) -> None:
        original = [_hex(colour) for colour in original_palette]
        extension = [colour for colour in IMPRINT if _hex(colour) not in set(original)]
        statements: list[ast.Assign | ast.AnnAssign] = [*self.of(ast.Assign), *self.of(ast.AnnAssign)]
        for statement in statements:
            target = _single_name_target(statement)
            if target is None or target.id not in _PALETTE_NAMES:
                continue
            value = statement.value
            if not isinstance(value, ast.List | ast.Tuple) or not all(
                isinstance(element, ast.Constant) and isinstance(element.value, str) for element in value.elts
            ):
                self.add("palette-prefix", f"{target.id} must be a list of colour string literals", statement)
                continue
            entries = [
                _hex(element.value)
                for element in value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            ]
            if entries[: len(original)] != original:
                message = f"{target.id} must keep the {len(original)} original palette entries in order"
                self.add("palette-prefix", message, statement)
            elif entries[len(original) :] != extension[: len(entries) - len(original)]:
                next_positions = ", ".join(extension[:3]) or "none left"
                message = f"{target.id} may only be extended with the next Imprint positions ({next_positions})"
                self.add("palette-prefix", message, statement)
