"""The Julia profile against real Julia: the loader's read and the validator's admitted idioms in the J1 image.

Skipped unless Docker is available and the image is present (`ANYPLOT_JULIA_IMAGE`, by default the renderer image of
J1, `anyplot-renderer:julia`; the toolchain image works too). Each test runs Julia with the renderer's Julia row
(`agents/renderer/commands.py`: the launcher by its path, `--compiled-modules=strict`, the row's environment) in a
container without network, as the plan's measurements did on 2026-10-29.
"""

import functools
import os
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from agents.anyplot.code.profiles.julia.loader import loader_statement, to_run_form
from agents.anyplot.code.profiles.julia.validate import validate_adaptation, validate_security
from agents.anyplot.data.kinds import read_kinds
from agents.renderer.commands import command_for

from .conftest import JULIA_WORKING, source


IMAGE = os.environ.get("ANYPLOT_JULIA_IMAGE", "anyplot-renderer:julia")


@functools.cache
def _image_present() -> bool:
    docker = shutil.which("docker")
    if docker is None:
        return False
    result = subprocess.run([docker, "image", "inspect", IMAGE], capture_output=True, check=False)
    return result.returncode == 0


pytestmark = pytest.mark.skipif(not _image_present(), reason=f"needs Docker and the image {IMAGE}")


def julia(work: Path, script: str, *, theme: str = "light") -> subprocess.CompletedProcess[str]:
    """Run `script` (a file in `work`) with the renderer's Julia row, offline, as the current user."""
    row = command_for("julia", "makie")
    environment = [flag for key, value in row.env.items() for flag in ("-e", f"{key}={value}")]
    return subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp",
            "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{work}:/work", "-w", "/work",
            "-e", f"ANYPLOT_THEME={theme}", "-e", "HOME=/tmp", *environment,
            IMAGE, *row.argv, script,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )  # fmt: skip


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


NAMES = ['Zeit · $Messung "lokal"', "Größe\\Pfad", "line\nbreak", "i", "big", "x", "b", "t", "d"]
CSV_ROWS = [
    ("2024-01-31T08:00:00", "a", "1", "1", "-9223372036854775807", "0.1", "True", "NA", "2024-01-31"),
    ("2024-01-31 08:00:00", "b", "2", "-2", "9223372036854775807", "1e308", "False", "001", "2024-02-29"),
    ("2024-01-31T08:00:00Z", "", "3", "", "", "-0.0", "", "", ""),
    ("2024-01-31T08:00:00+01:00", "c", "4", "3", "-9223372036854775800", "", "True", "  sp  ", "1999-12-31"),
    ("2024-01-31T08:00:00-05:30", "d", "5", "4", "5", "2.5e-10", "False", "a,b", "2024-01-01"),
    ("2024-01-31T08:00:00.123", "e", "6", "5", "6", "7", "True", 'q"uote', "2024-01-02"),
    ("2024-01-31T08:00:00.123456", "f", "7", "6", "7", "8", "False", "é", "2024-01-03"),
    ("2024-01-31T08:00:00.123456789+02:00", "g", "8", "7", "8", "9", "True", "x", "2024-01-04"),
    ("", "h", "9", "8", "9", "10", "False", "y", "2024-01-05"),
    ("2024-01-31T08:00", "i", "10", "9", "10", "11", "True", "z", "2024-01-06"),
    ("0001-01-01T00:30:00+01:00", "j", "11", "10", "11", "12", "False", "w", "2024-01-07"),
]
KINDS = {
    NAMES[0]: "datetime",
    NAMES[1]: "text",
    NAMES[2]: "integer",
    "i": "integer",
    "big": "big-integer",
    "x": "number",
    "b": "boolean",
    "t": "text",
    "d": "date",
}


def csv_text() -> str:
    def cell(text: str) -> str:
        return '"' + text.replace('"', '""') + '"' if any(char in text for char in ',"\n') else text

    return "\n".join(",".join(cell(value) for value in row) for row in [tuple(NAMES), *CSV_ROWS]) + "\n"


def test_the_loader_reads_every_kind_and_datetime_form_exactly(tmp_path: Path) -> None:
    """Measured on 2026-10-29: offsets and `Z` to UTC, a space separator, minutes without seconds, fractions
    truncated to milliseconds, year 1 with an offset into year 0; Int64 over its whole range (CSV.jl alone flips the
    sign of -9223372036854775807 to -9223372036854775800); `NA`, `001` and blanks stay text; names with `$`, quotes,
    a backslash, a line break and non-ASCII letters read back as written."""
    (tmp_path / "data.csv").write_text(csv_text(), encoding="utf-8")
    script = (
        loader_statement(NAMES, KINDS)
        + "\n"
        + source("""
        for name in names(df)
            values = [ismissing(v) ? "missing" : string(v) for v in df[!, name]]
            println(repr(name), " ", nonmissingtype(eltype(df[!, name])), " ", join(values, "|"))
        end
    """)
    )
    (tmp_path / "read.jl").write_text(script, encoding="utf-8")

    result = julia(tmp_path, "read.jl")

    assert result.returncode == 0, result.stderr[-2000:]
    lines = result.stdout.splitlines()
    assert lines == [
        '"Zeit · \\$Messung \\"lokal\\"" Dates.DateTime 2024-01-31T08:00:00|2024-01-31T08:00:00|2024-01-31T08:00:00|'
        "2024-01-31T07:00:00|2024-01-31T13:30:00|2024-01-31T08:00:00.123|2024-01-31T08:00:00.123|"
        "2024-01-31T06:00:00.123|missing|2024-01-31T08:00:00|0000-12-31T23:30:00",
        '"Größe\\\\Pfad" String a|b|missing|c|d|e|f|g|h|i|j',
        '"line\\nbreak" Int64 1|2|3|4|5|6|7|8|9|10|11',
        '"i" Int64 1|-2|missing|3|4|5|6|7|8|9|10',
        '"big" Int64 -9223372036854775807|9223372036854775807|missing|-9223372036854775800|5|6|7|8|9|10|11',
        '"x" Float64 0.1|1.0e308|-0.0|missing|2.5e-10|7.0|8.0|9.0|10.0|11.0|12.0',
        '"b" Bool true|false|missing|true|false|true|false|true|false|true|false',
        '"t" String NA|001|missing|  sp  |a,b|q"uote|é|x|y|z|w',
        '"d" Dates.Date 2024-01-31|2024-02-29|missing|1999-12-31|2024-01-01|2024-01-02|2024-01-03|2024-01-04|'
        "2024-01-05|2024-01-06|2024-01-07",
    ]
    kinds = read_kinds(csv_text(), {NAMES[0]: "datetime", "big": "integer"})
    assert kinds.submillisecond == {NAMES[0]: 2}  # .123456 and .123456789, never .123


def test_the_validators_idioms_run(tmp_path: Path) -> None:
    """What SECURITY admits is real, working Julia: string macros, broadcasts, module members, do blocks, a named
    tuple whose fields carry denied names (reading `t.open` is refused: a member's name is checked on any value), the
    file's own `cp`, a column read with `$` in its name."""
    code = source("""
        using CairoMakie
        using DataFrames
        using Dates
        using LinearAlgebra
        using Printf
        using Random

        const THEME = get(ENV, "ANYPLOT_THEME", "light")
        const INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"

        Random.seed!(42)
        labels = Dates.format.([Date(2024, 1, 1)], "u dd")
        label = @sprintf("%.1f", 2.5)
        title_text = L"\\alpha^2"
        ys = map([1, 2]) do x
            2x
        end
        t = (open = 1, close = 2)
        half = Base.Fix2(÷, 2)(10)
        flat = collect(Iterators.flatten([[1], [2]]))
        n = LinearAlgebra.norm([3.0, 4.0])
        cp = 1.33
        rounded = round(cp; digits = 1)
        z = @. [1.0, 2.0]^2 + 1
        s = sort([(1, 2), (2, 1)]; by = p -> p[2])
        m = Vector{Float64}(undef, 3)
        df = DataFrame("Größe \\$" => [1.0, 2.0, 3.0])
        col = df[!, "Größe \\$"]

        fig = Figure(size = (400, 225))
        ax = Axis(fig[1, 1]; title = title_text, xlabel = "$(rounded) · $(half) · $(t.close)")
        lines!(ax, col, col .* n; color = INK)
        save("plot-$(THEME).png", fig; px_per_unit = 2)
    """)
    assert validate_security(code) == []
    (tmp_path / "idioms.jl").write_text(code, encoding="utf-8")

    result = julia(tmp_path, "idioms.jl")

    assert result.returncode == 0, result.stderr[-2000:]
    assert png_size(tmp_path / "plot-light.png") == (800, 450)


def test_the_working_miniature_renders_from_data_csv(tmp_path: Path) -> None:
    """The adapted miniature through the loader: column names with `€` and `$`, a timestamp column it does not plot,
    3200x1800 in the dark theme."""
    assert validate_security(JULIA_WORKING) == []
    assert validate_adaptation(JULIA_WORKING, original_palette=[]) == []
    columns = ["Ausgaben (k €)", "Umsatz $ (k)", "Erfasst"]
    rows = [
        f"{10 + index},{300 + 7 * index},2026-03-0{1 + index % 9}T08:00:00.{index:06d}+01:00" for index in range(30)
    ]
    (tmp_path / "data.csv").write_text("\n".join([",".join(columns), *rows]) + "\n", encoding="utf-8")
    kinds = {"Ausgaben (k €)": "integer", "Umsatz $ (k)": "integer", "Erfasst": "datetime"}
    (tmp_path / "plot.jl").write_text(to_run_form(JULIA_WORKING, columns=columns, kinds=kinds), encoding="utf-8")

    result = julia(tmp_path, "plot.jl", theme="dark")

    assert result.returncode == 0, result.stderr[-2000:]
    assert png_size(tmp_path / "plot-dark.png") == (3200, 1800)
