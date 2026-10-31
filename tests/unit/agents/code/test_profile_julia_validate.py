"""Tests for agents/anyplot/code/profiles/julia/validate.py: the SECURITY and ADAPTATION profiles for Makie code.

The refused snippets are the named bypasses of the design passes (`agentic/specs/261024-agent-all-libraries.md`,
second opinions of 2026-10-24 and 2026-10-29) and the brief's list; each is refused by name or by shape.
"""

from collections import Counter

import pytest

from agents.anyplot.code.profiles.julia.normalise import normalise
from agents.anyplot.code.profiles.julia.regions import find_regions
from agents.anyplot.code.profiles.julia.validate import validate_adaptation, validate_security
from agents.anyplot.code.validate import Finding

from .conftest import JULIA_CATALOGUE_FILES, JULIA_CATALOGUE_NORMALISED, JULIA_WORKING, REPO_ROOT


HEAD = 'using CairoMakie\nconst THEME = get(ENV, "ANYPLOT_THEME", "light")\nfig = Figure(size = (1600, 900))\n'
SAVE = 'save("plot-$(THEME).png", fig; px_per_unit = 2)\n'
PALETTE = list(find_regions(JULIA_WORKING).imprint.entries)  # type: ignore[union-attr]


def security(body: str) -> list[Finding]:
    return validate_security(HEAD + body + "\n" + SAVE)


def rules(findings: list[Finding]) -> set[str]:
    return {finding.rule for finding in findings}


def test_the_working_form_in_miniature_passes_both_profiles() -> None:
    assert validate_security(JULIA_WORKING) == []
    assert validate_adaptation(JULIA_WORKING, original_palette=PALETTE) == []
    assert validate_security(JULIA_CATALOGUE_NORMALISED) == []


@pytest.mark.parametrize(
    "body",
    [
        # processes
        "run(`ls /`)",
        "x = `ls`",
        'p = pipeline(`ls`; stdout = "x.txt")',
        'c = Cmd(["ls", "/"])',
        '@cmd "ls"',
        'success(Cmd(["true"]))',
        "detach(c)",
        'withenv("A" => "1") do\n    nothing\nend',
        'c2 = setenv(c, "A" => "1")',
        'c3 = addenv(c, "A" => "1")',
        "runs = run.(cmds)",
        "f = run",
        "y = map(run, cmds)",
        # the environment
        'ENV["PATH"] = "/tmp"',
        'home = get(ENV, "HOME", "")',
        'delete!(ENV, "X")',
        # evaluation, loading and reflection
        "eval(:(x = 1))",
        "@eval x = 1",
        "Core.eval(Main, :(x = 1))",
        "Main.eval(:(x = 1))",
        "Base.eval(:(x = 1))",
        'include("other.jl")',
        'include_string(Main, "x = 1")',
        'Base.MainInclude.include("other.jl")',
        'e = Meta.parse("run(`ls`)")',
        "Base.require(Main, :Pkg)",
        "f = getfield(Base, :run)",
        'f = getfield(Base, Symbol("ru" * "n"))',
        "f = getproperty(Base, :run)",
        "setfield!(x, :a, 1)",
        "setproperty!(x, :a, 1)",
        "f = getglobal(Base, :run)",
        "setglobal!(Main, :THEME, 1)",
        "Base.invokelatest(f)",
        "invokelatest(f)",
        "m = Base",
        "f = Base.:run",
        "g = typeof(1).name.module",
        "h = x.Base.run",
        "k = parentmodule(sum)",
        # native code
        'ccall(:system, Int32, (Cstring,), "ls")',
        '@ccall system("ls"::Cstring)::Cint',
        "fp = @cfunction(f, Cint, ())",
        "p = cglobal(:jl_options)",
        "Core.Intrinsics.llvmcall(code, Int, Tuple{})",
        "v = unsafe_load(p)",
        "s = unsafe_string(p)",
        # definitions
        "macro m(x)\n    x\nend",
        "@generated function g(x)\n    x\nend",
        "module M\nend",
        # files and streams
        'open("x.txt", "w") do io\n    println(io, 1)\nend',
        'io = open("data.csv")',
        'write("x.txt", "a")',
        'text = read("data.csv", String)',
        'rows = readlines("data.csv")',
        'for row in eachline("data.csv")\nend',
        'rm("x")',
        'cp("a", "b")',
        'mv("a", "b")',
        'touch("x")',
        'mkdir("d")',
        'mkpath("d/e")',
        "p, io = mktemp()",
        "d = mktempdir()",
        "t = tempname()",
        'cd("/")',
        "files = readdir()",
        'for (r, ds, fs) in walkdir(".")\nend',
        'symlink("a", "b")',
        'hardlink("a", "b")',
        'chmod("x", 0o777)',
        'chown("x", 0)',
        "redirect_stdout(io)",
        'download("http://example.org")',
        'Base.Filesystem.rm("x")',
        "Libc.systemsleep(1)",
        'w = Sys.which("ls")',
        "Base.Sys.cpu_info()",
        "display(fig)",
        'record(fig, "x.mp4", 1:3) do i\nend',
        'img = load("x.png")',
        # computed callees
        "fs[1](x)",
        "x.f(1)",
        "(f)(1)",
        "(x -> x + 1)(2)",
        "identity(f)(1)",
        'Symbol("run")(1)',
        'var"run"(cmd)',
        "fs[1].(x)",
        "(f ∘ g)(x)",
        # string interpolation is code
        'label = "files: $(readdir())"',
        'label = "a $(open("x"))"',
        # string macros and commands
        'b = b"bytes"',
        'l = L"%$(run(c))"',
        'h = html"<b>x</b>"',
        # packages
        "using Downloads",
        "using Sockets",
        "using Distributed",
        "using Libdl",
        "using Mmap",
        "using Pkg",
        "using InteractiveUtils",
        "using Serialization",
        "using CSV",
        "import TimeZones",
        "import Dates as D",
        "using Dates: now as n",
        "using .Local",
        "import Base: run",
        "using Statistics: mean, open",
        # the save and the protected names
        'save("other.png", fig)',
        "map(save, figs)",
        'Makie.save("other.png", fig)',
        'THEME = "dark"',
        'get(a, b, c) = "dark"',
        'function get(a, b, c)\n    "dark"\nend',
        'Base.get(a::Dict, b, c) = "dark"',
        "save(args...) = nothing",
        "Random = 1",
        # literals
        'url = "https://example.org/data.csv"',
        'url = "//cdn.example.org/data.csv"',
        'big = "' + "x" * 201 + '"',
    ],
)
def test_refused(body: str) -> None:
    assert validate_security(HEAD + body + "\n" + SAVE) != [], body


@pytest.mark.parametrize(
    "body",
    [
        "using Random\nRandom.seed!(42)",
        'using Dates\nlabels = Dates.format.(dates, "u dd")',
        'using Printf\nlabel = @sprintf("%.1f", 2.5)',
        'c = colorant"#009E73"',
        'l = L"\\alpha^2"',
        "y = f.(x) .+ 1",
        "v = Float64.(x)",
        "m = Vector{Float64}(undef, 3)",
        "s = sort(xs; by = x -> x[2])",
        "ys = map(xs) do x\n    2x\nend",
        'n = get(counts, "k", 0)',
        "f(; read = 1)",
        "t = (open = 1, close = 2)",
        "align = (:left, :top)",
        "s = :open",
        "half = Base.Fix2(÷, 2)(10)",
        "flat = collect(Iterators.flatten(xs))",
        "using LinearAlgebra\nn = LinearAlgebra.norm(v)",
        'r = r"^[a-z]+$"',
        "cp = 1.33\nlabel = round(cp; digits = 2)",
        "z = @. x^2 + 1",
        'label = "n = $(length(xs))"',
        "x = 2.5f0",
        'quote_text = "say \\"hi\\""',
        "b = 1 // 2",
        "@assert length(xs) > 0",
        'g = cgrad([colorant"#009E73", colorant"#4467A3"])',
        "using DataFrames\ncol = df[!, COLUMN]",
    ],
)
def test_allowed(body: str) -> None:
    assert security(body) == [], body


@pytest.mark.parametrize(
    "body",
    [
        'cp = 1.33\ncp("a", "b")',
        "y = cp\ncp = 1.33",
        "cp = 1.33\ncp = 2.0",
        "function f()\n    cp = 1\nend",
        "cp = x -> x",
    ],
)
def test_a_denied_name_is_the_files_own_variable_only_when_bound_first_and_once(body: str) -> None:
    """histogram-capability's `cp` (the process capability index) is a variable: bound once at the top level before
    any other mention, it shadows Base's `cp`; anything else stays refused."""
    assert "banned-name" in rules(security(body)), body


def test_findings_name_the_rule_and_line_without_echoing_strings() -> None:
    findings = security('secret = "do not echo"\nrun(`ls`)')

    assert {(finding.rule, finding.line) for finding in findings} >= {("banned-call", 5), ("banned-name", 5)}
    assert all("do not echo" not in finding.message for finding in findings)


def test_the_import_label_is_a_closed_vocabulary() -> None:
    findings = security("using Downloads\nusing MadeUpPackage")

    assert sorted(finding.module or "" for finding in findings if finding.rule == "banned-import") == ["?", "Downloads"]


@pytest.mark.parametrize(
    ("body", "module"),
    [
        ('x = FileWatching.watch_file("data.csv")', "FileWatching"),
        ("w = FileWatching.watch_file", "FileWatching"),
        ("Logging.global_logger(logger)", "Logging"),
        ("REPL.x()", "REPL"),
        ("Test.@test x == 1", "Test"),
        ('Tar.extract("a.tar")', "Tar"),
        ('rows = CSV.read("data.csv", DataFrame)', "CSV"),
    ],
)
def test_a_dotted_name_starts_at_an_admitted_root(body: str, module: str) -> None:
    """Review of 2026-10-29: the callee rule accepted any root of the attribution vocabulary (`LOGGED_PACKAGES`), so
    `FileWatching.watch_file(...)` passed; a root comes from `MODULE_ROOTS` now, called or handed on."""
    findings = security(body)

    assert any(finding.rule == "banned-import" and finding.module == module for finding in findings), findings


def test_a_module_outside_the_roots_in_a_catalogue_file_is_refused() -> None:
    code = normalise((REPO_ROOT / "plots/scatter-basic/implementations/julia/makie.jl").read_text(encoding="utf-8"))
    assert validate_security(code) == []
    tampered = code.replace("# Regression line\n", '# Regression line\nx = FileWatching.watch_file("data.csv")\n')

    assert [(finding.rule, finding.module) for finding in validate_security(tampered)] == [
        ("banned-import", "FileWatching")
    ]


@pytest.mark.parametrize(
    ("body", "rule"),
    [
        ("using CairoMakie.Cairo", "banned-import"),
        ("using Makie.FileIO", "banned-import"),
        ("using Makie.GridLayoutBase", "banned-import"),
        ("import Makie.FileIO: load", "banned-import"),
        ("import Makie.FileIO: query", "banned-import"),
        ("import Base.Filesystem.rm", "banned-import"),
        ("using Statistics, Makie.FileIO", "banned-import"),
        ("import Makie.FileIO as F", "banned-import"),
        ("using ..Parent", "banned-import"),
        ("using .Local: helper", "banned-import"),
        ("using Base: run", "banned-name"),
        ("import Makie: FileIO", "banned-name"),
        ("import Makie: GridLayoutBase", "banned-name"),
        ("using Statistics: mean, open", "banned-name"),
        ("using Base: @eval", "banned-call"),
        ("import Base: +", "banned-import"),
    ],
)
def test_every_component_of_an_import_is_checked(body: str, rule: str) -> None:
    """Copilot review of #12459: the import rule read only a path's first name, so `using CairoMakie.Cairo` passed
    when the submodule was never named again. A path is one package name; what a selected import brings in is checked
    like any name."""
    assert rule in rules(security(body)), body


def test_the_catalogues_imports_are_single_names() -> None:
    """The 325 catalogue files load packages by their own name only; one selects a name (`using Statistics: mean`)."""
    assert security("using Statistics: mean\nusing Dates\nimport LinearAlgebra\nusing Printf: @sprintf") == []


@pytest.mark.parametrize(
    "body",
    [
        "f = Unlisted.dangerous\nf()",
        "(f,) = (Unlisted.dangerous,)\nf()",
        "a, f = 1, Unlisted.dangerous\nf()",
        "let f = Unlisted.dangerous\n    f()\nend",
        "map(Unlisted.dangerous, xs)",
        "foreach(Unlisted.dangerous, xs)",
        "const F = Unlisted.dangerous\nF()",
        "g = x -> Unlisted.dangerous(x)",
        "h(f = Unlisted.dangerous) = f()",
        "f = Foo.bar\nFoo = (bar = 1,)",
        "m = Tables\nf = m.columns",
        "k = Keyboard",
        "Makie.ImageIO.save(io, img)",
        "w = Makie.FilePaths",
    ],
)
def test_the_world_of_dotted_names_is_closed(body: str) -> None:
    """Copilot review of #12459: `f = Unlisted.dangerous; f()` passed, because the binding is no call and `f()` an
    ordinary one. A dotted name starts at a package root or a name bound above it, and no other module is a value or
    a member, so no alias, tuple, `let`, `const`, default or function argument carries such a member."""
    assert "banned-name" in rules(security(body)), body


@pytest.mark.parametrize(
    "body",
    [
        'ax = Axis(fig[1, 1])\nax.title = "x"',
        "s = fig.scene",
        "df = (col = [1, 2],)\nv = df.col",
        "for p in points\n    lines!(fig.scene, p.x, p.y)\nend",
        "xs = [p.x for p in points]",
        "xs = (p.x for p in points)",
        "xs = map(points) do p\n    p.x\nend",
        "getx(p) = p.x",
        "getx = p -> p.x",
        "function getx(p)\n    return p.x\nend",
        "let q = (x = 1,)\n    v = q.x\nend",
        "a, b = pairs_\nv = a.first",
        'c = colorant"#009E73"\nv = c.r',
        "try\n    f()\ncatch err\n    m = err.msg\nend",
    ],
)
def test_fields_of_values_the_file_binds_keep_passing(body: str) -> None:
    assert security(body) == [], body


@pytest.mark.parametrize(
    "body",
    [
        "invoke(f, Tuple{Int}, 1)",
        "Base.invoke(f, Tuple{Int}, 1)",
        "atexit(() -> nothing)",
        "finalizer(x -> nothing, obj)",
        "g = invoke",
        'surface = CairoMakie.Cairo.CairoPDFSurface("x.pdf", 10, 10)',
        'kind = Makie.FileIO.query("x.png")',
        'settings = Base.TOML.parsefile("x.toml")',
        "Base.CoreLogging.global_logger(logger)",
    ],
)
def test_defence_in_depth_names(body: str) -> None:
    """No plot needs code that runs later or elsewhere, nor the file-touching submodules an admitted root hands out
    (both reviewers, 2026-10-29)."""
    assert "banned-name" in rules(security(body)), body


@pytest.mark.parametrize(
    "code",
    [
        'const THEME = get(ENV, "ANYPLOT_THEME", "light"); THEME = "dark"\n' + SAVE,
        HEAD + "x = 1; " + SAVE,
        HEAD + "df = load_user_data(); df = 1\n" + SAVE,
        'using CairoMakie\nconst THEME = get(ENV, "ANYPLOT_THEME", "light")\nconst INK = THEME == "light" ? "#1" : "#2"\n'
        'INK = "#FF00FF"\n' + SAVE,
    ],
)
def test_protected_statements_are_bound_once_and_stand_alone(code: str) -> None:
    assert rules(validate_security(code)) & {"savefig-target", "banned-statement"}, code


@pytest.mark.parametrize(
    ("save", "message"),
    [
        ('save("plot.png", fig; px_per_unit = 2)', "writes"),
        ('save("plot-$(THEME).png", fig; px_per_unit = 2, size = (10, 10))', "only px_per_unit"),
        ('save("plot-$(THEME).png", fig; px_per_unit = 2, px_per_unit = 3)', "repeats"),
        ('save("plot-$(THEME).png", figs[1]; px_per_unit = 2)', "figure by its name"),
        ('save("plot-$(THEME).png", fig, extra; px_per_unit = 2)', "figure by its name"),
    ],
)
def test_the_protected_save_has_one_shape(save: str, message: str) -> None:
    findings = validate_security(HEAD + save + "\n")

    assert any(finding.rule == "savefig-target" and message in finding.message for finding in findings), findings


def test_no_save_and_no_theme_are_findings() -> None:
    assert rules(validate_security("x = 1\n")) == {"savefig-target"}


@pytest.mark.parametrize(
    ("code", "rule"), [("x = (1 +\n", "syntax"), ("x" * 60_001, "size"), ('x = "\ud800"\n', "encoding")]
)
def test_unreadable_code_is_a_finding(code: str, rule: str) -> None:
    assert [finding.rule for finding in validate_security(code)] == [rule]


def test_catalogue_corpus() -> None:
    """SECURITY over the 325 normalised files: findings in five, each for a real reason (2026-10-29)."""
    flagged: dict[str, Counter[str]] = {}
    for path in JULIA_CATALOGUE_FILES:
        findings = validate_security(normalise(path.read_text(encoding="utf-8")))
        if findings:
            flagged[path.parts[-4]] = Counter(finding.rule for finding in findings)

    assert sorted(flagged) == [
        "area-mountain-panorama",
        "bifurcation-basic",
        "map-tile-background",
        "qrcode-basic",
        "scatter-lag",
    ]
    for spec in ("area-mountain-panorama", "bifurcation-basic", "scatter-lag"):
        assert flagged[spec] == {"savefig-target": 2}  # the save inside with_theme(...) do
    assert flagged["qrcode-basic"]["banned-import"] == 1  # QRCoders, outside the project
    # Downloads and PNGFiles, each at its `using` and as the root of a call (`Downloads.download`, `PNGFiles.load`)
    assert flagged["map-tile-background"]["banned-import"] == 4


# --- ADAPTATION ------------------------------------------------------------------------------


def adaptation(code: str) -> set[str]:
    return rules(validate_adaptation(code, original_palette=PALETTE))


@pytest.mark.parametrize(
    ("change", "rule"),
    [
        (("df = load_user_data()\n", ""), "placeholder-count"),
        (("df = load_user_data()\n", "df = load_user_data()\ndf = load_user_data()\n"), "placeholder-count"),
        (("df = load_user_data()\n", "function f()\n    df = load_user_data()\nend\n"), "placeholder-use"),
        (("df = load_user_data()\n", "df = load_user_data()\nd2 = load_user_data\n"), "placeholder-use"),
        (("df = load_user_data()\n", "df = load_user_data()\nnoise = randn(10)\n"), "rng"),
        (("df = load_user_data()\n", "df = load_user_data()\nnoise = Random.randexp(3)\n"), "rng"),
        (("df = load_user_data()\n", "df = load_user_data()\nv = [" + ", ".join(["1"] * 21) + "]\n"), "literal-data"),
        (("df = load_user_data()\n", "df = load_user_data()\nusing RDatasets\n"), "dataset-package"),
        (
            ("df = load_user_data()\n", 'df = load_user_data()\nd = RDatasets.dataset("datasets", "iris")\n'),
            "dataset-package",
        ),
        (("df = load_user_data()\n", "df = load_user_data()\np = PalmerPenguins.load()\n"), "dataset-package"),
        (
            ("df = load_user_data()\n", 'df = load_user_data()\npush!(IMPRINT_PALETTE, colorant"#000000")\n'),
            "palette-prefix",
        ),
        (
            ("df = load_user_data()\n", 'df = load_user_data()\nIMPRINT_PALETTE[1] = colorant"#000000"\n'),
            "palette-prefix",
        ),
        (('colorant"#009E73", colorant"#C475FD"', 'colorant"#C475FD", colorant"#009E73"'), "palette-prefix"),
        (("const IMPRINT_PALETTE = [", "const IMPRINT_PALETTE = vcat(["), "palette-prefix"),
    ],
)
def test_adaptation_findings(change: tuple[str, str], rule: str) -> None:
    old, new = change
    code = JULIA_WORKING.replace(old, new, 1)
    if "vcat([" in code:
        code = code.replace('colorant"#99B314",\n]', 'colorant"#99B314",\n])', 1)

    assert rule in adaptation(code)


def test_rand_and_seed_stay_allowed_for_jitter() -> None:
    code = JULIA_WORKING.replace(
        "df = load_user_data()\n", "df = load_user_data()\nRandom.seed!(1)\njitter = 0.1 .* rand(nrow(df))\n"
    )

    assert adaptation(code) == set()


def test_a_dataset_package_passes_security() -> None:
    """RDatasets and PalmerPenguins are the project's (the pipeline loads them): only ADAPTATION refuses them."""
    code = HEAD + 'using RDatasets\nd = RDatasets.dataset("datasets", "iris")\np = PalmerPenguins.load()\n' + SAVE

    assert validate_security(code) == []


def test_the_palette_may_grow_by_the_next_imprint_positions_only() -> None:
    short = JULIA_WORKING.replace(
        '    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",\n', ""
    )
    original = list(find_regions(short).imprint.entries)  # type: ignore[union-attr]
    grown = short.replace('colorant"#BD8233",\n]', 'colorant"#BD8233", colorant"#AE3030",\n]')
    skipped = short.replace('colorant"#BD8233",\n]', 'colorant"#BD8233", colorant"#2ABCCD",\n]')

    assert validate_adaptation(grown, original_palette=original) == []
    assert rules(validate_adaptation(skipped, original_palette=original)) == {"palette-prefix"}
