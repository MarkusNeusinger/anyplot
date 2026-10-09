"""The exported `plot.py`: the run form that rendered, under an attribution header.

The export is byte for byte the run form after two comment lines and a blank line:

    # Adapted by anyplot.ai from scatter-basic (matplotlib 3.11.2) for your data.csv;
    # run: ANYPLOT_THEME=light python plot.py

The catalogue's four-line header and title rule do not apply to user plots
(docs/concepts/agent-network.md, "Fencing and exported code"). Exporting an export
replaces its header instead of stacking a second one, so `export_code` is idempotent.
The spec id, library and version are checked against strict patterns, because they
become source code.
"""

import re


HEADER_PREFIX = "# Adapted by anyplot.ai from "
RUN_LINE = "# run: ANYPLOT_THEME=light python plot.py"

_SPEC_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_LIBRARY = re.compile(r"[a-z][a-z0-9]*")
_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+-]{0,31}")
_EXISTING_HEADER = re.compile(r"\A# Adapted by anyplot\.ai from [^\r\n]*\r?\n# run: [^\r\n]*\r?\n(?:\r?\n)?")


def attribution(spec_id: str, library: str, library_version: str | None) -> str:
    """The two header lines plus the blank line after them."""
    if not _SPEC_ID.fullmatch(spec_id):
        raise ValueError(f"not a spec id: {spec_id!r}")
    if not _LIBRARY.fullmatch(library):
        raise ValueError(f"not a library id: {library!r}")
    if library_version is not None and not _VERSION.fullmatch(library_version):
        raise ValueError(f"not a library version: {library_version!r}")
    source = f"{library} {library_version}" if library_version else library
    return f"{HEADER_PREFIX}{spec_id} ({source}) for your data.csv;\n{RUN_LINE}\n\n"


def export_code(run_form: str, *, spec_id: str, library: str, library_version: str | None) -> str:
    """The downloadable `plot.py`: the attribution header, then `run_form` unchanged."""
    return attribution(spec_id, library, library_version) + _EXISTING_HEADER.sub("", run_form, count=1)
