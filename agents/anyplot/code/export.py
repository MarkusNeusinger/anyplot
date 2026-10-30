"""The exported `plot.py`: the run form that rendered, under an attribution header.

The export is byte for byte the run form after two comment lines and a blank line:

    # Adapted by anyplot.ai from scatter-basic (matplotlib 3.11.2) for your data.csv;
    # run: ANYPLOT_THEME=light python plot.py

The run line names the theme the run rendered (`PipelineArgs.theme`), so a user who
asked for a dark plot and follows the header gets the dark one; the code itself still
reads `ANYPLOT_THEME` and defaults to light. The catalogue's four-line header and
title rule do not apply to user plots (docs/concepts/agent-network.md, "Fencing and
exported code"). Exporting an export replaces its header instead of stacking a second
one, so `export_code` is idempotent. The spec id, library, version and theme are
checked against strict patterns, because they become source code.

The command after the theme is the language's (2026-10-29): `python plot.py` for
Python, `Rscript plot.R` for R, `julia --project=. plot.jl` for Julia, one of
`RUN_COMMANDS`; R and Julia read `#` comments too, so the header is the same two lines.
Julia's is the catalogue's own convention (`prompts/library/makie.md`, the landing page's
terminal): `--project=.` activates a `Project.toml` next to the file when the user keeps
one there, and without one Julia falls back to the default environment, where the user's
`CairoMakie`, `CSV`, `DataFrames` and `TimeZones` are installed.

JavaScript (`plot.js`, and `plot.tsx` for MUI X; JS-3, 2026-10-30) reads `//` comments,
and a `#` header is a syntax error there, so its two lines are `//` comments. Its code
does not run by itself: it reads the harness's `window.ANYPLOT_TOKENS`, `_THEME`, `_SIZE`
and `_DATA` and the library's global, so the run line names the self-contained
`plot.html` that the export carries next to it (the page the harness writes: the library,
the tokens, the data and this code; owner decision of 2026-10-30, question 12), not a
command for Node:

    // Adapted by anyplot.ai from scatter-basic (chartjs 4.4.7) for your data.csv;
    // run: open plot.html in a browser, which runs this code with the chart library, the light theme and your data
"""

import re


HEADER_PREFIX = "# Adapted by anyplot.ai from "
RUN_LINE = "# run: ANYPLOT_THEME={theme} {command}"
PYTHON_RUN = "python plot.py"
R_RUN = "Rscript plot.R"
JULIA_RUN = "julia --project=. plot.jl"
SCRIPT_RUN = "open plot.html in a browser"
"""JavaScript's run line: the exported page runs the code; it is no program of its own."""
SCRIPT_HEADER_PREFIX = "// Adapted by anyplot.ai from "
SCRIPT_RUN_LINE = "// run: {command}, which runs this code with the chart library, the {theme} theme and your data"
RUN_COMMANDS = frozenset({PYTHON_RUN, R_RUN, JULIA_RUN, SCRIPT_RUN})
"""The run commands a header may name: each language's command for its code artifact."""
EXPORT_THEMES = ("light", "dark")

_SPEC_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_LIBRARY = re.compile(r"[a-z][a-z0-9]*")
_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+-]{0,31}")
_EXISTING_HEADER = re.compile(
    r"\A(?:# Adapted by anyplot\.ai from [^\r\n]*\r?\n# run: [^\r\n]*\r?\n"
    r"|// Adapted by anyplot\.ai from [^\r\n]*\r?\n// run: [^\r\n]*\r?\n)(?:\r?\n)?"
)


def attribution(
    spec_id: str, library: str, library_version: str | None, theme: str = "light", *, run: str = PYTHON_RUN
) -> str:
    """The two header lines plus the blank line after them."""
    if not _SPEC_ID.fullmatch(spec_id):
        raise ValueError(f"not a spec id: {spec_id!r}")
    if not _LIBRARY.fullmatch(library):
        raise ValueError(f"not a library id: {library!r}")
    if library_version is not None and not _VERSION.fullmatch(library_version):
        raise ValueError(f"not a library version: {library_version!r}")
    if theme not in EXPORT_THEMES:
        raise ValueError(f"not a theme: {theme!r}")
    if run not in RUN_COMMANDS:
        raise ValueError(f"not a run command: {run!r}")
    source = f"{library} {library_version}" if library_version else library
    if run == SCRIPT_RUN:
        return (
            f"{SCRIPT_HEADER_PREFIX}{spec_id} ({source}) for your data.csv;\n"
            f"{SCRIPT_RUN_LINE.format(command=run, theme=theme)}\n\n"
        )
    return f"{HEADER_PREFIX}{spec_id} ({source}) for your data.csv;\n{RUN_LINE.format(theme=theme, command=run)}\n\n"


def export_code(
    run_form: str,
    *,
    spec_id: str,
    library: str,
    library_version: str | None,
    theme: str = "light",
    run: str = PYTHON_RUN,
) -> str:
    """The downloadable code: the attribution header, then `run_form` unchanged."""
    header = attribution(spec_id, library, library_version, theme, run=run)
    return header + _EXISTING_HEADER.sub("", run_form, count=1)
