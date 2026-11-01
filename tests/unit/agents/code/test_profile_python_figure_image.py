"""plotly and bokeh against the renderer image's figure mode (PB-2a, 2026-10-31): the prompt's idioms and the export.

Skipped unless Docker is available and the image is present (`ANYPLOT_FIGURE_IMAGE`, by default
`anyplot-renderer:figure`, a local tag of a renderer image with PB-1's figure mode). Each render goes through the local
Docker backend exactly as a development session's does: the library's runtime command (the harness in figure mode, then
the JavaScript row's harness) and environment, the checkout's `harness.py` and `render.mjs` mounted over the image's, no
network, a read-only root, the run form from the Python loader and `data.csv` next to it. The markup cases also run the
image's own `render.mjs`, so they need an image built from this tree.
"""

import asyncio
import functools
import os
import secrets
import shutil
import struct
import subprocess

import pytest

from agents.anyplot.code.loader import to_run_form
from agents.anyplot.render.backends import local as local_backend
from agents.anyplot.render.backends.local import LocalDockerBackend
from agents.anyplot.render.contract import RenderJob
from agents.anyplot.render.runtimes import PythonRuntime, runtime_for

from .conftest import FIGURE_PROMPT_IDIOMS


IMAGE = os.environ.get("ANYPLOT_FIGURE_IMAGE", "anyplot-renderer:figure")


@functools.cache
def _image_present() -> bool:
    docker = shutil.which("docker")
    if docker is None:
        return False
    return subprocess.run([docker, "image", "inspect", IMAGE], capture_output=True, check=False).returncode == 0


pytestmark = pytest.mark.skipif(not _image_present(), reason=f"needs Docker and the image {IMAGE}")

NAMES = ['Tag "lokal"', "Ausgaben (k €)", "Umsatz\\Netto", "Anzahl", "Region"]
DTYPES = {NAMES[0]: "datetime", NAMES[1]: "number", NAMES[2]: "number", NAMES[3]: "integer", NAMES[4]: "text"}
ROWS = [
    (
        "" if index in (5, 17) else f"2026-{1 + index // 28:02d}-{1 + index % 28:02d}T07:30:00+01:00",
        "" if index == 9 else f"{12.5 + index * 1.75:.2f}",
        "" if index in (3, 21) else f"{1_250_000 + 40_000 * index - 3_000 * (index % 7) ** 2}",
        "" if index == 11 else str(3 + index % 5),
        "" if index == 13 else ("Nord", "Süd", "Ost")[index % 3],
    )
    for index in range(40)
]


def csv_text() -> str:
    def cell(text: str) -> str:
        return '"' + text.replace('"', '""') + '"' if any(char in text for char in ',"\n') else text

    return "\n".join(",".join(cell(value) for value in row) for row in [tuple(NAMES), *ROWS]) + "\n"


def png_size(png: bytes) -> tuple[int, int]:
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", png[16:24])
    return width, height


def render(library: str, source: str) -> dict[str, tuple[int | None, bytes | None, str]]:
    backend = LocalDockerBackend(
        image=IMAGE, runtime=PythonRuntime(), environment="development", runtime_for=runtime_for
    )
    job = RenderJob(
        job_id=f"pb2-{library}-{secrets.token_hex(4)}",  # unique: parallel tests start containers named by it
        language="python",
        library=library,
        source=source,
        data_csv=csv_text(),
        themes=("light", "dark"),
        timeout_s=120,
    )
    result = asyncio.run(backend.render(job))
    return {theme: (out.exit_code, out.png, out.stderr_tail) for theme, out in result.outputs.items()}


@pytest.mark.parametrize("library", ["plotly", "bokeh"])
def test_the_prompts_idioms_render_from_a_table_with_gaps_in_both_themes(library: str) -> None:
    """The idiom form (`conftest.FIGURE_PROMPT_IDIOMS`, the section's code verbatim) through the Python loader renders
    3200x1800 in both themes from a table with missing dates, numbers, an integer and a text cell, a timestamp with an
    offset and a column name with a quote and a backslash (measured on 2026-10-31)."""
    run_form = to_run_form(FIGURE_PROMPT_IDIOMS[library], columns=NAMES, dtypes=DTYPES, parse_dates=[])

    for theme, (code, png, tail) in render(library, run_form).items():
        assert code == 0, (theme, tail[-2000:])
        assert png is not None and png_size(png) == (3200, 1800), theme


def test_a_webgl_trace_fails_as_no_webgl() -> None:
    source = (
        "import os\n\nimport plotly.graph_objects as go\n\n"
        'THEME = os.getenv("ANYPLOT_THEME", "light")\n'
        "fig = go.Figure(go.Scatter3d(x=[1, 2], y=[1, 2], z=[1, 2]))\n"
        'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")\n'
    )

    for theme, (code, png, tail) in render("plotly", source).items():
        assert code != 0 and png is None, theme
        assert runtime_for("plotly").error_summary(tail).startswith("a WebGL trace"), tail[-500:]


UNSAFE_FIGURES = {
    "bokeh-tooltip-in-tags": (
        "bokeh",
        "import json\nimport os\n\nfrom bokeh.embed import json_item\nfrom bokeh.models import Tooltip\n"
        "from bokeh.plotting import figure\n\n"
        'THEME = os.getenv("ANYPLOT_THEME", "light")\n'
        "p = figure(width=4800, height=2700, toolbar_location=None)\np.line([1, 2], [3, 4])\n"
        'p.tags = [Tooltip(content="x")]\n'
        'with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:\n'
        "    json.dump(json_item(p), figure_file)\n",
    ),
    "bokeh-div-built-at-run-time": (
        "bokeh",
        "import json\nimport os\n\nfrom bokeh.embed import json_item\nfrom bokeh.models import Div\n"
        "from bokeh.plotting import figure\n\n"
        'THEME = os.getenv("ANYPLOT_THEME", "light")\n'
        "p = figure(width=4800, height=2700, toolbar_location=None)\np.line([1, 2], [3, 4])\n"
        'p.tags = [Div(text=chr(60) + "img src=x onerror=alert(1)>")]\n'
        'with open(f"plot-{THEME}.json", "w", encoding="utf-8") as figure_file:\n'
        "    json.dump(json_item(p), figure_file)\n",
    ),
    "plotly-link-in-a-hovertemplate": (
        "plotly",
        "import os\n\nimport plotly.graph_objects as go\n\n"
        'THEME = os.getenv("ANYPLOT_THEME", "light")\n'
        "link = chr(60) + 'a href=\"javascript:alert(1)\">%{y}' + chr(60) + '/a>'\n"
        'fig = go.Figure(go.Bar(x=["a", "b"], y=[1, 2], hovertemplate=link))\n'
        'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")\n',
    ),
    "plotly-link-in-a-colour-bar-title": (
        "plotly",
        "import os\n\nimport plotly.graph_objects as go\n\n"
        'THEME = os.getenv("ANYPLOT_THEME", "light")\n'
        "title = chr(60) + 'a href=\"javascript:alert(1)\">t' + chr(60) + '/a>'\n"
        "fig = go.Figure(go.Scatter(x=[1, 2], y=[1, 2], mode='markers',\n"
        "    marker={'color': [1, 2], 'colorbar': {'title': {'text': title}}}))\n"
        'fig.update_layout(width=800, height=450).write_json(f"plot-{THEME}.json")\n',
    ),
}


@pytest.mark.parametrize("harness", ["checkout", "image"])
@pytest.mark.parametrize("case", sorted(UNSAFE_FIGURES))
def test_markup_built_at_run_time_fails_as_unsafe_markup(
    case: str, harness: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fable's reviews of PB-2a: what a browser would run or follow, built where no validator rule reads it
    (`chr(60)`, a model in a plot's `tags`), fails as `figure UnsafeMarkup` before a page opens. `image` runs the
    image's own `render.mjs` (the checkout's is not mounted), so a stale image fails here."""
    if harness == "image":
        monkeypatch.setattr(local_backend, "JS_HARNESS_SOURCE", local_backend.JS_HARNESS_SOURCE.with_name("absent.mjs"))
    library, source = UNSAFE_FIGURES[case]

    for theme, (code, png, tail) in render(library, source).items():
        last = [line for line in tail.splitlines() if line.strip()][-1:]
        assert code != 0 and png is None, (theme, tail[-500:])
        assert last and last[0].startswith("render: error: figure UnsafeMarkup "), (theme, tail[-500:])
        assert runtime_for(library).error_summary(tail).startswith("the figure holds what a browser"), tail[-500:]
