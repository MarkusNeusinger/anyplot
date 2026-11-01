"""The R and Julia text probes (`text_probe.R`, `text_probe.jl`) against the renderer image (2026-11-01).

Skipped unless Docker is available and the image is present (`ANYPLOT_TEXT_PROBE_IMAGE`, by default
`anyplot-renderer:figure`, a local tag of a renderer image with R and Julia). Each render goes through the local Docker
backend exactly as a development session's does: the row's command and environment, the harness in exec mode, the
checkout's `harness.py` and text probes mounted over the image's (`local.TEXT_PROBE_MOUNTS`), no network, a read-only
root. The probe is best-effort: a probe that fails leaves an error in place of the labels, never a failed render.
"""

import asyncio
import functools
import os
import secrets
import shutil
import subprocess
from typing import Any

import pytest

from agents.anyplot.render.backends.local import LocalDockerBackend
from agents.anyplot.render.contract import RenderJob
from agents.anyplot.render.runtimes import PythonRuntime, runtime_for


IMAGE = os.environ.get("ANYPLOT_TEXT_PROBE_IMAGE", "anyplot-renderer:figure")


@functools.cache
def _image_present() -> bool:
    docker = shutil.which("docker")
    if docker is None:
        return False
    return subprocess.run([docker, "image", "inspect", IMAGE], capture_output=True, check=False).returncode == 0


pytestmark = pytest.mark.skipif(not _image_present(), reason=f"needs Docker and the image {IMAGE}")

DATA = "Region,Umsatz\nNord,3\nSüd,5\n"
GGPLOT = """library(ggplot2)
THEME <- Sys.getenv("ANYPLOT_THEME", "light")
df <- readr::read_csv("data.csv", show_col_types = FALSE)
plot <- ggplot(df, aes(Region, Umsatz, fill = Region)) + geom_col() + geom_text(aes(label = Umsatz)) +
  labs(title = "Umsatz \\u2013 Übersicht", x = "Region", y = "CHF", fill = "Gebiet")
ggsave(sprintf("plot-%s.png", THEME), plot, device = ragg::agg_png, width = 16, height = 9, dpi = 200)
"""
MAKIE = """using CairoMakie
const THEME = get(ENV, "ANYPLOT_THEME", "light")
fig = Figure(size = (1600, 900))
ax = Axis(fig[1, 1]; title = "Umsatz – Übersicht", xlabel = "Region", ylabel = "CHF",
          xticks = (1:2, ["Nord", "Süd"]))
barplot!(ax, 1:2, [3, 5]; label = "Umsatz")
text!(ax, 2, 5; text = "Rekord")
Legend(fig[1, 2], ax, "Gebiet")
save("plot-$(THEME).png", fig; px_per_unit = 2)
"""


def render(library: str, source: str) -> tuple[int | None, Any]:
    backend = LocalDockerBackend(
        image=IMAGE, runtime=PythonRuntime(), environment="development", runtime_for=runtime_for
    )
    runtime = runtime_for(library)
    job = RenderJob(
        job_id=f"tp-{library}-{secrets.token_hex(4)}",  # unique: parallel tests start containers named by it
        language=runtime.language,
        library=library,
        source=source,
        data_csv=DATA,
        themes=("light",),
        timeout_s=180,
    )
    output = asyncio.run(backend.render(job)).outputs["light"]
    return output.exit_code, output.probe


def kinds_and_texts(probe: Any) -> set[tuple[str, str]]:
    assert isinstance(probe, dict) and isinstance(probe.get("labels"), list), probe
    return {(label["kind"], label["text"]) for label in probe["labels"]}


def test_a_ggplot2_save_leaves_its_drawn_texts_by_role() -> None:
    code, probe = render("ggplot2", GGPLOT)

    assert code == 0
    labels = kinds_and_texts(probe)
    assert {("title", "Umsatz – Übersicht"), ("x axis label", "Region"), ("y axis label", "CHF")} <= labels
    assert {("x tick label", "Süd"), ("legend text", "Gebiet"), ("legend text", "Nord"), ("annotation", "5")} <= labels


def test_a_makie_figure_leaves_its_drawn_texts_by_role() -> None:
    code, probe = render("makie", MAKIE)

    assert code == 0
    labels = kinds_and_texts(probe)
    assert {("title", "Umsatz – Übersicht"), ("x axis label", "Region"), ("y axis label", "CHF")} <= labels
    assert {("x tick label", "Süd"), ("legend text", "Gebiet"), ("legend text", "Umsatz")} <= labels
    assert ("annotation", "Rekord") in labels


def test_a_makie_label_is_the_title_only_when_it_stands_alone() -> None:
    """No axes title: the one largest `Label` is the title; labels of one size (panel letters) are other texts; a
    colorbar's label is its own kind (Gemini Flash review of #12503)."""
    source = """using CairoMakie
const THEME = get(ENV, "ANYPLOT_THEME", "light")
fig = Figure(size = (1600, 900))
Label(fig[0, 1:2], "Wetter"; fontsize = 30)
for (column, letter) in enumerate(["A", "B"])
    Label(fig[1, column, TopLeft()], letter; fontsize = 14)
end
ax = Axis(fig[1, 1]; xlabel = "Tag")
hm = heatmap!(ax, rand(4, 4))
Colorbar(fig[1, 2], hm; label = "Grad")
save("plot-$(THEME).png", fig; px_per_unit = 2)
"""
    code, probe = render("makie", source)

    assert code == 0
    labels = kinds_and_texts(probe)
    assert {("title", "Wetter"), ("text", "A"), ("text", "B"), ("colorbar label", "Grad")} <= labels
    assert not {("title", "A"), ("title", "B")} & labels


def test_a_ggplot2_patchwork_names_each_plot_s_title_and_its_own() -> None:
    combined = 'plot <- patchwork::wrap_plots(plot, plot) + patchwork::plot_annotation(title = "Gesamt"); '
    source = GGPLOT.replace("ggsave(sprintf", combined + "ggsave(sprintf")

    code, probe = render("ggplot2", source)

    assert code == 0
    labels = kinds_and_texts(probe)
    assert {("title", "Gesamt"), ("title", "Umsatz – Übersicht"), ("legend text", "Gebiet")} <= labels


def test_a_ggplot2_probe_that_fails_leaves_an_error_and_the_render_stands() -> None:
    """`ggsave` takes a grid grob too, which `ggplotGrob` cannot build: the probe fails, the save does not."""
    grob = GGPLOT.replace("ggsave(sprintf", "plot <- grid::textGrob('Umsatz'); ggsave(sprintf")

    code, probe = render("ggplot2", grob)

    assert code == 0 and probe == {"error": "Error"}


def test_a_makie_probe_that_fails_leaves_an_error_and_the_render_stands() -> None:
    """The plot's code shares the process with the hook and can break it: the hook writes the error, never exits."""
    broken = MAKIE + 'Base.eval(Main.AnyplotTextProbe, :(entries(M, figure) = error("tampered")))\n'

    code, probe = render("makie", broken)

    assert code == 0 and probe == {"error": "ErrorException"}
