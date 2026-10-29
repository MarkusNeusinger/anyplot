"""Tests for agents/anyplot/code/profiles/julia/errors.py: Julia's stderr to a summary that never quotes the message.

Every sample is real stderr of the J1 image (Julia 1.13.2, `--compiled-modules=strict`, 2026-10-29), the script
renamed to `/work/plot.jl` where it was another file; the exec-filter kill and the loader failure ran through the
renderer harness in exec mode.
"""

from pathlib import Path

import pytest

from agents.anyplot.code.profiles.julia.errors import (
    CACHE_MISS,
    NO_ERROR_LINE,
    NO_ERROR_OUTPUT,
    OUT_OF_MEMORY,
    RECURSION,
    error_summary,
)
from agents.anyplot.render.contract import MAX_STDERR_CHARS

from .conftest import source


FRAMES = """
 [2] include(mod::Module, _path::String)
   @ Base ./Base.jl:309
 [3] exec_options(opts::Base.JLOptions)
   @ Base ./client.jl:344
 [4] _start()
   @ Base ./client.jl:577
"""

SAMPLES = {
    "method": (
        source("""
            ERROR: LoadError: MethodError: no method matching f(::String)
            The function `f` exists, but no method is defined for this combination of argument types.

            Closest candidates are:
              f(!Matched::Int64)
               @ Main /work/plot.jl:1

            Stacktrace:
             [1] top-level scope
               @ /work/plot.jl:3
        """)
        + FRAMES
        + "in expression starting at /work/plot.jl:3\n",
        "MethodError for f() at line 3",
    ),
    "undefined": (
        source("""
            ERROR: LoadError: UndefVarError: `undefined_thing` not defined in `Main`
            Suggestion: check for spelling errors or missing imports.
            Stacktrace:
             [1] top-level scope
               @ /work/plot.jl:2
        """)
        + FRAMES
        + "in expression starting at /work/plot.jl:2\n",
        "UndefVarError for undefined_thing at line 2",
    ),
    "bounds in a function": (
        source("""
            ERROR: LoadError: BoundsError: attempt to access 2-element Vector{Int64} at index [5]
            Stacktrace:
             [1] throw_boundserror(A::Vector{Int64}, I::Tuple{Int64})
               @ Base ./essentials.jl:14
             [2] checkbounds
               @ ./essentials.jl:389 [inlined]
             [3] getindex
               @ ./essentials.jl:974 [inlined]
             [4] g(v::Vector{Int64})
               @ Main /work/plot.jl:2
             [5] top-level scope
               @ /work/plot.jl:5
        """)
        + "in expression starting at /work/plot.jl:5\n",
        "BoundsError at line 2; in getindex(); the statement starts at line 5",
    ),
    "error() with data in its message": (
        source("""
            ERROR: LoadError: Umsatz Zürich 123 was not found
            Stacktrace:
             [1] error(s::String)
               @ Base ./error.jl:44
             [2] top-level scope
               @ /work/plot.jl:2
        """)
        + "in expression starting at /work/plot.jl:2\n",
        "an error at line 2; in error()",
    ),
    "a missing column": (
        source("""
            ERROR: LoadError: ArgumentError: column name :Umsatz (€) not found in the data frame
            Stacktrace:
             [1] lookupname
               @ /opt/julia-depot/packages/DataFrames/0Y1g5/src/other/index.jl:431 [inlined]
             [4] getindex(df::DataFrame, ::typeof(!), col_ind::String)
               @ DataFrames /opt/julia-depot/packages/DataFrames/0Y1g5/src/dataframe/dataframe.jl:559
             [5] top-level scope
               @ /work/plot.jl:3
        """)
        + "in expression starting at /work/plot.jl:3\n",
        "ArgumentError at line 3; in getindex()",
    ),
    "a strict read": (
        source("""
            ERROR: LoadError: thread = 1 error parsing Int64 around row = 2, col = 1: "x
            ", error=INVALID: NEWLINE | EOF | INVALID_DELIMITER

            Stacktrace:
              [8] read(source::String, sink::Type; copycols::Bool, kwargs::@Kwargs{types::Dict{String, DataType}, strict::Bool})
                @ CSV /opt/julia-depot/packages/CSV/T1GBD/src/CSV.jl:117
              [9] top-level scope
                @ /work/plot.jl:3
        """)
        + "in expression starting at /work/plot.jl:3\n",
        "an error at line 3; in read()",
    ),
    "the loader's datetime": (
        source("""
            ERROR: LoadError: ArgumentError: not an ISO 8601 date and time: "2026-03-01 at 03:15+01:00"
            Stacktrace:
              [1] (::var"#utc#utc##0")(cell::String)
                @ Main /work/plot.jl:28
              [2] _broadcast_getindex_evalf
                @ ./broadcast.jl:704 [inlined]
        """)
        + "in expression starting at /work/plot.jl:20\n",
        "ArgumentError at line 28; the statement starts at line 20",
    ),
    "the exec filter's kill": (
        source("""
            ERROR: LoadError: failed process: Process(`ls /`, ProcessSignaled(31)) [0]

            Stacktrace:
             [1] pipeline_error
               @ ./process.jl:610 [inlined]
             [2] run(::Cmd; wait::Bool)
               @ Base ./process.jl:525
             [3] run(::Cmd)
               @ Base ./process.jl:522
             [4] top-level scope
               @ /work/plot.jl:3
        """)
        + "in expression starting at /work/plot.jl:3\n",
        "a process start, which the sandbox refuses at line 3; in run()",
    ),
    "a parse error": (
        source("""
            ERROR: LoadError: ParseError:
            # Error @ /work/plot.jl:2:1
            x = (1 +
            └ ── premature end of input
            Stacktrace:
             [1] top-level scope
               @ /work/plot.jl:2
        """)
        + "in expression starting at /work/plot.jl:2\n",
        "ParseError at line 2",
    ),
}


@pytest.mark.parametrize(("stderr", "summary"), SAMPLES.values(), ids=SAMPLES.keys())
def test_real_stderr(stderr: str, summary: str) -> None:
    assert error_summary(stderr) == summary


def test_a_deep_makie_failure_keeps_the_plot_line_in_the_tail() -> None:
    """7,551 characters of stderr: the renderer's tail loses the ERROR line but keeps the frame and the expression."""
    stderr = (Path(__file__).parent / "fixtures" / "julia_makie_text_align.stderr").read_text(encoding="utf-8")

    assert len(stderr) > MAX_STDERR_CHARS
    assert error_summary(stderr) == "an error at line 4; in text!()"
    assert (
        error_summary(stderr[-MAX_STDERR_CHARS:]) == "an error (the tail cut off its first line) at line 4; in text!()"
    )


@pytest.mark.parametrize(
    ("stderr", "summary"),
    [
        ("", NO_ERROR_OUTPUT),
        ("\n  \n", NO_ERROR_OUTPUT),
        ("something else\n", NO_ERROR_LINE),
        ("ERROR: LoadError: OutOfMemoryError()\nStacktrace:\n", OUT_OF_MEMORY),
        (
            "ERROR: LoadError: StackOverflowError:\nStacktrace:\n ┌ [1] f(x::Int64)\n │ @ Main /work/plot.jl:1\n",
            RECURSION,
        ),
        (
            "ERROR: LoadError: ArgumentError: Package QRCoders not found in current path.\n",
            "a package that is not installed (QRCoders)",
        ),
        (
            'ERROR: Precompiled image Base.PkgId(Base.UUID("13f3f980"), "CairoMakie") not available with flags '
            "CacheFlags(; use_pkgimages=true, debug_level=1, check_bounds=1, inline=true, opt_level=2)\n",
            CACHE_MISS,
        ),
    ],
)
def test_fixed_texts(stderr: str, summary: str) -> None:
    assert error_summary(stderr) == summary


def test_the_message_never_reaches_the_summary() -> None:
    stderr = 'ERROR: LoadError: KeyError: key "Umsatz Zürich" not found\nStacktrace:\n [1] top-level scope\n   @ /work/plot.jl:9\n'

    assert error_summary(stderr) == "KeyError at line 9"


@pytest.mark.parametrize(
    "first",
    [
        "ERROR: LoadError: UndefVarError: `a b; rm` not defined in `Main`",
        "ERROR: LoadError: MethodError: no method matching $(run)(::Int64)",
        "ERROR: LoadError: MadeUpError: anything",
    ],
)
def test_names_pass_only_in_a_closed_shape(first: str) -> None:
    summary = error_summary(first + "\nStacktrace:\n [1] top-level scope\n   @ /work/plot.jl:1\n")

    assert summary in ("UndefVarError at line 1", "MethodError at line 1", "an error at line 1")


def test_frames_of_another_file_are_not_the_plot() -> None:
    stderr = "ERROR: LoadError: BoundsError: x\nStacktrace:\n [1] f()\n   @ Main /work/other.jl:7\n"

    assert error_summary(stderr) == "BoundsError"
    assert error_summary(stderr.replace("other.jl", "snippet.jl"), code_file="snippet.jl") == "BoundsError at line 7"
