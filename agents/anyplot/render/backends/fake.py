"""The fake render backend for tests and offline development: fixture PNGs, no code runs.

`FakeBackend` returns a drawn 3200x1800 PNG per theme (a background in the theme's
page colour with a few bars, so R2 sees a non-blank image) and a probe without
findings, unless the test scripts something else: an exit code, a timeout, a stderr
tail, a canvas size, a PNG of its own, or a probe. Every job it receives is kept in
`jobs`, so a test can read what the pipeline asked to render.
"""

import io
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from PIL import Image, ImageDraw

from core.palette import IMPRINT

from ..contract import RenderJob, RenderResult, Theme, ThemeOutput


BACKGROUNDS: dict[Theme, str] = {"light": "#FAF8F1", "dark": "#1A1A17"}
INK: dict[Theme, str] = {"light": "#1A1A17", "dark": "#F0EFE8"}


def fixture_png(theme: Theme, size: tuple[int, int] = (3200, 1800)) -> bytes:
    """A deterministic, non-blank plot-like PNG in the theme's colours."""
    width, height = size
    image = Image.new("RGB", size, BACKGROUNDS[theme])
    draw = ImageDraw.Draw(image)
    left, bottom = width // 10, height - height // 8
    draw.line([(left, height // 10), (left, bottom), (width - width // 20, bottom)], fill=INK[theme], width=6)
    bar = (width - left) // 12
    for index in range(8):
        top = bottom - (index + 2) * height // 14
        x0 = left + bar // 2 + index * (bar + bar // 3)
        draw.rectangle([x0, top, x0 + bar, bottom - 3], fill=IMPRINT[index % len(IMPRINT)])
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@dataclass
class FakeOutcome:
    """What the fake returns for one theme of one job."""

    exit_code: int = 0
    timed_out: bool = False
    stderr_tail: str = ""
    size: tuple[int, int] = (3200, 1800)
    png: bytes | None = None
    probe: dict[str, Any] | None = None
    no_png: bool = False


Script = Callable[[RenderJob, Theme], FakeOutcome]


@dataclass
class FakeBackend:
    """Fixture renders; `script(job, theme)` decides the outcome (default: a clean render)."""

    script: Script | None = None
    name: str = "fake"
    jobs: list[RenderJob] = field(default_factory=list)

    async def render(self, job: RenderJob) -> RenderResult:
        self.jobs.append(job)
        result = RenderResult(job_id=job.job_id)
        for theme in job.themes:
            outcome = self.script(job, theme) if self.script else FakeOutcome()
            png = None if outcome.no_png or outcome.exit_code != 0 else outcome.png or fixture_png(theme, outcome.size)
            probe = outcome.probe if outcome.probe is not None else {"texts": [], "tick_overlaps": 0, "points": 0}
            result.outputs[theme] = ThemeOutput(
                theme=theme,
                exit_code=outcome.exit_code,
                timed_out=outcome.timed_out,
                png=png,
                probe=probe,
                stderr_tail=outcome.stderr_tail,
            )
        return result
