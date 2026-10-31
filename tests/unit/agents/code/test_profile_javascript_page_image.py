"""The downloadable `plot.html` against the real image (JS-4b): built, wrapped and probed in its Chromium.

Skipped unless Docker is available and the image is present (`ANYPLOT_JS_IMAGE`, by default `anyplot-renderer:js`, a
local tag of a renderer image with the JavaScript toolchain of JS-1). The page is built by the local Docker backend's
`page` (the renderer's JavaScript row with `ANYPLOT_PAGE_ONLY=1`, the checkout's `render.mjs` and `harness.py`
mounted over the image's), wrapped by the agents' `page_export.page_download`, and opened from `file://` in the
image's Chromium by `agents/renderer/page_probe.mjs`, as the renderer image's CI step does, in a container without
network.
"""

import asyncio
import functools
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from agents.anyplot.code.profiles.javascript.loader import to_run_form
from agents.anyplot.data.kinds import read_kinds
from agents.anyplot.data.typed_json import typed_json
from agents.anyplot.page_export import page_download
from agents.anyplot.render.backends.local import LocalDockerBackend
from agents.anyplot.render.runtimes import runtime_for
from agents.anyplot.render.runtimes.python import PythonRuntime
from agents.anyplot.schemas import PlotResult
from agents.anyplot.services import CodeVersion, Services
from agents.anyplot.settings import AgentSettings
from agents.renderer.commands import JS_FONTCONFIG_FILE, JS_NODE_MODULES, NODE_BINARY, PLAYWRIGHT_BROWSERS

from .conftest import JS_PROMPT_IDIOMS, REPO_ROOT
from .test_profile_javascript_image import IDIOM_DTYPES, IDIOM_NAMES, IDIOM_ROWS, csv_text


IMAGE = os.environ.get("ANYPLOT_JS_IMAGE", "anyplot-renderer:js")
PROBE = REPO_ROOT / "agents" / "renderer" / "page_probe.mjs"
PROBE_CSV = 'label,value\n"a</script>",3\nb,5\nc,2\nd,7\ne,4\n'
PROBE_DTYPES = {"label": "text", "value": "number"}


@functools.cache
def _image_present() -> bool:
    docker = shutil.which("docker")
    if docker is None:
        return False
    return subprocess.run([docker, "image", "inspect", IMAGE], capture_output=True, check=False).returncode == 0


pytestmark = pytest.mark.skipif(not _image_present(), reason=f"needs Docker and the image {IMAGE}")


def in_image(*command: str, mounts: tuple[tuple[Path, str], ...] = ()) -> subprocess.CompletedProcess[str]:
    """Node in the image, offline, as the current user, with the probe mounted and the row's browser and fonts."""
    volumes = [flag for source, target in mounts for flag in ("-v", f"{source}:{target}:ro")]
    return subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp",
            "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{PROBE}:/probe/page_probe.mjs:ro", *volumes,
            "-e", "HOME=/tmp", "-e", "XDG_CACHE_HOME=/tmp", "-e", "XDG_CONFIG_HOME=/tmp",
            "-e", f"PLAYWRIGHT_BROWSERS_PATH={PLAYWRIGHT_BROWSERS}", "-e", f"ANYPLOT_NODE_MODULES={JS_NODE_MODULES}",
            "-e", f"FONTCONFIG_FILE={JS_FONTCONFIG_FILE}",
            IMAGE, NODE_BINARY, "/probe/page_probe.mjs", *command,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )  # fmt: skip


def probe(wrapper: Path, *flags: str) -> dict[str, object]:
    done = in_image("check", "/page/plot.html", *flags, mounts=((wrapper.parent, "/page"),))
    report = json.loads(done.stdout)
    assert done.returncode == 0 and report["failures"] == [], (report, done.stderr[-2000:])
    return report


def version_of(library: str, run_form: str, csv: str, dtypes: dict[str, str], dates: list[str]) -> CodeVersion:
    kinds = read_kinds(csv, dtypes, dates)  # type: ignore[arg-type]
    return CodeVersion(
        number=1,
        working="",
        run_form=run_form,
        export="",
        data_csv=csv,
        render_id="r1",
        result=PlotResult(status="ok", attempts=1, artifacts=["plot-light.png", "plot.js", "data.csv"]),
        library=library,
        code_artifact="plot.js",
        data_json=typed_json(csv, kinds),
    )


def download(version: CodeVersion, theme: str, out: Path) -> tuple[Path, float]:
    """`page_download` through the local Docker backend: the wrapped page written to `out`, and the seconds it took."""
    settings = AgentSettings()
    backend = LocalDockerBackend(
        image=IMAGE,
        runtime=PythonRuntime(),
        environment="development",
        runtime_for=lambda library: runtime_for(library, cpu_seconds=settings.render_timeout_s),
    )
    started = time.monotonic()
    content = asyncio.run(
        page_download(Services(backend_factory=lambda: backend), settings, version, theme, spec_id="scatter-basic")  # type: ignore[arg-type]
    )
    took = time.monotonic() - started
    out.mkdir(parents=True, exist_ok=True)
    (out / "plot.html").write_bytes(content)
    return out / "plot.html", took


@pytest.mark.parametrize("library", ["chartjs", "d3", "echarts"])
def test_the_probe_page_keeps_its_plot_and_refuses_every_way_out(tmp_path: Path, library: str) -> None:
    """The probe's snippet draws from the typed table, hovers into a tooltip through the scaled frame, and every one
    of its escape attempts fails: `top.location`, `window.open`, `fetch`, storage, cookies, its own frame's navigation
    to an http URL; the frame's origin is `null`, and a listener on the loopback sees no request."""
    snippet = in_image("snippet", library)
    assert snippet.returncode == 0, snippet.stderr
    version = version_of(library, snippet.stdout, PROBE_CSV, PROBE_DTYPES, [])

    wrapper, _ = download(version, "dark", tmp_path)

    report = probe(wrapper, "--hover", "--attempts")
    checks = report["checks"]
    assert isinstance(checks, dict) and checks["opaque_origin"] == "null"


@pytest.mark.parametrize("library", ["chartjs", "d3", "echarts", "highcharts"])
def test_the_prompts_idioms_download_as_a_page_that_draws(tmp_path: Path, library: str) -> None:
    """Each library's idiom form (the adapter prompt's code, `conftest.JS_PROMPT_IDIOMS`) on the render test's table
    (missing cells, a column name with a quote and a backslash) downloads as a page that draws in its frame without a
    page error, in both themes."""
    run_form = to_run_form(JS_PROMPT_IDIOMS[library], library=library)
    csv = csv_text(IDIOM_NAMES, IDIOM_ROWS)
    for theme in ("light", "dark"):
        version = version_of(library, run_form, csv, IDIOM_DTYPES, [IDIOM_NAMES[0]])
        wrapper, _ = download(version, theme, tmp_path / theme)
        probe(wrapper)
