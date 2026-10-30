"""The JavaScript runtime against the real browser harness: the typed table in the page and the prompt's idioms.

Skipped unless Docker is available and the image is present (`ANYPLOT_JS_IMAGE`, by default `anyplot-renderer:js`, a
local tag of a renderer image with the JavaScript toolchain of JS-1). Each test runs the harness with the renderer's
JavaScript row (`agents/renderer/commands.py`: Node by its path, the row's environment with the harness's sandbox
mode) in a container without network, the checkout's `automation/js-render/render.mjs` mounted over the image's, as
the local backend mounts the checkout's `harness.py`, and the job's `data.json` written by
`agents/anyplot/data/typed_json.py`, as the renderer's executor writes it.
"""

import functools
import os
import shutil
import struct
import subprocess
from pathlib import Path

import pytest

from agents.anyplot.code.profiles.javascript.loader import to_run_form
from agents.anyplot.data.kinds import read_kinds
from agents.anyplot.data.typed_json import typed_json
from agents.anyplot.render.runtimes import runtime_for
from agents.renderer.commands import JS_HARNESS, command_for
from agents.renderer.executor import DATA_JSON_ENV, DATA_JSON_FILE, WORKDIR

from .conftest import JS_PROMPT_IDIOMS, REPO_ROOT, source


IMAGE = os.environ.get("ANYPLOT_JS_IMAGE", "anyplot-renderer:js")
HARNESS_SOURCE = REPO_ROOT / "automation" / "js-render" / "render.mjs"


@functools.cache
def _image_present() -> bool:
    docker = shutil.which("docker")
    if docker is None:
        return False
    result = subprocess.run([docker, "image", "inspect", IMAGE], capture_output=True, check=False)
    return result.returncode == 0


pytestmark = pytest.mark.skipif(not _image_present(), reason=f"needs Docker and the image {IMAGE}")


def render(work: Path, library: str, *, theme: str = "light") -> subprocess.CompletedProcess[str]:
    """Run the harness on the code file in `work` with the renderer's JavaScript row, offline, as the current user."""
    row = command_for("javascript", library)
    environment = [flag for key, value in row.env.items() for flag in ("-e", f"{key}={value}")]
    if (work / DATA_JSON_FILE).exists():
        environment += ["-e", f"{DATA_JSON_ENV}={WORKDIR}/{DATA_JSON_FILE}"]
    return subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp",
            "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{work}:/work", "-w", "/work",
            "-v", f"{HARNESS_SOURCE}:{JS_HARNESS}:ro",
            "-e", f"ANYPLOT_THEME={theme}", "-e", "HOME=/tmp", *environment,
            IMAGE, *row.argv, row.code_file,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )  # fmt: skip


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def csv_text(names: list[str], rows: list[tuple[str, ...]]) -> str:
    def cell(text: str) -> str:
        return '"' + text.replace('"', '""') + '"' if any(char in text for char in ',"\n') else text

    return "\n".join(",".join(cell(value) for value in row) for row in [tuple(names), *rows]) + "\n"


def write_job(work: Path, library: str, working: str, csv: str, dtypes: dict[str, str], dates: list[str]) -> None:
    """The run form and the typed table, as the pipeline hands them to the backend."""
    kinds = read_kinds(csv, dtypes, dates)  # type: ignore[arg-type]
    (work / command_for("javascript", library).code_file).write_text(to_run_form(working, library=library))
    (work / DATA_JSON_FILE).write_text(typed_json(csv, kinds), encoding="utf-8")


IDIOM_NAMES = ['Tag "lokal"', "Ausgaben (k €)", "Umsatz\\Netto", "Region"]
IDIOM_DTYPES = {IDIOM_NAMES[0]: "datetime", IDIOM_NAMES[1]: "number", IDIOM_NAMES[2]: "number", "Region": "text"}
IDIOM_ROWS = [
    (
        "" if index in (5, 17) else f"2026-{1 + index // 28:02d}-{1 + index % 28:02d}",
        "" if index == 9 else f"{12.5 + index * 1.75:.2f}",
        "" if index in (3, 21) else f"{1_250_000 + 40_000 * index - 3_000 * (index % 7) ** 2}",
        ("Nord", "Süd", "Ost")[index % 3],
    )
    for index in range(40)
]


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("library", ["chartjs", "d3", "echarts", "highcharts"])
def test_the_prompts_idioms_render_from_the_typed_table(tmp_path: Path, library: str, theme: str) -> None:
    """Each library's idiom form (`conftest.JS_PROMPT_IDIOMS`, the prompt's code verbatim) renders 3200x1800 from a
    table with missing dates, numbers and a column name with a quote and a backslash: `null` dropped before every
    statistic, `fmt` on the value axes, the time axes in UTC (measured on 2026-10-30)."""
    write_job(
        tmp_path, library, JS_PROMPT_IDIOMS[library], csv_text(IDIOM_NAMES, IDIOM_ROWS), IDIOM_DTYPES, [IDIOM_NAMES[0]]
    )

    result = render(tmp_path, library, theme=theme)

    assert result.returncode == 0, result.stderr[-2000:]
    assert png_size(tmp_path / f"plot-{theme}.png") == (3200, 1800)


def test_the_page_reads_every_kind_as_the_prompt_describes(tmp_path: Path) -> None:
    """The typed table in the page: `data.columns` in order, numbers, an integer past 2^53 as the nearest double,
    `true` and `false`, text that looks like a number kept as text, dates as `YYYY-MM-DD`, timestamps as UTC ISO with
    milliseconds (an offset converted, digits below the millisecond cut), and `null` for every missing cell. The
    snippet throws on the first difference, so the render fails with the check's name."""
    names = ["i", "big", "x", "b", "t", "d", "ts"]
    rows = [
        ("1", "9007199254740993", "0.5", "True", "001", "2024-01-31", "2024-01-31T08:00:00.123456+01:00"),
        ("", "", "", "", "", "", ""),
        ("-2", "5", "2.5e-10", "False", "NA", "1999-12-31", "2024-01-31T08:00:00Z"),
    ]
    dtypes = {"i": "integer", "big": "integer", "x": "number", "b": "boolean", "t": "text", "d": "datetime"}
    dtypes["ts"] = "datetime"
    working = source(r"""
        //# anyplot-orientation: landscape
        const t = window.ANYPLOT_TOKENS;

        const data = loadUserData();

        const expect = (name, ok) => {
          if (!ok) {
            throw new RangeError(name);
          }
        };
        expect("columns", data.columns.join(",") === "i,big,x,b,t,d,ts");
        expect("rows", data.length === 3);
        expect("integer", data[0].i === 1 && data[2].i === -2);
        expect("big", data[0].big === 9007199254740992);
        expect("number", data[0].x === 0.5 && data[2].x === 2.5e-10);
        expect("boolean", data[0].b === true && data[2].b === false);
        expect("text", data[0].t === "001" && data[2].t === "NA");
        expect("date", data[0].d === "2024-01-31" && data[2].d === "1999-12-31");
        expect("timestamp", data[0].ts === "2024-01-31T07:00:00.123Z" && data[2].ts === "2024-01-31T08:00:00.000Z");
        expect("missing", Object.values(data[1]).every((v) => v === null));
        expect("utc", new Date(data[0].d).getUTCHours() === 0 && new Date(data[0].ts).getUTCHours() === 7);
        const canvas = document.createElement("canvas");
        document.getElementById("container").appendChild(canvas);
        new Chart(canvas, { type: "bar", data: { labels: ["ok"], datasets: [{ data: [1], backgroundColor: t.palette[0] }] }, options: { animation: false } });
    """)
    write_job(tmp_path, "chartjs", working, csv_text(names, rows), dtypes, ["d", "ts"])

    result = render(tmp_path, "chartjs")

    assert result.returncode == 0, result.stderr[-2000:]
    kinds = read_kinds(csv_text(names, rows), dtypes, ["d", "ts"])  # type: ignore[arg-type]
    assert kinds.inexact == {"big": 1} and kinds.submillisecond == {"ts": 1} and kinds.offset == {"ts": 1}


def test_chartjs_has_no_time_axis_in_the_page(tmp_path: Path) -> None:
    """The prompt's claim: the page has no date adapter, so a Chart.js `type: "time"` axis fails the render, and the
    error summary names the snippet's line."""
    working = source("""
        //# anyplot-orientation: landscape
        const t = window.ANYPLOT_TOKENS;

        const data = loadUserData();

        const canvas = document.createElement("canvas");
        document.getElementById("container").appendChild(canvas);
        new Chart(canvas, {
          type: "line",
          data: { datasets: [{ data: data.map((d) => ({ x: d.day, y: d.value })), borderColor: t.palette[0] }] },
          options: { animation: false, scales: { x: { type: "time" } } },
        });
    """)
    csv = csv_text(["day", "value"], [("2024-01-01", "1"), ("2024-01-02", "2")])
    write_job(tmp_path, "chartjs", working, csv, {"day": "datetime", "value": "integer"}, ["day"])

    result = render(tmp_path, "chartjs")

    assert result.returncode != 0
    summary = runtime_for("chartjs").error_summary(result.stderr, run_form=to_run_form(working, library="chartjs"))
    assert "at line 8" in summary, (summary, result.stderr[-1000:])
