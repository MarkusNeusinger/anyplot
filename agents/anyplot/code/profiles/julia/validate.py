"""Two-profile validator of the Julia (Makie) code profile, over tree-sitter.

The Julia counterpart of `profiles/r/validate.py`, with the same `Finding` and, where a
rule has a Python or R twin, the same rule id. `validate_security` runs on the normalised
catalogue original (eligibility) and on every adapted working form; `validate_adaptation`
on adapted code only. Both return an empty list for valid code and never raise: oversize
code, text that is not UTF-8, code tree-sitter cannot read and a string Julia would
refuse are findings.

**Threat model.** The rules are hygiene, not the boundary (second opinions of 2026-10-24
and 2026-10-29, `agentic/specs/261024-agent-all-libraries.md`): the sandbox (gVisor, no
egress, a read-only root) and the exec filter (`agents/renderer/execdeny/`, preloaded
into Julia's launcher, which kills any process start) protect the service; this list
keeps the exported `plot.jl`, which runs unguarded on the user's machine, free of the
model's accidental file, network and process access, and makes the adapter's output
boring. Julia reaches any function from a symbol or a module in many ways; the rules
refuse by shape, as R's do, and the named bypasses of the design passes are tests.

SECURITY rules (rule ids in parentheses):

* **Denied names** (`banned-name`): `DENIED_NAMES` and the families of `DENIED_PATTERN`
  (`unsafe_*`, `redirect_*`), refused as any identifier: a callee, a value handed on
  (`map(run, cmds)`), a binding, and the member after a `.` on a module or on any value
  (`Base.run`, `x.Base.run`), because a property chain can reach a module at run time.
  The list holds process starts (`run`, `pipeline`, `Cmd`, `success`, `detach`, the
  environment helpers `withenv`, `setenv`, `addenv`), the environment itself (`ENV`,
  except in the theme statement), file and stream I/O (`open` in any mode, `read`,
  `write`, `readlines`, `eachline`, `rm`, `cp`, `mv`, `touch`, `mkdir`, `mkpath`,
  `mktemp`, `mktempdir`, `tempname`, `cd`, `readdir`, `walkdir`, `symlink`, `hardlink`,
  `chmod`, `chown`, `download`, the file tests), the modules that reach the system
  (`Filesystem`, `Libc`, `Sys`, `Libdl`, `Downloads`, `Sockets`, `Core`, `Main`, `Meta`,
  `MainInclude`, `Docs`, `InteractiveUtils`), evaluation and loading (`eval`, `evalfile`,
  `include`, `include_string`, `require`, `invokelatest`), reflection that turns a symbol
  or a type into a function or a module (`getfield`, `getproperty`, `setfield!`,
  `setproperty!`, `getglobal`, `setglobal!`, `parentmodule`, `module` as a member,
  `which`, `methods`), native code (`ccall`, `cglobal`, `llvmcall`, `pointer`), and the
  outputs besides the protected save (`display`, which opens a viewer, `record`, `load`).
  `getfield` and friends are refused on any value, a superset of "on modules": no
  catalogue file calls them. A name that is a keyword argument's or a named tuple field's
  name (`f(; read = 1)`), and a quoted symbol (`:open`), is no lookup and passes. One
  exception keeps a catalogue file eligible: a lowercase denied name the file makes its own
  variable, bound once by a top-level `name = value` that is no function, before any other
  mention (histogram-capability's `cp`, the process capability index), may be read; Julia
  then resolves it to the variable, never to `Base`'s function, and calling it stays refused.
* **Modules** (`banned-name`): a package or `Base` is only ever the prefix of a member
  (`Random.seed!`), never a value (`getfield(Base, :run)`, `m = Base`) or a binding.
* **Packages** (`banned-import`): `using` and `import` load only `PACKAGES` (the project's
  plotting packages and the standard libraries the catalogue uses) or a dataset package
  (`DATASET_PACKAGES`, RDatasets and PalmerPenguins, which ADAPTATION refuses instead);
  never `CSV` or `TimeZones`, which only the loader uses, and never under another name
  (`import X as Y`, `using X: y as z`) or relative to a module (`using .X`).
* **Callees and macros** (`banned-call`): a call names its function: a name, an operator,
  `Module.name` over a package or `Base`, or a type (`Vector{Float64}(undef, n)`).
  Refused callees: a parenthesised value (`(f)(x)`, a function literal called at once,
  `(f ∘ g)(x)`), an index (`fs[1](x)`), a field of a value (`x.f(...)`), a `var"..."` name
  and a call's result unless the call is a builder of `CALLABLE_FACTORIES` (`cgrad`,
  `Base.Fix1`, ...; 0 catalogue callees are call results, 2026-10-29). Broadcast calls
  (`f.(x)`) take the same rules. A macro is one of `MACROS` (`@.`, `@sprintf`,
  `@recipe`, ...; never `@eval`, `@cmd`, `@ccall`, `@cfunction`, `@generated`,
  `@__DIR__`); a string macro one of `STRING_MACROS` (`colorant"..."` in 4,089 catalogue
  places, `L"..."` without LaTeXStrings' `%$` interpolation, `dateformat`, `r`, `raw`); a
  command literal (`` `ls` ``, `cmd"..."`) is refused. String interpolation (`"$(...)"`)
  is code: it is walked with every rule, because it runs when the string is built.
* **Statements** (`banned-statement`): no `macro` and no `module` definition.
* **The save and its names** (`savefig-target`): exactly one protected save (`regions.py`),
  `save("plot-$(THEME).png", fig; px_per_unit = 2)` with the figure as a name and
  `px_per_unit` the only keyword; any other `save` call or use is refused. THEME is bound
  only by its theme statement, `save` and `get` are never bound (also not as methods of
  `Base`), a theme token only by its own statement, and each protected statement (theme,
  tokens, palette, placeholder, save) has its lines to itself (`banned-statement`), so
  `THEME = get(...); THEME = "dark"` is refused.
* **Literals**: no URL (`url-literal`, the Python profile's pattern) and no string over
  `MAX_STRING_CHARS` characters (`string-length`).

What still passes, honestly: Julia's `Base` holds internals this list does not name, and a
method added to a `Base` function changes what the plot's calls do. Neither starts a
process or touches a file without a name above; the sandbox and the exec filter contain
what slips through, and the check stays hygiene for the exported `plot.jl`.

ADAPTATION rules, with the Python profile's ids: exactly one top-level
`df = load_user_data()` (`placeholder-count`) and `load_user_data` nowhere else
(`placeholder-use`); no random draws that fabricate data (`rng`: `randn`, `randexp` and
their `!` forms; `rand`, `shuffle`, `randperm` and `Random.seed!` stay allowed for jitter
and subsampling, as R's `runif` and `sample`); no data from memory (`literal-data`: a
vector or matrix literal with more than `MAX_LITERAL_NUMBERS` numbers;
`dataset-package`: loading or calling RDatasets or PalmerPenguins, owner decision of
2026-10-29); the palette prefix kept (`palette-prefix`: `IMPRINT_PALETTE` or `IMPRINT`
assigned once, as a vector of colour literals that keeps the original entries in order
and adds only the next Imprint positions, and never stored into or changed by a mutating
call such as `push!(IMPRINT_PALETTE, ...)`).

Messages never echo string contents, at most `MAX_SNIPPET_CHARS` of code. Findings are
sorted by line.
"""

import re
from collections import Counter

from tree_sitter import Node

from core.palette import IMPRINT

from ....schemas import MAX_CODE_CHARS
from ...treesitter import (
    COMMENTS,
    JL_STRINGS,
    Source,
    Span,
    Visit,
    first_line,
    jl_arguments,
    jl_assignment,
    jl_bindings,
    jl_callee,
    jl_macro_name,
    jl_macro_string,
    jl_named,
    jl_number,
    jl_root,
    jl_string,
    jl_unwrap,
    last_line,
    syntax_problems,
    visits,
)
from ...validate import MAX_LITERAL_NUMBERS, MAX_MESSAGE_CHARS, MAX_STRING_CHARS, Finding
from .coupling import DATASET_PACKAGES, base_name, loaded_packages
from .regions import (
    BINDING_WRAPPERS,
    ENV_NAME,
    IMPRINT_NAMES,
    PLACEHOLDER,
    PLACEHOLDER_FUNC,
    SAVE_KEYWORDS,
    SAVE_NAME,
    SAVE_NAMES,
    STANDARD_TARGET,
    THEME_NAME,
    THEME_STATEMENT,
    Regions,
    colour_value,
    find_regions,
    is_placeholder,
)


MAX_SNIPPET_CHARS = 60

PACKAGES = frozenset(
    {
        "CairoMakie",
        "Makie",
        "Colors",
        "ColorSchemes",
        "DataFrames",
        "Random",
        "Statistics",
        "Dates",
        "Printf",
        "LinearAlgebra",
    }
)
"""What `using` and `import` may load: the plotting packages of the project (`Project.toml`) and the standard libraries
the catalogue uses (2026-10-29: CairoMakie in 325 files, Colors 321, Random 260, Statistics 73, Dates 17, ColorSchemes
14, Printf 12, LinearAlgebra 8, Makie 4, DataFrames 2)."""
LOADER_PACKAGES = frozenset({"CSV", "TimeZones"})
"""The packages only the loader uses (`loader.py`): the plot code reads `df`, never a file."""
MODULE_ROOTS = PACKAGES | DATASET_PACKAGES | frozenset({"Base", "Iterators"})
"""The names a dotted callee or member may start with (`Random.seed!`, `Base.Fix2`, `Iterators.flatten`)."""
LOGGED_PACKAGES = (
    MODULE_ROOTS
    | LOADER_PACKAGES
    | frozenset(
        {
            "Core",
            "Main",
            "Downloads",
            "Sockets",
            "Distributed",
            "Libdl",
            "Mmap",
            "Pkg",
            "InteractiveUtils",
            "Serialization",
            "PNGFiles",
            "FileIO",
            "QRCoders",
            "GLMakie",
            "WGLMakie",
            "Plots",
            "NetworkLayout",
            "REPL",
            "Logging",
            "FileWatching",
            "SharedArrays",
            "Profile",
            "Test",
        }
    )
)
"""The closed vocabulary a `banned-import` finding's `module` label comes from (`?` for any other package), so the
attribution log never records a name the model made up."""
UNKNOWN_PACKAGE = "?"

DENIED_NAMES = frozenset(
    {
        # processes and the environment
        "run",
        "pipeline",
        "Cmd",
        "success",
        "detach",
        "setenv",
        "addenv",
        "withenv",
        "ignorestatus",
        "kill",
        "process_running",
        "process_exited",
        "cmd_gen",
        "julia_cmd",
        "runtests",
        "compilecache",
        ENV_NAME,
        # files, streams and the network
        "open",
        "read",
        "read!",
        "readbytes!",
        "readchomp",
        "readline",
        "readlines",
        "readuntil",
        "readavailable",
        "eachline",
        "write",
        "rm",
        "cp",
        "mv",
        "rename",
        "touch",
        "mkdir",
        "mkpath",
        "mktemp",
        "mktempdir",
        "tempname",
        "tempdir",
        "cd",
        "pwd",
        "homedir",
        "readdir",
        "walkdir",
        "symlink",
        "hardlink",
        "readlink",
        "chmod",
        "chown",
        "stat",
        "lstat",
        "isfile",
        "isdir",
        "ispath",
        "islink",
        "filesize",
        "mtime",
        "sendfile",
        "cptree",
        "download",
        "connect",
        "listen",
        "accept",
        # modules that reach the system, the runtime or evaluation
        "Filesystem",
        "Libc",
        "Sys",
        "Libdl",
        "Mmap",
        "Downloads",
        "Sockets",
        "Distributed",
        "Core",
        "Main",
        "Meta",
        "MainInclude",
        "Docs",
        "InteractiveUtils",
        "Threads",
        # evaluation, loading and reflection
        "eval",
        "evalfile",
        "include",
        "include_string",
        "include_dependency",
        "require",
        "invokelatest",
        "invoke_in_world",
        "getfield",
        "getproperty",
        "setfield!",
        "setproperty!",
        "getglobal",
        "setglobal!",
        "parentmodule",
        "moduleroot",
        "module",
        "which",
        "methods",
        "edit",
        "less",
        "clipboard",
        # native code
        "ccall",
        "cglobal",
        "llvmcall",
        "Intrinsics",
        "pointer",
        "pointer_from_objref",
        # outputs besides the protected save
        "display",
        "record",
        "load",
    }
)
"""Names Julia code may not use (module docstring, "Denied names")."""
DENIED_PATTERN = re.compile(r"^(?:unsafe_|redirect_)")
MACROS = frozenset(
    {
        "@.",
        "@__dot__",
        "@sprintf",
        "@printf",
        "@recipe",
        "@extract",
        "@lift",
        "@warn",
        "@info",
        "@debug",
        "@assert",
        "@views",
        "@view",
        "@inbounds",
        "@kwdef",
        "@enum",
    }
)
"""The macros plot code may call: broadcasting, formatting, Makie's recipes and observables, logging, assertions and
array views (the catalogue's: `@.` 23, `@sprintf` 19, `@recipe` 6, `@extract` 1, `@warn` 1; `@__DIR__` 4, which the
normaliser removes)."""
STRING_MACROS = frozenset({"colorant", "L", "dateformat", "r", "raw"})
"""The string macros plot code may use: Colors' `colorant`, Makie's `L` (LaTeX), Dates' `dateformat`, and Base's `r`
(a regex) and `raw`; none runs code from its text (`L"%$(...)"`, LaTeXStrings' interpolation, is refused)."""
LATEX_INTERPOLATION = "%$"
CALLABLE_FACTORIES = frozenset({"cgrad", "Fix1", "Fix2", "Returns", "ComposedFunction"})
"""Builders whose result a call may call at once (`Base.Fix2(÷, 2)(x)`); any other call as a callee is refused,
because `identity(f)(x)` would call whatever function a value holds."""
PROTECTED_NAMES = frozenset({SAVE_NAME, "get"})
"""Names the save statement and the theme statement call: never bound by the code, also not as a `Base` method."""

RNG_DRAWS = frozenset({"randn", "randn!", "randexp", "randexp!"})
"""Random draws that fabricate data; `rand`, `shuffle`, `randperm` and `Random.seed!` stay allowed for jitter and
subsampling (R's precedent, owner 2026-10-29)."""

_URL_IN_TEXT = re.compile(r"(?i)(?:https?|ftp)://|\b(?:file|data):\S")
"""The Python profile's URL rule (`validate._URL_IN_TEXT`)."""
_HEX = re.compile(r"#[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?")
_WHITESPACE = re.compile(r"\s+")
_IMPORTS = frozenset({"using_statement", "import_statement"})
_CALLS = frozenset({"call_expression", "broadcast_call_expression"})
_STATEMENT_PARENTS = frozenset({"source_file", "block"})
OWN_VARIABLE = re.compile(r"[a-z][a-z0-9_]*")
"""The shape of a denied name the file may make its own variable: a lowercase word (`cp`), never a module, `ENV` or a
mutating function (`read!`)."""


def denied(name: str) -> bool:
    """Whether Julia code may not use `name` (module docstring, "Denied names")."""
    return name in DENIED_NAMES or DENIED_PATTERN.match(name) is not None


def validate_security(code: str) -> list[Finding]:
    """The SECURITY profile (module docstring); never raises."""
    source, findings = _parse(code)
    if source is None:
        return findings
    scan = _Scan(source)
    scan.security()
    return scan.result()


def validate_adaptation(code: str, *, original_palette: list[str]) -> list[Finding]:
    """The ADAPTATION profile: one placeholder, no fabricated data, the palette prefix kept."""
    source, findings = _parse(code)
    if source is None:
        return findings
    scan = _Scan(source)
    scan.adaptation(original_palette)
    return scan.result()


def _parse(code: str) -> tuple[Source | None, list[Finding]]:
    """Size, encoding and syntax: the checks that run before any rule can."""
    if len(code) > MAX_CODE_CHARS:
        return None, [Finding("size", f"code is {len(code):,} characters; the limit is {MAX_CODE_CHARS:,}", None)]
    try:
        code.encode("utf-8")
    except UnicodeEncodeError:
        return None, [Finding("encoding", "code is not valid UTF-8 text", None)]
    source = Source(code, "julia")
    problems = syntax_problems(source.tree, limit=1)
    if problems:
        return None, [Finding("syntax", f"syntax error: {problems[0].message()}", problems[0].line)]
    return source, []


def _snippet(source: Source, node: Node) -> str:
    """At most `MAX_SNIPPET_CHARS` of a node's code on one line, its string literals shown as `"..."`."""
    data = source.data
    parts: list[str] = []
    cursor = node.start_byte
    stack = [node]
    while stack:
        current = stack.pop()
        if current.type in JL_STRINGS:
            parts.append(data[cursor : current.start_byte].decode("utf-8", "replace") + '"..."')
            cursor = current.end_byte
            continue
        stack.extend(reversed(current.children))
    parts.append(data[cursor : node.end_byte].decode("utf-8", "replace"))
    text = _WHITESPACE.sub(" ", "".join(parts)).strip()
    return text if len(text) <= MAX_SNIPPET_CHARS else text[: MAX_SNIPPET_CHARS - 3] + "..."


def string_text(source: Source, node: Node) -> str:
    """A string literal's value when it has one, else the text of its literal parts (an interpolated or triple-quoted
    string): what a URL or length check reads."""
    value = jl_string(source, node)
    if value is not None:
        return value
    return "".join(source.text(child) for child in node.children if child.type in ("content", "escape_sequence"))


class _Scan:
    """One validation pass over a parsed Julia source."""

    def __init__(self, source: Source) -> None:
        self.source = source
        self.findings: list[Finding] = []
        self.visits = list(visits(source.root))
        self.regions: Regions = find_regions(source)
        self.bindings: dict[str, list[Node]] = {}
        for name, node in jl_bindings(source, source.root):
            self.bindings.setdefault(name, []).append(node)
        theme = self.regions.theme
        self.theme_chars = (theme.statement.start, theme.statement.end) if theme and theme.statement else None
        self.own_variables = self.find_own_variables()

    def find_own_variables(self) -> frozenset[str]:
        """Denied function names the file makes its own variable: bound once, by a top-level `name = value` that is
        no function, before any other mention of the name (histogram-capability's `cp`, the process capability index).

        Julia then resolves every later mention to the variable, not to `Base`'s function, so
        reading it passes; calling it stays refused (`check_identifier`).
        """
        own: set[str] = set()
        for name, nodes in self.bindings.items():
            if not denied(name) or OWN_VARIABLE.fullmatch(name) is None or len(nodes) != 1:
                continue
            node = nodes[0]
            statement = node.parent if node.parent is not None and node.parent.type in BINDING_WRAPPERS else node
            if statement.parent is None or statement.parent.type != "source_file":
                continue
            assignment = jl_assignment(self.source, node)
            if (
                assignment is None
                or assignment.operator != "="
                or assignment.target.type != "identifier"
                or assignment.function
                or jl_unwrap(assignment.value).type in ("arrow_function_expression", "function_definition")
            ):
                continue
            first = next(
                visit.node
                for visit in self.visits
                if visit.node.type == "identifier" and self.source.text(visit.node) == name
            )
            if first.id == assignment.target.id:
                own.add(name)
        return frozenset(own)

    # -- bookkeeping ---------------------------------------------------------------------

    def add(self, rule: str, message: str, node: Node | None, *, module: str | None = None) -> None:
        line = first_line(node) if node is not None else None
        self.findings.append(Finding(rule, message[:MAX_MESSAGE_CHARS], line, module))

    def result(self) -> list[Finding]:
        unique = dict.fromkeys(self.findings)
        return sorted(unique, key=lambda f: (f.line is None, f.line or 0, f.rule, f.message))

    def within(self, node: Node, span: Span | None) -> bool:
        """Whether `node` starts inside the exact characters of `span`."""
        return span is not None and span.start <= self.source.char(node.start_byte) < span.end

    def in_theme_statement(self, node: Node) -> bool:
        if self.theme_chars is None:
            return False
        return self.theme_chars[0] <= self.source.char(node.start_byte) < self.theme_chars[1]

    def snippet(self, node: Node) -> str:
        return _snippet(self.source, node)

    # -- SECURITY ------------------------------------------------------------------------

    def security(self) -> None:
        for visit in self.visits:
            node = visit.node
            kind = node.type
            if kind == "identifier":
                self.check_identifier(visit)
            elif kind in ("call_expression", "broadcast_call_expression"):
                self.check_call(node)
            elif kind == "macrocall_expression":
                self.check_macro(node)
            elif kind in ("prefixed_string_literal", "prefixed_command_literal"):
                self.check_string_macro(node)
            elif kind == "command_literal":
                self.add("banned-call", "a command literal starts a process; the plot runs none", node)
            elif kind in _IMPORTS:
                self.check_import(node)
            elif kind in ("macro_definition", "module_definition"):
                what = "a macro" if kind == "macro_definition" else "a module"
                self.add("banned-statement", f"{what} definition is not allowed; write plain functions", node)
            if kind == "string_literal":
                self.check_string(node)
        self.check_save()
        self.check_bindings()

    def name_position(self, visit: Visit) -> str:
        """Where an identifier stands: `skip` (checked by another rule or no lookup), `member` (after a `.`),
        `module-root` (before a `.`) or `lookup`."""
        node, parent = visit.node, visit.parent
        if parent is None:
            return "skip"
        ptype = parent.type
        if ptype in ("macro_identifier", "selected_import", "import_path", "import_alias") or ptype in _IMPORTS:
            return "skip"
        if ptype in ("prefixed_string_literal", "prefixed_command_literal") and visit.field == "prefix":
            return "skip"
        if ptype == "quote_expression" and len(jl_named(parent)) == 1:
            holder = parent.parent
            if holder is not None and holder.type == "field_expression" and jl_named(holder)[-1].id == parent.id:
                return "member"  # `Base.:run` names the member run
            return "skip"  # `:open` is a symbol, no lookup
        if ptype == "field_expression":
            named = jl_named(parent)
            if named and named[0].id == node.id:
                return "module-root"
            return "member"
        if ptype == "assignment" and parent.parent is not None:
            named = jl_named(parent)
            container = parent.parent.type
            if named and named[0].id == node.id and container in ("argument_list", "tuple_expression"):
                return "skip"  # a keyword argument's or a named tuple field's name
        return "lookup"  # `f(; k)` passes the variable k: a lookup like any other

    def check_identifier(self, visit: Visit) -> None:
        node = visit.node
        position = self.name_position(visit)
        if position == "skip":
            return
        name = self.source.text(node)
        if position == "module-root":
            if name in MODULE_ROOTS and self.dataset_member(visit):
                return
        if name == ENV_NAME and self.in_theme_statement(node):
            return
        called = node if position == "lookup" else visit.parent
        holder = called.parent if called is not None else None
        callee = (
            holder is not None and called is not None and holder.type in _CALLS and holder.children[0].id == called.id
        )
        if name in self.own_variables and position == "lookup" and not callee:
            return  # the file's own variable (`find_own_variables`)
        if name == SAVE_NAME and position in ("lookup", "member") and not callee:
            self.add("savefig-target", "save is only ever called where it is named, as the final save", node)
        if denied(name):
            if position == "member" and self.dataset_member(visit):
                return  # `PalmerPenguins.load()`: the ADAPTATION rule dataset-package refuses it
            self.add("banned-name", f"'{name}' is not allowed: {self.reason(name)}", node)
            return
        if name in MODULE_ROOTS and position == "lookup":
            self.add("banned-name", f"the package '{name}' is only ever a prefix, as in {name}.name", node)

    def dataset_member(self, visit: Visit) -> bool:
        """Whether an identifier is part of `RDatasets.x` or `PalmerPenguins.x`."""
        parent = visit.parent
        if parent is None or parent.type != "field_expression":
            return False
        root = jl_root(parent)
        return root.type == "identifier" and self.source.text(root) in DATASET_PACKAGES

    def reason(self, name: str) -> str:
        if name == ENV_NAME:
            return f"the environment is read only by {THEME_STATEMENT}"
        if name in ("display", "record", "load"):
            return "the plot is written only by the final save"
        return "the plot reads only df and writes only through the final save, without files, processes or eval"

    def check_call(self, node: Node) -> None:
        function = node.children[0] if node.children else None
        if function is None:
            return
        unwrapped = jl_unwrap(function)
        kind = unwrapped.type
        if function.type == "parenthesized_expression":
            self.add("banned-call", f"a computed function '{self.snippet(function)}'; name the function", node)
        elif kind == "index_expression":
            message = f"a function taken out of a value '{self.snippet(function)}'; call it by name"
            self.add("banned-call", message, node)
        elif kind == "field_expression":
            root = jl_root(unwrapped)
            if not (root.type == "identifier" and self.source.text(root) in LOGGED_PACKAGES):
                message = f"a function taken out of a value '{self.snippet(function)}'; call it by name"
                self.add("banned-call", message, node)
        elif kind in ("call_expression", "broadcast_call_expression"):
            if base_name(jl_callee(self.source, unwrapped)) not in CALLABLE_FACTORIES:
                message = f"the result of '{self.snippet(unwrapped)}' called at once; call a named function"
                self.add("banned-call", message, node)
        elif kind in ("prefixed_string_literal",):
            self.add("banned-name", 'a var"..." name makes a name from a string; write the name', node)
        elif kind not in ("identifier", "operator", "parametrized_type_expression", "curly_expression"):
            self.add("banned-call", f"a computed function '{self.snippet(function)}'; name the function", node)
        name = jl_callee(self.source, node)
        if name in SAVE_NAMES or base_name(name) == SAVE_NAME:
            if not self.is_protected_save(node):
                self.add("savefig-target", "the plot is saved only by the final save", node)

    def check_macro(self, node: Node) -> None:
        name = jl_macro_name(self.source, node)
        if name is None:
            self.add("banned-call", "a macro whose name is computed is not allowed", node)
            return
        module, separator, own = name.rpartition(".@")
        own = f"@{own}" if separator else name
        if own not in MACROS or (module and module not in MODULE_ROOTS):
            allowed = ", ".join(sorted(MACROS))
            self.add("banned-call", f"the macro {name} is not allowed; only {allowed}", node)

    def check_string_macro(self, node: Node) -> None:
        if node.type == "prefixed_command_literal":
            self.add("banned-call", "a command literal starts a process; the plot runs none", node)
            return
        found = jl_macro_string(self.source, node)
        prefix = found[0] if found is not None else None
        if prefix == "var":
            self.add("banned-name", 'a var"..." name makes a name from a string; write the name', node)
        elif prefix not in STRING_MACROS:
            allowed = ", ".join(f'{macro}"..."' for macro in sorted(STRING_MACROS))
            self.add("banned-call", f'string macro {prefix or "?"}"..." is not allowed; only {allowed}', node)
        elif prefix == "L" and found is not None and LATEX_INTERPOLATION in found[1]:
            self.add("banned-call", 'L"..." interpolates code after %$; write the text out', node)
        if found is not None:
            if len(found[1]) > MAX_STRING_CHARS:
                message = f"string literal of {len(found[1])} characters; the limit is {MAX_STRING_CHARS}"
                self.add("string-length", message, node)
            if _URL_IN_TEXT.search(found[1]):
                self.add("url-literal", "URL or file literal; the plot reads only df", node)

    def check_import(self, node: Node) -> None:
        for child in jl_named(node):
            if child.type in COMMENTS:
                continue
            if child.type == "import_alias" or any(part.type == "import_alias" for part in jl_named(child)):
                self.add("banned-import", "a package or name under another name (as) is not allowed", node)
                continue
            text = self.source.text(child)
            if text.startswith("."):
                self.add("banned-import", "a relative using or import is not allowed", node)
                continue
        for package in loaded_packages(self.source, node):
            label = package if package in LOGGED_PACKAGES else UNKNOWN_PACKAGE
            if package in LOADER_PACKAGES:
                message = f"'{package}' is the loader's; the data comes from df = load_user_data()"
                self.add("banned-import", message, node, module=label)
            elif package not in PACKAGES and package not in DATASET_PACKAGES:
                allowed = ", ".join(sorted(PACKAGES))
                self.add("banned-import", f"package '{package}' is not available → use {allowed}", node, module=label)
        for child in jl_named(node):
            names = jl_named(child)[1:] if child.type == "selected_import" else []
            for name in names:
                text = self.source.text(name)
                if denied(text):
                    self.add("banned-name", f"'{text}' is not allowed: {self.reason(text)}", name)

    def check_string(self, node: Node) -> None:
        if self.in_theme_statement(node):
            return
        value = string_text(self.source, node)
        if len(value) > MAX_STRING_CHARS:
            self.add(
                "string-length", f"string literal of {len(value)} characters; the limit is {MAX_STRING_CHARS}", node
            )
        if _URL_IN_TEXT.search(value):
            self.add("url-literal", "URL or file literal; the plot reads only df", node)

    def is_protected_save(self, node: Node) -> bool:
        save = self.regions.save
        return save is not None and save.span.start == self.source.char(node.start_byte)

    def check_save(self) -> None:
        save = self.regions.save
        if save is None:
            self.add("savefig-target", f"no final top-level save({STANDARD_TARGET}, fig; px_per_unit = 2)", None)
            return
        call = next(
            (
                visit.node
                for visit in self.visits
                if visit.node.type == "call_expression" and self.is_protected_save(visit.node)
            ),
            None,
        )
        if not save.standard_target:
            self.add("savefig-target", f"the final save writes {STANDARD_TARGET}", call)
        if save.positional != 2 or save.splat or save.figure is None or not re.fullmatch(r"[A-Za-z_]\w*", save.figure):
            self.add("savefig-target", "the final save takes the target, the figure by its name and px_per_unit", call)
        unknown = sorted({name for name in save.keywords if name not in SAVE_KEYWORDS})
        if unknown:
            self.add("savefig-target", f"the final save takes only px_per_unit, not {', '.join(unknown)}", call)
        repeated = sorted(name for name, count in Counter(save.keywords).items() if count > 1)
        if repeated:
            self.add("savefig-target", f"the final save repeats {', '.join(repeated)}", call)

    def check_bindings(self) -> None:
        """THEME and each token bound by their own statement alone, the save's names never; by node, not by line."""
        theme = self.regions.theme
        if theme is None:
            self.add("savefig-target", f"no {THEME_STATEMENT} at the top level", None)
        for node in self.bindings.get(THEME_NAME, []):
            if theme is None or not self.within(node, theme.statement):
                message = f"THEME is bound only by {THEME_STATEMENT}: the save writes {STANDARD_TARGET}"
                self.add("savefig-target", message, node)
        for name, nodes in self.bindings.items():
            if base_name(name) in PROTECTED_NAMES:
                for node in nodes:
                    message = f"'{name}' may not be bound: the final save and THEME use it"
                    self.add("savefig-target", message, node)
            elif name in MODULE_ROOTS or name in LOADER_PACKAGES:
                for node in nodes:
                    if node.type not in _IMPORTS:
                        self.add("banned-name", f"'{name}' names a package and may not be bound", node)
        for token in self.regions.theme_tokens:
            for node in self.bindings.get(token.name, []):
                if not self.within(node, token.statement):
                    message = f"the theme token {token.name} is bound only by its own statement"
                    self.add("banned-statement", message, node)
        self.check_alone()

    def check_alone(self) -> None:
        """Every protected statement (theme, tokens, palette, placeholder, save) has its lines to itself.

        Another statement on the same line would ride inside the protected region: the edit
        applier protects whole lines, and the loader replaces only the placeholder statement,
        so `df = load_user_data(); df = sample` would keep the sample. A trailing comment is fine.
        """
        regions = self.regions
        protected: list[tuple[str, str, Span | None]] = []
        if regions.theme is not None:
            protected.append(("savefig-target", "the THEME statement", regions.theme.statement))
        protected += [
            ("banned-statement", f"the theme token {token.name}", token.statement) for token in regions.theme_tokens
        ]
        if regions.imprint is not None:
            protected.append(("banned-statement", f"the palette {regions.imprint.name}", regions.imprint.statement))
        protected += [("banned-statement", "the placeholder", region.statement) for region in regions.placeholders]
        if regions.save is not None and regions.save.statement is not None:
            protected.append(("savefig-target", "the final save", regions.save.span))
        statements = [
            visit.node
            for visit in self.visits
            if visit.parent is not None
            and visit.parent.type in _STATEMENT_PARENTS
            and visit.node.is_named
            and visit.node.type not in COMMENTS
        ]
        for rule, what, span in protected:
            if span is None:
                continue
            for node in statements:
                start, end = self.source.char(node.start_byte), self.source.char(node.end_byte)
                if start <= span.start < end or span.start <= start < span.end:
                    continue  # the statement itself, a statement around it (a function body) or one inside it
                if first_line(node) <= span.last_line and last_line(node) >= span.first_line:
                    self.add(rule, f"{what} shares its line with other code; give it lines of its own", node)
                    break

    # -- ADAPTATION ----------------------------------------------------------------------

    def adaptation(self, original_palette: list[str]) -> None:
        self.check_placeholder()
        self.check_rng()
        self.check_literal_data()
        self.check_dataset_packages()
        self.check_palette(original_palette)

    def check_placeholder(self) -> None:
        count = len(self.regions.placeholders)
        if count != 1:
            message = f"expected exactly one top-level '{PLACEHOLDER}' statement, found {count}"
            self.add("placeholder-count", message, None)
        for visit in self.visits:
            node = visit.node
            if node.type != "identifier" or self.source.text(node) != PLACEHOLDER_FUNC:
                continue
            call = visit.parent
            statement = call.parent if call is not None else None
            if not (
                call is not None
                and call.type == "call_expression"
                and call.children[0].id == node.id
                and statement is not None
                and statement.parent is not None
                and statement.parent.type == "source_file"
                and is_placeholder(self.source, statement)
            ):
                message = f"'{PLACEHOLDER_FUNC}' is only allowed in the top-level statement '{PLACEHOLDER}'"
                self.add("placeholder-use", message, node)

    def check_rng(self) -> None:
        for visit in self.visits:
            node = visit.node
            if node.type not in ("call_expression", "broadcast_call_expression"):
                continue
            name = jl_callee(self.source, node) or ""
            if base_name(name) in RNG_DRAWS:
                self.add("rng", f"random data generation '{name}' is not allowed; the data comes from df", node)

    def check_literal_data(self) -> None:
        for visit in self.visits:
            node = visit.node
            if node.type not in ("vector_expression", "matrix_expression"):
                continue
            if visit.parent is not None and visit.parent.type in ("vector_expression", "matrix_row"):
                continue  # counted at the outermost literal
            count = self.numbers_in(node)
            if count > MAX_LITERAL_NUMBERS:
                message = f"literal with {count} numeric values; the limit is {MAX_LITERAL_NUMBERS}, data comes from df"
                self.add("literal-data", message, node)

    def numbers_in(self, node: Node) -> int:
        count = 0
        stack = [node]
        while stack:
            current = stack.pop()
            for item in jl_named(current):
                item = jl_unwrap(item)
                if jl_number(self.source, item) is not None:
                    count += 1
                elif item.type in ("vector_expression", "matrix_expression", "matrix_row"):
                    stack.append(item)
        return count

    def check_dataset_packages(self) -> None:
        """`using RDatasets` or `PalmerPenguins.load()`: the sample data of a package, never the user's."""
        for visit in self.visits:
            node = visit.node
            packages: list[str] = []
            if node.type in _IMPORTS:
                packages = loaded_packages(self.source, node)
            elif node.type == "field_expression" and (visit.parent is None or visit.parent.type != "field_expression"):
                root = jl_root(node)
                packages = [self.source.text(root)] if root.type == "identifier" else []
            for package in packages:
                if package in DATASET_PACKAGES:
                    message = f"'{package}' is a dataset package; the data comes from df = load_user_data()"
                    self.add("dataset-package", message, node)

    def check_palette(self, original_palette: list[str]) -> None:
        original = [colour.upper() for colour in original_palette]
        extension = [colour.upper() for colour in IMPRINT if colour.upper() not in set(original)]
        for name in sorted(IMPRINT_NAMES):
            assigned = 0
            for node in self.bindings.get(name, []):
                assignment = jl_assignment(self.source, node) if node.type in ("assignment",) else None
                if (
                    assignment is None
                    or assignment.mutation
                    or assignment.operator != "="
                    or assignment.names != (name,)
                ):
                    self.add("palette-prefix", f"'{name}' holds the palette and may only be assigned plainly", node)
                    continue
                assigned += 1
                if assigned > 1:
                    self.add("palette-prefix", f"{name} is assigned again; keep one literal palette", node)
                    continue
                entries = self.palette_entries(assignment.value)
                if entries is None:
                    self.add("palette-prefix", f"{name} must be a vector of colour literals", node)
                elif entries[: len(original)] != original:
                    message = f"{name} must keep the {len(original)} original palette entries in order"
                    self.add("palette-prefix", message, node)
                elif len(entries) > len(original) + len(extension):
                    limit = len(original) + len(extension)
                    message = f"{name} has {len(entries)} entries, more than the {limit} colours the palette has"
                    self.add("palette-prefix", message, node)
                elif entries[len(original) :] != extension[: len(entries) - len(original)]:
                    next_positions = ", ".join(extension[:3]) or "none left"
                    message = f"{name} may only be extended with the next Imprint positions ({next_positions})"
                    self.add("palette-prefix", message, node)
        for visit in self.visits:
            node = visit.node
            if node.type not in ("call_expression", "broadcast_call_expression"):
                continue
            if not base_name(jl_callee(self.source, node)).endswith("!"):
                continue
            first = next((argument for argument in jl_arguments(self.source, node) if argument.position == 0), None)
            if first is not None and jl_unwrap(first.value).type == "identifier":
                target = self.source.text(jl_unwrap(first.value))
                if target in IMPRINT_NAMES:
                    self.add(
                        "palette-prefix", f"{target} is changed in place; extend the literal palette instead", node
                    )

    def palette_entries(self, value: Node) -> list[str] | None:
        node = jl_unwrap(value)
        if node.type != "vector_expression":
            return None
        entries: list[str] = []
        for item in jl_named(node):
            text = colour_value(self.source, item)
            if text is None or not _HEX.fullmatch(text):
                return None
            entries.append(text.upper())
        return entries
